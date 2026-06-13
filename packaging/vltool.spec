# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Video Localization Tool native shell.

Usage:
    pyinstaller packaging/vltool.spec --noconfirm

Output:
    dist/VLTool/VLTool.exe   (Windows one-dir bundle)

Notes:
- one-dir (not one-file) because ffmpeg/yt-dlp and the static frontend
  are loaded at runtime from the same folder — one-file extracts to a
  temp dir every launch and breaks relative assets.
- `ffmpeg.exe` and `yt-dlp.exe` are expected to sit in
  `packaging/bin/` before build. If not present, the build still works
  but the resulting app will surface doctor warnings at runtime.
- The engine/voices_catalog.json and desktop/static/** trees are
  explicitly declared in `datas` so they land next to the EXE.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

SPEC_PATH = Path(SPECPATH)  # type: ignore[name-defined]  # injected by PyInstaller
REPO_ROOT = SPEC_PATH.parent

block_cipher = None


def _collect_static() -> list[tuple[str, str]]:
    """Return (src, dest_dir) pairs for every file under desktop/static."""
    static_root = REPO_ROOT / "desktop" / "static"
    pairs: list[tuple[str, str]] = []
    for path in static_root.rglob("*"):
        if path.is_file():
            rel_dir = path.parent.relative_to(static_root)
            dest = str(Path("desktop") / "static" / rel_dir)
            pairs.append((str(path), dest))
    return pairs


def _bundled_binaries() -> list[tuple[str, str]]:
    """Optionally include ffmpeg / yt-dlp dropped into packaging/bin/."""
    bin_dir = SPEC_PATH / "bin"
    if not bin_dir.exists():
        return []
    pairs: list[tuple[str, str]] = []
    for name in ("ffmpeg.exe", "ffprobe.exe", "yt-dlp.exe"):
        candidate = bin_dir / name
        if candidate.exists():
            pairs.append((str(candidate), "bin"))
    return pairs


datas: list[tuple[str, str]] = []
datas.extend(_collect_static())
datas.append((str(REPO_ROOT / "engine" / "voices_catalog.json"), "engine"))
datas.append((str(REPO_ROOT / "engine" / "translation_glossary.json"), "engine"))
# faster-whisper loads the Silero VAD ONNX model from package data at runtime.
# Without these assets, packaged builds fail during transcription when VAD is enabled.
datas.extend(collect_data_files("faster_whisper"))

binaries: list[tuple[str, str]] = _bundled_binaries()

hidden_imports = [
    # pywebview optional edge backends — explicit so PyInstaller finds them.
    "webview.platforms.edgechromium",
    "webview.platforms.winforms",
    "webview.platforms.cef",
    # edge-tts uses aiohttp / cryptography — already picked up automatically
    # but listed to be defensive on fresh environments.
    "aiohttp",
    "edge_tts",
    # faster-whisper loads ctranslate2 at runtime; let PyInstaller trace it.
    "ctranslate2",
    "faster_whisper",
]

a = Analysis(
    [str(REPO_ROOT / "desktop" / "native.py")],
    pathex=[str(REPO_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim a few large unused packages.
        "tkinter",
        "test",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VLTool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # set True while debugging packaging issues
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(REPO_ROOT / "packaging" / "vltool.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="VLTool",
)
