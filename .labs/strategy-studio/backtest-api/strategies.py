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


def turnaround_tuesday(df, params):
    """Monday close below its 25-day SMA -> hold Tuesday only. Long only.

    From reel Ddw5W-VRfE7 (italian_founder), strategy #2, stated for US30.
    The engine shifts signals by one bar, so flagging MONDAY puts the position
    on during TUESDAY and flat again on Wednesday -- exactly the stated rule,
    with no lookahead.

    The source specifies "no stop, no target", which is why there is no exit
    parameter here: the exit is the calendar.
    """
    sma_days = int(params.get("sma_days", 25))
    close = df["Close"]
    sma = close.rolling(sma_days).mean()
    is_monday = pd.Series(df.index.dayofweek == 0, index=df.index)
    return (is_monday & (close < sma)).astype(int)



def halloween(df, params):
    """Long Nov-Apr, flat (earning risk-free) May-Oct. Two trades a year.

    Bouman & Jacobsen (2002) and Zhang & Jacobsen (2021, "everywhere and all
    the time") document this across 37 countries; the 2021 out-of-sample window
    (1998-2017) still beat buy-and-hold in 30 of 37, and the effect survives
    transaction costs -- which matters here, because cost is what killed the
    last three candidates we tested.

    Two properties make it worth a slot in THIS registry specifically:
      - ~2 trades/year, so the 5bps/side that destroyed the overnight effect
        (-99%) and turnaround_tuesday (95% of edge) is a rounding error.
      - the signal is the CALENDAR, not price, so it is structurally
        uncorrelated with the momentum/trend family that dominates the book.
    """
    start_m = int(params.get("start_month", 11))   # November
    end_m = int(params.get("end_month", 4))        # through April
    m = pd.Series(df.index.month, index=df.index)
    if start_m > end_m:                            # wraps the year end
        inseason = (m >= start_m) | (m <= end_m)
    else:
        inseason = (m >= start_m) & (m <= end_m)
    return inseason.astype(int)


def halloween_trend(df, params):
    """Halloween seasonality AND price above its long MA.

    The pure calendar rule holds you through Nov-Apr bear legs regardless. This
    gates it on trend so the seasonal window is only taken when the tape agrees
    -- still low turnover, but it can sidestep a seasonal window that is
    falling apart (2008-09 being the obvious case).
    """
    ma = int(params.get("ma_days", 200))
    close = df["Close"]
    return (halloween(df, params) & (close > close.rolling(ma).mean())).astype(int)


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


def rotation_top_k(df, params):
    """Cross-sectional rotation (relative strength): long THIS symbol only
    while its trailing return ranks in the top-k of a diversified universe,
    with an absolute filter requiring the return also be positive (Antonacci
    dual momentum). A different MECHANISM than timing one chart — cross-asset
    ranking — so its curve decorrelates from the single-symbol momentum family
    that dominates this registry."""
    import engine
    universe = [s.strip().upper() for s in
                str(params.get("universe", "SPY,QQQ,IWM,EFA,EEM,GLD,TLT")).split(",")
                if s.strip()]
    sym = str(params.get("_symbol", "SPY")).upper()
    if sym not in universe:
        universe.insert(0, sym)
    lb = int(params.get("lookback_days", 90))
    k = int(params.get("top_k", 3))
    abs_filter = bool(params.get("abs_filter", True))

    early = (df.index[0] - pd.Timedelta(days=400)).strftime("%Y-%m-%d")
    closes = {}
    for s in universe:
        try:
            c = engine.fetch(s, early)["Close"].reindex(df.index).ffill()
            if c.notna().sum() > lb:
                closes[s] = c
        except Exception:
            continue  # yfinance miss — drop from the universe, don't crash
    if sym not in closes:
        return pd.Series(0, index=df.index)

    rets = pd.DataFrame(closes).pct_change(lb)
    ranks = rets.rank(axis=1, ascending=False)
    sig = ranks[sym] <= k
    if abs_filter:
        sig &= rets[sym] > 0
    return sig.fillna(False).astype(int)


