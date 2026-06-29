"""Multi-Factor AI Analyst Strategy -- Backtest

Inspired by ValueCell: a team of AI agents each handling a different factor.
We simulate 3 "agents":
  1. Fundamental Agent: ranks by 6-month price momentum (proxy for earnings growth/value)
  2. Sentiment Agent: ranks by 1-month return (proxy for market sentiment)
  3. Technical Agent: ranks by trend (price vs 50-day MA) and RSI health

Universe: 20 large-cap liquid stocks across sectors.
Monthly rebalance: buy top-ranked basket, hold for 1 month, re-rank.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf


# Stock universe — diversified large caps
UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "JPM", "V", "UNH",
    "XOM", "JNJ", "PG", "HD", "MA",
    "COST", "ABBV", "CRM", "AMD", "NFLX",
]

DEFAULT_PARAMS = {
    "top_n": 5,             # Buy top N ranked stocks each month
    "momentum_months": 6,   # Lookback for fundamental momentum
    "sentiment_months": 1,  # Lookback for sentiment momentum
    "ma_period": 50,        # Moving average period for technical
    "rsi_period": 14,       # RSI period
    "stop_loss_pct": -10.0, # Per-position stop loss
    "start_year": 2020,
}

PARAM_GRID = {
    "top_n": [3, 5, 7],
    "momentum_months": [3, 6, 9],
    "sentiment_months": [1, 2, 3],
    "stop_loss_pct": [-8.0, -10.0, -15.0, -100.0],
}


def describe_strategy() -> str:
    return (
        "Multi-Factor AI Analyst strategy inspired by ValueCell. Scores stocks on "
        "3 factors: fundamental momentum (6-month return), sentiment (1-month return), "
        "and technical health (price vs 50-day MA + RSI). Buys top-ranked basket each "
        "month. Tests whether a simple multi-factor ranking beats buy-and-hold."
    )


def compute_rsi(series, period=14):
    """Compute RSI from a price series."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def fetch_all_data(start_year=2020):
    """Fetch daily data for all stocks in the universe."""
    start = f"{start_year - 1}-01-01"  # extra year for lookback
    end = datetime.now().strftime("%Y-%m-%d")

    all_data = {}
    for ticker in UNIVERSE:
        try:
            df = yf.download(ticker, start=start, end=end, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if len(df) > 100:
                all_data[ticker] = df
        except Exception:
            continue

    return all_data


def rank_stocks(all_data, date, params):
    """
    Rank stocks on the 3 factors as of a given date.
    Returns sorted list of (ticker, composite_score).
    """
    momentum_months = params.get("momentum_months", 6)
    sentiment_months = params.get("sentiment_months", 1)
    ma_period = params.get("ma_period", 50)
    rsi_period = params.get("rsi_period", 14)

    scores = {}

    for ticker, df in all_data.items():
        hist = df[df.index <= date]
        if len(hist) < max(momentum_months * 21, ma_period + 20):
            continue

        close = hist["Close"]
        current_price = float(close.iloc[-1])

        # Factor 1: Fundamental momentum (N-month return)
        lookback_1 = momentum_months * 21
        if len(close) > lookback_1:
            past_price_1 = float(close.iloc[-lookback_1])
            fund_score = (current_price - past_price_1) / past_price_1
        else:
            continue

        # Factor 2: Sentiment momentum (M-month return)
        lookback_2 = sentiment_months * 21
        if len(close) > lookback_2:
            past_price_2 = float(close.iloc[-lookback_2])
            sent_score = (current_price - past_price_2) / past_price_2
        else:
            continue

        # Factor 3: Technical health
        ma = float(close.rolling(ma_period).mean().iloc[-1])
        rsi = float(compute_rsi(close, rsi_period).iloc[-1])

        # Above MA = positive, RSI between 30-70 = healthy
        ma_signal = 1.0 if current_price > ma else -0.5
        rsi_signal = 1.0 if 30 < rsi < 70 else (0.5 if 25 < rsi < 75 else 0.0)
        tech_score = (ma_signal + rsi_signal) / 2

        # Composite: equal weight the 3 factors (normalize to z-scores later)
        scores[ticker] = {
            "fundamental": fund_score,
            "sentiment": sent_score,
            "technical": tech_score,
        }

    if not scores:
        return []

    # Convert to DataFrame and rank
    score_df = pd.DataFrame(scores).T

    # Rank each factor (higher = better)
    for col in score_df.columns:
        score_df[f"{col}_rank"] = score_df[col].rank(pct=True)

    # Composite score = average of percentile ranks
    rank_cols = [c for c in score_df.columns if c.endswith("_rank")]
    score_df["composite"] = score_df[rank_cols].mean(axis=1)

    # Sort by composite descending
    score_df = score_df.sort_values("composite", ascending=False)

    return list(score_df.index)


def run_backtest(data_unused, params: dict) -> pd.DataFrame:
    """
    Monthly rebalancing multi-factor strategy.
    """
    top_n = params.get("top_n", 5)
    stop_loss_pct = params.get("stop_loss_pct", -10.0)
    start_year = params.get("start_year", 2020)

    # Fetch data
    all_data = fetch_all_data(start_year)
    if not all_data:
        return pd.DataFrame()

    # Get common date range
    first_ticker = list(all_data.keys())[0]
    dates = all_data[first_ticker].index

    # Generate monthly rebalance dates
    start_date = pd.Timestamp(f"{start_year}-02-01")
    end_date = dates[-1]
    rebalance_dates = pd.date_range(start=start_date, end=end_date, freq="MS")

    trades = []

    for i in range(len(rebalance_dates) - 1):
        entry_date = rebalance_dates[i]
        exit_date = rebalance_dates[i + 1]

        # Rank stocks
        ranked = rank_stocks(all_data, entry_date, params)
        if len(ranked) < top_n:
            continue

        # Buy top N
        basket = ranked[:top_n]

        for ticker in basket:
            df = all_data.get(ticker)
            if df is None:
                continue

            # Entry
            entry_bars = df[df.index >= entry_date]
            if len(entry_bars) == 0:
                continue
            actual_entry = entry_bars.index[0]
            entry_price = float(entry_bars.iloc[0]["Open"])

            # Hold period
            holding = df[(df.index >= actual_entry) & (df.index < exit_date)]
            if len(holding) == 0:
                continue

            # Check stop loss
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
                "exit_date": exit_date_actual.date() if hasattr(exit_date_actual, 'date') else exit_date_actual,
                "direction": "long",
                "ticker": ticker,
                "entry": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "pnl": round(pnl_points, 2),
                "pnl_pct": round(pnl_pct, 2),
                "exit_reason": "stop_loss" if stopped_out else "rebalance",
            })

    return pd.DataFrame(trades) if trades else pd.DataFrame()
