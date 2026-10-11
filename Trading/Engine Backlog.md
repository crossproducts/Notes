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
| E6b | **Bracket orders: stop-entry + stop-loss + R-multiple target, resolved intrabar** | any reel that specifies entries the way traders actually say them | M | Hit this live on `DeUGFf4yLX8`: the rules were fully mechanical and on daily bars, but `fn(df,params) -> 0/1` cannot express a fill, a stop and a target *inside* one bar, so it needed a bespoke harness (`research/ema_pullback_check.py`) instead of a registry entry. Daily OHLC is enough if the ambiguous-bar convention is pessimistic and stated. Smaller than E2 - no new data, only path-dependent fills |
| E8 | **Audit the 11 `backtested` queue entries** | queue integrity | M | `validate_queue.py` found E4 was not a one-off. Three more entries carry `status: backtested` with an **empty note**, and **four** generated backtests **never reference the engine and contain no cost model** — same failure, unexamined: `0d87f719dc0c` Multi-Factor AI Analyst, `21fdab62deae` AI Infra Rotation, `748f15d07e9c` Congressional Copycat, `dde48fadcf1d` Asian Range Breakout. Each needs opening, re-scoring through the engine or re-marking. The validator exits 1 until they are resolved, which is the point |

## Done

- **E5 — pin `backtest-api/requirements.txt`** *(closed 2026-10-11)*
  Pinned all 44 packages by freezing the image that was verified working,
  10 direct and 34 transitive. Unpinned deps here were never a style
  question: a rebuild once resolved a newer SQLAlchemy that maps bare
  `postgresql://` onto psycopg v3, which the image does not ship, and the
  API crash-looped. That was patched at the URL; this is the root cause.
  Rebuilt and redeployed against the pins — pandas 3.0.6, numpy 2.4.6,
  SQLAlchemy 2.1.3, FastAPI 0.142.2.

- **E7 — trials-aware scoring (deflated sharpe)** *(shipped 2026-10-11)*
  `analysis.annotate_deflated` charges every ranking for its own size:
  Bailey & López de Prado's expected-max-sharpe under the null, then a
  probabilistic sharpe against it, corrected for sample length, skew and
  kurtosis. No scipy in the image, so the normal CDF/inverse are written out
  (Acklam, |err| < 1.2e-9); validated against known quantiles and against the
  brute-force simulation (analytic 0.368 vs simulated 0.36 at N=20).
  Live on `/champion/evaluate/{symbol}`. **The answer is uncomfortable:**
  with 16 strategies ranked, the best of that many ZERO-EDGE candidates would
  score **0.417**, and the champion scores **0.44** — a **deflated sharpe of
  0.55**, barely better than a coin flip, where 0.95 is the usual bar.
  Nothing in the registry clears it. The fat tails matter: kurtosis runs 7.7
  to 56.8 and skew is negative almost everywhere, both cutting confidence.
  `auto_promote(min_dsr=...)` can gate on it but defaults to OFF — switching
  it on today leaves the book with no champion at all, which is a decision to
  take deliberately, not a pipeline to break by surprise.

- **E4 — record the verdict for `b9a107049e52`** *(closed 2026-10-11)*
  Bull vs Bear Debate was marked `backtested` with an empty note. It should
  never have carried that status. The six LLM agents in the interpreted
  config do not appear in the generated backtest at all — the bull agent is
  six hand-set TA conditions, the bear agent six more, the debate a 0.15
  margin. The script also bypasses the engine entirely (own data fetch, own
  weekly top-5 rebalance, hardcoded 2020 start) and models **zero
  transaction costs** on ~104 turnovers a year.
  Re-marked `skipped`. The finding is about the pipeline, not the strategy:
  **an LLM layer cannot be backtested, so the generator quietly substitutes
  numeric proxies and we end up measuring something else.** Any future
  agent-framework reel (TradingAgents, `391cb4883ce9`) inherits this verdict.

- **E6 — champion selection is window-dependent** *(resolved 2026-10-11)*
  Confirmed and fixed. `momentum` scored sharpe **0.95** on a 2020 start and
  **0.23** on 2000+ — a 0.72 spread, the worst of any real strategy, and it
  failed to beat buy-and-hold on two of three windows.
  **New rule**, in `analysis.robust_score` / `rank_robust` and wired into
  `/champion/auto`: score every strategy over windows spanning >=2 bear markets
  (2000 / 2007 / 2020), rank on the **worst** window, and require it to beat
  buy-and-hold in **every** window. New endpoint `/champion/evaluate/{symbol}`
  exposes the ranking. The walk-forward gate also moved from a hardcoded
  `2018-01-01` (one bear market) to the full-cycle window.
  **Result: `triple_momentum` took the belt** (worst-window 0.44, spread 0.29,
  beats B&H in all three) from `momentum` (0.23, spread 0.72).
  Two traps fixed on the way: `DATA_FLOOR` stops `vix_gold_filter` and
  `rotation_top_k` being scored before GLD/EEM existed (they silently become
  buy-and-hold on NaN comparisons and look excellent); and promotion now picks
  the **longest-history run** of the winning strategy, not the highest-sharpe
  one, which would have re-introduced the same bias at the run level.

## Decided against

- **A separate "engine projects" repo.** An engine capability is a feature of
  the studio, not a sibling product. A second codebase means two deploys and a
  seam where any new sleeve has to talk back to the champion registry anyway.

## Sizing

`S` — an evening · `M` — a weekend · `L` — a multi-week project with design up front.

Related: [[Home]] · [[Strategy Ideas]] · [[Strategy Studio System]] · [[Decisions]]
