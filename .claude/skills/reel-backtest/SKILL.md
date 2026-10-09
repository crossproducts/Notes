---
name: reel-backtest
description: Turn a trading-strategy video (Instagram reel, TikTok, YouTube) into a backtest — transcribe it, interpret the strategy with Claude, generate backtest code, fetch market data, run the backtest + param optimization, and report performance. Use when the user drops a strategy video URL or wants to research/backtest a reel. Lives in .labs/audio-extraction/.
---

# Reel → Strategy → Backtest Pipeline

Standalone pipeline in `.labs/audio-extraction/`. Paste a strategy video URL and
it runs 6 stages: extract (yt-dlp/Whisper, Playwright fallback) → interpret
(Claude) → generate (Claude) → data (Alpaca) → backtest + optimization → report.

## Prerequisites
- `.env` in `.labs/audio-extraction/` holds `ANTHROPIC_API_KEY`,
  `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`. Gitignored — never print or commit it.
- One-time setup: `pip install -r requirements.txt`, and
  `playwright install chromium` (only for the browser fallback on login-walled reels).

Run everything from `.labs/audio-extraction/`.

## Queue-driven (recommended)
`sources.yaml` is the research queue. Each entry has a `status`
(`pending | backtested | error | skipped`) and gets a `cache_key` filled in
after a successful run.
```bash
python run_queue.py            # process every source with status: pending
python run_queue.py --dry-run  # list what would run, without running
python run_queue.py --status error --model small   # reprocess errored sources
```
Flags: `--status` (default `pending`), `--model` (Whisper: tiny/base/small/medium/large,
default `base`), `--dry-run`. On success a source flips to `backtested` and gets
a `cache_key`.

To add work: append an entry to `sources.yaml` with `url`, `name`,
`status: pending`, and optional `tags`, then run `run_queue.py`.

## One-off (bypasses the queue)
```bash
python pipeline.py "https://www.instagram.com/reel/..."   # positional URL
python pipeline.py "https://..." small                    # optional Whisper model (2nd positional arg)
```

## Research intake (agent-reach)

Sources no longer have to be pasted by hand.

```bash
python discover.py              # DRY RUN - what it would queue
python discover.py --write      # append it
```

Pulls the RSS feeds in `feeds.yaml`, keyword-filters, and routes:
YouTube links -> `sources.yaml` as `pending`; everything else ->
`Trading/Strategy Ideas.md` for triage. Dry-run by default.

**YouTube fast path:** for YouTube URLs the extract stage now pulls the
publisher's own captions via agent-reach and skips the audio download *and*
Whisper entirely. Falls back to download+Whisper when captions are missing.

**agent-reach is NOT an Instagram fallback** - its youtube channel drives the
same yt-dlp that is already login-walled there. Instagram still needs the
Playwright+ffmpeg path.

One-time setup (needs Python >=3.11; the pipeline is on 3.10, so it is called
through the CLI):

```bash
py -3.14 -m pip install agent-reach
py -3.14 -m agent_reach install rss youtube
py -3.14 -m agent_reach doctor
```

## Extraction fallback chain

`yt-dlp` -> `playwright` (sniffs DASH media URLs off the page) -> `ffmpeg`
(fetches them, demuxes audio, cuts frames) -> `whisper` (local transcript).
Two gotchas documented in the lab README: strip `bytestart`/`byteend` from
sniffed URLs, and rank Instagram's `/m78/` (audio) above `/m367/` (video-only).

## Inspect a result
Backtest viz lives in `notebooks/visualize.ipynb` — set `CACHE_KEY` to the value
from `sources.yaml`, run all cells (equity curve, drawdown, PnL dist,
optimization heatmap). Reports also land in `output/*.json`.

## Notes
- These backtests run **offline** against historical bars — they do **not**
  appear in the Alpaca dashboard, which only shows API-submitted orders. Alpaca's
  UI matters only if a strategy graduates to paper trading.
- `extract.py` falls back to headless Playwright when yt-dlp can't pull a source
  (e.g. login-walled Instagram reels).
- Interpret/generate stages call the Anthropic API and cost tokens; prefer
  `--dry-run` first when the queue is large.
