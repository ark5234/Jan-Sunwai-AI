$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $root 'frontend'

Push-Location $frontend
try {
    Write-Host '[perf] installing frontend dependencies'
    npm install

    Write-Host '[perf] building production bundle'
    npm run build:prod

    Write-Host '[perf] starting preview server'
    $preview = Start-Process -FilePath npm -ArgumentList 'run', 'preview:ci' -PassThru -WindowStyle Hidden

    $ready = $false
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    while ($stopwatch.Elapsed.TotalSeconds -lt 30) {
        try {
            $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:4173' -UseBasicParsing -TimeoutSec 2
            if ($resp.StatusCode -eq 200) {
                $ready = $true
                break
            }
        }
        catch {
            # keep retrying until timeout
        }
    }

    if (-not $ready) {
        throw 'Preview server did not become ready in 30 seconds.'
    }

    Write-Host '[perf] running lighthouse'
    npm run perf:lighthouse

    $reportPath = Join-Path $frontend 'lighthouse-report.json'
    if (-not (Test-Path $reportPath)) {
        throw 'Lighthouse report was not generated.'
    }

    $report = Get-Content $reportPath -Raw | ConvertFrom-Json
    $score = [math]::Round(($report.categories.performance.score * 100), 0)
    Write-Host "[perf] Lighthouse performance score: $score"

    if ($score -lt 80) {
        throw "Lighthouse score below target (80): $score"
    }

    Write-Host '[perf] PASS'
}
finally {
    if ($preview -and -not $preview.HasExited) {
        Stop-Process -Id $preview.Id -Force
    }
    Pop-Location
}
