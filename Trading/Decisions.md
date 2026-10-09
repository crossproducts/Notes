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

Related: [[Home]] · [[Go-Live Checklist]]
