"""Walk-forward validation and Monte Carlo resampling."""

import itertools

import numpy as np
import pandas as pd

import engine
from strategies import REGISTRY


def _combos(grid: dict):
    keys = list(grid.keys())
    for vals in itertools.product(*grid.values()):
        yield dict(zip(keys, vals))


def walkforward(strategy: str, symbol: str, start: str,
                train_years: int = 2, test_months: int = 6) -> dict:
    """Rolling anti-overfitting check: optimize params on a train window, apply
    them UNSEEN on the following test window, roll forward, stitch the
    out-of-sample segments. If OOS falls apart vs in-sample, it's curve-fit."""
    spec = REGISTRY[strategy]
    df = engine.fetch(symbol, start)
    if len(df) < 300:
        raise ValueError("not enough data")

    train_bars = train_years * 252
    test_bars = int(test_months * 21)
    windows, oos_factor = [], 1.0

    i = train_bars
    while i + 20 < len(df):
        train, test = df.iloc[i - train_bars:i], df.iloc[i:i + test_bars]
        best_params, best_ret = None, -np.inf
        for params in _combos(spec["grid"]):
            p = {**params, "_symbol": symbol}
            sig = spec["fn"](train, p)
            eq, _ = engine.equity_from_signal(train["Close"], sig, open_=train.get("Open"))
            r = eq.iloc[-1] / eq.iloc[0] - 1
            if r > best_ret:
                best_ret, best_params = r, params

        p = {**best_params, "_symbol": symbol}
        sig = spec["fn"](pd.concat([train, test]), p).loc[test.index]
        eq, _ = engine.equity_from_signal(test["Close"], sig, open_=test.get("Open"))
        oos_ret = eq.iloc[-1] / eq.iloc[0] - 1
        oos_factor *= (1 + oos_ret)
        windows.append({
            "test_start": str(test.index[0].date()), "test_end": str(test.index[-1].date()),
            "chosen_params": best_params,
            "train_return_pct": round(float(best_ret) * 100, 2),
            "oos_return_pct": round(float(oos_ret) * 100, 2),
        })
        i += test_bars

    return {
        "strategy": strategy, "symbol": symbol,
        "windows": windows,
        "stitched_oos_return_pct": round((oos_factor - 1) * 100, 2),
        "verdict": ("params unstable across windows — likely curve-fit"
                    if len({str(w["chosen_params"]) for w in windows}) == len(windows) and len(windows) > 2
                    else "params reasonably stable"),
    }


def montecarlo(equity: pd.Series, n_paths: int = 1000) -> dict:
    """Bootstrap-resample daily returns: the DISTRIBUTION of outcomes this
    strategy could have produced, not the one lucky path that happened."""
    rets = equity.pct_change().dropna().values
    if len(rets) < 30:
        raise ValueError("not enough return observations")
    rng = np.random.default_rng(42)
    idx = rng.integers(0, len(rets), size=(n_paths, len(rets)))
    paths = np.cumprod(1 + rets[idx], axis=1)
    finals = (paths[:, -1] - 1) * 100
    peaks = np.maximum.accumulate(paths, axis=1)
    dds = ((paths - peaks) / peaks).min(axis=1) * 100

    pct = lambda a, q: round(float(np.percentile(a, q)), 2)
    return {
        "n_paths": n_paths,
        "final_return_pct": {"p5": pct(finals, 5), "p50": pct(finals, 50), "p95": pct(finals, 95)},
        "max_drawdown_pct": {"p5": pct(dds, 5), "p50": pct(dds, 50), "p95": pct(dds, 95)},
        "prob_negative_pct": round(float((finals < 0).mean() * 100), 1),
    }


# --- E6: regime-robust champion scoring --------------------------------------
# A champion picked from one 6.5-year window is an artifact of that window.
# Measured 2020+, `momentum` scores sharpe 0.95 and ranks #1; measured 2000+ it
# scores 0.23 and ranks #9, below buy-and-hold. Rank on the WORST window a
# strategy has been measured in, not the luckiest one.

# Windows must span >= 2 bear markets between them.
#   2000 -> dot-com, GFC, COVID, 2022      2007 -> GFC, COVID, 2022
#   2020 -> 2022 only (kept for continuity with the old single-window view)
ROBUST_WINDOWS = ["2000-01-01", "2007-01-01", "2020-01-01"]

# Auxiliary-data inception. Before these dates the strategy reindex+ffills a
# series that does not exist yet -> NaN -> comparison False -> permanently long.
# It silently becomes buy-and-hold and scores beautifully. Do not score it there.
DATA_FLOOR = {"vix_gold_filter": "2005-01-01", "rotation_top_k": "2005-01-01"}


def _window_sharpe(strategy: str, symbol: str, start: str, cost_bps: float):
    df = engine.fetch(symbol, start)
    if len(df) < 300:
        return None
    sig = REGISTRY[strategy]["fn"](df, {"_symbol": symbol})
    eq, _ = engine.equity_from_signal(df["Close"], sig, cost_bps=cost_bps,
                                      open_=df.get("Open"))
    m = engine.metrics(eq, sig, df["Close"])
    c = df["Close"]
    yrs = len(df) / 252
    bh_ann = (c.iloc[-1] / c.iloc[0]) ** (1 / yrs) - 1
    bh_vol = c.pct_change().dropna().std() * np.sqrt(252)
    bh_sharpe = (bh_ann - engine.RISK_FREE_RATE) / bh_vol if bh_vol else float("nan")
    return {"sharpe": m["sharpe"], "buyhold_sharpe": round(float(bh_sharpe), 2),
            "beats_buyhold": bool(m["sharpe"] > bh_sharpe),
            "max_drawdown_pct": m["max_drawdown_pct"],
            "switches": int((sig.diff().abs() > 0).sum())}


def robust_score(strategy: str, symbol: str, cost_bps: float = 5.0) -> dict:
    """Score a strategy across regimes. `robust_sharpe` is the WORST window.

    Also reports whether it clears buy-and-hold in EVERY window -- the bar that
    separates a real timing rule from one that only looked good in a bull run.
    """
    floor = DATA_FLOOR.get(strategy)
    per = {}
    for w in ROBUST_WINDOWS:
        if floor and floor > w:
            per[w] = {"skipped": f"aux data starts {floor}"}
            continue
        try:
            r = _window_sharpe(strategy, symbol, w, cost_bps)
            if r:
                per[w] = r
        except Exception as e:
            per[w] = {"error": type(e).__name__}

    scored = [v for v in per.values() if "sharpe" in v]
    if not scored:
        return {"strategy": strategy, "robust_sharpe": None, "windows": per,
                "note": "not scoreable on any window"}
    sharpes = [v["sharpe"] for v in scored]
    return {
        "strategy": strategy,
        "robust_sharpe": round(min(sharpes), 2),       # worst regime
        "best_sharpe": round(max(sharpes), 2),
        "spread": round(max(sharpes) - min(sharpes), 2),
        "beats_buyhold_all_windows": all(v["beats_buyhold"] for v in scored),
        "windows_scored": len(scored),
        "windows": per,
    }


def rank_robust(symbol: str, cost_bps: float = 5.0, exclude: set | None = None):
    """Every builtin ranked by worst-window sharpe."""
    exclude = exclude or set()
    out = [robust_score(n, symbol, cost_bps)
           for n in REGISTRY if n not in exclude]
    out = [o for o in out if o.get("robust_sharpe") is not None]
    out.sort(key=lambda o: -o["robust_sharpe"])
    return out
