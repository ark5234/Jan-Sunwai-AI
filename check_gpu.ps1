# =============================================================================
#  Jan-Sunwai AI — GPU Check & Driver Setup
#  Automatically called by setup.ps1
#  Can also be run standalone: .\check_gpu.ps1
# =============================================================================

function Write-Step($msg) { Write-Host "`n>>> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  !!  $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "  XX  $msg" -ForegroundColor Red }

Write-Host "`n============================================" -ForegroundColor Magenta
Write-Host "  GPU Check" -ForegroundColor Magenta
Write-Host "============================================`n" -ForegroundColor Magenta

# ── Detect GPU ────────────────────────────────────────────────────────────────
Write-Step "Scanning for GPU..."

$gpus = Get-WmiObject Win32_VideoController | Select-Object -Property Name, DriverVersion, Status
$nvidiaGpu = $gpus | Where-Object { $_.Name -match "NVIDIA" }
$amdGpu    = $gpus | Where-Object { $_.Name -match "AMD|Radeon" }
$intelGpu  = $gpus | Where-Object { $_.Name -match "Intel" }

foreach ($gpu in $gpus) {
    Write-Host "  Found: $($gpu.Name)  [Driver: $($gpu.DriverVersion)]" -ForegroundColor Gray
}

# ── Check nvidia-smi (confirms driver is functional) ─────────────────────────
$nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue

if ($nvidiaGpu -and $nvidiaSmi) {
    Write-Ok "NVIDIA GPU detected with working drivers."
    Write-Host ""
    nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv,noheader
    Write-Host ""
    Write-Ok "GPU is ready. Ollama will use it automatically."
    exit 0
}

if ($nvidiaGpu -and -not $nvidiaSmi) {
    Write-Warn "NVIDIA GPU detected but drivers may be incomplete (nvidia-smi not found)."
    Write-Warn "GPU: $($nvidiaGpu.Name)"
    $reinstall = $true
} elseif (-not $nvidiaGpu) {
    if ($amdGpu) {
        Write-Warn "AMD GPU detected: $($amdGpu.Name)"
        Write-Warn "Ollama supports AMD via ROCm on Linux only. On Windows, Ollama will use CPU."
    } elseif ($intelGpu) {
        Write-Warn "Intel integrated graphics detected: $($intelGpu.Name)"
        Write-Warn "Ollama will run on CPU — slower but functional."
    } else {
        Write-Warn "No GPU detected at all."
    }
    $reinstall = $false
    $noNvidia = $true
}

# ── Prompt user ───────────────────────────────────────────────────────────────
Write-Host ""
if ($reinstall) {
    Write-Host "  NVIDIA GPU found but drivers appear incomplete." -ForegroundColor Yellow
    Write-Host "  Would you like to install/update NVIDIA drivers now? (Y/N)" -ForegroundColor Yellow
} elseif ($noNvidia) {
    Write-Host "  No NVIDIA GPU found. The project will work on CPU but will be slow." -ForegroundColor Yellow
    Write-Host "  If you have an NVIDIA GPU that wasn't detected, install drivers now? (Y/N)" -ForegroundColor Yellow
} else {
    exit 0
}

$choice = Read-Host "  Your choice"

if ($choice -match "^[Yy]") {

    Write-Step "Attempting NVIDIA driver install..."

    # Try winget first (works on Win11 and updated Win10)
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "  Installing via winget (NVIDIA Display Driver)..." -ForegroundColor Gray
        try {
            winget install -e --id NVIDIA.NVIDIA_Display_Driver --silent --accept-package-agreements --accept-source-agreements
            Write-Ok "NVIDIA driver install initiated via winget."
            Write-Warn "A RESTART may be required after driver install."
            Write-Warn "After restarting, re-run setup.ps1 to continue."
        } catch {
            Write-Warn "winget install failed: $_"
            Write-Warn "Falling back to manual download..."
            Start-Process "https://www.nvidia.com/en-us/drivers/"
            Write-Host ""
            Write-Host "  The NVIDIA driver download page has been opened in your browser." -ForegroundColor Yellow
            Write-Host "  1. Select your GPU model and download the driver." -ForegroundColor White
            Write-Host "  2. Install it, restart your machine." -ForegroundColor White
            Write-Host "  3. Then re-run setup.ps1" -ForegroundColor White
        }
    } else {
        # No winget — open browser
        Write-Warn "winget not available. Opening NVIDIA driver download page..."
        Start-Process "https://www.nvidia.com/en-us/drivers/"
        Write-Host ""
        Write-Host "  1. Select your GPU model and download the driver." -ForegroundColor White
        Write-Host "  2. Install it, restart your machine." -ForegroundColor White
        Write-Host "  3. Then re-run setup.ps1" -ForegroundColor White
    }

} else {
    Write-Host ""
    if ($noNvidia) {
        Write-Ok "Continuing without NVIDIA GPU. Ollama will run on CPU."
        Write-Warn "Expect ~2-5 minutes per image instead of ~5-10 seconds."
    } else {
        Write-Ok "Skipping driver install. Continuing setup..."
    }
}

Write-Host ""
