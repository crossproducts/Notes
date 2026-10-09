#!/usr/bin/env python3
"""
gen_diagrams.py - render every Architecture-AWS diagram as a .drawio.svg.

Each output file is two things at once:

  * a plain SVG that GitHub renders inline in the markdown doc, and
  * a draw.io document (the mxGraph XML lives in the root <svg content="...">
    attribute), so the same file opens editable in the drawio VS Code extension.

Specs live in specs/cat*.py as SPECS dicts. Layout is a grid: you give each node
a (col, row) and the generator does the geometry, routing, arrowheads and legend.

    python Architecture-AWS/_generator/gen_diagrams.py            # all
    python Architecture-AWS/_generator/gen_diagrams.py aws-048    # one
"""

import glob
import html
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "diagrams")

# --- visual language (matches Architecture/Diagrams/drawio-plugins/notes-arch.js) ---
KIND = {
    "edge":    ("#E8EEF9", "#2F5BB7"),  # clients, gateways, CDN, DNS
    "compute": ("#E7F3EA", "#2E7D4F"),  # lambda, ecs, eks, ec2
    "data":    ("#FBF0DC", "#A8741A"),  # s3, dynamodb, rds, redshift
    "async":   ("#F3E9F7", "#7B3FA0"),  # sqs, sns, eventbridge, kinesis
    "ai":      ("#E9F2F6", "#1F7A8C"),  # bedrock, sagemaker, vectors
    "ops":     ("#F0F0F3", "#5A5A66"),  # cloudwatch, config, ssm
    "sec":     ("#FDECEA", "#C0392B"),  # iam, kms, guardduty, waf
    "ext":     ("#FFFFFF", "#8A8A94"),  # off-AWS systems, humans, SaaS
}

EDGE_KIND = {
    "sync":  ("#2F5BB7", "none", 1.6),
    "async": ("#7B3FA0", "6 4", 1.6),
    "data":  ("#A8741A", "none", 1.6),
    "tele":  ("#5A5A66", "2 3", 1.3),
    "sec":   ("#C0392B", "4 3", 1.6),
}

NW, NH = 170, 64          # node box
CW, CH = 272, 132         # grid pitch
PAD_X, PAD_Y = 34, 74     # canvas margin (top leaves room for title + zone label)
ZPAD = 22                 # zone padding around its grid span
LEGEND_H = 30


# ---------------------------------------------------------------- geometry --
def nx(col):
    return PAD_X + col * CW


def ny(row):
    return PAD_Y + row * CH


def wrap(text, limit):
    """Greedy word wrap; AWS service names are long, so allow a hard split."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) <= limit:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            while len(w) > limit:
                lines.append(w[: limit - 1] + "-")
                w = w[limit - 1 :]
            cur = w
    if cur:
        lines.append(cur)
    return lines[:3]


# ------------------------------------------------------------------- model --
class Diag:
    def __init__(self, spec, key):
        self.key = key
        self.spec = spec
        self.nodes = {}
        for n in spec["nodes"]:
            nid, label, kind, col, row = n[0], n[1], n[2], n[3], n[4]
            sub = n[5] if len(n) > 5 else None
            self.nodes[nid] = dict(
                id=nid, label=label, kind=kind, col=col, row=row, sub=sub,
                x=nx(col), y=ny(row),
            )
        self.zones = spec.get("zones", [])
        self.edges = spec.get("edges", [])

        maxcol = max(n["col"] for n in self.nodes.values())
        maxrow = max(n["row"] for n in self.nodes.values())
        for z in self.zones:
            maxcol = max(maxcol, z["cols"][1])
            maxrow = max(maxrow, z["rows"][1])
        self.w = nx(maxcol) + NW + PAD_X
        self.h = ny(maxrow) + NH + PAD_Y + LEGEND_H

    def zone_rect(self, z):
        c0, c1 = z["cols"]
        r0, r1 = z["rows"]
        x = nx(c0) - ZPAD
        y = ny(r0) - ZPAD - 8
        return x, y, (nx(c1) + NW + ZPAD) - x, (ny(r1) + NH + ZPAD) - y

    def route(self, src, dst):
        """Orthogonal path + the arrowhead's incoming direction."""
        a, b = self.nodes[src], self.nodes[dst]
        dx, dy = b["col"] - a["col"], b["row"] - a["row"]
        ay, by = a["y"] + NH / 2, b["y"] + NH / 2

        if dx > 0:
            x1, x2 = a["x"] + NW, b["x"]
            if dy == 0:
                return f"M {x1} {ay} H {x2}", (x2, ay), "right", ((x1 + x2) / 2, ay)
            xm = (x1 + x2) / 2
            return (f"M {x1} {ay} H {xm} V {by} H {x2}", (x2, by), "right", (xm, (ay + by) / 2))
        if dx < 0:
            x1, x2 = a["x"], b["x"] + NW
            if dy == 0:
                return f"M {x1} {ay} H {x2}", (x2, ay), "left", ((x1 + x2) / 2, ay)
            xm = (x1 + x2) / 2
            return (f"M {x1} {ay} H {xm} V {by} H {x2}", (x2, by), "left", (xm, (ay + by) / 2))

        cx = a["x"] + NW / 2
        if dy > 0:
            y1, y2 = a["y"] + NH, b["y"]
            return f"M {cx} {y1} V {y2}", (cx, y2), "down", (cx, (y1 + y2) / 2)
        y1, y2 = a["y"], b["y"] + NH
        return f"M {cx} {y1} V {y2}", (cx, y2), "up", (cx, (y1 + y2) / 2)


