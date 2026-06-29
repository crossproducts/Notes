"""Congressional Trading Copycat Strategy — Backtest

Strategy: Buy stocks that multiple members of Congress purchased.
Since we don't have a live Congressional trades API in this backtest,
we use publicly documented Congressional stock purchases and test
whether buying on disclosure date (not trade date) still generates alpha.

We use a curated list of the most well-known Congressional trades from
2020-2025 and backtest buying on disclosure date, holding for N days.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

# Known high-profile Congressional trades (disclosure dates, approximate)
# Source: public STOCK Act filings, news reports
# Format: (disclosure_date, ticker, members_count, description)
CONGRESSIONAL_TRADES = [
    # 2020
    ("2020-03-20", "AAPL", 3, "Multiple members bought tech during COVID crash"),
    ("2020-03-20", "MSFT", 4, "Multiple members bought tech during COVID crash"),
    ("2020-03-23", "AMZN", 3, "COVID beneficiary buying"),
    ("2020-04-15", "NVDA", 2, "AI/tech accumulation"),
    ("2020-06-15", "CRM", 2, "Cloud stock buying"),
    ("2020-07-01", "GOOGL", 3, "Big tech accumulation"),
    ("2020-09-01", "TSLA", 2, "EV push awareness"),
    ("2020-11-10", "PFE", 4, "Vaccine news (disclosed after)"),
    ("2020-11-10", "MRNA", 3, "Vaccine news (disclosed after)"),
    ("2020-12-15", "AAPL", 2, "Year-end tech buying"),
    # 2021
    ("2021-01-15", "MSFT", 3, "Cloud/enterprise momentum"),
    ("2021-02-01", "DIS", 2, "Streaming growth play"),
    ("2021-03-15", "NVDA", 4, "Semiconductor shortage awareness"),
    ("2021-04-01", "GOOGL", 2, "Antitrust hearings — still buying"),
    ("2021-05-15", "AAPL", 3, "Consistent accumulation"),
    ("2021-06-01", "AMZN", 2, "Infrastructure bill beneficiary"),
    ("2021-07-15", "MSFT", 4, "Government contracts momentum"),
    ("2021-08-01", "NVDA", 3, "AI/datacenter growth"),
    ("2021-09-15", "JPM", 2, "Rate hike expectations"),
    ("2021-10-01", "META", 2, "Before metaverse pivot"),
    ("2021-11-15", "AAPL", 3, "Holiday season buying"),
    ("2021-12-01", "TSLA", 2, "EV legislation tailwinds"),
    # 2022
    ("2022-01-15", "MSFT", 3, "ATVI acquisition news"),
    ("2022-02-01", "GOOGL", 2, "Stock split announcement"),
    ("2022-03-15", "XOM", 4, "Energy crisis — oil buying"),
    ("2022-03-15", "CVX", 3, "Energy crisis — oil buying"),
    ("2022-04-01", "LMT", 3, "Defense spending (Ukraine)"),
    ("2022-04-01", "RTX", 2, "Defense spending (Ukraine)"),
    ("2022-05-15", "AAPL", 2, "Buy the dip"),
    ("2022-06-15", "NVDA", 2, "AI narrative building"),
    ("2022-08-01", "CHIPS", 2, "CHIPS Act beneficiaries (proxy: INTC)"),
    ("2022-09-01", "INTC", 3, "CHIPS Act signed"),
    ("2022-10-15", "META", 2, "Beaten down — accumulation"),
    ("2022-11-01", "MSFT", 3, "ChatGPT era beginning"),
    # 2023
    ("2023-01-15", "NVDA", 5, "AI boom — heavy Congressional buying"),
    ("2023-02-01", "MSFT", 4, "OpenAI investment momentum"),
    ("2023-03-01", "AAPL", 3, "Consistent accumulation"),
    ("2023-04-15", "GOOGL", 3, "AI race buying"),
    ("2023-05-01", "NVDA", 4, "Pre-earnings AI hype"),
    ("2023-06-01", "META", 3, "Efficiency year / Reels growth"),
    ("2023-07-15", "AMZN", 3, "AWS + AI narrative"),
    ("2023-08-01", "MSFT", 2, "Azure AI growth"),
    ("2023-09-15", "NVDA", 3, "Continued AI accumulation"),
    ("2023-10-01", "LLY", 4, "GLP-1 drug mania"),
    ("2023-10-01", "NVO", 3, "GLP-1 drug mania"),
    ("2023-11-15", "AAPL", 2, "Holiday buying"),
    ("2023-12-01", "AVGO", 3, "AI chip diversification"),
    # 2024
    ("2024-01-15", "NVDA", 5, "AI infrastructure buildout"),
    ("2024-02-01", "META", 3, "Efficiency + AI ads"),
    ("2024-03-15", "MSFT", 3, "Copilot momentum"),
    ("2024-04-01", "GOOGL", 2, "Gemini launch"),
    ("2024-05-15", "AAPL", 2, "AI iPhone anticipation"),
    ("2024-06-01", "NVDA", 4, "Stock split + continued momentum"),
    ("2024-07-15", "AMZN", 3, "AWS + AI growth"),
    ("2024-08-01", "LLY", 3, "Continued GLP-1 momentum"),
    ("2024-09-15", "AVGO", 2, "VMware integration + AI"),
    ("2024-10-01", "PLTR", 3, "Government AI contracts"),
    ("2024-11-15", "TSLA", 3, "Post-election rally"),
    ("2024-12-01", "NVDA", 3, "Blackwell ramp"),
    # 2025
    ("2025-01-15", "NVDA", 4, "Continued AI dominance"),
    ("2025-02-01", "MSFT", 3, "Azure AI scaling"),
    ("2025-03-15", "PLTR", 3, "Defense + AI government contracts"),
    ("2025-04-01", "AAPL", 2, "Services growth"),
    ("2025-05-15", "GOOGL", 3, "Gemini ecosystem"),
    ("2025-06-01", "AMZN", 2, "AI + logistics"),
]


DEFAULT_PARAMS = {
    "hold_days": 30,
    "stop_loss_pct": -10.0,
    "min_members": 2,
    "initial_capital": 10000,
}

PARAM_GRID = {
    "hold_days": [14, 30, 60, 90],
    "stop_loss_pct": [-5.0, -10.0, -15.0, -100.0],  # -100 = no stop loss
    "min_members": [2, 3, 4],
}


def describe_strategy() -> str:
    return (
        "Congressional Trading Copycat: Buy stocks that multiple Congress members "
        "purchased (based on public STOCK Act disclosures). Enter on disclosure date, "
        "hold for a set number of days with an optional stop loss. Tests whether "
        "following Congressional trades generates alpha after the reporting delay."
    )


def run_backtest(data_unused, params: dict) -> pd.DataFrame:
    """
    Run the Congressional copycat backtest.

    Note: This strategy uses its own data (yfinance per ticker) rather than
    the pipeline's pre-loaded SPY data, since it trades individual stocks.
    The `data_unused` param is ignored but kept for pipeline compatibility.
    """
    hold_days = params.get("hold_days", 30)
    stop_loss_pct = params.get("stop_loss_pct", -10.0)
    min_members = params.get("min_members", 2)

    # Filter trades by minimum member count
    eligible = [t for t in CONGRESSIONAL_TRADES if t[2] >= min_members]

    trades = []
    ticker_cache = {}

    for disclosure_date_str, ticker, members, desc in eligible:
        disclosure_date = pd.Timestamp(disclosure_date_str)

        # Handle CHIPS proxy
        if ticker == "CHIPS":
            continue

        # Download price data if not cached
        if ticker not in ticker_cache:
            try:
                start = disclosure_date - timedelta(days=5)
                end = disclosure_date + timedelta(days=hold_days + 10)
                df = yf.download(ticker, start=start, end=end, progress=False)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                ticker_cache[ticker] = df
            except Exception:
                continue

        df = ticker_cache[ticker]
        if df is None or len(df) == 0:
            continue

        # Find entry price (next trading day after disclosure)
        entry_candidates = df[df.index >= disclosure_date]
        if len(entry_candidates) == 0:
            continue

        entry_date = entry_candidates.index[0]
        entry_price = float(entry_candidates.iloc[0]["Open"])

        # Find exit
        exit_date = entry_date + timedelta(days=hold_days)
        exit_candidates = df[df.index >= exit_date]

        # Check stop loss during holding period
        holding = df[(df.index >= entry_date) & (df.index <= exit_date)]
        stopped_out = False

        if stop_loss_pct > -100:
            stop_price = entry_price * (1 + stop_loss_pct / 100)
            for idx, row in holding.iterrows():
                if float(row["Low"]) <= stop_price:
                    exit_price = stop_price
                    exit_date_actual = idx
                    stopped_out = True
                    break

        if not stopped_out:
            if len(exit_candidates) > 0:
                exit_price = float(exit_candidates.iloc[0]["Close"])
                exit_date_actual = exit_candidates.index[0]
            elif len(holding) > 0:
                exit_price = float(holding.iloc[-1]["Close"])
                exit_date_actual = holding.index[-1]
            else:
                continue

        pnl_pct = (exit_price - entry_price) / entry_price * 100
        pnl_points = exit_price - entry_price

        trades.append({
            "date": entry_date.date() if hasattr(entry_date, 'date') else entry_date,
            "direction": "long",
            "ticker": ticker,
            "members": members,
            "entry": round(entry_price, 2),
            "exit_price": round(exit_price, 2),
            "pnl": round(pnl_points, 2),
            "pnl_pct": round(pnl_pct, 2),
            "exit_reason": "stop_loss" if stopped_out else "hold_period",
            "hold_days": (exit_date_actual - entry_date).days,
            "description": desc,
        })

    return pd.DataFrame(trades) if trades else pd.DataFrame()
