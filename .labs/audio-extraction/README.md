# Video → Strategy → Backtest Pipeline

Paste a trading-strategy video (Instagram reel, TikTok, YouTube) into the queue,
and the pipeline transcribes it, interprets the strategy, generates backtest
code, fetches market data, runs the backtest + parameter optimization, and
reports performance.

## Layout

```
audio-extraction/
├── sources.yaml        ← research queue: URLs you want backtested
├── run_queue.py        ← process every `pending` source in the queue
├── pipeline.py         ← run a single URL directly
├── stages/             ← the 6 pipeline stages
│   ├── extract.py        download full video (yt-dlp), extract audio (ffmpeg),
│   │                     capture frames (ffmpeg scene-detect / fixed-interval),
│   │                     transcribe (Whisper); Playwright fallback for gated sources
│   ├── interpret.py      transcript + video frames → strategy config (Claude vision)
│   ├── generate.py       strategy config → backtest code (Claude)
│   ├── data.py           historical market data (Alpaca)
│   ├── backtest.py       run backtest + param optimization
│   └── report.py         performance stats → output/*.json
├── cache/              ← per-source artifacts, keyed by cache_key
│   │                     includes {key}.mp4, {key}.mp3, {key}_frames/*.jpg
├── output/             ← saved report JSON
├── strategies/         ← curated strategies / standalone notebooks
└── notebooks/
    └── visualize.ipynb ← equity curve, drawdown, PnL dist, optimization heatmap
```

## Usage

**Queue-driven (recommended).** Add sources to `sources.yaml` as `pending`, then:

```bash
python run_queue.py            # process all pending sources
python run_queue.py --dry-run  # preview without running
```

**Studio-driven.** `python studio_worker.py` polls the Strategy Studio API for
URLs pasted into its `/ui` "Analyze Video" box, runs the pipeline on each, and
reports back; finished strategies show up in the studio as `video:<cache_key>`.

On success each source gets a `cache_key` and flips to `backtested`.

**One-off:**

```bash
python pipeline.py "https://www.instagram.com/reel/..."
```

**Visualize a result.** Open `notebooks/visualize.ipynb`, set `CACHE_KEY` to the
value from `sources.yaml`, and run all cells.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium     # only needed for the browser fallback
```

Set `ANTHROPIC_API_KEY`, `ALPACA_API_KEY`, and `ALPACA_SECRET_KEY` in `.env`.

## Notes

- **Backtest viz lives here, not in Alpaca's UI.** The Alpaca dashboard only
  shows orders submitted through their API; these backtests run offline against
  historical bars, so the notebook is the right place to inspect them. Alpaca's
  UI becomes relevant only if you graduate a strategy to paper trading.
- `extract.py` downloads the full video (`cache/{key}.mp4`) and derives audio
  from it via ffmpeg. It then extracts up to 10 JPEG frames using ffmpeg
  scene-change detection; if the video has a static camera (fewer than 3 scene
  cuts), it falls back to fixed-interval sampling with ffprobe for duration.
  Old cache entries that have only an mp3 still work — frame capture is skipped
  with a warning.
- `interpret.py` sends the frames alongside the transcript to Claude's vision
  model (`claude-sonnet-4-6`) so on-screen tickers, chart settings, and
  indicator values are captured even when the speaker does not mention them
  aloud. If no frames are available the call degrades to text-only.
- `extract.py` falls back to a headless browser (Playwright) when yt-dlp can't
  pull a source — e.g. login-walled Instagram reels. In that path it attempts a
  best-effort video save for frame capture, but never lets that block audio.
