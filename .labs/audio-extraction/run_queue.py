#!/usr/bin/env python3
"""Process the strategy research queue (sources.yaml) through the pipeline.

Each source in sources.yaml with the target status is run end-to-end
(extract -> interpret -> generate -> data -> backtest -> report). On success
the source's `cache_key` is recorded and its status flips to `backtested`,
so it won't be reprocessed on the next run.

Usage:
    python run_queue.py                 # process every `pending` source
    python run_queue.py --status error  # retry sources that previously errored
    python run_queue.py --dry-run       # show what would run, change nothing
"""

import argparse
from pathlib import Path

import yaml

from pipeline import run_pipeline
from stages.extract import url_to_cache_key

ROOT = Path(__file__).parent
QUEUE = ROOT / "sources.yaml"


def load_queue():
    data = yaml.safe_load(QUEUE.read_text(encoding="utf-8")) or {}
    return data, data.get("sources") or []


def save_queue(data):
    QUEUE.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--status", default="pending", help="process sources with this status (default: pending)")
    ap.add_argument("--model", default="base", help="Whisper model: tiny, base, small, medium, large")
    ap.add_argument("--dry-run", action="store_true", help="list sources without running them")
    args = ap.parse_args()

    data, sources = load_queue()
    todo = [s for s in sources if s.get("status") == args.status and s.get("url")]

    if not todo:
        print(f"No sources with status '{args.status}'. Nothing to do.")
        return

    print(f"{len(todo)} source(s) with status '{args.status}':")
    for s in todo:
        print(f"  - {s.get('name') or s['url']}")

    for s in todo:
        url = s["url"]
        print(f"\n{'#' * 70}\n# {s.get('name') or url}\n{'#' * 70}")
        if args.dry_run:
            print("  [dry-run] would process")
            continue
        try:
            run_pipeline(url, args.model)
            s["cache_key"] = url_to_cache_key(url)
            s["status"] = "backtested"
            s.pop("error", None)
        except Exception as e:  # keep the queue moving on a single failure
            print(f"  ERROR: {e}")
            s["status"] = "error"
            s["error"] = str(e)[:200]
        save_queue(data)  # persist after each source so progress survives a crash

    print("\nQueue run complete.")


if __name__ == "__main__":
    main()
