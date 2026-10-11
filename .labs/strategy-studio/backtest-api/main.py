"""Strategy Studio — backtest API.

Endpoints (n8n nodes call these; results land in Postgres for Grafana):
  GET  /strategies          catalog: built-ins + imported video-pipeline strategies
  POST /backtest            run one strategy (risk controls, regime filter, benchmarks)
  POST /walkforward         rolling train/test validation (anti-overfitting)
  GET  /montecarlo/{run_id} bootstrap the run's returns -> outcome distribution
  GET  /analyze/{run_id}    local Ollama (qwen) writes a plain-English summary
  GET  /runs                recent runs
"""

import importlib.util
import json
import os
import sys
import urllib.request
import uuid
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, text

import analysis
import engine
from strategies import REGISTRY, SLOW_STRATEGIES

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://studio:studio@localhost:5433/backtests")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
IMPORTED_DIR = Path(os.getenv("IMPORTED_DIR", "/app/imported"))

db = create_engine(DATABASE_URL)
app = FastAPI(title="Strategy Studio Backtest API")

UI_DIR = Path(__file__).parent / "ui"

DDL = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    created TIMESTAMPTZ DEFAULT now(),
    strategy TEXT, symbol TEXT, params JSONB,
    total_return_pct DOUBLE PRECISION, benchmark_return_pct DOUBLE PRECISION,
    spy_return_pct DOUBLE PRECISION, max_drawdown_pct DOUBLE PRECISION,
    sharpe DOUBLE PRECISION, trades INT, win_rate DOUBLE PRECISION,
    regime_filter BOOLEAN DEFAULT false, halted BOOLEAN DEFAULT false
);
CREATE TABLE IF NOT EXISTS equity_curve (
    run_id TEXT, ts TIMESTAMPTZ, equity DOUBLE PRECISION
);
ALTER TABLE equity_curve ADD COLUMN IF NOT EXISTS series TEXT DEFAULT 'strategy';
CREATE TABLE IF NOT EXISTS paper_actions (
    ts TIMESTAMPTZ DEFAULT now(),
    symbol TEXT, strategy TEXT, signal INT,
    action TEXT, detail TEXT, equity DOUBLE PRECISION
);
CREATE TABLE IF NOT EXISTS champions (
    symbol TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    promoted TIMESTAMPTZ DEFAULT now(),
    note TEXT
);
CREATE TABLE IF NOT EXISTS risk_state (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS video_queue (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    note TEXT, cache_key TEXT,
    created TIMESTAMPTZ DEFAULT now(),
    updated TIMESTAMPTZ DEFAULT now()
);
"""


@app.on_event("startup")
def init_db():
    with db.begin() as conn:
        for stmt in DDL.strip().split(";"):
            if stmt.strip():
                conn.execute(text(stmt))
    import scheduler
    scheduler.start()


# ---- operator dashboard (static single-page app) ----

if UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")


@app.get("/ui", include_in_schema=False)
def ui_index():
    """Serve the operator dashboard."""
    index = UI_DIR / "index.html"
    if not index.exists():
        raise HTTPException(404, "ui/ not present in this deployment")
    return FileResponse(str(index))


@app.get("/scheduler")
def scheduler_status():
    import scheduler
    return scheduler.jobs_status()


# ---- imported video-pipeline strategies (mounted from audio-extraction/cache) ----

def imported_strategies() -> dict:
    out = {}
    if IMPORTED_DIR.exists():
        for f in sorted(IMPORTED_DIR.glob("*_backtest.py")):
            out[f"video:{f.name.replace('_backtest.py', '')}"] = f
    return out


def run_imported(path: Path, params: dict):
    spec = importlib.util.spec_from_file_location(f"imp_{path.stem}", str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    merged = {**getattr(mod, "DEFAULT_PARAMS", {}), **params}
    trades = mod.run_backtest(None, merged)  # video strategies fetch their own data
    if trades is None or len(trades) == 0:
        raise HTTPException(400, "imported strategy produced no trades")
    trades["date"] = pd.to_datetime(trades["date"])
    trades = trades.sort_values("date")
    equity = 100_000 + trades["pnl"].cumsum() * 100  # points -> rough $ scale
    equity.index = trades["date"]
    pnls = trades["pnl"]
    peak = equity.cummax()
    return equity, {
        "total_return_pct": round(float(equity.iloc[-1] / 100_000 - 1) * 100, 2),
        "max_drawdown_pct": round(float(((equity - peak) / peak).min() * 100), 2),
        "sharpe": 0.0,
        "trades": int(len(trades)),
        "win_rate": round(float((pnls > 0).mean() * 100), 1),
    }


# ---- request models ----

class RiskParams(BaseModel):
    position_size_pct: float = 100.0
    max_dd_stop_pct: float | None = None   # circuit breaker: halt past this drawdown


class BacktestRequest(BaseModel):
    strategy: str = "momentum"
    symbol: str = "SPY"
    start: str = "2020-01-01"
    params: dict = {}
    risk: RiskParams = RiskParams()
    regime_filter: bool = False            # only trade when SPY > 200d MA
    cost_bps: float = 5.0                  # per-side spread+slippage; 0 = frictionless fantasy


class WalkforwardRequest(BaseModel):
    strategy: str = "momentum"
    symbol: str = "SPY"
    start: str = "2018-01-01"
    train_years: int = 2
    test_months: int = 6


# ---- endpoints ----

@app.get("/health")
def health():
    return {"ok": True}


@app.get("/strategies")
def strategies():
    return {
        "builtin": {k: {"grid": v["grid"]} for k, v in REGISTRY.items()},
        "imported": list(imported_strategies().keys()),
    }


def _persist(run_id, req, m, bench, equity, halted=False, extra_curves: dict | None = None):
    with db.begin() as conn:
        conn.execute(text(
            "INSERT INTO runs (run_id, strategy, symbol, params, total_return_pct, "
            "benchmark_return_pct, spy_return_pct, max_drawdown_pct, sharpe, trades, "
            "win_rate, regime_filter, halted) VALUES (:r,:s,:sym,:p,:tr,:br,:spy,:dd,"
            ":sh,:t,:w,:rf,:h)"),
            {"r": run_id, "s": req.strategy, "sym": req.symbol,
             "p": json.dumps(req.params), "tr": m["total_return_pct"],
             "br": bench.get("benchmark_return_pct"), "spy": bench.get("spy_return_pct"),
             "dd": m["max_drawdown_pct"], "sh": m["sharpe"], "t": m["trades"],
             "w": m["win_rate"], "rf": getattr(req, "regime_filter", False), "h": halted})
        curves = {"strategy": equity, **(extra_curves or {})}
        for series, curve in curves.items():
            rows = [{"r": run_id, "ts": ts.to_pydatetime(), "e": float(v), "sr": series}
                    for ts, v in curve.items()]
            conn.execute(text(
                "INSERT INTO equity_curve (run_id, ts, equity, series) VALUES (:r,:ts,:e,:sr)"), rows)


@app.post("/backtest")
def backtest(req: BacktestRequest):
    run_id = uuid.uuid4().hex[:12]

    imported = imported_strategies()
    if req.strategy in imported:
        equity, m = run_imported(imported[req.strategy], req.params)
        w_start = str(equity.index[0].date())
        bench = engine.benchmarks("SPY", equity.index, w_start)
        curves = engine.benchmark_curves("SPY", equity.index, w_start)
        _persist(run_id, req, m, bench, equity, extra_curves=curves)
        return {"run_id": run_id, **m, **bench}

    if req.strategy not in REGISTRY:
        raise HTTPException(400, f"unknown strategy '{req.strategy}'")

    df = engine.fetch(req.symbol, req.start)
    if len(df) < 60:
        raise HTTPException(400, "not enough data")

    params = {**req.params, "_symbol": req.symbol}
    signal = REGISTRY[req.strategy]["fn"](df, params)
    if req.regime_filter:
        signal = signal * engine.regime_mask(df.index, req.start)

    equity, halted = engine.equity_from_signal(
        df["Close"], signal,
        position_size_pct=req.risk.position_size_pct,
        max_dd_stop_pct=req.risk.max_dd_stop_pct,
        cost_bps=req.cost_bps,
        open_=df.get("Open"))  # fill at next open — matches live 9:35 execution

    m = engine.metrics(equity, signal, df["Close"])
    bench = engine.benchmarks(req.symbol, df.index, req.start)
    curves = engine.benchmark_curves(req.symbol, df.index, req.start)
    _persist(run_id, req, m, bench, equity, halted, extra_curves=curves)
    return {"run_id": run_id, **m, **bench, "halted_by_risk_engine": halted}


@app.post("/walkforward")
def walkforward(req: WalkforwardRequest):
    if req.strategy not in REGISTRY:
        raise HTTPException(400, f"walk-forward supports built-ins only, not '{req.strategy}'")
    try:
        return analysis.walkforward(req.strategy, req.symbol, req.start,
                                    req.train_years, req.test_months)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/montecarlo/{run_id}")
def montecarlo(run_id: str, n_paths: int = 1000):
    curve = pd.read_sql(text(
        "SELECT ts, equity FROM equity_curve WHERE run_id=:r AND series='strategy' ORDER BY ts"),
        db, params={"r": run_id})
    if len(curve) == 0:
        raise HTTPException(404, "run not found")
    equity = curve.set_index("ts")["equity"]
    try:
        return {"run_id": run_id, **analysis.montecarlo(equity, n_paths)}
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/analyze/{run_id}")
def analyze(run_id: str):
    row = pd.read_sql(text("SELECT * FROM runs WHERE run_id=:r"), db, params={"r": run_id})
    if len(row) == 0:
        raise HTTPException(404, "run not found")
    r = row.iloc[0].to_dict()
    prompt = (
        f"Backtest result — strategy: {r['strategy']} on {r['symbol']}. "
        f"Total return {r['total_return_pct']}% vs buy-and-hold {r['benchmark_return_pct']}% "
        f"and SPY {r['spy_return_pct']}%. Max drawdown {r['max_drawdown_pct']}%, "
        f"Sharpe {r['sharpe']}, {r['trades']} trades, win rate {r['win_rate']}%. "
        "In 3 short sentences: how did it do, how does it compare to just holding, "
        "and what is the main risk? Plain text.")
    payload = json.dumps({"model": OLLAMA_MODEL, "stream": False,
                          "messages": [{"role": "user", "content": prompt}]}).encode()
    try:
        rq = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=payload,
                                    headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(rq, timeout=120) as resp:
            out = json.loads(resp.read())
        return {"run_id": run_id, "model": OLLAMA_MODEL,
                "summary": out.get("message", {}).get("content", "").strip()}
    except Exception as e:
        raise HTTPException(502, f"Ollama unreachable at {OLLAMA_URL}: {e}")


@app.get("/runs")
def runs(limit: int = 20):
    df = pd.read_sql(text("SELECT * FROM runs ORDER BY created DESC LIMIT :n"),
                     db, params={"n": limit})
    return json.loads(df.to_json(orient="records", date_format="iso"))


@app.get("/equity/{run_id}")
def equity_curves(run_id: str):
    """Equity curves for a run, grouped by series as stored in the DB:
    'strategy', 'buyhold_<SYMBOL>', 'buyhold_SPY', 'risk_free'.

    Returns: {"series": {"strategy": [{"ts": ..., "equity": ...}, ...], ...}}
    """
    df = pd.read_sql(
        text("SELECT ts, equity, series FROM equity_curve WHERE run_id=:r ORDER BY ts"),
        db, params={"r": run_id})
    if len(df) == 0:
        raise HTTPException(404, f"run '{run_id}' not found")
    df["ts"] = df["ts"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    out: dict = {}
    for series, group in df.groupby("series"):
        out[series] = group[["ts", "equity"]].to_dict(orient="records")
    return {"series": out}


# ---- champion / challenger registry (MLflow-style, per symbol) ----

@app.get("/leaderboard")
def leaderboard(symbol: str = "SPY", metric: str = "sharpe", limit: int = 10):
    """Challengers ranked by a metric; the reigning champion is flagged.
    Rank on risk-adjusted metrics (sharpe) — raw return rewards luck.

    NOTE: this is a per-RUN view, and each run's sharpe is specific to the
    window it was back-tested over. A 2020-start run of a strategy will outrank
    its own full-cycle run. The champion is NOT selected from this ordering any
    more — see /champion/evaluate/{symbol}, which scores each STRATEGY across
    regimes and ranks on its worst window (E6). Expect the champion to sit
    below single-window runs here; that is the point."""
    if metric not in ("sharpe", "total_return_pct", "max_drawdown_pct", "win_rate"):
        raise HTTPException(400, "metric must be sharpe|total_return_pct|max_drawdown_pct|win_rate")
    # Every metric is "higher is better" — drawdown is stored NEGATIVE, so the
    # shallowest (best) drawdown is the largest value. Always DESC.
    order = "DESC"
    df = pd.read_sql(text(
        f"SELECT r.*, (c.run_id IS NOT NULL) AS is_champion FROM runs r "
        f"LEFT JOIN champions c ON c.run_id = r.run_id AND c.symbol = r.symbol "
        f"WHERE r.symbol = :s ORDER BY r.{metric} {order} NULLS LAST LIMIT :n"),
        db, params={"s": symbol, "n": limit})
    return json.loads(df.to_json(orient="records", date_format="iso"))


@app.post("/champion/{run_id}")
def promote(run_id: str, note: str = ""):
    """Manually promote a run to champion for its symbol (dethrones the current one)."""
    row = pd.read_sql(text("SELECT symbol FROM runs WHERE run_id=:r"), db, params={"r": run_id})
    if len(row) == 0:
        raise HTTPException(404, "run not found")
    symbol = row.iloc[0]["symbol"]
    with db.begin() as conn:
        conn.execute(text(
            "INSERT INTO champions (symbol, run_id, note) VALUES (:s,:r,:n) "
            "ON CONFLICT (symbol) DO UPDATE SET run_id=:r, promoted=now(), note=:n"),
            {"s": symbol, "r": run_id, "n": note})
    return {"symbol": symbol, "champion": run_id, "note": note}


@app.get("/champion/evaluate/{symbol}")
def champion_evaluate(symbol: str, cost_bps: float = 5.0):
    """Rank every builtin by WORST-window sharpe across regimes (E6).

    The old ranking used a single window's sharpe, which made the champion an
    artifact of its measurement period. This scores each strategy over windows
    spanning >=2 bear markets and ranks on the worst one.
    """
    rows = analysis.rank_robust(symbol, cost_bps, exclude=SLOW_STRATEGIES)
    return {"symbol": symbol, "windows": analysis.ROBUST_WINDOWS,
            "ranked": [{k: v for k, v in r.items() if k != "windows"} for r in rows],
            "detail": {r["strategy"]: r["windows"] for r in rows}}


@app.post("/champion/auto/{symbol}")
def auto_promote(symbol: str, metric: str = "sharpe", min_trades: int = 5,
                 validate: bool = True, robust: bool = True,
                 min_dsr: float | None = None):
    """Auto-promote the best run for a symbol IF it beats the current champion
    on the metric. With validate=True (default), a NEW champion must also pass
    a walk-forward gate: positive stitched out-of-sample return. Promoting on
    in-sample metrics alone is institutionalized overfitting."""
    # E6: rank by WORST-window sharpe across regimes, not one window's metric.
    # Measured 2020+ `momentum` ranks #1 (0.95); measured 2000+ it ranks #9
    # (0.23), below buy-and-hold. Single-window selection picks the strategy
    # that best fits the sample you happened to choose.
    if robust:
        ranked = analysis.rank_robust(symbol, exclude=SLOW_STRATEGIES)
        ranked = [r for r in ranked if r["beats_buyhold_all_windows"]]
        if not ranked:
            raise HTTPException(404, "no strategy beats buy-and-hold in every window")
        # E7: charge the ranking for its own size. Reported always, gated only
        # on request -- at the current registry NOTHING clears 0.95 (the
        # champion sits at ~0.54), so defaulting min_dsr on would leave the
        # book with no champion at all. That is a finding to act on
        # deliberately, not a promotion pipeline to break by surprise.
        if min_dsr is not None:
            ranked = [r for r in ranked
                      if (r.get("deflated_sharpe") or 0.0) >= min_dsr]
            if not ranked:
                raise HTTPException(404, (
                    f"no strategy clears deflated_sharpe >= {min_dsr}: the best "
                    f"worst-window sharpe is indistinguishable from the best of "
                    f"this many zero-edge trials. See /champion/evaluate/{symbol}"))
        winner = ranked[0]["strategy"]
        # Pick the LONGEST-HISTORY run of the winning strategy, not the
        # highest-sharpe one. Ordering by sharpe here would re-introduce the
        # exact single-window bias at the run level: a 2020-start run of the
        # same strategy scores 0.73 where its full-cycle run scores 0.44, and
        # the champion row would then advertise the flattering number.
        best = pd.read_sql(text(
            "SELECT r.* FROM runs r "
            "JOIN (SELECT run_id, MIN(ts) AS first_ts FROM equity_curve "
            "      GROUP BY run_id) e ON e.run_id = r.run_id "
            "WHERE r.symbol=:s AND r.strategy=:g AND r.trades >= :t "
            "ORDER BY e.first_ts ASC, r.sharpe DESC LIMIT 1"),
            db, params={"s": symbol, "g": winner, "t": min_trades})
        if len(best) == 0:
            raise HTTPException(404, f"'{winner}' wins on robustness but has no "
                                     f"stored run for {symbol}; back-test it first")
        challenger = best.iloc[0]
        challenger_robust = ranked[0]
    else:
        best = pd.read_sql(text(   # all metrics higher-is-better (dd is negative)
            f"SELECT * FROM runs WHERE symbol=:s AND trades >= :t "
            f"ORDER BY {metric} DESC NULLS LAST LIMIT 1"),
            db, params={"s": symbol, "t": min_trades})
        if len(best) == 0:
            raise HTTPException(404, f"no runs for {symbol} with >= {min_trades} trades")
        challenger = best.iloc[0]
        challenger_robust = None

    cur = pd.read_sql(text(
        "SELECT r.* FROM champions c JOIN runs r ON r.run_id = c.run_id WHERE c.symbol=:s"),
        db, params={"s": symbol})
    if len(cur) > 0:
        champ = cur.iloc[0]
        if challenger_robust:
            champ_robust = analysis.robust_score(champ["strategy"], symbol)
            better = (challenger_robust["robust_sharpe"] or -9) > (champ_robust["robust_sharpe"] or -9)
        else:
            better = challenger[metric] > champ[metric]  # higher-is-better (dd negative)
        if not better or challenger["run_id"] == champ["run_id"]:
            return {"symbol": symbol, "result": "champion defended",
                    "champion": champ["run_id"], f"champion_{metric}": float(champ[metric]),
                    "best_challenger": challenger["run_id"],
                    f"challenger_{metric}": float(challenger[metric])}

    # OOS gate: a would-be champion must survive walk-forward before wearing the belt
    if validate and challenger["strategy"] in REGISTRY:
        try:
            wf = analysis.walkforward(challenger["strategy"], symbol,
                                      analysis.ROBUST_WINDOWS[0])
            if wf["stitched_oos_return_pct"] <= 0:
                return {"symbol": symbol, "result": "challenger failed OOS gate",
                        "challenger": challenger["run_id"],
                        "strategy": challenger["strategy"],
                        "stitched_oos_return_pct": wf["stitched_oos_return_pct"],
                        "note": "in-sample winner, out-of-sample loser — not promoted"}
        except ValueError:
            pass  # not enough data to validate; allow (small-history symbols)

    with db.begin() as conn:
        conn.execute(text(
            "INSERT INTO champions (symbol, run_id, note) VALUES (:s,:r,:n) "
            "ON CONFLICT (symbol) DO UPDATE SET run_id=:r, promoted=now(), note=:n"),
            {"s": symbol, "r": challenger["run_id"], "n": f"auto-promoted on {metric}"})
    return {"symbol": symbol, "result": "new champion", "champion": challenger["run_id"],
            "strategy": challenger["strategy"], f"{metric}": float(challenger[metric])}


# ---- Alpaca PAPER trading: automate the champion's signal ----

@app.get("/paper/account")
def paper_account():
    import paper
    try:
        return paper.account_summary(paper.get_client())
    except Exception as e:
        raise HTTPException(502, f"Alpaca paper API: {e}")


@app.get("/paper/positions")
def paper_positions():
    import paper
    try:
        client = paper.get_client()
        return [{"symbol": p.symbol, "qty": float(p.qty),
                 "market_value": float(p.market_value),
                 "unrealized_pl": float(p.unrealized_pl)}
                for p in client.get_all_positions()]
    except Exception as e:
        raise HTTPException(502, f"Alpaca paper API: {e}")


@app.post("/paper/execute/{symbol}")
def paper_execute(symbol: str, position_pct: float = 10.0):
    """Automate the CHAMPION strategy for a symbol: recompute today's signal
    and reconcile the paper position to match. Schedule via n8n on market days."""
    import paper

    champ = get_champion(symbol)  # 404s if no champion
    strategy = champ["strategy"]
    if strategy not in REGISTRY:
        raise HTTPException(400,
            f"champion '{strategy}' is not a builtin signal strategy; "
            "promote a builtin champion for live execution")
    params = champ.get("params") or {}
    if isinstance(params, str):
        params = json.loads(params)

    # today's signal on fresh daily data
    df = engine.fetch(symbol, "2022-01-01")
    signal = int(REGISTRY[strategy]["fn"](df, {**params, "_symbol": symbol}).iloc[-1])

    import risk

    try:
        client = paper.get_client()
        acct = paper.account_summary(client)
        qty = paper.position_qty(client, symbol)
        pending = paper.pending_orders(client, symbol)

        # Kill switch: full halt — nothing executes (BUY or SELL)
        if risk.is_killed():
            action = "BLOCKED"
            detail = "kill switch engaged — full halt"
            with db.begin() as conn:
                conn.execute(text(
                    "INSERT INTO paper_actions (symbol, strategy, signal, action, detail, equity) "
                    "VALUES (:sym,:s,:sig,:a,:d,:e)"),
                    {"sym": symbol, "s": strategy, "sig": signal, "a": action,
                     "d": detail, "e": acct["equity"]})
            return {"symbol": symbol, "champion_strategy": strategy, "signal_today": signal,
                    "action": action, "detail": detail, "account_equity": acct["equity"],
                    "paper": True, "blocked": True}

        if pending > 0:
            action, detail = "HOLD", f"{pending} pending order(s) — waiting for fill, no action"
        elif signal == 1 and qty == 0:
            buy_notional_dollars = acct["equity"] * position_pct / 100
            ok, reason = risk.pre_trade_check(client, symbol, buy_notional_dollars)
            if not ok:
                action, detail = "BLOCKED", reason
            else:
                oid = paper.buy_notional(client, symbol, buy_notional_dollars)
                action, detail = "BUY", f"notional {position_pct}% of equity, order {oid}"
        elif signal == 0 and qty > 0:
            oid = paper.close_position(client, symbol)
            action, detail = "SELL", f"closed {qty} shares, order {oid}"
        else:
            action, detail = "HOLD", f"signal={signal}, position={qty} — already aligned"
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Alpaca paper API: {e}")

    with db.begin() as conn:
        conn.execute(text(
            "INSERT INTO paper_actions (symbol, strategy, signal, action, detail, equity) "
            "VALUES (:sym,:s,:sig,:a,:d,:e)"),
            {"sym": symbol, "s": strategy, "sig": signal, "a": action,
             "d": detail, "e": acct["equity"]})

    return {"symbol": symbol, "champion_strategy": strategy, "signal_today": signal,
            "action": action, "detail": detail, "account_equity": acct["equity"],
            "paper": True, "blocked": action == "BLOCKED"}


@app.get("/paper/log")
def paper_log(limit: int = 30):
    df = pd.read_sql(text("SELECT * FROM paper_actions ORDER BY ts DESC LIMIT :n"),
                     db, params={"n": limit})
    return json.loads(df.to_json(orient="records", date_format="iso"))


# ---- portfolio mode: allocate paper capital across ALL champions ----

@app.get("/portfolio/analysis")
def portfolio_analysis():
    """Inverse-volatility weights + correlation matrix across all champions.
    404 if fewer than 2 champions have sufficient overlapping equity-curve history."""
    import portfolio
    result = portfolio.analysis(db)
    if result.get("_insufficient"):
        raise HTTPException(404, result["reason"])
    return result


@app.post("/portfolio/execute")
def portfolio_execute(deploy_pct: float = 50.0):
    """For each champion with a computed weight, recompute today's signal and
    reconcile the paper position.  deploy_pct (0-100) is the fraction of account
    equity spread across the whole book (each symbol gets equity * deploy_pct/100 * weight).

    Only builtin-REGISTRY strategies can generate signals; others are flagged and skipped.
    Kill switch halts everything (same guard as /paper/execute).
    Every action is logged to paper_actions (detail includes portfolio w=<weight>).
    """
    import portfolio as _portfolio
    import paper
    import risk

    result = _portfolio.analysis(db)
    if result.get("_insufficient"):
        raise HTTPException(404, result["reason"])

    champions = result["champions"]  # [{symbol, run_id, strategy, weight, ...}]

    try:
        client = paper.get_client()
        acct = paper.account_summary(client)
    except Exception as e:
        raise HTTPException(502, f"Alpaca paper API: {e}")

    equity = acct["equity"]

    # Kill switch: full halt — log once and return
    if risk.is_killed():
        with db.begin() as conn:
            conn.execute(text(
                "INSERT INTO paper_actions (symbol, strategy, signal, action, detail, equity) "
                "VALUES (:sym,:s,:sig,:a,:d,:e)"),
                {"sym": None, "s": "portfolio", "sig": None, "a": "BLOCKED",
                 "d": "kill switch engaged — full halt", "e": equity})
        return {
            "blocked": True,
            "reason": "kill switch engaged — full halt",
            "account_equity": equity,
            "actions": [],
            "weights_used": {},
        }

    actions = []
    weights_used = {}

    for champ in champions:
        sym      = champ["symbol"]
        strategy = champ["strategy"]
        weight   = champ["weight"]
        run_id   = champ["run_id"]
        weights_used[sym] = weight

        # Only builtin REGISTRY strategies can recompute signals
        if strategy not in REGISTRY:
            actions.append({
                "symbol": sym, "strategy": strategy, "weight": weight,
                "action": "SKIPPED",
                "detail": f"non-builtin strategy '{strategy}' cannot generate a live signal",
            })
            with db.begin() as conn:
                conn.execute(text(
                    "INSERT INTO paper_actions (symbol, strategy, signal, action, detail, equity) "
                    "VALUES (:sym,:s,:sig,:a,:d,:e)"),
                    {"sym": sym, "s": strategy, "sig": None, "a": "SKIPPED",
                     "d": f"portfolio w={weight:.4f} — non-builtin, no signal",
                     "e": equity})
            continue

        # Load champion params
        champ_row = pd.read_sql(
            text("SELECT r.params FROM champions c JOIN runs r ON r.run_id = c.run_id "
                 "WHERE c.symbol=:s"),
            db, params={"s": sym})
        params = {}
        if len(champ_row) > 0:
            raw = champ_row.iloc[0]["params"]
            if isinstance(raw, str):
                params = json.loads(raw)
            elif isinstance(raw, dict):
                params = raw

        # Recompute today's signal
        try:
            df = engine.fetch(sym, "2022-01-01")
            signal = int(REGISTRY[strategy]["fn"](df, {**params, "_symbol": sym}).iloc[-1])
        except Exception as e:
            actions.append({
                "symbol": sym, "strategy": strategy, "weight": weight,
                "action": "ERROR",
                "detail": f"signal recompute failed: {e}",
            })
            with db.begin() as conn:
                conn.execute(text(
                    "INSERT INTO paper_actions (symbol, strategy, signal, action, detail, equity) "
                    "VALUES (:sym,:s,:sig,:a,:d,:e)"),
                    {"sym": sym, "s": strategy, "sig": None, "a": "ERROR",
                     "d": f"portfolio w={weight:.4f} — signal error: {e}",
                     "e": equity})
            continue

        # Reconcile position
        try:
            qty     = paper.position_qty(client, sym)
            pending = paper.pending_orders(client, sym)

            if pending > 0:
                action = "HOLD"
                detail = f"portfolio w={weight:.4f} — {pending} pending order(s), waiting for fill"
            elif signal == 1 and qty == 0:
                buy_notional = equity * deploy_pct / 100.0 * weight
                ok, reason = risk.pre_trade_check(client, sym, buy_notional)
                if not ok:
                    action = "BLOCKED"
                    detail = f"portfolio w={weight:.4f} — {reason}"
                else:
                    oid = paper.buy_notional(client, sym, buy_notional)
                    action = "BUY"
                    detail = f"portfolio w={weight:.4f} notional ${buy_notional:.0f} deploy_pct={deploy_pct}%, order {oid}"
            elif signal == 0 and qty > 0:
                oid = paper.close_position(client, sym)
                action = "SELL"
                detail = f"portfolio w={weight:.4f} — closed {qty} shares, order {oid}"
            else:
                action = "HOLD"
                detail = f"portfolio w={weight:.4f} — signal={signal}, position={qty}, already aligned"

        except Exception as e:
            action = "ERROR"
            detail = f"portfolio w={weight:.4f} — Alpaca error: {e}"

        with db.begin() as conn:
            conn.execute(text(
                "INSERT INTO paper_actions (symbol, strategy, signal, action, detail, equity) "
                "VALUES (:sym,:s,:sig,:a,:d,:e)"),
                {"sym": sym, "s": strategy, "sig": signal, "a": action,
                 "d": detail, "e": equity})

        actions.append({
            "symbol": sym, "strategy": strategy, "weight": weight,
            "signal_today": signal, "action": action, "detail": detail,
        })

    return {
        "blocked": False,
        "deploy_pct": deploy_pct,
        "account_equity": equity,
        "weights_used": weights_used,
        "actions": actions,
    }


# ---- live risk layer ----

@app.get("/risk/status")
def risk_status():
    """Kill switch state, current limits, and live readings from Alpaca.
    Degrades gracefully if Alpaca is unreachable."""
    import risk
    import paper
    killed = risk.is_killed()
    limits = {
        "max_daily_loss_pct": risk.RISK_MAX_DAILY_LOSS_PCT,
        "max_open_positions": risk.RISK_MAX_OPEN_POSITIONS,
        "max_symbol_exposure_pct": risk.RISK_MAX_SYMBOL_EXPOSURE_PCT,
    }
    try:
        client = paper.get_client()
        readings = risk.live_readings(client)
    except Exception as e:
        readings = {"available": False, "error": str(e)}
    return {"kill_switch": killed, "limits": limits, "readings": readings}


@app.post("/risk/kill")
def risk_kill(note: str = ""):
    """Engage the kill switch — all paper execution halts until /risk/resume."""
    import risk
    risk.set_kill(True)
    with db.begin() as conn:
        conn.execute(text(
            "INSERT INTO paper_actions (symbol, strategy, signal, action, detail, equity) "
            "VALUES (:sym,:s,:sig,:a,:d,:e)"),
            {"sym": None, "s": None, "sig": None, "a": "KILL",
             "d": note or "kill switch engaged", "e": None})
    return {"kill_switch": True, "note": note}


@app.post("/risk/resume")
def risk_resume(note: str = ""):
    """Disengage the kill switch — paper execution resumes normal risk checks."""
    import risk
    risk.set_kill(False)
    with db.begin() as conn:
        conn.execute(text(
            "INSERT INTO paper_actions (symbol, strategy, signal, action, detail, equity) "
            "VALUES (:sym,:s,:sig,:a,:d,:e)"),
            {"sym": None, "s": None, "sig": None, "a": "RESUME",
             "d": note or "kill switch disengaged", "e": None})
    return {"kill_switch": False, "note": note}


@app.get("/risk/reconcile")
def risk_reconcile():
    """Compare actual Alpaca paper positions against the champions table.

    Returns:
      - orphan_positions: symbols held in Alpaca with no champion
      - book_mismatches: champions whose recomputed signal disagrees with the held position
    """
    import paper
    try:
        client = paper.get_client()
        positions = client.get_all_positions()
    except Exception as e:
        raise HTTPException(502, f"Alpaca paper API: {e}")

    # load all champions
    champs_df = pd.read_sql(text(
        "SELECT c.symbol, c.run_id, r.strategy, r.params "
        "FROM champions c JOIN runs r ON r.run_id = c.run_id"),
        db)
    champion_symbols = set(champs_df["symbol"].tolist())

    # build a {symbol: qty} map from actual Alpaca positions, normalised to the
    # champion/yfinance form. Alpaca crypto positions may key on 'BTC/USD' OR
    # 'BTCUSD' (see paper.position_qty) — try both before declaring an orphan.
    held = {}
    for pos in positions:
        raw = str(pos.symbol).upper()
        candidates = {raw, raw.replace("/", "-")}
        if raw.endswith("USD") and len(raw) > 3 and "/" not in raw and "-" not in raw:
            candidates.add(raw[:-3] + "-USD")  # 'BTCUSD' -> 'BTC-USD'
        sym = next((c for c in candidates if c in champion_symbols),
                   raw.replace("/", "-"))
        held[sym] = float(pos.qty)

    # orphan positions: in Alpaca but no champion
    orphans = [
        {"symbol": sym, "qty": qty}
        for sym, qty in held.items()
        if sym not in champion_symbols
    ]

    # book mismatches: champion signal disagrees with held position
    mismatches = []
    for _, row in champs_df.iterrows():
        sym = row["symbol"]
        strategy = row["strategy"]
        if strategy not in REGISTRY:
            continue  # imported/video strategy — can't recompute signal here
        params = row.get("params") or {}
        if isinstance(params, str):
            params = json.loads(params)
        try:
            df = engine.fetch(sym, "2022-01-01")
            signal = int(REGISTRY[strategy]["fn"](df, {**params, "_symbol": sym}).iloc[-1])
        except Exception as e:
            mismatches.append({"symbol": sym, "strategy": strategy,
                               "error": f"signal recompute failed: {e}"})
            continue
        qty = held.get(sym, 0.0)
        holding = qty > 0
        expected_holding = signal == 1
        if holding != expected_holding:
            mismatches.append({
                "symbol": sym,
                "strategy": strategy,
                "signal_today": signal,
                "qty_held": qty,
                "verdict": "BOOK_MISMATCH",
                "detail": (
                    f"signal={signal} but {'holding' if holding else 'not holding'} {qty} shares"
                ),
            })

    return {
        "orphan_positions": orphans,
        "book_mismatches": mismatches,
        "held_symbols": list(held.keys()),
        "champion_symbols": list(champion_symbols),
    }


@app.get("/champion/{symbol}")
def get_champion(symbol: str):
    df = pd.read_sql(text(
        "SELECT c.promoted, c.note, r.* FROM champions c JOIN runs r ON r.run_id = c.run_id "
        "WHERE c.symbol=:s"), db, params={"s": symbol})
    if len(df) == 0:
        raise HTTPException(404, f"no champion for {symbol}")
    return json.loads(df.to_json(orient="records", date_format="iso"))[0]


@app.get("/monitor/{symbol}")
def monitor_symbol(symbol: str, window_days: int = 63):
    """Is this symbol's champion still behaving like its backtest? Compares a
    recent trailing window to the strategy's baseline and flags decay."""
    import monitor
    champ = get_champion(symbol)
    params = champ.get("params") or {}
    if isinstance(params, str):
        params = json.loads(params)
    return monitor.monitor(champ["strategy"], symbol, params, window_days)


# ---- nightly pipeline: sweep -> promote -> summary (n8n schedules this) ----

class NotifyRequest(BaseModel):
    text: str


@app.post("/notify")
def notify(req: NotifyRequest):
    """Send a text via the Gmail SMTP -> carrier-gateway path (email-sender lab).
    Env: GMAIL_ADDRESS, GMAIL_APP_PASSWORD, DEFAULT_RECIPIENT."""
    import smtplib
    from email.message import EmailMessage

    gmail = os.getenv("GMAIL_ADDRESS")
    app_pw = os.getenv("GMAIL_APP_PASSWORD")
    to = os.getenv("DEFAULT_RECIPIENT")
    if not (gmail and app_pw and to):
        raise HTTPException(400, "set GMAIL_ADDRESS/GMAIL_APP_PASSWORD/DEFAULT_RECIPIENT in .env")
    msg = EmailMessage()
    msg["From"], msg["To"] = gmail, to
    msg.set_content(req.text[:300])  # SMS-friendly
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(gmail, app_pw)
        s.send_message(msg)
    return {"sent_to": to, "chars": len(req.text[:300])}


@app.post("/nightly/{symbol}")
def nightly(symbol: str, start: str = "2020-01-01", metric: str = "sharpe"):
    """One call n8n can schedule: backtest every built-in strategy (skipping
    slow EDGAR ones), auto-promote, return an SMS-ready summary."""
    results = []
    for name in REGISTRY:
        if name in SLOW_STRATEGIES:
            continue  # EDGAR scans too slow/rate-limited for a sweep
        try:
            r = backtest(BacktestRequest(strategy=name, symbol=symbol, start=start))
            results.append({"strategy": name, "run_id": r["run_id"],
                            "sharpe": r["sharpe"], "return_pct": r["total_return_pct"]})
        except HTTPException as e:
            results.append({"strategy": name, "error": str(e.detail)})

    promo = auto_promote(symbol, metric=metric)
    champ = get_champion(symbol)
    summary = (f"[studio] {symbol} nightly: {promo['result']}. "
               f"Champion: {champ['strategy']} sharpe={champ['sharpe']} "
               f"ret={champ['total_return_pct']}% dd={champ['max_drawdown_pct']}% "
               f"(SPY {champ['spy_return_pct']}%)")
    return {"symbol": symbol, "swept": results, "promotion": promo, "summary": summary}


# ---- video queue: paste a reel/TikTok/YouTube URL in the UI; a HOST-side
# worker (.labs/audio-extraction/studio_worker.py) claims it, runs the video
# pipeline, and reports back. Finished strategies appear as video:<cache_key>
# via the read-only /app/imported mount. ----

class VideoRequest(BaseModel):
    url: str


class VideoComplete(BaseModel):
    status: str            # done | error
    cache_key: str = ""
    note: str = ""


@app.post("/videos")
def video_queue_add(req: VideoRequest):
    url = req.url.strip()
    if not url.lower().startswith(("http://", "https://")) or len(url) > 2000:
        raise HTTPException(400, "url must start with http(s):// and be under 2000 chars")
    dup = pd.read_sql(text(
        "SELECT id FROM video_queue WHERE url=:u AND status IN ('pending','processing')"),
        db, params={"u": url})
    if len(dup) > 0:
        raise HTTPException(409, f"already queued (id {dup.iloc[0]['id']})")
    vid = uuid.uuid4().hex[:12]
    with db.begin() as conn:
        conn.execute(text("INSERT INTO video_queue (id, url) VALUES (:i,:u)"),
                     {"i": vid, "u": url})
    return {"id": vid, "url": url, "status": "pending"}


@app.get("/videos")
def video_queue_list(limit: int = 50):
    df = pd.read_sql(text("SELECT * FROM video_queue ORDER BY created DESC LIMIT :n"),
                     db, params={"n": limit})
    return json.loads(df.to_json(orient="records", date_format="iso"))


@app.post("/videos/claim")
def video_queue_claim():
    """Atomically claim the oldest pending URL (SKIP LOCKED: two pollers can't
    grab the same row). The host worker polls this."""
    with db.begin() as conn:
        row = conn.execute(text(
            "UPDATE video_queue SET status='processing', updated=now() "
            "WHERE id = (SELECT id FROM video_queue WHERE status='pending' "
            "ORDER BY created LIMIT 1 FOR UPDATE SKIP LOCKED) RETURNING id, url")).fetchone()
    if row is None:
        return {"empty": True}
    return {"id": row[0], "url": row[1]}


@app.post("/videos/{video_id}/complete")
def video_queue_complete(video_id: str, req: VideoComplete):
    if req.status not in ("done", "error"):
        raise HTTPException(400, "status must be done|error")
    with db.begin() as conn:
        r = conn.execute(text(
            "UPDATE video_queue SET status=:s, cache_key=:c, note=:n, updated=now() "
            "WHERE id=:i"),
            {"s": req.status, "c": req.cache_key, "n": req.note[:500], "i": video_id})
    if r.rowcount == 0:
        raise HTTPException(404, "unknown video id")
    return {"id": video_id, "status": req.status, "cache_key": req.cache_key}
