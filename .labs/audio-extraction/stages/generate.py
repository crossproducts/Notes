"""Stage 3: Generate — use Claude API to generate backtest code from strategy config."""

import json
import os
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "cache"

SYSTEM_PROMPT = """You are a quantitative developer who writes Python backtesting code.
Given a trading strategy config (JSON), generate a complete, runnable Python backtest function.

Requirements:
- The function signature MUST be: def run_backtest(data, params) -> pd.DataFrame
- `data` is a pandas DataFrame with columns: open, high, low, close, volume
  - Index is DatetimeIndex in US/Eastern timezone
  - Data is 5-minute bars
- `params` is a dict with tunable parameters (with defaults)
- Return a DataFrame of trades with columns: date, direction, entry, exit_price, pnl, exit_reason
- Include a DEFAULT_PARAMS dict with reasonable defaults
- Include a PARAM_GRID dict with lists of values to optimize over
- Use numpy for speed where possible
- Pre-group data by date for performance
- Handle edge cases (no trades, empty data, etc.)
- The code must be self-contained (only imports: pandas, numpy, datetime)

Also generate a function: def describe_strategy() -> str
That returns a 2-3 sentence description of what the strategy does.

Respond with ONLY the Python code — no markdown fences, no explanation."""


def run(strategy_config: dict, cache_key: str) -> str:
    """Generate backtest code from strategy config. Returns the code as a string."""
    import anthropic

    code_path = CACHE_DIR / f"{cache_key}_backtest.py"

    if code_path.exists():
        print(f"  [cache hit] Backtest code exists: {code_path.name}")
        return code_path.read_text(encoding="utf-8")

    print("\n[STAGE 3: GENERATE]")
    print("  Generating backtest code from strategy config...")

    client = anthropic.Anthropic()

    user_message = f"""Generate a Python backtest for this trading strategy:

{json.dumps(strategy_config, indent=2)}

Remember:
- Function signature: def run_backtest(data, params) -> pd.DataFrame
- data has columns: open, high, low, close, volume (5-min bars, US/Eastern DatetimeIndex)
- Return DataFrame with: date, direction, entry, exit_price, pnl, exit_reason
- Include DEFAULT_PARAMS dict and PARAM_GRID dict
- Pure Python code only, no markdown."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    code = response.content[0].text.strip()

    # Strip markdown fences if present
    if code.startswith("```"):
        lines = code.split("\n")
        code = "\n".join(lines[1:])
        if code.endswith("```"):
            code = code[:-3].strip()
    if code.startswith("python"):
        code = code[6:].strip()

    # Save code
    code_path.write_text(code, encoding="utf-8")
    print(f"  Backtest code generated ({len(code)} chars)")
    print(f"  Saved: {code_path.name}")

    return code
