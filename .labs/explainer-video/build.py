#!/usr/bin/env python3
"""Narrated explainer videos: a deck module in, an MP4 out.

Reuses what this repo already has rather than adding anything: the neural TTS
from `.labs/email-sender/send_voice.py`, the headless Chromium the extraction
pipeline installs, and ffmpeg. No new dependencies.

A deck is a Python module exposing TITLE, VOICE (optional) and SCENES -- a list
of {"narration": str, "html": str}. Each scene becomes one still frame held for
exactly as long as its narration, so the picture and the voice can never drift.

    python build.py decks/crypto_aws.py
    python build.py decks/crypto_aws.py --engine sapi    # fully offline
    python build.py decks/crypto_aws.py --scene 4        # re-render one frame

ENGINES, best first:
  kokoro  (default) Kokoro-82M via onnxruntime. Local, Apache-2.0, ~340 MB of
          weights, ~2.4x realtime on CPU, 54 voices. Nothing leaves the machine.
  edge    Microsoft neural voices. Slightly smoother, but it SENDS THE
          NARRATION TEXT to a Microsoft endpoint. Fine for public material.
  sapi    The built-in Windows voice. Offline, instant, robotic.

Not Coqui/XTTS: the company shut down in 2024 and the repo is archived; XTTS-v2
is ~1.8 GB, wants a GPU for realtime, and its model licence is non-commercial.
"""

import argparse
import asyncio
import html as html_mod
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
MODELS = HERE / "models"
WORK = OUT / ".work"
W, H = 1920, 1080
PAD_SECONDS = 0.55          # breathing room after each line
DEFAULT_VOICE = "am_michael"          # kokoro
EDGE_VOICE = "en-US-AndrewNeural"
KOKORO_MODEL = "kokoro-v1.0.onnx"
KOKORO_VOICES = "voices-v1.0.bin"
_KOKORO = None
DEFAULT_RATE = "-5%"        # a touch slower than default: this is teaching


