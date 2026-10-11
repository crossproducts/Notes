"""Reel DeUGFf4yLX8 -- "449% in 12 months" EMA-stack pullback with a 2R bracket.

The on-screen card states the rules completely, on DAILY bars, LONG ONLY:

  1. Trend      EMA3 > EMA7 > EMA50  ("a clean uptrend stack")
  2. Volatility ATR(14) flat or falling, "not expanding ... no blow-off"
  3. Trigger    a bearish candle (close < open) inside that uptrend
  4. Bracket    next session, BUY STOP just above the trigger candle's HIGH;
                stop-loss just below its LOW; target = entry + 2R;
                "if price breaks the candle's low first ... the system resets"

That is a complete, falsifiable specification -- the first one out of the reel
queue in a dozen videos. It is NOT expressible in the engine's
`fn(df, params) -> 0/1` contract, because the fill, the stop and the target are
all INTRABAR, so it gets a harness instead of a registry entry.

Three conventions, each chosen to be pessimistic for the strategy, because the
whole question is whether a real edge survives honest assumptions:

  - a bar that touches BOTH the stop and the target resolves as the STOP
  - a bar that touches both the buy stop and the trigger low is taken as
    filled-then-stopped (-1R), not as a clean cancel
  - a gap through the buy stop fills at the OPEN, never at the stop price

Results are reported twice: raw R-multiples (sizing-independent -- the honest
view of whether there is an edge at all) and a 1%-risk-per-trade equity curve
(what a person would actually run). Costs are the engine default, 5 bps/side.

    python research/ema_pullback_check.py                  # SPY QQQ, 2000+
    python research/ema_pullback_check.py BTC-USD --start 2015-01-01
"""

import argparse
import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
for _p in (_here.parent, _here.parent / "backtest-api"):
    if (_p / "engine.py").exists():
        sys.path.insert(0, str(_p))
        break

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import engine  # noqa: E402

COST_BPS = 5.0
RISK_PCT = 0.01     # fraction of equity risked per trade
MAX_WAIT = 5        # sessions a resting buy stop stays live
MAX_HOLD = 250      # hard cap so an unresolved trade cannot run forever
TICK = 1e-4         # "just above / just below", as a fraction of price


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def wilder_atr(df, n=14):
    h, l, c = df["High"], df["Low"], df["Close"]
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


def simulate(df, cost_bps=COST_BPS, max_wait=MAX_WAIT, atr_lb=1, filters=True):
    """Walk the bars and return one record per completed trade.

    filters=False is the CONTROL arm: identical bracket, identical trigger
    candle, but without the EMA stack and the ATR condition. If the two arms
    score the same, the reel's two headline filters are decoration.
    """
    o, h, l, c = (df[k].to_numpy(float) for k in ("Open", "High", "Low", "Close"))
    e3, e7, e50 = (ema(df["Close"], n).to_numpy(float) for n in (3, 7, 50))
    a = wilder_atr(df).to_numpy(float)

    trig = (c < o)                                  # the bearish trigger candle
    if filters:
        trig &= (e3 > e7) & (e7 > e50)              # the "clean uptrend stack"
        trig[atr_lb:] &= a[atr_lb:] <= a[:-atr_lb]  # ATR flat or falling
    trig[:50] = False                               # EMA50 not warm yet

    cost = cost_bps / 1e4
    n, i, out = len(df), 0, []
    while i < n - 1:
        if not trig[i]:
            i += 1
            continue
        entry = h[i] * (1 + TICK)
        stop = l[i] * (1 - TICK)
        if not entry > stop:
            i += 1
            continue
        R = entry - stop
        target = entry + 2.0 * R

        fill_j = fill_px = None
        forced_loss = False
        for j in range(i + 1, min(i + 1 + max_wait, n)):
            hit_entry, hit_stop = h[j] >= entry, l[j] <= stop
            if hit_entry and hit_stop:              # ambiguous -> assume worst
                fill_j, fill_px, forced_loss = j, max(entry, o[j]), True
                break
            if hit_stop:                            # pullback failed, reset
                break
            if hit_entry:
                fill_j, fill_px = j, max(entry, o[j])
                break
        if fill_j is None:
            i += 1
            continue

        if forced_loss:
            exit_j, exit_px, how = fill_j, stop, "stop"
        else:
            exit_j = exit_px = how = None
            for j in range(fill_j, min(fill_j + MAX_HOLD, n)):
                if l[j] <= stop:                    # stop checked before target
                    exit_j, exit_px, how = j, min(stop, o[j]), "stop"
                    break
                if h[j] >= target:
                    exit_j, exit_px, how = j, max(target, o[j]), "target"
                    break
            if exit_j is None:
                exit_j = min(fill_j + MAX_HOLD, n) - 1
                exit_px, how = c[exit_j], "timeout"

        pnl = (exit_px - fill_px) - cost * (fill_px + exit_px)
        out.append(dict(entry_i=fill_j, exit_i=exit_j, R=R, fill=fill_px,
                        exit=exit_px, pnl_per_share=pnl, r_mult=pnl / R,
                        how=how, bars=exit_j - fill_j))
        i = exit_j + 1          # one position at a time
    return out


