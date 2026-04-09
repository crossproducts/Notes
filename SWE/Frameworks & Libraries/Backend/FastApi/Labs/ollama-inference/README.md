# Ollama Inference API

A FastAPI wrapper around a locally running Ollama instance.

---

## Prerequisites

- Windows 10/11
- PowerShell 5.1+
- Python 3.10+

---

## Step 1 — Start Ollama with Mistral

Open **PowerShell** and run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

> Only needed once. Allows local scripts to run.

Then navigate to this folder and run the setup script:

```powershell
cd path\to\ollama-inference
.\setup_ollama.ps1
```

This will:
1. Download and install Ollama (if not already installed)
2. Pull the `mistral` model (~4GB, one-time download)
3. Start the Ollama server at `http://localhost:11434`

Leave this terminal open — the server must stay running.

---

## Step 2 — Start the FastAPI Server

Open a **second PowerShell terminal** and run:

```powershell
cd path\to\ollama-inference
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

---

## Step 3 — Use the API

### Interactive docs (Swagger UI)

Open your browser and go to:

```
http://localhost:8000/docs
```

### Example requests

**List available models:**
```powershell
curl http://localhost:8000/models
```

**Chat (single turn):**
```powershell
curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d '{"model": "mistral", "prompt": "What is machine learning?"}'
```

**Raw completion:**
```powershell
curl -X POST http://localhost:8000/generate `
  -H "Content-Type: application/json" `
  -d '{"model": "mistral", "prompt": "Once upon a time"}'
```

**Streaming response:**
```powershell
curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d '{"model": "mistral", "prompt": "Explain gravity", "stream": true}'
```

---

## Project Structure

```
ollama-inference/
├── main.py              # FastAPI app
├── requirements.txt     # Python dependencies
├── setup_ollama.ps1     # Ollama install + serve script
└── README.md
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ollama is not running` error | Make sure `setup_ollama.ps1` is still running in the other terminal |
| Script blocked by PowerShell | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` first |
| Port 11434 already in use | Ollama is already running — skip to Step 2 |
| Port 8000 already in use | Use `uvicorn main:app --reload --port 8001` |
| Model not found | Run `ollama pull mistral` manually in a terminal |
