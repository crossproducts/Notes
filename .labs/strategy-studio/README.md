# Strategy Studio

Drag-and-drop trading-strategy pipeline: compose strategies visually in **n8n**,
backtest them against historical data, and explore results in **Grafana**
dashboards. Graduates the video→backtest pipeline (`.labs/audio-extraction`)
into an interactive platform.

## Architecture

```
                 ┌────────────────────────────────────────────┐
                 │              n8n  (drag & drop)             │
                 │  strategy nodes → pipeline → schedule/run   │
                 └──────┬─────────────────────────┬────────────┘
                        │ HTTP                    │ chart image (QuickChart)
                        ▼                         ▼
            ┌───────────────────┐        report / SMS / email
            │  backtest-api     │        (via .labs/email-sender)
            │  (Python+FastAPI) │
            │  vectorbt engine  │
            └───┬───────────┬───┘
                │           │ writes results
     data      ▼           ▼
  ┌─────────────────┐   ┌──────────┐        ┌─────────────┐
  │ connectors      │   │ Postgres │ ◄───── │   Grafana   │
  │ alpaca (stocks/ │   │ (trades, │  reads │ dashboards: │
  │  options/crypto)│   │  equity  │        │ equity curve│
  │ oanda (forex)   │   │  curves, │        │ drawdown    │
  │ edgar (13F)     │   │  runs)   │        │ heatmaps    │
  │ quiver (congress│   └──────────┘        └─────────────┘
  └─────────────────┘
```

### Division of labor (research-backed)
- **n8n** — orchestration + drag-and-drop composition. It does NOT do interactive
  dashboards; it can render static chart images via its QuickChart node (fine for
  pushing a result PNG to SMS/email/Telegram, not for exploration).
- **Grafana** — the real visualization layer. Reads backtest results from
  Postgres; interactive equity curves, drawdown, parameter heatmaps, run compare.
- **backtest-api** — a small FastAPI service wrapping a proper engine
  (**vectorbt**) so n8n nodes just POST `{strategy, params, symbol, range}` and
  get a `run_id` back. Keeps the heavy lifting out of n8n.

### How "drag & drop strategies" maps to n8n
Each strategy = an **n8n sub-workflow** with a standard interface
(in: symbol/timeframe/params → out: run_id/metrics). Composing a pipeline =
dragging strategy nodes into a canvas, wiring them to data-source nodes and a
"compare results" node. n8n handles scheduling (nightly re-runs), branching,
and notifications.

## Data connectors

| Source | Assets | Notes |
|--------|--------|-------|
| **Alpaca** | US stocks, ETFs, options, crypto | Already have keys (audio-extraction lab). **No forex** — confirmed. |
| **OANDA** | Forex | The standard developer-friendly forex API; free practice account. |
| **SEC EDGAR** | 13F filings (whales) | **Free.** Quarterly institutional holdings → whale-copy strategies. |
| **Quiver Quantitative** | Congress trades | Real API (paid tier). Free alternative: scrape House/Senate disclosure sites. |
| **yfinance** | Daily equities fallback | Free, already used by generated backtests. |

## Strategy catalog (initial)

1. **Congress copycat** — follow reported House/Senate trades (data lags 30–45
   days by law; the backtest must model that lag honestly).
2. **Whale 13F copycat** — replicate top holdings/changes of chosen funds
   (Berkshire, Renaissance…). Quarterly rebalance; also lagged (45 days).
3. **Imported from videos** — every strategy already extracted by
   `.labs/audio-extraction` (multi-factor, rotation, ORB…) wrapped as nodes.
4. **Classic technicals** — momentum, mean-reversion, breakout; the baseline set.
5. **Forex carry/trend** — via OANDA, to exercise the second connector.

## Roadmap

- **Phase 1 — core loop.** docker-compose up (n8n + Postgres + Grafana +
  backtest-api). One strategy (momentum) runs end-to-end: n8n node → API →
  results in Postgres → Grafana equity curve.
- **Phase 2 — strategy catalog.** Wrap audio-extraction strategies + classic
  technicals as sub-workflows; parameter grids; run-compare dashboard.
- **Phase 3 — alt-data.** EDGAR 13F ingest (free) → whale copycat; congress
  feed (Quiver or scraper) → congress copycat. Model the disclosure lag.
- **Phase 4 — validation & alerts.** Walk-forward analysis (anti-overfitting),
  benchmark vs buy-and-hold, and n8n pushes result summaries through
  `.labs/email-sender` → **SMS to your phone** when a nightly run finishes.
- **Phase 5 — MCP server.** Expose `run_backtest`, `list_strategies`,
  `get_results` as MCP tools so Claude can drive the studio conversationally.
- **Phase 6 — paper trading.** Graduate a validated strategy to Alpaca paper
  API; n8n schedules live signal generation. (This is when Alpaca's own UI
  finally becomes useful — real orders.)

## Implemented features (beyond the initial ask)

