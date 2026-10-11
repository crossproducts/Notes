"""Walk-forward validation and Monte Carlo resampling."""

import itertools
import math

import numpy as np
import pandas as pd

import engine
from strategies import REGISTRY


def _combos(grid: dict):
    keys = list(grid.keys())
    for vals in itertools.product(*grid.values()):
        yield dict(zip(keys, vals))


def walkforward(strategy: str, symbol: str, start: str,
                train_years: int = 2, test_months: int = 6) -> dict:
    """Rolling anti-overfitting check: optimize params on a train window, apply
    them UNSEEN on the following test window, roll forward, stitch the
    out-of-sample segments. If OOS falls apart vs in-sample, it's curve-fit."""
    spec = REGISTRY[strategy]
    df = engine.fetch(symbol, start)
    if len(df) < 300:
        raise ValueError("not enough data")

    train_bars = train_years * 252
    test_bars = int(test_months * 21)
    windows, oos_factor = [], 1.0

    i = train_bars
    while i + 20 < len(df):
        train, test = df.iloc[i - train_bars:i], df.iloc[i:i + test_bars]
        best_params, best_ret = None, -np.inf
        for params in _combos(spec["grid"]):
            p = {**params, "_symbol": symbol}
            sig = spec["fn"](train, p)
            eq, _ = engine.equity_from_signal(train["Close"], sig, open_=train.get("Open"))
            r = eq.iloc[-1] / eq.iloc[0] - 1
            if r > best_ret:
                best_ret, best_params = r, params

        p = {**best_params, "_symbol": symbol}
        sig = spec["fn"](pd.concat([train, test]), p).loc[test.index]
        eq, _ = engine.equity_from_signal(test["Close"], sig, open_=test.get("Open"))
        oos_ret = eq.iloc[-1] / eq.iloc[0] - 1
        oos_factor *= (1 + oos_ret)
        windows.append({
            "test_start": str(test.index[0].date()), "test_end": str(test.index[-1].date()),
            "chosen_params": best_params,
            "train_return_pct": round(float(best_ret) * 100, 2),
            "oos_return_pct": round(float(oos_ret) * 100, 2),
        })
        i += test_bars

    return {
        "strategy": strategy, "symbol": symbol,
        "windows": windows,
        "stitched_oos_return_pct": round((oos_factor - 1) * 100, 2),
        "verdict": ("params unstable across windows — likely curve-fit"
                    if len({str(w["chosen_params"]) for w in windows}) == len(windows) and len(windows) > 2
                    else "params reasonably stable"),
    }


def montecarlo(equity: pd.Series, n_paths: int = 1000) -> dict:
    """Bootstrap-resample daily returns: the DISTRIBUTION of outcomes this
    strategy could have produced, not the one lucky path that happened."""
    rets = equity.pct_change().dropna().values
    if len(rets) < 30:
        raise ValueError("not enough return observations")
    rng = np.random.default_rng(42)
    idx = rng.integers(0, len(rets), size=(n_paths, len(rets)))
    paths = np.cumprod(1 + rets[idx], axis=1)
    finals = (paths[:, -1] - 1) * 100
    peaks = np.maximum.accumulate(paths, axis=1)
    dds = ((paths - peaks) / peaks).min(axis=1) * 100

    pct = lambda a, q: round(float(np.percentile(a, q)), 2)
    return {
        "n_paths": n_paths,
        "final_return_pct": {"p5": pct(finals, 5), "p50": pct(finals, 50), "p95": pct(finals, 95)},
        "max_drawdown_pct": {"p5": pct(dds, 5), "p50": pct(dds, 50), "p95": pct(dds, 95)},
        "prob_negative_pct": round(float((finals < 0).mean() * 100), 1),
    }


# --- E6: regime-robust champion scoring --------------------------------------
# A champion picked from one 6.5-year window is an artifact of that window.
# Measured 2020+, `momentum` scores sharpe 0.95 and ranks #1; measured 2000+ it
# scores 0.23 and ranks #9, below buy-and-hold. Rank on the WORST window a
# strategy has been measured in, not the luckiest one.

# Windows must span >= 2 bear markets between them.
#   2000 -> dot-com, GFC, COVID, 2022      2007 -> GFC, COVID, 2022
#   2020 -> 2022 only (kept for continuity with the old single-window view)
ROBUST_WINDOWS = ["2000-01-01", "2007-01-01", "2020-01-01"]

# Auxiliary-data inception. Before these dates the strategy reindex+ffills a
# series that does not exist yet -> NaN -> comparison False -> permanently long.
# It silently becomes buy-and-hold and scores beautifully. Do not score it there.
DATA_FLOOR = {"vix_gold_filter": "2005-01-01", "rotation_top_k": "2005-01-01"}


