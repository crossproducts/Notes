"""E6: re-run champion selection over a FULL market cycle.

Every run in the registry starts 2020-01-01 -- a 6.5-year window containing one
brief bear (2022). The champion was therefore chosen on a sample that may simply
favour it. This re-ranks every builtin over windows that include 2000-02, 2008
and 2020, and checks whether the ranking is stable.

Two data traps this handles explicitly, because they fail SILENTLY:
  - GLD starts 2004-11-18 and EEM 2003-04-14. `vix_gold_filter` and
    `rotation_top_k` reindex+ffill those, so before inception the comparison is
    NaN -> False -> "not risk off" -> permanently long. The strategy quietly
    becomes buy-and-hold for the first five years and looks great.
    They are therefore only scored from 2005.
  - SLOW_STRATEGIES (EDGAR) are excluded: rate-limited, not window-comparable.

Usage (research/ is mounted read-only at /app/research):
    docker compose exec -T api python /app/research/champion_full_cycle.py
"""

import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
for _p in (_here.parent, _here.parent / "backtest-api"):
    if (_p / "engine.py").exists():
        sys.path.insert(0, str(_p))
        break

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import analysis  # noqa: E402
import engine  # noqa: E402
import strategies as S  # noqa: E402

SYMBOL = "SPY"
COST = 5.0
# Strategies whose auxiliary data does not exist before 2005; scoring them
# earlier silently measures buy-and-hold instead.
DATA_LIMITED = {"vix_gold_filter": "2005-01-01", "rotation_top_k": "2005-01-01"}
WINDOWS = [("2000-01-01", "full cycle (2000-02, 2008, 2020, 2022)"),
           ("2007-01-01", "GFC onward (2008, 2020, 2022)"),
           ("2020-01-01", "champion window (2022 only)")]


def score(name, start):
    df = engine.fetch(SYMBOL, start)
    if len(df) < 300:
        return None
    sig = S.REGISTRY[name]["fn"](df, {"_symbol": SYMBOL})
    eq, halted = engine.equity_from_signal(df["Close"], sig, cost_bps=COST,
                                           open_=df.get("Open"))
    m = engine.metrics(eq, sig, df["Close"])
    yrs = len(df) / 252
    ann = (eq.iloc[-1] / eq.iloc[0]) ** (1 / yrs) - 1
    return dict(sharpe=m["sharpe"], total=m["total_return_pct"],
                ann=ann * 100, dd=m["max_drawdown_pct"],
                switches=int((sig.diff().abs() > 0).sum()), yrs=yrs)


def buyhold(start):
    df = engine.fetch(SYMBOL, start)
    c = df["Close"]
    r = c.pct_change().dropna()
    yrs = len(c) / 252
    ann = (c.iloc[-1] / c.iloc[0]) ** (1 / yrs) - 1
    vol = r.std() * np.sqrt(252)
    eq = (1 + r).cumprod()
    return dict(sharpe=(ann - engine.RISK_FREE_RATE) / vol,
                total=(c.iloc[-1] / c.iloc[0] - 1) * 100, ann=ann * 100,
                dd=float((eq / eq.cummax() - 1).min() * 100), switches=0, yrs=yrs)


def main():
    names = [n for n in S.REGISTRY if n not in S.SLOW_STRATEGIES]
    print(f"{SYMBOL}, {COST}bps/side, excess sharpe vs "
          f"{engine.RISK_FREE_RATE*100:.1f}% risk-free\n")

    table = {}
    for start, label in WINDOWS:
        print(f"=== {label}  (from {start}) ===")
        rows = []
        for n in names:
            eff = DATA_LIMITED.get(n)
            if eff and eff > start:
                rows.append((n, None, f"skipped - aux data starts {eff}"))
                continue
            try:
                rows.append((n, score(n, start), ""))
            except Exception as e:
                rows.append((n, None, f"ERROR {type(e).__name__}"))
        bh = buyhold(start)
        rows.append(("BUY & HOLD", bh, "<- the bar"))

        ok = [(n, r, note) for n, r, note in rows if r]
        ok.sort(key=lambda x: -x[1]["sharpe"])
        print(f"  {'rank':>4} {'strategy':<20} {'sharpe':>7} {'ann%':>7} "
              f"{'total%':>9} {'maxDD%':>8} {'switch':>7}")
        for i, (n, r, note) in enumerate(ok, 1):
            star = " *" if n == "BUY & HOLD" else "  "
            print(f"  {i:>4}{star}{n:<20} {r['sharpe']:>7.2f} {r['ann']:>7.2f} "
                  f"{r['total']:>9.1f} {r['dd']:>8.1f} {r['switches']:>7}  {note}")
        for n, r, note in rows:
            if not r:
                print(f"       {n:<20} {note}")
        table[start] = {n: r["sharpe"] for n, r, _ in ok}
        print()

    # --- rank stability -----------------------------------------------------
    print("=== rank stability across windows (sharpe) ===")
    common = set.intersection(*(set(v) for v in table.values()))
    print(f"  {'strategy':<20} " + " ".join(f"{s[:4]:>9}" for s, _ in WINDOWS) + "   spread")
    for n in sorted(common, key=lambda x: -table[WINDOWS[0][0]].get(x, -9)):
        vals = [table[s].get(n) for s, _ in WINDOWS]
        print(f"  {n:<20} " + " ".join(f"{v:>9.2f}" for v in vals)
              + f"   {max(vals)-min(vals):>6.2f}")


if __name__ == "__main__":
    main()