| Feature | Where | Status |
|---------|-------|--------|
| Walk-forward validation | `POST /walkforward` — rolling train/optimize → unseen test, stitched OOS return + stability verdict | ✅ |
| Risk engine | `risk` block on `/backtest`: `position_size_pct`, `max_dd_stop_pct` circuit breaker (halts trading past the drawdown limit) | ✅ |
| Regime filter | `regime_filter: true` — only trade when SPY > 200-day MA | ✅ |
| Monte Carlo | `GET /montecarlo/{run_id}` — bootstrap the run's returns; p5/p50/p95 outcome + drawdown distribution | ✅ |
| Benchmark node | every run auto-compared to same-symbol buy-and-hold AND SPY, stored + on the Grafana table | ✅ |
| Insider-buying strategy | `insider_form4` — SEC Form 4 open-market purchases via free EDGAR API (first run per ticker is slow, then cached) | ✅ |
| Video-pipeline import | audio-extraction strategies auto-discovered as `video:<key>` nodes (mounted read-only) | ✅ |
| Local-LLM analyst | `GET /analyze/{run_id}` — host Ollama (qwen2.5:3b) writes a plain-English summary; caveat: 3B models garble details, treat as a draft | ✅ |
| Champion/challenger registry | MLflow-style: `GET /leaderboard`, `POST /champion/auto/{symbol}` (promotes only if the challenger beats the champion on the metric — default sharpe), `GET /champion/{symbol}` | ✅ |
| GitOps-ish workflows | `workflows/` versioned in the repo; `sh workflows-sync.sh import\|export\|diff` syncs with n8n (convention, not reconciliation — n8n has no reconciler) | ✅ |
| Nightly champion pipeline | in-API scheduler (weekdays 18:00 ET): sweeps built-ins per `STUDIO_SYMBOLS` → auto-promotes (**OOS-gated**) → **texts you the result**; failures SMS `[ERROR]` instead of dying silently; optional `HEALTHCHECK_URL` dead-man ping | ✅ |
| Transaction costs | `cost_bps` on every backtest (default 5bps/side spread+slippage proxy); walk-forward inherits it — frictionless is opt-in, not the default | ✅ |
| Champions Grafana panel | current title-holder per symbol on the provisioned dashboard | ✅ |
| CI → ECR | `.github/workflows/backtest-api-ecr.yml` (manual dispatch until AWS is stood up; OIDC, no long-lived keys) | ✅ |
| Paper trading (Phase 6) | `/paper/account`, `/paper/positions`, `/paper/execute/{symbol}` (reconciles the **champion's live signal** into the Alpaca paper account; `paper=True` hardcoded), `/paper/log` audit trail; pending-order guard prevents duplicate entries; n8n `Paper Trade — QQQ champion daily` cron (9:35 market days) + SMS | ✅ |
| Video queue in the UI | paste a reel/TikTok/YouTube URL at `/ui` → Postgres queue → host-side `.labs/audio-extraction/studio_worker.py` runs the pipeline → strategy appears as `video:<cache_key>` | ✅ |
| Diversifying strategies | `rotation_top_k` (cross-sectional dual momentum over an ETF universe) + `whale_13f` (13F copycat, default Berkshire; signals on FILING dates so the 45-day lag is honest) | ✅ |
| Sentiment strategy | needs a sentiment data feed — still roadmap | ⬜ |

Grafana is auto-provisioned: Postgres datasource + a "Strategy Studio" dashboard
(equity curve per run via `$run` dropdown, and a runs table with benchmark columns).

## Next features (planned)

Ordered by value-per-effort:

1. **Nightly champion pipeline (n8n)** — scheduled workflow: sweep strategies →
   `/champion/auto` per symbol → QuickChart equity PNG → **SMS the result via
   `.labs/email-sender`**. Ties three labs together; pure wiring, no new code.
2. **Champions panel in Grafana** — add the `champions` table + "champion vs
   challengers" comparison panel to the provisioned dashboard.
3. **CI image build** — GitHub Actions: build/push `backtest-api` to ECR on
   change; ArgoCD picks it up (closes the GitOps loop for code, not just config).
4. **Congress copycat for real** — Quiver API key (or disclosure scraper) →
   congress connector; the backtest MUST model the 30–45-day disclosure lag.
5. **OANDA forex connector** — second broker, first non-equity asset class;
   validates the connector abstraction.
6. **MCP server (Phase 5)** — expose `run_backtest` / `leaderboard` /
   `promote_champion` as MCP tools; drive the studio from Claude.
7. **vectorbt engine upgrade** — swap the hand-rolled loop for vectorbt;
   unlocks intraday backtests on the Alpaca 5-min data you already cache.
8. **Portfolio mode** — allocate across N champions, correlation matrix panel,
   portfolio-level risk engine (the real quant step).
9. **Sentiment connector** — the remaining unimplemented strategy idea.
10. **Paper trading (Phase 6)** — graduate a walk-forward-surviving champion to
    Alpaca paper; n8n schedules live signals.

## AWS deployment

`infra/` (Terragrunt: VPC/EKS/ECR/RDS, tear-down discipline) + `k8s/` (ArgoCD
app-of-apps). See `infra/README.md`. Local compose remains the daily driver.

## Decisions still open

- Quiver API (paid, clean) vs scraping disclosures (free, brittle) for congress data
- Postgres (Grafana-native, relational) vs InfluxDB/Timescale for results store
- n8n licence note: self-hosted n8n is source-available (fair-code), free for
  personal use — fine for a lab
- Whether Phase 6 auto-trades paper or only generates signals

## Quick start (Phase 1 scaffold)

```bash
cd .labs/strategy-studio
cp .env.example .env      # add keys
docker compose up -d
# operator dashboard → http://localhost:8001/ui   (Strategy Studio single-page app)
# swagger/api docs   → http://localhost:8001/docs  (all endpoints)
# grafana            → http://localhost:3001  (admin / admin on first login)

# n8n was removed (2026-07): its only real duties — two cron schedules + SMS
# chaining — moved into the API (backtest-api/scheduler.py). One less container,
# no UI credentials, errors alert instead of failing silently. Paper trades run
# weekdays 9:35, champion sweep 18:00 ET, automatically.
```
