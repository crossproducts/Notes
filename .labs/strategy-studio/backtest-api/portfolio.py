"""Portfolio analysis — inverse-volatility weighting across all champions.

analysis(db) loads equity curves from Postgres (series='strategy'), aligns
them on common trading dates, computes pairwise correlations, per-symbol
annualised vol/sharpe, and inverse-vol weights (hard-capped at
PORTFOLIO_MAX_WEIGHT_PCT per symbol; excess waterfills to uncapped names, any
remainder stays in cash).  Returns a dict ready to be JSON-serialised
by the /portfolio/analysis endpoint.

No network calls; pure Postgres + numpy/pandas.
"""

import os

import numpy as np
import pandas as pd
from sqlalchemy import text

from engine import RISK_FREE_RATE

PORTFOLIO_MAX_WEIGHT_PCT = float(os.getenv("PORTFOLIO_MAX_WEIGHT_PCT", "40.0"))
MIN_OVERLAP_DAYS = 60  # minimum common trading-day rows required to include a champion


def analysis(db) -> dict:
    """Compute portfolio stats for all champions with usable equity curves.

    Returns a dict with keys:
      champions       — list of {symbol, run_id, strategy, vol, sharpe, weight}
      skipped         — list of {symbol, run_id, reason}
      correlation     — {symbols: [...], matrix: [[...], ...]}
      blended_sharpe  — float
      blended_max_drawdown_pct — float
      weights_sum     — float (should be ~1.0 after normalisation)
      max_weight_cap_pct — the env cap applied
    """
    # Load all champions with their run_ids and strategies
    champs_df = pd.read_sql(
        text(
            "SELECT c.symbol, c.run_id, r.strategy "
            "FROM champions c JOIN runs r ON r.run_id = c.run_id"
        ),
        db,
    )

    if len(champs_df) == 0:
        return _empty("no champions in database")

    # Load equity curves for all champion run_ids in one query
    run_ids = champs_df["run_id"].tolist()
    placeholders = ", ".join(f":r{i}" for i in range(len(run_ids)))
    params = {f"r{i}": rid for i, rid in enumerate(run_ids)}
    curves_df = pd.read_sql(
        text(
            f"SELECT run_id, ts, equity FROM equity_curve "
            f"WHERE run_id IN ({placeholders}) AND series='strategy' ORDER BY ts"
        ),
        db,
        params=params,
    )
    curves_df["ts"] = pd.to_datetime(curves_df["ts"]).dt.normalize()  # strip time, keep date

    # Build per-symbol daily-return series; keep only the date part of the index
    series_map: dict[str, pd.Series] = {}  # symbol -> daily return series (date index)
    skipped: list[dict] = []

    for _, row in champs_df.iterrows():
        sym = row["symbol"]
        rid = row["run_id"]
        curve = curves_df[curves_df["run_id"] == rid].copy()
        if len(curve) < 2:
            skipped.append({"symbol": sym, "run_id": rid,
                             "reason": "equity curve has fewer than 2 rows"})
            continue
        curve = curve.sort_values("ts").drop_duplicates("ts").set_index("ts")["equity"]
        daily_ret = curve.pct_change().dropna()
        series_map[sym] = daily_ret

    rid_by_sym = dict(zip(champs_df["symbol"], champs_df["run_id"]))

    # Too-short histories can't contribute regardless of alignment
    for sym in list(series_map):
        if len(series_map[sym]) < MIN_OVERLAP_DAYS:
            skipped.append({
                "symbol": sym, "run_id": rid_by_sym[sym],
                "reason": f"only {len(series_map[sym])} days of history (need >= {MIN_OVERLAP_DAYS})",
            })
            del series_map[sym]

    # Align on common dates (inner join). The join truncates everyone to the
    # newest champion's window — so if the common window is too short, drop the
    # shortest-history champion and retry rather than 404ing the whole book.
    aligned = None
    while len(series_map) >= 2:
        candidate = pd.concat(series_map, axis=1, join="inner").dropna()
        if len(candidate) >= MIN_OVERLAP_DAYS:
            aligned = candidate
            break
        shortest = min(series_map, key=lambda k: len(series_map[k]))
        skipped.append({
            "symbol": shortest, "run_id": rid_by_sym[shortest],
            "reason": (f"common window only {len(candidate)} days with this champion "
                       f"included (need >= {MIN_OVERLAP_DAYS})"),
        })
        del series_map[shortest]

    if aligned is None:
        return _empty(
            "portfolio needs at least 2 champions with sufficient overlapping history",
            skipped=skipped,
        )
    final_symbols = list(aligned.columns)

    # Per-symbol stats
    rf_daily = (1 + RISK_FREE_RATE) ** (1 / 252) - 1
    sym_stats: list[dict] = []
    for sym in final_symbols:
        ret = aligned[sym]
        vol_annual = float(ret.std() * np.sqrt(252))
        sharpe = float((ret.mean() - rf_daily) / ret.std() * np.sqrt(252)) if ret.std() > 0 else 0.0
        sym_stats.append({"symbol": sym, "vol_annual": vol_annual, "sharpe": round(sharpe, 4)})

    # Inverse-volatility weights (raw)
    vols = np.array([s["vol_annual"] for s in sym_stats])
    inv_vols = np.where(vols > 0, 1.0 / vols, 0.0)
    raw_sum = inv_vols.sum()
    if raw_sum == 0:
        # degenerate: equal weight
        weights = np.ones(len(final_symbols)) / len(final_symbols)
    else:
        weights = inv_vols / raw_sum

    # Apply per-symbol cap by WATERFILL: excess from capped names is
    # redistributed only to uncapped names (re-normalising across capped names
    # would silently push them back over the cap). If everyone hits the cap
    # (n * cap < 1), the remainder stays in cash — the cap is a hard promise.
    cap = PORTFOLIO_MAX_WEIGHT_PCT / 100.0
    capped_mask = np.zeros(len(weights), dtype=bool)
    for _ in range(len(weights)):
        over = (weights > cap + 1e-12) & ~capped_mask
        if not over.any():
            break
        excess = float((weights[over] - cap).sum())
        weights[over] = cap
        capped_mask |= over
        free = ~capped_mask
        if free.any() and weights[free].sum() > 0:
            weights[free] += excess * weights[free] / weights[free].sum()
    cash_weight = max(0.0, 1.0 - float(weights.sum()))

    # Attach weights to sym_stats
    for i, s in enumerate(sym_stats):
        s["weight"] = round(float(weights[i]), 6)

    # Look up run_id / strategy for each final symbol
    lookup = champs_df.set_index("symbol")
    for s in sym_stats:
        sym = s["symbol"]
        s["run_id"]   = lookup.loc[sym, "run_id"]
        s["strategy"] = lookup.loc[sym, "strategy"]

    # Pairwise correlation matrix
    corr = aligned[final_symbols].corr()
    corr_matrix = [[round(float(corr.loc[r, c]), 4) for c in final_symbols] for r in final_symbols]

    # Blended (weighted) return series; the un-deployed cash fraction earns rf
    w_series = pd.Series(weights, index=final_symbols)
    blended = aligned[final_symbols].dot(w_series) + rf_daily * cash_weight

    blended_sharpe = float(
        (blended.mean() - rf_daily) / blended.std() * np.sqrt(252)
    ) if blended.std() > 0 else 0.0

    # Max drawdown of blended series
    blended_equity = (1 + blended).cumprod()
    peak = blended_equity.cummax()
    blended_max_dd = float(((blended_equity - peak) / peak).min() * 100)

    return {
        "champions": sym_stats,
        "skipped": skipped,
        "correlation": {
            "symbols": final_symbols,
            "matrix": corr_matrix,
        },
        "blended_sharpe": round(blended_sharpe, 4),
        "blended_max_drawdown_pct": round(blended_max_dd, 2),
        "weights_sum": round(float(weights.sum()), 6),
        "cash_weight": round(cash_weight, 6),
        "max_weight_cap_pct": PORTFOLIO_MAX_WEIGHT_PCT,
    }


def _empty(reason: str, skipped: list | None = None) -> dict:
    """Return an empty-portfolio sentinel that the endpoint can 404 on."""
    return {
        "_insufficient": True,
        "reason": reason,
        "champions": [],
        "skipped": skipped or [],
        "correlation": {"symbols": [], "matrix": []},
        "blended_sharpe": None,
        "blended_max_drawdown_pct": None,
        "weights_sum": 0.0,
        "max_weight_cap_pct": PORTFOLIO_MAX_WEIGHT_PCT,
    }
