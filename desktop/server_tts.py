"""TTS-settings endpoint handlers (per-video override + per-project default).

Thin adapters over engine.tts_settings. Extracted from the server monolith
with behaviour identical to the previous inline handlers.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from desktop.server_shared import _err, _ok, _require, require_job_workspace
from engine.tts_settings import (
    TTSSettingsError,
    load_project_tts_settings,
    load_video_tts_override,
    save_project_tts_settings,
    save_video_tts_override,
    validate_settings as validate_tts_settings,
)


def handle_get_video_tts(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    jw, error = require_job_workspace(body)
    if error:
        return error
    try:
        settings = load_video_tts_override(jw)
    except TTSSettingsError as e:
        return _err("invalid_tts_settings", str(e))
    return _ok({"settings": settings})


def handle_save_video_tts(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    jw, error = require_job_workspace(body)
    if error:
        return error
    raw = body.get("settings")
    if not isinstance(raw, dict):
        return _err("invalid_tts_settings", "settings must be a JSON object")
    try:
        cleaned = validate_tts_settings(raw)
        path = save_video_tts_override(jw, raw)
    except TTSSettingsError as e:
        return _err("invalid_tts_settings", str(e))
    return _ok({"path": str(path.resolve()), "settings": cleaned})


def handle_get_project_tts(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "project_root")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    pr = Path(str(body["project_root"])).expanduser().resolve()
    if not pr.is_dir():
        return _err("project_missing", f"Project root not found: {pr}")
    try:
        settings = load_project_tts_settings(pr)
    except TTSSettingsError as e:
        return _err("invalid_tts_settings", str(e))
    return _ok({"settings": settings})


def handle_save_project_tts(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "project_root")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    pr = Path(str(body["project_root"])).expanduser().resolve()
    if not pr.is_dir():
        return _err("project_missing", f"Project root not found: {pr}")
    raw = body.get("settings")
    if not isinstance(raw, dict):
        return _err("invalid_tts_settings", "settings must be a JSON object")
    try:
        cleaned = validate_tts_settings(raw)
        path = save_project_tts_settings(pr, raw)
    except TTSSettingsError as e:
        return _err("invalid_tts_settings", str(e))
    return _ok({"path": str(path.resolve()), "settings": cleaned})
