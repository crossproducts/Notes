#!/usr/bin/env python3
"""Research intake: pull RSS feeds via agent-reach, route new items for triage.

This closes the gap in the research loop. Until now a source only entered the
queue when someone pasted a link by hand; this finds candidates on a schedule.

Routing follows the architecture already in the vault:
    YouTube links   -> sources.yaml                  (the video queue)
    everything else -> Trading/Strategy Ideas.md     (the human triage inbox)

    python discover.py                 # DRY RUN - prints what it would add
    python discover.py --write         # actually append
    python discover.py --limit 40 --write

Dry-run by default, matching autoresponder.py: nothing in this lab writes or
sends on a bare invocation.
"""

import argparse
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from stages import reach  # noqa: E402

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pyyaml required -- pip install pyyaml")

HERE = Path(__file__).parent
FEEDS = HERE / "feeds.yaml"
SOURCES = HERE / "sources.yaml"
IDEAS = HERE.parent.parent / "Trading" / "Strategy Ideas.md"

YT = re.compile(r"(youtube\.com/watch|youtu\.be/|youtube\.com/shorts/)", re.I)


def existing_urls():
    """Every URL already known, so we never re-suggest one."""
    seen = set()
    if SOURCES.exists():
        d = yaml.safe_load(io.open(SOURCES, encoding="utf-8")) or {}
        for s in (d.get("sources") or []):
            if s.get("url"):
                seen.add(s["url"].split("?")[0].rstrip("/"))
    if IDEAS.exists():
        for m in re.finditer(r"https?://\S+", io.open(IDEAS, encoding="utf-8").read()):
            seen.add(m.group(0).rstrip(")|").split("?")[0].rstrip("/"))
    return seen


def matches(item, keywords):
    blob = f"{item.get('title','')} {item.get('summary','')}".lower()
    return [k for k in keywords if k.lower() in blob]


def append_sources(items):
    text = io.open(SOURCES, encoding="utf-8").read()
    anchor = "  # --- add new sources below as `pending` ---"
    block = ""
    for it in items:
        name = it["title"].replace('"', "'")[:70]
        block += (f'  - url: {it["url"]}\n'
                  f'    name: "{name}"\n'
                  f'    status: pending\n'
                  f'    tags: [discovered, rss]\n'
                  f'    note: >-\n'
                  f'      auto-discovered from {it["feed"]} (matched: '
                  f'{", ".join(it["hits"])}). Not yet triaged.\n\n')
    io.open(SOURCES, "w", encoding="utf-8", newline="\n").write(
        text.replace(anchor, block + anchor))


def append_ideas(items):
    text = io.open(IDEAS, encoding="utf-8").read()
    anchor = "|  |  | inbox |  |"
    rows = ""
    for it in items:
        title = it["title"].replace("|", "/")[:80]
        rows += (f'| [{title}]({it["url"]}) | {it["feed"]} | inbox | '
                 f'auto-discovered, matched: {", ".join(it["hits"])} |\n')
    io.open(IDEAS, "w", encoding="utf-8", newline="\n").write(
        text.replace(anchor, rows + anchor))



def scan_ig_profile(url, profile_dir=None, scrolls=6):
    """Reel shortcodes from an Instagram profile.

    Logged out, Instagram serves only the ~6 most recent posts before the login
    wall -- that is a hard cap, not a scroll problem (the reels tab returns the
    same 6). Pass --ig-profile-dir to reuse a Playwright persistent context you
    have logged into by hand; then the full grid is reachable.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  playwright not installed - skipping profile scan")
        return []

    UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
    ids, walled = set(), False
    with sync_playwright() as p:
        if profile_dir:
            ctx = p.chromium.launch_persistent_context(profile_dir, headless=True,
                                                       user_agent=UA)
            close = ctx.close
        else:
            br = p.chromium.launch(headless=True)
            ctx = br.new_context(user_agent=UA)
            close = br.close
        pg = ctx.new_page()
        try:
            pg.goto(url.rstrip("/") + "/reels/", wait_until="domcontentloaded",
                    timeout=45_000)
            pg.wait_for_timeout(4_000)
            for _ in range(scrolls):
                pg.keyboard.press("End")
                pg.wait_for_timeout(2_000)
            html = pg.content()
            ids = set(re.findall(r"/reel/([A-Za-z0-9_-]{5,})", html))
            walled = "log in" in pg.inner_text("body")[:400].lower()
        except Exception as e:
            print(f"  profile scan failed: {type(e).__name__}")
        finally:
            close()
    if walled and not profile_dir:
        print(f"  (login wall hit - only the {len(ids)} most recent are visible)")
    return [f"https://www.instagram.com/reel/{i}/" for i in sorted(ids)]


def profiles_to_queue(cfg, known, profile_dir):
    out = []
    for prof in (cfg.get("instagram_profiles") or []):
        urls = scan_ig_profile(prof["url"], profile_dir)
        new = [u for u in urls if u.split("?")[0].rstrip("/") not in known]
        for u in new:
            known.add(u.rstrip("/"))
            out.append({"url": u, "title": f"{prof['name']} reel {u.rstrip('/').split('/')[-1]}",
                        "feed": f"ig:{prof['name']}", "hits": ["profile-scan"]})
        print(f"  ig:{prof['name']}: {len(urls)} reels visible, {len(new)} new")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="actually append (default: dry run)")
    ap.add_argument("--limit", type=int, default=20, help="items to pull per feed")
    ap.add_argument("--profiles", action="store_true", help="also scan instagram_profiles")
    ap.add_argument("--ig-profile-dir", default=None,
                    help="Playwright persistent-context dir with an IG login "
                         "(lifts the 6-post logged-out cap)")
    args = ap.parse_args()

    if not reach.available():
        sys.exit("ERROR: agent-reach not available. Install it on Python >=3.11 and run\n"
                 "       `agent-reach install rss`, then re-run. See README.")

    cfg = yaml.safe_load(io.open(FEEDS, encoding="utf-8"))
    keywords, feeds = cfg.get("keywords", []), cfg.get("feeds", [])
    known = existing_urls()

    vids, ideas, scanned = [], [], 0
    for f in feeds:
        items = reach.rss_items(f["url"], args.limit)
        scanned += len(items)
        if not items:
            print(f"  {f['name']}: no items (feed down or empty)")
            continue
        kept = 0
        for it in items:
            url = it["url"].split("?")[0].rstrip("/")
            if url in known:
                continue
            hits = matches(it, keywords)
            if not hits:
                continue
            known.add(url)
            kept += 1
            rec = {**it, "feed": f["name"], "hits": hits}
            (vids if YT.search(it["url"]) else ideas).append(rec)
        print(f"  {f['name']}: {len(items)} items, {kept} new match(es)")

    if args.profiles:
        vids.extend(profiles_to_queue(cfg, known, args.ig_profile_dir))

    print(f"\nscanned {scanned} items across {len(feeds)} feeds")
    print(f"  -> sources.yaml (video queue): {len(vids)}")
    print(f"  -> Strategy Ideas (triage)   : {len(ideas)}")

    for it in (vids + ideas)[:15]:
        print(f"    [{','.join(it['hits'][:2])}] {it['title'][:72]}")

    if not args.write:
        print("\ndry run - nothing written. Re-run with --write to append.")
        return
    if vids:
        append_sources(vids)
        print(f"appended {len(vids)} to sources.yaml")
    if ideas:
        append_ideas(ideas)
        print(f"appended {len(ideas)} to Trading/Strategy Ideas.md")
    if not vids and not ideas:
        print("nothing new to append.")


if __name__ == "__main__":
    main()
