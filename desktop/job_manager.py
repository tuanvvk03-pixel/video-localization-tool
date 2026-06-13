"""Background job runner for the desktop server.

The desktop server historically ran each pipeline job *inline* on the HTTP
request thread: `/api/run-until-edit` blocked for the whole transcribe ->
translate (or render) run before responding. That ties up a worker thread for
minutes, offers no way to cancel, and loses the result if the connection drops.

`JobManager` decouples execution from the request: a handler validates input,
then `submit()`s the heavy work and returns a job id immediately. The work runs
on a small thread pool; the UI polls for state/result. State lifecycle:

    queued -> running -> succeeded | failed | cancelled

Keyed by job id (the resolved job-workspace path), so the same workspace cannot
run twice concurrently — a second submit while one is active raises JobBusyError.

Cancellation is cooperative: the work callable receives a `threading.Event` and
should check it between steps. A job cancelled before it starts never runs.
(Hard-killing an in-flight in-process stage is out of scope here; that needs the
job to run as a child process — a planned follow-up.)
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

# Process exit codes used when we stop a child ourselves (mirrors shell
# conventions: 130 = terminated by SIGINT-equivalent, 124 = timeout per GNU
# `timeout`). The job handlers treat any non-zero rc as a failed run.
RC_CANCELLED = 130
RC_TIMEOUT = 124

# State constants (plain strings so they serialize straight into JSON).
QUEUED = "queued"
RUNNING = "running"
SUCCEEDED = "succeeded"
FAILED = "failed"
CANCELLED = "cancelled"

ACTIVE_STATES = frozenset({QUEUED, RUNNING})

# A unit of work receives the cancel event and returns the (status, payload)
# tuple the HTTP handler would otherwise have returned synchronously.
JobWork = Callable[[threading.Event], "tuple[int, dict[str, Any]]"]


class JobBusyError(RuntimeError):
    """Raised when submitting a job whose id is already queued or running."""


@dataclass
class JobRecord:
    job_id: str
    state: str
    submitted_at: float
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    result: Optional[tuple[int, dict[str, Any]]] = None
    error: Optional[str] = None
    cancel_event: threading.Event = field(default_factory=threading.Event)

    def public_dict(self) -> dict[str, Any]:
        """JSON-safe snapshot for /api/job-progress (omits the cancel event)."""
        return {
            "job_id": self.job_id,
            "state": self.state,
            "submitted_at": self.submitted_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "cancel_requested": self.cancel_event.is_set(),
            "error": self.error,
            # result is the handler payload; expose only when finished so the UI
            # can render the final status the synchronous call used to return.
            "result": self.result[1] if (self.result and self.state == SUCCEEDED) else None,
            "result_status": self.result[0] if self.result else None,
        }


class JobManager:
    def __init__(self, max_workers: int = 4) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="vljob")
        self._records: dict[str, JobRecord] = {}
        self._lock = threading.RLock()

    def submit(self, job_id: str, work: JobWork) -> JobRecord:
        """Queue `work` under `job_id`; raise JobBusyError if one is active."""
        with self._lock:
            existing = self._records.get(job_id)
            if existing is not None and existing.state in ACTIVE_STATES:
                raise JobBusyError(job_id)
            record = JobRecord(job_id=job_id, state=QUEUED, submitted_at=time.time())
            self._records[job_id] = record
        self._executor.submit(self._run, record, work)
        return record

    def _run(self, record: JobRecord, work: JobWork) -> None:
        with self._lock:
            if record.cancel_event.is_set():
                record.state = CANCELLED
                record.finished_at = time.time()
                return
            record.state = RUNNING
            record.started_at = time.time()
        try:
            result = work(record.cancel_event)
        except Exception as exc:  # noqa: BLE001 - boundary: capture for the poller
            with self._lock:
                record.error = str(exc)
                record.state = FAILED
                record.finished_at = time.time()
            return
        with self._lock:
            record.result = result
            record.state = CANCELLED if record.cancel_event.is_set() else SUCCEEDED
            record.finished_at = time.time()

    def get(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._records.get(job_id)

    def is_active(self, job_id: str) -> bool:
        with self._lock:
            rec = self._records.get(job_id)
            return rec is not None and rec.state in ACTIVE_STATES

    def request_cancel(self, job_id: str) -> bool:
        """Signal cooperative cancellation. Returns False if no such job."""
        with self._lock:
            rec = self._records.get(job_id)
            if rec is None:
                return False
            rec.cancel_event.set()
            return True

    def shutdown(self, *, wait: bool = False) -> None:
        self._executor.shutdown(wait=wait)


def terminate_process_tree(proc: "subprocess.Popen[Any]") -> None:
    """Kill a child process *and its descendants* (e.g. ffmpeg spawned by run_job).

    Terminating only the direct child would orphan its grandchildren, so we
    kill the whole tree: ``taskkill /T`` on Windows, the process group on POSIX
    (the child must have been started with ``start_new_session=True``).
    """
    if proc.poll() is not None:
        return
    try:
        if sys.platform.startswith("win"):
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                check=False,
            )
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (OSError, ProcessLookupError):
        try:
            proc.kill()
        except OSError:
            pass


class ProcessRegistry:
    """Tracks live child processes by job id so a job can be force-terminated."""

    def __init__(self) -> None:
        self._procs: dict[str, "subprocess.Popen[Any]"] = {}
        self._lock = threading.RLock()

    def register(self, job_id: str, proc: "subprocess.Popen[Any]") -> None:
        with self._lock:
            self._procs[job_id] = proc

    def unregister(self, job_id: str) -> None:
        with self._lock:
            self._procs.pop(job_id, None)

    def terminate(self, job_id: str) -> bool:
        """Force-kill the tracked process tree for job_id. False if none."""
        with self._lock:
            proc = self._procs.get(job_id)
        if proc is None:
            return False
        terminate_process_tree(proc)
        return True


def supervise_process(
    proc: "subprocess.Popen[Any]",
    *,
    cancel_event: Optional[threading.Event] = None,
    timeout_s: Optional[float] = None,
    poll_interval: float = 0.25,
    registry: Optional[ProcessRegistry] = None,
    job_id: Optional[str] = None,
) -> int:
    """Wait for `proc`, force-killing its tree on cancel or timeout.

    Returns the child's exit code, or RC_CANCELLED / RC_TIMEOUT when we stopped
    it. Registers the process in `registry` (if given) for the duration so an
    out-of-band cancel request can reach it.
    """
    if registry is not None and job_id is not None:
        registry.register(job_id, proc)
    start = time.time()
    try:
        while True:
            try:
                return proc.wait(timeout=poll_interval)
            except subprocess.TimeoutExpired:
                pass
            if cancel_event is not None and cancel_event.is_set():
                terminate_process_tree(proc)
                _reap(proc)
                return RC_CANCELLED
            if timeout_s and (time.time() - start) > timeout_s:
                terminate_process_tree(proc)
                _reap(proc)
                return RC_TIMEOUT
    finally:
        if registry is not None and job_id is not None:
            registry.unregister(job_id)


def _reap(proc: "subprocess.Popen[Any]") -> None:
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except OSError:
            pass
