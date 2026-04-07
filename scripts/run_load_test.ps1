$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root 'backend'
$hostUrl = if ($args.Count -gt 0) { $args[0] } else { 'http://localhost:8000' }
$users = if ($env:USERS) { $env:USERS } else { '70' }
$spawnRate = if ($env:SPAWN_RATE) { $env:SPAWN_RATE } else { '10' }
$duration = if ($env:DURATION) { $env:DURATION } else { '15m' }
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outDir = Join-Path $root "reports/load/$stamp"

New-Item -ItemType Directory -Path $outDir -Force | Out-Null

Push-Location $backend
try {
    python -m pip install -r requirements-loadtest.txt
    python -m locust -f locustfile.py --host $hostUrl --headless -u $users -r $spawnRate -t $duration --html (Join-Path $outDir 'locust-report.html') --csv (Join-Path $outDir 'locust') --only-summary
}
finally {
    Pop-Location
}

Write-Host "[load-test] report generated at: $outDir"
