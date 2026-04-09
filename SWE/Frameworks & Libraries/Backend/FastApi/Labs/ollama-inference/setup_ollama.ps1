# setup_ollama.ps1
# Downloads Ollama, installs it, pulls Mistral, and starts the server.
# Run from PowerShell as a normal user (no admin required for install).

$ErrorActionPreference = "Stop"

# ── 1. Install Ollama if not already installed ────────────────────────────────
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "Ollama not found. Downloading installer..." -ForegroundColor Cyan

    $installer = "$env:TEMP\OllamaSetup.exe"
    Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile $installer

    Write-Host "Running installer (follow any prompts)..." -ForegroundColor Cyan
    Start-Process -FilePath $installer -Wait

    # Refresh PATH so 'ollama' is available in this session
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH", "User")

    if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
        Write-Error "Ollama install failed or PATH not updated. Restart your terminal and re-run this script."
        exit 1
    }

    Write-Host "Ollama installed successfully." -ForegroundColor Green
} else {
    Write-Host "Ollama already installed: $(ollama --version)" -ForegroundColor Green
}

# ── 2. Pull Mistral ───────────────────────────────────────────────────────────
Write-Host "`nPulling mistral model (this may take a few minutes)..." -ForegroundColor Cyan
ollama pull mistral
Write-Host "Mistral ready." -ForegroundColor Green

# ── 3. Start Ollama server ────────────────────────────────────────────────────
Write-Host "`nStarting Ollama server on http://localhost:11434 ..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop.`n" -ForegroundColor Yellow
ollama serve
