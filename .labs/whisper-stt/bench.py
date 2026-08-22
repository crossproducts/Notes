"""
bench.py — compare openai-whisper vs faster-whisper on the same audio file.

Usage:
    python bench.py AUDIO.wav
    python bench.py AUDIO.wav --model small
"""

import argparse
import os
import subprocess
import sys
import tempfile
import time

import numpy as np
import soundfile as sf

SAMPLE_RATE = 16_000


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def load_wav(path: str) -> np.ndarray:
    """Load audio, resample to 16 kHz mono float32 if needed."""
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    if data.shape[1] > 1:
        data = data.mean(axis=1)
    else:
        data = data[:, 0]
    if sr != SAMPLE_RATE:
        eprint(f"[bench] Resampling {sr} Hz → {SAMPLE_RATE} Hz via ffmpeg...")
        data = _resample_via_ffmpeg(path)
    return data


def _resample_via_ffmpeg(path: str) -> np.ndarray:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", path, "-ar", str(SAMPLE_RATE), "-ac", "1",
             "-f", "wav", tmp_path],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        data, _ = sf.read(tmp_path, dtype="float32")
        return data
    finally:
        os.unlink(tmp_path)


def bench_faster(audio: np.ndarray, model_size: str) -> dict:
    from faster_whisper import WhisperModel

    t0 = time.perf_counter()
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    load_time = time.perf_counter() - t0

    t1 = time.perf_counter()
    segments, _info = model.transcribe(audio, language=None, beam_size=5)
    transcript = " ".join(seg.text.strip() for seg in segments).strip()
    transcribe_time = time.perf_counter() - t1

    return {
        "engine": f"faster-whisper/{model_size}",
        "load_s": load_time,
        "transcribe_s": transcribe_time,
        "transcript": transcript,
    }


def bench_openai(audio: np.ndarray, model_size: str) -> dict:
    import whisper

    t0 = time.perf_counter()
    model = whisper.load_model(model_size, device="cpu")
    load_time = time.perf_counter() - t0

    t1 = time.perf_counter()
    result = model.transcribe(audio, fp16=False)
    transcript = result["text"].strip()
    transcribe_time = time.perf_counter() - t1

    return {
        "engine": f"openai-whisper/{model_size}",
        "load_s": load_time,
        "transcribe_s": transcribe_time,
        "transcript": transcript,
    }


def print_table(rows: list[dict]) -> None:
    eng_w = max(len(r["engine"]) for r in rows)
    tx_w  = max(len(r["transcript"]) for r in rows)
    tx_w  = min(tx_w, 60)  # cap column width for readability

    header = (
        f"{'engine':<{eng_w}}  "
        f"{'load (s)':>8}  "
        f"{'transcribe (s)':>14}  "
        f"transcript"
    )
    sep = "-" * (eng_w + 8 + 14 + tx_w + 10)

    print()
    print(header)
    print(sep)
    for r in rows:
        tx = r["transcript"]
        if len(tx) > tx_w:
            tx = tx[:tx_w - 3] + "..."
        print(
            f"{r['engine']:<{eng_w}}  "
            f"{r['load_s']:>8.2f}  "
            f"{r['transcribe_s']:>14.2f}  "
            f"{tx}"
        )
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark faster-whisper vs openai-whisper on a WAV file"
    )
    parser.add_argument("wav", metavar="AUDIO.wav", help="Path to audio file")
    parser.add_argument(
        "--model", default="base",
        choices=["tiny", "base", "small", "medium"],
        help="Whisper model size (default: base)"
    )
    args = parser.parse_args()

    if not os.path.exists(args.wav):
        print(f"[bench] File not found: {args.wav}", file=sys.stderr)
        sys.exit(1)

    print(f"[bench] Loading {args.wav}...", file=sys.stderr)
    audio = load_wav(args.wav)
    duration = len(audio) / SAMPLE_RATE
    print(f"[bench] Audio: {duration:.1f}s  |  model: {args.model}\n", file=sys.stderr)

    results = []

    print("[bench] Running faster-whisper...", file=sys.stderr)
    results.append(bench_faster(audio, args.model))

    print("[bench] Running openai-whisper...", file=sys.stderr)
    results.append(bench_openai(audio, args.model))

    print_table(results)


if __name__ == "__main__":
    main()
