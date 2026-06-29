"""Stage 6: Report — generate performance report and save results."""

import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def performance_summary(trades: pd.DataFrame) -> dict:
    """Calculate performance metrics from a trades DataFrame."""
    if trades is None or len(trades) == 0:
        return {"error": "No trades to analyze"}

    pnls = trades["pnl"].values
    winners = pnls[pnls > 0]
    losers = pnls[pnls <= 0]

    total_pnl = pnls.sum()
    gp = winners.sum() if len(winners) > 0 else 0
    gl = abs(losers.sum()) if len(losers) > 0 else 0

    cum = np.cumsum(pnls)
    peak = np.maximum.accumulate(cum)
    max_dd = (cum - peak).min()

    return {
        "total_trades": len(pnls),
        "winners": len(winners),
        "losers": len(losers),
        "win_rate": round(len(winners) / len(pnls) * 100, 1),
        "total_pnl": round(float(total_pnl), 2),
        "avg_winner": round(float(winners.mean()), 2) if len(winners) > 0 else 0,
        "avg_loser": round(float(losers.mean()), 2) if len(losers) > 0 else 0,
        "risk_reward": round(abs(float(winners.mean()) / float(losers.mean())), 2) if len(losers) > 0 and len(winners) > 0 else 0,
        "profit_factor": round(gp / gl, 2) if gl > 0 else 999,
        "max_drawdown": round(float(max_dd), 2),
    }


def print_report(strategy_config: dict, backtest_results: dict, data_info: str):
    """Print a formatted report to console."""
    desc = backtest_results.get("description", "")
    default_trades = backtest_results.get("default_trades", pd.DataFrame())
    opt_results = backtest_results.get("optimization_results", pd.DataFrame())

    print(f"\n{'='*70}")
    print(f"  PIPELINE REPORT")
    print(f"{'='*70}")

    print(f"\n  Strategy: {strategy_config.get('name', 'Unknown')}")
    print(f"  Type: {strategy_config.get('setup', {}).get('type', 'Unknown')}")
    print(f"  Description: {desc}")
    print(f"  Data: {data_info}")

    if len(default_trades) > 0:
        stats = performance_summary(default_trades)
        print(f"\n  --- Default Parameters ---")
        print(f"  Params: {backtest_results.get('default_params', {})}")
        print(f"  Total Trades:    {stats['total_trades']}")
        print(f"  Win Rate:        {stats['win_rate']}%")
        print(f"  Profit Factor:   {stats['profit_factor']}")
        print(f"  Risk:Reward:     {stats['risk_reward']}")
        print(f"  Total PnL:       {stats['total_pnl']} points")
        print(f"  Max Drawdown:    {stats['max_drawdown']} points")

        # Dollar examples
        avg_price = 450
        ret_pct = stats["total_pnl"] / avg_price * 100
        print(f"\n  --- Dollar Examples ---")
        print(f"  $1,000  -> ${1000 * (1 + ret_pct / 100):,.2f}  ({ret_pct:.1f}%)")
        print(f"  $10,000 -> ${10000 * (1 + ret_pct / 100):,.2f}")
    else:
        print("\n  No trades generated with default parameters.")

    if isinstance(opt_results, pd.DataFrame) and len(opt_results) > 0:
        print(f"\n  --- Optimization Results (Top 10 by Profit Factor) ---")
        top = opt_results.sort_values("profit_factor", ascending=False).head(10)
        print(top.to_string(index=False))

        best = opt_results.sort_values("total_pnl", ascending=False).iloc[0]
        print(f"\n  --- Best PnL Combo ---")
        print(f"  Total PnL: {best['total_pnl']} | PF: {best['profit_factor']} | Win%: {best['win_rate']} | Trades: {int(best['trades'])}")

    print(f"\n{'='*70}")


def save_report(strategy_config: dict, backtest_results: dict, cache_key: str):
    """Save the full report as JSON."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    default_trades = backtest_results.get("default_trades", pd.DataFrame())
    opt_results = backtest_results.get("optimization_results", pd.DataFrame())

    report = {
        "timestamp": datetime.now().isoformat(),
        "cache_key": cache_key,
        "strategy": strategy_config,
        "description": backtest_results.get("description", ""),
        "default_params": backtest_results.get("default_params", {}),
        "default_performance": performance_summary(default_trades) if len(default_trades) > 0 else {},
        "top_optimized": opt_results.sort_values("profit_factor", ascending=False).head(20).to_dict("records") if isinstance(opt_results, pd.DataFrame) and len(opt_results) > 0 else [],
    }

    report_path = OUTPUT_DIR / f"{cache_key}_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\n  Report saved: {report_path}")
    return report


def run(strategy_config: dict, backtest_results: dict, cache_key: str, data_info: str) -> dict:
    """Generate and save the final report."""
    print("\n[STAGE 6: REPORT]")
    print_report(strategy_config, backtest_results, data_info)
    report = save_report(strategy_config, backtest_results, cache_key)
    return report
