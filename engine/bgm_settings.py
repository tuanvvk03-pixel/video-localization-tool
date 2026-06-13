"""Per-video background music (BGM) helpers."""
from __future__ import annotations

from engine.json_store import write_json_atomic
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from engine.ffmpeg_bins import resolve_ffmpeg_executable, resolve_ffprobe_executable

ALLOWED_BGM_EXTS = {".mp3", ".wav", ".m4a", ".aac"}
MAX_BGM_BYTES = 50 * 1024 * 1024
BGM_REL_DIR = Path("assets") / "bgm"
BGM_NORMALIZED_NAME = "bgm_normalized.wav"


class BGMError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _write_json(path: Path, body: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, body)


def _safe_filename(name: str) -> str:
    stem = Path(name).stem.strip() or "bgm"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-._") or "bgm"
    ext = Path(name).suffix.lower()
    return f"{stem[:80]}{ext}"


def _workspace_rel(path: Path, workspace: Path) -> str:
    try:
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def normalize_bgm_settings(raw: Any) -> dict[str, Any]:
    data = raw if isinstance(raw, dict) else {}
    out: dict[str, Any] = {}
    original_path = str(data.get("original_path") or "").strip()
    normalized_path = str(data.get("normalized_path") or "").strip()
    original_filename = str(data.get("original_filename") or "").strip()
    if original_path:
        out["original_path"] = original_path
    if normalized_path:
        out["normalized_path"] = normalized_path
    if original_filename:
        out["original_filename"] = original_filename
    try:
        out["duration_ms"] = max(0, int(float(data.get("duration_ms") or 0)))
    except (TypeError, ValueError):
        out["duration_ms"] = 0
    try:
        volume = float(data.get("volume_db", -20))
    except (TypeError, ValueError):
        volume = -20.0
    out["volume_db"] = max(-40.0, min(0.0, round(volume, 2)))
    out["loop"] = bool(data.get("loop", True))
    try:
        fade_in = int(float(data.get("fade_in_ms", 500)))
    except (TypeError, ValueError):
        fade_in = 500
    try:
        fade_out = int(float(data.get("fade_out_ms", 1000)))
    except (TypeError, ValueError):
        fade_out = 1000
    out["fade_in_ms"] = max(0, min(10000, fade_in))
    out["fade_out_ms"] = max(0, min(10000, fade_out))
    return out


def load_bgm_state(job_workspace: str | Path) -> dict[str, Any] | None:
    jw = Path(job_workspace)
    state = _load_json(jw / "video_state.json")
    raw = state.get("bgm")
    if not isinstance(raw, dict):
        return None
    bgm = normalize_bgm_settings(raw)
    normalized = str(bgm.get("normalized_path") or "")
    if normalized and not (jw / normalized).is_file():
        return None
    return bgm


def save_bgm_state(job_workspace: str | Path, bgm: dict[str, Any]) -> dict[str, Any]:
    jw = Path(job_workspace)
    state_path = jw / "video_state.json"
    state = _load_json(state_path)
    cleaned = normalize_bgm_settings(bgm)
    state["bgm"] = cleaned
    _write_json(state_path, state)
    return cleaned


def update_bgm_settings(job_workspace: str | Path, patch: dict[str, Any]) -> dict[str, Any]:
    current = load_bgm_state(job_workspace) or {}
    current.update(patch)
    return save_bgm_state(job_workspace, current)


def clear_bgm_state(job_workspace: str | Path, *, delete_files: bool = True) -> None:
    jw = Path(job_workspace)
    state_path = jw / "video_state.json"
    state = _load_json(state_path)
    state.pop("bgm", None)
    _write_json(state_path, state)
    if delete_files:
        shutil.rmtree(jw / BGM_REL_DIR, ignore_errors=True)


def _probe_duration_ms(path: Path) -> int:
    ffprobe = resolve_ffprobe_executable()
    if not ffprobe:
        return 0
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise BGMError((proc.stderr or proc.stdout or "ffprobe failed").strip())
    try:
        return max(0, int(round(float((proc.stdout or "0").strip()) * 1000.0)))
    except ValueError as e:
        raise BGMError("Could not read BGM duration.") from e


def import_bgm_file(
    job_workspace: str | Path,
    source_path: str | Path,
    *,
    volume_db: float = -20.0,
    loop: bool = True,
    fade_in_ms: int = 500,
    fade_out_ms: int = 1000,
) -> dict[str, Any]:
    jw = Path(job_workspace).expanduser().resolve()
    src = Path(source_path).expanduser().resolve()
    if not jw.is_dir():
        raise BGMError(f"Job workspace not found: {jw}")
    if not src.is_file():
        raise BGMError(f"BGM file does not exist: {src}")
    if src.suffix.lower() not in ALLOWED_BGM_EXTS:
        raise BGMError("BGM must be one of: mp3, wav, m4a, aac.")
    size = src.stat().st_size
    if size <= 0:
        raise BGMError("BGM file is empty.")
    if size > MAX_BGM_BYTES:
        raise BGMError("BGM file is larger than 50MB.")
    ffmpeg, ffmpeg_err = resolve_ffmpeg_executable()
    if ffmpeg is None:
        raise BGMError(ffmpeg_err or "ffmpeg not found")

    bgm_dir = jw / BGM_REL_DIR
    shutil.rmtree(bgm_dir, ignore_errors=True)
    bgm_dir.mkdir(parents=True, exist_ok=True)
    original_name = src.name
    copied = bgm_dir / _safe_filename(original_name)
    shutil.copy2(src, copied)
    normalized = bgm_dir / BGM_NORMALIZED_NAME
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(copied),
        "-vn",
        "-ac",
        "2",
        "-ar",
        "48000",
        "-c:a",
        "pcm_s16le",
        str(normalized),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0 or not normalized.is_file():
        raise BGMError(f"Could not normalize BGM with ffmpeg: {(proc.stderr or proc.stdout).strip()}")
    duration_ms = _probe_duration_ms(normalized)
    if duration_ms <= 0:
        raise BGMError("BGM has no readable audio duration.")
    return save_bgm_state(
        jw,
        {
            "original_path": _workspace_rel(copied, jw),
            "normalized_path": _workspace_rel(normalized, jw),
            "original_filename": original_name,
            "duration_ms": duration_ms,
            "volume_db": volume_db,
            "loop": loop,
            "fade_in_ms": fade_in_ms,
            "fade_out_ms": fade_out_ms,
        },
    )
