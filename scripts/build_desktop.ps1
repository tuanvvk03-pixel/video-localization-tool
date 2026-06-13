# scripts/build_desktop.ps1
#
# Build the Windows native EXE for the video localization tool.
#
# Prereqs (one-time):
#     python -m pip install -r engine/requirements.txt
#     python -m pip install -r engine/requirements-desktop.txt
#
# Optional: drop ffmpeg.exe, ffprobe.exe, yt-dlp.exe into packaging/bin/
# so they get bundled into the resulting dist/VLTool/ folder.
#
# Usage:
#     pwsh scripts/build_desktop.ps1
#     pwsh scripts/build_desktop.ps1 -Clean
#     pwsh scripts/build_desktop.ps1 -SmokeTest

[CmdletBinding()]
param(
    [switch]$Clean,
    [switch]$SmokeTest
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if ($Clean) {
    Write-Host "[build] cleaning dist/ and build/"
    if (Test-Path dist)  { Remove-Item dist  -Recurse -Force }
    if (Test-Path build) { Remove-Item build -Recurse -Force }
}

Write-Host "[build] invoking PyInstaller on packaging/vltool.spec"
python -m PyInstaller packaging/vltool.spec --noconfirm
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

$exePath = Join-Path $repoRoot "dist/VLTool/VLTool.exe"
if (-not (Test-Path $exePath)) {
    throw "Expected output not found: $exePath"
}
Write-Host "[build] success -> $exePath"

if ($SmokeTest) {
    Write-Host "[build] launching for smoke test (close the window to continue)"
    & $exePath
}
