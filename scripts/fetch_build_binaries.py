"""Populate packaging/bin/ with ffmpeg, ffprobe, yt-dlp for PyInstaller bundling.

Order of preference:
  1. Already present in packaging/bin/      -> skip
  2. Found via `shutil.which` (local install) -> copy
     (ffmpeg/ffprobe only; yt-dlp is almost always a pip-installed launcher
      stub that won't run standalone, so we download the GitHub release.)
  3. Download from upstream                  -> fetch

Run once before `make build-desktop`:
    python scripts/fetch_build_binaries.py
    python scripts/fetch_build_binaries.py --force   # force re-download
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_DIR = REPO_ROOT / "packaging" / "bin"

FFMPEG_ZIP_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/"
    "ffmpeg-master-latest-win64-gpl.zip"
)
YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"

MIN_STANDALONE_SIZE = 5 * 1024 * 1024  # 5 MB — pip launcher stubs are ~100 KB


def _download(url: str) -> bytes:
    print(f"[fetch] GET {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "vltool-build/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return resp.read()


def _extract_ffmpeg(zip_bytes: bytes, dest: Path) -> None:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        wanted = {"ffmpeg.exe", "ffprobe.exe"}
        for name in zf.namelist():
            base = Path(name).name
            if base in wanted:
                with zf.open(name) as src, (dest / base).open("wb") as out:
                    shutil.copyfileobj(src, out)
                wanted.discard(base)
                print(f"[fetch] extracted {base}")
        if wanted:
            raise RuntimeError(f"ffmpeg archive missing: {sorted(wanted)}")


def _try_local(tool_name: str, dest: Path) -> bool:
    found = shutil.which(tool_name)
    if not found:
        return False
    src = Path(found)
    if src.stat().st_size < MIN_STANDALONE_SIZE:
        print(f"[fetch] local {tool_name} too small ({src.stat().st_size} B) — probably a launcher stub, skipping")
        return False
    shutil.copy2(src, dest)
    print(f"[fetch] copied local {tool_name} from {src}")
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="ignore existing files in packaging/bin/")
    ns = ap.parse_args(argv)

    BIN_DIR.mkdir(parents=True, exist_ok=True)

    ffmpeg_exe = BIN_DIR / "ffmpeg.exe"
    ffprobe_exe = BIN_DIR / "ffprobe.exe"
    ytdlp_exe = BIN_DIR / "yt-dlp.exe"

    if ns.force:
        for p in (ffmpeg_exe, ffprobe_exe, ytdlp_exe):
            p.unlink(missing_ok=True)

    if ffmpeg_exe.exists() and ffprobe_exe.exists():
        print("[fetch] ffmpeg + ffprobe already in packaging/bin/, skipping")
    else:
        got_local = _try_local("ffmpeg", ffmpeg_exe) and _try_local("ffprobe", ffprobe_exe)
        if not got_local:
            ffmpeg_exe.unlink(missing_ok=True)
            ffprobe_exe.unlink(missing_ok=True)
            _extract_ffmpeg(_download(FFMPEG_ZIP_URL), BIN_DIR)

    if ytdlp_exe.exists():
        print("[fetch] yt-dlp already in packaging/bin/, skipping")
    else:
        ytdlp_exe.write_bytes(_download(YTDLP_URL))
        print(f"[fetch] downloaded {ytdlp_exe.name}")

    for p in (ffmpeg_exe, ffprobe_exe, ytdlp_exe):
        size_mb = p.stat().st_size / (1024 * 1024)
        print(f"[fetch]   {p.name}: {size_mb:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
