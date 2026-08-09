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
import io
from pathlib import Path

from ruamel.yaml import YAML

from pipeline import run_pipeline
from stages.extract import url_to_cache_key

ROOT = Path(__file__).parent
QUEUE = ROOT / "sources.yaml"

# Round-trip YAML, not safe_load/safe_dump: writing status and cache_key back
# rewrites the whole file, and safe_dump would have erased the queue's header
# docs and the "add new sources below" marker on the first successful run.
_yaml = YAML()
_yaml.preserve_quotes = True
_yaml.width = 80                                # match the file's existing wrap
_yaml.indent(mapping=2, sequence=4, offset=2)   # "  - url:" / "    name:"


# The order fields appear in within a source entry. `error` sits next to the
# `status` it explains, and both written-back fields stay ahead of the long
# free-text ones so neither ends up as an entry's last key (see set_field).
FIELD_ORDER = ["url", "name", "status", "error", "cache_key", "tags", "note"]


def load_queue():
    data = _yaml.load(QUEUE.read_text(encoding="utf-8")) or {}
    return data, data.get("sources") or []


def set_field(source, key, value):
    """Set a field on a source entry, keeping FIELD_ORDER.

    Plain assignment appends a *new* key to the end of the mapping, and ruamel
    anchors the queue's trailing comments to the last key of the last source —
    so an appended cache_key lands underneath the "add new sources below"
    marker, where the next person to add a source would corrupt the file.
    """
    if key in source:
        source[key] = value
        return
    rank = {name: i for i, name in enumerate(FIELD_ORDER)}
    last = len(FIELD_ORDER)
    target = rank.get(key, last)
    pos = next(
        (i for i, existing in enumerate(source) if rank.get(existing, last) > target),
        len(source),
    )
    # Belt and braces for an entry whose fields are all ranked ahead of this
    # one: appending would still put the new key where the comments are, so
    # slot it in one position earlier instead.
    if pos == len(source) and len(source) > 1 and _carries_trailing_comment(source):
        pos -= 1
    source.insert(pos, key, value)


def _carries_trailing_comment(source) -> bool:
    """True if ruamel has parked a comment block on this entry's last key."""
    keys = list(source)
    return bool(keys) and getattr(source, "ca", None) and source.ca.items.get(keys[-1])


def save_queue(data):
    buf = io.StringIO()
    _yaml.dump(data, buf)
    # ruamel marks each fold point of a wrapped plain scalar with a trailing
    # space. It parses back identically, but it dirties every diff, so strip it.
    QUEUE.write_text(
        "".join(line.rstrip() + "\n" for line in buf.getvalue().splitlines()),
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
            set_field(s, "cache_key", url_to_cache_key(url))
            set_field(s, "status", "backtested")
            s.pop("error", None)
        except Exception as e:  # keep the queue moving on a single failure
            print(f"  ERROR: {e}")
            set_field(s, "status", "error")
            set_field(s, "error", str(e)[:200])
        save_queue(data)  # persist after each source so progress survives a crash

    print("\nQueue run complete.")


if __name__ == "__main__":
    main()
