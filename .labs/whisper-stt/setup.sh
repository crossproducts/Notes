#!/usr/bin/env bash
# Idempotent setup for whisper-stt lab.
# Creates .venv (Python 3.10) and installs requirements.
# Windows: venv python lives at .venv/Scripts/python.exe

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$LAB_DIR"

VENV_PYTHON=".venv/Scripts/python.exe"

echo "==> whisper-stt setup"

# ── Create venv ──────────────────────────────────────────────────────────────
if [ ! -f "$VENV_PYTHON" ]; then
    echo "--> Creating .venv with host python..."
    python -m venv .venv
else
    echo "--> .venv already exists, skipping creation."
fi

# ── Upgrade pip ──────────────────────────────────────────────────────────────
echo "--> Upgrading pip..."
"$VENV_PYTHON" -m pip install --upgrade pip --quiet

# ── Install requirements ─────────────────────────────────────────────────────
echo "--> Installing requirements (this may take several minutes — torch is large)..."
"$VENV_PYTHON" -m pip install -r requirements.txt --quiet

# ── Print versions ───────────────────────────────────────────────────────────
echo ""
echo "==> Installed versions:"
"$VENV_PYTHON" - <<'EOF'
import importlib, sys

packages = {
    "whisper":         "openai-whisper",
    "faster_whisper":  "faster-whisper",
    "sounddevice":     "sounddevice",
    "soundfile":       "soundfile",
    "torch":           "torch",
}

for mod, label in packages.items():
    try:
        m = importlib.import_module(mod)
        ver = getattr(m, "__version__", "?")
        print(f"  {label:<20} {ver}")
    except ImportError:
        print(f"  {label:<20} NOT FOUND")

print(f"  {'python':<20} {sys.version.split()[0]}")
EOF

echo ""
echo "==> Setup complete. Activate with: source .venv/Scripts/activate"
