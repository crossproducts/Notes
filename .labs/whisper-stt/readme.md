# whisper-stt

Dictate into your mic, get clean text on stdout and the Windows clipboard —
ready to paste into Claude Code or pipe into other labs.

Compares two engines: **openai-whisper** (PyTorch) and **faster-whisper**
(CTranslate2 int8, ~4× faster on CPU).

## Layout

```
whisper-stt/
├── requirements.txt   ← openai-whisper, faster-whisper, sounddevice, soundfile
├── setup.sh           ← idempotent venv + install
├── dictate.py         ← mic → transcript → stdout + clipboard
├── bench.py           ← compare both engines on the same file
└── readme.md          ← you are here
```

## Prerequisites

- Python 3.10+ on PATH as `python`
- ffmpeg 4.3+ on PATH (resampling, format conversion)
- Windows 10/11 (`clip` for clipboard; SAPI for test wav generation)
- ~2–3 GB disk for torch + model weights (downloaded on first use)

## Steps

```bash
cd .labs/whisper-stt
bash setup.sh                         # creates .venv, installs deps (~2-3 GB, be patient)
source .venv/Scripts/activate
```

## Verify

### Generate a test wav (no mic needed — uses Windows SAPI TTS)

```bash
powershell.exe -NoProfile -Command "
  Add-Type -AssemblyName System.Speech
  \$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
  \$s.SetOutputToWaveFile('test.wav')
  \$s.Speak('The payment api container keeps restarting because an environment variable is missing.')
  \$s.Dispose()
"
```

### Transcribe with each engine

```bash
python dictate.py --wav test.wav --engine faster   # default
python dictate.py --wav test.wav --engine openai
```

Both should produce a transcript containing "payment" and "restarting".
Check the clipboard:

```powershell
powershell.exe -NoProfile -Command "Get-Clipboard"
```

### Benchmark both engines

```bash
python bench.py test.wav
```

Sample output (base model, CPU):

```
engine                    load (s)  transcribe (s)  transcript
----------------------------------------------------------------------
faster-whisper/base           0.80            1.20  The payment API container ...
openai-whisper/base           2.10            3.80  The payment API container ...
```

## Use it for prompting

### Dictate → clipboard → paste

1. `python dictate.py` — speaks "Recording", wait until you're done, press Enter
2. Transcript appears on stdout and is already in your clipboard
3. Switch to Claude Code, paste

### Pipe to another script

```bash
# Ask holmesgpt with your dictated question
./ask.sh "$(python dictate.py)"

# Or chain into the audio-extraction lab's pipeline
python dictate.py | xargs -I{} python ..//audio-extraction/pipeline.py "{}"
```

### Model size trade-off

| model  | ~size | WER (en) | speed (CPU) |
|--------|-------|----------|-------------|
| tiny   | 39 MB | high     | fastest     |
| base   | 74 MB | good     | fast        |
| small  | 244 MB| better   | moderate    |
| medium | 769 MB| best CPU | slow        |

`base` is the default and the right choice for prompting notes.

## GPU (optional)

faster-whisper with CUDA needs cuDNN installed separately:

```bash
python dictate.py --device cuda --engine faster
```

openai-whisper needs a CUDA-enabled torch wheel:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
python dictate.py --device cuda --engine openai
```

Neither is required — CPU int8 (faster-whisper default) is fast enough for
short prompting snippets.

## Teardown

```bash
deactivate
rm -rf .venv

# Remove cached model weights
rm -rf ~/.cache/whisper               # openai-whisper models
rm -rf ~/.cache/huggingface           # faster-whisper models
```
