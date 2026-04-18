$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    python scripts/run_cookie_smoke_test.py @args
}
finally {
    Pop-Location
}
