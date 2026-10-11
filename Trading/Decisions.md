# Decisions

Append-only. Date, decision, why. Future-you will thank present-you.

- **2026-07** — Removed n8n; its two cron duties + SMS chaining moved into the
  API scheduler. One less container, errors alert instead of failing silently.
- **2026-07** — `paper=True` hardcoded in `paper.py`. Going live is a code
  change with review, never a config flip.
- **2026-07** — Champion promotion gates on walk-forward OOS return, not
  in-sample sharpe (in-sample promotion is institutionalized overfitting).
- **2026-07** — Transaction costs (5 bps/side) default ON in every backtest;
  frictionless is opt-in.
- **2026-07-18** — Added: ffmpeg frame capture + Claude vision to the video
  pipeline (on-screen numbers were being lost); live risk layer with kill
  switch; product UI served by the API. Second brain created (`Trading/`).
- **2026-07-18** — Fill-timing skew fixed with **Option A** (backtest fills at
  next open, matching 9:35 live execution). Option B (MOC orders at close)
  rejected for now — requires Alpaca Elite; revisit at live scale.
- **2026-07-18** — Portfolio mode (inverse-vol weights across champions,
  capped 40%/symbol) is **manual-only** (`/portfolio/execute`); the 9:35
  scheduler still runs single-champion until portfolio behavior is observed.
- **2026-07-18** — Expectation set by research: assume ~80% of video-extracted
  strategies fail cost-adjusted walk-forward. The reel pipeline is an idea
  generator, not a validator.
- **2026-10-06** — Rejected the efficiency-ratio forecast gate (reel
  DeF5_5yPtDb) and kept it out of the champion path. Rebuilt it honestly
  (strictly OOS, train-only cuts) rather than reusing the reel's published
  weights; the model scores OOS AUC 0.52-0.54 and lands *below* the
  majority-class baseline, and gating made all 10 strategy/instrument
  combinations worse. Kept as builtin `efficiency_gate` — a registered,
  reproducible negative result is worth more than a deleted branch.
- **2026-10-06** — Pinned the Postgres driver (`postgresql+psycopg2://`) in
  compose and `main.py`. The API image rebuilt onto a newer SQLAlchemy that
  resolves a bare `postgresql://` to psycopg v3, which the image does not
  ship; the container crash-looped. Unpinned requirements are the root cause
  and are still unpinned — worth a follow-up.
- **2026-10-06** — Fixed `sources.yaml`: it had been **unparseable since
  committed** (a `Red flag:` colon inside a plain multi-line scalar), so
  `run_queue.py` could not read the research queue at all. Notes containing
  `: ` are now folded block scalars (`>-`). Worth a CI check — a queue that
  silently cannot load is worse than an empty one.
- **2026-10-09** — Expanded the studio rather than starting a separate
  "engine projects" repo, and added [[Engine Backlog]] for capability work.
  Driver: of six @quantpapers reels, only one was directly testable and two
  were blocked on engine capability — the pipeline now yields more engine
  requirements than strategies, and they had nowhere to live.
- **2026-10-09** — Overnight/close-to-open effect tested and **rejected**. The
  anomaly is real and exact (overnight x intraday reproduces buy&hold to the
  dollar) but it round-trips every session: at our 5bps/side SPY is -99%
  (sharpe -1.42) and QQQ -96%. Survives only at ~1bp institutional execution,
  and even then SPY's sharpe (0.27) trails buy&hold (0.45). Best demonstration
  yet of why transaction costs default ON.
- **2026-10-10** — SSRN/literature sweep for champion-competitive strategies.
  Added `halloween` + `halloween_trend` builtins (Bouman & Jacobsen 2002;
  Zhang & Jacobsen 2021). Rationale is cost and correlation, not raw return:
  ~2 trades/yr makes 5bps a rounding error, and the signal is the calendar, so
  it correlates **0.42** to our trend/momentum family — which correlates
  **0.81 internally**, i.e. our book is one bet wearing six hats. Walk-forward
  19/22 positive OOS windows, stitched +596%.
  Rejected **volatility-managed portfolios** (Moreira & Muir 2017) on two
  counts: replications (Cederburg et al.; Barroso & Detzel) find up to 15x
  turnover and no positive alpha after costs — and our engine is binary
  (`invested = w if sig>0`), so continuous sizing is an engine gap regardless.
- **2026-10-10** — Discovered champion selection is **window-dependent** and
  logged it as E6. All runs start 2020-01-01; over 2000+ the ranking reverses
  (`momentum` 0.95->0.23, `trend_ma` 0.73->0.45). Our incumbent may be an
  artifact of a bull-market measurement window. This is a flaw in the HARNESS,
  not in any strategy, which makes it more important than any single result.
