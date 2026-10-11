"""Devil's advocate: the case AGAINST promoting a candidate.

Every other module here is trying to find a champion. This one is trying to
stop it. It is given the leading candidate and asked to argue, on the evidence,
that the promotion is a mistake.

WHY IT IS NOT AN LLM. E4 is the reason. The last multi-agent idea that came
through this pipeline (`b9a107049e52`, "Bull vs Bear Debate") had its six
agents silently replaced by hand-set technical conditions, because an LLM layer
cannot be backtested -- so what got measured was never the thing proposed. An
objection you cannot reproduce is not evidence, it is atmosphere. Every check
below is deterministic and re-runnable on demand. `narrate()` exists to put
these findings into prose, and it is explicitly cosmetic: it can add no
objection that the checks did not already produce.

    from advocate import case_against
    case_against("SPY")          # -> verdict + objections, worst first

Severity:
    blocking  the promotion should not happen on this evidence
    serious   a real weakness; promote only with a stated reason
    minor     worth recording, not worth stopping for
"""

import re

import numpy as np
import pandas as pd

import analysis
import engine
from strategies import REGISTRY, SLOW_STRATEGIES

SEVERITY_RANK = {"blocking": 0, "serious": 1, "minor": 2}

# A deflated sharpe is a probability that the edge survives the search that
# found it. 0.95 is the conventional bar; below 0.75 the ranking is not
# distinguishing the winner from its own candidate pool at all.
DSR_SERIOUS, DSR_BLOCKING = 0.95, 0.75
SPREAD_SERIOUS, SPREAD_MINOR = 0.50, 0.30
BH_MARGIN_SERIOUS = 0.05
MIN_SWITCHES = 30
COST_STRESS_MULT = 2.0
CROWDING_SERIOUS = 0.90


def _objection(check, severity, finding, detail=None):
    return {"check": check, "severity": severity, "finding": finding,
            "detail": detail or {}}


# ------------------------------------------------------------------ checks --
def _check_selection_noise(row, _ctx):
    dsr = row.get("deflated_sharpe")
    null = row.get("null_max_sharpe")
    if dsr is None:
        return _objection("selection_noise", "serious",
                          "No deflated sharpe could be computed, so the search "
                          "that produced this candidate is uncharged.")
    if dsr < DSR_BLOCKING:
        sev = "blocking"
    elif dsr < DSR_SERIOUS:
        sev = "serious"
    else:
        return None
    return _objection(
        "selection_noise", sev,
        f"Deflated sharpe {dsr:.2f} is below the {DSR_SERIOUS} bar: after "
        f"charging for {row.get('trials')} ranked candidates, this is not "
        f"clearly better than the best of that many zero-edge strategies "
        f"(which would score {null}).",
        {"deflated_sharpe": dsr, "null_max_sharpe": null,
         "trials": row.get("trials")})


def _check_margin_over_null(row, _ctx):
    null, sr = row.get("null_max_sharpe"), row.get("robust_sharpe")
    if null is None or sr is None:
        return None
    margin = sr - null
    if margin > 0.10:
        return None
    return _objection(
        "margin_over_null", "blocking" if margin <= 0 else "serious",
        f"Worst-window sharpe {sr:.2f} sits only {margin:+.2f} above the "
        f"{null:.2f} expected from pure selection. The entire measured edge is "
        f"inside the noise of having looked at {row.get('trials')} strategies.",
        {"margin": round(margin, 3)})


def _check_regime_instability(row, _ctx):
    spread = row.get("spread")
    if spread is None or spread < SPREAD_MINOR:
        return None
    sev = "serious" if spread >= SPREAD_SERIOUS else "minor"
    return _objection(
        "regime_instability", sev,
        f"Sharpe swings {spread:.2f} between its best and worst regime "
        f"({row.get('robust_sharpe')} to {row.get('best_sharpe')}). A rule "
        f"whose score depends this much on the window is a rule whose next "
        f"window is a coin toss.",
        {"spread": spread})


def _check_buyhold_margin(row, _ctx):
    windows = row.get("windows") or {}
    margins = {w: round(v["sharpe"] - v["buyhold_sharpe"], 3)
               for w, v in windows.items() if "sharpe" in v}
    if not margins:
        return None
    thin = min(margins.values())
    if thin > BH_MARGIN_SERIOUS:
        return None
    return _objection(
        "buyhold_margin", "blocking" if thin <= 0 else "serious",
        f"In its thinnest window the candidate beats buy-and-hold by only "
        f"{thin:+.3f} sharpe. Holding the index is free, has no promotion "
        f"risk, and needs no monitoring.",
        {"margins_by_window": margins})


