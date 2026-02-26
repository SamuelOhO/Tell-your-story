param(
    [string]$DbPath
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Get-DbPathFromEnv {
    param([string]$RepoRoot)

    $envFile = Join-Path $RepoRoot "backend\.env"
    if (-not (Test-Path $envFile)) {
        return $null
    }

    $line = Get-Content $envFile | Where-Object { $_ -match "^\s*DB_PATH\s*=" } | Select-Object -First 1
    if (-not $line) {
        return $null
    }

    $value = ($line -split "=", 2)[1].Trim()
    if (-not $value) {
        return $null
    }
    return $value.Trim('"')
}

function Resolve-AppPath {
    param(
        [string]$RepoRoot,
        [string]$PathValue
    )

    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }

    return [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $PathValue))
}

$repoRoot = Get-RepoRoot
$resolvedDbPathValue = $DbPath
if (-not $resolvedDbPathValue) {
    $resolvedDbPathValue = Get-DbPathFromEnv -RepoRoot $repoRoot
}
if (-not $resolvedDbPathValue) {
    $resolvedDbPathValue = "backend/data/tell_your_story.db"
}

$dbFile = Resolve-AppPath -RepoRoot $repoRoot -PathValue $resolvedDbPathValue
$dbDir = Split-Path -Parent $dbFile

if (-not (Test-Path $dbDir)) {
    New-Item -Path $dbDir -ItemType Directory -Force | Out-Null
}

$probePath = Join-Path $dbDir ".write-probe.tmp"
try {
    "probe" | Set-Content -Path $probePath -Encoding UTF8
    Remove-Item -Path $probePath -Force -ErrorAction SilentlyContinue
}
catch {
    throw "DB directory is not writable: $dbDir"
}

$exists = Test-Path $dbFile
if ($exists) {
    try {
        $stream = [System.IO.File]::Open($dbFile, "Open", "Read", "ReadWrite")
        $stream.Close()
    }
    catch {
        throw "DB file exists but cannot be read: $dbFile"
    }
}

Write-Output "DB_PATH_VALUE=$resolvedDbPathValue"
Write-Output "DB_FILE=$dbFile"
Write-Output "DB_DIR=$dbDir"
Write-Output "DB_FILE_EXISTS=$exists"
Write-Output "DB_DIR_WRITABLE=True"
