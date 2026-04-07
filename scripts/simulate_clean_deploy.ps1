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
        Write-Host '[deploy-sim] backend/.env missing; copying backend/env.production'
        Copy-Item 'backend/env.production' 'backend/.env'
    }

    Write-Host '[deploy-sim] validating compose config'
    docker compose -f docker-compose.prod.yml config -q

    Write-Host '[deploy-sim] measuring cold start'
    $start = Get-Date
    docker compose -f docker-compose.prod.yml up -d --build
    $elapsed = (Get-Date) - $start
    Write-Host "[deploy-sim] cold-start seconds: $([math]::Round($elapsed.TotalSeconds, 2))"

    Invoke-WebRequest -Uri 'http://localhost:8000/health/live' -UseBasicParsing -TimeoutSec 10 | Out-Null
    Invoke-WebRequest -Uri 'http://localhost:5173' -UseBasicParsing -TimeoutSec 10 | Out-Null

    Write-Host '[deploy-sim] PASS'
}
finally {
    Pop-Location
}
