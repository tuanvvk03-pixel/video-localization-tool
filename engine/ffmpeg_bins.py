"""Resolve ffmpeg/ffprobe executables (FFMPEG_BIN / FFPROBE_BIN, bundled, or PATH)."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _bundled_bin(name: str) -> Path | None:
    """Return <bundle>/bin/<name> when running under PyInstaller, else None."""
    if not getattr(sys, "frozen", False):
        return None
    base = getattr(sys, "_MEIPASS", None)
    if not base:
        return None
    candidate = Path(base) / "bin" / name
    return candidate if candidate.is_file() else None


def resolve_ffmpeg_executable() -> tuple[str | None, str | None]:
    """
    Returns (path, None) on success, or (None, error_message) if unusable.

    Lookup order: FFMPEG_BIN env -> PyInstaller bundle -> shutil.which("ffmpeg").
    If FFMPEG_BIN is set, that path is used only (no fallback).
    """
    raw = (os.environ.get("FFMPEG_BIN") or "").strip()
    if raw:
        candidate = Path(raw).expanduser()
        if not candidate.is_file():
            return None, (
                f"FFMPEG_BIN is set to {raw!r} but that path is not an existing file. "
                "Fix FFMPEG_BIN or unset it to use the bundled/PATH ffmpeg."
            )
        return str(candidate.resolve()), None

    bundled = _bundled_bin("ffmpeg.exe") or _bundled_bin("ffmpeg")
    if bundled is not None:
        return str(bundled.resolve()), None

    found = shutil.which("ffmpeg")
    if not found:
        return None, (
            "ffmpeg not found: set environment variable FFMPEG_BIN to the full path "
            "to the ffmpeg executable, or install ffmpeg and add it to PATH."
        )
    return found, None


def resolve_ffprobe_executable() -> str | None:
    """
    Optional tool for future stages. Lookup order:
    FFPROBE_BIN env -> PyInstaller bundle -> shutil.which("ffprobe").
    Returns None if not found (not an error).
    """
    raw = (os.environ.get("FFPROBE_BIN") or "").strip()
    if raw:
        candidate = Path(raw).expanduser()
        if candidate.is_file():
            return str(candidate.resolve())
        return None

    bundled = _bundled_bin("ffprobe.exe") or _bundled_bin("ffprobe")
    if bundled is not None:
        return str(bundled.resolve())

    return shutil.which("ffprobe")
