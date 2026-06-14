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

# E1 — brand logo / watermark overlay.
ALLOWED_LOGO_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_LOGO_BYTES = 25 * 1024 * 1024
RENDER_LOGO_REL_DIR = Path("assets") / "render_logo"
ALLOWED_LOGO_POSITIONS = {"top-left", "top-right", "bottom-left", "bottom-right"}
DEFAULT_LOGO_POSITION = "top-right"
DEFAULT_LOGO_SCALE = 0.15  # logo width as a fraction of the target frame width
DEFAULT_LOGO_OPACITY = 1.0
DEFAULT_LOGO_MARGIN = 0.03  # margin from the edges as a fraction of frame width

# E2 — intro/outro clips + head/tail trim.
ALLOWED_CLIP_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
MAX_CLIP_BYTES = 300 * 1024 * 1024
RENDER_INTRO_REL_DIR = Path("assets") / "render_intro"
RENDER_OUTRO_REL_DIR = Path("assets") / "render_outro"
MAX_TRIM_SEC = 600.0


class RenderSettingsError(ValueError):
    pass


def _clamp_float(value: Any, *, lo: float, hi: float, default: float, field: str) -> float:
    if value is None or value == "":
        return default
    try:
        f = float(value)
    except (TypeError, ValueError):
        raise RenderSettingsError(f"{field} must be a number.")
    if f < lo or f > hi:
        raise RenderSettingsError(f"{field} must be between {lo} and {hi}.")
    return f


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

    # Logo / watermark overlay. Position + scale + opacity always normalize so the
    # UI can configure them before/after uploading the image; the overlay only
    # applies at render time when logo_path resolves to a real file.
    logo_path = str(data.get("logo_path") or "").strip()
    if logo_path:
        out["logo_path"] = logo_path
        logo_filename = str(data.get("logo_original_filename") or "").strip()
        if logo_filename:
            out["logo_original_filename"] = logo_filename
        position = str(data.get("logo_position") or DEFAULT_LOGO_POSITION).strip()
        if position not in ALLOWED_LOGO_POSITIONS:
            raise RenderSettingsError(
                "logo_position must be one of: top-left, top-right, bottom-left, bottom-right."
            )
        out["logo_position"] = position
        out["logo_scale"] = _clamp_float(
            data.get("logo_scale"), lo=0.02, hi=1.0, default=DEFAULT_LOGO_SCALE, field="logo_scale"
        )
        out["logo_opacity"] = _clamp_float(
            data.get("logo_opacity"), lo=0.0, hi=1.0, default=DEFAULT_LOGO_OPACITY, field="logo_opacity"
        )
        out["logo_margin"] = _clamp_float(
            data.get("logo_margin"), lo=0.0, hi=0.5, default=DEFAULT_LOGO_MARGIN, field="logo_margin"
        )

    # Intro / outro clips (paths kept only when present) + head/tail trim seconds.
    intro_path = str(data.get("intro_clip_path") or "").strip()
    if intro_path:
        out["intro_clip_path"] = intro_path
        intro_name = str(data.get("intro_original_filename") or "").strip()
        if intro_name:
            out["intro_original_filename"] = intro_name
    outro_path = str(data.get("outro_clip_path") or "").strip()
    if outro_path:
        out["outro_clip_path"] = outro_path
        outro_name = str(data.get("outro_original_filename") or "").strip()
        if outro_name:
            out["outro_original_filename"] = outro_name
    head_trim = _clamp_float(data.get("head_trim_sec"), lo=0.0, hi=MAX_TRIM_SEC, default=0.0, field="head_trim_sec")
    tail_trim = _clamp_float(data.get("tail_trim_sec"), lo=0.0, hi=MAX_TRIM_SEC, default=0.0, field="tail_trim_sec")
    if head_trim > 0:
        out["head_trim_sec"] = head_trim
    if tail_trim > 0:
        out["tail_trim_sec"] = tail_trim

    # E3 — anti-dedup transforms (only emitted when they differ from a no-op, so
    # transforms_active() stays a simple presence check).
    speed = _clamp_float(data.get("transform_speed"), lo=0.5, hi=2.0, default=1.0, field="transform_speed")
    zoom = _clamp_float(data.get("transform_zoom"), lo=1.0, hi=1.5, default=1.0, field="transform_zoom")
    brightness = _clamp_float(data.get("transform_brightness"), lo=-0.3, hi=0.3, default=0.0, field="transform_brightness")
    contrast = _clamp_float(data.get("transform_contrast"), lo=0.5, hi=1.5, default=1.0, field="transform_contrast")
    saturation = _clamp_float(data.get("transform_saturation"), lo=0.0, hi=2.0, default=1.0, field="transform_saturation")
    if abs(speed - 1.0) > 1e-6:
        out["transform_speed"] = speed
    if bool(data.get("transform_hflip")):
        out["transform_hflip"] = True
    if abs(zoom - 1.0) > 1e-6:
        out["transform_zoom"] = zoom
    if abs(brightness) > 1e-6:
        out["transform_brightness"] = brightness
    if abs(contrast - 1.0) > 1e-6:
        out["transform_contrast"] = contrast
    if abs(saturation - 1.0) > 1e-6:
        out["transform_saturation"] = saturation
    return out


