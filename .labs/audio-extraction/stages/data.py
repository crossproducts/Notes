"""Stage 4: Data — fetch and cache historical market data from Alpaca."""

import os
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd

CACHE_DIR = Path(__file__).parent.parent / "cache"


def fetch_alpaca_data(
    symbol: str = "SPY",
    start: datetime = None,
    end: datetime = None,
    timeframe_minutes: int = 5,
) -> pd.DataFrame:
    """Fetch intraday data from Alpaca. Caches to parquet."""
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if start is None:
        start = datetime(2020, 1, 1)
    if end is None:
        end = datetime.now() - timedelta(days=1)

    cache_file = CACHE_DIR / f"{symbol}_{timeframe_minutes}min_{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}.parquet"

    if cache_file.exists():
        print(f"  [cache hit] Loading {cache_file.name}")
        data = pd.read_parquet(cache_file)
        print(f"  Loaded {len(data)} bars ({data.index[0].date()} to {data.index[-1].date()})")
        return data

    print(f"  Fetching {symbol} {timeframe_minutes}-min data from Alpaca...")
    print(f"  Range: {start.date()} to {end.date()}")

    client = StockHistoricalDataClient(
        os.getenv("ALPACA_API_KEY"),
        os.getenv("ALPACA_SECRET_KEY"),
    )

    all_bars = []
    chunk_size = timedelta(days=30)
    current = start
    total_bars = 0

    while current < end:
        chunk_end = min(current + chunk_size, end)
        req = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame(timeframe_minutes, TimeFrameUnit.Minute),
            start=current,
            end=chunk_end,
        )
        bars = client.get_stock_bars(req)
        df = bars.df
        if len(df) > 0:
            all_bars.append(df)
            total_bars += len(df)
        current = chunk_end

    if not all_bars:
        raise RuntimeError(f"No data returned for {symbol}")

    full_data = pd.concat(all_bars)
    full_data = full_data.droplevel(0)  # remove symbol level
    full_data.index = full_data.index.tz_convert("US/Eastern")

    full_data.to_parquet(cache_file)
    unique_days = len(set(full_data.index.date))
    print(f"  Downloaded {total_bars} bars across {unique_days} trading days")
    print(f"  Saved: {cache_file.name}")

    return full_data


def run(strategy_config: dict) -> pd.DataFrame:
    """Fetch data based on strategy config."""
    print("\n[STAGE 4: DATA]")

    instrument = strategy_config.get("instrument", "SPY").upper()
    # Map common names to tickers
    ticker_map = {
        "ES": "SPY", "NQ": "QQQ", "S&P 500": "SPY", "S&P500": "SPY",
        "NASDAQ": "QQQ", "RUSSELL": "IWM", "DOW": "DIA",
    }
    symbol = ticker_map.get(instrument, instrument)

    # Check for cached data first (any recent parquet for this symbol)
    existing = list(CACHE_DIR.glob(f"{symbol}_5min_*.parquet"))
    if existing:
        latest = max(existing, key=lambda p: p.stat().st_mtime)
        print(f"  Found existing data: {latest.name}")
        data = pd.read_parquet(latest)
        print(f"  Loaded {len(data)} bars ({data.index[0].date()} to {data.index[-1].date()})")
        return data

    return fetch_alpaca_data(symbol)