# --------------------------------------------------------------- svg output --
def arrowhead(pt, direction, color):
    x, y = pt
    s = 6.0
    if direction == "right":
        p = f"{x},{y} {x-s*1.5},{y-s*0.72} {x-s*1.5},{y+s*0.72}"
    elif direction == "left":
        p = f"{x},{y} {x+s*1.5},{y-s*0.72} {x+s*1.5},{y+s*0.72}"
    elif direction == "down":
        p = f"{x},{y} {x-s*0.72},{y-s*1.5} {x+s*0.72},{y-s*1.5}"
    else:
        p = f"{x},{y} {x-s*0.72},{y+s*1.5} {x+s*0.72},{y+s*1.5}"
    return f'<polygon points="{p}" fill="{color}"/>'


def esc(t):
    return html.escape(str(t), quote=False)


def render_svg(d):
    s = d.spec
    o = []
    o.append(f'<rect width="{d.w}" height="{d.h}" fill="#FFFFFF"/>')

    o.append(
        f'<text x="{PAD_X}" y="26" font-family="Segoe UI,Helvetica,Arial,sans-serif" '
        f'font-size="15" font-weight="600" fill="#1A1A1A">{esc(d.key.upper())} &#183; '
        f'{esc(s["title"])}</text>'
    )

    for z in d.zones:
        x, y, w, h = d.zone_rect(z)
        stroke = z.get("color", "#9AA0AC")
        dash = z.get("dash", "7 5")
        o.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="none" '
            f'stroke="{stroke}" stroke-width="1.4" stroke-dasharray="{dash}"/>'
        )
        o.append(
            f'<text x="{x+12}" y="{y+18}" font-family="Segoe UI,Helvetica,Arial,sans-serif" '
            f'font-size="11" font-weight="600" fill="{stroke}">{esc(z["label"])}</text>'
        )

    used = set()
    heads = []   # drawn last so a label box never hides an arrowhead
    labels = []  # drawn after every path so no crossing edge overpaints a label
    for e in d.edges:
        src, dst, label = e[0], e[1], e[2]
        ek = e[3] if len(e) > 3 else "sync"
        used.add(ek)
        color, dash, wdt = EDGE_KIND[ek]
        path, end, direction, mid = d.route(src, dst)
        da = f' stroke-dasharray="{dash}"' if dash != "none" else ""
        o.append(
            f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{wdt}"{da}/>'
        )
        heads.append(arrowhead(end, direction, color))
        if label:
            mx_, my_ = mid
            tw = len(label) * 5.3 + 8
            labels.append(
                f'<rect x="{mx_-tw/2:.1f}" y="{my_-8}" width="{tw:.1f}" height="14" rx="3" '
                f'fill="#FFFFFF"/>'
                f'<text x="{mx_:.1f}" y="{my_+3}" text-anchor="middle" '
                f'font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="9.5" '
                f'fill="{color}">{esc(label)}</text>'
            )
    # every path is drawn before any label, and arrowheads last, so a crossing
    # edge can never be painted over a label it does not belong to
    o.extend(labels)
    o.extend(heads)

    for n in d.nodes.values():
        fill, stroke = KIND[n["kind"]]
        o.append(
            f'<rect x="{n["x"]}" y="{n["y"]}" width="{NW}" height="{NH}" rx="7" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
        )
        lines = wrap(n["label"], 24)
        has_sub = bool(n["sub"])
        total = len(lines) + (1 if has_sub else 0)
        y0 = n["y"] + NH / 2 - (total - 1) * 7 + 4
        for i, ln in enumerate(lines):
            o.append(
                f'<text x="{n["x"]+NW/2}" y="{y0+i*14:.0f}" text-anchor="middle" '
                f'font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="12" '
                f'fill="#1A1A1A">{esc(ln)}</text>'
            )
        if has_sub:
            o.append(
                f'<text x="{n["x"]+NW/2}" y="{y0+len(lines)*14:.0f}" text-anchor="middle" '
                f'font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="9.5" '
                f'fill="{stroke}">{esc(n["sub"])}</text>'
            )

    ly = d.h - 14
    lx = PAD_X
    order = [k for k in ("sync", "async", "data", "tele", "sec") if k in used]
    names = {"sync": "sync", "async": "async / event", "data": "bulk data",
             "tele": "telemetry", "sec": "security control"}
    for k in order:
        color, dash, _ = EDGE_KIND[k]
        da = f' stroke-dasharray="{dash}"' if dash != "none" else ""
        o.append(f'<path d="M {lx} {ly-4} H {lx+22}" stroke="{color}" stroke-width="1.6"{da}/>')
        o.append(
            f'<text x="{lx+28}" y="{ly}" font-family="Segoe UI,Helvetica,Arial,sans-serif" '
            f'font-size="10" fill="#5A5A66">{esc(names[k])}</text>'
        )
        lx += 34 + len(names[k]) * 5.8 + 18
    return "\n".join(o)


