"""Stage 5: Backtest — execute generated backtest code and run optimization."""

import json
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import numpy as np

CACHE_DIR = Path(__file__).parent.parent / "cache"


def load_backtest_module(code: str, cache_key: str):
    """Dynamically load the generated backtest code as a module."""
    code_path = CACHE_DIR / f"{cache_key}_backtest.py"
    if not code_path.exists():
        code_path.write_text(code, encoding="utf-8")

    spec = importlib.util.spec_from_file_location(f"backtest_{cache_key}", str(code_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_optimization(module, data: pd.DataFrame) -> pd.DataFrame:
    """Run parameter optimization using the module's PARAM_GRID."""
    param_grid = getattr(module, "PARAM_GRID", {})
    default_params = getattr(module, "DEFAULT_PARAMS", {})

    if not param_grid:
        print("  No PARAM_GRID defined, running with defaults only.")
        trades = module.run_backtest(data, default_params)
        return trades, [{"params": default_params, "trades": trades}]

    # Generate all combinations
    keys = list(param_grid.keys())
    values = list(param_grid.values())

    def product(*pools):
        result = [[]]
        for pool in pools:
            result = [x + [y] for x in result for y in pool]
        return result

    combos = product(*values)
    print(f"  Testing {len(combos)} parameter combinations...")

    results = []
    for combo in combos:
        params = {**default_params, **dict(zip(keys, combo))}
        try:
            trades = module.run_backtest(data, params)
            if trades is None or len(trades) < 5:
                continue

            pnls = trades["pnl"].values
            winners = pnls[pnls > 0]
            losers = pnls[pnls <= 0]

            gp = winners.sum() if len(winners) > 0 else 0
            gl = abs(losers.sum()) if len(losers) > 0 else 0

            cum = np.cumsum(pnls)
            max_dd = (cum - np.maximum.accumulate(cum)).min()

            results.append({
                **{k: v for k, v in zip(keys, combo)},
                "trades": len(trades),
                "win_rate": round(len(winners) / len(pnls) * 100, 1),
                "total_pnl": round(pnls.sum(), 2),
                "profit_factor": round(gp / gl, 2) if gl > 0 else 999,
                "max_drawdown": round(max_dd, 2),
                "avg_pnl": round(pnls.mean(), 3),
            })
        except Exception as e:
            continue

    return pd.DataFrame(results)


def run(backtest_code: str, data: pd.DataFrame, cache_key: str) -> dict:
    """Execute the backtest and optimization."""
    print("\n[STAGE 5: BACKTEST]")

    module = load_backtest_module(backtest_code, cache_key)

    # Run with defaults first
    default_params = getattr(module, "DEFAULT_PARAMS", {})
    print(f"  Default params: {default_params}")

    print("  Running backtest with default parameters...")
    default_trades = module.run_backtest(data, default_params)

    if default_trades is None or len(default_trades) == 0:
        print("  WARNING: No trades generated with default params.")
        default_trades = pd.DataFrame()

    # Run optimization
    print("  Running parameter optimization...")
    opt_results = run_optimization(module, data)

    # Get strategy description
    desc_fn = getattr(module, "describe_strategy", None)
    description = desc_fn() if desc_fn else "No description available."

    return {
        "description": description,
        "default_trades": default_trades,
        "optimization_results": opt_results,
        "default_params": default_params,
    }
