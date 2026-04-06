$ErrorActionPreference = 'Stop'

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outDir = if ($args.Count -gt 0) { $args[0] } else { ".\backups\mongo_$timestamp" }
$mongoUri = if ($env:MONGODB_URL) { $env:MONGODB_URL } else { 'mongodb://localhost:27017/jan_sunwai_db' }

Write-Host "[backup] creating backup at: $outDir"
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

mongodump --uri="$mongoUri" --out="$outDir"

Write-Host "[backup] completed successfully"
