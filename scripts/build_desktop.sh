#!/usr/bin/env bash
# scripts/build_desktop.sh
#
# Build the native app bundle on Linux / macOS. On Windows, use
# scripts/build_desktop.ps1 instead.
#
# Prereqs (one-time):
#     python -m pip install -r engine/requirements.txt
#     python -m pip install -r engine/requirements-desktop.txt
#
# Linux note: pywebview needs WebKitGTK. On Debian/Ubuntu:
#     sudo apt install gir1.2-webkit2-4.1 python3-gi
#
# Usage:
#     scripts/build_desktop.sh
#     scripts/build_desktop.sh --clean
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." &>/dev/null && pwd)"
cd "$repo_root"

if [[ "${1:-}" == "--clean" ]]; then
    echo "[build] cleaning dist/ and build/"
    rm -rf dist build
fi

echo "[build] invoking PyInstaller on packaging/vltool.spec"
python -m PyInstaller packaging/vltool.spec --noconfirm

out_dir="$repo_root/dist/VLTool"
if [[ ! -d "$out_dir" ]]; then
    echo "[build] ERROR: expected output folder not found: $out_dir" >&2
    exit 1
fi
echo "[build] success -> $out_dir"
