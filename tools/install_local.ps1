<#
.SYNOPSIS
    Install the built application for the current user without the setup
    program.

.DESCRIPTION
    Copies dist\VoxNote (created by tools\build_release.ps1) to
    %LOCALAPPDATA%\Programs\VoxNote and creates a desktop and a Start menu
    shortcut. Use this on computers where Windows blocks the unsigned
    installer. Run it again after a new build to update the installation.

        .\tools\install_local.ps1
        .\tools\install_local.ps1 -Uninstall

    Settings, transcripts, logs and downloaded speech models are not touched
    by either command.
#>
param(
    [switch]$Uninstall,
    [switch]$NoDesktopShortcut
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path $root "dist\VoxNote"
$target = Join-Path $env:LOCALAPPDATA "Programs\VoxNote"
$desktop = Join-Path ([Environment]::GetFolderPath("Desktop")) "VoxNote.lnk"
$startMenu = Join-Path ([Environment]::GetFolderPath("Programs")) "VoxNote.lnk"

if (Get-Process VoxNote -ErrorAction SilentlyContinue) {
    throw "VoxNote is running. Close it and run this script again."
}

if ($Uninstall) {
    foreach ($path in $desktop, $startMenu) {
        if (Test-Path $path) { Remove-Item $path }
    }
    if (Test-Path (Join-Path $target "VoxNote.exe")) { Remove-Item $target -Recurse -Force }
    Write-Host "VoxNote was removed. Your settings, transcripts and models were kept."
    return
}

if (-not (Test-Path (Join-Path $source "VoxNote.exe"))) {
    throw "dist\VoxNote\VoxNote.exe was not found. Build it first with tools\build_release.ps1 -SkipInstaller."
}

if (Test-Path (Join-Path $target "VoxNote.exe")) { Remove-Item $target -Recurse -Force }
New-Item -ItemType Directory -Force -Path $target | Out-Null
Copy-Item -Path (Join-Path $source "*") -Destination $target -Recurse -Force

$shell = New-Object -ComObject WScript.Shell
$links = @($startMenu)
if (-not $NoDesktopShortcut) { $links += $desktop }
foreach ($path in $links) {
    $link = $shell.CreateShortcut($path)
    $link.TargetPath = Join-Path $target "VoxNote.exe"
    $link.WorkingDirectory = $target
    $link.Description = "VoxNote - speech to text on your own computer"
    $link.Save()
}
Write-Host "VoxNote was installed to $target"
Write-Host "Shortcuts: $($links -join ', ')"
