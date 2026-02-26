param(
    [string]$DbPath,
    [string]$BackupDir = "backups",
    [string]$RestoreFrom
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

$dbPathValue = $DbPath
if (-not $dbPathValue) {
    $dbPathValue = Get-DbPathFromEnv -RepoRoot $repoRoot
}
if (-not $dbPathValue) {
    $dbPathValue = "backend/data/tell_your_story.db"
}

$dbFile = Resolve-AppPath -RepoRoot $repoRoot -PathValue $dbPathValue
$backupDirResolved = Resolve-AppPath -RepoRoot $repoRoot -PathValue $BackupDir
New-Item -Path $backupDirResolved -ItemType Directory -Force | Out-Null

if ($RestoreFrom) {
    $restoreSource = Resolve-AppPath -RepoRoot $repoRoot -PathValue $RestoreFrom
    if (-not (Test-Path $restoreSource)) {
        throw "Restore source not found: $restoreSource"
    }
    $dbDir = Split-Path -Parent $dbFile
    New-Item -Path $dbDir -ItemType Directory -Force | Out-Null
    Copy-Item -Path $restoreSource -Destination $dbFile -Force
    Write-Output "RESTORE_SOURCE=$restoreSource"
    Write-Output "RESTORE_TARGET=$dbFile"
    exit 0
}

if (-not (Test-Path $dbFile)) {
    throw "DB file not found: $dbFile"
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$baseName = [System.IO.Path]::GetFileNameWithoutExtension($dbFile)
$extension = [System.IO.Path]::GetExtension($dbFile)
if (-not $extension) {
    $extension = ".db"
}
$backupFile = Join-Path $backupDirResolved "$baseName`_$timestamp$extension"
Copy-Item -Path $dbFile -Destination $backupFile -Force

$sourceSize = (Get-Item $dbFile).Length
$backupSize = (Get-Item $backupFile).Length
if ($sourceSize -ne $backupSize) {
    throw "Backup size mismatch. source=$sourceSize backup=$backupSize"
}

Write-Output "DB_FILE=$dbFile"
Write-Output "BACKUP_FILE=$backupFile"
Write-Output "BACKUP_SIZE=$backupSize"
