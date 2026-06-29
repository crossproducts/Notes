"""Bull vs Bear Debate Strategy -- Backtest (TowerIC-inspired)

Simulates a multi-agent trading firm:
  - Fundamental Analyst: scores value (P/E proxy via earnings yield, book value momentum)
  - Sentiment Analyst: scores momentum and volatility regime
  - Bull Agent: aggregates bullish signals (uptrend, positive momentum, low vol)
  - Bear Agent: aggregates bearish signals (downtrend, negative momentum, high vol, overbought)
  - Trader: only executes when bull score > bear score by a threshold
  - Risk Manager: enforces stop loss and position limits

The key innovation: the adversarial debate filter. Most strategies only look at
bullish signals. This one requires the bull case to OVERCOME specific bear objections.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf


UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "JPM", "V", "UNH",
    "XOM", "JNJ", "PG", "HD", "MA",
    "COST", "ABBV", "CRM", "AMD", "NFLX",
]

DEFAULT_PARAMS = {
    "debate_threshold": 0.15,  # Bull must beat bear by this margin
    "lookback_days": 60,       # Analysis window
    "hold_days": 5,            # Weekly rebalance (5 trading days)
    "top_n": 5,                # Max positions
    "stop_loss_pct": -5.0,     # Per-position stop (risk manager)
    "max_portfolio_risk": 0.25, # Max portfolio drawdown tolerance
    "start_year": 2020,
}

PARAM_GRID = {
    "debate_threshold": [0.05, 0.10, 0.15, 0.20, 0.30],
    "hold_days": [5, 10, 20],
    "stop_loss_pct": [-3.0, -5.0, -8.0, -100.0],
}


def describe_strategy() -> str:
    return (
        "Bull vs Bear Debate strategy inspired by TowerIC Research. For each stock, "
        "a Bull agent scores bullish factors (uptrend, momentum, low volatility) and "
        "a Bear agent scores bearish factors (downtrend, overbought RSI, high volatility, "
        "negative momentum). Only trades when Bull score exceeds Bear score by a threshold. "
        "Weekly rebalance with risk management stop losses."
    )


def compute_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def bull_agent_score(close, volume, lookback=60):
    """Bull agent: scores bullish signals (0 to 1)."""
    if len(close) < lookback:
        return 0

    recent = close.iloc[-lookback:]
    score = 0
    max_score = 6

    # 1. Price above 20-day MA (short-term uptrend)
    ma20 = close.rolling(20).mean().iloc[-1]
    if float(close.iloc[-1]) > float(ma20):
        score += 1

    # 2. Price above 50-day MA (medium-term uptrend)
    ma50 = close.rolling(50).mean().iloc[-1]
    if float(close.iloc[-1]) > float(ma50):
        score += 1

    # 3. Positive 1-month momentum
    if len(close) >= 21:
        mom_1m = (float(close.iloc[-1]) - float(close.iloc[-21])) / float(close.iloc[-21])
        if mom_1m > 0:
            score += 1
        if mom_1m > 0.05:  # Strong momentum bonus
            score += 0.5

    # 4. Volume increasing (buying pressure)
    if len(volume) >= 20:
        recent_vol = float(volume.iloc[-5:].mean())
        avg_vol = float(volume.iloc[-20:].mean())
        if recent_vol > avg_vol:
            score += 0.5

    # 5. RSI not oversold (momentum intact)
    rsi = float(compute_rsi(close).iloc[-1])
    if 40 < rsi < 65:  # Healthy bullish range
        score += 1

    # 6. Higher lows (bullish structure)
    if len(close) >= 10:
        low_5d_ago = float(close.iloc[-10:-5].min())
        low_recent = float(close.iloc[-5:].min())
        if low_recent > low_5d_ago:
            score += 1

    return score / max_score


def bear_agent_score(close, volume, lookback=60):
    """Bear agent: scores bearish risk signals (0 to 1)."""
    if len(close) < lookback:
        return 0.5  # Default to cautious

    score = 0
    max_score = 6

    # 1. Price below 50-day MA (downtrend)
    ma50 = close.rolling(50).mean().iloc[-1]
    if float(close.iloc[-1]) < float(ma50):
        score += 1

    # 2. Negative 1-month momentum
    if len(close) >= 21:
        mom_1m = (float(close.iloc[-1]) - float(close.iloc[-21])) / float(close.iloc[-21])
        if mom_1m < 0:
            score += 1
        if mom_1m < -0.05:  # Strong negative momentum
            score += 0.5

    # 3. RSI overbought (exhaustion risk)
    rsi = float(compute_rsi(close).iloc[-1])
    if rsi > 70:
        score += 1
    if rsi > 80:
        score += 0.5

    # 4. High volatility (risk elevated)
    if len(close) >= 20:
        returns = close.pct_change().iloc[-20:]
        vol = float(returns.std()) * np.sqrt(252)  # Annualized
        if vol > 0.40:  # >40% annual vol = risky
            score += 1

    # 5. Volume declining (lack of conviction)
    if len(volume) >= 20:
        recent_vol = float(volume.iloc[-5:].mean())
        avg_vol = float(volume.iloc[-20:].mean())
        if recent_vol < avg_vol * 0.7:
            score += 0.5

    # 6. Lower highs (bearish structure)
    if len(close) >= 10:
        high_5d_ago = float(close.iloc[-10:-5].max())
        high_recent = float(close.iloc[-5:].max())
        if high_recent < high_5d_ago:
            score += 1

    return score / max_score


def fundamental_score(close, lookback=60):
    """Fundamental analyst: value + quality proxy."""
    if len(close) < lookback:
        return 0

    # 3-month return as earnings growth proxy
    if len(close) >= 63:
        ret_3m = (float(close.iloc[-1]) - float(close.iloc[-63])) / float(close.iloc[-63])
    else:
        ret_3m = 0

    # Stability: lower drawdown = higher quality
    peak = close.iloc[-lookback:].expanding().max()
    drawdown = (close.iloc[-lookback:] - peak) / peak
    max_dd = float(drawdown.min())

    # Score: positive growth + low drawdown = good
    growth_score = min(max(ret_3m, -0.3), 0.5) / 0.5  # Normalize to ~[-0.6, 1]
    stability_score = 1 + max_dd  # max_dd is negative, so higher = more stable

    return (growth_score * 0.5 + stability_score * 0.5)


def sentiment_score(close, volume, lookback=20):
    """Sentiment analyst: recent momentum + volume confirmation."""
    if len(close) < lookback:
        return 0

    # 1-week momentum
    ret_1w = (float(close.iloc[-1]) - float(close.iloc[-5])) / float(close.iloc[-5])

    # Volume trend
    if len(volume) >= 10:
        vol_ratio = float(volume.iloc[-5:].mean()) / float(volume.iloc[-10:].mean())
    else:
        vol_ratio = 1.0

    # Positive momentum + increasing volume = strong sentiment
    mom_score = min(max(ret_1w * 10, -1), 1)  # Scale and clip
    vol_score = min(vol_ratio, 2.0) / 2.0

    return (mom_score + vol_score) / 2


def run_backtest(data_unused, params: dict) -> pd.DataFrame:
    """Run the bull vs bear debate backtest."""
    debate_threshold = params.get("debate_threshold", 0.15)
    lookback = params.get("lookback_days", 60)
    hold_days = params.get("hold_days", 5)
    top_n = params.get("top_n", 5)
    stop_loss_pct = params.get("stop_loss_pct", -5.0)
    start_year = params.get("start_year", 2020)

    # Fetch all data
    all_data = {}
    start = f"{start_year - 1}-01-01"
    end = datetime.now().strftime("%Y-%m-%d")
    for ticker in UNIVERSE:
        try:
            df = yf.download(ticker, start=start, end=end, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if len(df) > 100:
                all_data[ticker] = df
        except Exception:
            continue

    if not all_data:
        return pd.DataFrame()

    # Get trading dates
    ref = list(all_data.values())[0]
    all_dates = ref[ref.index >= f"{start_year}-02-01"].index

    # Rebalance every hold_days trading days
    rebalance_indices = list(range(0, len(all_dates), hold_days))
    trades = []

    for i in range(len(rebalance_indices) - 1):
        entry_idx = rebalance_indices[i]
        exit_idx = rebalance_indices[i + 1]

        entry_date = all_dates[entry_idx]
        exit_date = all_dates[min(exit_idx, len(all_dates) - 1)]

        # Run debate for each stock
        debate_results = []

        for ticker, df in all_data.items():
            hist = df[df.index <= entry_date]
            if len(hist) < lookback + 20:
                continue

            close = hist["Close"]
            volume = hist["Volume"]

            bull = bull_agent_score(close, volume, lookback)
            bear = bear_agent_score(close, volume, lookback)
            fund = fundamental_score(close, lookback)
            sent = sentiment_score(close, volume)

            # Debate margin: how much bull beats bear
            debate_margin = bull - bear

            # Composite conviction
            conviction = (debate_margin * 0.4 + fund * 0.3 + sent * 0.3)

            debate_results.append({
                "ticker": ticker,
                "bull": round(bull, 3),
                "bear": round(bear, 3),
                "margin": round(debate_margin, 3),
                "fundamental": round(fund, 3),
                "sentiment": round(sent, 3),
                "conviction": round(conviction, 3),
            })

        if not debate_results:
            continue

        # Trader decides: only take trades where bull wins the debate
        debate_df = pd.DataFrame(debate_results)
        qualified = debate_df[debate_df["margin"] > debate_threshold]
        qualified = qualified.sort_values("conviction", ascending=False)

        # Take top N
        picks = qualified.head(top_n)

        for _, pick in picks.iterrows():
            ticker = pick["ticker"]
            df = all_data[ticker]

            # Entry
            entry_bars = df[df.index >= entry_date]
            if len(entry_bars) == 0:
                continue
            actual_entry = entry_bars.index[0]
            entry_price = float(entry_bars.iloc[0]["Open"])

            # Hold and check stop
            holding = df[(df.index >= actual_entry) & (df.index <= exit_date)]
            if len(holding) == 0:
                continue

            stopped_out = False
            exit_price = None
            exit_date_actual = None

            if stop_loss_pct > -100:
                stop_price = entry_price * (1 + stop_loss_pct / 100)
                for idx, row in holding.iterrows():
                    if float(row["Low"]) <= stop_price:
                        exit_price = stop_price
                        exit_date_actual = idx
                        stopped_out = True
                        break

            if not stopped_out:
                exit_bars = df[df.index >= exit_date]
                if len(exit_bars) > 0:
                    exit_price = float(exit_bars.iloc[0]["Open"])
                    exit_date_actual = exit_bars.index[0]
                else:
                    exit_price = float(holding.iloc[-1]["Close"])
                    exit_date_actual = holding.index[-1]

            pnl_pct = (exit_price - entry_price) / entry_price * 100
            pnl_points = exit_price - entry_price

            trades.append({
                "date": actual_entry.date(),
                "direction": "long",
                "ticker": ticker,
                "bull_score": pick["bull"],
                "bear_score": pick["bear"],
                "debate_margin": pick["margin"],
                "conviction": pick["conviction"],
                "entry": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "pnl": round(pnl_points, 2),
                "pnl_pct": round(pnl_pct, 2),
                "exit_reason": "stop_loss" if stopped_out else "rebalance",
            })

    return pd.DataFrame(trades) if trades else pd.DataFrame()
