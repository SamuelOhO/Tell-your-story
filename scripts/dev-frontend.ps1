param(
    [string]$TargetRoot = "C:\tmp\tell_your_story_frontend",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$source = Join-Path $PSScriptRoot "..\frontend"
$source = (Resolve-Path $source).Path

if (Test-Path $TargetRoot) {
    Write-Host "[info] reusing existing target: $TargetRoot"
} else {
    New-Item -ItemType Directory -Path $TargetRoot | Out-Null
}

Write-Host "[info] syncing frontend to ASCII path..."
robocopy $source $TargetRoot /E /XD node_modules .git frontend .npm-cache-temp | Out-Null

Push-Location $TargetRoot
try {
    if (-not $SkipInstall) {
        Write-Host "[info] npm install"
        npm install --no-audit --no-fund
    }

    Write-Host "[info] npm run dev"
    npm run dev
} finally {
    Pop-Location
}
