"""Unit tests for the desktop background JobManager."""
from __future__ import annotations

import sys
import threading
import time
import unittest
from http import HTTPStatus
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import subprocess  # noqa: E402

from desktop.job_manager import (  # noqa: E402
    CANCELLED,
    FAILED,
    JobBusyError,
    JobManager,
    ProcessRegistry,
    RC_CANCELLED,
    RC_TIMEOUT,
    RUNNING,
    SUCCEEDED,
    supervise_process,
)


def _spawn(code: str) -> subprocess.Popen:
    kwargs: dict = {}
    if not sys.platform.startswith("win"):
        kwargs["start_new_session"] = True
    return subprocess.Popen([sys.executable, "-c", code], **kwargs)


def _wait_for(predicate, timeout: float = 5.0, interval: float = 0.01) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


class JobManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mgr = JobManager(max_workers=4)
        self.addCleanup(self.mgr.shutdown)

    def test_submit_runs_work_and_captures_result(self) -> None:
        def work(_cancel: threading.Event) -> tuple[int, dict]:
            return HTTPStatus.OK, {"ok": True, "data": {"value": 42}}

        rec = self.mgr.submit("job-a", work)
        self.assertTrue(_wait_for(lambda: rec.state == SUCCEEDED))
        self.assertEqual(rec.result, (HTTPStatus.OK, {"ok": True, "data": {"value": 42}}))
        self.assertIsNotNone(rec.started_at)
        self.assertIsNotNone(rec.finished_at)
        self.assertIsNone(rec.error)

    def test_failed_work_captures_error(self) -> None:
        def work(_cancel: threading.Event) -> tuple[int, dict]:
            raise RuntimeError("boom")

        rec = self.mgr.submit("job-fail", work)
        self.assertTrue(_wait_for(lambda: rec.state == FAILED))
        self.assertEqual(rec.error, "boom")
        self.assertIsNone(rec.result)

    def test_concurrent_submit_same_id_is_busy(self) -> None:
        gate = threading.Event()

        def work(_cancel: threading.Event) -> tuple[int, dict]:
            gate.wait(timeout=5)
            return HTTPStatus.OK, {"ok": True, "data": {}}

        rec = self.mgr.submit("job-busy", work)
        self.assertTrue(_wait_for(lambda: rec.state == RUNNING))
        with self.assertRaises(JobBusyError):
            self.mgr.submit("job-busy", work)
        gate.set()
        self.assertTrue(_wait_for(lambda: rec.state == SUCCEEDED))

    def test_resubmit_after_completion_is_allowed(self) -> None:
        def work(_cancel: threading.Event) -> tuple[int, dict]:
            return HTTPStatus.OK, {"ok": True, "data": {}}

        rec1 = self.mgr.submit("job-reuse", work)
        self.assertTrue(_wait_for(lambda: rec1.state == SUCCEEDED))
        rec2 = self.mgr.submit("job-reuse", work)
        self.assertTrue(_wait_for(lambda: rec2.state == SUCCEEDED))
        self.assertIsNot(rec1, rec2)

    def test_cooperative_cancel_marks_cancelled(self) -> None:
        started = threading.Event()

        def work(cancel: threading.Event) -> tuple[int, dict]:
            started.set()
            # Simulate a stage loop that checks the cancel flag between steps.
            for _ in range(500):
                if cancel.is_set():
                    break
                time.sleep(0.01)
            return HTTPStatus.OK, {"ok": True, "data": {}}

        rec = self.mgr.submit("job-cancel", work)
        self.assertTrue(started.wait(timeout=5))
        self.assertTrue(self.mgr.request_cancel("job-cancel"))
        self.assertTrue(_wait_for(lambda: rec.state == CANCELLED))

    def test_request_cancel_unknown_returns_false(self) -> None:
        self.assertFalse(self.mgr.request_cancel("nope"))

    def test_get_and_is_active(self) -> None:
        gate = threading.Event()

        def work(_cancel: threading.Event) -> tuple[int, dict]:
            gate.wait(timeout=5)
            return HTTPStatus.OK, {"ok": True, "data": {}}

        self.assertIsNone(self.mgr.get("missing"))
        rec = self.mgr.submit("job-active", work)
        self.assertTrue(_wait_for(lambda: self.mgr.is_active("job-active")))
        self.assertIs(self.mgr.get("job-active"), rec)
        gate.set()
        self.assertTrue(_wait_for(lambda: not self.mgr.is_active("job-active")))

    def test_public_dict_shape(self) -> None:
        def work(_cancel: threading.Event) -> tuple[int, dict]:
            return HTTPStatus.OK, {"ok": True, "data": {"n": 1}}

        rec = self.mgr.submit("job-dict", work)
        self.assertTrue(_wait_for(lambda: rec.state == SUCCEEDED))
        pub = rec.public_dict()
        self.assertEqual(pub["job_id"], "job-dict")
        self.assertEqual(pub["state"], SUCCEEDED)
        self.assertEqual(pub["result"], {"ok": True, "data": {"n": 1}})
        self.assertEqual(pub["result_status"], HTTPStatus.OK)
        self.assertFalse(pub["cancel_requested"])
        self.assertNotIn("cancel_event", pub)