def transforms_active(settings: dict[str, Any] | None) -> bool:
    """True when any E3 anti-dedup transform is set in the settings."""
    if not settings:
        return False
    return any(
        k in settings
        for k in (
            "transform_speed", "transform_hflip", "transform_zoom",
            "transform_brightness", "transform_contrast", "transform_saturation",
        )
    )


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
    logo = str(settings.get("logo_path") or "")
    if logo and not (jw / logo).is_file():
        for k in ("logo_path", "logo_original_filename", "logo_position", "logo_scale", "logo_opacity", "logo_margin"):
            settings.pop(k, None)
    intro = str(settings.get("intro_clip_path") or "")
    if intro and not (jw / intro).is_file():
        settings.pop("intro_clip_path", None)
        settings.pop("intro_original_filename", None)
    outro = str(settings.get("outro_clip_path") or "")
    if outro and not (jw / outro).is_file():
        settings.pop("outro_clip_path", None)
        settings.pop("outro_original_filename", None)
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


def import_render_logo_image(
    job_workspace: str | Path,
    source_path: str | Path,
) -> dict[str, Any]:
    jw = Path(job_workspace).expanduser().resolve()
    src = Path(source_path).expanduser().resolve()
    if not jw.is_dir():
        raise RenderSettingsError(f"Job workspace not found: {jw}")
    if not src.is_file():
        raise RenderSettingsError(f"Logo image does not exist: {src}")
    if src.suffix.lower() not in ALLOWED_LOGO_EXTS:
        raise RenderSettingsError("Logo image must be one of: png, jpg, jpeg, webp (png recommended for transparency).")
    size = src.stat().st_size
    if size <= 0:
        raise RenderSettingsError("Logo image is empty.")
    if size > MAX_LOGO_BYTES:
        raise RenderSettingsError("Logo image is larger than 25MB.")

    logo_dir = jw / RENDER_LOGO_REL_DIR
    shutil.rmtree(logo_dir, ignore_errors=True)
    logo_dir.mkdir(parents=True, exist_ok=True)
    copied = logo_dir / _safe_filename(src.name)
    shutil.copy2(src, copied)

    current = load_render_settings(jw) or {"aspect_ratio": "source"}
    current.update(
        {
            "logo_path": _workspace_rel(copied, jw),
            "logo_original_filename": src.name,
        }
    )
    # Seed sensible overlay defaults if the user hasn't set them yet.
    current.setdefault("logo_position", DEFAULT_LOGO_POSITION)
    current.setdefault("logo_scale", DEFAULT_LOGO_SCALE)
    current.setdefault("logo_opacity", DEFAULT_LOGO_OPACITY)
    current.setdefault("logo_margin", DEFAULT_LOGO_MARGIN)
    return save_render_settings(jw, current)


def clear_render_logo(job_workspace: str | Path, *, delete_files: bool = True) -> dict[str, Any]:
    jw = Path(job_workspace)
    current = load_render_settings(jw) or {"aspect_ratio": "source"}
    for k in ("logo_path", "logo_original_filename", "logo_position", "logo_scale", "logo_opacity", "logo_margin"):
        current.pop(k, None)
    if delete_files:
        shutil.rmtree(jw / RENDER_LOGO_REL_DIR, ignore_errors=True)
    return save_render_settings(jw, current)


def _import_render_clip(
    job_workspace: str | Path, source_path: str | Path, *, rel_dir: Path, kind: str
) -> dict[str, Any]:
    jw = Path(job_workspace).expanduser().resolve()
    src = Path(source_path).expanduser().resolve()
    if not jw.is_dir():
        raise RenderSettingsError(f"Job workspace not found: {jw}")
    if not src.is_file():
        raise RenderSettingsError(f"{kind} clip does not exist: {src}")
    if src.suffix.lower() not in ALLOWED_CLIP_EXTS:
        raise RenderSettingsError(f"{kind} clip must be one of: mp4, mov, mkv, webm, m4v.")
    size = src.stat().st_size
    if size <= 0:
        raise RenderSettingsError(f"{kind} clip is empty.")
    if size > MAX_CLIP_BYTES:
        raise RenderSettingsError(f"{kind} clip is larger than 300MB.")

    clip_dir = jw / rel_dir
    shutil.rmtree(clip_dir, ignore_errors=True)
    clip_dir.mkdir(parents=True, exist_ok=True)
    copied = clip_dir / _safe_filename(src.name)
    shutil.copy2(src, copied)

    current = load_render_settings(jw) or {"aspect_ratio": "source"}
    prefix = kind.lower()  # "intro" / "outro"
    current[f"{prefix}_clip_path"] = _workspace_rel(copied, jw)
    current[f"{prefix}_original_filename"] = src.name
    return save_render_settings(jw, current)


def import_render_intro_clip(job_workspace: str | Path, source_path: str | Path) -> dict[str, Any]:
    return _import_render_clip(job_workspace, source_path, rel_dir=RENDER_INTRO_REL_DIR, kind="Intro")


def import_render_outro_clip(job_workspace: str | Path, source_path: str | Path) -> dict[str, Any]:
    return _import_render_clip(job_workspace, source_path, rel_dir=RENDER_OUTRO_REL_DIR, kind="Outro")


def _clear_render_clip(job_workspace: str | Path, *, rel_dir: Path, prefix: str, delete_files: bool) -> dict[str, Any]:
    jw = Path(job_workspace)
    current = load_render_settings(jw) or {"aspect_ratio": "source"}
    current.pop(f"{prefix}_clip_path", None)
    current.pop(f"{prefix}_original_filename", None)
    if delete_files:
        shutil.rmtree(jw / rel_dir, ignore_errors=True)
    return save_render_settings(jw, current)


def clear_render_intro(job_workspace: str | Path, *, delete_files: bool = True) -> dict[str, Any]:
    return _clear_render_clip(job_workspace, rel_dir=RENDER_INTRO_REL_DIR, prefix="intro", delete_files=delete_files)


def clear_render_outro(job_workspace: str | Path, *, delete_files: bool = True) -> dict[str, Any]:
    return _clear_render_clip(job_workspace, rel_dir=RENDER_OUTRO_REL_DIR, prefix="outro", delete_files=delete_files)
