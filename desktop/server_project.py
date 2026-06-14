"""Multi-video project endpoint handlers.

Adapters over engine.project_manager for creating projects, adding videos, and
reading/patching per-video overrides. Extracted from the server monolith with
behaviour identical to the previous inline handlers.
"""
from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import Any

from desktop.server_shared import _err, _ok, _require
from engine.project_manager import (
    ProjectError,
    add_video as project_add_video,
    init_project,
    list_video_statuses,
    load_project,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _default_projects_root() -> Path:
    return (REPO_ROOT / "Projects").resolve()


def handle_init_project(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Create a multi-video project directory via engine.project_manager.init_project()."""
    missing = _require(body, "project_name")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    project_name = str(body["project_name"]).strip()
    if not project_name:
        return _err("missing_field", "project_name is empty")
    raw_root = str(body.get("projects_root") or "").strip()
    used_default_root = not raw_root
    projects_root = _default_projects_root() if used_default_root else Path(raw_root).expanduser()
    try:
        projects_root.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return _err("projects_root_create_failed", f"Could not create projects root: {e}")

    project_id = str(body.get("project_id") or "").strip()
    config_overrides = body.get("config_overrides") or {}
    if not isinstance(config_overrides, dict):
        return _err("bad_config_overrides", "config_overrides must be an object")
    force = bool(body.get("force"))
    try:
        state = init_project(
            projects_root,
            project_name,
            project_id=project_id,
            config_overrides=config_overrides,
            force=force,
        )
    except ProjectError as e:
        return _err("init_project_failed", str(e))
    except OSError as e:
        return _err("init_project_failed", f"OS error: {e}")
    return _ok(
        {
            "project_id": state.project_id,
            "project_root": state.project_root,
            "projects_root": str(projects_root.resolve()),
            "used_default_projects_root": used_default_root,
            "project_name": state.config.project_name,
        }
    )


def handle_add_video_to_project(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Copy a source video into an existing project and register it as a new video_workspace."""
    missing = _require(body, "project_root", "video")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    project_root = Path(str(body["project_root"])).expanduser()
    if not project_root.is_dir():
        return _err("project_not_found", f"Project directory not found: {project_root}")
    video = Path(str(body["video"])).expanduser()
    if not video.is_file():
        return _err("video_not_found", f"Video file does not exist: {video}")
    video_id = str(body.get("video_id") or "").strip()
    force = bool(body.get("force"))
    override = body.get("override")
    if override is not None and not isinstance(override, dict):
        return _err("bad_override", "override must be an object")
    try:
        entry = project_add_video(
            project_root,
            video,
            video_id=video_id,
            force=force,
        )
    except ProjectError as e:
        return _err("add_video_failed", str(e))
    except OSError as e:
        return _err("add_video_failed", f"OS error: {e}")

    if isinstance(override, dict) and override:
        status, payload = handle_save_video_override(
            {
                "project_root": str(project_root),
                "video_id": entry.video_id,
                "override": override,
            }
        )
        if status != HTTPStatus.OK:
            return status, payload

    return _ok(
        {
            "video_id": entry.video_id,
            "workspace": entry.workspace,
            "source_path": entry.source_path,
            "duration_s": entry.duration_s,
            "is_long": entry.is_long,
            "added_at_unix": entry.added_at_unix,
        }
    )


_VIDEO_OVERRIDE_KEYS = {
    "api_key",
    "translate_backend",
    "tts_provider",
    "tts_voice",
    "mix_mode",
    "enable_source_cleanup",
    "enable_translation_qa",
}


def handle_save_video_override(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Update per-video overrides in project_state.json (shallow merge, None clears a key)."""
    missing = _require(body, "project_root", "video_id")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    project_root = Path(str(body["project_root"])).expanduser()
    video_id = str(body["video_id"]).strip()
    override = body.get("override")
    if override is None:
        override = {}
    if not isinstance(override, dict):
        return _err("bad_override", "override must be an object")
    try:
        state = load_project(project_root)
    except ProjectError as e:
        return _err("project_not_found", str(e))
    if not any(v.video_id == video_id for v in state.videos):
        return _err("video_not_in_project", f"video_id not in project: {video_id}")

    current = dict(state.config.per_video_overrides.get(video_id) or {})
    unknown = [k for k in override.keys() if k not in _VIDEO_OVERRIDE_KEYS]
    if unknown:
        return _err("unknown_override_keys", f"Unknown override keys: {sorted(unknown)}")
    for k, v in override.items():
        if v is None:
            current.pop(k, None)
        else:
            current[k] = v
    if current:
        state.config.per_video_overrides[video_id] = current
    else:
        state.config.per_video_overrides.pop(video_id, None)

    from engine.project_manager import _write_state as _pm_write_state  # noqa: WPS450

    try:
        _pm_write_state(state)
    except OSError as e:
        return _err("save_override_failed", f"Could not write project_state.json: {e}")
    return _ok(
        {
            "video_id": video_id,
            "override": current,
            "resolved": state.config.resolve_for(video_id),
        }
    )


def handle_export_project(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Collect every rendered final.mp4 in the project into one export folder."""
    missing = _require(body, "project_root")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    project_root = Path(str(body["project_root"])).expanduser()
    if not project_root.is_dir():
        return _err("project_not_found", f"Project directory not found: {project_root}")
    from engine.project_export import export_project_renders

    try:
        result = export_project_renders(project_root, dest=(str(body.get("dest")) if body.get("dest") else None))
    except (ProjectError, OSError, ValueError) as e:
        return _err("export_failed", str(e))
    return _ok(result)


def handle_get_project(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Return full project state + per-video status snapshots."""
    missing = _require(body, "project_root")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    project_root = Path(str(body["project_root"])).expanduser()
    if not project_root.is_dir():
        return _err("project_not_found", f"Project directory not found: {project_root}")
    try:
        state = load_project(project_root)
        statuses = list_video_statuses(project_root)
    except ProjectError as e:
        return _err("project_not_found", str(e))
    config_dict = {
        "project_name": state.config.project_name,
        "api_key": state.config.api_key,
        "translate_backend": state.config.translate_backend,
        "tts_provider": state.config.tts_provider,
        "tts_voice": state.config.tts_voice,
        "mix_mode": state.config.mix_mode,
        "enable_source_cleanup": state.config.enable_source_cleanup,
        "enable_translation_qa": state.config.enable_translation_qa,
        "per_video_overrides": dict(state.config.per_video_overrides),
    }
    videos = [
        {
            "video_id": v.video_id,
            "workspace": v.workspace,
            "source_path": v.source_path,
            "duration_s": v.duration_s,
            "is_long": v.is_long,
            "added_at_unix": v.added_at_unix,
            "override": dict(state.config.per_video_overrides.get(v.video_id) or {}),
            "resolved": state.config.resolve_for(v.video_id),
        }
        for v in state.videos
    ]
    return _ok(
        {
            "project_id": state.project_id,
            "project_root": state.project_root,
            "config": config_dict,
            "videos": videos,
            "statuses": statuses,
        }
    )
