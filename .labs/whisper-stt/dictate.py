"""
dictate.py — mic → transcript → stdout + Windows clipboard

Usage:
    python dictate.py                          # record from mic, faster-whisper base
    python dictate.py --engine openai          # use openai-whisper
    python dictate.py --model small            # choose model size
    python dictate.py --wav path/to/file.wav   # transcribe existing file, no mic
    python dictate.py --device cuda            # GPU (needs cuDNN / CUDA torch)

The transcript is the only thing written to stdout so you can pipe it:
    echo "$(python dictate.py)" | pbcopy       # macOS example
    python dictate.py | clip                   # Windows (but clipboard is also set automatically)
"""

import argparse
import io
import os
import subprocess
import sys
import tempfile

import numpy as np
import sounddevice as sd
import soundfile as sf

SAMPLE_RATE = 16_000  # Hz — both engines prefer 16 kHz mono


# ── helpers ──────────────────────────────────────────────────────────────────

def eprint(*args, **kwargs):
    """Print to stderr (keeps stdout clean for piping)."""
    print(*args, file=sys.stderr, **kwargs)


def record_mic() -> np.ndarray:
    """Block until Enter is pressed, recording mono 16 kHz audio. Returns float32 array."""
    chunks = []

    def callback(indata, frames, time, status):
        if status:
            eprint(f"[mic] {status}")
        chunks.append(indata.copy())

    eprint("[dictate] Recording — press Enter to stop...")
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                        callback=callback):
        input()  # blocks until Enter

    eprint("[dictate] Recording stopped.")
    if not chunks:
        eprint("[dictate] No audio captured.", file=sys.stderr)
        sys.exit(1)

    audio = np.concatenate(chunks, axis=0).flatten()
    return audio


def load_wav(path: str) -> np.ndarray:
    """Load any wav/audio file and resample to 16 kHz mono float32."""
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    # mix down to mono
    if data.shape[1] > 1:
        data = data.mean(axis=1)
    else:
        data = data[:, 0]
    # resample if needed (simple linear — good enough for speech)
    if sr != SAMPLE_RATE:
        eprint(f"[dictate] Resampling {sr} Hz → {SAMPLE_RATE} Hz via ffmpeg...")
        data = _resample_via_ffmpeg(path)
    return data


def _resample_via_ffmpeg(path: str) -> np.ndarray:
    """Use ffmpeg to resample to 16 kHz mono, return float32 ndarray."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", path, "-ar", str(SAMPLE_RATE), "-ac", "1",
             "-f", "wav", tmp_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        data, _ = sf.read(tmp_path, dtype="float32")
        return data
    finally:
        os.unlink(tmp_path)


def audio_to_wav_bytes(audio: np.ndarray) -> bytes:
    """Encode float32 ndarray as in-memory 16 kHz mono WAV bytes."""
    buf = io.BytesIO()
    sf.write(buf, audio, SAMPLE_RATE, format="WAV", subtype="PCM_16")
    buf.seek(0)
    return buf.read()


def copy_to_clipboard(text: str) -> None:
    """Write text to the Windows clipboard via `clip`. Silently skips on non-Windows."""
    try:
        # clip.exe expects UTF-16 LE with BOM on modern Windows
        proc = subprocess.Popen(
            ["clip"],
            stdin=subprocess.PIPE,
            shell=True,
        )
        proc.communicate(input=text.encode("utf-16-le"))
        eprint("[dictate] Transcript copied to clipboard.")
    except Exception as exc:
        eprint(f"[dictate] Clipboard copy failed (non-fatal): {exc}")


# ── engines ──────────────────────────────────────────────────────────────────

def transcribe_faster(audio: np.ndarray, model_size: str, device: str) -> str:
    from faster_whisper import WhisperModel
    eprint(f"[dictate] Loading faster-whisper/{model_size} on {device} (int8)...")
    model = WhisperModel(model_size, device=device, compute_type="int8")
    eprint("[dictate] Transcribing...")
    segments, _info = model.transcribe(audio, language=None, beam_size=5)
    return " ".join(seg.text.strip() for seg in segments).strip()


def transcribe_openai(audio: np.ndarray, model_size: str, device: str) -> str:
    import whisper
    eprint(f"[dictate] Loading openai-whisper/{model_size} on {device}...")
    model = whisper.load_model(model_size, device=device)
    eprint("[dictate] Transcribing...")
    result = model.transcribe(audio, fp16=False)
    return result["text"].strip()


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Dictate to mic (or transcribe a wav) → stdout + clipboard"
    )
    parser.add_argument(
        "--engine", choices=["faster", "openai"], default="faster",
        help="STT engine (default: faster)"
    )
    parser.add_argument(
        "--model", default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base)"
    )
    parser.add_argument(
        "--device", default="cpu", choices=["cpu", "cuda"],
        help="Compute device (default: cpu)"
    )
    parser.add_argument(
        "--wav", metavar="PATH", default=None,
        help="Transcribe an existing WAV file instead of recording"
    )
    args = parser.parse_args()

    # ── load / record audio ──────────────────────────────────────────────────
    if args.wav:
        eprint(f"[dictate] Loading {args.wav}...")
        audio = load_wav(args.wav)
    else:
        audio = record_mic()

    # ── transcribe ───────────────────────────────────────────────────────────
    if args.engine == "faster":
        transcript = transcribe_faster(audio, args.model, args.device)
    else:
        transcript = transcribe_openai(audio, args.model, args.device)

    # ── output ───────────────────────────────────────────────────────────────
    copy_to_clipboard(transcript)
    print(transcript)  # only line on stdout


if __name__ == "__main__":
    main()
