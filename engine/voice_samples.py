"""Per-video voice samples (speaker reference clips for XTTS cloning).

A user uploads a 6-30s clip of a target voice; we copy + normalize it to a clean
mono 24kHz PCM16 WAV under ``assets/voice_samples/`` so the XTTS provider can use
its absolute path as the cue's clone voice (override
``{"provider": "xtts", "voice_id": "<that path>"}``). Mirrors engine.bgm_settings.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from engine.ffmpeg_bins import resolve_ffmpeg_executable, resolve_ffprobe_executable

ALLOWED_SAMPLE_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
MAX_SAMPLE_BYTES = 50 * 1024 * 1024
SAMPLES_REL_DIR = Path("assets") / "voice_samples"


class VoiceSampleError(ValueError):
    pass


def _sample_id(name: str) -> str:
    stem = Path(name).stem.strip() or "voice"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-._") or "voice"
    return stem[:80]


def _probe_duration_ms(path: Path) -> int:
    ffprobe = resolve_ffprobe_executable()
    if not ffprobe:
        return 0
    cmd = [
        ffprobe, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        return 0
    try:
        return max(0, int(round(float((proc.stdout or "0").strip()) * 1000.0)))
    except ValueError:
        return 0


def _sample_dict(jw: Path, wav: Path) -> dict[str, Any]:
    return {
        "id": wav.stem,
        "filename": wav.name,
        "rel_path": wav.resolve().relative_to(jw.resolve()).as_posix(),
        "path": str(wav.resolve()),
        "duration_ms": _probe_duration_ms(wav),
    }


def list_voice_samples(job_workspace: str | Path) -> list[dict[str, Any]]:
    jw = Path(job_workspace)
    d = jw / SAMPLES_REL_DIR
    if not d.is_dir():
        return []
    out: list[dict[str, Any]] = []
    try:
        for wav in sorted(d.glob("*.wav")):
            if wav.is_file():
                out.append(_sample_dict(jw, wav))
    except OSError:
        return []
    return out


def import_voice_sample(job_workspace: str | Path, source_path: str | Path) -> dict[str, Any]:
    jw = Path(job_workspace).expanduser().resolve()
    src = Path(source_path).expanduser().resolve()
    if not jw.is_dir():
        raise VoiceSampleError(f"Job workspace not found: {jw}")
    if not src.is_file():
        raise VoiceSampleError(f"Voice sample file does not exist: {src}")
    if src.suffix.lower() not in ALLOWED_SAMPLE_EXTS:
        raise VoiceSampleError("Voice sample must be one of: wav, mp3, m4a, aac, flac, ogg.")
    size = src.stat().st_size
    if size <= 0:
        raise VoiceSampleError("Voice sample file is empty.")
    if size > MAX_SAMPLE_BYTES:
        raise VoiceSampleError("Voice sample is larger than 50MB.")
    ffmpeg, ffmpeg_err = resolve_ffmpeg_executable()
    if ffmpeg is None:
        raise VoiceSampleError(ffmpeg_err or "ffmpeg not found")

    out_dir = jw / SAMPLES_REL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    sample_id = _sample_id(src.name)
    normalized = out_dir / f"{sample_id}.wav"
    # Clean mono 24kHz PCM16 — ideal speaker reference for XTTS.
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(src), "-vn", "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le",
        str(normalized),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0 or not normalized.is_file():
        raise VoiceSampleError(
            f"Could not normalize voice sample with ffmpeg: {(proc.stderr or proc.stdout).strip()}"
        )
    return _sample_dict(jw, normalized)


def remove_voice_sample(job_workspace: str | Path, sample_id: str) -> None:
    jw = Path(job_workspace)
    sid = _sample_id(str(sample_id or ""))
    if not sid:
        return
    target = (jw / SAMPLES_REL_DIR / f"{sid}.wav").resolve()
    try:
        target.relative_to((jw / SAMPLES_REL_DIR).resolve())
    except ValueError:
        return
    if target.is_file():
        target.unlink(missing_ok=True)
