"""Stage 1: Extract — download video, extract audio, transcribe."""

import subprocess
import tempfile
import os
import hashlib
import json
from pathlib import Path

from . import reach

CACHE_DIR = Path(__file__).parent.parent / "cache"


def url_to_cache_key(url: str) -> str:
    """Create a stable cache key from a URL."""
    # Strip tracking params for cache consistency
    clean = url.split("?")[0].rstrip("/")
    return hashlib.md5(clean.encode()).hexdigest()[:12]


def download_video(url: str, cache_key: str) -> tuple[str, str]:
    """Download full video as mp4 and derive mp3 audio from it.

    Returns (audio_path, video_path). video_path may be empty string if the
    video download failed or was skipped (audio-only fallback).

    Cache logic:
    - If both mp3 and mp4 exist: cache hit, skip all downloads.
    - If only mp3 exists (old cache entry): audio cache hit, frames will be
      empty because there is no video file.
    - If neither exists: download full video, then derive mp3 via ffmpeg.
    """
    audio_path = CACHE_DIR / f"{cache_key}.mp3"
    video_path = CACHE_DIR / f"{cache_key}.mp4"

    if audio_path.exists() and video_path.exists():
        print(f"  [cache hit] Audio + video already downloaded: {audio_path.name}")
        return str(audio_path), str(video_path)

    if audio_path.exists():
        # Old cache entry — only audio present; frames will be empty.
        print(f"  [cache hit] Audio already downloaded (no video cache): {audio_path.name}")
        print("  Warning: no video file found for this cache entry; frame capture skipped.")
        return str(audio_path), ""

    print("  Downloading full video...")
    cmd = [
        "yt-dlp",
        "-f", "mp4/bestvideo*+bestaudio/best",
        "--remux-video", "mp4",
        "--merge-output-format", "mp4",
        "-o", str(video_path),
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0 or not video_path.exists():
        print(
            f"  yt-dlp video download failed "
            f"({result.stderr.strip().splitlines()[-1] if result.stderr.strip() else 'no stderr'})"
        )
        # yt-dlp may leave a partial file; a truncated mp4 must not become a
        # permanent cache hit
        video_path.unlink(missing_ok=True)
        print("  Falling back to headless-browser capture (audio-only)...")
        audio = download_audio_via_browser(url, cache_key, video_path=str(video_path))
        return audio, str(video_path) if video_path.exists() else ""

    print(f"  Video saved: {video_path.name}")

    # Derive mp3 from the downloaded video via ffmpeg.
    print("  Extracting audio from video...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "libmp3lame",
        "-q:a", "0",
        str(audio_path),
    ]
    r2 = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if r2.returncode != 0 or not audio_path.exists():
        print(f"  ffmpeg audio extraction failed: {r2.stderr[-300:]}")
        raise RuntimeError("ffmpeg could not extract audio from downloaded video")

    print(f"  Audio saved: {audio_path.name}")
    return str(audio_path), str(video_path)


# Keep the old name as an alias so any external callers won't break.
def download_audio(url: str, cache_key: str) -> str:
    """Backwards-compatible wrapper — returns only the audio path."""
    audio_path, _ = download_video(url, cache_key)
    return audio_path


def download_audio_via_browser(url: str, cache_key: str, video_path: str = "") -> str:
    """Fallback: drive a headless browser to discover the media URL, then let
    ffmpeg fetch it and extract audio. Used when yt-dlp can't handle the source.

    If video_path is given and an .mp4 candidate URL is discovered, attempts
    to also save the full video stream for later frame extraction.

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
        # no-user-gesture: allow UNMUTED autoplay — a muted DASH player may
        # never request the audio track at all, leaving only video URLs to sniff
        browser = p.chromium.launch(
            headless=True,
            args=["--autoplay-policy=no-user-gesture-required"],
        )
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
        page.wait_for_timeout(2_000)
        # Unmute once playing — muted playback can skip audio-track requests
        try:
            page.evaluate(
                "document.querySelectorAll('video').forEach(v => { v.muted = false; v.volume = 1.0; })"
            )
        except Exception:
            pass
        page.wait_for_timeout(5_000)

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
        # Instagram serves its DASH *audio* track as content-type video/mp4 with
        # /m78/ in the path, and the video-only tracks as /m367/. Without this
        # they all rank equal, so a reel with many video tracks exhausts the
        # 6-candidate budget on streams that contain no audio at all and the
        # extract fails with "Output file #0 does not contain any stream".
        if "/m78/" in path:
            return 0
        if "/m367/" in path:
            return 2
        if path.endswith(".mp4"):
            return 1
        return 3

    seen, candidates = set(), []
    mp4_candidates = []
    for u, ctype in sorted(media_urls, key=rank):
        # Strip byte-range fragment params so ffmpeg gets the WHOLE file.
        clean = _re.sub(r"[&?](bytestart|byteend)=\d+", "", u)
        if clean not in seen:
            seen.add(clean)
            candidates.append(clean)
            # Only real VIDEO tracks are frame-capture candidates. Instagram's
            # audio track also ends in .mp4, so without excluding /m78/ we save
            # the audio stream as the "video" and frame extraction silently
            # yields 0 frames from an mp4 that has no video stream at all.
            path = clean.split("?")[0].lower()
            if path.endswith(".mp4") and "/m78/" not in path:
                mp4_candidates.append(clean)

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

            # Opportunistically save video for frame extraction.
            if video_path and mp4_candidates and not Path(video_path).exists():
                _try_save_video(mp4_candidates[0], referer, video_path)

            return str(audio_path)
        last_err = result.stderr[-300:]

    raise RuntimeError(f"ffmpeg failed on all {len(candidates[:6])} captured URLs: {last_err}")


def _try_save_video(media_url: str, referer: str, video_path: str) -> None:
    """Best-effort: copy a video stream to disk for frame extraction.

    Never raises — failure is silently swallowed so the audio flow continues.
    """
    print(f"  Attempting to save video stream for frame capture: {media_url.split('?')[0]}")
    cmd = [
        "ffmpeg", "-y",
        "-headers", f"Referer: {referer}\r\n",
        "-user_agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "-i", media_url,
        "-c", "copy",
        video_path,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and Path(video_path).exists():
            print(f"  Video stream saved: {Path(video_path).name}")
        else:
            # ffmpeg leaves a partial file on failure; remove it or the cache
            # treats the truncated mp4 as valid forever
            Path(video_path).unlink(missing_ok=True)
            print("  Warning: could not save video stream for frame capture (continuing audio-only)")
    except Exception as exc:
        Path(video_path).unlink(missing_ok=True)
        print(f"  Warning: video save attempt raised {exc} (continuing audio-only)")


def _get_video_duration(video_path: str) -> float:
    """Use ffprobe to get video duration in seconds. Returns 0.0 on failure."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode == 0 and r.stdout.strip():
            return float(r.stdout.strip())
    except Exception:
        pass
    return 0.0


def extract_frames(video_path: str, cache_key: str, max_frames: int = 10) -> list[str]:
    """Extract representative frames from a video as JPEGs for vision analysis.

    Strategy:
    1. Try scene-change detection (threshold 0.3). If >= 3 frames are found,
       keep an evenly-spaced subset capped at max_frames.
    2. If scene detection yields fewer than 3 frames (static camera / talking
       head), fall back to fixed-interval sampling using ffprobe for duration.

    All frames are downscaled to max 1024 px wide. Results are cached in
    cache/{cache_key}_frames/. Returns list of file paths (possibly empty).
    """
    if not video_path or not Path(video_path).exists():
        return []

    frames_dir = CACHE_DIR / f"{cache_key}_frames"

    # Cache: reuse if non-empty.
    if frames_dir.exists() and any(frames_dir.glob("*.jpg")):
        existing = sorted(frames_dir.glob("*.jpg"))
        print(f"  [cache hit] {len(existing)} frames already extracted: {frames_dir.name}/")
        return [str(f) for f in existing]

    frames_dir.mkdir(parents=True, exist_ok=True)
    scene_dir = frames_dir / "_scene_tmp"
    scene_dir.mkdir(parents=True, exist_ok=True)

    print("  Extracting frames via scene-change detection...")
    scene_pattern = str(scene_dir / "frame_%04d.jpg")
    cmd_scene = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", "select='gt(scene,0.3)',scale='min(1024,iw)':-2",
        "-vsync", "vfr",
        "-q:v", "2",
        scene_pattern,
    ]
    subprocess.run(cmd_scene, capture_output=True, text=True)

    scene_frames = sorted(scene_dir.glob("*.jpg"))

    if len(scene_frames) >= 3:
        # Keep evenly spaced subset, capped at max_frames.
        selected = _evenly_spaced(scene_frames, max_frames)
        print(f"  Scene detection found {len(scene_frames)} frames; keeping {len(selected)}")
    else:
        print(
            f"  Scene detection found only {len(scene_frames)} frame(s); "
            "falling back to fixed-interval sampling..."
        )
        selected = _fixed_interval_frames(video_path, frames_dir, cache_key, max_frames)
        # Clean up sparse scene frames — fixed interval results go to frames_dir directly.
        for f in scene_frames:
            try:
                f.unlink()
            except Exception:
                pass
        try:
            scene_dir.rmdir()
        except Exception:
            pass

        return selected

    # Move selected frames to frames_dir with clean names.
    final_paths = []
    for i, src in enumerate(selected):
        dest = frames_dir / f"frame_{i:04d}.jpg"
        src.rename(dest)
        final_paths.append(str(dest))

    # Remove leftover unselected scene frames.
    for f in scene_dir.glob("*.jpg"):
        try:
            f.unlink()
        except Exception:
            pass
    try:
        scene_dir.rmdir()
    except Exception:
        pass

    print(f"  Frames saved to {frames_dir.name}/ ({len(final_paths)} files)")
    return final_paths


