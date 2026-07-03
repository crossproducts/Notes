"""Strategy registry. Each strategy: fn(df, params) -> 0/1 signal Series.
GRID drives walk-forward optimization. The engine shifts signals by 1 bar,
so strategies may use same-bar closes without lookahead."""

import numpy as np
import pandas as pd

import edgar


def _stateful(entries: pd.Series, exits: pd.Series) -> pd.Series:
    """Entry/exit events -> held-position signal (enter on entry, flat on exit)."""
    state = pd.Series(np.nan, index=entries.index)
    state[entries] = 1.0
    state[exits] = 0.0
    return state.ffill().fillna(0)


def momentum(df, params):
    lb = int(params.get("lookback_days", 90))
    close = df["Close"]
    return (close > close.shift(lb)).astype(int)


def mean_reversion(df, params):
    period = int(params.get("rsi_period", 14))
    oversold = float(params.get("oversold", 30))
    exit_level = float(params.get("exit_level", 55))
    close = df["Close"]
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rsi = 100 - 100 / (1 + gain / loss)
    return _stateful(rsi < oversold, rsi > exit_level)


def breakout(df, params):
    entry_n = int(params.get("entry_days", 55))
    exit_n = int(params.get("exit_days", 20))
    close = df["Close"]
    hi = close.rolling(entry_n).max().shift(1)
    lo = close.rolling(exit_n).min().shift(1)
    return _stateful(close > hi, close < lo)


def bollinger_squeeze(df, params):
    """Squeeze breakout (B-tier in the tier-list video): enter when price breaks
    the upper band WHILE bandwidth is in its tightest quantile (volatility
    compression -> expansion); exit on close below the mid band."""
    n = int(params.get("bb_period", 20))
    k = float(params.get("bb_std", 2.0))
    sq_win = int(params.get("squeeze_window", 120))
    sq_q = float(params.get("squeeze_q", 0.2))
    close = df["Close"]
    mid = close.rolling(n).mean()
    sd = close.rolling(n).std()
    upper = mid + k * sd
    bw = (2 * k * sd) / mid
    squeeze = bw <= bw.rolling(sq_win).quantile(sq_q)
    entries = (close > upper) & squeeze.shift(1).fillna(False)
    exits = close < mid
    return _stateful(entries, exits)


def insider_form4(df, params):
    """Long for hold_days after any insider open-market purchase (SEC Form 4).
    First run per ticker is slow (EDGAR scan), then cached."""
    hold = int(params.get("hold_days", 90))
    symbol = params.get("_symbol", "AAPL")
    dates = edgar.purchase_filing_dates(symbol, int(params.get("max_filings", 80)))
    sig = pd.Series(0, index=df.index)
    for d in dates:
        ts = pd.Timestamp(d)
        sig[(df.index >= ts) & (df.index <= ts + pd.Timedelta(days=hold))] = 1
    return sig


REGISTRY = {
    "momentum": {"fn": momentum, "grid": {"lookback_days": [60, 90, 120, 180]}},
    "mean_reversion": {"fn": mean_reversion,
                       "grid": {"oversold": [25, 30, 35], "exit_level": [50, 55, 60]}},
    "breakout": {"fn": breakout,
                 "grid": {"entry_days": [40, 55, 70], "exit_days": [15, 20, 30]}},
    "bollinger_squeeze": {"fn": bollinger_squeeze,
                          "grid": {"bb_period": [15, 20, 25], "squeeze_q": [0.15, 0.2, 0.3]}},
    "insider_form4": {"fn": insider_form4, "grid": {"hold_days": [30, 60, 90]}},
}
