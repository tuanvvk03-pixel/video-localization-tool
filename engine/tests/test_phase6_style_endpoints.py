"""Phase 6 — HTTP endpoint tests for subtitle style."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from desktop import server


class VideoStyleEndpointTest(unittest.TestCase):
    def test_save_then_get_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            jw = Path(td)
            status, payload = server.handle_save_video_style(
                {
                    "job_workspace": str(jw),
                    "style": {
                        "subtitle_font": "Arial",
                        "subtitle_background_color": "#112233",
                        "bold": True,
                        "italic": False,
                        "align": "center",
                    },
                }
            )
            self.assertEqual(status, 200)
            self.assertTrue(payload["ok"], payload)

            status, payload = server.handle_get_video_style({"job_workspace": str(jw)})
            self.assertEqual(status, 200)
            self.assertEqual(
                payload["data"]["style"],
                {
                    "subtitle_font": "Arial",
                    "subtitle_background_color": "#112233",
                    "bold": True,
                    "italic": False,
                    "align": "center",
                },
            )

    def test_get_empty_when_no_file(self):
        with tempfile.TemporaryDirectory() as td:
            status, payload = server.handle_get_video_style({"job_workspace": td})
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["style"], {})

    def test_save_rejects_bad_hex(self):
        with tempfile.TemporaryDirectory() as td:
            status, payload = server.handle_save_video_style(
                {"job_workspace": td, "style": {"subtitle_background_color": "red"}}
            )
            self.assertEqual(status, 400)
            self.assertEqual(payload["error"]["code"], "invalid_style")

    def test_save_requires_job_workspace(self):
        status, payload = server.handle_save_video_style({"style": {}})
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "missing_field")

    def test_save_rejects_non_object_style(self):
        with tempfile.TemporaryDirectory() as td:
            status, payload = server.handle_save_video_style(
                {"job_workspace": td, "style": "not a dict"}
            )
            self.assertEqual(status, 400)


class ProjectStyleEndpointTest(unittest.TestCase):
    def test_save_then_get_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            pr = Path(td)
            status, payload = server.handle_save_project_style(
                {"project_root": str(pr), "style": {"subtitle_font": "Roboto"}}
            )
            self.assertEqual(status, 200, payload)
            # verify file lives at the expected path
            self.assertTrue((pr / "style" / "global_subtitle_style.json").is_file())

            status, payload = server.handle_get_project_style({"project_root": str(pr)})
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["style"], {"subtitle_font": "Roboto"})

    def test_get_rejects_missing_project(self):
        status, payload = server.handle_get_project_style(
            {"project_root": "/definitely/does/not/exist/xyz"}
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "project_missing")


class RunAfterEditForwardsStyleArgsTest(unittest.TestCase):
    """/api/run-after-edit should propagate subtitle/TTS args to run_job argv."""

    def test_subtitle_mode_and_project_root_propagate(self):
        with tempfile.TemporaryDirectory() as td:
            jw = Path(td)
            (jw / "artifacts" / "edit").mkdir(parents=True)
            (jw / "artifacts" / "edit" / "edited_voice.srt").write_text(
                "1\n00:00:00,000 --> 00:00:01,000\nhi\n", encoding="utf-8"
            )

            captured: list[list[str]] = []

            original_main = server.run_job.main

            def fake_main(argv):
                captured.append(list(argv))
                return 0

            server.run_job.main = fake_main
            try:
                status, payload = server.handle_run_after_edit(
                    {
                        "job_workspace": str(jw),
                        "project_name": "p",
                        "subtitle_mode": "burn",
                        "project_root": str(jw.parent),
                        "tts_provider": "azure_tts",
                        "tts_rate": 15,
                        "to_stage": "rendered",
                    }
                )
            finally:
                server.run_job.main = original_main

            self.assertEqual(status, 200, payload)
            self.assertEqual(len(captured), 1)
            argv = captured[0]
            self.assertIn("--render-subtitle-mode", argv)
            self.assertEqual(argv[argv.index("--render-subtitle-mode") + 1], "burn")
            self.assertIn("--project-root", argv)
            self.assertIn("--tts-provider", argv)
            self.assertEqual(argv[argv.index("--tts-provider") + 1], "azure_tts")
            self.assertIn("--tts-rate", argv)
            self.assertEqual(argv[argv.index("--tts-rate") + 1], "+15%")


class PingEndpointTest(unittest.TestCase):
    def test_ping_returns_ok(self):
        status, payload = server.handle_ping({})
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["status"], "ok")


if __name__ == "__main__":
    unittest.main()
