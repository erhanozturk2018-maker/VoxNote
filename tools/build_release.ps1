<#
.SYNOPSIS
    Build the VoxNote executable and its installer.

.DESCRIPTION
    1. Runs the automated tests.
    2. Builds dist\VoxNote\VoxNote.exe with PyInstaller (VoxNote.spec).
    3. Compiles dist\installer\VoxNote-Setup-<version>.exe with Inno Setup 6
       (installer\VoxNote.iss), if Inno Setup is installed.

    Run from the project folder with the virtual environment that contains
    the runtime dependencies and PyInstaller:

        .\tools\build_release.ps1

    Use -SkipTests or -SkipInstaller to leave out a step.
#>
param(
    [switch]$SkipTests,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

$version = & $python -c "import app; print(app.APP_VERSION)"
Write-Host "Building VoxNote $version"

if (-not $SkipTests) {
    & $python -m pytest
    if ($LASTEXITCODE -ne 0) { throw "Tests failed; nothing was built." }
}

& $python tools\make_icon.py
if ($LASTEXITCODE -ne 0) { throw "Icon generation failed." }

& $python -m PyInstaller --noconfirm --clean VoxNote.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }
Write-Host "Application folder: $root\dist\VoxNote"

if ($SkipInstaller) { return }

$candidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$iscc = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    Write-Warning "Inno Setup 6 was not found, so no installer was built. Install it with: winget install -e --id JRSoftware.InnoSetup"
    return
}

& $iscc "/DAppVersion=$version" "installer\VoxNote.iss"
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed." }
Write-Host "Installer: $root\dist\installer\VoxNote-Setup-$version.exe"
