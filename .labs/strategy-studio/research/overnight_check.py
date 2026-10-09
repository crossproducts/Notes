"""Test the overnight-vs-intraday claim (reel DeF6WMaB-NX / Knuteson).

Claim: holding ONLY overnight (close -> next open) captures essentially all of
the long-run return, while holding ONLY intraday (open -> close) loses almost
everything -- and the two multiply back to buy-and-hold.

This is directly testable with the daily OHLC we already fetch; no new data.
The decisive question is NOT whether the pattern exists (it is well documented)
but whether it SURVIVES COSTS: the overnight leg trades every single day, so a
round trip per session at 5 bps/side is ~25%/yr of friction.
"""

import sys
from pathlib import Path

# engine/strategies live in backtest-api. Resolve for both the mounted
# container path (/app/research -> /app) and a local checkout.
_here = Path(__file__).resolve().parent
for _p in (_here.parent, _here.parent / "backtest-api"):
    if (_p / "engine.py").exists():
        sys.path.insert(0, str(_p))
        break

import numpy as np
import pandas as pd

import engine


def legs(df):
    """Overnight = Open_t / Close_{t-1}. Intraday = Close_t / Open_t."""
    o, c = df["Open"], df["Close"]
    overnight = (o / c.shift(1) - 1).dropna()
    intraday = (c / o - 1).reindex(overnight.index)
    buyhold = (c / c.shift(1) - 1).reindex(overnight.index)
    return overnight, intraday, buyhold


def stats(r, cost_bps=0.0, trades_per_day=0):
    """Annualised stats; cost applied per round trip per day."""
    net = r - (trades_per_day * cost_bps / 1e4)
    cum = float((1 + net).prod() - 1)
    ann = float((1 + net).prod() ** (252 / len(net)) - 1)
    vol = float(net.std() * np.sqrt(252))
    sharpe = ann / vol if vol else float("nan")
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    return dict(total=cum * 100, ann=ann * 100, vol=vol * 100, sharpe=sharpe, dd=dd * 100)


def row(label, s):
    return (f"  {label:28s} {s['total']:>14,.0f}% {s['ann']:>8.1f}% "
            f"{s['vol']:>7.1f}% {s['sharpe']:>7.2f} {s['dd']:>8.1f}%")


def main(symbols, start="1999-01-01"):
    print(f"{'':30s} {'total':>15s} {'ann':>8s} {'vol':>7s} {'sharpe':>7s} {'maxDD':>8s}")
    for sym in symbols:
        df = engine.fetch(sym, start)
        if len(df) < 500:
            print(f"\n{sym}: insufficient data")
            continue
        on, intra, bh = legs(df)
        print(f"\n=== {sym}  {on.index[0].date()} .. {on.index[-1].date()}  "
              f"({len(on)} sessions) ===")
        print(row("buy & hold", stats(bh)))
        print(row("overnight only (gross)", stats(on)))
        print(row("intraday only (gross)", stats(intra)))
        # The overnight leg buys at the close and sells at the next open:
        # one round trip EVERY session = 2 x 5bps of friction per day.
        print(row("overnight only @ 5bps/side", stats(on, 5.0, 2)))
        print(row("overnight only @ 1bp/side", stats(on, 1.0, 2)))
        # sanity: the two legs should multiply back to roughly buy-and-hold
        prod = float(((1 + on) * (1 + intra)).prod() - 1)
        print(f"  {'(on x intra) vs buy&hold':28s} {prod*100:>14,.0f}% vs "
              f"{stats(bh)['total']:,.0f}%")


if __name__ == "__main__":
    import sys
    main(sys.argv[1:] or ["MU", "SPY", "QQQ"])
