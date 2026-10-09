# Engine Backlog

> Capabilities the **studio** lacks, not strategies. Lives here because
> [[Strategy Ideas]] is explicitly *"capture → triage → `sources.yaml` (videos)
> or a built-in strategy sketch"* — an engine requirement is neither, so
> findings kept landing with nowhere to go.

The research pipeline now produces more **engine requirements than strategies**.
Of the six @quantpapers reels processed 2026-10-09, one was directly testable,
one was a duplicate, one was education, one was untestable, and **two were
blocked on engine capability**. That ratio is the reason this file exists.

## Open

| # | Capability | Unblocks | Size | Why it matters |
|---|---|---|---|---|
| E1 | **Market-neutral long/short, multi-asset** | Deep Learning Stat Arb (`13233f413fe3`) | L | Engine is `fn(df,params) -> 0/1`, long-only, single-symbol. Stat arb needs long/short across ~550 names. Post-cost Sharpe ~1 is **not** better than our champion (1.17) — the real prize is **low correlation** to an all-long-beta book |
| E2 | **Intraday bars + cross-sectional ranking** | Heston intraday periodicity (`701ea111c21e`) | L | Needs 30-min bars over a wide cross-section and same-bin ranking. Alpaca supplies minute bars, so the *data* is reachable; the *engine* is not |
| E3 | **Refresh `architecture-review.md`** | trust in our own docs | S | It is **stale**: still claims "zero transaction costs ❌" and "promotion gates on in-sample sharpe". Both were fixed 2026-07 (see [[Decisions]]). A gap analysis that lists closed gaps is worse than none |
| E4 | **Record the verdict for `b9a107049e52`** | queue integrity | S | Bull vs Bear Debate was marked `backtested` with an **empty note**. Its conclusion was never written down, so it is unciteable — and the Grok-desk reel (`21ea6aeb17c5`) turned on exactly that precedent |
| E5 | **Pin `backtest-api/requirements.txt`** | build reproducibility | S | Unpinned deps mean a rebuild can crash-loop the API. It already did: newer SQLAlchemy resolved bare `postgresql://` to psycopg v3, which the image does not ship. Patched the URL; root cause untouched |

## Decided against

- **A separate "engine projects" repo.** An engine capability is a feature of
  the studio, not a sibling product. A second codebase means two deploys and a
  seam where any new sleeve has to talk back to the champion registry anyway.

## Sizing

`S` — an evening · `M` — a weekend · `L` — a multi-week project with design up front.

Related: [[Home]] · [[Strategy Ideas]] · [[Strategy Studio System]] · [[Decisions]]
