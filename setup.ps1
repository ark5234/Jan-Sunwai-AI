# =============================================================================
#  Jan-Sunwai AI — One-Shot Setup Script (Windows)
#  Run from the project root after unzipping:
#
#      Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#      .\setup.ps1
#
#  Prerequisites (must already be on the machine):
#      - NVIDIA drivers (for GPU acceleration via Ollama)
#      - Internet connection
# =============================================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

function Write-Step($msg) { Write-Host "`n>>> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  !!  $msg" -ForegroundColor Yellow }

Write-Host "`n============================================" -ForegroundColor Magenta
Write-Host "  Jan-Sunwai AI — Setup" -ForegroundColor Magenta
Write-Host "============================================`n" -ForegroundColor Magenta

# ── 0. GPU Check ──────────────────────────────────────────────────────────────
Write-Step "Running GPU check..."
& (Join-Path $ProjectRoot "check_gpu.ps1")

# ── 1. Python ─────────────────────────────────────────────────────────────────
Write-Step "Checking Python..."
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Warn "Python not found. Installing via winget..."
    winget install -e --id Python.Python.3.13 --silent --accept-package-agreements --accept-source-agreements
    $env:PATH += ";$env:LOCALAPPDATA\Programs\Python\Python313;$env:LOCALAPPDATA\Programs\Python\Python313\Scripts"
} else {
    Write-Ok "Python found: $($py.Source)"
}

# ── 2. Python venv + dependencies ─────────────────────────────────────────────
Write-Step "Setting up Python virtual environment..."
$venvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
    Write-Ok "Created .venv"
} else {
    Write-Ok ".venv already exists"
}

$pip = Join-Path $venvPath "Scripts\pip.exe"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
Write-Step "Installing Python dependencies..."
& $pip install --upgrade pip --quiet
& $pip install -r (Join-Path $ProjectRoot "backend\requirements.txt")
Write-Ok "Python dependencies installed"

# ── 3. Node.js ────────────────────────────────────────────────────────────────
Write-Step "Checking Node.js..."
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Warn "Node.js not found. Installing via winget..."
    winget install -e --id OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
    $env:PATH += ";$env:ProgramFiles\nodejs"
} else {
    Write-Ok "Node.js found: $(node --version)"
}

# ── 4. Frontend npm install ───────────────────────────────────────────────────
Write-Step "Installing frontend dependencies..."
Push-Location (Join-Path $ProjectRoot "frontend")
npm install
Pop-Location
Write-Ok "Frontend dependencies installed"

# ── 5. Docker Desktop ─────────────────────────────────────────────────────────
Write-Step "Checking Docker..."
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    Write-Warn "Docker not found. Installing Docker Desktop via winget..."
    winget install -e --id Docker.DockerDesktop --silent --accept-package-agreements --accept-source-agreements
    Write-Warn "Docker Desktop installed. You may need to RESTART your machine and re-run this script."
    Write-Warn "After restart, run: docker-compose up -d mongodb"
    Write-Host "`nPress any key to continue setup anyway..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} else {
    Write-Ok "Docker found: $(docker --version)"
}

# ── 6. Start MongoDB via Docker Compose ───────────────────────────────────────
Write-Step "Starting MongoDB via Docker Compose..."
try {
    Push-Location $ProjectRoot
    docker compose up -d mongodb
    Pop-Location
    Write-Ok "MongoDB container is running on port 27017"
} catch {
    Write-Warn "Could not start MongoDB container: $_"
    Write-Warn "Run manually after Docker starts: docker compose up -d mongodb"
}

# ── 7. Ollama ─────────────────────────────────────────────────────────────────
Write-Step "Checking Ollama..."
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Warn "Ollama not found. Downloading installer..."
    $ollamaInstaller = Join-Path $env:TEMP "OllamaSetup.exe"
    Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile $ollamaInstaller
    Write-Warn "Running Ollama installer (follow prompts)..."
    Start-Process $ollamaInstaller -Wait
    $env:PATH += ";$env:LOCALAPPDATA\Programs\Ollama"
    Write-Ok "Ollama installed"
} else {
    Write-Ok "Ollama found: $(ollama --version)"
}

# ── 8. Start Ollama service ───────────────────────────────────────────────────
Write-Step "Starting Ollama service..."
$ollamaRunning = $false
try {
    Invoke-RestMethod http://localhost:11434/api/tags | Out-Null
    $ollamaRunning = $true
    Write-Ok "Ollama already running"
} catch {
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 4
    try {
        Invoke-RestMethod http://localhost:11434/api/tags | Out-Null
        $ollamaRunning = $true
        Write-Ok "Ollama started"
    } catch {
        Write-Warn "Ollama did not start in time. Models will be pulled but may require Ollama to be started manually."
    }
}

# ── 9. Pull Ollama models ─────────────────────────────────────────────────────
Write-Step "Pulling AI models (this downloads ~4.5 GB — please wait)..."
Write-Host "  Pulling qwen2.5vl:3b (Vision model — 3.2 GB)..." -ForegroundColor Gray
ollama pull qwen2.5vl:3b
Write-Ok "qwen2.5vl:3b ready"

Write-Host "  Pulling llama3.2:1b (Reasoning model — 1.3 GB)..." -ForegroundColor Gray
ollama pull llama3.2:1b
Write-Ok "llama3.2:1b ready"

# ── 10. Summary ───────────────────────────────────────────────────────────────
Write-Host "`n============================================" -ForegroundColor Magenta
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Magenta
Write-Host @"

To START the project, open 3 terminals:

  Terminal 1 — MongoDB (Docker):
      docker compose up -d mongodb

  Terminal 2 — Backend:
      scripts\run_backend.bat

  Terminal 3 — Frontend:
      scripts\run_frontend.bat

Then open: http://localhost:5173

"@ -ForegroundColor White
