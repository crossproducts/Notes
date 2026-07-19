# Strategy Studio System

What actually runs. Code: `.labs/strategy-studio/` (API, Grafana, compose) and
`.labs/audio-extraction/` (video → strategy pipeline).

## Services (docker compose)
| Service | Port | Purpose |
|---|---|---|
| backtest-api | 8001 | FastAPI: backtests, walk-forward, champions, paper trading, risk, scheduler |
| Postgres | 5433 | runs, equity curves, champions, paper audit log, risk state |
| Grafana | 3001 | equity/drawdown dashboards (auto-provisioned) |

## Automated schedule (in-API scheduler — n8n was removed 2026-07)
- **9:35 ET market days** — reconcile champion signal into Alpaca **paper** account, SMS result
- **18:00 ET weekdays** — nightly sweep per symbol → OOS-gated champion auto-promotion → SMS

## Safety properties
- `paper=True` is hardcoded in `paper.py` — going live is a human code change, never config
- Champion promotion requires a positive stitched out-of-sample walk-forward return
- All backtests include transaction costs by default (5 bps/side)
- Live risk layer: kill switch + max daily loss + position/exposure caps checked pre-trade
  (see `/risk/status`, `/risk/kill`)

## Video → strategy pipeline
Reel URL → yt-dlp/Playwright download → Whisper transcript **+ ffmpeg frame
capture** → Claude (text + vision) → strategy config → generated backtest →
report. Queue lives in `.labs/audio-extraction/sources.yaml`.

Related: [[Paper Trading Journal]] · [[Go-Live Checklist]] · [[Decisions]]