# --------------------------------------------------------------- page shell --
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0E1116; --panel:#161B22; --ink:#E9EDF2; --dim:#8B96A5;
  --edge:#5B9BF8; --compute:#4FBF7F; --data:#E3A008; --accent:#F0B429;
}
html,body{width:1920px;height:1080px;overflow:hidden}
body{
  background:
    radial-gradient(1200px 700px at 78% 12%, #18212E 0%, rgba(14,17,22,0) 62%),
    var(--bg);
  color:var(--ink);
  font-family:'Segoe UI',Inter,Helvetica,Arial,sans-serif;
  display:flex;align-items:center;justify-content:center;
  -webkit-font-smoothing:antialiased;
}
.slide{width:1720px;height:900px;display:flex;flex-direction:column;justify-content:center}
h1{font-size:92px;font-weight:700;letter-spacing:-2px;line-height:1.04}
h2{font-size:62px;font-weight:650;letter-spacing:-1px;margin-bottom:14px;line-height:1.08}
.kicker{font-size:25px;font-weight:650;letter-spacing:4.5px;text-transform:uppercase;
  color:var(--accent);margin-bottom:26px}
.sub{font-size:35px;color:var(--dim);line-height:1.45;max-width:1500px;margin-top:20px}
.analogy{font-size:38px;color:var(--accent);font-style:italic;margin-top:34px;line-height:1.35}
.row{display:flex;gap:30px;align-items:stretch;margin-top:46px}
.row.center{align-items:center}
.card{background:var(--panel);border:2px solid #263040;border-radius:20px;
  padding:34px 36px;flex:1;min-height:200px}
.card h3{font-size:36px;font-weight:650;margin-bottom:14px}
.card p{font-size:28px;color:var(--dim);line-height:1.42}
.card .big{font-size:66px;font-weight:700;line-height:1.1}
.pill{display:inline-block;padding:12px 26px;border-radius:999px;font-size:27px;
  font-weight:650;border:2px solid currentColor}
.blue{color:#6FA8FF}.green{color:#5FD08A}.amber{color:#F0B429}
.red{color:#F2777A}.purple{color:#C08CE0}.grey{color:#8B96A5}
.b-blue{border-color:#2E4A77;background:#141E30}
.b-green{border-color:#2A5740;background:#10231A}
.b-amber{border-color:#6B5212;background:#241C08}
.b-red{border-color:#6B2B2D;background:#241012}
.b-purple{border-color:#4A2F66;background:#1A1024}
.arrow{font-size:56px;color:#4C5A6E;align-self:center;padding:0 6px}
.mono{font-family:'Cascadia Code',Consolas,monospace;font-size:26px;color:#9FD0FF}
.note{font-size:26px;color:#6F7C8C;margin-top:30px}
.tag{font-size:22px;letter-spacing:2px;text-transform:uppercase;color:var(--dim);
  font-weight:650;margin-bottom:10px}
ul{margin-top:26px}
li{font-size:33px;color:var(--ink);line-height:1.62;list-style:none;margin-bottom:8px}
li::before{content:"\\2014";color:var(--accent);margin-right:18px}
.kv{font-size:27px;line-height:1.95;color:var(--dim)}
.kv b{color:var(--ink);font-weight:650}
.footer{position:absolute;bottom:42px;left:100px;font-size:22px;color:#49546380;
  letter-spacing:2px}
"""


def page(body: str) -> str:
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{CSS}</style></head><body><div class='slide'>{body}</div></body></html>")


# ------------------------------------------------------------------ helpers --
def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.exit(f"ERROR: {cmd[0]} failed\n{(r.stderr or r.stdout)[-1200:]}")
    return r


def probe_duration(path: Path) -> float:
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "json", str(path)])
    return float(json.loads(r.stdout)["format"]["duration"])


# ---------------------------------------------------------------------- tts --
async def _edge(text, out_mp3, voice, rate):
    import edge_tts
    await edge_tts.Communicate(text, voice, rate=rate).save(str(out_mp3))


def _rate_to_speed(rate: str) -> float:
    """'-5%' -> 0.95. Kokoro takes a speed multiplier, edge takes a percentage."""
    try:
        return max(0.5, min(2.0, 1.0 + int(rate.strip().strip("%")) / 100.0))
    except ValueError:
        return 1.0


def tts_kokoro(text, out_mp3: Path, voice: str, rate: str):
    """Kokoro-82M via onnxruntime. Apache-2.0, ~82M params, fully offline.

    Chosen over Coqui/XTTS deliberately: Coqui the company shut down in 2024 and
    its repo is archived, XTTS-v2 is ~1.8GB and wants a GPU for realtime, and
    its model licence is non-commercial. Kokoro is a fraction of the size, runs
    comfortably faster than realtime on CPU, and is permissively licensed.
    """
    global _KOKORO
    import soundfile as sf
    from kokoro_onnx import Kokoro
    model, voices = MODELS / KOKORO_MODEL, MODELS / KOKORO_VOICES
    if not model.exists() or not voices.exists():
        sys.exit(f"ERROR: kokoro model files missing in {MODELS}/ -- see README")
    if _KOKORO is None:
        _KOKORO = Kokoro(str(model), str(voices))
    samples, sr = _KOKORO.create(text, voice=voice, speed=_rate_to_speed(rate),
                                 lang="en-us")
    wav = out_mp3.with_suffix(".wav")
    sf.write(str(wav), samples, sr)
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
         "-codec:a", "libmp3lame", "-q:a", "2", str(out_mp3)])
    wav.unlink(missing_ok=True)


def tts(text: str, out_mp3: Path, engine: str, voice: str, rate: str):
    if engine == "kokoro":
        tts_kokoro(text, out_mp3, voice, rate)
        return "kokoro"
    if engine == "edge":
        try:
            asyncio.run(_edge(text, out_mp3, EDGE_VOICE if voice.startswith(("a", "b"))
                              and "_" in voice else voice, rate))
            return "edge"
        except Exception as e:
            print(f"    edge-tts failed ({type(e).__name__}); falling back to SAPI")
    wav = out_mp3.with_suffix(".wav")
    sapi_rate = 0
    try:
        sapi_rate = max(-10, min(10, round(int(rate.strip("%+")) / 10)))
        if rate.strip().startswith("-"):
            sapi_rate = -abs(sapi_rate)
    except ValueError:
        pass
    ps = ("Add-Type -AssemblyName System.Speech; "
          "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
          f"$s.Rate = {sapi_rate}; $s.SetOutputToWaveFile('{wav}'); "
          f"$s.Speak([Console]::In.ReadToEnd()); $s.Dispose()")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       input=text, capture_output=True, text=True)
    if r.returncode != 0 or not wav.exists():
        sys.exit(f"ERROR: SAPI synthesis failed: {(r.stderr or '')[:300]}")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
         "-codec:a", "libmp3lame", "-q:a", "3", str(out_mp3)])
    wav.unlink(missing_ok=True)
    return "sapi"


# -------------------------------------------------------------------- build --
def load_deck(path: Path):
    spec = importlib.util.spec_from_file_location("deck", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def render_frames(scenes, only=None):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        for i, sc in enumerate(scenes):
            if only is not None and i != only:
                continue
            f = WORK / f"frame_{i:03d}.png"
            pg.set_content(page(sc["html"]), wait_until="load")
            pg.wait_for_timeout(120)
            pg.screenshot(path=str(f))
            print(f"    frame {i:02d}  {f.name}")
        br.close()


def build_assets(scenes, args, voice):
    """Render every frame and synthesise every line. Returns per-scene seconds."""
    print("  rendering frames...")
    render_frames(scenes)
    print(f"  synthesising narration ({args.engine}, {voice} @ {args.rate})...")
    durations = []
    for i, sc in enumerate(scenes):
        mp3 = WORK / f"vo_{i:03d}.mp3"
        used = tts(sc["narration"], mp3, args.engine, voice, args.rate)
        raw = probe_duration(mp3)
        padded = WORK / f"vop_{i:03d}.mp3"
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-af", "apad",
             "-t", f"{raw + PAD_SECONDS:.3f}", "-codec:a", "libmp3lame",
             "-q:a", "3", str(padded)])
        d = probe_duration(padded)
        durations.append(d)
        print(f"    scene {i:02d}  {d:5.1f}s  [{used}]  {sc['narration'][:58]}...")
    return durations



def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--engine", choices=("kokoro", "edge", "sapi"),
                    default="kokoro",
                    help="kokoro = local neural (default); edge = neural but sends text to Microsoft; sapi = local, robotic")
    ap.add_argument("--voice", default=None)
    ap.add_argument("--rate", default=DEFAULT_RATE)
    ap.add_argument("--scene", type=int, default=None,
                    help="render only this frame to out/preview.png and stop")
    ap.add_argument("--resume", action="store_true",
                    help="reuse frames and narration already in out/.work "
                         "(skips rendering and TTS; for re-muxing only)")
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"ERROR: {tool} not on PATH")

    deck = load_deck(Path(args.deck))
    scenes = deck.SCENES
    voice = args.voice or getattr(deck, "VOICE", DEFAULT_VOICE)
    slug = getattr(deck, "SLUG", Path(args.deck).stem)
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)

    if args.scene is not None:
        render_frames(scenes, only=args.scene)
        shutil.copy(WORK / f"frame_{args.scene:03d}.png", OUT / "preview.png")
        print(f"preview -> {OUT / 'preview.png'}")
        return

    print(f"{deck.TITLE}  ({len(scenes)} scenes)")
    have = all((WORK / f"frame_{i:03d}.png").exists()
               and (WORK / f"vop_{i:03d}.mp3").exists() for i in range(len(scenes)))
    if args.resume and have:
        durations = [probe_duration(WORK / f"vop_{i:03d}.mp3")
                     for i in range(len(scenes))]
        print(f"  resuming from {WORK} ({len(durations)} frames + narration)")
    else:
        if args.resume:
            print("  --resume given but artifacts are incomplete; building fresh")
        durations = build_assets(scenes, args, voice)
    total = sum(durations)
    print(f"  total runtime {int(total // 60)}m {total % 60:04.1f}s")

    vlist = WORK / "frames.txt"
    with open(vlist, "w", encoding="utf-8", newline="\n") as f:
        for i, d in enumerate(durations):
            f.write(f"file 'frame_{i:03d}.png'\nduration {d:.3f}\n")
        f.write(f"file 'frame_{len(durations)-1:03d}.png'\n")   # concat quirk

    alist = WORK / "audio.txt"
    with open(alist, "w", encoding="utf-8", newline="\n") as f:
        for i in range(len(durations)):
            f.write(f"file 'vop_{i:03d}.mp3'\n")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", "audio.txt", "-codec:a", "libmp3lame", "-q:a", "2",
         "narration.mp3"], cwd=WORK)
    # The concat demuxer needs the last image repeated or it is shown for a
    # single frame -- but that repeat then inherits the previous duration and
    # adds it again, and -shortest does NOT catch it because an image-concat
    # video stream has no known length. So cap the output at the real audio
    # length. Without this the video ran 47s past the end of the narration.
    track_len = probe_duration(WORK / "narration.mp3")

    out = OUT / f"{slug}.mp4"
    print("  muxing...")
    run(["ffmpeg", "-y", "-loglevel", "error",
         "-f", "concat", "-safe", "0", "-i", "frames.txt",
         "-i", "narration.mp3",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-pix_fmt", "yuv420p", "-r", "30",
         "-c:a", "aac", "-b:a", "112k",
         "-t", f"{track_len:.3f}",
         "-movflags", "+faststart", str(out.resolve())], cwd=WORK)

    size = out.stat().st_size / 1_048_576
    print(f"\nwrote {out}  ({size:.1f} MB, {int(total // 60)}m {total % 60:04.1f}s)")


if __name__ == "__main__":
    main()