def _evenly_spaced(items: list, n: int) -> list:
    """Return up to n evenly-spaced items from a list."""
    if len(items) <= n:
        return list(items)
    step = (len(items) - 1) / (n - 1)
    return [items[round(i * step)] for i in range(n)]


def _fixed_interval_frames(
    video_path: str, frames_dir: Path, cache_key: str, max_frames: int
) -> list[str]:
    """Sample max_frames evenly-spaced frames from the video using timestamps."""
    duration = _get_video_duration(video_path)
    if duration <= 0:
        print("  Warning: could not determine video duration; skipping frame extraction")
        return []

    # Generate timestamps evenly spaced across the video.
    if max_frames == 1:
        timestamps = [duration / 2]
    else:
        step = duration / (max_frames + 1)
        timestamps = [step * (i + 1) for i in range(max_frames)]

    print(f"  Sampling {len(timestamps)} frames from {duration:.1f}s video...")
    paths = []
    for i, ts in enumerate(timestamps):
        out_path = frames_dir / f"frame_{i:04d}.jpg"
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{ts:.3f}",
            "-i", video_path,
            "-vframes", "1",
            "-vf", "scale='min(1024,iw)':-2",
            "-q:v", "2",
            str(out_path),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and out_path.exists():
            paths.append(str(out_path))

    print(f"  Fixed-interval frames saved: {len(paths)}")
    return paths


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

    # Fast path: YouTube publishes its own captions, so for YT sources we can
    # skip the audio download AND the Whisper pass -- seconds instead of
    # minutes. Falls through to the normal path when there are no captions.
    # This is NOT a fallback for Instagram: that channel drives the same yt-dlp
    # that is already login-walled there. See stages/reach.py.
    transcript = None
    if reach.is_youtube(url):
        transcript = reach.youtube_transcript(url, cache_key)
        if transcript:
            print(f"  Transcript via agent-reach captions ({len(transcript)} chars) "
                  f"- skipped download + Whisper")

    if transcript:
        # Still fetch the video for frame capture; audio is no longer needed.
        _, video_path = download_video(url, cache_key)
    else:
        audio_path, video_path = download_video(url, cache_key)
        transcript = transcribe(audio_path, cache_key, whisper_model)

    # Extract frames (empty list if no video file available).
    frames = extract_frames(video_path, cache_key) if video_path else []
    if frames:
        print(f"  Captured {len(frames)} frame(s) for vision analysis")
    else:
        print("  No frames captured (audio-only mode)")

    return {
        "cache_key": cache_key,
        "url": url,
        "caption": caption,
        "transcript": transcript,
        "audio_path": audio_path,
        "video_path": video_path,
        "frames": frames,
    }
