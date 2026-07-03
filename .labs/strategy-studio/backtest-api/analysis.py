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
            eq, _ = engine.equity_from_signal(train["Close"], sig)
            r = eq.iloc[-1] / eq.iloc[0] - 1
            if r > best_ret:
                best_ret, best_params = r, params

        p = {**best_params, "_symbol": symbol}
        sig = spec["fn"](pd.concat([train, test]), p).loc[test.index]
        eq, _ = engine.equity_from_signal(test["Close"], sig)
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