def _check_sample_size(row, _ctx):
    windows = row.get("windows") or {}
    sw = [v.get("switches") for v in windows.values() if v.get("switches") is not None]
    if not sw:
        return None
    fewest = min(sw)
    if fewest >= MIN_SWITCHES:
        return None
    return _objection(
        "sample_size", "serious" if fewest < MIN_SWITCHES / 2 else "minor",
        f"As few as {fewest} signal changes in a window. A sharpe computed "
        f"over that many decisions is an estimate with a very wide error bar, "
        f"whatever the daily bar count says.",
        {"fewest_switches": fewest, "switches_by_window":
            {w: v.get("switches") for w, v in windows.items()}})


def _check_data_floor(row, _ctx):
    windows = row.get("windows") or {}
    skipped = {w: v.get("skipped") for w, v in windows.items() if v.get("skipped")}
    if not skipped:
        return None
    return _objection(
        "data_floor", "serious",
        f"Scored on only {row.get('windows_scored')} of "
        f"{len(analysis.ROBUST_WINDOWS)} windows; the rest were skipped because "
        f"its auxiliary data does not reach back that far. It has never been "
        f"tested in the regimes it is missing.",
        {"skipped": skipped})


def _check_negative_window(row, _ctx):
    windows = row.get("windows") or {}
    bad = {w: v["sharpe"] for w, v in windows.items()
           if "sharpe" in v and v["sharpe"] <= 0}
    if not bad:
        return None
    return _objection(
        "negative_window", "blocking",
        f"Negative excess sharpe in {len(bad)} window(s): {bad}. It lost to "
        f"cash, after costs, in a regime it has already seen.",
        {"windows": bad})


def _check_drawdown(row, _ctx):
    windows = row.get("windows") or {}
    dds = {w: v.get("max_drawdown_pct") for w, v in windows.items()
           if v.get("max_drawdown_pct") is not None}
    if not dds:
        return None
    worst = min(dds.values())
    if worst > -30.0:
        return None
    return _objection(
        "drawdown", "serious" if worst <= -40 else "minor",
        f"Deepest drawdown {worst:.1f}%. The reason to run a timing rule "
        f"instead of holding the index is a shallower hole; this one is not "
        f"obviously shallower.",
        {"max_drawdown_by_window": dds})


def _check_cost_fragility(row, ctx):
    """Re-score at double the cost assumption. If the edge evaporates, the
    result was a statement about the fee model, not about the market."""
    name = row["strategy"]
    stressed = analysis.robust_score(name, ctx["symbol"],
                                     ctx["cost_bps"] * COST_STRESS_MULT)
    sr0, sr1 = row.get("robust_sharpe"), stressed.get("robust_sharpe")
    if sr0 is None or sr1 is None:
        return None
    drop = sr0 - sr1
    ctx["cost_stress"] = {"cost_bps": ctx["cost_bps"] * COST_STRESS_MULT,
                          "robust_sharpe": sr1, "drop": round(drop, 3)}
    if sr1 <= 0:
        sev = "blocking"
    elif drop >= 0.15:
        sev = "serious"
    elif drop >= 0.08:
        sev = "minor"
    else:
        return None
    return _objection(
        "cost_fragility", sev,
        f"At {ctx['cost_bps'] * COST_STRESS_MULT:.0f} bps/side the worst-window "
        f"sharpe falls {sr0:.2f} -> {sr1:.2f}. Our 5 bps is an assumption, not "
        f"a quote; a rule this sensitive to it is betting on the fee model.",
        ctx["cost_stress"])


def _equity_returns(name, symbol, start, cost_bps):
    df = engine.fetch(symbol, start)
    sig = REGISTRY[name]["fn"](df, {"_symbol": symbol})
    eq, _ = engine.equity_from_signal(df["Close"], sig, cost_bps=cost_bps,
                                      open_=df.get("Open"))
    return eq.pct_change().dropna()


def _check_crowding(row, ctx):
    """A candidate that moves with the incumbent adds risk, not diversification."""
    inc = ctx.get("incumbent")
    if not inc or inc == row["strategy"] or inc not in REGISTRY:
        return None
    try:
        start = analysis.ROBUST_WINDOWS[0]
        a = _equity_returns(row["strategy"], ctx["symbol"], start, ctx["cost_bps"])
        b = _equity_returns(inc, ctx["symbol"], start, ctx["cost_bps"])
        joined = pd.concat([a, b], axis=1).dropna()
        if len(joined) < 250:
            return None
        rho = float(joined.corr().iloc[0, 1])
    except Exception as e:
        return _objection("crowding", "minor",
                          f"Could not measure correlation to the incumbent "
                          f"({type(e).__name__}).")
    ctx["correlation_to_incumbent"] = round(rho, 3)
    if rho < CROWDING_SERIOUS:
        return None
    return _objection(
        "crowding", "serious",
        f"Daily returns correlate {rho:.2f} with the incumbent `{inc}`. "
        f"Swapping one for the other changes the label on the book far more "
        f"than it changes the book.",
        {"incumbent": inc, "correlation": round(rho, 3)})


