# Explainer Video

Turns a Python "deck" into a narrated MP4. Written to learn things properly:
a diagram you read is skimmed, a diagram someone talks you through is not.

Each scene is one still frame held for exactly as long as its narration line,
so picture and voice cannot drift out of sync.

```bash
python build.py decks/crypto_aws.py
# -> out/certificates-mtls-kms.mp4
```

## Decks

| Deck | Covers |
|---|---|
| [`decks/crypto_aws.py`](decks/crypto_aws.py) | Certificates, chain of trust, TLS vs mTLS, envelope encryption, HSMs, and how all of it maps onto ACM, AWS Private CA, KMS and CloudHSM |

A deck is a module exposing `TITLE`, `SLUG`, optional `VOICE`, and `SCENES` —
a list of `{"narration": str, "html": str}`. The HTML is the body of a
1920×1080 slide; `build.py` supplies the stylesheet, so a scene is usually
three or four `<div class='card'>`s and a headline.

```bash
python build.py decks/crypto_aws.py --scene 11   # render one frame to out/preview.png
```

That flag is the fast iteration loop — no TTS, no encode, about two seconds.

## Text to speech

| Engine | Quality | Local? | Notes |
|---|---|---|---|
| **`kokoro`** (default) | very good | **yes** | Kokoro-82M via onnxruntime. Apache-2.0, 54 voices, ~2.4× realtime on an i9 CPU, no GPU needed |
| `edge` | excellent | no | Microsoft neural voices. **Sends the narration text to a Microsoft endpoint** |
| `sapi` | poor | yes | The built-in Windows voice. Instant, robotic, zero setup |

```bash
python build.py decks/crypto_aws.py --engine sapi --rate -10%
python build.py decks/crypto_aws.py --voice bm_george    # British male
```

Kokoro voice names are `{a|b}{f|m}_name` — `a`/`b` for American/British,
`f`/`m` for the voice's gender. `am_michael`, `af_heart`, `bm_george` and
`bf_emma` are good starting points; `python -c "from kokoro_onnx import
Kokoro; print(Kokoro('models/kokoro-v1.0.onnx','models/voices-v1.0.bin')
.get_voices())"` lists all 54.

### Why not Coqui

It comes up every time, so: Coqui the company shut down in January 2024 and
`coqui-ai/TTS` is archived. Its best model, XTTS-v2, is ~1.8 GB, wants a GPU to
hit realtime, and ships under a **non-commercial** model licence. Kokoro is
~340 MB, permissively licensed, and beats it on quality-per-megabyte by a wide
margin. If you later want zero-shot voice *cloning* specifically, look at
F5-TTS or Chatterbox rather than going back to XTTS.

## Setup

```bash
pip install kokoro-onnx soundfile          # local TTS
pip install edge-tts                       # only for --engine edge
playwright install chromium                # already installed by audio-extraction
```

Then fetch the Kokoro weights into `models/` (~340 MB, gitignored):

```bash
B=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
curl -sSL -o models/kokoro-v1.0.onnx  $B/kokoro-v1.0.onnx
curl -sSL -o models/voices-v1.0.bin   $B/voices-v1.0.bin
```

`ffmpeg` and `ffprobe` must be on PATH — the extraction pipeline already needs
them, so on this machine they are.

## How it works

```
deck.py ──┬── html ──> Playwright Chromium ──> frame_NNN.png  (1920x1080)
          │
          └── narration ──> Kokoro ──> vo_NNN.mp3 ──> +0.55s silence
                                              │
                            ffprobe duration ─┘
                                              │
     ffmpeg concat demuxer (frame + its exact duration) + concatenated audio
                                              │
                                              └──> out/<slug>.mp4  (H.264 + AAC)
```

Nothing here is new infrastructure: Chromium comes from the extraction
pipeline, the TTS idea and the SAPI fallback come from
[`../email-sender/send_voice.py`](../email-sender/send_voice.py), and ffmpeg is
already load-bearing in three other labs.

`models/` and `out/` are gitignored — the weights are re-downloadable and the
video is fully regenerable from the deck, which is the actual source.
