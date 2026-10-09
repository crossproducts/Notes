# Strategy Ideas (inbox)

Capture → triage → `sources.yaml` (videos) or a built-in strategy sketch.
An idea graduates only by beating the champion out-of-sample.

## Queue
| Idea / URL | Source | Status | Notes |
|---|---|---|---|
| [Efficiency-Ratio forecast gate](https://www.instagram.com/reel/DeF5_5yPtDb/) | IG reel | **rejected** | ML gate on predicted next-day efficiency. Backtested 2026-10-06, `cache_key 114edfdb3d01`. OOS AUC 0.52-0.54 (noise); hurt 10/10 base-strategy/instrument combos. Arena rank 97/100 on SPY. |
|  |  | inbox |  |

## Alt-data backlog (from the studio roadmap)
- Congress copycat — must model the 30–45 day disclosure lag honestly
- 13F whale drift — quarterly, 45-day lag
- Overnight/close-to-open effects — less crowded per retail-edge research
- Sentiment feed — still needs a data source

## Not a strategy?

If an idea needs a capability the engine does not have (long/short,
intraday bars, cross-sectional ranking), it belongs in [[Engine Backlog]],
not here. Most academic sources land there.

## Triage rule
Ten minutes max per idea: is it testable with data we have (Alpaca/yfinance/EDGAR)?
If yes → queue it. If it needs paid data → park it here with the cost.

Related: [[Home]] · [[Strategy Studio System]]
