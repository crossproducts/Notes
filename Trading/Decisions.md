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

Related: [[Home]] · [[Go-Live Checklist]]
