"""Shared response + workspace helpers for the desktop server handlers.

Every ``handle_*`` endpoint builds its reply through ``_ok`` / ``_err`` and
validates inputs with ``_require``. Extracting these here lets handler groups
move into their own modules (server_bgm, server_render, …) without importing
``server.py`` itself — keeping the dependency graph acyclic:

    server.py ─┐
    server_*  ─┴─> server_shared ──> server_errors

The historical leading-underscore names are kept so existing call sites in
``server.py`` import them unchanged.
"""
from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import Any

from desktop.server_errors import classify_error_details


def _ok(data: Any) -> tuple[int, dict[str, Any]]:
    return HTTPStatus.OK, {"ok": True, "data": data}


def _err(
    code: str, message: str, status: int = HTTPStatus.BAD_REQUEST
) -> tuple[int, dict[str, Any]]:
    return status, {"ok": False, "error": {"code": code, "message": message}}


def _require(body: dict[str, Any], *keys: str) -> str | None:
    for k in keys:
        if not body.get(k):
            return k
    return None


def _path_or_none(p: Path | None) -> str | None:
    return str(p.resolve()) if p else None


def _tail_log(jw: Path, max_lines: int = 40) -> list[str]:
    p = jw / "run.log"
    if not p.is_file():
        return []
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    lines = text.splitlines()
    return lines[-max_lines:]


def _err_with_log(jw: Path, code: str, message: str) -> tuple[int, dict[str, Any]]:
    tail = _tail_log(jw)
    status, payload = _err(code, message)
    payload["error"]["log_tail"] = tail
    payload["error"].update(classify_error_details(message, tail, fallback_code=code))
    return status, payload


def require_job_workspace(
    body: dict[str, Any], field: str = "job_workspace"
) -> tuple[Path, None] | tuple[None, tuple[int, dict[str, Any]]]:
    """Resolve and validate a job-workspace path from the request body.

    Returns ``(workspace, None)`` on success or ``(None, error_response)`` for a
    missing field / non-existent directory, matching the long-hand pattern the
    handlers previously inlined.
    """
    missing = _require(body, field)
    if missing:
        return None, _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body[field])).expanduser().resolve()
    if not jw.is_dir():
        return None, _err("workspace_missing", f"Job workspace not found: {jw}")
    return jw, None
