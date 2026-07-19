# Strategy Studio: Next-Level Plan
*Research-backed phased roadmap — solo operator, evenings, ~8 weeks*

Generated: 2026-07-18. Research agent: Claude Sonnet 4.6.

---

## Section A — UI for a Personal Trading Product

### Q1. Best-value UI approach in 2026 for a solo-operator daily-signal dashboard

**Recommendation: Stay on Grafana + add a thin FastAPI-served HTML page (htmx or vanilla JS) for operational controls.**

For a *daily-signal* system (one trade per day, no intraday streaming), Grafana already does the heavy lifting: equity curves, run comparison, leaderboard panels are all provisioned. The gap is *operational UI* — triggering a manual backtest, approving a champion promotion, pressing the kill switch — which Swagger (`/docs`) currently fills awkwardly.

The right addition is a minimal FastAPI-served HTML page (< 200 lines of Jinja2 + htmx for the interactive bits), not a full SPA framework. This adds zero new containers and zero build tooling.

Reject the alternatives for this use case:
- **Streamlit/NiceGUI**: fast to prototype but adds a second Python web process, session-state quirks, and you already have a FastAPI backend — wrapping it again is duplication.
- **Next.js/React**: massive build toolchain for a one-person ops dashboard; use only if you expect to hand the system to others or need real-time WebSocket data (you don't — daily signals).
- **Grafana alone**: cannot do operational controls (POST requests, forms, buttons that mutate state).

Sources: [Streamlit vs NiceGUI comparison](https://www.bitdoze.com/streamlit-vs-nicegui/), [Python Dashboard 2026 Guide](https://www.usedatabrain.com/how-to/create-python-dashboard), [Real-time Streamlit + WebSocket](https://medium.com/data-science-collective/building-a-real-time-forex-dashboard-with-streamlit-and-websocket-56a14a985f42)

---

### Q2. Best charting library for equity curves, drawdown, candlestick + trade markers

**Recommendation: TradingView Lightweight Charts v5.x**

- **License**: Apache 2.0 — free for commercial use; requires visible TradingView attribution link. No per-seat or revenue-share fee.
- **Size**: ~35 KB min, canvas-based, renders 10,000+ data points at 60 FPS.
- **Supported types**: candlestick, Heikin-Ashi, line, area, OHLC bars, volume histogram — all as first-class citizens. Markers/annotations are native. This is a purpose-built financial charting library, not a general-purpose chart lib ported to finance.
- **Drawback**: Apache 2.0 attribution requirement (add the TradingView link somewhere visible). Non-issue for a personal dashboard.

Alternatives considered:
- **uPlot** (MIT, ~50 KB): excellent for pure time-series (equity curves, drawdown). Supports OHLC. MIT license is cleaner than Apache 2.0. Use if you want zero attribution requirement and don't need candlestick-first ergonomics.
- **Plotly** (MIT/open-source): great Python-native integration with Grafana or Streamlit; heavier bundle; candlestick support exists but it's not the primary design target.
- **Apache ECharts** (Apache 2.0): broadest chart type coverage; Canvas rendering handles big data; good for heatmaps (param grids already in Grafana).

**Practical choice**: embed Lightweight Charts in the thin FastAPI HTML page for the live trade view + equity curve. Keep ECharts (or Grafana built-in) for parameter heatmaps. uPlot is a drop-in alternative if attribution is unwanted.

Sources: [Lightweight Charts homepage](https://www.tradingview.com/lightweight-charts/), [GitHub repo](https://github.com/tradingview/lightweight-charts), [uPlot GitHub](https://github.com/leeoniya/uplot), [JS chart library comparison 2026](https://lalatenduswain.medium.com/the-complete-guide-to-javascript-charting-libraries-in-2026-choosing-the-right-visualization-tool-dac9aeb15f60)

---

### Q3. Table-stakes screens for professional strategy platforms, and which subset matters for one operator

Professional platforms (QuantConnect, Composer, TradingView Strategy Tester) converge on these screens:

| Screen | QuantConnect | Composer | TV Strategy Tester | Need for this system? |
|---|---|---|---|---|
| Equity curve (cumulative returns) | ✅ | ✅ | ✅ | **YES — already in Grafana** |
| Drawdown chart | ✅ | ✅ | ✅ | **YES — already in Grafana** |
| Trade list (entry/exit/P&L) | ✅ | ✅ | ✅ | **YES — paper_log table exists** |
| Benchmark comparison | ✅ | ✅ | ✅ | **YES — already stored** |
| Parameter sensitivity / heatmap | ✅ | ❌ | ❌ | **YES — worth adding to Grafana** |
| Walk-forward OOS overlay | ✅ | ❌ | ❌ | **YES — /walkforward exists, visualize it** |
| Live position reconciliation | ✅ | ✅ | ❌ | **YES — the gap to fill** |
| Risk / kill switch panel | ✅ | ✅ | ❌ | **YES — the gap to fill** |
| Portfolio allocation view | ✅ | ✅ | ❌ | Later (Phase 3) |
| Strategy composition (drag-drop) | ❌ | ✅ | ❌ | No — n8n was removed deliberately |

For one operator: equity curve, drawdown, trade list, benchmark, walk-forward overlay, and a live positions/risk panel. The rest is nice-to-have.

Sources: [QuantConnect terminal](https://www.quantconnect.com/terminal/), [Backtesting Software Ranked 2026](https://www.luxalgo.com/blog/backtesting-software-ranked-for-retail-quants/), [Best Backtesting Platforms 2026](https://backtrex.com/en/blog/best-backtesting-platforms)

---

## Section B — Paper Trading → Live Readiness

### Q4. Credible promotion checklist from paper to live money

No single canonical standard exists, but practitioners converge on these gates:

**Minimum duration**: 3–6 months of paper trading across at least two distinct market regimes (e.g., trending + mean-reverting, low-vol + high-vol). Freqtrade's community checklist requires a minimum 7-day dry run *after* a 3-month backtest — but this is a crypto framework with much higher trade frequency. For a *daily signal* strategy, 3 months of paper = ~60 trading days = 60 signals, which is marginally sufficient.

**Minimum trade count**: 
- Statistical floor (CLT): ~30 trades
- Reliable metric estimation: ~100 trades  
- Institutional confidence: 200–500 trades across multiple regimes

A daily signal on one symbol generates ~21 trades/month. At that rate, 3 months = ~63 trades — borderline. Consider running the champion on 3–5 symbols in paper simultaneously to reach 100+ paper trades faster.

**Performance thresholds (practitioner consensus)**:
- Post-cost Sharpe ratio (paper period) > 1.0
- Maximum drawdown during paper period < 20%
- Paper return within ±50% of backtest return (not wildly better, which signals backtest overfit)
- Paper win rate within ±15 percentage points of backtest win rate
- Zero failed executions (order errors, missed fills, duplicate orders)

**Tracking error vs backtest**: The most important signal is *divergence*. If paper is consistently beating the backtest by a wide margin, the backtest is overfit. If paper is dramatically underperforming, there is a signal-timing or cost assumption bug.

**Go/no-go gate before real money**: See Phase 2 gate below.

Sources: [Freqtrade pre-live checklist](https://dev.to/henry_lin_3ac6363747f45b4/lesson-22-freqtrade-pre-live-trading-checklist-1i8e), [Minimum trades for valid backtest](https://www.backtestbase.com/education/how-many-trades-for-backtest), [Sharpe ratio for algo trading](https://www.quantstart.com/articles/Sharpe-Ratio-for-Algorithmic-Trading-Performance-Measurement/), [Alpaca paper vs live guide](https://alpaca.markets/learn/paper-trading-vs-live-trading-a-data-backed-guide-on-when-to-start-trading-real-money)

---

### Q5. Alpaca specifics in 2026: paper vs live behavioral differences

**Key behavioral differences (Alpaca paper vs live)**:

| Dimension | Paper | Live |
|---|---|---|
| Fill model | Simplified — best available NBBO, infinite liquidity | Real order book; quantity limited to available liquidity at NBBO |
| Slippage | Not simulated | Real slippage; large orders walk the book |
| Market impact | Not simulated | Real |
| Order queue position | Not simulated | Real (non-marketable limit orders queue) |
| Price improvement | Not simulated | Real (sometimes better than NBBO) |
| Dividends | NOT simulated | Paid to account |
| Borrow fees (short) | "Coming soon" | Applied |
| PDT rule | Enforced (simulated) | Enforced (real) |
| Regulatory fees | Not simulated | Applied |
| Data feed | IEX market data | IEX market data (same) |
| Starting balance | Default $100k | Actual deposited funds |
| API spec | Identical | Identical (different keys, different base URL) |

**Critical implication**: paper fills will always be *better* than live fills. This is the most important source of paper-to-live performance degradation. The system's 5 bps cost assumption partially compensates, but does not model queue position or market impact.

**PDT rule**: Both environments enforce it. Orders that would generate a 4th day trade within 5 business days are rejected if net liquidation value < $25,000. For a *daily signal* system executing once per morning, PDT is not triggered (a "day trade" requires opening and closing a position within the same day). A position opened at 9:35 and held overnight is not a day trade.

**Account minimum**: No stated minimum for live. $0 commission on US stocks and ETFs. Crypto trading available.

**MOC/LOC orders**: Available via `time_in_force="cls"` — but **only on Alpaca Elite plan**. CLS orders submitted after 3:50 pm ET are rejected; after 7:00 pm ET they queue for the next close. For a non-Elite account, the alternative is a limit order placed ~3:45 pm ET via a second scheduled job.

**Broker comparison**: For a sub-$25k daily-signal account, Alpaca remains the best choice for algorithmic US equities in 2026 due to commission-free API access, paper/live parity of API spec, and no account minimum. IBKR has a better execution quality model (real market impact simulation, more order types), but its API complexity and the $10k/month minimum activity fees (for the Lite tier) make it less attractive at this scale. Tradier has a commission-free API tier but thinner ecosystem.

Sources: [Alpaca paper trading docs](https://docs.alpaca.markets/us/docs/paper-trading), [Alpaca order types](https://alpaca.markets/learn/13-order-types-you-should-know-about), [Alpaca working with orders](https://docs.alpaca.markets/us/docs/working-with-orders), [Alpaca paper vs live support](https://alpaca.markets/support/difference-paper-live-trading)

---

### Q6. Live execution timing alignment: MOC vs 9:35 market orders

**The core problem**: The current system backtests on daily close data and executes at 9:35 the next morning — a known and flagged signal-timing skew. The two clean solutions are:

**Option A — Execute at open (9:35 market order, backtest with next-open fills)**  
Align the backtest to fill at the *open* of the bar following the signal. The system already executes at 9:35, so change the backtest engine's fill price from `close` to `next_open`. This is the simpler code change. Downside: opening auction can gap significantly from prior close on news.

**Option B — Execute near close (MOC/LOC order, backtest with close fills)**  
The backtest already uses close prices. Change live execution to submit a CLS (Market on Close) order by 3:50 pm ET the same day the signal fires (not the next morning). This requires a second scheduler slot at ~3:45 pm ET on market days and an **Alpaca Elite plan** for the `cls` time-in-force. Upside: tight alignment with backtest assumptions. Downside: cost ($?) and the 3:50 pm deadline constraint.

**Recommendation**: Implement **Option A** first (pure code change in the engine, no account upgrade needed). Change `vectorized_engine.py` to use `next_open` as the fill price. This eliminates the skew at zero cost. Graduate to Option B when/if you move to a live account and care about close-price fills enough to pay for Elite.

MOC orders are not available in the free Alpaca tier — the `cls` time_in_force requires Elite. For paper trading, a 9:35 market order is an acceptable proxy. The discipline needed is consistency: whichever you pick, both backtest and live must use the same fill assumption.

Sources: [Alpaca order types and time-in-force](https://alpaca.markets/learn/13-order-types-you-should-know-about), [QuantConnect MOC timing issue](https://www.quantconnect.com/forum/discussion/18821/timing-issue-using-market-orders-on-daily-resolution/), [MOC order mechanics](https://kjtradingsystems.com/market-on-close.html)

---

### Q7. Minimal live risk layer for one account

The architecture review already identified this as the critical gap: the current system has a backtest-time drawdown breaker but no *live* pre-trade risk check. Here is the minimal viable live risk layer:

**Required components**:

1. **Max daily loss circuit breaker**: Track realized + unrealized P&L since market open. If P&L drops below `-max_daily_loss_pct * account_equity`, halt all new orders for the day and send SMS alert. Implement as middleware in `/paper/execute`.

2. **Max position count**: Reject orders if `len(current_positions) >= max_positions`. Current system trades one symbol at a time, so this is a guard, not a constraint.

3. **Per-symbol exposure cap**: Reject order if `|order_notional| > max_symbol_pct * account_equity`. The system already has a 10% notional cap — move this check to pre-trade in the execution endpoint, not inside strategy code.

4. **Kill switch**: `POST /risk/kill` sets a flag in Postgres (`risk_state` table). `/paper/execute` checks this flag before submitting any order. `GET /risk/status` returns current state. Can be triggered from the thin ops HTML page or SMS.

5. **Reconciliation job**: Nightly (or pre-market) job that calls `GET /paper/positions` (Alpaca) and compares against the system's expected book (last trade log). Differences trigger an SMS alert. This is the "expected book vs broker positions" check the architecture review flagged.

**Reference implementations**:
- [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) — production-grade risk engine in Rust/Python; overkill to adopt wholesale but its `RiskEngine` class is readable source for the pattern. Supports position limits, exposure caps, kill switch.
- `yakub268/algo-trading-platform` on GitHub: production live system (2026) with three-tier risk: bot-level gates, fleet-level limits, orchestrator-level veto. $30/day loss limit, 25 max positions, 80% exposure cap, contradictory-position blocker.

**What NOT to do**: Don't embed risk logic inside strategy code. It must be a separate layer that all execution paths pass through. The architecture review is explicit on this.

Sources: [NautilusTrader](https://nautilustrader.io/), [NautilusTrader GitHub](https://github.com/nautechsystems/nautilus_trader), [Risk management strategies algo trading](https://www.luxalgo.com/blog/risk-management-strategies-for-algo-trading/), [algo52 kill switch](https://www.algo52.com/compliance/risk-management/)

---

## Section C — Making the Research Loop Smarter

### Q8. Multimodal video extraction: frame sampling + Claude vision for chart reading

**Current gap**: the audio-extraction pipeline transcribes speech but discards all on-screen information — tickers, chart patterns, indicator values, price levels shown visually.

**Recommended frame extraction strategy**:

Use ffmpeg scene-change detection as the primary method (not fixed-interval sampling). Scene changes in financial videos correspond to chart cuts, ticker changes, and new indicator displays — exactly the frames worth sending to Claude. Fixed-interval sampling generates redundant near-duplicate frames and inflates token usage.

**ffmpeg command pattern**:
```bash
# Scene-change keyframes (threshold 0.3 = moderate sensitivity)
ffmpeg -i video.mp4 -vf "select='gt(scene,0.3)'" -vsync vfr frames/scene_%04d.jpg

# Deduplicate: compute brightness MAD between consecutive frames; drop if < 2.0
# (implemented in claude-real-video and jordan rendric's claude-video-vision)
```

**Token budget guidance**: A typical 10-minute trading reel produces 40–120 scene-change frames at 0.3 threshold. Deduplicated, this drops to 20–60 unique frames. At Claude's vision pricing, 60 frames at low detail is affordable. The key optimizations:
1. Scale frames to 512×512 or smaller before sending (chart text is readable at this resolution).
2. Use `low` detail mode for initial frame pass; send only frames flagged as "contains chart" to a second `high` detail call.
3. Send frames in a single multi-image message alongside the transcript, asking Claude to correlate visual and audio signals.

**Prompt structure**: "You are analyzing a trading strategy video. The transcript is: [transcript]. The following frames are from the video at the timestamps indicated. For each frame containing a chart or ticker: extract the ticker symbol, timeframe, visible indicator names and values, key price levels, and any on-screen text about entry/exit rules. Then reconcile with the transcript."

Sources: [claude-real-video GitHub](https://github.com/HUANGCHIHHUNGLeo/claude-real-video), [claude-video-vision GitHub](https://github.com/jordanrendric/claude-video-vision), [claude-video GitHub](https://github.com/bradautomates/claude-video), [Claude video analysis 2026](https://cutback.video/blog/can-claude-analyze-videos-2026-answer-selects-mpc)

---

### Q9. Research on finfluencer strategy quality — calibrating expectations

**What the academic literature says (2025–2026)**:

A key finding from the 2026 AEA conference paper (Hull & Qi): finfluencers' skills are persistent but **skill is not sufficient for survival** — unskilled and antiskilled finfluencers command *larger* followings than skilled ones. Engagement is driven by entertainment, narrative, and stock momentum storytelling rather than actual edge.

A study of Financial YouTubers in India found they are more likely to recommend stocks with strong *past performance* and high trading volume — i.e., they chase momentum and describe it as strategy. This is look-ahead bias baked into the "strategy" itself.

**Practical calibration**:
- Assume 80%+ of video strategies will *not* survive a properly cost-adjusted, walk-forward backtest. The base rate of real edge in a retail video strategy is low.
- The most common failure mode is: strategy was a momentum overlay on the 2020–2021 bull run; backtest period selection cherry-picks that window.
- The value of the video pipeline is *idea generation and parameter starting points*, not strategy validation. Every imported strategy needs to pass the full champion/challenger gate (walk-forward OOS, cost-adjusted Sharpe > 1.0) before being taken seriously.
- Strategies involving specific technical patterns (ORB, specific MA crosses) are easier to formalize and test honestly than qualitative "read the tape" strategies.

Sources: [Finfluencers AEA 2026 paper](https://www.aeaweb.org/conference/2026/program/paper/NrYH7E2d), [Finfluencer recommendations ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0165176525003489), [Finfluencer quality framework Springer](https://link.springer.com/article/10.1057/s41264-025-00334-7), [Kakhbod et al. finfluencers paper](https://jhfinance.web.unc.edu/wp-content/uploads/sites/12369/2023/11/Finfluencers.pdf)

---

## Section D — Path to Actually Making Money

### Q10. Where retail algos can still find edge in 2026

**Practitioner consensus on less-crowded edges**:

1. **Overnight effect / overnight drift**: Documented anomaly — nearly all US equity market gains over 30 years have been earned overnight, with intraday returns flat or negative. However, the 2026 arxiv paper (Hull & Qi) finds that the extreme turnover required to systematically trade it (daily rebalancing of 25–50 positions) makes transaction costs prohibitive for retail. *Viable as a timing rule* (prefer overnight holds to intraday) rather than as a standalone strategy. The overnight drift is strongest in small/mid-caps with retail attention.

2. **Congressional disclosure lag**: STOCK Act requires disclosure within 45 days; actual average is 49 days with 12.5% of trades filed later. Despite the lag, Signal Congress data (2023–2026) shows bipartisan clusters (both parties buying the same stock within 30 days) have historically outperformed S&P 500 by +8% at 180 days. A-tier and S-tier legislators (by win rate) can be tracked as a filter. **This edge is data-dependent** — requires a Quiver Quantitative API key (~$50/mo for the relevant tier) or a scraper. The edge narrows as it becomes more widely followed.

3. **Small-cap momentum**: Momentum returns are primarily earned overnight (per academic literature). Less crowded than large-cap because institutional size constraints prevent them from entering. High transaction costs for small-caps (wider spreads) eat the edge at small size — model this honestly at 15–25 bps/side for small-caps vs 5 bps for large liquid ETFs.

4. **13F drift / whale copycat**: Quarterly rebalancing lag is structural (45-day filing delay + quarterly cadence). The edge documented for certain funds (Berkshire, certain 13F filers) is mostly priced in for well-known positions. Less efficient for smaller, less-followed 13F filers.

5. **Crypto microstructure**: Higher spreads, more retail flow, less institutional efficiency than US equities. Requires 24/7 operation and different risk (exchange custody risk). Out of scope for this system's current architecture.

**Waste of time for this system**:
- HFT (sub-millisecond): requires co-location, FIX, direct market access — not available to retail
- Large-cap intraday momentum: extremely crowded; institutional algo presence at microsecond scale
- Statistical arbitrage pairs: crowded at hedge funds; edge is commoditized

Sources: [Overnight returns research arxiv 2026](https://arxiv.org/html/2507.04481v1), [Elm Wealth overnight drift](https://elmwealth.com/night-moves-overnight-drift/), [Signal Congress research](https://www.signalcongress.com/research), [Quiver Quantitative congress data](https://www.quiverquant.com/congresstrading/), [Congressional trading guide 2026](https://congresstierlist.com/guides/congressional-stock-trading/), [Hedge fund momentum 2026](https://www.withintelligence.com/insights/hedge-fund-outlook-2026/)

---

### Q11. Realistic return expectations for a $5–25k daily-signal account

**Framework**:

With 5 bps/side costs (the system's current default) and a daily signal on liquid large-cap ETFs or stocks:
- Each roundtrip costs 10 bps (0.10%)
- A daily-signal strategy trades roughly once per day it's in the market; if in the market 60% of trading days, that's ~125 roundtrips/year
- Annual cost drag: 125 × 0.10% = 12.5% — *substantial*
- This means the gross strategy edge must exceed 12.5%/year before it produces any net return
- For small-caps (15–25 bps/side), the break-even rises to 37.5–62.5%/year gross — very high bar

**Realistic outcome targets for a *good* result**:
- Post-cost Sharpe ratio: 0.8–1.5 (annualized, out-of-sample paper period)
- Annualized net return: 10–25% on a $10k account
- Maximum drawdown tolerance: < 20%
- Monthly infra burn to clear: ~$30–40/mo (current docker-compose local setup is $0 infra; cloud VM adds ~$12–25/mo)

**A Sharpe of 1.0 with 15% annualized return on $10k = $1,500/year net** — respectable for a learning system but not "quit your job" money. The value is compounding, risk management experience, and the option to scale.

A 2025 paper tracking the top 20 "in play" stocks daily showed Sharpe of 2.81 and 36% alpha — but this requires more active selection and higher turnover than a champion-per-symbol daily signal.

Sources: [Sharpe ratio for algo trading QuantStart](https://www.quantstart.com/articles/Sharpe-Ratio-for-Algorithmic-Trading-Performance-Measurement/), [Realistic Sharpe ratios 2026 EliteTrader](https://www.elitetrader.com/et/threads/realistic-sharpe-ratios-in-2026-hft-vs-retail-algos-deep-dive.388680/), [Algo trading metrics guide](https://tradingwyckoff.com/en/algorithmic-trading/algorithmic-trading-metrics/)

---

### Q12. Tax and structural considerations

**Wash sale rule and automated trading**:

The wash sale rule (IRC Section 1091) disallows loss deductions if you buy a "substantially identical" security within 30 days before or after a loss sale (61-day window). For an automated daily signal that may buy/sell the same ETF repeatedly, this can trigger wash sales across hundreds of transactions, dramatically complicating tax accounting even in years with net losses.

**Section 475(f) Mark-to-Market Election**:

Traders who qualify can elect MTM accounting, which:
1. Treats all open positions as sold at fair market value on December 31 each year
2. **Completely exempts traders from the wash sale rule** — the primary benefit for algo traders
3. Converts capital gains/losses to ordinary income/loss — removes the $3,000 annual cap on capital loss deductions
4. Losses become fully deductible as ordinary losses (valuable in losing years)

**Who qualifies**: The IRS requires "trader" status (not "investor") — substantial, regular trading activity, short-term profit focus, significant time commitment. An automated system running daily signals likely qualifies if it generates 200+ trades/year, but this is a facts-and-circumstances determination. Consult a CPA.

**2026 election deadline**: To elect MTM for 2026, you must have filed the election statement attached to your 2025 tax return by **April 15, 2026**. If you missed this, the earliest you can elect is for tax year 2027 (election filed by April 15, 2027 with your 2026 return, or with a timely extension request).

**Practical advice**:
- If trading < 200 roundtrips/year (plausible for a daily-signal champion-per-symbol system), the wash sale burden is manageable with good record-keeping
- If you scale to multiple symbols (3–5 champions), 475(f) election becomes worth serious consideration
- Keep the system's audit log (`paper_log` table) — it is exactly the record-keeping evidence the IRS requires

Sources: [Section 475(f) MTM election guide 2026](https://unclekam.com/tax-write-offs/deductions/mark-to-market-election-section-475/), [IRS rules for day traders 2026](https://www.alphaexcapital.com/stocks/stock-brokers-and-trading-accounts/taxes-and-regulations-for-stock-investors/irs-rules-for-day-traders), [Wash sale algo trading](https://terms.law/Trading-Legal/guides/wash-sale-algo-trading.html), [Section 475 MTM election deadline](https://kascpas.com/blog/section-475-mark-to-market-trader-tax), [Databento MTM compliance guide](https://databento.com/compliance/mark-to-market-election)

---

## The Plan: Phases 0–3

*Executable by one person in evenings, ~8 weeks total. Builds on what exists — no rebuild of the engine, no n8n.*

---

### DO NOT BUILD LIST

Before the phases: things that look productive but don't move the needle for a solo operator:

1. **MCP server** — exposing `/run_backtest` as a Claude tool sounds fun but adds zero live-trading capability. Build it after real money is at stake.
2. **OANDA forex connector** — second broker, different asset class, before the primary system is live-validated. Distraction.
3. **Portfolio-level allocation across N champions** — requires more capital and paper history to validate. Not week-8 material.
4. **Sentiment connector** — no free high-quality sentiment feed; building a scraper is a rabbit hole; this is Phase 4+ work.
5. **Local LLM analyst (Ollama)** — 3B models give garbled output (per README's own caveat). The effort to improve this is better spent on the risk layer.
6. **AWS EKS deployment** — infra learning lab, not trading lab. Keep docker-compose until real money demands HA.
7. **n8n re-introduction** — was deliberately removed. The in-process scheduler is sufficient and simpler.
8. **Intraday strategies** — requires intraday data feed, different backtesting approach, different execution cadence. Out of scope until daily strategies are live-proven.
9. **New charting library in Grafana** — Grafana already has sufficient charting; investing in a custom React/Chart.js frontend before the risk layer exists is wrong priority order.
10. **Congress copycat (real API)** — Quiver API is $50+/mo; the strategy needs the lag modeled correctly first. Research project, not week-8 scope.

---

### Phase 0 — Harden the Foundation (Weeks 1–2)

**Goal**: Make the existing paper-trading system production-honest before adding anything new. No new features — close the gaps flagged in the architecture review.

**Tasks**:

1. **Fix signal-timing skew** (1 evening)  
   In the backtest engine, change the fill price from `close` to `next_open` for all daily-signal strategies. Add a config flag `fill_at="next_open|close"` so both modes are testable. Re-run the current champion's backtest with `next_open` fills and note the Sharpe delta. If Sharpe drops below 0.5, the "strategy" was timing arbitrage, not edge.

2. **Wire champion promotion gate to walk-forward OOS** (1 evening)  
   `POST /champion/auto/{symbol}` currently promotes on in-sample Sharpe. Change it to require: (a) walk-forward OOS Sharpe > 1.0 AND (b) cost-adjusted. The `/walkforward` endpoint exists — wire the result into the promotion decision.

3. **Add failure alerting (dead-man switch)** (1 evening)  
   The architecture review flags silent failures as the "always-on blocker." Add:
   - Error handler in the scheduler (`scheduler.py`) that sends SMS on any uncaught exception (not just success)
   - `HEALTHCHECK_URL` ping at the end of the nightly sweep (use healthchecks.io free tier) — missed ping = email/SMS even if the entire container dies
   - Log errors to a `scheduler_errors` table in Postgres for post-mortem

4. **Flag survivorship bias on multi-symbol backtests** (½ evening)  
   Add a warning field to the backtest response: `"survivorship_bias_warning": true` when `universe_size > 1` and the universe was not specified with point-in-time membership. This is a data-quality flag, not a fix — the fix requires a paid PIT data source.

**Acceptance criteria**:
- [ ] Re-running the current champion with `next_open` fills produces a Sharpe that is logged and compared to the `close` fill Sharpe
- [ ] `/champion/auto/{symbol}` rejects promotion if walk-forward OOS Sharpe < 1.0
- [ ] A deliberately broken scheduler job sends an SMS alert within 5 minutes
- [ ] healthchecks.io shows a green heartbeat on market days

**Phase 0 go/no-go gate**: All four acceptance criteria met before proceeding.

---

### Phase 1 — Live Risk Layer (Weeks 3–4)

**Goal**: Add the pre-trade risk layer that separates strategy logic from execution safety. This is the prerequisite for any real-money discussion.

**Tasks**:

1. **`risk_state` table in Postgres** (½ evening)  
   Columns: `kill_switch_active` (bool), `max_daily_loss_pct` (float, default 2.0), `max_positions` (int, default 5), `max_symbol_pct` (float, default 10.0). Seeded at startup if not present.

2. **Pre-trade risk check middleware** (2 evenings)  
   Add a `RiskGuard` class called by `/paper/execute` before any order submission:
   - Check `kill_switch_active` — if True, return 403 with reason
   - Check current open positions count vs `max_positions`
   - Check proposed order notional vs `max_symbol_pct * account_equity`
   - Compute today's realized + unrealized P&L (from Alpaca account equity delta since open); if < `-max_daily_loss_pct * account_equity`, halt and send SMS
   - Log every pre-trade check result to a `risk_log` table

3. **Kill switch endpoints** (½ evening)  
   `POST /risk/kill` — sets `kill_switch_active = True`, sends SMS  
   `POST /risk/resume` — clears kill switch  
   `GET /risk/status` — returns current risk state + today's P&L vs limits

4. **Reconciliation job** (1 evening)  
   Add to the scheduler: weekdays at 9:40 ET (after paper trade executes), compare:
   - System's expected position (from `paper_log`: last open trade per symbol)
   - Alpaca's actual position (`GET /paper/positions`)
   - If mismatch: log to `reconciliation_errors` table + SMS alert  
   
5. **Thin ops HTML page** (1 evening)  
   FastAPI-served `/ops` endpoint returning a minimal HTML page (Jinja2 + htmx) with:
   - Current risk state (read from `/risk/status`)
   - Kill switch button (POST to `/risk/kill`)
   - Today's P&L vs limit
   - Last 5 paper trades from `paper_log`
   - Link to Grafana
   
   This replaces the need to SSH into the box to check status.

**Acceptance criteria**:
- [ ] Submitting an order when `kill_switch_active = True` returns 403 (tested via `/docs`)
- [ ] An order that would exceed 10% notional cap is rejected with a reason code
- [ ] Simulated daily loss of 3% (via a test endpoint) triggers SMS and halts further orders that day
- [ ] Reconciliation job runs successfully at 9:40 ET on a market day and produces output
- [ ] `/ops` page loads and shows current risk state

**Phase 1 go/no-go gate**: All five acceptance criteria met before any discussion of real money.

---

### Phase 2 — Paper Validation Period (Weeks 5–8)

**Goal**: Run the hardened system for 8+ weeks in paper mode, accumulate evidence, and build the paper-to-live dossier.

**Tasks**:

1. **Expand to 3 symbols** (½ evening)  
   Add 2 more symbols to `STUDIO_SYMBOLS` (e.g., SPY, QQQ, IWM — all liquid ETFs with low spread cost assumption justified). This generates 3× the paper trade count per week, reaching ~100 paper trades in 8 weeks rather than 33.

2. **Walk-forward overlay panel in Grafana** (1 evening)  
   Add a Grafana panel that displays the walk-forward OOS stitched equity curve alongside the in-sample curve. The `/walkforward` endpoint returns this data; it needs a Grafana query or a scheduled job that stores OOS curve points in Postgres.

3. **Paper performance tracking dashboard** (1 evening)  
   Add a Grafana "Paper vs Backtest" panel that tracks, per symbol per week:
   - Paper cumulative return
   - Backtest expected return (same period)
   - Tracking error (paper - backtest)
   - Paper Sharpe (rolling 4-week)
   
   Alert (SMS) if paper Sharpe drops below 0.5 for 2 consecutive weeks — possible signal of regime change or execution bug.

4. **Multimodal video upgrade** (2 evenings — optional, can defer to Phase 3)  
   Update the audio-extraction pipeline to extract scene-change frames via ffmpeg (threshold 0.3), deduplicate, and pass frames + transcript to Claude in a single call. Use the prompt structure from Q8 above. Test on 3 recent reels and compare extracted strategies to audio-only results.

5. **Build the go/no-go dossier** (ongoing)  
   At the end of week 8, compile:
   - Paper period: start date, end date, trade count per symbol
   - Paper Sharpe (annualized) per symbol
   - Max drawdown during paper period
   - Tracking error vs backtest (paper return ÷ backtest return for same period)
   - Zero execution errors (failed orders, duplicate positions, missed reconciliations)
   - Risk layer has never been bypassed

**Acceptance criteria (end of Phase 2)**:
- [ ] ≥ 100 total paper trades across all symbols
- [ ] Paper period ≥ 8 weeks (ideally spanning a volatility event)
- [ ] At least one champion per symbol with OOS walk-forward Sharpe ≥ 1.0
- [ ] Paper Sharpe ≥ 0.8 (annualized, not in-sample)
- [ ] Paper return within ±50% of backtest return for same period (not wildly better = overfit)
- [ ] Max drawdown during paper period < 20%
- [ ] Zero undetected reconciliation mismatches (may have detected ones that were resolved)
- [ ] Dead-man switch has been triggered at least once in testing

**Phase 2 go/no-go gate (REAL MONEY GATE)**:

**All six performance criteria above must be met.** If paper Sharpe is high but tracking error is extreme (paper much better than backtest), do NOT go live — the backtest is overfit and real performance will revert. If paper Sharpe is < 0.8 for all symbols, extend the paper period or re-run the champion sweep with a larger strategy grid before proceeding.

Additional pre-live checklist (qualitative):
- [ ] You can explain, in plain English, *why* the champion strategy makes money (what market behavior it exploits)
- [ ] You have read and understand the Alpaca live account fee schedule and any borrow/regulatory fees
- [ ] You have a written risk plan: max loss per trade, max loss per day, max loss before shutting down for the month
- [ ] Tax situation reviewed: is your trade frequency sufficient to consider 475(f)? (Consult a CPA if > 200 trades/year projected)
- [ ] Start size decided: < 10% of investable net worth, or a specific dollar amount you can afford to lose entirely

---

### Phase 3 — Live Money (Post week 8, conditional on Phase 2 gate)

**Goal**: Deploy real money on the smallest viable position size, treat as a learning phase, not a profit phase.

**Tasks**:

1. **Fund live Alpaca account** (½ hour)  
   Minimum suggested: $5,000–$10,000. Position sizing at 10% = $500–$1,000 per trade. This is small enough to be educational, large enough that execution costs and fills are realistic.

2. **Switch API keys** (½ hour)  
   Change `.env` `APCA_API_BASE_URL` to the live endpoint and swap to live API keys. The paper account remains active for continued parallel paper runs. The code path is identical — `paper=True` is the only flag.
   
   Wait: the current code has `paper=True` **hardcoded**. Before going live, refactor `/paper/execute` to read `APCA_PAPER_MODE=true/false` from env. This is a 10-line change but a critical one — audit the entire execution path.

3. **Lower position size for first 30 days** (config change)  
   Set `position_size_pct` to 5% for the first month. Scale back up to 10% only after 30 live trades with no execution surprises.

4. **Daily reconciliation review** (5 min/day)  
   Check the `/ops` page daily for the first month. Do not rely solely on SMS alerts — human eyes on the system during the initial live period.

5. **Post-trade analysis** (weekly, 1 hour)  
   Compare live fills vs paper fills for the same signals. Document slippage. If live fills are consistently 10+ bps worse than paper, revisit the cost assumption (raise `cost_bps` to 8–10 bps in backtests).

**Acceptance criteria**:
- [ ] 30 live trades executed without execution errors or unexpected positions
- [ ] Live Sharpe (annualized from 30 trades, rough) ≥ 0.5
- [ ] Live max drawdown < 20%
- [ ] No risk layer bypass events
- [ ] Live vs paper fill quality documented (slippage delta measured)

**Phase 3 go/no-go gate (scale-up)**: After 3 months live (not just Phase 2 paper), with ≥ 60 live trades and sustained Sharpe ≥ 0.8, consider scaling position size to 15–20% or adding a second symbol. Not before.

---

## Summary: Go/No-Go Gates Before Real Money

| Gate | When | What must be true |
|---|---|---|
| **Phase 0 → 1** | End week 2 | Timing fix deployed; walk-forward gate wired; dead-man switch firing; healthcheck green |
| **Phase 1 → 2** | End week 4 | Risk layer fully functional; kill switch tested; reconciliation running; ops page live |
| **Phase 2 → 3 (REAL MONEY)** | End week 8 | ≥100 paper trades, ≥8 weeks, paper Sharpe ≥0.8, tracking error ≤50%, max DD <20%, zero undetected mismatches, written risk plan, tax situation reviewed |
| **Phase 3 → Scale** | 3 months post-live | ≥60 live trades, live Sharpe ≥0.8, slippage documented, no risk bypasses |

---

## Sources

### Primary Sources

- [Alpaca Paper Trading Documentation](https://docs.alpaca.markets/us/docs/paper-trading)
- [Alpaca Order Types and Time-in-Force](https://alpaca.markets/learn/13-order-types-you-should-know-about)
- [Alpaca Working with Orders](https://docs.alpaca.markets/us/docs/working-with-orders)
- [Alpaca Paper vs Live Guide (data-backed)](https://alpaca.markets/learn/paper-trading-vs-live-trading-a-data-backed-guide-on-when-to-start-trading-real-money)
- [Alpaca Paper vs Live Support FAQ](https://alpaca.markets/support/difference-paper-live-trading)
- [NautilusTrader open-source trading platform](https://nautilustrader.io/)
- [NautilusTrader GitHub](https://github.com/nautechsystems/nautilus_trader)
- [TradingView Lightweight Charts homepage](https://www.tradingview.com/lightweight-charts/)
- [TradingView Lightweight Charts GitHub](https://github.com/tradingview/lightweight-charts)
- [uPlot GitHub (MIT license)](https://github.com/leeoniya/uplot)
- [IRS Section 475(f) MTM election guide](https://unclekam.com/tax-write-offs/deductions/mark-to-market-election-section-475/)
- [Section 475 election deadline 2026](https://kascpas.com/blog/section-475-mark-to-market-trader-tax)
- [Wash sale rule for algorithmic trading](https://terms.law/Trading-Legal/guides/wash-sale-algo-trading.html)
- [Databento MTM compliance guide](https://databento.com/compliance/mark-to-market-election)
- [Signal Congress research (congressional trading backtest data)](https://www.signalcongress.com/research)
- [Quiver Quantitative congress trading data](https://www.quiverquant.com/congresstrading/)
- [Minimum trades for valid backtest](https://www.backtestbase.com/education/how-many-trades-for-backtest)
- [Freqtrade pre-live trading checklist](https://dev.to/henry_lin_3ac6363747f45b4/lesson-22-freqtrade-pre-live-trading-checklist-1i8e)

### Academic / Research Sources

- [Overnight news and overnight returns (arxiv 2026)](https://arxiv.org/html/2507.04481v1)
- [Intraday and overnight return anomalies — 11.6M observations (ScienceDirect 2025)](https://www.sciencedirect.com/science/article/abs/pii/S1544612325018926)
- [Elm Wealth: overnight drift anomaly survey](https://elmwealth.com/night-moves-overnight-drift/)
- [Finfluencers — skill vs survival (AEA 2026)](https://www.aeaweb.org/conference/2026/program/paper/NrYH7E2d)
- [Finfluencer recommendations and past returns (ScienceDirect 2025)](https://www.sciencedirect.com/science/article/abs/pii/S0165176525003489)
- [Kakhbod et al. finfluencers paper (UNC)](https://jhfinance.web.unc.edu/wp-content/uploads/sites/12369/2023/11/Finfluencers.pdf)
- [Sharpe ratio for algorithmic trading (QuantStart)](https://www.quantstart.com/articles/Sharpe-Ratio-for-Algorithmic-Trading-Performance-Measurement/)

### Tool / Library Sources

- [claude-real-video GitHub (scene-aware frame extraction)](https://github.com/HUANGCHIHHUNGLeo/claude-real-video)
- [claude-video-vision GitHub (MCP plugin)](https://github.com/jordanrendric/claude-video-vision)
- [claude-video GitHub](https://github.com/bradautomates/claude-video)
- [QuantConnect terminal and docs](https://www.quantconnect.com/terminal/)
- [OpenAlgo open-source algo platform](https://github.com/marketcalls/openalgo)
- [algo52 risk management and kill switch](https://www.algo52.com/compliance/risk-management/)

### Market / Regulatory Sources

- [Congressional stock trading complete guide 2026](https://congresstierlist.com/guides/congressional-stock-trading/)
- [GovGreed congressional trade analysis](https://www.govgreed.com/data/do-politicians-beat-the-market)
- [IRS rules for day traders 2026](https://www.alphaexcapital.com/stocks/stock-brokers-and-trading-accounts/taxes-and-regulations-for-stock-investors/irs-rules-for-day-traders)
- [QuantConnect MOC timing discussion](https://www.quantconnect.com/forum/discussion/18821/timing-issue-using-market-orders-on-daily-resolution/)
- [MOC order mechanics (KJ Trading Systems)](https://kjtradingsystems.com/market-on-close.html)
- [Backtesting software ranked 2026 (LuxAlgo)](https://www.luxalgo.com/blog/backtesting-software-ranked-for-retail-quants/)