def _window_sharpe(strategy: str, symbol: str, start: str, cost_bps: float):
    df = engine.fetch(symbol, start)
    if len(df) < 300:
        return None
    sig = REGISTRY[strategy]["fn"](df, {"_symbol": symbol})
    eq, _ = engine.equity_from_signal(df["Close"], sig, cost_bps=cost_bps,
                                      open_=df.get("Open"))
    m = engine.metrics(eq, sig, df["Close"])
    eqr = eq.pct_change().dropna()
    c = df["Close"]
    yrs = len(df) / 252
    bh_ann = (c.iloc[-1] / c.iloc[0]) ** (1 / yrs) - 1
    bh_vol = c.pct_change().dropna().std() * np.sqrt(252)
    bh_sharpe = (bh_ann - engine.RISK_FREE_RATE) / bh_vol if bh_vol else float("nan")
    return {"sharpe": m["sharpe"], "buyhold_sharpe": round(float(bh_sharpe), 2),
            # carried for the deflated sharpe (E7): sample length and the
            # non-normality correction both come from the equity returns
            "n_obs": int(len(eqr)),
            "skew": round(float(eqr.skew()), 4) if len(eqr) > 2 else 0.0,
            "kurt": round(float(eqr.kurt()) + 3.0, 4) if len(eqr) > 3 else 3.0,
            "beats_buyhold": bool(m["sharpe"] > bh_sharpe),
            "max_drawdown_pct": m["max_drawdown_pct"],
            "switches": int((sig.diff().abs() > 0).sum())}


def robust_score(strategy: str, symbol: str, cost_bps: float = 5.0) -> dict:
    """Score a strategy across regimes. `robust_sharpe` is the WORST window.

    Also reports whether it clears buy-and-hold in EVERY window -- the bar that
    separates a real timing rule from one that only looked good in a bull run.
    """
    floor = DATA_FLOOR.get(strategy)
    per = {}
    for w in ROBUST_WINDOWS:
        if floor and floor > w:
            per[w] = {"skipped": f"aux data starts {floor}"}
            continue
        try:
            r = _window_sharpe(strategy, symbol, w, cost_bps)
            if r:
                per[w] = r
        except Exception as e:
            per[w] = {"error": type(e).__name__}

    scored = [v for v in per.values() if "sharpe" in v]
    if not scored:
        return {"strategy": strategy, "robust_sharpe": None, "windows": per,
                "note": "not scoreable on any window"}
    sharpes = [v["sharpe"] for v in scored]
    worst = min(scored, key=lambda v: v["sharpe"])
    return {
        "strategy": strategy,
        # the deflated sharpe is computed on the same window we rank on
        "n_obs": worst.get("n_obs"),
        "skew": worst.get("skew", 0.0),
        "kurt": worst.get("kurt", 3.0),
        "robust_sharpe": round(min(sharpes), 2),       # worst regime
        "best_sharpe": round(max(sharpes), 2),
        "spread": round(max(sharpes) - min(sharpes), 2),
        "beats_buyhold_all_windows": all(v["beats_buyhold"] for v in scored),
        "windows_scored": len(scored),
        "windows": per,
    }


# --- E7: trials-aware scoring (deflated sharpe) -----------------------------
# A ranking reports the BEST of N candidates, and the best of N coin flips is
# not zero. Bailey & Lopez de Prado (2014) make that explicit: estimate the
# sharpe you would expect from the best of N zero-edge trials, then ask how
# confident we are that the observed sharpe beats THAT, not zero.
#
# Measured for this registry: best-of-20 zero-edge strategies score a
# worst-window sharpe of 0.29 mean / 0.48 at the 95th pct, against the
# champion's 0.44. See Trading/Decisions.md, 2026-10-11.
#
# LIMIT, stated so nobody reads more into the number than it carries: `trials`
# counts STRATEGIES ranked. `walkforward` re-optimises a parameter grid inside
# every window, which is a second search this does not charge for. The real
# trial count is higher than the number reported here, so a deflated sharpe
# from this module is an UPPER bound on confidence.
#
# TWO BIASES, PULLING OPPOSITE WAYS. Read the number knowing both:
#   1. `trials` counts STRATEGIES ranked. `walkforward` re-optimises a
#      parameter grid inside every window, a second search this does not
#      charge for -> reported confidence is too HIGH.
#   2. The published method takes V[SR] as the SAMPLING variance under the
#      null. We use the observed cross-sectional spread of a HETEROGENEOUS
#      registry, which also contains real dispersion (bollinger_squeeze at
#      -0.30 sits beside triple_momentum at 0.44). That inflates the null
#      max -> reported confidence is too LOW.
# They partially offset. Treat the output as an order-of-magnitude check on
# whether a ranking's winner is distinguishable from its own search, not as
# a precise p-value.

