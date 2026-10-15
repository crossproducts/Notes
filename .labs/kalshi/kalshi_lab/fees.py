"""Kalshi fee model.

The fee is the single most important number in this lab, because of its shape:

    fee = coefficient x contracts x P x (1 - P) x series_multiplier

P x (1 - P) peaks at P = 0.50 and collapses toward the extremes. So the fee is
*maximised exactly where a coin-flip market sits* and nearly free out in the
tails. That matters here specifically, because the published Kalshi edge is
tail-concentrated (favourites earn small positive returns, longshots lose) --
see docs/edge-thesis.md. The fee curve and the edge curve point the same way,
which is the main reason this lab is worth building at all.

Expressed as a FRACTION OF NOTIONAL the picture inverts, and that is the number
that decides whether a trade is worth taking:

    fee_per_contract / P = 0.07 x (1 - P)

so a 5c longshot pays ~6.7% of notional in fees per side, while a 95c favourite
pays ~0.35%. Buying cheap is punished roughly 19x harder than buying dear.

CAUTION -- these constants are not from Kalshi's own documentation. They come
from third-party guides (see README sources), which agree on the 0.07 taker
coefficient and the 0.0175 maker coefficient but DISAGREE on rounding, and note
that the per-series multiplier and the maker-fee flag vary by series. Treat
every default here as a placeholder to be replaced by values read from
`/trade-api/v2/series/{series_ticker}` before any real money moves. `FeeSchedule`
exists so that swap is a one-line change rather than a hunt through the code.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Third-party-reported coefficients. Verify against the official fee schedule.
TAKER_COEFFICIENT = 0.07
MAKER_COEFFICIENT = 0.0175  # a quarter of taker; applies only to flagged series

# Rounding is genuinely disputed between sources: one reports rounding up to the
# next cent per ORDER, another describes six-decimal per-trade fees with
# adjustments. "order" is the conservative default for a taker; "none" is for
# analysis where you want the smooth curve rather than the billed amount.
ROUNDING_MODES = ("order", "contract", "none")


@dataclass(frozen=True)
class FeeSchedule:
    """How one series is billed. Populate from the series API, not from memory."""

    taker_coefficient: float = TAKER_COEFFICIENT
    maker_coefficient: float = MAKER_COEFFICIENT
    multiplier: float = 1.0       # 0.0 for fee-free series; varies for sports
    maker_fees_enabled: bool = False  # most series rest orders for free
    rounding: str = "order"

    def __post_init__(self) -> None:
        if self.rounding not in ROUNDING_MODES:
            raise ValueError(f"rounding must be one of {ROUNDING_MODES}")
        if self.multiplier < 0:
            raise ValueError("multiplier must be >= 0")


DEFAULT_SCHEDULE = FeeSchedule()


# Binary floating point makes exact fees land a hair above their true value --
# 0.07 * 100 * 0.5 * 0.5 evaluates to 1.7500000000000002, and a naive ceil turns
# that $1.75 into $1.76. Snapping to this many decimals before rounding up keeps
# the exact cases exact while leaving genuine fractions of a cent to round up.
_CENT_PRECISION = 9


def _ceil_cents(dollars: float) -> float:
    return math.ceil(round(dollars * 100.0, _CENT_PRECISION)) / 100.0


def _round_cents(dollars: float, mode: str, contracts: int) -> float:
    """Apply the schedule's rounding, in cents, and return dollars."""
    if mode == "none":
        return dollars
    if mode == "contract":
        return _ceil_cents(dollars / contracts) * contracts
    return _ceil_cents(dollars)  # "order"


def fee(
    contracts: int,
    price: float,
    *,
    maker: bool = False,
    schedule: FeeSchedule = DEFAULT_SCHEDULE,
) -> float:
    """Trading fee in DOLLARS for `contracts` at `price`.

    `price` is in dollars per contract (0.0-1.0), not cents. A resting order on
    a series without maker fees is free, which is the whole structural argument
    for making rather than taking -- see `docs/edge-thesis.md`.
    """
    if contracts <= 0:
        return 0.0
    if not 0.0 <= price <= 1.0:
        raise ValueError(f"price must be in [0, 1] dollars, got {price}")

    if maker and not schedule.maker_fees_enabled:
        return 0.0
    coefficient = schedule.maker_coefficient if maker else schedule.taker_coefficient

    raw = coefficient * contracts * price * (1.0 - price) * schedule.multiplier
    return _round_cents(raw, schedule.rounding, contracts)


def fee_per_contract(price: float, **kwargs) -> float:
    """Unrounded per-contract fee -- the smooth curve, for analysis and EV."""
    schedule = kwargs.pop("schedule", DEFAULT_SCHEDULE)
    smooth = FeeSchedule(
        taker_coefficient=schedule.taker_coefficient,
        maker_coefficient=schedule.maker_coefficient,
        multiplier=schedule.multiplier,
        maker_fees_enabled=schedule.maker_fees_enabled,
        rounding="none",
    )
    return fee(1, price, schedule=smooth, **kwargs)


def fee_as_fraction_of_notional(price: float, **kwargs) -> float:
    """Fee per contract divided by the price paid.

    This is the number to compare an edge against. For a taker it reduces to
    `coefficient x (1 - price)`, so it rises steeply as contracts get cheaper.
    """
    if price <= 0.0:
        return float("inf")
    return fee_per_contract(price, **kwargs) / price


def round_trip_cost(price: float, *, exit_price: float | None = None, **kwargs) -> float:
    """Total per-contract fees to enter at `price` and exit at `exit_price`.

    Held to settlement there is no exit fee -- settlement is not a trade, which
    is a real structural advantage over equities, where every round trip is
    billed twice. Pass `exit_price` only when modelling an early exit.
    """
    cost = fee_per_contract(price, **kwargs)
    if exit_price is not None:
        cost += fee_per_contract(exit_price, **kwargs)
    return cost
