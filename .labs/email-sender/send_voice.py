#!/usr/bin/env python3
"""Send a spoken voice note to a phone as MMS, through the same Gmail bridge.

Text -> neural TTS -> AAC/M4A -> attached to an email addressed at the carrier
gateway. The carrier turns an email WITH an attachment into an MMS, and iOS
Messages plays .m4a inline, so it lands as a tappable voice note rather than a
file you have to open.

    python send_voice.py --text "Backtest finished. The gate failed, 0 for 10."
    python send_voice.py --text-file note.txt --voice en-US-AvaNeural
    python send_voice.py --text "hi" --to 5551234567@tmomail.net
    python send_voice.py --text "hi" --keep out.m4a --dry-run   # build, don't send

Why M4A/AAC mono: it is the smallest format iOS plays natively without
transcoding. At 32 kbps mono, speech is ~4 KB/sec -- about 3.5 minutes inside a
900 KB MMS budget. AMR would be smaller but sounds like a 2003 phone call.

TTS engines, in order of preference:
  edge-tts  neural, free, no API key -- but the TEXT IS SENT to a Microsoft
            endpoint to be synthesised. Do not use it for anything sensitive.
  sapi      Windows System.Speech. Fully offline, robotic. --engine sapi.

Carrier MMS ceilings are small and vary (~300 KB - 1 MB). The default budget is
deliberately conservative; oversized notes are re-encoded at a lower bitrate and
then, if still too big, refused rather than silently truncated by the carrier.
"""

import argparse
import asyncio
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from send_email import build_message  # noqa: E402  (reuse, don't duplicate SMTP)

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

DEFAULT_VOICE = "en-US-AndrewNeural"
MMS_BUDGET = int(os.getenv("MMS_BUDGET_BYTES", 900_000))
BITRATE_LADDER = ["32k", "24k", "16k"]

GATEWAYS = ("tmomail.net", "vtext.com", "vzwpix.com", "txt.att.net", "mms.att.net",
            "mymetropcs.com", "messaging.sprintpcs.com", "msg.fi.google.com")


def tts_edge(text, out_mp3, voice, rate):
    import edge_tts

    async def go():
        kw = {"rate": rate} if rate else {}
        await edge_tts.Communicate(text, voice, **kw).save(str(out_mp3))

    asyncio.run(go())


def tts_sapi(text, out_wav, rate):
    """Offline fallback. SAPI rate is -10..10; map an edge-style '+20%' onto it."""
    sapi_rate = 0
    if rate:
        try:
            sapi_rate = max(-10, min(10, round(int(rate.strip("%+")) / 10)))
            if rate.startswith("-"):
                sapi_rate = -abs(sapi_rate)
        except ValueError:
            pass
    ps = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$s.Rate = {sapi_rate}; "
        f"$s.SetOutputToWaveFile('{out_wav}'); "
        f"$s.Speak([Console]::In.ReadToEnd()); $s.Dispose()"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       input=text, text=True, capture_output=True)
    if r.returncode != 0 or not Path(out_wav).exists():
        sys.exit(f"ERROR: SAPI synthesis failed: {r.stderr.strip()[:300]}")


def encode_m4a(src, dst, bitrate):
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-ac", "1", "-ar", "24000",
         "-c:a", "aac", "-b:a", bitrate, "-movflags", "+faststart", str(dst)],
        capture_output=True, text=True)
    if r.returncode != 0 or not Path(dst).exists():
        sys.exit(f"ERROR: ffmpeg encode failed: {r.stderr[-400:]}")


def duration_s(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def synthesize(text, out_m4a, voice, rate, engine, budget):
    """TTS -> mono AAC, stepping the bitrate down until it fits the MMS budget."""
    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / ("speech.mp3" if engine == "edge" else "speech.wav")
        if engine == "edge":
            try:
                tts_edge(text, raw, voice, rate)
            except Exception as e:
                print(f"edge-tts unavailable ({type(e).__name__}); falling back to offline SAPI.")
                engine, raw = "sapi", Path(td) / "speech.wav"
                tts_sapi(text, raw, rate)
        else:
            tts_sapi(text, raw, rate)

        if not raw.exists() or raw.stat().st_size == 0:
            sys.exit("ERROR: TTS produced no audio.")

        for br in BITRATE_LADDER:
            encode_m4a(raw, out_m4a, br)
            size = out_m4a.stat().st_size
            if size <= budget:
                return size, duration_s(out_m4a), br, engine
            print(f"  {br} -> {size/1000:.0f} KB, over the {budget/1000:.0f} KB budget; reducing.")

    sys.exit(f"ERROR: note is {size/1000:.0f} KB at the lowest bitrate, over the "
             f"{budget/1000:.0f} KB MMS budget. Shorten the text, or send it to a real "
             f"inbox with send_email.py --attach (25 MB there).")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="what to say")
    src.add_argument("--text-file", help="read the text from a file ('-' for stdin)")
    ap.add_argument("--to", nargs="+", default=None,
                    help="recipient(s); defaults to DEFAULT_RECIPIENT from .env")
    ap.add_argument("--voice", default=DEFAULT_VOICE, help=f"edge-tts voice (default {DEFAULT_VOICE})")
    ap.add_argument("--rate", default=None, help="speech rate, e.g. '+15%%' or '-10%%'")
    ap.add_argument("--engine", choices=("edge", "sapi"), default="edge",
                    help="edge = neural but sends text to Microsoft; sapi = offline, robotic")
    ap.add_argument("--subject", default="", help="MMS subject (most carriers show it as a line)")
    ap.add_argument("--budget", type=int, default=MMS_BUDGET, help="max attachment bytes")
    ap.add_argument("--keep", help="also write the .m4a here")
    ap.add_argument("--dry-run", action="store_true", help="build the audio, do not send")
    args = ap.parse_args()

    if args.text_file:
        text = sys.stdin.read() if args.text_file == "-" else Path(args.text_file).read_text(encoding="utf-8")
    else:
        text = args.text
    text = text.strip()
    if not text:
        sys.exit("ERROR: nothing to say.")

    to = args.to or ([os.getenv("DEFAULT_RECIPIENT")] if os.getenv("DEFAULT_RECIPIENT") else None)
    if not to:
        sys.exit("ERROR: no recipient - pass --to or set DEFAULT_RECIPIENT in .env.")

    out = Path(args.keep) if args.keep else Path(tempfile.gettempdir()) / "voice_note.m4a"
    size, dur, br, engine = synthesize(text, out, args.voice, args.rate, args.engine, args.budget)

    print(f"voice note : {dur:.1f}s, {size/1000:.0f} KB, AAC mono @ {br}"
          f" ({'neural ' + args.voice if engine == 'edge' else 'offline SAPI'})")
    print(f"file       : {out}")

    if args.dry_run:
        print("dry-run - not sent.")
        return

    sender, password = os.getenv("GMAIL_ADDRESS"), os.getenv("GMAIL_APP_PASSWORD")
    if not sender or not password:
        sys.exit("ERROR: set GMAIL_ADDRESS and GMAIL_APP_PASSWORD (in .env or environment).")

    if not any(r.endswith(GATEWAYS) for r in to):
        print("NOTE: no recipient looks like a carrier gateway - this will arrive as a "
              "normal email attachment, not an MMS voice note.")

    import smtplib
    msg = build_message(sender, to, args.subject, "", [str(out)])
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(sender, password)
        s.send_message(msg)
    print(f"sent to {', '.join(to)}")


if __name__ == "__main__":
    main()
