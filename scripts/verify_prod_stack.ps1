$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    Write-Host '[prod-verify] bringing up production compose stack'
    docker compose --profile prod up -d --build

    Write-Host '[prod-verify] checking backend live endpoint'
    $ready = $false
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt 40) {
        try {
            $r = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/health/live' -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) {
                $ready = $true
                break
            }
        }
        catch {
            # retry
        }
    }
    if (-not $ready) {
        throw 'Backend health endpoint did not become ready in time.'
    }

    Write-Host '[prod-verify] checking SPA deep-link fallback'
    $deep = Invoke-WebRequest -Uri 'http://localhost:5173/dashboard' -UseBasicParsing -TimeoutSec 10
    if ($deep.StatusCode -ne 200) {
        throw "SPA deep-link check failed with status $($deep.StatusCode)"
    }
    if ($deep.Content -notmatch '<html') {
        throw 'SPA deep-link did not return HTML shell.'
    }

    Write-Host '[prod-verify] checking backend-to-ollama network route'
    docker compose --profile prod exec -T backend python -c "import os,urllib.request;u=os.getenv('OLLAMA_BASE_URL','http://host.docker.internal:11434').rstrip('/')+'/api/tags';urllib.request.urlopen(u,timeout=5);print('ok')"

    Write-Host '[prod-verify] running short load smoke against production stack'
    $env:USERS = if ($env:USERS) { $env:USERS } else { '20' }
    $env:SPAWN_RATE = if ($env:SPAWN_RATE) { $env:SPAWN_RATE } else { '5' }
    $env:DURATION = if ($env:DURATION) { $env:DURATION } else { '2m' }
    powershell -ExecutionPolicy Bypass -File scripts/run_load_test.ps1 'http://localhost:8000'

    Write-Host '[prod-verify] PASS'
}
finally {
    Pop-Location
}
