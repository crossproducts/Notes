"""Asian Range Breakout — Backtest

S-tier strategy from the tier-list video: the Asian session (00:00-06:00 UTC)
forms a consolidation range; the London session breaks it. Trade the first
breakout of the range during the London window, stop on the opposite side of
the range, take profit at a risk-reward multiple of the range size, time-stop
at end of day.

Session strategies need a 24h market, so this runs on forex (EURUSD by
default) with yfinance hourly data (~720 days available).
"""

import pandas as pd
import numpy as np
import yfinance as yf


DEFAULT_PARAMS = {
    "symbol": "EURUSD=X",
    "period_days": 720,     # yfinance 1h-data limit is ~730d
    "asian_start_utc": 0,   # Asian range = bars with hour in [start, end)
    "asian_end_utc": 6,
    "entry_cutoff_utc": 14, # stop looking for a breakout after this hour
    "risk_reward": 1.5,     # target = entry +/- rr * range_size
    "min_range_pct": 0.05,  # skip days with a degenerate (too-tight) range
}

PARAM_GRID = {
    "risk_reward": [1.0, 1.5, 2.0],
    "entry_cutoff_utc": [10, 12, 14],
    "asian_end_utc": [5, 6, 7],
}


def describe_strategy() -> str:
    return (
        "Asian Range Breakout (S-tier in the source video's ranking): mark the "
        "Asian-session high/low, trade the first London-session breakout, stop at "
        "the opposite side of the range, target a risk-reward multiple of the "
        "range, time-stop at end of day. Consolidation -> volatility expansion."
    )


def _fetch(symbol: str, period_days: int) -> pd.DataFrame:
    df = yf.download(symbol, period=f"{min(period_days, 729)}d",
                     interval="1h", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    return df


def run_backtest(data_unused, params: dict) -> pd.DataFrame:
    p = {**DEFAULT_PARAMS, **(params or {})}
    df = _fetch(p["symbol"], int(p["period_days"]))
    if len(df) < 200:
        return pd.DataFrame()

    rr = float(p["risk_reward"])
    a0, a1 = int(p["asian_start_utc"]), int(p["asian_end_utc"])
    cutoff = int(p["entry_cutoff_utc"])

    trades = []
    for day, bars in df.groupby(df.index.date):
        asian = bars[(bars.index.hour >= a0) & (bars.index.hour < a1)]
        if len(asian) < 3:
            continue
        hi, lo = float(asian["High"].max()), float(asian["Low"].min())
        rng = hi - lo
        mid = (hi + lo) / 2
        if rng <= 0 or rng / mid * 100 < float(p["min_range_pct"]):
            continue

        window = bars[(bars.index.hour >= a1) & (bars.index.hour <= 22)]
        direction, entry, stop, target, entry_ts = 0, None, None, None, None

        for ts, row in window.iterrows():
            if ts.hour > cutoff and direction == 0:
                break
            if direction == 0:
                if float(row["High"]) > hi:      # long breakout
                    direction, entry = 1, hi
                    stop, target = lo, hi + rr * rng
                    entry_ts = ts
                elif float(row["Low"]) < lo:     # short breakout
                    direction, entry = -1, lo
                    stop, target = hi, lo - rr * rng
                    entry_ts = ts
                continue

            # position open: conservative — assume stop hit before target
            if direction == 1:
                if float(row["Low"]) <= stop:
                    exit_px, reason = stop, "stop"
                elif float(row["High"]) >= target:
                    exit_px, reason = target, "target"
                else:
                    continue
            else:
                if float(row["High"]) >= stop:
                    exit_px, reason = stop, "stop"
                elif float(row["Low"]) <= target:
                    exit_px, reason = target, "target"
                else:
                    continue
            break
        else:
            if direction != 0:
                exit_px, reason = float(window.iloc[-1]["Close"]), "eod"

        if direction == 0:
            continue

        pnl_pct = (exit_px - entry) / entry * 100 * direction
        trades.append({
            "date": entry_ts.date(),
            "direction": "long" if direction == 1 else "short",
            "entry": round(entry, 5),
            "exit_price": round(exit_px, 5),
            # pnl expressed in percent (forex points are pip-scale, useless raw)
            "pnl": round(pnl_pct, 3),
            "pnl_pct": round(pnl_pct, 3),
            "exit_reason": reason,
        })

    return pd.DataFrame(trades) if trades else pd.DataFrame()
