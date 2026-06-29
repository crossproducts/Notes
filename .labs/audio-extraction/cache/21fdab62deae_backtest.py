"""AI Infrastructure Cycles Rotation — Backtest

Based on Leopold Aschenbrenner's "Situational Awareness" thesis (June 2024).
AI growth requires infrastructure in waves. Each cycle is a bottleneck:
  1. Chips (GPUs) — 2022-2024
  2. Energy (power for datacenters) — 2024-2026
  3. Nuclear/Protons (scalable clean baseload) — 2024-2027
  4. Cooling infrastructure — 2025-2027
  5. Robotics/Physical AI — 2025-2028

Strategy: Equal-weight buy each cycle's basket at cycle start, hold for N months.
Compare cycle returns vs SPY buy-and-hold over same period.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf


# Define the cycles with approximate "early mover" entry dates
# These represent when the thesis would have pointed you to each cycle
CYCLES = {
    "1_chips": {
        "entry_date": "2022-10-01",  # Before the ChatGPT launch (Nov 2022)
        "tickers": ["NVDA", "AMD", "AVGO", "MRVL", "TSM"],
        "description": "AI Chips — GPU compute for training",
    },
    "2_energy": {
        "entry_date": "2024-01-15",  # Energy bottleneck becoming apparent
        "tickers": ["VST", "CEG", "NRG", "ETN", "PWR"],
        "description": "Energy — power for datacenters",
    },
    "3_nuclear": {
        "entry_date": "2024-03-01",  # Nuclear narrative building
        "tickers": ["CCJ", "LEU", "SMR", "UEC"],
        "description": "Nuclear/Uranium — clean baseload power",
    },
    "4_cooling": {
        "entry_date": "2024-09-01",  # Cooling demand recognized
        "tickers": ["VRT", "CARR", "JCI"],
        "description": "Cooling — datacenter thermal management",
    },
    "5_robotics": {
        "entry_date": "2025-01-15",  # Physical AI narrative
        "tickers": ["ISRG", "ROK", "TER", "PLTR"],
        "description": "Robotics/Physical AI",
    },
}


DEFAULT_PARAMS = {
    "hold_months": 6,
    "stop_loss_pct": -15.0,
    "equal_weight": True,
}

PARAM_GRID = {
    "hold_months": [3, 6, 9, 12],
    "stop_loss_pct": [-10.0, -15.0, -20.0, -100.0],
}


def describe_strategy() -> str:
    return (
        "AI Infrastructure Cycles Rotation based on Leopold Aschenbrenner's "
        "'Situational Awareness' thesis. Invest in sequential AI bottleneck cycles "
        "(chips > energy > nuclear > cooling > robotics) before each becomes "
        "consensus. Equal-weight basket per cycle, hold for N months."
    )


def fetch_prices(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Fetch daily prices for a ticker."""
    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()


def run_backtest(data_unused, params: dict) -> pd.DataFrame:
    """
    Backtest the AI cycles rotation strategy.

    Each cycle is an equal-weight basket. We buy all tickers in the basket
    on the entry date and hold for hold_months.
    """
    hold_months = params.get("hold_months", 6)
    stop_loss_pct = params.get("stop_loss_pct", -15.0)

    all_trades = []

    for cycle_name, cycle in CYCLES.items():
        entry_date = pd.Timestamp(cycle["entry_date"])
        exit_date = entry_date + pd.DateOffset(months=hold_months)
        # Extend data fetch for stop loss checking
        fetch_end = exit_date + timedelta(days=10)

        for ticker in cycle["tickers"]:
            df = fetch_prices(
                ticker,
                (entry_date - timedelta(days=5)).strftime("%Y-%m-%d"),
                fetch_end.strftime("%Y-%m-%d"),
            )

            if df is None or len(df) == 0:
                continue

            # Entry: first trading day on or after entry_date
            entry_candidates = df[df.index >= entry_date]
            if len(entry_candidates) == 0:
                continue

            actual_entry_date = entry_candidates.index[0]
            entry_price = float(entry_candidates.iloc[0]["Open"])

            # Track through holding period
            holding = df[(df.index >= actual_entry_date) & (df.index <= exit_date)]
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
                exit_candidates = df[df.index >= exit_date]
                if len(exit_candidates) > 0:
                    exit_price = float(exit_candidates.iloc[0]["Close"])
                    exit_date_actual = exit_candidates.index[0]
                else:
                    exit_price = float(holding.iloc[-1]["Close"])
                    exit_date_actual = holding.index[-1]

            pnl_pct = (exit_price - entry_price) / entry_price * 100
            pnl_points = exit_price - entry_price
            hold_days = (exit_date_actual - actual_entry_date).days

            all_trades.append({
                "date": actual_entry_date.date(),
                "direction": "long",
                "cycle": cycle_name,
                "ticker": ticker,
                "entry": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "pnl": round(pnl_points, 2),
                "pnl_pct": round(pnl_pct, 2),
                "exit_reason": "stop_loss" if stopped_out else "hold_period",
                "hold_days": hold_days,
                "description": cycle["description"],
            })

    return pd.DataFrame(all_trades) if all_trades else pd.DataFrame()


def compare_vs_spy(trades: pd.DataFrame) -> dict:
    """Compare cycle returns vs SPY over the same periods."""
    if len(trades) == 0:
        return {}

    results = {}
    for cycle_name in trades["cycle"].unique():
        cycle_trades = trades[trades["cycle"] == cycle_name]
        first_entry = pd.Timestamp(cycle_trades["date"].min())
        last_exit_days = int(cycle_trades["hold_days"].max())
        end_date = first_entry + timedelta(days=last_exit_days + 5)

        spy = fetch_prices("SPY", first_entry.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        if len(spy) > 0:
            spy_start = float(spy.iloc[0]["Open"])
            spy_end = float(spy.iloc[-1]["Close"])
            spy_return = (spy_end - spy_start) / spy_start * 100
        else:
            spy_return = 0

        cycle_avg_return = cycle_trades["pnl_pct"].mean()

        results[cycle_name] = {
            "cycle_return": round(cycle_avg_return, 1),
            "spy_return": round(spy_return, 1),
            "alpha": round(cycle_avg_return - spy_return, 1),
        }

    return results
