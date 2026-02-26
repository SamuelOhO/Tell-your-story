param(
    [string]$FrontendTargetRoot = "C:\tmp\tell_your_story_frontend_verify",
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$repoRoot = Get-RepoRoot
Push-Location $repoRoot
try {
    Write-Host "[1/2] backend tests"
    $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
    $env:UPSTAGE_API_KEY = ""
    $env:OPENAI_API_KEY = ""
    & ".\venv\Scripts\python.exe" -m pytest -q tests
    if ($LASTEXITCODE -ne 0) {
        throw "Backend tests failed."
    }

    if ($SkipFrontend) {
        Write-Host "[2/2] frontend checks skipped by -SkipFrontend"
        exit 0
    }

    Write-Host "[2/2] frontend ci checks"
    New-Item -Path $FrontendTargetRoot -ItemType Directory -Force | Out-Null
    robocopy frontend $FrontendTargetRoot /E /XD node_modules .git frontend .npm-cache-temp | Out-Null

    Push-Location $FrontendTargetRoot
    try {
        npm ci --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) {
            throw "npm ci failed."
        }
        npm run lint
        if ($LASTEXITCODE -ne 0) {
            throw "npm run lint failed."
        }
        npm run build
        if ($LASTEXITCODE -ne 0) {
            throw "npm run build failed."
        }
    }
    finally {
        Pop-Location
    }

    Write-Host "[done] local verification passed"
}
finally {
    Pop-Location
}
