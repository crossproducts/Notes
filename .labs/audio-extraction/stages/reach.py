"""Thin wrapper around the `agent-reach` CLI.

Why a CLI wrapper and not an import: agent-reach requires Python >= 3.11 and
this pipeline runs on 3.10 (where whisper/playwright/yt-dlp live). The CLI is
the stable interface across that boundary, so we shell out.

What this is FOR, and what it is NOT for:

  * NOT an Instagram fallback. agent-reach's youtube channel drives the same
    yt-dlp that already fails on login-walled reels -- it returns the identical
    error. The Playwright+ffmpeg path in extract.py remains the only thing that
    cracks those.
  * IS a YouTube fast path. YouTube publishes its own captions, so we can skip
    the audio download AND the Whisper pass entirely -- seconds instead of
    minutes, and no 461 MB model load.
  * IS a discovery intake. The rss channel pulls feeds, which is how sources
    get into the research queue without someone pasting a link.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "cache"
TIMEOUT = 180

YOUTUBE_RE = re.compile(r"(youtube\.com/watch|youtu\.be/|youtube\.com/shorts/)", re.I)


def is_youtube(url: str) -> bool:
    return bool(YOUTUBE_RE.search(url or ""))


def _cmd():
    """Locate agent-reach. The console script is usually NOT on PATH, so prefer
    the py launcher's module form, which works regardless of PATH."""
    exe = shutil.which("agent-reach")
    if exe:
        return [exe]
    if shutil.which("py"):
        return ["py", "-3.14", "-m", "agent_reach"]
    return None


def available() -> bool:
    cmd = _cmd()
    if not cmd:
        return False
    try:
        r = subprocess.run(cmd + ["doctor"], capture_output=True, text=True, timeout=30)
        return r.returncode == 0 and "ok" in r.stdout
    except Exception:
        return False


def _get(target, query, extra=None):
    cmd = _cmd()
    if not cmd:
        return None
    try:
        r = subprocess.run(cmd + ["get", target, query] + (extra or []),
                           capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    out = r.stdout.strip()
    if out.lower().startswith("agent-reach:") and "error" in out.lower():
        return None
    return out


def youtube_transcript(url: str, cache_key: str = None):
    """YouTube captions as plain text, or None if unavailable.

    Returns None (rather than raising) whenever captions are missing, the video
    is private, or the channel errors -- the caller then falls back to the
    download + Whisper path.
    """
    raw = _get("youtube", url)
    if not raw:
        return None

    # Strip the channel's markdown header block: a '# youtube:transcript' line,
    # a '## <title>' line, and the uploader/date/stats line beneath it.
    lines = raw.split("\n")
    body, seen_title = [], False
    for ln in lines:
        if ln.startswith("# "):
            continue
        if ln.startswith("## "):
            seen_title = True
            continue
        if seen_title and (ln.startswith("views:") or re.match(r"^\S+\s+\d{4}-\d{2}-\d{2}\s", ln)):
            continue
        body.append(ln)

    text = "\n".join(body).strip()
    if len(text) < 40:          # header-only response == no real transcript
        return None

    if cache_key:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (CACHE_DIR / f"{cache_key}_transcript.txt").write_text(text, encoding="utf-8")
        (CACHE_DIR / f"{cache_key}_transcript.src").write_text(
            "agent-reach:youtube (publisher captions, no Whisper)", encoding="utf-8")
    return text


def rss_items(feed_url: str, limit: int = 20):
    """[{title, url, summary}] from an RSS/Atom feed, or [] on failure."""
    raw = _get("rss", feed_url, ["--limit", str(limit)])
    if not raw:
        return []
    items, cur = [], None
    for ln in raw.split("\n"):
        if ln.startswith("## "):
            if cur:
                items.append(cur)
            cur = {"title": ln[3:].strip(), "url": "", "summary": ""}
        elif cur is not None:
            m = re.search(r"(https?://\S+)", ln)
            if m and not cur["url"]:
                cur["url"] = m.group(1)
            elif ln.strip():
                cur["summary"] = (cur["summary"] + " " + ln.strip()).strip()
    if cur:
        items.append(cur)
    return [i for i in items if i.get("url")]