def equity_curve(trades, df, risk_pct=RISK_PCT, start_equity=100_000.0):
    """Fixed-fractional sizing, no leverage (notional capped at equity)."""
    eq = pd.Series(start_equity, index=df.index, dtype=float)
    cash, capped = start_equity, 0
    for t in trades:
        shares = (cash * risk_pct) / t["R"]
        if shares * t["fill"] > cash:
            shares, capped = cash / t["fill"], capped + 1
        cash += shares * t["pnl_per_share"]
        eq.iloc[t["exit_i"]:] = cash
    return eq, capped


def report(symbol, start, cost_bps=COST_BPS, filters=True, label=""):
    df = engine.fetch(symbol, start)
    if len(df) < 300:
        print(f"  {symbol}: not enough data")
        return None
    tr = simulate(df, cost_bps=cost_bps, filters=filters)
    if not tr:
        print(f"  {symbol}: no trades triggered")
        return None

    r = np.array([t["r_mult"] for t in tr])
    wins = r > 0
    eq, capped = equity_curve(tr, df)
    yrs = len(df) / 252
    ann = (eq.iloc[-1] / eq.iloc[0]) ** (1 / yrs) - 1
    dd = float((eq / eq.cummax() - 1).min() * 100)
    dr = eq.pct_change().dropna()
    sharpe = ((ann - engine.RISK_FREE_RATE) / (dr.std() * np.sqrt(252))
              if dr.std() > 0 else float("nan"))

    bh = df["Close"]
    bh_ann = (bh.iloc[-1] / bh.iloc[0]) ** (1 / yrs) - 1
    bh_eq = (1 + bh.pct_change().dropna()).cumprod()
    bh_dd = float((bh_eq / bh_eq.cummax() - 1).min() * 100)

    how = pd.Series([t["how"] for t in tr]).value_counts().to_dict()
    print(f"\n  === {symbol} {label}  {df.index[0].date()} -> {df.index[-1].date()} "
          f"({yrs:.1f}y, {cost_bps:.0f}bps/side) ===")
    print(f"    trades {len(tr)}  win {wins.mean()*100:.1f}%  "
          f"expectancy {r.mean():+.3f}R  median {np.median(r):+.3f}R")
    print(f"    exits  {how}   avg hold {np.mean([t['bars'] for t in tr]):.1f} bars")
    print(f"    strat  {ann*100:+7.2f}%/yr  total {(eq.iloc[-1]/eq.iloc[0]-1)*100:+9.1f}%"
          f"  maxDD {dd:7.2f}%  sharpe {sharpe:5.2f}")
    print(f"    B&H    {bh_ann*100:+7.2f}%/yr  total {(bh.iloc[-1]/bh.iloc[0]-1)*100:+9.1f}%"
          f"  maxDD {bh_dd:7.2f}%")
    if capped:
        print(f"    note   sizing hit the no-leverage cap on {capped} trade(s)")
    return dict(symbol=symbol, arm=label, trades=len(tr), win=wins.mean(), exp=r.mean(),
                ann=ann * 100, dd=dd, sharpe=sharpe, bh_ann=bh_ann * 100)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbols", nargs="*", default=["SPY", "QQQ"])
    ap.add_argument("--start", default="2000-01-01")
    ap.add_argument("--cost", type=float, default=COST_BPS)
    args = ap.parse_args()

    print(f"EMA3>EMA7>EMA50 + ATR(14) flat/falling + bearish candle -> "
          f"buy stop, 2R bracket\nrisk {RISK_PCT*100:.0f}%/trade, "
          f"excess sharpe vs {engine.RISK_FREE_RATE*100:.1f}% risk-free")

    # Three arms: the rules as stated, the same thing gross, and a control that
    # keeps the bracket but drops the two filters the reel says are the edge.
    arms = [(args.cost, True, "[as stated]"),
            (0.0, True, "[gross 0bps]"),
            (args.cost, False, "[CONTROL no EMA/ATR]")]
    rows = [x for sym in args.symbols for x in
            [report(sym, args.start, c, f, lab) for c, f, lab in arms] if x]

    print("\n  === summary ===")
    print(f"  {'symbol':<9}{'arm':<23}{'trades':>7}{'win%':>7}{'exp(R)':>9}"
          f"{'ann%':>8}{'B&H%':>8}{'maxDD%':>9}{'sharpe':>8}")
    for r in rows:
        print(f"  {r['symbol']:<9}{r['arm']:<23}{r['trades']:>7}{r['win']*100:>7.1f}"
              f"{r['exp']:>+9.3f}{r['ann']:>8.2f}{r['bh_ann']:>8.2f}"
              f"{r['dd']:>9.2f}{r['sharpe']:>8.2f}")
    print("\n  A 2R bracket breaks even at a 33.3% win rate -- which is also what a"
          "\n  driftless random walk gives. Read win% against 33.3, not against 50.")


if __name__ == "__main__":
    main()
