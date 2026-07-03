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
"""


@app.on_event("startup")
def init_db():
    with db.begin() as conn:
        for stmt in DDL.strip().split(";"):
            if stmt.strip():
                conn.execute(text(stmt))


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


def _persist(run_id, req, m, bench, equity, halted=False):
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
        rows = [{"r": run_id, "ts": ts.to_pydatetime(), "e": float(v)} for ts, v in equity.items()]
        conn.execute(text("INSERT INTO equity_curve (run_id, ts, equity) VALUES (:r,:ts,:e)"), rows)


@app.post("/backtest")
def backtest(req: BacktestRequest):
    run_id = uuid.uuid4().hex[:12]

    imported = imported_strategies()
    if req.strategy in imported:
        equity, m = run_imported(imported[req.strategy], req.params)
        bench = engine.benchmarks("SPY", equity.index, str(equity.index[0].date()))
        _persist(run_id, req, m, bench, equity)
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
        max_dd_stop_pct=req.risk.max_dd_stop_pct)

    m = engine.metrics(equity, signal, df["Close"])
    bench = engine.benchmarks(req.symbol, df.index, req.start)
    _persist(run_id, req, m, bench, equity, halted)
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
    curve = pd.read_sql(text("SELECT ts, equity FROM equity_curve WHERE run_id=:r ORDER BY ts"),
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
