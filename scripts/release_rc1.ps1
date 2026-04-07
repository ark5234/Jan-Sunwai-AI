$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$tag = if ($args.Count -gt 0) { $args[0] } else { 'v1.0-rc1' }

Push-Location $root
try {
    Write-Host '[release] running backend tests'
    $env:PYTHONPATH = Join-Path $root 'backend'
    python -m pytest backend/tests -q

    Write-Host '[release] running frontend lint/build'
    Push-Location frontend
    npm run lint
    npm run build
    Pop-Location

    git rev-parse $tag *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[release] tag already exists: $tag"
        exit 0
    }

    git tag -a $tag -m "Release candidate $tag"
    Write-Host "[release] created local tag: $tag"
    Write-Host "[release] push with: git push origin $tag"
}
finally {
    Pop-Location
}
