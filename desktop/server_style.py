"""Subtitle-style endpoint handlers (per-video override + per-project default).

Thin adapters over engine.subtitle_style. Extracted from the server monolith
with behaviour identical to the previous inline handlers.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from desktop.server_shared import _err, _ok, _require, require_job_workspace
from engine.subtitle_style import (
    SubtitleStyleError,
    load_project_style,
    load_video_style_override,
    save_project_style,
    save_video_style_override,
)


def handle_get_video_style(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    jw, error = require_job_workspace(body)
    if error:
        return error
    try:
        style = load_video_style_override(jw)
    except SubtitleStyleError as e:
        return _err("invalid_style", str(e))
    return _ok({"style": style})


def handle_save_video_style(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    jw, error = require_job_workspace(body)
    if error:
        return error
    raw = body.get("style")
    if not isinstance(raw, dict):
        return _err("invalid_style", "style must be a JSON object")
    try:
        path = save_video_style_override(jw, raw)
    except SubtitleStyleError as e:
        return _err("invalid_style", str(e))
    return _ok({"path": str(path.resolve()), "style": raw})


def handle_get_project_style(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "project_root")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    pr = Path(str(body["project_root"])).expanduser().resolve()
    if not pr.is_dir():
        return _err("project_missing", f"Project root not found: {pr}")
    try:
        style = load_project_style(pr)
    except SubtitleStyleError as e:
        return _err("invalid_style", str(e))
    return _ok({"style": style})


def handle_save_project_style(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "project_root")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    pr = Path(str(body["project_root"])).expanduser().resolve()
    if not pr.is_dir():
        return _err("project_missing", f"Project root not found: {pr}")
    raw = body.get("style")
    if not isinstance(raw, dict):
        return _err("invalid_style", "style must be a JSON object")
    try:
        path = save_project_style(pr, raw)
    except SubtitleStyleError as e:
        return _err("invalid_style", str(e))
    return _ok({"path": str(path.resolve()), "style": raw})
