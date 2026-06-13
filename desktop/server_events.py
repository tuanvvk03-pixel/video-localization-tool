"""Server-Sent Events stream for live job progress + log tail.

Pushes the same payload the client used to *poll* from ``/api/job-progress``
(progress fields + ``last_error`` + ``log_tail``) so the UI can drop its
``setInterval``. No engine changes: the server tails the ``job_state.json`` +
``run.log`` that the run subprocess already writes, computes ``_progress_payload``
(reused from Phase B), and emits a frame only when the payload changes.

Acyclic deps: ``server.py -> server_events -> server_progress / server_import_config / server_shared``.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, Iterator

from desktop.server_import_config import _load_json_file
from desktop.server_progress import _progress_payload
from desktop.server_shared import _tail_log


def _sse(event: str, data: Any) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")


def _job_progress_payload(jw: Path, *, log_lines: int) -> dict[str, Any]:
    """Mirror /api/job-progress data (minus the JobManager record) for a workspace."""
    state = _load_json_file(jw / "job_state.json")
    return {
        **_progress_payload(state, jw=jw),
        "last_error": state.get("last_error"),
        "log_tail": _tail_log(jw, max_lines=log_lines),
    }


def iter_job_event_frames(
    jw: Path,
    *,
    poll_interval: float = 1.0,
    heartbeat_s: float = 15.0,
    max_runtime_s: float = 3600.0,
    log_lines: int = 200,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> Iterator[bytes]:
    """Yield SSE frames for a job workspace until it reaches a terminal lifecycle.

    Emits a ``progress`` frame (the /api/job-progress-shaped payload) on every
    change, ``: ping`` heartbeats while idle, and a final ``done`` frame once the
    lifecycle is completed/failed (or a max-runtime safety cap is hit), then
    returns so the handler closes the connection. ``sleep``/``monotonic`` are
    injectable for deterministic tests.
    """
    last_payload: dict[str, Any] | None = None
    start = monotonic()
    last_emit = start
    while True:
        now = monotonic()
        payload = _job_progress_payload(jw, log_lines=log_lines)
        if payload != last_payload:
            yield _sse("progress", payload)
            last_payload = payload
            last_emit = now

        lifecycle = str(payload.get("lifecycle") or "")
        if lifecycle in ("completed", "failed"):
            yield _sse("done", payload)
            return
        if now - start >= max_runtime_s:
            yield _sse("done", payload)
            return
        if now - last_emit >= heartbeat_s:
            yield b": ping\n\n"
            last_emit = now
        sleep(poll_interval)
