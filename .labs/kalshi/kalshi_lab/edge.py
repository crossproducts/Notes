"""Expected value and position sizing for binary event contracts.

A Kalshi contract pays $1 if the event resolves YES and $0 otherwise, so the
arithmetic is cleaner than equities: with an all-in cost per contract of

    c = price + fee_per_contract

and a believed true probability `p`, the expected value per contract is simply
`p - c`, and the Kelly-optimal fraction of bankroll is `(p - c) / (1 - c)`.

The clean algebra is a trap, though. Every quantity above is known exactly
EXCEPT `p`, which is the one you are guessing, and Kelly is brutally sensitive
to overestimating it: believing 0.60 when the truth is 0.50 does not merely
shrink the edge, it turns a positive-EV bet into a negative one while telling
you to size up. That is why `kelly_fraction` defaults to a quarter-Kelly cap
and why `should_trade` demands the edge clear a margin wide enough to absorb
being wrong about `p`, rather than merely clearing zero.

Everything here is per-contract and fee-aware; nothing assumes frictionless
fills. The equities lab learned that lesson the expensive way -- its own
architecture review records that zero-cost backtests inflated every comparison
it had made until costs were added.
"""

from __future__ import annotations

from dataclasses import dataclass

from .fees import fee_per_contract

# A quarter of full Kelly. Full Kelly is optimal only if `p` is exactly right;
# at a quarter you give up a little growth for a lot of tolerance to being wrong.
DEFAULT_KELLY_FRACTION = 0.25

# Minimum edge (in probability points) before a trade is worth taking. 0.03 is
# a starting placeholder, NOT a derived constant: it should be replaced by the
# measured calibration error of your own forecaster on settled markets, via
# `calibration.calibration_report`. A forecaster with +/-8pp error has no
# business trading a 3pp edge.
DEFAULT_MIN_EDGE = 0.03


@dataclass(frozen=True)
class Trade:
    """A sized, costed trade candidate."""

    side: str            # "yes" or "no"
    price: float         # dollars per contract, the side's own price
    cost_per_contract: float
    p_true: float        # believed probability THIS SIDE resolves in the money
    edge: float          # p_true - cost_per_contract
    kelly_fraction: float
    contracts: int
    stake: float
    expected_value: float

    @property
    def edge_bps(self) -> float:
        return self.edge * 10_000


def cost_per_contract(price: float, *, maker: bool = False, **kwargs) -> float:
    """Price plus fee -- the real break-even probability for this contract."""
    return price + fee_per_contract(price, maker=maker, **kwargs)


def break_even_prob(price: float, **kwargs) -> float:
    """The probability at which this contract is a coin flip after fees.

    Any forecast below this loses money in expectation no matter how confident.
    """
    return cost_per_contract(price, **kwargs)


def expected_value(p_true: float, price: float, **kwargs) -> float:
    """EV in dollars per contract. Positive means the bet is worth taking."""
    _validate_prob(p_true)
    return p_true - cost_per_contract(price, **kwargs)


def kelly_fraction(
    p_true: float,
    price: float,
    *,
    fraction: float = DEFAULT_KELLY_FRACTION,
    **kwargs,
) -> float:
    """Fraction of bankroll to stake, scaled by `fraction` (quarter-Kelly).

    Returns 0.0 for a non-positive edge; never returns more than `fraction`,
    and never recommends betting the bankroll.
    """
    _validate_prob(p_true)
    c = cost_per_contract(price, **kwargs)
    if c <= 0.0 or c >= 1.0:
        return 0.0
    edge = p_true - c
    if edge <= 0.0:
        return 0.0
    return min(edge / (1.0 - c) * fraction, fraction)


def should_trade(
    p_true: float,
    price: float,
    *,
    min_edge: float = DEFAULT_MIN_EDGE,
    **kwargs,
) -> bool:
    """True if the edge clears `min_edge` AFTER fees."""
    return expected_value(p_true, price, **kwargs) >= min_edge


def size_trade(
    p_true: float,
    price: float,
    bankroll: float,
    *,
    side: str = "yes",
    fraction: float = DEFAULT_KELLY_FRACTION,
    min_edge: float = DEFAULT_MIN_EDGE,
    max_contracts: int | None = None,
    **kwargs,
) -> Trade | None:
    """Size a trade, or return None if it does not clear the edge threshold.

    `p_true` is the probability that THIS SIDE finishes in the money, and
    `price` is this side's own price -- so for a NO trade pass the NO price and
    the probability of NO, not their YES counterparts.
    """
    if side not in ("yes", "no"):
        raise ValueError('side must be "yes" or "no"')
    if bankroll <= 0:
        return None
    if not should_trade(p_true, price, min_edge=min_edge, **kwargs):
        return None

    c = cost_per_contract(price, **kwargs)
    f = kelly_fraction(p_true, price, fraction=fraction, **kwargs)
    contracts = int(bankroll * f / c) if c > 0 else 0
    if max_contracts is not None:
        contracts = min(contracts, max_contracts)
    if contracts < 1:
        return None

    return Trade(
        side=side,
        price=price,
        cost_per_contract=c,
        p_true=p_true,
        edge=p_true - c,
        kelly_fraction=f,
        contracts=contracts,
        stake=contracts * c,
        expected_value=contracts * (p_true - c),
    )


def _validate_prob(p: float) -> None:
    if not 0.0 <= p <= 1.0:
        raise ValueError(f"probability must be in [0, 1], got {p}")
