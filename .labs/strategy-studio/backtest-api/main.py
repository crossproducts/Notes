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
from pydantic import BaseModel
from sqlalchemy import create_engine, text

import analysis
import engine
from strategies import REGISTRY

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://studio:studio@localhost:5433/backtests")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
IMPORTED_DIR = Path(os.getenv("IMPORTED_DIR", "/app/imported"))

db = create_engine(DATABASE_URL)
app = FastAPI(title="Strategy Studio Backtest API")

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
"""


@app.on_event("startup")
def init_db():
    with db.begin() as conn:
        for stmt in DDL.strip().split(";"):
            if stmt.strip():
                conn.execute(text(stmt))
    import scheduler
    scheduler.start()


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
        cost_bps=req.cost_bps)

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


# ---- champion / challenger registry (MLflow-style, per symbol) ----

@app.get("/leaderboard")
def leaderboard(symbol: str = "SPY", metric: str = "sharpe", limit: int = 10):
    """Challengers ranked by a metric; the reigning champion is flagged.
    Rank on risk-adjusted metrics (sharpe) — raw return rewards luck."""
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


@app.post("/champion/auto/{symbol}")
def auto_promote(symbol: str, metric: str = "sharpe", min_trades: int = 5,
                 validate: bool = True):
    """Auto-promote the best run for a symbol IF it beats the current champion
    on the metric. With validate=True (default), a NEW champion must also pass
    a walk-forward gate: positive stitched out-of-sample return. Promoting on
    in-sample metrics alone is institutionalized overfitting."""
    best = pd.read_sql(text(   # all metrics higher-is-better (dd is negative)
        f"SELECT * FROM runs WHERE symbol=:s AND trades >= :t "
        f"ORDER BY {metric} DESC NULLS LAST LIMIT 1"),
        db, params={"s": symbol, "t": min_trades})
    if len(best) == 0:
        raise HTTPException(404, f"no runs for {symbol} with >= {min_trades} trades")
    challenger = best.iloc[0]

    cur = pd.read_sql(text(
        "SELECT r.* FROM champions c JOIN runs r ON r.run_id = c.run_id WHERE c.symbol=:s"),
        db, params={"s": symbol})
    if len(cur) > 0:
        champ = cur.iloc[0]
        better = challenger[metric] > champ[metric]  # higher-is-better (dd negative)
        if not better or challenger["run_id"] == champ["run_id"]:
            return {"symbol": symbol, "result": "champion defended",
                    "champion": champ["run_id"], f"champion_{metric}": float(champ[metric]),
                    "best_challenger": challenger["run_id"],
                    f"challenger_{metric}": float(challenger[metric])}

    # OOS gate: a would-be champion must survive walk-forward before wearing the belt
    if validate and challenger["strategy"] in REGISTRY:
        try:
            wf = analysis.walkforward(challenger["strategy"], symbol, "2018-01-01")
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

    try:
        client = paper.get_client()
        acct = paper.account_summary(client)
        qty = paper.position_qty(client, symbol)
        pending = paper.pending_orders(client, symbol)

        if pending > 0:
            action, detail = "HOLD", f"{pending} pending order(s) — waiting for fill, no action"
        elif signal == 1 and qty == 0:
            oid = paper.buy_notional(client, symbol, acct["equity"] * position_pct / 100)
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
            "paper": True}


@app.get("/paper/log")
def paper_log(limit: int = 30):
    df = pd.read_sql(text("SELECT * FROM paper_actions ORDER BY ts DESC LIMIT :n"),
                     db, params={"n": limit})
    return json.loads(df.to_json(orient="records", date_format="iso"))


@app.get("/champion/{symbol}")
def get_champion(symbol: str):
    df = pd.read_sql(text(
        "SELECT c.promoted, c.note, r.* FROM champions c JOIN runs r ON r.run_id = c.run_id "
        "WHERE c.symbol=:s"), db, params={"s": symbol})
    if len(df) == 0:
        raise HTTPException(404, f"no champion for {symbol}")
    return json.loads(df.to_json(orient="records", date_format="iso"))[0]


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
        if name == "insider_form4":
            continue  # EDGAR scan too slow/rate-limited for a sweep
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
