"""Stage 2: Interpret — use Claude API to parse transcript into a strategy config."""

import json
import os
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "cache"

SYSTEM_PROMPT = """You are a quantitative trading strategy analyst.
Given a video transcript about a trading strategy, extract the strategy rules into a structured JSON config.

You MUST respond with valid JSON only — no markdown, no explanation, just the JSON object.

Use this exact schema:
{
  "name": "Strategy Name",
  "description": "One sentence summary",
  "instrument": "SPY or QQQ or specific ticker mentioned",
  "timeframe": "5min or 1min or 1h etc",
  "session": {
    "start": "09:30",
    "end": "16:00",
    "timezone": "US/Eastern"
  },
  "setup": {
    "type": "breakout or mean_reversion or momentum or trend_following",
    "range_window": {"start": "09:30", "end": "09:45"},
    "description": "How the setup is identified"
  },
  "entry": {
    "long": "Condition for long entry",
    "short": "Condition for short entry"
  },
  "exit": {
    "stop_loss": "How stop loss is determined",
    "take_profit": "How take profit is determined",
    "time_stop": "When to close if neither SL nor TP hit"
  },
  "filters": [
    {"name": "filter_name", "type": "indicator or volume or time", "description": "What it filters for"}
  ],
  "risk": {
    "risk_reward_ratio": 1.5,
    "max_trades_per_day": 1,
    "position_sizing": "How position size is determined"
  },
  "parameters_to_optimize": [
    {"name": "param_name", "range": [1.0, 2.0, 3.0], "description": "What this parameter controls"}
  ],
  "notes": "Any additional context or warnings from the transcript"
}

If certain fields are not mentioned in the transcript, use reasonable defaults and note them.
If the strategy is unclear or not a trading strategy, set name to "UNCLEAR" and explain in notes."""


def run(transcript: str, caption: str, cache_key: str) -> dict:
    """Parse transcript into a strategy config using Claude API."""
    import anthropic

    config_path = CACHE_DIR / f"{cache_key}_strategy.json"

    if config_path.exists():
        print(f"  [cache hit] Strategy config exists: {config_path.name}")
        return json.loads(config_path.read_text(encoding="utf-8"))

    print("\n[STAGE 2: INTERPRET]")
    print("  Sending transcript to Claude for strategy extraction...")

    client = anthropic.Anthropic()

    user_message = f"""Here is the transcript from a trading strategy video:

TRANSCRIPT:
{transcript}

POST CAPTION:
{caption}

Extract the trading strategy into the structured JSON config."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    response_text = response.content[0].text.strip()

    # Parse JSON (handle potential markdown wrapping)
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
        response_text = response_text.strip()

    strategy_config = json.loads(response_text)

    # Save config
    config_path.write_text(json.dumps(strategy_config, indent=2), encoding="utf-8")
    print(f"  Strategy identified: {strategy_config.get('name', 'Unknown')}")
    print(f"  Type: {strategy_config.get('setup', {}).get('type', 'Unknown')}")
    print(f"  Config saved: {config_path.name}")

    return strategy_config
