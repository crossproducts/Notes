# Deep-Research Prompt: Strategy Studio → Production

> Paste this into a deep-research tool (or hand it to a research agent). The
> deliverable it must produce is described at the bottom.

---

## Context (what exists today)

I run a self-hosted algorithmic trading lab with two connected projects:

1. **Strategy Studio** (`.labs/strategy-studio`) — a FastAPI "backtest-api"
   (hand-rolled vectorized engine) + Postgres + Grafana, run via docker-compose.
   It already has: transaction costs (5 bps/side default), walk-forward
   validation, Monte Carlo, regime filter, a champion/challenger registry with
   an out-of-sample promotion gate, an in-process scheduler (nightly strategy
   sweep 18:00 ET, paper-trade reconcile 9:35 ET on market days), SMS alerts
   via Gmail→carrier gateway, and **Alpaca paper trading** endpoints
   (`/paper/execute/{symbol}` reconciles the champion's daily signal into the
   paper account; `paper=True` hardcoded). Grafana shows equity curves and a
   runs table. There is no product UI — only Grafana and `/docs` (Swagger).

2. **Video → strategy pipeline** (`.labs/audio-extraction`) — downloads trading
   reels (yt-dlp/Playwright), Whisper-transcribes, Claude interprets the
   transcript into a strategy config, generates backtest code, backtests on
   Alpaca data. Currently **audio-only**: charts, tickers, and numbers shown
   on-screen in the video are lost.

An honest self-assessment (docs/architecture-review.md) already flags: no live
risk layer separate from strategy code, signal-timing skew (backtest fills at
close, live executes 9:35 next day), survivorship bias in multi-symbol
universes, and silent-failure risk for autonomous operation.

Operator profile: solo developer, Windows + Docker Desktop, hobby-scale budget
(< $50/mo infra), Alpaca paper account, comfortable with Python/FastAPI/K8s.
Goal is **real money eventually, with paper trading as the proving ground** —
not a SaaS, a personal production system.

## Research questions

Answer each with current (2026) information, citing sources. Prefer primary
sources (broker docs, regulator sites, library repos) over blog spam.

### A. UI for a personal trading product
1. For a solo-operator trading dashboard, what is the best-value UI approach in
   2026: (a) static SPA served by FastAPI (htmx/Alpine/vanilla + a chart lib),
   (b) Streamlit/Gradio/NiceGUI-style Python UI, (c) Next.js/React app, or
   (d) lean harder on Grafana? Weigh build time, maintenance, and real-time
   needs (websockets vs polling for a daily-signal system).
2. Which charting library best renders equity curves, drawdown, and candlestick
   + trade-marker overlays with minimal build tooling (TradingView
   lightweight-charts vs Plotly vs ECharts vs uPlot)? License caveats?
3. What screens do professional strategy platforms (QuantConnect, Composer,
   TradingView strategy tester) consider table-stakes, and which subset matters
   for one operator?

### B. Paper trading → live readiness
4. What is a credible promotion checklist from paper to live money used by
   practitioners (minimum paper duration, trade count, tracking error vs
   backtest, Sharpe/drawdown thresholds)? Is 3 months of paper standard?
5. Alpaca specifics in 2026: paper-vs-live API behavioral differences (fills,
   slippage modeling, data entitlements), live account minimums, PDT rule
   implications for a daily-signal account under $25k, and crypto trading
   terms. Any reasons to prefer a different broker (IBKR, Tradier) for going
   live at small size?
6. How should live execution timing be aligned with backtest assumptions
   (close-to-close vs open fills)? Concretely: is executing near close via
   MOC/limit-on-close better than 9:35 market orders for a daily signal, and
   what does Alpaca support?
7. What does a minimal but real live-risk layer look like for one account:
   max daily loss, max position count, per-symbol exposure caps, kill switch,
   reconciliation (expected book vs broker positions)? Any open-source
   reference implementations worth copying?

### C. Making the research loop smarter (video/multimodal)
8. State of the art for extracting trading strategies from video in 2026:
   frame sampling strategies (scene-change detection vs fixed interval) with
   ffmpeg, and feeding frames to Claude vision alongside the transcript. What
   frame rates / counts give good chart-reading without token blowup?
9. Are there known pipelines/papers on "finfluencer strategy mining" and what
   do they find about the quality of retail video strategies (base rates of
   backtest survival)? This calibrates expectations.

### D. Path to actually making money (honest edges for retail)
10. Where do practitioners agree small retail algos can still find edge in
    2026 (less crowded: overnight effects, small-cap momentum, crypto
    microstructure, congressional-disclosure lag, 13F drift)? Where is it a
    waste (HFT, large-cap intraday)?
11. Realistic expectations: for a $5–25k account trading daily signals with
    5 bps costs, what annualized return/Sharpe would a *good* outcome be, and
    what monthly burn (data, infra) must the edge clear?
12. Tax and structural considerations for a US individual algo trading
    (wash sales with automated daily strategies, mark-to-market 475(f)
    election — when does it matter)?

## Required deliverable

A **phased plan** (Phase 0/1/2/3) where each phase has: goal, concrete tasks,
acceptance criteria ("definition of done"), and an explicit go/no-go gate
before real money. Include a "do NOT build" list — features that look
productive but don't move the money-making needle for a solo operator. Keep
the total plan executable by one person in evenings over ~8 weeks.