# ------------------------------------------------------------ drawio output --
def mx_style(kind):
    fill, stroke = KIND[kind]
    return (
        "rounded=1;arcSize=8;whiteSpace=wrap;html=1;fontSize=12;fontColor=#1A1A1A;"
        f"strokeWidth=1.5;fillColor={fill};strokeColor={stroke};"
    )


def mx_edge_style(ek):
    color, dash, wdt = EDGE_KIND[ek]
    st = (
        "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;fontSize=11;"
        f"strokeColor={color};strokeWidth={wdt};endArrow=blockThin;endFill=1;"
    )
    if dash != "none":
        st += f"dashed=1;dashPattern={dash};"
    return st


def render_mxfile(d):
    c = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    n = 2

    for z in d.zones:
        x, y, w, h = d.zone_rect(z)
        stroke = z.get("color", "#9AA0AC")
        st = (
            "rounded=1;arcSize=6;whiteSpace=wrap;html=1;container=1;collapsible=0;"
            "verticalAlign=top;align=left;spacingLeft=10;spacingTop=4;fillColor=none;"
            f"strokeColor={stroke};fontColor={stroke};fontSize=11;fontStyle=1;"
            f"dashed=1;dashPattern={z.get('dash','7 5').replace(' ',' ')};strokeWidth=1.4;"
        )
        c.append(
            f'<mxCell id="z{n}" value="{html.escape(z["label"])}" style="{html.escape(st)}" '
            f'vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" '
            f'as="geometry"/></mxCell>'
        )
        n += 1

    for node in d.nodes.values():
        val = node["label"]
        if node["sub"]:
            val += f'<br><font style="font-size:9.5px">{node["sub"]}</font>'
        c.append(
            f'<mxCell id="{node["id"]}" value="{html.escape(val)}" '
            f'style="{html.escape(mx_style(node["kind"]))}" vertex="1" parent="1">'
            f'<mxGeometry x="{node["x"]}" y="{node["y"]}" width="{NW}" height="{NH}" '
            f'as="geometry"/></mxCell>'
        )

    for e in d.edges:
        src, dst, label = e[0], e[1], e[2]
        ek = e[3] if len(e) > 3 else "sync"
        c.append(
            f'<mxCell id="e{n}" value="{html.escape(label or "")}" '
            f'style="{html.escape(mx_edge_style(ek))}" edge="1" parent="1" '
            f'source="{src}" target="{dst}"><mxGeometry relative="1" as="geometry"/></mxCell>'
        )
        n += 1

    body = "".join(c)
    return (
        f'<mxfile host="vscode" agent="gen_diagrams.py" version="21.0.0">'
        f'<diagram id="{d.key}" name="{html.escape(d.spec["title"])}">'
        f'<mxGraphModel dx="1100" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" '
        f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" '
        f'pageHeight="826" math="0" shadow="0"><root>{body}</root></mxGraphModel>'
        f"</diagram></mxfile>"
    )


def build(key, spec):
    d = Diag(spec, key)
    content = html.escape(render_mxfile(d), quote=True)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{d.w}" height="{d.h}" viewBox="0 0 {d.w} {d.h}" '
        f'content="{content}">\n{render_svg(d)}\n</svg>\n'
    )
    path = os.path.join(OUT, f"{key}.drawio.svg")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    return path


def load_specs():
    specs = {}
    for f in sorted(glob.glob(os.path.join(HERE, "specs", "cat*.py"))):
        name = os.path.splitext(os.path.basename(f))[0]
        sp = importlib.util.spec_from_file_location(name, f)
        mod = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(mod)
        for k, v in mod.SPECS.items():
            if k in specs:
                raise SystemExit(f"duplicate spec key {k} in {f}")
            specs[k] = v
    return specs


def main():
    os.makedirs(OUT, exist_ok=True)
    specs = load_specs()
    only = sys.argv[1:]
    built = 0
    for key in sorted(specs):
        if only and key not in only:
            continue
        build(key, specs[key])
        built += 1
    print(f"built {built} diagram(s) into {OUT}  (specs loaded: {len(specs)})")


if __name__ == "__main__":
    main()
