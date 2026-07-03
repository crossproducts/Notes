"""Stage 1: Extract — download video, extract audio, transcribe."""

import subprocess
import tempfile
import os
import hashlib
import json
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "cache"


def url_to_cache_key(url: str) -> str:
    """Create a stable cache key from a URL."""
    # Strip tracking params for cache consistency
    clean = url.split("?")[0].rstrip("/")
    return hashlib.md5(clean.encode()).hexdigest()[:12]


def download_audio(url: str, cache_key: str) -> str:
    """Download video and extract audio as mp3. Returns path to audio file.

    Tries yt-dlp first; falls back to a headless-browser capture for sources
    yt-dlp can't crack (e.g. login-walled Instagram reels).
    """
    audio_path = CACHE_DIR / f"{cache_key}.mp3"

    if audio_path.exists():
        print(f"  [cache hit] Audio already downloaded: {audio_path.name}")
        return str(audio_path)

    print("  Downloading video and extracting audio...")
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "-o", str(audio_path),
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  yt-dlp failed ({result.stderr.strip().splitlines()[-1] if result.stderr.strip() else 'no stderr'})")
        print("  Falling back to headless-browser capture...")
        return download_audio_via_browser(url, cache_key)

    # yt-dlp may produce a slightly different filename
    if not audio_path.exists():
        for f in CACHE_DIR.glob(f"{cache_key}*"):
            if f.suffix in (".mp3", ".m4a", ".wav"):
                audio_path = f
                break

    if not audio_path.exists():
        print("  yt-dlp produced no audio file; falling back to headless-browser capture...")
        return download_audio_via_browser(url, cache_key)

    print(f"  Audio saved: {audio_path.name}")
    return str(audio_path)


def download_audio_via_browser(url: str, cache_key: str) -> str:
    """Fallback: drive a headless browser to discover the media URL, then let
    ffmpeg fetch it and extract audio. Used when yt-dlp can't handle the source.

    Requires:  pip install playwright  &&  playwright install chromium
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError(
            "Browser fallback needs Playwright. Install with:\n"
            "    pip install playwright && playwright install chromium"
        ) from e

    audio_path = CACHE_DIR / f"{cache_key}.mp3"
    media_urls: list[tuple[str, str]] = []  # (url, content-type)

    def is_media(u: str) -> bool:
        u = u.split("?")[0].lower()
        return u.endswith((".mp4", ".m3u8", ".m4a"))

    print("  Launching headless browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            )
        )
        page = context.new_page()

        # Sniff network for media responses.
        def on_response(resp):
            u = resp.url
            ctype = (resp.headers or {}).get("content-type", "")
            if is_media(u) or ctype.startswith(("video/", "audio/")):
                media_urls.append((u, ctype))

        page.on("response", on_response)

        page.goto(url, wait_until="networkidle", timeout=45_000)
        # Nudge any lazy/click-to-play players, then let media requests fire.
        try:
            page.evaluate(
                "document.querySelectorAll('video').forEach(v => { v.muted = true; v.play().catch(() => {}); })"
            )
        except Exception:
            pass
        page.wait_for_timeout(4_000)

        # If the network sniff missed it, fall back to the <video src>.
        if not media_urls:
            try:
                src = page.eval_on_selector("video", "v => v.currentSrc || v.src")
                if src:
                    media_urls.append((src, ""))
            except Exception:
                pass

        referer = url
        context.close()
        browser.close()

    if not media_urls:
        raise RuntimeError("Browser fallback found no media URL on the page")

    # Sites like Instagram serve DASH: SEPARATE video and audio tracks. Rank
    # candidates audio-first (that's the track we actually want), dedupe, then
    # try each until ffmpeg finds an audio stream.
    import re as _re

    def rank(item):
        u, ctype = item
        path = u.split("?")[0].lower()
        if ctype.startswith("audio/") or path.endswith(".m4a"):
            return 0
        if path.endswith(".mp4"):
            return 1
        return 2

    seen, candidates = set(), []
    for u, ctype in sorted(media_urls, key=rank):
        # Strip byte-range fragment params so ffmpeg gets the WHOLE file.
        clean = _re.sub(r"[&?](bytestart|byteend)=\d+", "", u)
        if clean not in seen:
            seen.add(clean)
            candidates.append(clean)

    last_err = ""
    for media_url in candidates[:6]:
        print(f"  Trying media URL: {media_url.split('?')[0]}")
        cmd = [
            "ffmpeg", "-y",
            "-headers", f"Referer: {referer}\r\n",
            "-user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "-i", media_url,
            "-vn",
            "-acodec", "libmp3lame",
            "-q:a", "0",
            str(audio_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and audio_path.exists():
            print(f"  Audio saved: {audio_path.name}")
            return str(audio_path)
        last_err = result.stderr[-300:]

    raise RuntimeError(f"ffmpeg failed on all {len(candidates[:6])} captured URLs: {last_err}")


def transcribe(audio_path: str, cache_key: str, model_size: str = "base") -> str:
    """Transcribe audio to text using Whisper. Returns transcript string."""
    transcript_path = CACHE_DIR / f"{cache_key}_transcript.txt"

    if transcript_path.exists():
        print(f"  [cache hit] Transcript already exists: {transcript_path.name}")
        return transcript_path.read_text(encoding="utf-8")

    print(f"  Loading Whisper model ({model_size})...")
    import whisper
    model = whisper.load_model(model_size)

    print("  Transcribing audio...")
    result = model.transcribe(audio_path)
    transcript = result["text"]

    # Save transcript
    transcript_path.write_text(transcript, encoding="utf-8")

    # Save segments for reference
    segments_path = CACHE_DIR / f"{cache_key}_segments.json"
    segments_path.write_text(
        json.dumps(result["segments"], indent=2, default=str),
        encoding="utf-8",
    )

    print(f"  Transcript saved ({len(transcript)} chars)")
    return transcript


def get_caption(url: str) -> str:
    """Get the post caption via yt-dlp (bonus metadata)."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--skip-download", "--print", "description", url],
            capture_output=True, text=True, timeout=15,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def run(url: str, whisper_model: str = "base") -> dict:
    """Run the full extraction stage. Returns dict with transcript and metadata."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = url_to_cache_key(url)

    print("\n[STAGE 1: EXTRACT]")
    caption = get_caption(url)
    if caption:
        print(f"  Caption: {caption[:80]}...")

    audio_path = download_audio(url, cache_key)
    transcript = transcribe(audio_path, cache_key, whisper_model)

    return {
        "cache_key": cache_key,
        "url": url,
        "caption": caption,
        "transcript": transcript,
        "audio_path": audio_path,
    }