TRADING_DAYS = 252
EULER_GAMMA = 0.5772156649015329


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Inverse standard normal CDF, Acklam's rational approximation.

    |error| < 1.15e-9, which is far inside what matters here. Written out
    because the API image has no scipy and adding one for two call sites is
    not worth a rebuild that already crash-looped once on an unpinned dep.
    """
    if not 0.0 < p < 1.0:
        return float("-inf") if p <= 0.0 else float("inf")
    a = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
    b = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00)
    lo, hi = 0.02425, 1.0 - 0.02425
    if p < lo:
        q = math.sqrt(-2.0 * math.log(p))
        return ((((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
                / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0))
    if p > hi:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -((((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
                 / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0))
    q = p - 0.5
    r = q * q
    return ((((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
            / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0))


def expected_max_sharpe(n_trials: int, sharpe_std: float) -> float:
    """Sharpe expected from the BEST of n_trials strategies that all have zero
    true edge. Returned in whatever units sharpe_std is given in.

    sharpe_std is the cross-sectional spread of the candidates' sharpes: a
    registry whose members disagree wildly has more room for a lucky winner
    than one whose members all score the same.
    """
    if n_trials < 2 or not sharpe_std or sharpe_std <= 0:
        return 0.0
    n = float(n_trials)
    return sharpe_std * ((1.0 - EULER_GAMMA) * _norm_ppf(1.0 - 1.0 / n)
                         + EULER_GAMMA * _norm_ppf(1.0 - 1.0 / (n * math.e)))


def probabilistic_sharpe(sr_ann: float, benchmark_ann: float, n_obs,
                         skew: float = 0.0, kurt: float = 3.0):
    """P(true sharpe > benchmark), given sample length and non-normality.

    UNITS ARE THE TRAP HERE. The published formula takes PER-PERIOD sharpes;
    everything else in this codebase is ANNUALISED. Both arguments are divided
    by sqrt(252) before use -- skipping that silently inflates the result.

    `kurt` is NON-excess (3.0 for a normal), while pandas .kurt() returns
    excess, so callers add 3.
    """
    if not n_obs or n_obs < 3:
        return None
    sr = sr_ann / math.sqrt(TRADING_DAYS)
    sr0 = benchmark_ann / math.sqrt(TRADING_DAYS)
    var = 1.0 - skew * sr + ((kurt - 1.0) / 4.0) * sr * sr
    if var <= 0:
        return None
    return _norm_cdf((sr - sr0) * math.sqrt(n_obs - 1.0) / math.sqrt(var))


def annotate_deflated(rows: list) -> list:
    """Charge every row in a ranking for the size of the search that found it.

    Adds, in place: `trials`, `null_max_sharpe` (what the best of that many
    zero-edge candidates would score) and `deflated_sharpe` (confidence the
    observed worst-window sharpe beats it). Read deflated_sharpe like a
    p-value complement: 0.95 is the usual bar, below ~0.90 means the ranking
    alone cannot distinguish the winner from a lucky candidate.
    """
    scored = [r for r in rows if r.get("robust_sharpe") is not None]
    if len(scored) < 2:
        return rows
    sr = np.array([r["robust_sharpe"] for r in scored], dtype=float)
    sr0 = expected_max_sharpe(len(scored), float(sr.std(ddof=1)))
    for r in scored:
        r["trials"] = len(scored)
        r["null_max_sharpe"] = round(sr0, 3)
        d = probabilistic_sharpe(r["robust_sharpe"], sr0, r.get("n_obs"),
                                 r.get("skew", 0.0), r.get("kurt", 3.0))
        r["deflated_sharpe"] = round(d, 4) if d is not None else None
        r["clears_selection_noise"] = bool(d is not None and d >= 0.95)
    return rows


def rank_robust(symbol: str, cost_bps: float = 5.0, exclude: set | None = None,
                deflate: bool = True):
    """Every builtin ranked by worst-window sharpe.

    With deflate=True (default) each row is also charged for the size of the
    search -- see annotate_deflated. The ORDER is unchanged; the deflated
    sharpe is reported, not ranked on, because deflation is a monotone
    transform of the sharpe within one ranking and would not reorder anything.
    """
    exclude = exclude or set()
    out = [robust_score(n, symbol, cost_bps)
           for n in REGISTRY if n not in exclude]
    out = [o for o in out if o.get("robust_sharpe") is not None]
    out.sort(key=lambda o: -o["robust_sharpe"])
    if deflate:
        annotate_deflated(out)
    return out
