$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    Write-Host '[deploy-sim] validating prerequisites'
    foreach ($cmd in @('git', 'docker', 'python', 'node', 'npm')) {
        if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
            throw "Missing required command: $cmd"
        }
    }

    if (-not (Test-Path 'backend/.env')) {
        throw '[deploy-sim] backend/.env is missing. Create backend/.env before running deployment simulation.'
    }

    Write-Host '[deploy-sim] validating compose config'
    docker compose --profile prod config -q

    Write-Host '[deploy-sim] measuring cold start'
    $start = Get-Date
    docker compose --profile prod up -d --build
    $elapsed = (Get-Date) - $start
    Write-Host "[deploy-sim] cold-start seconds: $([math]::Round($elapsed.TotalSeconds, 2))"

    Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/health/live' -UseBasicParsing -TimeoutSec 10 | Out-Null
    Invoke-WebRequest -Uri 'http://localhost:5173' -UseBasicParsing -TimeoutSec 10 | Out-Null

    Write-Host '[deploy-sim] PASS'
}
finally {
    Pop-Location
}