CHECKS = [_check_selection_noise, _check_margin_over_null, _check_negative_window,
          _check_buyhold_margin, _check_cost_fragility, _check_regime_instability,
          _check_crowding, _check_data_floor, _check_sample_size, _check_drawdown]


# ------------------------------------------------------------------- entry --
def case_against(symbol: str, strategy: str | None = None, cost_bps: float = 5.0,
                 incumbent: str | None = None, ranked: list | None = None) -> dict:
    """Build the case against promoting `strategy` (default: the leading one).

    Returns a verdict and the objections, worst first. The verdict is advice,
    not enforcement -- `auto_promote` decides what to do with it.
    """
    if ranked is None:
        ranked = analysis.rank_robust(symbol, cost_bps, exclude=SLOW_STRATEGIES)
    if not ranked:
        return {"symbol": symbol, "verdict": "NO CANDIDATE", "objections": []}

    if strategy:
        row = next((r for r in ranked if r["strategy"] == strategy), None)
        if row is None:
            return {"symbol": symbol, "strategy": strategy,
                    "verdict": "NOT SCOREABLE", "objections": []}
    else:
        eligible = [r for r in ranked if r.get("beats_buyhold_all_windows")]
        row = (eligible or ranked)[0]

    ctx = {"symbol": symbol, "cost_bps": cost_bps, "incumbent": incumbent}
    objections = []
    for check in CHECKS:
        try:
            o = check(row, ctx)
        except Exception as e:                       # a broken check must not
            o = _objection(check.__name__.lstrip("_"), "minor",  # silence the rest
                           f"check failed: {type(e).__name__}")
        if o:
            objections.append(o)
    objections.sort(key=lambda o: SEVERITY_RANK[o["severity"]])

    counts = {s: sum(1 for o in objections if o["severity"] == s)
              for s in ("blocking", "serious", "minor")}
    if counts["blocking"]:
        verdict = "BLOCK"
    elif counts["serious"]:
        verdict = "CONTEST"
    else:
        verdict = "NO OBJECTION"

    return {
        "symbol": symbol,
        "strategy": row["strategy"],
        "robust_sharpe": row.get("robust_sharpe"),
        "deflated_sharpe": row.get("deflated_sharpe"),
        "verdict": verdict,
        "counts": counts,
        "objections": objections,
        "evidence": {k: v for k, v in ctx.items()
                     if k not in ("symbol", "cost_bps", "incumbent")},
        "note": ("Deterministic checks only. Re-run to reproduce exactly; see "
                 "advocate.py for why this is not an LLM."),
    }


def summary_line(case: dict) -> str:
    """One line fit for an SMS -- the scheduler has 300 characters."""
    c = case.get("counts", {})
    head = f"[{case['verdict']}] {case.get('strategy', '?')} "
    head += f"dsr={case.get('deflated_sharpe')} "
    head += f"blocking={c.get('blocking', 0)} serious={c.get('serious', 0)}"
    top = case.get("objections") or []
    if top:
        # split on sentence ends only -- "sharpe 0.55" must not become "sharpe 0"
        first = re.split(r"(?<=[a-zA-Z)])\. ", top[0]["finding"])[0]
        head += " | " + first
    return head[:300]


def narrate(case: dict) -> str:
    """Prose rendering of the SAME objections. Cosmetic by construction: it
    reads `case`, it does not re-examine the candidate, and it cannot raise an
    objection the checks did not already make."""
    if case["verdict"] == "NO OBJECTION":
        return (f"No objection to promoting {case.get('strategy')}. Every check "
                f"passed; that is not proof it works, only that this module "
                f"found nothing to argue with.")
    lines = [f"The case against promoting {case['strategy']} "
             f"(worst-window sharpe {case.get('robust_sharpe')}):", ""]
    for i, o in enumerate(case["objections"], 1):
        lines.append(f"{i}. [{o['severity'].upper()}] {o['finding']}")
    lines.append("")
    lines.append({"BLOCK": "Recommendation: do not promote on this evidence.",
                  "CONTEST": "Recommendation: promote only with a written reason "
                             "answering the serious objections above."}
                 .get(case["verdict"], ""))
    return "\n".join(lines)
