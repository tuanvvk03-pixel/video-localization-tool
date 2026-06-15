# -*- mode: python ; coding: utf-8 -*-
"""FULL PyInstaller spec — bundles the heavy ML stack (torch + coqui-tts/XTTS +
Demucs + transformers + faster-whisper) on top of the lean shell.

    pyinstaller packaging/vltool_full.spec --noconfirm  ->  dist/VLTool/VLTool.exe

This artifact is multi-GB and is meant for GPU machines (CUDA). On CPU-only
machines it still runs (edge-tts dub / transcribe / branding / batch) but XTTS
voice-clone and Demucs keep-music will be slow. Models (viXTTS, htdemucs) are
downloaded on first use, not bundled.
"""
from __future__ import annotations

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files

SPEC_PATH = Path(SPECPATH)  # type: ignore[name-defined]
REPO_ROOT = SPEC_PATH.parent

block_cipher = None


def _collect_static() -> list[tuple[str, str]]:
    static_root = REPO_ROOT / "desktop" / "static"
    pairs: list[tuple[str, str]] = []
    for path in static_root.rglob("*"):
        if path.is_file():
            rel_dir = path.parent.relative_to(static_root)
            pairs.append((str(path), str(Path("desktop") / "static" / rel_dir)))
    return pairs


def _bundled_binaries() -> list[tuple[str, str]]:
    bin_dir = SPEC_PATH / "bin"
    pairs: list[tuple[str, str]] = []
    if bin_dir.exists():
        for name in ("ffmpeg.exe", "ffprobe.exe", "yt-dlp.exe"):
            c = bin_dir / name
            if c.exists():
                pairs.append((str(c), "bin"))
    return pairs


datas: list[tuple[str, str]] = []
binaries: list[tuple[str, str]] = []
hiddenimports: list[str] = []

# App data.
datas.extend(_collect_static())
datas.append((str(REPO_ROOT / "engine" / "voices_catalog.json"), "engine"))
datas.append((str(REPO_ROOT / "engine" / "translation_glossary.json"), "engine"))
datas.extend(collect_data_files("faster_whisper"))

# Heavy ML stack — collect code + data + native libs (incl. CUDA) for each.
_HEAVY = [
    "torch", "torchaudio", "TTS", "demucs", "transformers", "tokenizers",
    "ctranslate2", "faster_whisper", "encodec", "julius", "einops",
    "openunmix", "dora", "omegaconf", "soundfile", "sentencepiece",
]
for pkg in _HEAVY:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception as exc:  # noqa: BLE001
        print(f"[spec] collect_all({pkg}) skipped: {exc}")

binaries += _bundled_binaries()

hiddenimports += [
    "webview.platforms.edgechromium",
    "webview.platforms.winforms",
    "aiohttp",
    "edge_tts",
    "ctranslate2",
    "faster_whisper",
    "TTS.tts.models.xtts",
    "demucs.api",
    "demucs.separate",
]

a = Analysis(
    [str(REPO_ROOT / "desktop" / "native.py")],
    pathex=[str(REPO_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "test", "tests"],
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
    console=False,
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
