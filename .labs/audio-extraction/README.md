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


## How extraction actually works (3 layers)

Getting a transcript out of a social video is a fallback chain, not one tool.
Each layer exists because the one above it fails on a specific class of source.

```
                    URL
                     |
   [1] yt-dlp  -------+------>  works: public YouTube / TikTok
                     |          fails: login-walled Instagram reels
                     v
   [2] Playwright (headless Chromium)
                     |   loads the page, sniffs the network for media URLs
                     |   (Instagram serves DASH: audio and video are SEPARATE)
                     v
   [3] ffmpeg  -------+------>  fetches the sniffed URL -> .mp3 (audio)
                     |                                 -> .mp4 (video)
                     v
       Whisper (local) -> transcript.txt
       ffmpeg again    -> scene-detect frames -> vision
```

**What each does:**

| Layer | Tool | Job |
|---|---|---|
| 1 | `yt-dlp` | Direct download. One shot, no browser. |
| 2 | `playwright` + Chromium | Loads the real page so the player requests media, then sniffs those URLs off the network. This is what cracks login-walled reels. |
| 3 | `ffmpeg` | Fetches the sniffed CDN URL with the right `Referer`/UA, demuxes audio to mp3, copies video to mp4, and later cuts frames. |
| 4 | `whisper` (local) | Audio -> text. Runs on CPU, model cached in `~/.cache/whisper`. |

**Two non-obvious details that break it if you get them wrong:**

- **Byte-range params must be stripped.** The sniffed URLs carry
  `bytestart`/`byteend`, which hand ffmpeg a single segment instead of the whole
  file. `extract.py` strips them before fetching.
- **Instagram's audio track is served as `content-type: video/mp4`.** You tell
  them apart by path: `/m78/` is audio, `/m367/` is video-only. Without ranking
  on that, a reel with many video renditions burns the whole candidate budget on
  streams containing no audio and fails with *"Output file #0 does not contain
  any stream"*.

## Research intake (agent-reach)

`agent-reach` adds two channels. **It is not a third extraction fallback** --
its `youtube` channel drives the *same* yt-dlp that is already login-walled on
Instagram, and returns the identical error. It does two different jobs:

**1. YouTube fast path.** YouTube publishes its own captions, so for YT sources
the pipeline now skips the audio download *and* the Whisper pass entirely --
seconds instead of minutes, no 461 MB model load. Wired into `stages/extract.py`;
falls through to download+Whisper when a video has no captions.

**2. RSS discovery.** `discover.py` pulls the feeds in `feeds.yaml`, keyword-filters
them, and routes results the way the vault already splits things:

```bash
python discover.py              # DRY RUN - prints what it would add
python discover.py --write      # actually append
```

| Item type | Goes to | Why |
|---|---|---|
| YouTube link | `sources.yaml` as `pending` | the pipeline can transcribe + backtest it |
| anything else | `Trading/Strategy Ideas.md` inbox | needs human triage first |

Setup (one-time) -- note agent-reach needs **Python >= 3.11**, while the pipeline
runs on 3.10, so it is invoked through its CLI, not imported:

```bash
py -3.14 -m pip install agent-reach
py -3.14 -m agent_reach install rss
py -3.14 -m agent_reach install youtube
py -3.14 -m agent_reach doctor      # both should report ok
```

