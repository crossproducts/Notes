"""Runnable end-to-end demo on synthetic data: `python -m kalshi_lab.demo`.

Stages 3-5 of the pipeline (score -> gate -> size) against generated history,
so the gate's behaviour is inspectable before any API key exists. Stage 1
(ingest from Kalshi) is the open piece -- see README.

The two synthetic series are chosen to mirror the published finding: rate
markets are close to efficient and should be REJECTED, while a series with a
real forecasting edge should PASS. If a change ever makes the efficient series
pass, the gate has been broken.
"""

from __future__ import annotations

import random

from .edge import size_trade
from .fees import fee_as_fraction_of_notional
from .screen import calibration_by_price_bucket, screen_series

BANKROLL = 2_000.0


def _series(n_events, strikes, skill, seed, longshot_bias=0.0):
    """Synthetic settled history; `longshot_bias` overprices cheap contracts."""
    rng = random.Random(seed)
    model, market, outs, events = [], [], [], []
    for e in range(n_events):
        p = rng.uniform(0.05, 0.95)
        outcome = 1 if rng.random() < p else 0
        for _ in range(strikes):
            price = min(max(p + rng.uniform(-0.03, 0.03), 0.01), 0.99)
            if price < 0.25:                 # cheap contracts quoted too dear
                price = min(price + longshot_bias, 0.99)
            market.append(price)
            model.append(min(max(price + skill * (outcome - price), 0.0), 1.0))
            outs.append(outcome)
            events.append(e)
    return model, market, outs, events


def main() -> None:
    print("=" * 72)
    print("FEE HURDLE -- required relative mispricing just to break even")
    print("=" * 72)
    print(f"  {'price':>7}  {'fee/contract':>14}  {'as % of notional':>18}")
    for price in (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95):
        frac = fee_as_fraction_of_notional(price)
        print(f"  {price:>7.2f}  {frac * price:>14.5f}  {frac:>17.2%}")
    print("\n  A 5c longshot must be ~19x more mispriced than a 95c favourite")
    print("  before it is worth touching. Fees peak in dollars at 50c, but as")
    print("  a share of capital at risk they punish the tails you buy cheap.\n")

    print("=" * 72)
    print("GATE -- two series, one efficient and one with a real edge")
    print("=" * 72)

    efficient = _series(60, 20, skill=0.02, seed=11)
    verdict = screen_series("KXRATES (efficient)", *efficient, n_resamples=400, seed=1)
    print(verdict.summary(), "\n")

    skilled = _series(60, 20, skill=0.45, seed=12)
    verdict = screen_series("KXJOBS (has edge)", *skilled, n_resamples=400, seed=1)
    print(verdict.summary(), "\n")

    print("=" * 72)
    print("MARKET CALIBRATION -- where is this series mispriced?")
    print("=" * 72)
    _, market, outs, _ = _series(300, 6, skill=0.0, seed=13, longshot_bias=0.07)
    print(f"  {'price band':>12}  {'n':>5}  {'predicted':>10}  {'observed':>9}  {'gap':>8}")
    for b in calibration_by_price_bucket(market, outs, n_bins=10):
        print(
            f"  {b.low:>5.2f}-{b.high:<5.2f}  {b.count:>5}  "
            f"{b.mean_predicted:>10.3f}  {b.observed_rate:>9.3f}  {b.gap:>+8.3f}"
        )
    print("\n  Negative gaps in the low bands = cheap contracts resolve YES less")
    print("  often than their price implies. Trade that by BUYING THE OTHER SIDE,")
    print("  where the fee hurdle is also ~19x lower.\n")

    print("=" * 72)
    print(f"SIZING -- quarter-Kelly on a ${BANKROLL:,.0f} bankroll")
    print("=" * 72)
    for p_true, price, label in (
        (0.55, 0.50, "thin edge on a coin flip"),
        (0.70, 0.50, "strong edge mid-book"),
        (0.98, 0.95, "small edge on a favourite"),
        (0.12, 0.05, "longshot you believe is cheap"),
        (0.88, 0.95, "same market, buying the favourite"),
    ):
        t = size_trade(p_true, price, BANKROLL)
        if t is None:
            print(f"  {label:<31} p={p_true:.2f} @ {price:.2f}  ->  NO TRADE")
        else:
            print(
                f"  {label:<31} p={p_true:.2f} @ {price:.2f}  ->  "
                f"{t.contracts:>4} contracts, ${t.stake:>7.2f} staked, "
                f"EV ${t.expected_value:>6.2f}"
            )

    print("""
  Two honest caveats the numbers above do not show.

  The longshot line sizes up happily -- because it was TOLD p=0.12 against a
  5c price, a 140% relative mispricing that swamps the 6.65% fee hurdle. The
  machinery is agnostic; it is the belief that is suspect. Published work says
  cheap contracts are systematically OVERpriced, so the realistic version of
  that market is the last line: p below the price, and the trade is the other
  side. Feeding an optimistic p into a correct sizer is the main way to lose
  money with this lab.

  The favourite is refused at a 3pp edge while the coin flip is accepted at
  the same 3pp. A fixed edge floor in probability POINTS is not neutral across
  the price range -- 3pp on a 95c contract means claiming p=0.98, a far bolder
  forecast than p=0.53. Replace DEFAULT_MIN_EDGE with your measured
  calibration error per price bucket before trusting either answer.
""")


if __name__ == "__main__":
    main()
