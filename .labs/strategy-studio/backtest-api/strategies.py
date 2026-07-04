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


def triple_momentum(df, params):
    """Multi-timeframe momentum: check 3-, 6-, and 12-month returns and go long
    when at least `min_agree` of them are positive. Diversifying across lookbacks
    cuts the single-horizon noise that whipsaws plain momentum — and time-series
    momentum is one of the most durable documented anomalies (his 'economic
    principles' point is fair)."""
    p1 = int(params.get("p1", 63)); p2 = int(params.get("p2", 126)); p3 = int(params.get("p3", 252))
    min_agree = int(params.get("min_agree", 2))
    close = df["Close"]
    votes = sum((close > close.shift(p)).astype(int) for p in (p1, p2, p3))
    return (votes >= min_agree).astype(int)


def ma200_timing(df, params):
    """The 200-day MA timing rule (Meb Faber): long the index when price is
    above its 200-day moving average, flat when below. One parameter, decades
    of literature — the classic 'cut the bear markets' risk-reduction overlay.
    The claim to test: similar return to buy-and-hold with far lower drawdown."""
    ma = int(params.get("ma_days", 200))
    close = df["Close"]
    return (close > close.rolling(ma).mean()).astype(int)


def dual_momentum(df, params):
    """Momentum with a trend gate: long only when price is above N-days-ago
    AND above its long MA. The MA filter cuts the whipsaw longs that hurt raw
    momentum's Sharpe in choppy/bear tape."""
    lb = int(params.get("lookback_days", 90))
    ma = int(params.get("trend_ma", 200))
    close = df["Close"]
    return ((close > close.shift(lb)) & (close > close.rolling(ma).mean())).astype(int)


def macd(df, params):
    """Long while the MACD line is above its signal line — a smoothed trend
    read that flips less often than raw price-vs-price momentum."""
    fast = int(params.get("fast", 12)); slow = int(params.get("slow", 26))
    sigp = int(params.get("signal", 9))
    close = df["Close"]
    macd_line = close.ewm(span=fast).mean() - close.ewm(span=slow).mean()
    return (macd_line > macd_line.ewm(span=sigp).mean()).astype(int)


def trend_ma(df, params):
    """Classic golden-cross: long while fast SMA > slow SMA. Fewest trades of
    the bunch — low turnover means costs barely bite."""
    fast = int(params.get("fast_ma", 50)); slow = int(params.get("slow_ma", 200))
    close = df["Close"]
    return (close.rolling(fast).mean() > close.rolling(slow).mean()).astype(int)


def momentum_12_1(df, params):
    """Academic 12-1 momentum: 12-month return skipping the most recent month
    (the skip avoids short-term reversal). The version that actually survives
    in the literature."""
    long_lb = int(params.get("long_days", 252)); skip = int(params.get("skip_days", 21))
    close = df["Close"]
    return (close.shift(skip) > close.shift(long_lb)).astype(int)


def vix_gold_filter(df, params):
    """From the 'beats NASDAQ buy-and-hold with VIX+gold correlations' video:
    stay long the symbol except in risk-off regimes — VIX above its moving
    average AND gold outperforming the symbol (flight-to-safety confirmation).
    The claim to test: tracks buy-and-hold in bull runs, sidesteps drawdowns."""
    import engine
    vix_ma = int(params.get("vix_ma_days", 50))
    mom = int(params.get("mom_days", 20))
    early = (df.index[0] - pd.Timedelta(days=400)).strftime("%Y-%m-%d")

    vix = engine.fetch("^VIX", early)["Close"].reindex(df.index).ffill()
    gold = engine.fetch("GLD", early)["Close"].reindex(df.index).ffill()

    vix_elevated = vix > vix.rolling(vix_ma).mean()
    gold_leading = gold.pct_change(mom) > df["Close"].pct_change(mom)
    risk_off = vix_elevated & gold_leading
    return (~risk_off).astype(int)


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
    "vix_gold_filter": {"fn": vix_gold_filter,
                        "grid": {"vix_ma_days": [30, 50, 100], "mom_days": [10, 20, 40]}},
    "ma200_timing": {"fn": ma200_timing, "grid": {"ma_days": [150, 200, 250]}},
    "triple_momentum": {"fn": triple_momentum,
                        "grid": {"min_agree": [2, 3], "p3": [200, 252]}},
    "dual_momentum": {"fn": dual_momentum,
                      "grid": {"lookback_days": [60, 90, 120], "trend_ma": [100, 150, 200]}},
    "macd": {"fn": macd, "grid": {"fast": [8, 12], "slow": [21, 26]}},
    "trend_ma": {"fn": trend_ma,
                 "grid": {"fast_ma": [20, 50], "slow_ma": [100, 150, 200]}},
    "momentum_12_1": {"fn": momentum_12_1,
                      "grid": {"long_days": [200, 252], "skip_days": [10, 21]}},
    "insider_form4": {"fn": insider_form4, "grid": {"hold_days": [30, 60, 90]}},
}
