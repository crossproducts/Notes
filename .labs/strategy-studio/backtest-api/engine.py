"""Core backtest engine: signal -> equity, with risk controls, regime filter,
benchmarks, and shared metrics."""

import os

import numpy as np
import pandas as pd
import yfinance as yf

_data_cache = {}


def fetch(symbol: str, start: str) -> pd.DataFrame:
    key = (symbol, start)
    if key not in _data_cache:
        df = yf.download(symbol, start=start, progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        _data_cache[key] = df
    return _data_cache[key]


def regime_mask(index: pd.DatetimeIndex, start: str) -> pd.Series:
    """Bull-regime mask: SPY above its 200-day MA (computed with extra history)."""
    early = (pd.Timestamp(start) - pd.Timedelta(days=400)).strftime("%Y-%m-%d")
    spy = fetch("SPY", early)["Close"]
    bull = (spy > spy.rolling(200).mean()).astype(int)
    return bull.reindex(index).ffill().fillna(0)


RISK_FREE_RATE = float(os.getenv("RISK_FREE_RATE", "0.042"))  # annual; ~current T-bill/HYSA


def equity_from_signal(close: pd.Series, signal: pd.Series,
                       position_size_pct: float = 100.0,
                       max_dd_stop_pct: float | None = None,
                       cost_bps: float = 5.0,
                       risk_free_rate: float | None = None,
                       initial: float = 100_000.0):
    """Risk engine: position sizing, max-drawdown circuit breaker, transaction
    COSTS (cost_bps/side), and RISK-FREE ACCRUAL on idle capital — cash out of
    the market (and the un-invested fraction) earns the risk-free rate, exactly
    as real trend-timing models park in T-bills. Without this, sit-in-cash
    strategies are badly under-credited. Signal shifted 1 bar — no lookahead."""
    rf = RISK_FREE_RATE if risk_free_rate is None else risk_free_rate
    rf_daily = (1 + rf) ** (1 / 252) - 1
    sig = signal.shift(1).fillna(0).values
    rets = close.pct_change().fillna(0).values
    w = position_size_pct / 100.0
    cost = cost_bps / 10_000.0 * w

    eq = np.empty(len(rets))
    e, peak, halted, prev = initial, initial, False, 0.0
    for i in range(len(rets)):
        if not halted and sig[i] != prev:   # position change = pay the spread
            e *= (1 - cost)
            prev = sig[i]
        invested = w if (not halted and sig[i] > 0) else 0.0
        # invested fraction earns the market; the rest earns risk-free
        e *= (1 + rets[i] * invested + rf_daily * (1 - invested))
        peak = max(peak, e)
        if max_dd_stop_pct and (e - peak) / peak * 100 <= -abs(max_dd_stop_pct):
            halted = True  # circuit breaker: flat (earning rf) for the rest
        eq[i] = e
    return pd.Series(eq, index=close.index), halted


def metrics(equity: pd.Series, signal: pd.Series, close: pd.Series,
            risk_free_rate: float | None = None) -> dict:
    rf = RISK_FREE_RATE if risk_free_rate is None else risk_free_rate
    rf_daily = (1 + rf) ** (1 / 252) - 1
    rets = equity.pct_change().fillna(0)
    peak = equity.cummax()
    max_dd = float(((equity - peak) / peak).min() * 100)
    active = rets[signal.shift(1).fillna(0) > 0]
    # EXCESS-return Sharpe: reward only performance ABOVE the risk-free rate.
    # In a ~4% world, raw Sharpe flatters everything; this is the honest hurdle.
    sharpe = float((rets.mean() - rf_daily) / rets.std() * np.sqrt(252)) if rets.std() > 0 else 0.0
    return {
        "total_return_pct": round(float(equity.iloc[-1] / equity.iloc[0] - 1) * 100, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "sharpe": round(sharpe, 2),
        "trades": int(signal.diff().abs().sum() / 2),
        "win_rate": round(float((active > 0).sum() / max(len(active), 1) * 100), 1),
    }


def benchmarks(symbol: str, index: pd.DatetimeIndex, start: str) -> dict:
    """Buy-and-hold of the same symbol, of SPY, and 'just hold cash' at the
    risk-free rate over the identical window — a strategy that can't beat the
    risk-free line has no business holding your money."""
    out = {}
    for name, sym in (("benchmark_return_pct", symbol), ("spy_return_pct", "SPY")):
        c = fetch(sym, start)["Close"].reindex(index).ffill().dropna()
        out[name] = round(float(c.iloc[-1] / c.iloc[0] - 1) * 100, 2) if len(c) > 1 else None
    years = max((index[-1] - index[0]).days / 365.25, 1e-9)
    out["risk_free_return_pct"] = round(((1 + RISK_FREE_RATE) ** years - 1) * 100, 2)
    return out


def benchmark_curves(symbol: str, index: pd.DatetimeIndex, start: str,
                     initial: float = 100_000.0) -> dict[str, pd.Series]:
    """Buy-and-hold equity curves (same starting capital) for overlaying the
    strategy's curve in Grafana: 'buyhold_<symbol>' and 'buyhold_SPY'."""
    out = {}
    for sym in dict.fromkeys([symbol, "SPY"]):  # dedupe, keep order
        c = fetch(sym, start)["Close"].reindex(index).ffill().dropna()
        if len(c) > 1:
            out[f"buyhold_{sym}"] = c / c.iloc[0] * initial
    # risk-free growth line for the same dates
    rf_daily = (1 + RISK_FREE_RATE) ** (1 / 252) - 1
    out["risk_free"] = pd.Series(initial * (1 + rf_daily) ** np.arange(len(index)), index=index)
    return out
