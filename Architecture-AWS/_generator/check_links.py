#!/usr/bin/env python3
"""
check_links.py - verify every relative link and image in Architecture-AWS resolves.

Cross-references between the 101 pages are written by hand, so this is the guard
against a typo'd slug. Run it after adding or renaming anything.

    python Architecture-AWS/_generator/check_links.py
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from manifest import ARCHS, filename  # noqa: E402

LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def main():
    problems = []
    checked = 0

    for fn in sorted(os.listdir(ROOT)):
        if not fn.endswith(".md"):
            continue
        path = os.path.join(ROOT, fn)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for m in LINK.finditer(text):
            target = m.group(1).strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = target.split("#")[0]
            if not target:
                continue
            checked += 1
            resolved = os.path.normpath(os.path.join(ROOT, target))
            if not os.path.exists(resolved):
                line = text[: m.start()].count("\n") + 1
                problems.append(f"{fn}:{line}  ->  {target}")

    # every written doc should have its diagram
    for aid in sorted(ARCHS):
        doc = os.path.join(ROOT, filename(aid))
        dia = os.path.join(ROOT, "diagrams", f"{aid}.drawio.svg")
        if os.path.exists(doc) and not os.path.exists(dia):
            problems.append(f"{filename(aid)}  ->  MISSING DIAGRAM {aid}.drawio.svg")

    print(f"checked {checked} relative links across Architecture-AWS")
    if problems:
        print(f"\n{len(problems)} unresolved:\n")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("all links resolve")


if __name__ == "__main__":
    main()
