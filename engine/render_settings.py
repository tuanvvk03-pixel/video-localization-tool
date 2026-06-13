"""Per-video render layout settings."""
from __future__ import annotations

from engine.json_store import write_json_atomic
import json
import re
import shutil
from pathlib import Path
from typing import Any

ALLOWED_ASPECT_RATIOS = {"source", "16:9", "9:16"}
ALLOWED_BACKGROUND_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_BACKGROUND_BYTES = 25 * 1024 * 1024
RENDER_BACKGROUND_REL_DIR = Path("assets") / "render_background"


class RenderSettingsError(ValueError):
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
    stem = Path(name).stem.strip() or "background"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-._") or "background"
    ext = Path(name).suffix.lower()
    return f"{stem[:80]}{ext}"


def _workspace_rel(path: Path, workspace: Path) -> str:
    try:
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def normalize_render_settings(raw: Any) -> dict[str, Any]:
    data = raw if isinstance(raw, dict) else {}
    aspect = str(data.get("aspect_ratio") or "source").strip()
    if aspect not in ALLOWED_ASPECT_RATIOS:
        raise RenderSettingsError("aspect_ratio must be one of: source, 16:9, 9:16.")

    out: dict[str, Any] = {"aspect_ratio": aspect}
    background_path = str(data.get("background_path") or "").strip()
    background_filename = str(data.get("background_original_filename") or "").strip()
    if background_path:
        out["background_path"] = background_path
    if background_filename:
        out["background_original_filename"] = background_filename
    return out


def load_render_settings(job_workspace: str | Path) -> dict[str, Any] | None:
    jw = Path(job_workspace)
    state = _load_json(jw / "video_state.json")
    raw = state.get("render")
    if not isinstance(raw, dict):
        return None
    settings = normalize_render_settings(raw)
    background = str(settings.get("background_path") or "")
    if background and not (jw / background).is_file():
        settings.pop("background_path", None)
    return settings


def save_render_settings(job_workspace: str | Path, settings: dict[str, Any]) -> dict[str, Any]:
    jw = Path(job_workspace)
    state_path = jw / "video_state.json"
    state = _load_json(state_path)
    cleaned = normalize_render_settings(settings)
    state["render"] = cleaned
    _write_json(state_path, state)
    return cleaned


def update_render_settings(job_workspace: str | Path, patch: dict[str, Any]) -> dict[str, Any]:
    current = load_render_settings(job_workspace) or {"aspect_ratio": "source"}
    current.update(patch)
    return save_render_settings(job_workspace, current)


def import_render_background_image(
    job_workspace: str | Path,
    source_path: str | Path,
) -> dict[str, Any]:
    jw = Path(job_workspace).expanduser().resolve()
    src = Path(source_path).expanduser().resolve()
    if not jw.is_dir():
        raise RenderSettingsError(f"Job workspace not found: {jw}")
    if not src.is_file():
        raise RenderSettingsError(f"Background image does not exist: {src}")
    if src.suffix.lower() not in ALLOWED_BACKGROUND_EXTS:
        raise RenderSettingsError("Background image must be one of: jpg, jpeg, png, webp.")
    size = src.stat().st_size
    if size <= 0:
        raise RenderSettingsError("Background image is empty.")
    if size > MAX_BACKGROUND_BYTES:
        raise RenderSettingsError("Background image is larger than 25MB.")

    bg_dir = jw / RENDER_BACKGROUND_REL_DIR
    shutil.rmtree(bg_dir, ignore_errors=True)
    bg_dir.mkdir(parents=True, exist_ok=True)
    copied = bg_dir / _safe_filename(src.name)
    shutil.copy2(src, copied)

    current = load_render_settings(jw) or {"aspect_ratio": "source"}
    current.update(
        {
            "background_path": _workspace_rel(copied, jw),
            "background_original_filename": src.name,
        }
    )
    return save_render_settings(jw, current)


def clear_render_background(job_workspace: str | Path, *, delete_files: bool = True) -> dict[str, Any]:
    jw = Path(job_workspace)
    current = load_render_settings(jw) or {"aspect_ratio": "source"}
    current.pop("background_path", None)
    current.pop("background_original_filename", None)
    if delete_files:
        shutil.rmtree(jw / RENDER_BACKGROUND_REL_DIR, ignore_errors=True)
    return save_render_settings(jw, current)
