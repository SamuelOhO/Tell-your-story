[CmdletBinding()]
param(
    [switch]$UseAsciiFrontend,
    [string]$FrontendTargetRoot = "C:\tmp\tell_your_story_frontend",
    [switch]$SkipFrontendInstall
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Start-TerminalProcess {
    param([string]$Title, [string]$Command)
    $wrapped = @"
`$Host.UI.RawUI.WindowTitle = '$Title'
$Command
"@
    return Start-Process powershell -PassThru -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", $wrapped
    )
}

$repoRoot = Get-RepoRoot
$pythonExe = Join-Path $repoRoot "venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "Python venv not found: $pythonExe"
}

$backendCommand = @"
Set-Location '$repoRoot'
& '$pythonExe' -m uvicorn backend.main:app --reload
"@

if ($UseAsciiFrontend) {
    $frontendCommand = "Set-Location '$repoRoot'; & '.\scripts\dev-frontend.ps1' -TargetRoot '$FrontendTargetRoot'"
    if ($SkipFrontendInstall) {
        $frontendCommand += " -SkipInstall"
    }
}
else {
    $frontendCommand = @"
Set-Location '$repoRoot\frontend'
npm run dev
"@
}

$be = Start-TerminalProcess -Title "TellYourStory Backend" -Command $backendCommand
$fe = Start-TerminalProcess -Title "TellYourStory Frontend" -Command $frontendCommand

Write-Host "[started] backend pid: $($be.Id)"
Write-Host "[started] frontend pid: $($fe.Id)"
Write-Host "[info] close each terminal window to stop dev servers."
