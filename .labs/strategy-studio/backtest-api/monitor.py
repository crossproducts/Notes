"""Forward-decay monitor: is a champion still behaving like its backtest?

Compares the strategy's performance in a RECENT trailing window against its own
longer-run baseline (both cost-adjusted, same engine). This answers "is it still
good NOW" without waiting for live paper P&L to accumulate — the recent window
is the freshest evidence we have, judged against the strategy's historical norm.

Decay = the recent window is materially worse than the baseline:
  - recent Sharpe < DECAY_FRAC of baseline Sharpe, OR
  - recent drawdown deeper than the full-history max drawdown (regime it never saw)
"""

import numpy as np
import pandas as pd

import engine
from strategies import REGISTRY

DECAY_FRAC = 0.5  # recent Sharpe below half the baseline = flag


def _sharpe(r: pd.Series) -> float:
    return float(r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else 0.0


def _annual(r: pd.Series) -> float:
    if len(r) == 0:
        return 0.0
    return float((1 + r).prod() ** (252 / len(r)) - 1) * 100


def _maxdd(eq: pd.Series) -> float:
    peak = eq.cummax()
    return float(((eq - peak) / peak).min() * 100)


def monitor(strategy: str, symbol: str, params: dict,
            window_days: int = 63, cost_bps: float = 5.0) -> dict:
    """window_days=63 ~ one quarter of trading days."""
    if strategy not in REGISTRY:
        return {"symbol": symbol, "strategy": strategy, "verdict": "unmonitorable",
                "note": "champion is an imported/video strategy — no recompute path"}

    df = engine.fetch(symbol, "2017-01-01")
    signal = REGISTRY[strategy]["fn"](df, {**(params or {}), "_symbol": symbol})
    equity, _ = engine.equity_from_signal(df["Close"], signal, cost_bps=cost_bps)
    rets = equity.pct_change().dropna()
    if len(rets) < window_days + 120:
        return {"symbol": symbol, "strategy": strategy, "verdict": "insufficient_data",
                "note": f"need >{window_days + 120} bars, have {len(rets)}"}

    baseline = rets.iloc[:-window_days]
    recent = rets.iloc[-window_days:]
    recent_eq = equity.iloc[-window_days:]

    base_sharpe = _sharpe(baseline)
    rec_sharpe = _sharpe(recent)
    # compare recent drawdown against the BASELINE period's worst — NOT the full
    # curve (which contains the recent window, making a breach near-impossible).
    base_maxdd = _maxdd(equity.iloc[:-window_days])
    rec_maxdd = _maxdd(recent_eq)

    flags = []
    if base_sharpe > 0 and rec_sharpe < DECAY_FRAC * base_sharpe:
        flags.append(f"sharpe_decay (recent {rec_sharpe:.2f} < {DECAY_FRAC}x baseline {base_sharpe:.2f})")
    if rec_maxdd < base_maxdd:
        flags.append(f"drawdown_breach (recent {rec_maxdd:.1f}% worse than baseline worst {base_maxdd:.1f}%)")

    ratio = round(rec_sharpe / base_sharpe, 2) if base_sharpe > 0 else None
    return {
        "symbol": symbol, "strategy": strategy,
        "window_days": window_days,
        "baseline_sharpe": round(base_sharpe, 2),
        "recent_sharpe": round(rec_sharpe, 2),
        "live_vs_expected_ratio": ratio,
        "recent_annual_return_pct": round(_annual(recent), 2),
        "baseline_annual_return_pct": round(_annual(baseline), 2),
        "recent_drawdown_pct": round(rec_maxdd, 2),
        "baseline_max_drawdown_pct": round(base_maxdd, 2),
        "flags": flags,
        "verdict": "DECAY" if flags else "healthy",
    }
