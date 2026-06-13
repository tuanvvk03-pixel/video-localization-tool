"""Zip dist/VLTool/ into dist/VLTool-win64.zip and drop the build/ scratch folder.

Run after `make build-desktop` (or `python -m PyInstaller packaging/vltool.spec`):
    python scripts/package_release.py
"""
from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DIST_FOLDER = REPO_ROOT / "dist" / "VLTool"
BUILD_FOLDER = REPO_ROOT / "build"
ZIP_PATH = REPO_ROOT / "dist" / "VLTool-win64.zip"


def main() -> int:
    if not DIST_FOLDER.is_dir():
        print(f"[package] missing {DIST_FOLDER} — run `make build-desktop` first", file=sys.stderr)
        return 1

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    print(f"[package] zipping {DIST_FOLDER} -> {ZIP_PATH}")
    files = [p for p in DIST_FOLDER.rglob("*") if p.is_file()]
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for i, path in enumerate(files, 1):
            arc = Path("VLTool") / path.relative_to(DIST_FOLDER)
            zf.write(path, arc)
            if i % 200 == 0 or i == len(files):
                print(f"[package]   {i}/{len(files)}")

    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"[package] wrote {ZIP_PATH.name} ({size_mb:.1f} MB)")

    if BUILD_FOLDER.is_dir():
        print(f"[package] removing scratch {BUILD_FOLDER}")
        shutil.rmtree(BUILD_FOLDER, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
