#!/usr/bin/env python3
"""Validate sources.yaml -- the research queue's integrity gate.

Written because of E4. `b9a107049e52` sat in the queue marked `backtested`
with an empty note for weeks. Opening it showed the status was simply false:
the generated script had its six LLM "agents" replaced by hand-set technical
conditions, never touched the engine, and modelled zero transaction costs. It
had RUN. It had not been TESTED. Nothing in the pipeline could tell those apart.

These checks make that distinction mechanical:

  E1  status must be one of the four known values
  E2  `backtested` requires a non-empty note -- a verdict nobody wrote down is
      a verdict nobody can cite, and the entry is unciteable in exactly the way
      E4 was
  E3  `backtested` requires a cache_key
  E4  cache_key must have artifacts on disk
  E5  no duplicate URLs or cache_keys
  W1  a `backtested` entry whose generated backtest never references the engine
      -- the E4 root cause, where a strategy is measured by its own bespoke
      loop instead of the one with the cost model and the gates
  W2  a generated backtest with no cost model at all

    python validate_queue.py            # report, exit 1 on any error
    python validate_queue.py --strict   # warnings are errors too

Exits non-zero on failure so it can sit in a pre-commit hook or CI.
"""

import argparse
import io
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pyyaml required -- pip install pyyaml")

HERE = Path(__file__).parent
SOURCES = HERE / "sources.yaml"
CACHE = HERE / "cache"
VALID_STATUS = {"pending", "backtested", "error", "skipped"}

# A generated backtest that references any of these is at least talking to the
# shared engine rather than rolling its own loop.
ENGINE_MARKERS = ("equity_from_signal", "import engine", "from engine",
                  "engine.fetch", "engine.metrics")
COST_MARKERS = ("cost_bps", "commission", "slippage", "bps", "transaction_cost")


def check(sources):
    errors, warnings = [], []
    seen_urls, seen_keys = {}, {}

    for i, s in enumerate(sources):
        where = f"[{i}] {s.get('name') or s.get('url') or '<unnamed>'}"
        status = s.get("status")
        note = (s.get("note") or "").strip()
        key = s.get("cache_key")
        url = (s.get("url") or "").split("?")[0].rstrip("/")

        if status not in VALID_STATUS:
            errors.append(f"E1 {where}: status {status!r} not in {sorted(VALID_STATUS)}")

        if status == "backtested":
            if not note:
                errors.append(
                    f"E2 {where}: status=backtested with an EMPTY note. Record what "
                    f"the backtest concluded, or the entry is unciteable (see E4).")
            if not key:
                errors.append(f"E3 {where}: status=backtested with no cache_key")

        if key:
            if not list(CACHE.glob(f"{key}*")):
                errors.append(f"E4 {where}: cache_key {key} has no artifacts in cache/")
            if key in seen_keys:
                errors.append(f"E5 {where}: cache_key {key} also used by {seen_keys[key]}")
            seen_keys[key] = where

        if url:
            if url in seen_urls:
                errors.append(f"E5 {where}: duplicate url, also at {seen_urls[url]}")
            seen_urls[url] = where

        # --- the E4 root cause -------------------------------------------
        if status == "backtested" and key:
            bt = CACHE / f"{key}_backtest.py"
            if bt.exists():
                src = io.open(bt, encoding="utf-8", errors="replace").read()
                if not any(m in src for m in ENGINE_MARKERS):
                    warnings.append(
                        f"W1 {where}: {bt.name} never references the engine. A "
                        f"bespoke loop skips the cost model, the robust windows "
                        f"and the walk-forward gate -- the exact E4 failure.")
                low = src.lower()
                if not any(re.search(rf"\b{m}\b", low) for m in COST_MARKERS):
                    warnings.append(
                        f"W2 {where}: {bt.name} contains no cost model. Gross "
                        f"results have been wrong by ~100pp in this repo.")
    return errors, warnings


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args()

    try:
        data = yaml.safe_load(io.open(SOURCES, encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        sys.exit(f"E0 sources.yaml does not parse: {str(e)[:300]}")
    sources = data.get("sources") or []

    errors, warnings = check(sources)
    counts = {}
    for s in sources:
        counts[s.get("status")] = counts.get(s.get("status"), 0) + 1

    print(f"sources.yaml: {len(sources)} entries {counts}")
    for w in warnings:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  ERROR {e}")
    if not errors and not warnings:
        print("  all checks pass")

    if errors or (args.strict and warnings):
        sys.exit(1)


if __name__ == "__main__":
    main()
