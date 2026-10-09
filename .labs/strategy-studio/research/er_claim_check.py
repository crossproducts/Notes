"""Falsification harness for the Efficiency-Ratio Forecast Gate (reel DeF5_5yPtDb).

Tests the reel's claims separately from any one application of them:

  1. Does the model predict next-day efficiency at all?  (OOS AUC / accuracy)
  2. Does predicted efficiency sort outcomes monotonically into terciles,
     the way the reel's low/medium/high table claims?
  3. Does gating the bottom tercile help, across several base strategies?

Everything is strictly out-of-sample: expanding-window refit, training-only
standardisation, training-only tercile cuts.
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
import strategies as S


def oos_predictions(df, min_train=756, refit_days=252):
    """OOS P(high efficiency tomorrow) + the realised next-day efficiency."""
    feats, eff = S._eff_features(df)
    X = feats.to_numpy(dtype=float)
    y_eff = eff.shift(-1).to_numpy(dtype=float)
    ok = np.isfinite(X).all(axis=1) & np.isfinite(y_eff)

    n = len(df)
    p_out = np.full(n, np.nan)
    lbl_out = np.full(n, np.nan)
    idx = np.arange(n)

    start = min_train
    while start < n:
        end = min(start + refit_days, n)
        tr = ok & (idx < start)
        te = ok & (idx >= start) & (idx < end)
        if tr.sum() >= 250 and te.any():
            Xtr = X[tr]
            mu, sd = Xtr.mean(0), Xtr.std(0)
            sd[sd == 0] = 1.0
            thr = np.quantile(y_eff[tr], 2 / 3)
            w = S._fit_logistic((Xtr - mu) / sd, (y_eff[tr] >= thr).astype(float))
            p_out[idx[te]] = S._logistic_p(w, (X[te] - mu) / sd)
            lbl_out[idx[te]] = (y_eff[te] >= thr).astype(float)
        start = end

    return pd.Series(p_out, index=df.index), pd.Series(lbl_out, index=df.index)


def auc(y, p):
    m = np.isfinite(y) & np.isfinite(p)
    y, p = y[m], p[m]
    if len(np.unique(y)) < 2:
        return float("nan")
    r = pd.Series(p).rank().to_numpy()
    n1, n0 = y.sum(), (1 - y).sum()
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def bucket_stats(rets):
    rets = rets[np.isfinite(rets)]
    if len(rets) == 0:
        return dict(days=0, mean_bps=np.nan, win=np.nan, pf=np.nan)
    gains, losses = rets[rets > 0].sum(), -rets[rets < 0].sum()
    return dict(
        days=len(rets),
        mean_bps=rets.mean() * 1e4,
        win=(rets > 0).mean() * 100,
        pf=(gains / losses) if losses > 0 else float("inf"),
    )


def main(symbol="SPY", start="2010-01-01"):
    df = engine.fetch(symbol, start)
    close = df["Close"]
    fwd = close.pct_change().shift(-1)          # tomorrow's return

    p, lbl = oos_predictions(df)
    print(f"=== {symbol} {start} .. {df.index[-1].date()}  ({len(df)} bars) ===\n")

    # --- Claim 1: does the model predict efficiency at all? -----------------
    a = auc(lbl.to_numpy(), p.to_numpy())
    m = np.isfinite(p) & np.isfinite(lbl)
    acc = ((p[m] >= 0.5).astype(float) == lbl[m]).mean() * 100
    base_rate = lbl[m].mean() * 100
    print("CLAIM 1 - does it predict next-day efficiency?")
    print(f"  OOS AUC            {a:.3f}   (0.50 = coin flip)")
    print(f"  OOS accuracy       {acc:.1f}%  (base rate {base_rate:.1f}%)")
    print(f"  scored days        {int(m.sum())}\n")

    # --- Claim 2: monotonic tercile sort ------------------------------------
    print("CLAIM 2 - does predicted efficiency sort next-day outcomes?")
    pv = p[m]
    q1, q2 = pv.quantile(1 / 3), pv.quantile(2 / 3)
    names = ["LOW ", "MED ", "HIGH"]
    masks = [m & (p <= q1), m & (p > q1) & (p <= q2), m & (p > q2)]

    print(f"  {'bucket':6s} {'days':>5s} {'realised eff':>13s} "
          f"{'buy&hold bps':>13s} {'win%':>6s} {'PF':>6s}")
    for nm, mk in zip(names, masks):
        eff_real = lbl[mk].mean() * 100          # share that WERE high-efficiency
        st = bucket_stats(fwd[mk].to_numpy())
        print(f"  {nm:6s} {st['days']:5d} {eff_real:12.1f}% "
              f"{st['mean_bps']:13.2f} {st['win']:6.1f} {st['pf']:6.3f}")

    # --- Claim 3: gating several base strategies ----------------------------
    print("\nCLAIM 3 - does gating the bottom tercile help a strategy?")
    print(f"  {'base':16s} {'variant':10s} {'ret%':>9s} {'sharpe':>7s} "
          f"{'maxDD%':>8s} {'switches':>9s}")
    for base in ("momentum", "mean_reversion", "breakout", "trend_ma", "macd"):
        sig = S.REGISTRY[base]["fn"](df, {"_symbol": symbol}).astype(int)
        gate = (p > q1).astype(int)
        gate[~m] = 1                              # warm-up passes through
        for variant, s in (("base", sig), ("gated", sig * gate)):
            eq, _ = engine.equity_from_signal(close, s, cost_bps=5, open_=df.get("Open"))
            met = engine.metrics(eq, s, close)
            print(f"  {base:16s} {variant:10s} {met['total_return_pct']:9.1f} "
                  f"{met['sharpe']:7.2f} {met['max_drawdown_pct']:8.1f} "
                  f"{int((s.diff().abs() > 0).sum()):9d}")


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "SPY")
