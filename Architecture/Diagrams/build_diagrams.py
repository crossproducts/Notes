#!/usr/bin/env python3
"""Render the repo's own architecture diagrams as .drawio.svg.

Reuses the generator written for Architecture-AWS -- same grid layout, same
colour-as-type palette (Architecture/Diagrams/drawio-plugins/notes-arch.js), so
a repo diagram and an AWS reference diagram look like they belong together.

    python Architecture/Diagrams/build_diagrams.py

Layout is a grid: give each node a (col, row) and the generator does geometry,
orthogonal routing, arrowheads and the legend. The router draws straight H/V
runs and one H-V-H dogleg, so keep edges between NEIGHBOURING cells -- a long
sideways hop will be routed straight through whatever boxes sit in between.
"""

import importlib.util
import os
import pathlib
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))   # repo root (Notes/)
GEN = os.path.join(ROOT, "Architecture-AWS", "_generator", "gen_diagrams.py")

_spec = importlib.util.spec_from_file_location("gen_diagrams", GEN)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)

# --- the trading research pipeline ------------------------------------------
# Spans three labs: audio-extraction (intake + extraction + interpret),
# strategy-studio (engine, champion registry, live loop) and email-sender
# (the Gmail -> carrier-gateway bridge). Kept as ONE diagram because the
# interesting part is the seam between them.

