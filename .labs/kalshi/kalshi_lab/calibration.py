"""Calibration scoring -- the reason this lab can be honest in a way the
equities lab structurally cannot.

An equity backtest can never tell you whether a *forecast* was right, only
whether a P&L curve went up, which is why the equities lab needs walk-forward
splits, Monte Carlo and a champion/challenger gate to fend off overfitting.
Event contracts hand you something better for free: every market resolves to a
known 0 or 1. That is a supervised label. You can measure whether your
probabilities are any good directly, on thousands of settled markets, without
simulating a single trade.

The gate that matters is `skill_vs_market`. Being well calibrated is NOT an
edge -- the market price is also well calibrated, and published work finds
Kalshi prices close to calibrated near resolution, with mispricing confined
mostly to the tails and to particular series. The only question that pays is
whether your forecast beats THE PRICE at predicting the outcome. If it does
not, every downstream component -- sizing, execution, risk -- is decoration on
a coin flip.

Statistical caution: contracts are not independent observations. Every strike
on one CPI print resolves off the same number, so a hundred correlated
contracts carry roughly one event's worth of information. A naive bootstrap
over contracts will badly overstate your significance. `bootstrap_ci` resamples
whole event clusters for that reason, and you should pass a real `clusters`
argument rather than letting each contract be its own cluster.
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass, field

EPSILON = 1e-15  # keeps log-loss finite at p = 0 or 1


@dataclass(frozen=True)
class Bin:
    """One reliability bucket."""

    low: float
    high: float
    count: int
    mean_predicted: float
    observed_rate: float

    @property
    def gap(self) -> float:
        """Observed minus predicted. Positive = the forecast was too low."""
        return self.observed_rate - self.mean_predicted


@dataclass(frozen=True)
class CalibrationReport:
    n: int
    brier: float
    log_loss: float
    slope: float
    intercept: float
    mean_absolute_error: float
    bins: list[Bin] = field(default_factory=list)

    @property
    def is_well_calibrated(self) -> bool:
        """Rough screen only: slope near 1, intercept near 0.

        Deliberately crude. Use `bootstrap_ci` for anything you would act on.
        """
        return abs(self.slope - 1.0) < 0.15 and abs(self.intercept) < 0.05


def _validate(predictions: Sequence[float], outcomes: Sequence[int]) -> None:
    if len(predictions) != len(outcomes):
        raise ValueError(
            f"predictions and outcomes differ in length: "
            f"{len(predictions)} vs {len(outcomes)}"
        )
    if not predictions:
        raise ValueError("need at least one observation")
    for p in predictions:
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"prediction out of [0, 1]: {p}")
    for o in outcomes:
        if o not in (0, 1, True, False):
            raise ValueError(f"outcome must be 0 or 1, got {o}")


def brier_score(predictions: Sequence[float], outcomes: Sequence[int]) -> float:
    """Mean squared error of probabilistic forecasts. Lower is better.

    0.25 is what you score by predicting 0.5 on everything, so treat 0.25 as
    the "knows nothing" line rather than treating 0 as the target.
    """
    _validate(predictions, outcomes)
    return sum((p - o) ** 2 for p, o in zip(predictions, outcomes)) / len(predictions)


def log_loss(predictions: Sequence[float], outcomes: Sequence[int]) -> float:
    """Cross-entropy. Punishes confident errors far harder than Brier does."""
    _validate(predictions, outcomes)
    total = 0.0
    for p, o in zip(predictions, outcomes):
        p = min(max(p, EPSILON), 1.0 - EPSILON)
        total += -(o * math.log(p) + (1 - o) * math.log(1.0 - p))
    return total / len(predictions)


def reliability_bins(
    predictions: Sequence[float], outcomes: Sequence[int], n_bins: int = 10
) -> list[Bin]:
    """Bucket forecasts and compare predicted against observed in each bucket.

    This is where a favourite-longshot bias becomes visible: a consistently
    negative gap in the low bins means cheap contracts are overpriced.
    """
    _validate(predictions, outcomes)
    if n_bins < 1:
        raise ValueError("n_bins must be >= 1")

    buckets: list[list[tuple[float, int]]] = [[] for _ in range(n_bins)]
    for p, o in zip(predictions, outcomes):
        idx = min(int(p * n_bins), n_bins - 1)  # p == 1.0 belongs in the last bin
        buckets[idx].append((p, int(o)))

    out = []
    for i, bucket in enumerate(buckets):
        if not bucket:
            continue
        ps = [p for p, _ in bucket]
        os_ = [o for _, o in bucket]
        out.append(
            Bin(
                low=i / n_bins,
                high=(i + 1) / n_bins,
                count=len(bucket),
                mean_predicted=sum(ps) / len(ps),
                observed_rate=sum(os_) / len(os_),
            )
        )
    return out


def calibration_slope(
    predictions: Sequence[float], outcomes: Sequence[int]
) -> tuple[float, float]:
    """OLS of outcome on predicted probability. Returns (slope, intercept).

    Perfect calibration gives slope 1, intercept 0. Slope below 1 means the
    forecasts are over-confident -- spread too wide for the skill behind them.

    This is the linear-probability form, not the logistic form more common in
    the literature; it needs no solver and is monotone in the same direction,
    but do not compare its numbers directly against a published logistic slope.
    """
    _validate(predictions, outcomes)
    n = len(predictions)
    mean_p = sum(predictions) / n
    mean_o = sum(outcomes) / n
    var = sum((p - mean_p) ** 2 for p in predictions)
    if var == 0.0:
        # Every forecast identical: slope undefined, so report "no information".
        return 0.0, mean_o
    cov = sum((p - mean_p) * (o - mean_o) for p, o in zip(predictions, outcomes))
    slope = cov / var
    return slope, mean_o - slope * mean_p


def calibration_report(
    predictions: Sequence[float], outcomes: Sequence[int], n_bins: int = 10
) -> CalibrationReport:
    """Everything above in one pass."""
    _validate(predictions, outcomes)
    slope, intercept = calibration_slope(predictions, outcomes)
    return CalibrationReport(
        n=len(predictions),
        brier=brier_score(predictions, outcomes),
        log_loss=log_loss(predictions, outcomes),
        slope=slope,
        intercept=intercept,
        mean_absolute_error=sum(abs(p - o) for p, o in zip(predictions, outcomes))
        / len(predictions),
        bins=reliability_bins(predictions, outcomes, n_bins),
    )


def skill_vs_market(
    model_predictions: Sequence[float],
    market_prices: Sequence[float],
    outcomes: Sequence[int],
) -> dict[str, float]:
    """THE gate. Does the forecast beat the price at predicting the outcome?

    Returns both Brier scores and the Brier Skill Score of the model relative
    to the market, where positive means the model is better, 0 means no skill
    beyond the price, and negative means the price is better than you are.

    A positive BSS is necessary but NOT sufficient to trade: the improvement
    still has to survive fees (`fees.fee_as_fraction_of_notional`) and an
    event-clustered confidence interval (`bootstrap_ci`). Small positive
    numbers on a few hundred correlated contracts are noise.
    """
    _validate(model_predictions, outcomes)
    _validate(market_prices, outcomes)
    model = brier_score(model_predictions, outcomes)
    market = brier_score(market_prices, outcomes)
    return {
        "model_brier": model,
        "market_brier": market,
        "brier_skill_score": 1.0 - model / market if market > 0 else 0.0,
        "improvement": market - model,
    }


def bootstrap_paired_improvement(
    model_predictions: Sequence[float],
    market_prices: Sequence[float],
    outcomes: Sequence[int],
    clusters: Sequence[object] | None = None,
    *,
    n_resamples: int = 2000,
    confidence: float = 0.95,
    seed: int | None = None,
) -> tuple[float, float]:
    """Event-clustered CI for (market Brier - model Brier). Positive = skill.

    Paired on purpose: both forecasts are scored against the same resolutions,
    so they are strongly correlated and bootstrapping them separately would
    throw away that pairing and inflate the interval. Each resampled contract
    carries its model forecast, the market price and the outcome together.
    """
    _validate(model_predictions, outcomes)
    _validate(market_prices, outcomes)
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")

    labels = (
        list(clusters) if clusters is not None else list(range(len(model_predictions)))
    )
    if len(labels) != len(model_predictions):
        raise ValueError("clusters must be the same length as predictions")

    grouped: dict[object, list[tuple[float, float, int]]] = {}
    for label, m, k, o in zip(labels, model_predictions, market_prices, outcomes):
        grouped.setdefault(label, []).append((m, k, int(o)))
    keys = list(grouped)

    rng = random.Random(seed)
    stats = []
    for _ in range(n_resamples):
        sample: list[tuple[float, float, int]] = []
        for _ in range(len(keys)):
            sample.extend(grouped[keys[rng.randrange(len(keys))]])
        model = [m for m, _, _ in sample]
        market = [k for _, k, _ in sample]
        outs = [o for _, _, o in sample]
        stats.append(brier_score(market, outs) - brier_score(model, outs))

    stats.sort()
    tail = (1.0 - confidence) / 2.0
    return (
        stats[int(tail * n_resamples)],
        stats[min(int((1.0 - tail) * n_resamples), n_resamples - 1)],
    )


def bootstrap_ci(
    predictions: Sequence[float],
    outcomes: Sequence[int],
    clusters: Sequence[object] | None = None,
    *,
    statistic=brier_score,
    n_resamples: int = 2000,
    confidence: float = 0.95,
    seed: int | None = None,
) -> tuple[float, float]:
    """Event-clustered bootstrap CI for any (predictions, outcomes) statistic.

    `clusters` labels which event each contract belongs to -- every strike on
    one CPI print shares a label. Whole clusters are resampled together, so the
    interval reflects the number of independent EVENTS rather than the much
    larger number of correlated contracts. Omitting `clusters` treats each
    contract as independent, which is almost always wrong here and will hand
    you an interval that is too narrow.
    """
    _validate(predictions, outcomes)
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")

    labels = list(clusters) if clusters is not None else list(range(len(predictions)))
    if len(labels) != len(predictions):
        raise ValueError("clusters must be the same length as predictions")

    grouped: dict[object, list[tuple[float, int]]] = {}
    for label, p, o in zip(labels, predictions, outcomes):
        grouped.setdefault(label, []).append((p, int(o)))
    keys = list(grouped)

    rng = random.Random(seed)
    stats = []
    for _ in range(n_resamples):
        sample: list[tuple[float, int]] = []
        for _ in range(len(keys)):
            sample.extend(grouped[keys[rng.randrange(len(keys))]])
        stats.append(statistic([p for p, _ in sample], [o for _, o in sample]))

    stats.sort()
    tail = (1.0 - confidence) / 2.0
    return (
        stats[int(tail * n_resamples)],
        stats[min(int((1.0 - tail) * n_resamples), n_resamples - 1)],
    )
