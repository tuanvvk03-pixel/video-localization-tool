"""Phase 3 acceptance: single-video workflow orchestrator CLI.

Covers the parts that can run without external services (OpenAI/edge-tts/ffmpeg):
- init-job: workspace creation, video copy, fingerprint
- run-after-edit refuses when edited_voice.srt is missing
- run-until-edit delegates to run_job with voice-mode argv (verified via monkeypatch)
- run-after-edit marks voice_edited and delegates when edited_voice.srt exists
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import app_cli


SAMPLE_VOICE_SRT = (
    "1\n00:00:00,000 --> 00:00:02,000\nXin chao the gioi\n\n"
    "2\n00:00:02,000 --> 00:00:04,000\nCau hai\n\n"
)


def _run(argv: list[str]) -> tuple[int, dict]:
    buf_out = io.StringIO()
    with contextlib.redirect_stdout(buf_out):
        rc = app_cli.main(argv)
    lines = [ln for ln in buf_out.getvalue().splitlines() if ln.strip()]
    payload = json.loads(lines[-1]) if lines else {}
    return rc, payload


class Phase3AppCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase3_app_cli_"))
        self.workspace_root = self.tmp_root / "workspaces"
        self.workspace_root.mkdir()
        self.fake_video = self.tmp_root / "clip my video.mp4"
        self.fake_video.write_bytes(b"\x00\x01FAKEVIDEO")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def _init(self) -> Path:
        rc, payload = _run(
            [
                "init-job",
                "--video",
                str(self.fake_video),
                "--workspace-root",
                str(self.workspace_root),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        return Path(payload["data"]["job_workspace"])

    def _seed_voice_workspace(self, jw: Path) -> None:
        (jw / "artifacts" / "translate").mkdir(parents=True, exist_ok=True)
        (jw / "artifacts" / "translate" / "translated_voice.srt").write_text(
            SAMPLE_VOICE_SRT, encoding="utf-8"
        )

    def test_init_job_copies_video_and_returns_fingerprint(self) -> None:
        jw = self._init()
        self.assertTrue((jw / "input" / "source.mp4").is_file())
        self.assertEqual(jw.name, "clip-my-video")
        rc, payload = _run(
            [
                "init-job",
                "--video",
                str(self.fake_video),
                "--workspace-root",
                str(self.workspace_root),
            ]
        )
        self.assertEqual(rc, 1)
        self.assertEqual(payload["error"]["code"], "workspace_exists")

    def test_init_job_missing_video_errors(self) -> None:
        rc, payload = _run(
            [
                "init-job",
                "--video",
                str(self.tmp_root / "nope.mp4"),
                "--workspace-root",
                str(self.workspace_root),
            ]
        )
        self.assertEqual(rc, 1)
        self.assertEqual(payload["error"]["code"], "video_not_found")

    def test_probe_video_url_returns_payload(self) -> None:
        orig = app_cli.probe_video_url
        app_cli.probe_video_url = lambda _url: {  # type: ignore[assignment]
            "title": "Demo Video",
            "video_id": "abc123",
        }
        try:
            rc, payload = _run(["probe-video-url", "--url", "https://example.com/watch?v=abc123"])
        finally:
            app_cli.probe_video_url = orig  # type: ignore[assignment]
        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["video_id"], "abc123")

    def test_init_job_from_url_returns_download_payload(self) -> None:
        orig = app_cli.init_job_from_url
        app_cli.init_job_from_url = lambda **_kwargs: {  # type: ignore[assignment]
            "job_id": "demo-video",
            "job_workspace": str(self.workspace_root / "demo-video"),
            "input_video_path": str(self.workspace_root / "demo-video" / "input" / "source.mp4"),
            "download_manifest_path": str(self.workspace_root / "demo-video" / "artifacts" / "download" / "download_manifest.json"),
        }
        try:
            rc, payload = _run(
                [
                    "init-job-from-url",
                    "--url",
                    "https://example.com/watch?v=abc123",
                    "--workspace-root",
                    str(self.workspace_root),
                ]
            )
        finally:
            app_cli.init_job_from_url = orig  # type: ignore[assignment]
        self.assertEqual(rc, 0, msg=payload)
        self.assertEqual(payload["data"]["job_id"], "demo-video")

    def test_run_after_edit_refuses_when_edited_voice_missing(self) -> None:
        jw = self._init()
        rc, payload = _run(
            [
                "run-after-edit",
                "--job-workspace",
                str(jw),
                "--project-name",
                "demo",
            ]
        )
        self.assertEqual(rc, 1)
        self.assertEqual(payload["error"]["code"], "edited_voice_missing")

    def test_run_until_edit_delegates_with_voice_argv(self) -> None:
        jw = self._init()
        self._seed_voice_workspace(jw)

        captured: dict[str, list[str]] = {}

        def fake_run_job(argv: list[str]) -> int:
            captured["argv"] = list(argv)
            return 0

        orig = app_cli.run_job.main
        app_cli.run_job.main = fake_run_job  # type: ignore[assignment]
        try:
            rc, payload = _run(
                [
                    "run-until-edit",
                    "--job-workspace",
                    str(jw),
                    "--project-name",
                    "demo",
                ]
            )
        finally:
            app_cli.run_job.main = orig  # type: ignore[assignment]

        self.assertEqual(rc, 0, msg=payload)
        argv = captured["argv"]
        self.assertIn("--to-stage", argv)
        self.assertEqual(argv[argv.index("--to-stage") + 1], "translated")
        self.assertIn("--finalize-mode", argv)
        self.assertEqual(argv[argv.index("--finalize-mode") + 1], "voice")
        self.assertIn("--translate-backend", argv)
        self.assertEqual(argv[argv.index("--translate-backend") + 1], "block_v2")

        self.assertTrue((jw / "artifacts" / "edit" / "edited_voice.srt").is_file())
        self.assertEqual(payload["data"]["voice_edit_status"], "voice_edit_pending")
        self.assertEqual(payload["data"]["next_action"], "edit_edited_voice_srt")

    def test_run_after_edit_marks_and_delegates_with_render_argv(self) -> None:
        jw = self._init()
        self._seed_voice_workspace(jw)
        # Pretend the user already seeded + saved the edit.
        edit_dir = jw / "artifacts" / "edit"
        edit_dir.mkdir(parents=True, exist_ok=True)
        (edit_dir / "edited_voice.srt").write_text(SAMPLE_VOICE_SRT, encoding="utf-8")

        captured: dict[str, list[str]] = {}

        def fake_run_job(argv: list[str]) -> int:
            captured["argv"] = list(argv)
            return 0

        orig = app_cli.run_job.main
        app_cli.run_job.main = fake_run_job  # type: ignore[assignment]
        try:
            rc, payload = _run(
                [
                    "run-after-edit",
                    "--job-workspace",
                    str(jw),
                    "--project-name",
                    "demo",
                    "--to-stage",
                    "rendered",
                ]
            )
        finally:
            app_cli.run_job.main = orig  # type: ignore[assignment]

        self.assertEqual(rc, 0, msg=payload)
        argv = captured["argv"]
        self.assertEqual(argv[argv.index("--to-stage") + 1], "rendered")
        self.assertEqual(argv[argv.index("--finalize-mode") + 1], "voice")

        state = json.loads((jw / "video_state.json").read_text(encoding="utf-8"))
        self.assertTrue(state.get("voice_edited"))
        self.assertEqual(state.get("voice_edit_status"), "voice_edited")

    def test_run_until_edit_reports_missing_translated_voice(self) -> None:
        jw = self._init()

        orig = app_cli.run_job.main
        app_cli.run_job.main = lambda _argv: 0  # type: ignore[assignment]
        try:
            rc, payload = _run(
                [
                    "run-until-edit",
                    "--job-workspace",
                    str(jw),
                    "--project-name",
                    "demo",
                ]
            )
        finally:
            app_cli.run_job.main = orig  # type: ignore[assignment]

        self.assertEqual(rc, 1)
        self.assertEqual(payload["error"]["code"], "translated_voice_missing")

    def test_preflight_returns_ok_payload(self) -> None:
        captured: dict[str, object] = {}
        orig = app_cli.build_preflight_report

        def fake_report(**kwargs):
            captured.update(kwargs)
            return {"ok": True, "checks": [{"name": "demo", "ok": True, "required": True}]}

        app_cli.build_preflight_report = fake_report  # type: ignore[assignment]
        try:
            rc, payload = _run(
                [
                    "preflight",
                    "--job-workspace",
                    str(self.workspace_root / "x"),
                    "--translate-backend",
                    "block_v2",
                    "--tts-provider",
                    "edge_tts",
                    "--require-download",
                    "--require-input",
                    "--require-render",
                ]
            )
        finally:
            app_cli.build_preflight_report = orig  # type: ignore[assignment]
        self.assertEqual(rc, 0, msg=payload)
        self.assertTrue(payload["ok"])
        self.assertTrue(captured["require_download"])
        self.assertTrue(captured["require_input"])
        self.assertTrue(captured["require_render"])

    def test_preflight_returns_error_payload_when_checks_fail(self) -> None:
        orig = app_cli.build_preflight_report
        app_cli.build_preflight_report = lambda **_kwargs: {  # type: ignore[assignment]
            "ok": False,
            "checks": [{"name": "demo", "ok": False, "required": True}],
        }
        try:
            rc, payload = _run(["preflight"])
        finally:
            app_cli.build_preflight_report = orig  # type: ignore[assignment]
        self.assertEqual(rc, 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "preflight_failed")
        self.assertIn("data", payload)

    def test_doctor_alias_returns_same_payload_contract(self) -> None:
        orig = app_cli.build_preflight_report
        app_cli.build_preflight_report = lambda **_kwargs: {  # type: ignore[assignment]
            "ok": True,
            "profile": "runtime_doctor",
            "checks": [{"name": "demo", "ok": True, "required": True}],
        }
        try:
            rc, payload = _run(["doctor"])
        finally:
            app_cli.build_preflight_report = orig  # type: ignore[assignment]
        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["profile"], "runtime_doctor")


if __name__ == "__main__":
    unittest.main()
