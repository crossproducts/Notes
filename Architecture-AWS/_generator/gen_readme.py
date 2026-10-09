#!/usr/bin/env python3
"""
gen_readme.py - build Architecture-AWS/readme.md from manifest.py.

The index is generated so its links can never drift from the files on disk. A
missing doc or diagram shows up as a TODO marker in the table rather than a
broken link, so the readme is always an honest status board.

    python Architecture-AWS/_generator/gen_readme.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from manifest import ARCHS, CATEGORIES, by_category, check, filename  # noqa: E402

# Reading paths: a named goal -> the architectures to read in order.
PATHS = [
    ("Ship a web app on AWS", ["aws-028", "aws-010", "aws-002", "aws-003", "aws-066", "aws-094"]),
    ("Expose an API to the outside world", ["aws-001", "aws-005", "aws-009", "aws-008", "aws-063"]),
    ("Run containers without regret", ["aws-019", "aws-020", "aws-022", "aws-021", "aws-025"]),
    ("Build a data platform", ["aws-037", "aws-041", "aws-038", "aws-044", "aws-046", "aws-045"]),
    ("Go real-time", ["aws-051", "aws-047", "aws-050", "aws-048"]),
    ("Pass a security audit", ["aws-057", "aws-061", "aws-060", "aws-055", "aws-064"]),
    ("Stop being paged at 3am", ["aws-066", "aws-072", "aws-065", "aws-071", "aws-070"]),
    ("Put a model in production", ["aws-075", "aws-073", "aws-077", "aws-081"]),
    ("Survive losing a region", ["aws-087", "aws-085", "aws-086", "aws-083", "aws-084"]),
    ("Get the bill under control", ["aws-092", "aws-095", "aws-093", "aws-030", "aws-082"]),
]

HEADER = """# Architecture-AWS

101 AWS architectures, each one distinct, each written to be used rather than admired.

Every architecture gets its own page with a rendered diagram, a component table that
names *the setting that actually matters*, a request/data flow, cost at three scales,
failure modes, security notes, and a **"what people miss"** section — the detail that
turns a working design into one that survives contact with production.

## How to read this

| Field | Meaning |
|---|---|
| **Maturity** | `Production` — well-trodden, safe default · `Growing` — solid but evolving fast · `Specialist` — right for a narrow problem, wrong as a default |
| **Effort** | `S` — days · `M` — weeks · `L` — a quarter or more, usually with more than one team |
| **Cost** | `us-east-1`, on-demand, no commitments, priced at three scales so the *shape* of the curve is visible. Treat as an order of magnitude, not a quote. |

Diagrams are `.drawio.svg` files: GitHub renders them inline, and the same file opens
as an editable diagram in the draw.io VS Code extension. See
[the plugin notes](../Architecture/Diagrams/drawio-plugin.md).

### The visual language

Colour means *type of thing*, line style means *type of relationship* — consistent
across all 101 diagrams.

| Colour | Meaning | | Line | Meaning |
|---|---|---|---|---|
| 🔵 blue | edge, gateway, CDN, DNS | | solid blue | synchronous call |
| 🟢 green | compute | | dashed purple | async / event |
| 🟠 amber | storage and databases | | solid amber | bulk data movement |
| 🟣 purple | queues, topics, streams | | dotted grey | telemetry |
| 🔷 teal | AI/ML | | dashed red | security control |
| ⚪ grey | observability and ops | | | |
| 🔴 red | security services | | | |
| ⬜ white | systems outside AWS | | | |

## Reading paths

Rather than reading 101 pages in order, follow the one that matches what you are
actually doing.
"""

FOOTER = """
## On non-overlap

These 101 are deliberately disjoint. Where two architectures touch the same service
they do so from different angles — `aws-001` is about *authorising* a request at the
gateway, `aws-005` about *surviving* too many of them, `aws-009` about *changing* what
is behind it, and `aws-006` about never exposing it publicly at all. Where one
architecture is a prerequisite for another, the page says so under **See also**
instead of repeating it.

## Regenerating

```bash
python Architecture-AWS/_generator/manifest.py       # validate the 101
python Architecture-AWS/_generator/gen_diagrams.py   # rebuild every diagram
python Architecture-AWS/_generator/gen_readme.py     # rebuild this index
```

Add an architecture by appending to `manifest.py`, adding its diagram spec under
`_generator/specs/`, then writing the doc. The index picks it up automatically and
flags it as `TODO` until both the doc and the diagram exist.

## See also

- [Architecture/Reference-Architectures](../Architecture/Reference-Architectures/) — long-form blueprints
- [Architecture/ADRs](../Architecture/ADRs/) — decisions actually taken
- [Architecture/Tradeoff-Analysis](../Architecture/Tradeoff-Analysis/) — the comparisons behind them
- [.labs/AWS](../.labs/AWS/) — labs that provision some of these for real
"""


def main():
    check()
    cats = by_category()
    names = {c[0]: (c[1], c[2]) for c in CATEGORIES}

    out = [HEADER]

    for label, ids in PATHS:
        chain = " → ".join(f"[`{i}`]({filename(i)})" for i in ids)
        out.append(f"- **{label}** · {chain}")
    out.append("")

    out.append("## The 101\n")
    counts = " · ".join(f"[{names[c][0]}](#{c}) ({len(cats[c])})" for c in sorted(cats))
    out.append(f"{counts}\n")

    done = 0
    for cid in sorted(cats):
        cname, blurb = names[cid]
        anchor = f'<a id="{cid}"></a>'
        out.append(f"### {anchor}{cid} · {cname}\n")
        out.append(f"*{blurb}*\n")
        out.append("| ID | Architecture | What it gives you | Maturity | Effort |")
        out.append("|---|---|---|---|---|")
        for aid in cats[cid]:
            _, slug, title, line, maturity, effort = ARCHS[aid]
            fn = filename(aid)
            has_doc = os.path.exists(os.path.join(ROOT, fn))
            has_dia = os.path.exists(os.path.join(ROOT, "diagrams", f"{aid}.drawio.svg"))
            if has_doc:
                done += 1
                link = f"[{title}]({fn})"
            else:
                link = f"{title} <sub>`TODO`</sub>"
            if has_doc and not has_dia:
                link += " <sub>`no diagram`</sub>"
            out.append(
                f"| `{aid.split('-')[1]}` | {link} | {line} | {maturity} | {effort} |"
            )
        out.append("")

    out.append(f"> **Status:** {done} / {len(ARCHS)} pages written.\n")
    out.append(FOOTER)

    path = os.path.join(ROOT, "readme.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    print(f"wrote {path}  ({done}/{len(ARCHS)} docs present)")


if __name__ == "__main__":
    main()