class AsyncRunDispatchTest(unittest.TestCase):
    """Integration: run handlers dispatch to JOB_MANAGER when async is requested."""

    def setUp(self) -> None:
        import tempfile

        from desktop import server as desktop_server

        self.server = desktop_server
        self.tmp = Path(tempfile.mkdtemp(prefix="phase24_async_"))
        self.addCleanup(self._cleanup)
        self._orig_work = desktop_server._run_until_edit_work

    def _cleanup(self) -> None:
        import shutil

        self.server._run_until_edit_work = self._orig_work  # type: ignore[assignment]
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _progress(self) -> dict:
        status, payload = self.server.handle_job_progress({"job_workspace": str(self.tmp)})
        self.assertEqual(status, HTTPStatus.OK)
        return payload["data"]

    def test_sync_mode_returns_result_inline(self) -> None:
        self.server._run_until_edit_work = (  # type: ignore[assignment]
            lambda body, jw: (HTTPStatus.OK, {"ok": True, "data": {"stub": "sync"}})
        )
        status, payload = self.server.handle_run_until_edit(
            {"job_workspace": str(self.tmp), "project_name": "p"}
        )
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["stub"], "sync")

    def test_async_mode_returns_job_id_then_completes(self) -> None:
        self.server._run_until_edit_work = (  # type: ignore[assignment]
            lambda body, jw: (HTTPStatus.OK, {"ok": True, "data": {"stub": "async"}})
        )
        status, payload = self.server.handle_run_until_edit(
            {"job_workspace": str(self.tmp), "project_name": "p", "async": True}
        )
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["job_id"], str(self.tmp))
        self.assertEqual(payload["data"]["state"], "running")

        self.assertTrue(_wait_for(lambda: self._progress()["job"]["state"] == "succeeded"))
        job = self._progress()["job"]
        self.assertEqual(job["result"], {"ok": True, "data": {"stub": "async"}})

    def test_async_busy_returns_conflict(self) -> None:
        gate = threading.Event()
        self.addCleanup(gate.set)

        def slow(body, jw):
            gate.wait(timeout=5)
            return HTTPStatus.OK, {"ok": True, "data": {}}

        self.server._run_until_edit_work = slow  # type: ignore[assignment]
        first = self.server.handle_run_until_edit(
            {"job_workspace": str(self.tmp), "project_name": "p", "async": True}
        )
        self.assertEqual(first[0], HTTPStatus.OK)
        self.assertTrue(_wait_for(lambda: self._progress()["job"]["state"] == "running"))
        status, payload = self.server.handle_run_until_edit(
            {"job_workspace": str(self.tmp), "project_name": "p", "async": True}
        )
        self.assertEqual(status, HTTPStatus.CONFLICT)
        self.assertEqual(payload["error"]["code"], "job_busy")
        gate.set()

    def test_cancel_job_requests_cancellation(self) -> None:
        gate = threading.Event()
        self.addCleanup(gate.set)

        def slow(body, jw):
            gate.wait(timeout=5)
            return HTTPStatus.OK, {"ok": True, "data": {}}

        self.server._run_until_edit_work = slow  # type: ignore[assignment]
        self.server.handle_run_until_edit(
            {"job_workspace": str(self.tmp), "project_name": "p", "async": True}
        )
        self.assertTrue(_wait_for(lambda: self._progress()["job"]["state"] == "running"))
        status, payload = self.server.handle_cancel_job({"job_workspace": str(self.tmp)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["data"]["cancel_requested"])
        self.assertTrue(_wait_for(lambda: self._progress()["job"]["cancel_requested"]))
        gate.set()

    def test_cancel_job_unknown_returns_404(self) -> None:
        import tempfile

        other = Path(tempfile.mkdtemp(prefix="phase24_nojob_"))
        try:
            status, payload = self.server.handle_cancel_job({"job_workspace": str(other)})
            self.assertEqual(status, HTTPStatus.NOT_FOUND)
            self.assertEqual(payload["error"]["code"], "job_not_found")
        finally:
            import shutil

            shutil.rmtree(other, ignore_errors=True)


class SuperviseProcessTest(unittest.TestCase):
    def test_normal_completion_returns_exit_code(self) -> None:
        proc = _spawn("import sys; sys.exit(0)")
        self.assertEqual(supervise_process(proc, poll_interval=0.05), 0)

    def test_nonzero_exit_code_passed_through(self) -> None:
        proc = _spawn("import sys; sys.exit(7)")
        self.assertEqual(supervise_process(proc, poll_interval=0.05), 7)

    def test_cancel_terminates_process(self) -> None:
        proc = _spawn("import time; time.sleep(30)")
        cancel = threading.Event()
        registry = ProcessRegistry()
        result: dict = {}

        def run() -> None:
            result["rc"] = supervise_process(
                proc, cancel_event=cancel, registry=registry, job_id="j", poll_interval=0.05
            )

        th = threading.Thread(target=run)
        th.start()
        time.sleep(0.2)  # let supervise_process start and register the proc
        cancel.set()
        th.join(timeout=10)
        self.assertFalse(th.is_alive())
        self.assertEqual(result["rc"], RC_CANCELLED)
        self.assertIsNotNone(proc.poll())

    def test_timeout_terminates_process(self) -> None:
        proc = _spawn("import time; time.sleep(30)")
        rc = supervise_process(proc, timeout_s=0.5, poll_interval=0.05)
        self.assertEqual(rc, RC_TIMEOUT)
        self.assertIsNotNone(proc.poll())


class RunJobSubprocessIntegrationTest(unittest.TestCase):
    """The async run context makes _run_job_common spawn run_job as a child."""

    def test_async_context_runs_run_job_as_subprocess(self) -> None:
        import shutil
        import tempfile

        from desktop import server

        jw = Path(tempfile.mkdtemp(prefix="phase24_subproc_"))
        self.addCleanup(lambda: shutil.rmtree(jw, ignore_errors=True))
        (jw / "input").mkdir(parents=True, exist_ok=True)  # but no source.mp4

        cancel = threading.Event()
        token = server._RUN_CONTEXT.set(
            {"job_id": str(jw), "cancel_event": cancel, "timeout_s": 120}
        )
        try:
            rc = server._run_job_common(
                jw,
                project_name="p",
                api_key="",
                source_language="",
                to_stage="transcribed",
                translate_backend="block_v2",
                tts_provider="edge_tts",
                tts_voice="",
                tts_rate="",
                mix_mode="replace_original_speech",
                enable_translation_qa=False,
                enable_source_cleanup=False,
            )
        finally:
            server._RUN_CONTEXT.reset(token)
        # No input video -> run_job fails, but the key assertion is that it ran
        # out-of-process: run.log carries the subprocess marker.
        self.assertNotEqual(rc, 0)
        log_text = (jw / "run.log").read_text(encoding="utf-8", errors="replace")
        self.assertIn("(subprocess)", log_text)


class ProcessRegistryTest(unittest.TestCase):
    def test_terminate_kills_registered_process(self) -> None:
        reg = ProcessRegistry()
        proc = _spawn("import time; time.sleep(30)")
        reg.register("k", proc)
        self.assertTrue(reg.terminate("k"))
        self.assertTrue(_wait_for(lambda: proc.poll() is not None))
        reg.unregister("k")

    def test_terminate_unknown_returns_false(self) -> None:
        self.assertFalse(ProcessRegistry().terminate("nope"))


if __name__ == "__main__":
    unittest.main()
