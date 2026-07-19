"""Host-side video-queue worker for Strategy Studio.

The studio UI queues video URLs into Postgres (POST /videos); this script —
running on the HOST, where the pipeline's heavy deps live (Whisper, yt-dlp,
Playwright, ffmpeg) — claims one at a time, runs the full video → strategy →
backtest pipeline, and reports the result back. Finished strategies appear in
the studio's strategy dropdown as video:<cache_key> (the cache dir is mounted
into the API container).

Run it:
    python studio_worker.py            # poll forever (Ctrl+C to stop)
    python studio_worker.py --once     # process at most one item, then exit

Needs this project's requirements installed and ANTHROPIC_API_KEY etc. in .env.
Override the API base with STUDIO_API (default http://localhost:8001).
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

API = os.getenv("STUDIO_API", "http://localhost:8001").rstrip("/")
POLL_SECONDS = 20


def _post(path: str, payload: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(payload or {}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def process_one() -> bool:
    """Claim and process a single queued video. Returns False when queue is empty."""
    claim = _post("/videos/claim")
    if claim.get("empty"):
        return False

    vid, url = claim["id"], claim["url"]
    print(f"\n[studio-worker] claimed {vid}: {url}")

    from pipeline import run_pipeline
    from stages.extract import url_to_cache_key

    try:
        run_pipeline(url)
        cache_key = url_to_cache_key(url)
        _post(f"/videos/{vid}/complete",
              {"status": "done", "cache_key": cache_key,
               "note": f"strategy available as video:{cache_key}"})
        print(f"[studio-worker] done {vid} -> video:{cache_key}")
    except Exception as e:
        _post(f"/videos/{vid}/complete",
              {"status": "error", "note": str(e)[:400]})
        print(f"[studio-worker] ERROR on {vid}: {e}")
    return True


def main():
    once = "--once" in sys.argv
    print(f"[studio-worker] polling {API} every {POLL_SECONDS}s (Ctrl+C to stop)")
    try:
        while True:
            try:
                worked = process_one()
            except urllib.error.URLError as e:
                print(f"[studio-worker] API unreachable: {e} — retrying in {POLL_SECONDS}s")
                worked = False
            if once:
                break
            if not worked:
                time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        print("\n[studio-worker] stopped")


if __name__ == "__main__":
    main()
