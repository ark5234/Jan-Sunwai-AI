$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

function Write-Step($msg) { Write-Host "`n>>> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  !!  $msg" -ForegroundColor Yellow }

Write-Host "`n============================================" -ForegroundColor Magenta
Write-Host "  Jan-Sunwai AI — Setup" -ForegroundColor Magenta
Write-Host "============================================`n" -ForegroundColor Magenta

Write-Step "Running GPU check..."
& (Join-Path $ProjectRoot "scripts\system\check_gpu.ps1")

Write-Step "Checking Python..."
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Warn "Python not found. Installing via winget..."
    winget install -e --id Python.Python.3.13 --silent --accept-package-agreements --accept-source-agreements
    $env:PATH += ";$env:LOCALAPPDATA\Programs\Python\Python313;$env:LOCALAPPDATA\Programs\Python\Python313\Scripts"
} else {
    Write-Ok "Python found: $($py.Source)"
}

Write-Step "Setting up Python virtual environment..."
$venvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
    Write-Ok "Created .venv"
} else {
    Write-Ok ".venv already exists"
}

$pip = Join-Path $venvPath "Scripts\pip.exe"
Write-Step "Installing Python dependencies..."
& $pip install --upgrade pip --quiet
& $pip install -r (Join-Path $ProjectRoot "backend\requirements.txt")
Write-Ok "Python dependencies installed"

Write-Step "Ensuring backend environment file..."
$envFile = Join-Path $ProjectRoot "backend\.env"
if (-not (Test-Path $envFile)) {
    Write-Warn "backend/.env not found. Create backend/.env manually before running the backend."
} else {
    Write-Ok "backend/.env already exists"
}

Write-Step "Checking Node.js..."
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Warn "Node.js not found. Installing via winget..."
    winget install -e --id OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
    $env:PATH += ";$env:ProgramFiles\nodejs"
} else {
    Write-Ok "Node.js found: $(node --version)"
}

Write-Step "Installing frontend dependencies..."
Push-Location (Join-Path $ProjectRoot "frontend")
npm install
Pop-Location
Write-Ok "Frontend dependencies installed"

Write-Step "Checking Docker..."
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    Write-Warn "Docker not found. Installing Docker Desktop via winget..."
    winget install -e --id Docker.DockerDesktop --silent --accept-package-agreements --accept-source-agreements
    Write-Warn "Docker Desktop installed. You may need to RESTART your machine and re-run this script."
    Write-Warn "After restart, run: docker compose up -d mongodb"
    Write-Host "`nPress any key to continue setup anyway..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} else {
    Write-Ok "Docker found: $(docker --version)"
}

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

Write-Step "Starting Ollama service..."
try {
    Invoke-RestMethod http://localhost:11434/api/tags | Out-Null
    Write-Ok "Ollama already running"
} catch {
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 4
    try {
        Invoke-RestMethod http://localhost:11434/api/tags | Out-Null
        Write-Ok "Ollama started"
    } catch {
        Write-Warn "Ollama did not start in time. Models will be pulled but may require Ollama to be started manually."
    }
}

Write-Step "Pulling AI models (reads model names from backend/.env)..."
& "$PSScriptRoot\.venv\Scripts\python.exe" "$PSScriptRoot\backend\download_models.py"
if ($LASTEXITCODE -ne 0) { Write-Warn "Model pull failed. Run manually: python backend/download_models.py" }

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
