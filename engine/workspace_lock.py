from __future__ import annotations

import json
import os
import socket
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class WorkspaceLockError(RuntimeError):
    def __init__(self, lock_path: Path, details: dict[str, Any] | None = None) -> None:
        super().__init__(f"Workspace is already locked: {lock_path}")
        self.lock_path = lock_path
        self.details = details or {}


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _lock_payload(owner: str) -> dict[str, Any]:
    return {
        "version": 1,
        "owner": owner,
        "owner_token": uuid.uuid4().hex,
        "pid": os.getpid(),
        "thread_id": threading.get_ident(),
        "hostname": socket.gethostname(),
        "acquired_at_unix": time.time(),
    }


def describe_lock_details(details: dict[str, Any] | None) -> str:
    if not isinstance(details, dict) or not details:
        return "lock is held by another process"
    owner = str(details.get("owner") or "unknown")
    pid = details.get("pid")
    host = str(details.get("hostname") or "unknown-host")
    acquired = details.get("acquired_at_unix")
    parts = [f"owner={owner}", f"pid={pid}", f"host={host}"]
    if isinstance(acquired, (int, float)):
        parts.append(f"acquired_at_unix={float(acquired):.3f}")
    return ", ".join(parts)


@contextmanager
def acquire_workspace_lock(
    job_workspace: str | Path,
    *,
    owner: str = "run_job",
) -> Iterator[Path]:
    jw = Path(job_workspace).expanduser().resolve()
    lock_dir = jw / ".locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / f"{owner}.lock.json"
    payload = _lock_payload(owner)

    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as e:
        raise WorkspaceLockError(lock_path, _load_json(lock_path)) from e

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    except Exception:
        try:
            lock_path.unlink()
        except OSError:
            pass
        raise

    try:
        yield lock_path
    finally:
        current = _load_json(lock_path)
        if current is not None and current.get("owner_token") != payload["owner_token"]:
            return
        try:
            lock_path.unlink()
        except OSError:
            pass