SPECS = {
    "trading-pipeline": {
        "key_label": "NOTES",
        "title": "Trading research pipeline - reel to strategy to champion to phone",
        "zones": [
            {"label": "1 - Research intake (agent-reach + discover.py)",
             "cols": (0, 3), "rows": (0, 2), "color": "#2F5BB7"},
            {"label": "2 - Extraction (host, Python 3.10)",
             "cols": (0, 4), "rows": (3, 4), "color": "#2E7D4F"},
            {"label": "3 - Interpret to generate to backtest (Claude API + Alpaca)",
             "cols": (0, 4), "rows": (5, 5), "color": "#1F7A8C"},
            {"label": "4 - Strategy Studio (docker compose)",
             "cols": (0, 3), "rows": (6, 6), "color": "#A8741A"},
            {"label": "5 - Live loop (paper only)",
             "cols": (0, 2), "rows": (7, 8), "color": "#C0392B"},
            {"label": "6 - Notifications (email-sender lab)",
             "cols": (1, 4), "rows": (9, 10), "color": "#7B3FA0"},
        ],
        "nodes": [
            # --- 1. intake ---
            ("rss",     "agent-reach - rss",      "ext",     0, 0, "feedparser channel"),
            ("disc",    "discover.py",            "ops",     1, 0, "keyword filter, dry-run default"),
            ("ideas",   "Strategy Ideas.md",      "data",    2, 0, "human triage inbox"),
            ("igs",     "IG profile scan",        "edge",    0, 1, "Playwright, 6-post logged-out cap"),
            ("queue",   "sources.yaml",           "data",    1, 1, "queue + verdict per source"),
            ("paste",   "studio /ui, pipeline.py", "edge",   3, 1, "manual URL"),
            ("runq",    "run_queue.py",           "compute", 1, 2, "claims status: pending"),
            ("worker",  "studio_worker.py",       "compute", 2, 2, "polls studio, runs on host"),

            # --- 2. extraction ---
            ("aryt",    "agent-reach - youtube",  "ext",     0, 3, "published captions"),
            ("extract", "stages/extract.py",      "compute", 1, 3, "orchestrates the fallback"),
            ("ytdlp",   "yt-dlp",                 "compute", 0, 4, "public YouTube / TikTok"),
            ("pw",      "Playwright Chromium",    "compute", 1, 4, "sniffs DASH media URLs"),
            ("ffm",     "ffmpeg",                 "compute", 2, 4, "strip byte-range, demux, cut frames"),
            ("whis",    "Whisper (local)",        "ai",      3, 4, "CPU, model in ~/.cache"),
            ("cache",   "cache/{key}.*",          "data",    4, 4, "mp4, mp3, frames, transcript"),

            # --- 3. interpret -> backtest (runs right-to-left) ---
            ("interp",  "interpret.py",           "ai",      4, 5, "transcript + frames, vision"),
            ("gen",     "generate.py",            "ai",      3, 5, "config to backtest code"),
            ("dataf",   "stages/data.py",         "compute", 2, 5, "Alpaca historical bars"),
            ("bt",      "stages/backtest.py",     "compute", 1, 5, "+ parameter optimization"),
            ("rep",     "stages/report.py",       "data",    0, 5, "output/*.json"),

            # --- 4. studio ---
            ("studio",  "Strategy Studio API",    "compute", 0, 6, "FastAPI :8001, /champion/auto"),
            ("engine",  "engine.py + analysis.py", "compute", 1, 6, "yfinance, 5bps/side, robust_score"),
            ("pg",      "Postgres 16",            "data",    2, 6, "runs, equity_curve, champions"),
            ("graf",    "Grafana :3000",          "ops",     3, 6, "dashboards"),

            # --- 5. live loop ---
            ("sched",   "scheduler.py",           "async",   1, 7, "APScheduler cron + healthchecks.io"),
            ("mon",     "monitor.py",             "ops",     2, 7, "forward-decay vs own baseline"),
            ("paperm",  "paper.py",               "compute", 0, 8, "Alpaca PAPER, paper=True pinned"),
            ("riskm",   "risk.py",                "sec",     1, 8, "kill switch, loss + exposure caps"),

            # --- 6. notifications ---
            ("notify",  "POST /notify",           "async",   1, 9, "300-char SMS body"),
            ("smtp",    "Gmail SMTP :465",        "ext",     2, 9, "app password"),
            ("gw",      "carrier gateway",        "ext",     3, 9, "@tmomail.net"),
            ("phone",   "iPhone",                 "ext",     4, 9, "text + tappable voice note"),
            ("voice",   "send_voice.py",          "async",   1, 10, "edge-tts | SAPI, ffmpeg AAC mono"),
        ],
        "edges": [
            # 1. intake
            ("rss", "disc", "feed items", "data"),
            ("disc", "ideas", "everything else", "data"),
            ("disc", "queue", "YouTube links", "data"),
            ("igs", "queue", "reel shortcodes", "data"),
            ("queue", "runq", "status: pending", "sync"),
            ("paste", "worker", "URL", "sync"),

            # 2. extraction
            ("runq", "extract", "", "sync"),
            ("worker", "extract", "", "sync"),
            ("aryt", "extract", "captions", "data"),
            ("extract", "ytdlp", "1. try direct", "sync"),
            ("ytdlp", "pw", "2. login wall", "sync"),
            ("pw", "ffm", "3. sniffed URL", "sync"),
            ("ffm", "whis", "4. mp3", "data"),
            ("whis", "cache", "transcript", "data"),

            # 3. interpret -> backtest
            ("cache", "interp", "", "data"),
            ("interp", "gen", "strategy config", "sync"),
            ("gen", "dataf", "", "sync"),
            ("dataf", "bt", "bars", "data"),
            ("bt", "rep", "", "sync"),

            # 4. studio
            ("rep", "studio", "video:<key>", "data"),
            ("studio", "engine", "", "sync"),
            ("engine", "pg", "runs + curves", "data"),
            ("pg", "graf", "", "data"),

            # 5. live loop
            ("studio", "sched", "in-process cron", "async"),
            ("sched", "riskm", "09:35 execute", "async"),
            ("riskm", "paperm", "pre-trade check", "sec"),
            ("sched", "mon", "Fri 17:00", "async"),

            # 6. notifications
            ("paperm", "notify", "action taken", "async"),
            ("mon", "notify", "[DECAY]", "async"),
            ("notify", "smtp", "", "sync"),
            ("smtp", "gw", "", "sync"),
            ("gw", "phone", "SMS / MMS", "sync"),
            ("voice", "smtp", "m4a attachment", "data"),
        ],
    },
}


def export_png(svg_path, scale=2):
    """Also emit a .png beside the .drawio.svg.

    The SVG stays the source of truth -- it is what GitHub renders and what
    draw.io opens for editing. The PNG is for everywhere that will not render
    SVG: chat, slide decks, issue comments, some Markdown previewers.

    Rendered through the Playwright Chromium the extraction pipeline already
    installs, so there is no new dependency; if it is missing we say so and
    carry on rather than failing the build.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  (playwright not installed - skipped .png, SVG is unaffected)")
        return None
    out = svg_path[: -len(".drawio.svg")] + ".png"
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(device_scale_factor=scale)
        pg.goto(pathlib.Path(svg_path).resolve().as_uri())
        pg.wait_for_timeout(300)
        pg.query_selector("svg").screenshot(path=out)
        b.close()
    return out


def main():
    gen.OUT = HERE
    only = sys.argv[1:]
    for key in sorted(SPECS):
        if only and key not in only:
            continue
        svg = gen.build(key, SPECS[key])
        print("wrote", svg)
        png = export_png(svg)
        if png:
            print("wrote", png, f"({os.path.getsize(png) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