def whale_13f(df, params):
    """13F whale copycat: long while the chosen fund's most recent 13F-HR
    lists the symbol among its holdings; flat once a filing drops it. Signals
    change on FILING dates (not quarter-end), so the legal ~45-day disclosure
    lag is modeled honestly — the backtest never knows more than the market
    did. Default whale: Berkshire Hathaway. First run per fund/symbol is slow
    (EDGAR scan), then disk-cached."""
    symbol = params.get("_symbol", "AAPL")
    cik = params.get("fund_cik", 1067983)  # Berkshire Hathaway
    try:
        periods = edgar.thirteenf_holding_periods(cik, symbol,
                                                  int(params.get("max_filings", 12)))
    except Exception as e:
        print(f"[whale_13f] WARNING: EDGAR unavailable ({e}) — staying flat")
        periods = []
    state = pd.Series(np.nan, index=df.index)
    for fdate, held in periods:  # ascending; later filings overwrite same-bar earlier ones
        pos = df.index.searchsorted(pd.Timestamp(fdate))
        if pos < len(df.index):
            state.iloc[pos] = 1.0 if held else 0.0
    return state.ffill().fillna(0).astype(int)


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


# --- Efficiency-Ratio forecast gate (reel DeF5_5yPtDb) -----------------------
# A meta-filter, not a strategy. A logistic regression predicts whether TOMORROW
# is a clean directional session (high efficiency) or chop, from the 15
# measurements named in the reel; the forecast gates a base strategy so the
# predicted-chop days are skipped.
#
# No lookahead anywhere: the model is refit on an expanding window and only ever
# scores the block that FOLLOWS its training data; feature standardisation, the
# tercile label cut, and the gate threshold are all computed on training rows
# only. During warm-up the gate passes through (gate=1) so the gated and base
# curves are identical until the model exists — any later divergence is the gate.

def _daily_efficiency(df):
    """Intraday directional efficiency |C-O|/(H-L): 1.0 = clean one-way session.
    A 1-day Kaufman ER is degenerate (always 1.0), so per-day efficiency has to
    be the intraday form; multi-day features below use the real Kaufman ER."""
    rng = (df["High"] - df["Low"]).replace(0, np.nan)
    return ((df["Close"] - df["Open"]).abs() / rng).clip(0, 1)


def _kaufman_er(close, n):
    """|net move over n| / sum(|daily moves| over n)."""
    net = (close - close.shift(n)).abs()
    path = close.diff().abs().rolling(n).sum().replace(0, np.nan)
    return (net / path).clip(0, 1)


def _eff_features(df):
    """The 15 measurements shown in the reel, in its own two groupings."""
    close = df["Close"]
    eff = _daily_efficiency(df)
    ret = close.pct_change()
    vol20 = ret.rolling(20).std()
    chop = (eff < 0.3).astype(float)
    streak = chop.groupby((chop == 0).cumsum()).cumsum()   # chop days in a row
    ma50 = close.rolling(50).mean()
    vr = (close.pct_change(5).rolling(60).var() /
          (5 * ret.rolling(60).var())).replace([np.inf, -np.inf], np.nan)
    hi10, lo10 = close.rolling(10).max().shift(1), close.rolling(10).min().shift(1)
    fb = (((df["High"] > hi10) & (close < hi10)) |
          ((df["Low"] < lo10) & (close > lo10))).astype(float)

    return pd.DataFrame({
        # "what the market just did"
        "realised_vol_20": vol20,
        "eff_today": eff,
        "er_20": _kaufman_er(close, 20),
        "variance_ratio": vr,
        "false_breakout_rate": fb.rolling(20).mean(),
        "dist_from_ma50": (close - ma50) / ma50,
        # "what it's been doing lately"
        "chop_streak": streak,
        "er_5": _kaufman_er(close, 5),
        "er_10": _kaufman_er(close, 10),
        "eff_mean_20": eff.rolling(20).mean(),
        "eff_lag1": eff.shift(1),
        "eff_lag2": eff.shift(2),
        "vol_change": vol20 / vol20.shift(20) - 1,
        "chop_share_5": chop.rolling(5).mean(),
        "chop_share_10": chop.rolling(10).mean(),
    }), eff


