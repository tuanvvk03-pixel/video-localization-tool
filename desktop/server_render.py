"""Render-settings and render-background endpoint handlers.

Thin adapters over engine.render_settings. Extracted from the server monolith
with behaviour identical to the previous inline handlers.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from desktop.server_shared import _err, _ok, _require, require_job_workspace
from engine.render_settings import (
    RenderSettingsError,
    clear_render_background,
    clear_render_logo,
    import_render_background_image,
    import_render_logo_image,
    load_render_settings,
    update_render_settings,
)


def handle_render_settings_status(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    jw, error = require_job_workspace(body)
    if error:
        return error
    try:
        settings = load_render_settings(jw)
    except (RenderSettingsError, OSError, ValueError) as e:
        return _err("invalid_render_settings", str(e))
    return _ok({"render": settings})


def handle_render_settings_save(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    jw, error = require_job_workspace(body)
    if error:
        return error
    raw = body.get("render")
    if not isinstance(raw, dict):
        raw = {"aspect_ratio": body.get("aspect_ratio")}
    try:
        settings = update_render_settings(jw, raw)
    except (RenderSettingsError, OSError, ValueError) as e:
        return _err("invalid_render_settings", str(e))
    return _ok({"render": settings})


def handle_render_background_upload(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "job_workspace", "image_path")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    try:
        settings = import_render_background_image(jw, str(body["image_path"]))
    except (RenderSettingsError, OSError, ValueError) as e:
        return _err("invalid_render_background", str(e))
    return _ok({"render": settings})


def handle_render_background_remove(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    jw, error = require_job_workspace(body)
    if error:
        return error
    try:
        settings = clear_render_background(jw, delete_files=True)
    except (RenderSettingsError, OSError, ValueError) as e:
        return _err("invalid_render_background", str(e))
    return _ok({"render": settings})


def handle_render_logo_upload(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "job_workspace", "image_path")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    try:
        settings = import_render_logo_image(jw, str(body["image_path"]))
    except (RenderSettingsError, OSError, ValueError) as e:
        return _err("invalid_render_logo", str(e))
    return _ok({"render": settings})


def handle_render_logo_remove(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    jw, error = require_job_workspace(body)
    if error:
        return error
    try:
        settings = clear_render_logo(jw, delete_files=True)
    except (RenderSettingsError, OSError, ValueError) as e:
        return _err("invalid_render_logo", str(e))
    return _ok({"render": settings})
