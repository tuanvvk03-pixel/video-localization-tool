"""Shared helpers for durable JSON state writes.

Pipeline stages and the desktop server repeatedly rewrite small JSON state files
(``job_state.json``, ``video_state.json``, per-stage manifests, settings). A
plain ``path.write_text(...)`` truncates the destination first, so a crash or a
concurrent reader can observe a half-written / empty file. ``write_json_atomic``
removes that window: it writes to a sibling temp file, flushes+fsyncs, then
``os.replace`` swaps it into place (atomic on POSIX, and on Windows when the
temp file and destination share a volume — they always do here, being siblings).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def write_json_atomic(path: str | Path, payload: Any, *, indent: int = 2) -> None:
    """Serialize ``payload`` to ``path`` atomically with a trailing newline."""
    dst = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=indent) + "\n"
    tmp = dst.with_name(f"{dst.name}.tmp.{os.getpid()}")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, dst)
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