- **2026-10-11** — **Champion promotion rule changed** (E6). Selection no
  longer ranks on one window's sharpe. It now scores each strategy over
  2000/2007/2020, ranks on the **worst** window, and requires beating
  buy-and-hold in **all** of them. `/champion/evaluate/{symbol}` shows the
  ranking; the WF gate moved off its hardcoded 2018 start to the full cycle.
  **`triple_momentum` is the new SPY champion** (worst-window 0.44, spread
  0.29, 87 trades, maxDD -21.2%), replacing `momentum` (0.23, spread 0.72,
  20 trades). `trend_ma` was a near-tie at 0.43 — I had predicted it would win
  and the rule disagreed by 0.01; went with the rule.
  Caveat kept on the record: on walk-forward alone `momentum` was marginally
  AHEAD (543.6% vs 541.6%, 18/22 vs 15/22 positive windows), because WF
  re-optimises the lookback each window. Momentum's weakness is its *frozen*
  90-day parameter, not the concept.
  `/leaderboard` is unchanged and still a per-run, single-window view — the
  champion will sit below 2020-start runs there by design.

Related: [[Home]] · [[Go-Live Checklist]]

- **2026-10-11** — Measured our own **selection-noise floor**, prompted by a
  reel titled *"I backtested 10,000 strategies, here is the most profitable"*.
  Simulating our actual rule (best-of-N on the **worst** of the three E6
  windows) with every candidate having **zero true edge**: best-of-20 gives a
  worst-window sharpe of **mean 0.29, 95th pct 0.48**. The champion
  (`triple_momentum`) scores **0.44**. It clears the mean floor but **not the
  95th percentile** — roughly the 85-90th percentile of pure noise.
  Two things cut in our favour and are not modelled: the builtins are heavily
  correlated (trend/momentum family 0.81 internally), so the effective number
  of independent trials is well under 20; and the champion must also beat
  buy-and-hold in all three windows, a hurdle the null ignores.
  **Conclusion: the backtest alone cannot settle this.** This is the
  quantitative argument for the go-live gates that already exist — >=100
  paper trades and >=8 weeks on one champion are not bureaucracy, they are
  the only out-of-sample evidence that is not subject to this selection.

- **2026-10-11** — Shipped **E7**, and it changes what the champion means.
  Charging the ranking for its own size: 16 strategies, cross-sectional sharpe
  spread 0.21, so the best of 16 **zero-edge** candidates would score **0.417**.
  `triple_momentum` scores **0.44**. Deflated sharpe **0.55** — against a 0.95
  bar. **Nothing in the registry clears selection noise.**
  Two biases pull opposite ways and are documented in `analysis.py`: we do not
  charge for walk-forward's parameter grid (confidence too high), and we take
  V[SR] from a heterogeneous registry that contains real dispersion, not just
  sampling noise (confidence too low). Treat 0.55 as an order-of-magnitude
  check, not a p-value.
  **What this does NOT mean:** that the champion is worthless. It means the
  backtest cannot tell us, which is what the paper-trading gates are for.
  `min_dsr` therefore defaults OFF — turning it on today would leave no
  champion, and that should be a deliberate choice.

- **2026-10-11** — Added the **devil's advocate** (`advocate.py`). Every other
  module looks for a champion; this one argues the promotion is a mistake, on
  ten deterministic checks: selection noise, margin over the null, negative
  windows, buy-and-hold margin, cost fragility at 2x, regime spread, crowding
  against the incumbent, data floors, sample size, drawdown.
  **Deliberately not an LLM**, and E4 is the reason: the last multi-agent idea
  through this pipeline had its six agents silently replaced by hand-set
  technical conditions, so what got measured was never what was proposed. An
  objection you cannot reproduce is not evidence. `narrate()` writes the same
  findings in prose and can add nothing.
  It currently returns **BLOCK** on `triple_momentum`. Two objections, both
  the E7 finding. Two things it *cleared*, worth recording: the edge is **not**
  cost-fragile (0.44 -> 0.41 at 10 bps/side) and correlation to the incumbent
  `momentum` is 0.841, under the 0.90 crowding bar.
  Advisory by default — it reports, `auto_promote` decides — because a
  promotion pipeline that silently stops is worse than one that says why.
  `require_advocate_clear=True` makes it binding. The nightly SMS now carries
  the verdict: a pipeline that only reports good news trains you not to read it.

