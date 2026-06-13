"""Background-music (BGM) endpoint handlers.

Thin request/response adapters over engine.bgm_settings. Extracted from the
server monolith; behaviour is identical to the previous inline handlers.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from desktop.server_shared import _err, _ok, _require, require_job_workspace
from engine.bgm_settings import (
    BGMError,
    clear_bgm_state,
    import_bgm_file,
    load_bgm_state,
    update_bgm_settings,
)


def handle_bgm_status(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    jw, error = require_job_workspace(body)
    if error:
        return error
    return _ok({"bgm": load_bgm_state(jw)})


def handle_bgm_upload(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "job_workspace", "bgm_path")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    try:
        bgm = import_bgm_file(
            jw,
            str(body["bgm_path"]),
            volume_db=float(body.get("volume_db", -20)),
            loop=bool(body.get("loop", True)),
            fade_in_ms=int(float(body.get("fade_in_ms", 500))),
            fade_out_ms=int(float(body.get("fade_out_ms", 1000))),
        )
    except (BGMError, OSError, ValueError) as e:
        return _err("invalid_bgm", str(e))
    return _ok({"bgm": bgm})


def handle_bgm_save(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    jw, error = require_job_workspace(body)
    if error:
        return error
    raw = body.get("bgm")
    if not isinstance(raw, dict):
        raw = {
            "volume_db": body.get("volume_db"),
            "loop": body.get("loop"),
            "fade_in_ms": body.get("fade_in_ms"),
            "fade_out_ms": body.get("fade_out_ms"),
        }
    try:
        bgm = update_bgm_settings(jw, raw)
    except (BGMError, OSError, ValueError) as e:
        return _err("invalid_bgm", str(e))
    return _ok({"bgm": bgm})


def handle_bgm_remove(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    jw, error = require_job_workspace(body)
    if error:
        return error
    clear_bgm_state(jw, delete_files=True)
    return _ok({"bgm": None})