def _fit_logistic(X, y, l2=1.0, iters=60):
    """Ridge-penalised logistic regression by Newton/IRLS. numpy only — the API
    image has no sklearn and this is 15 features on a few thousand rows."""
    n, k = X.shape
    Xb = np.hstack([np.ones((n, 1)), X])
    w = np.zeros(k + 1)
    reg = np.eye(k + 1) * l2
    reg[0, 0] = 0.0                      # never penalise the intercept
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(Xb @ w, -30, 30)))
        W = np.clip(p * (1 - p), 1e-6, None)
        grad = Xb.T @ (y - p) - reg @ w
        H = (Xb.T * W) @ Xb + reg
        try:
            step = np.linalg.solve(H, grad)
        except np.linalg.LinAlgError:
            break
        w = w + step
        if np.max(np.abs(step)) < 1e-8:
            break
    return w


def _logistic_p(w, X):
    Xb = np.hstack([np.ones((X.shape[0], 1)), X])
    return 1.0 / (1.0 + np.exp(-np.clip(Xb @ w, -30, 30)))


def efficiency_gate(df, params):
    base_name = str(params.get("base", "momentum"))
    gate_q = float(params.get("gate_q", 0.33))        # skip this bottom fraction
    min_train = int(params.get("min_train_days", 756))
    refit_days = int(params.get("refit_days", 252))

    if base_name == "efficiency_gate" or base_name not in REGISTRY:
        base_name = "momentum"
    base_params = {k: v for k, v in params.items()
                   if k not in ("base", "gate_q", "min_train_days", "refit_days")}
    base_sig = REGISTRY[base_name]["fn"](df, base_params).astype(int)

    feats, eff = _eff_features(df)
    X = feats.to_numpy(dtype=float)
    y_eff = eff.shift(-1).to_numpy(dtype=float)       # tomorrow's efficiency
    ok = np.isfinite(X).all(axis=1) & np.isfinite(y_eff)

    n = len(df)
    gate = np.ones(n, dtype=int)                      # warm-up = pass-through
    idx = np.arange(n)

    start = min_train
    while start < n:
        end = min(start + refit_days, n)
        tr = ok & (idx < start)                       # strictly the past
        te = ok & (idx >= start) & (idx < end)
        if tr.sum() >= 250 and te.any():
            Xtr = X[tr]
            mu, sd = Xtr.mean(0), Xtr.std(0)
            sd[sd == 0] = 1.0
            Ztr = (Xtr - mu) / sd
            label = (y_eff[tr] >= np.quantile(y_eff[tr], 2 / 3)).astype(float)
            w = _fit_logistic(Ztr, label)
            cut = np.quantile(_logistic_p(w, Ztr), gate_q)
            gate[idx[te]] = (_logistic_p(w, (X[te] - mu) / sd) >= cut).astype(int)
        elif te.any():
            gate[idx[te]] = 1
        start = end

    return pd.Series(base_sig.to_numpy() * gate, index=df.index)


# EDGAR-scanning strategies: too slow / rate-limited for nightly sweeps
SLOW_STRATEGIES = {"insider_form4", "whale_13f"}

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
    "rotation_top_k": {"fn": rotation_top_k,
                       "grid": {"lookback_days": [60, 90, 120], "top_k": [2, 3]}},
    "whale_13f": {"fn": whale_13f, "grid": {"max_filings": [8, 12]}},
    "halloween": {"fn": halloween,
                  "grid": {"start_month": [10, 11], "end_month": [4, 5]}},
    "halloween_trend": {"fn": halloween_trend,
                        "grid": {"ma_days": [100, 200], "start_month": [10, 11]}},
    "turnaround_tuesday": {"fn": turnaround_tuesday,
                            "grid": {"sma_days": [15, 25, 50]}},
    "efficiency_gate": {"fn": efficiency_gate,
                        "grid": {"gate_q": [0.2, 0.33, 0.5],
                                 "lookback_days": [60, 90, 120]}},
}
