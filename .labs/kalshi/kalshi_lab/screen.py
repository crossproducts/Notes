"""Stage 4 of the pipeline: decide whether a series is worth trading at all.

This is the Kalshi analogue of the equities lab's champion/challenger gate, and
it exists for the same reason: that lab's own architecture review found it had
been promoting strategies on in-sample Sharpe, which is precisely the
overfitting its walk-forward endpoint was built to catch. The gate here is
deliberately harder to pass than "the backtest made money".

A series graduates only if all four hold:

  1. SKILL      -- the forecaster beats the market price's own Brier score.
  2. SIGNIFICANCE -- an event-clustered bootstrap CI on that improvement
                   excludes zero. Contracts are not independent; a hundred
                   strikes on one CPI print carry one event's information.
  3. FEES       -- the mean per-trade edge clears the fee hurdle with margin.
  4. SAMPLE     -- enough distinct EVENTS, not merely enough contracts.

Failing any one returns a verdict explaining which, so a rejection is
diagnostic rather than a shrug. Nothing here is a profitability claim: passing
means "worth paper-trading next", not "this makes money".
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .calibration import (
    bootstrap_paired_improvement,
    calibration_report,
    skill_vs_market,
)
from .edge import DEFAULT_MIN_EDGE
from .fees import fee_as_fraction_of_notional

# A series needs this many distinct resolved EVENTS before its numbers mean
# anything. 30 is a convention, not a derivation -- with monthly macro prints
# that is already two and a half years of history, which is the real constraint.
MIN_EVENTS = 30


@dataclass(frozen=True)
class SeriesVerdict:
    series: str
    n_contracts: int
    n_events: int
    model_brier: float
    market_brier: float
    brier_skill_score: float
    skill_ci: tuple[float, float]
    mean_edge: float
    mean_fee_hurdle: float
    passed: bool
    reasons: list[str]

    @property
    def net_edge(self) -> float:
        """Mean edge left after the fee hurdle. The only number that spends."""
        return self.mean_edge - self.mean_fee_hurdle

    def summary(self) -> str:
        verdict = "PASS" if self.passed else "REJECT"
        # BSS is a ratio and skill_ci is on the Brier DIFFERENCE -- different
        # scales, so they are labelled rather than printed as one quantity.
        head = (
            f"[{verdict}] {self.series}: {self.n_contracts} contracts / "
            f"{self.n_events} events | BSS {self.brier_skill_score:+.4f} | "
            f"Brier improvement CI "
            f"[{self.skill_ci[0]:+.4f}, {self.skill_ci[1]:+.4f}] | "
            f"net edge {self.net_edge:+.4f}"
        )
        return head + "".join(f"\n    - {r}" for r in self.reasons)


def screen_series(
    series: str,
    model_predictions: Sequence[float],
    market_prices: Sequence[float],
    outcomes: Sequence[int],
    event_ids: Sequence[object],
    *,
    min_edge: float = DEFAULT_MIN_EDGE,
    min_events: int = MIN_EVENTS,
    confidence: float = 0.95,
    n_resamples: int = 2000,
    seed: int | None = None,
) -> SeriesVerdict:
    """Run the four gates over one series' settled history."""
    n = len(model_predictions)
    if not (n == len(market_prices) == len(outcomes) == len(event_ids)):
        raise ValueError("all inputs must be the same length")

    skill = skill_vs_market(model_predictions, market_prices, outcomes)
    n_events = len(set(event_ids))

    # CI on the IMPROVEMENT (market Brier - model Brier), clustered by event.
    lo, hi = bootstrap_paired_improvement(
        model_predictions,
        market_prices,
        outcomes,
        event_ids,
        n_resamples=n_resamples,
        confidence=confidence,
        seed=seed,
    )

    mean_edge = sum(
        abs(m - p) for m, p in zip(model_predictions, market_prices)
    ) / n
    mean_fee_hurdle = sum(
        fee_as_fraction_of_notional(max(p, 0.01)) * p for p in market_prices
    ) / n

    reasons: list[str] = []
    if skill["brier_skill_score"] <= 0:
        reasons.append(
            f"no skill: model Brier {skill['model_brier']:.4f} does not beat "
            f"the market's {skill['market_brier']:.4f}"
        )
    if lo <= 0.0:
        reasons.append(
            f"improvement not significant: clustered {confidence:.0%} CI "
            f"[{lo:+.4f}, {hi:+.4f}] includes zero"
        )
    if mean_edge - mean_fee_hurdle < min_edge:
        reasons.append(
            f"edge {mean_edge:.4f} does not clear fee hurdle "
            f"{mean_fee_hurdle:.4f} by the {min_edge:.4f} margin"
        )
    if n_events < min_events:
        reasons.append(f"only {n_events} distinct events, need {min_events}")

    passed = not reasons
    if passed:
        reasons.append("clears skill, significance, fee and sample gates")

    return SeriesVerdict(
        series=series,
        n_contracts=n,
        n_events=n_events,
        model_brier=skill["model_brier"],
        market_brier=skill["market_brier"],
        brier_skill_score=skill["brier_skill_score"],
        skill_ci=(lo, hi),
        mean_edge=mean_edge,
        mean_fee_hurdle=mean_fee_hurdle,
        passed=passed,
        reasons=reasons,
    )


def calibration_by_price_bucket(
    market_prices: Sequence[float], outcomes: Sequence[int], n_bins: int = 10
):
    """Reliability of the MARKET itself, bucketed by price.

    Run this before building any forecaster. It answers the prior question --
    where, if anywhere, is this series mispriced? -- and reproduces the
    published favourite-longshot finding as a negative gap in the low bins.
    """
    return calibration_report(market_prices, outcomes, n_bins).bins
