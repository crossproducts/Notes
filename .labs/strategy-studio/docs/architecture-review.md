# Strategy Studio vs. Wall Street Quant Architecture

An honest gap analysis (2026-07), plus the plan for running autonomously 24/7.

## Layer-by-layer comparison

| Layer | Wall Street quant shop | Strategy Studio | Verdict |
|---|---|---|---|
| **Data** | Tick stores (kdb+/Arctic), data lakehouse, point-in-time correctness, survivorship-bias-free vendors (CRSP), corporate-action handling, data QA pipelines | yfinance/Alpaca fetched ad-hoc, parquet cache, no PIT discipline | Biggest quality gap |
| **Research / backtest** | Event-driven engines with **cost models**, purged/combinatorial CV, factor libraries, capacity analysis | Vectorized engine; walk-forward ✅, Monte Carlo ✅, **zero transaction costs** ❌ | Right shape, missing costs |
| **Strategy registry** | Model registry with deployment gates (OOS performance, capacity, risk sign-off) | Champion/challenger ✅ — but promotion gates on **in-sample sharpe** | Pattern right, gate wrong |
| **Execution** | OMS/EMS split, execution algos (VWAP/TWAP), smart routing, FIX, reconciliation | Market notional orders at 9:35, pending-order guard, audit log | Fine for paper scale |
| **Risk** | Independent real-time risk layer: pre-trade checks, exposure limits, kill switch — **separate from strategy code** | Backtest-time DD breaker; 10% notional cap | No *live* risk layer |
| **Monitoring / ops** | 24/7 ops, telemetry, reconciliation jobs, dead-man switches | SMS on success; **failures are silent** | The always-on blocker |
| **MLOps** | Feature stores to kill training-serving skew (the #1 reason models fail live despite strong backtests) | Backtest computes signal on close; live executes 9:35 next day = uncontrolled skew | Same disease, small scale |
| **Governance** | Audit, secrets management, change control | GitOps'd config ✅, sealed-secrets discipline ✅, audit table ✅, CI scaffold ✅ | Genuinely decent |

The encouraging part: the studio has a *miniature of almost every layer* — the skeleton
is architecturally correct. The gaps are about honesty (costs, bias) and robustness
(risk, monitoring), not shape.

## Prioritized improvements

1. **Transaction costs + slippage in the engine.** Every backtest currently assumes
   free, frictionless fills. Even 1bp+spread assumptions change high-turnover
   results dramatically. Until then, all strategy comparisons are inflated.
   (Add `cost_bps` to the engine; default it ON.)
2. **Survivorship bias.** The multi-factor video strategy picks from 20 *currently*
   large-cap names — stocks chosen because they already won. A 2020 backtest on that
   universe is structurally flattering. Real fix: point-in-time universes; cheap fix:
   flag it on every multi-symbol result.
3. **Champion promotion gate = walk-forward OOS, cost-adjusted.** Promoting on
   in-sample sharpe is exactly the overfitting the walk-forward endpoint exists to
   catch. Wire `/champion/auto` to require a walk-forward pass.
4. **Live risk layer, separate from strategies.** Max daily loss, max open positions,
   max per-symbol exposure, and a `/risk/kill` switch that halts all paper execution.
   Pre-trade check in `/paper/execute`, not inside strategy code.
5. **Failure alerting (dead-man switch).** SMS fires on success but crashes are
   silent — fatal for autonomous operation. n8n error workflow → `/notify`, plus an
   external heartbeat (healthchecks.io pings) so "the whole box died" also alerts.
6. **Signal-timing skew.** Backtests fill at next bar after a close signal; live
   trades at 9:35. Either backtest with open-to-open fills or execute near close —
   pick one and align.
7. Later: event-driven engine (vectorbt / nautilus_trader), reconciliation job
   (expected book vs Alpaca positions), portfolio-level allocation across champions.

## Running 24/7 without touching it

Three options, honest costs:

| Option | Cost | Fit |
|---|---|---|
| **A. This PC, always on** | $0 | Docker restart policies (added) + Docker Desktop autostart + disable sleep + activate n8n workflows. Fragile: reboots, laptop lifestyle, OneDrive-synced repo path. |
| **B. Small cloud VM (recommended)** | ~$12–25/mo | Lightsail 4GB or EC2 `t4g.medium`. Same `docker compose up -d` — the stack is already portable. Access via **Tailscale** (free) instead of exposing n8n/Grafana publicly. |
| **C. EKS (the infra/ lab)** | ~$150+/mo | Wrong tool for always-on hobby scale — it's a *learning* environment with teardown discipline. Reuse its ECR + CI when convenient. |
| (Serverless) | — | EventBridge→Lambda suits a single stateless function; this is a 4-service stateful stack — a VM is simpler and cheaper. |

**Recommended path (B):**
1. Provision Lightsail 4GB / t4g.medium (~$24/mo), Docker + compose plugin
2. `git clone` the repo, copy `.env` over, `docker compose up -d`
3. `restart: unless-stopped` (now in compose) survives reboots; enable unattended-upgrades
4. Tailscale on the VM + your phone/PC → n8n/Grafana reachable privately, nothing public
5. Activate the two n8n schedules (nightly champion 18:00, paper trade 9:35)
6. Reliability net: n8n Error Trigger workflow → `/notify`; healthchecks.io heartbeat
   ping added to the nightly workflow (missed ping = email/SMS even if everything died)
7. Skip the local-LLM analyst on the VM (qwen needs ~3GB) — leave `OLLAMA_URL`
   unset/unreachable; only `/analyze` degrades. Or point it at Claude Haiku later.

Note: paper trades only "throughout the day" as far as the strategy warrants — the
current champion is a *daily* momentum signal (one reconcile per morning). Intraday
cadence means intraday strategies + intraday data (Alpaca 5-min feed) first.

## Sources

- [Algorithmic trading architecture deep dive (BlackRock/Tower case studies)](https://dev.to/nashetking/algorithmic-trading-architecture-and-quants-a-deep-dive-with-case-studies-on-blackrock-and-tower-research-55ao)
- [Quant 2.0: lakehouses, feature stores, MLOps](https://altstreet.investments/blog/quant-2-architecture-modern-trading-stack-ai-mlops)
- [Automated trading systems: design & architecture (QuantInsti)](https://www.quantinsti.com/articles/automated-trading-system/)
- [Algorithmic trading on AWS (SageMaker/Data Exchange)](https://aws.amazon.com/blogs/industries/algorithmic-trading-on-aws-with-amazon-sagemaker-and-aws-data-exchange/)
- [Lambda vs EC2 cost breakeven (Trek10)](https://www.trek10.com/blog/lambda-cost)
- [Alpaca: Python + AWS trading algorithm](https://alpaca.markets/learn/python-aws-trading-algorithm)
