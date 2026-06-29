#!/usr/bin/env python3
"""
Video Strategy Pipeline
=======================
Paste a video link → get a full backtest report.

Usage:
    python pipeline.py "https://www.instagram.com/reel/..."

Stages:
    1. Extract  — download video, extract audio, transcribe (yt-dlp + ffmpeg + Whisper)
    2. Interpret — parse transcript into strategy config (Claude API)
    3. Generate  — create backtest code from config (Claude API)
    4. Data      — fetch historical market data (Alpaca API)
    5. Backtest  — run backtest + parameter optimization
    6. Report    — performance stats + dollar examples
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

from stages import extract, interpret, generate, data, backtest, report


def run_pipeline(url: str, whisper_model: str = "base"):
    """Run the full pipeline from URL to report."""

    print("=" * 70)
    print("  VIDEO STRATEGY PIPELINE")
    print("=" * 70)
    print(f"  URL: {url}")
    print(f"  Whisper model: {whisper_model}")

    # Validate env vars
    missing = []
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if not os.getenv("ALPACA_API_KEY"):
        missing.append("ALPACA_API_KEY")
    if missing:
        print(f"\n  ERROR: Missing environment variables: {', '.join(missing)}")
        print(f"  Add them to {env_path}")
        sys.exit(1)

    # Stage 1: Extract
    extraction = extract.run(url, whisper_model)
    print(f"\n  Transcript preview: {extraction['transcript'][:200]}...")

    # Stage 2: Interpret
    strategy_config = interpret.run(
        extraction["transcript"],
        extraction["caption"],
        extraction["cache_key"],
    )

    # Stage 3: Generate backtest code
    backtest_code = generate.run(strategy_config, extraction["cache_key"])

    # Stage 4: Fetch data
    market_data = data.run(strategy_config)
    data_info = f"{len(market_data)} bars, {market_data.index[0].date()} to {market_data.index[-1].date()}"

    # Stage 5: Run backtest
    backtest_results = backtest.run(
        backtest_code, market_data, extraction["cache_key"]
    )

    # Stage 6: Report
    final_report = report.run(
        strategy_config, backtest_results, extraction["cache_key"], data_info
    )

    print("\n  Pipeline complete!")
    return final_report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <video_url> [whisper_model]")
        print("  whisper_model: tiny, base (default), small, medium, large")
        sys.exit(1)

    url = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "base"
    run_pipeline(url, model)
