from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.preflight import build_preflight_report


class PreflightReportTest(unittest.TestCase):
    @staticmethod
    def _probe_ok(*_args, **_kwargs):
        return SimpleNamespace(returncode=0, stdout="ffmpeg version 6.1\n", stderr="")

    def test_block_v2_requires_api_key(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            report = build_preflight_report(
                translate_backend="block_v2",
                tts_provider="edge_tts",
            )
        self.assertFalse(report["ok"])
        checks = {c["name"]: c for c in report["checks"]}
        self.assertFalse(checks["openai_api_key"]["ok"])
        self.assertEqual(report["profile"], "runtime_doctor")

    def test_legacy_translate_does_not_require_api_key(self) -> None:
        with mock.patch("engine.preflight.importlib.util.find_spec", return_value=object()), \
                mock.patch("engine.preflight.resolve_ffmpeg_executable", return_value=("ffmpeg", None)), \
                mock.patch("engine.preflight.subprocess.run", side_effect=self._probe_ok):
            report = build_preflight_report(
                translate_backend="legacy",
                tts_provider="edge_tts",
            )
        self.assertTrue(report["ok"])
        checks = {c["name"]: c for c in report["checks"]}
        self.assertTrue(checks["translate_backend"]["ok"])
        self.assertTrue(report["capabilities"]["translate_ready"])
        self.assertTrue(report["capabilities"]["tts_ready"])

    def test_edge_tts_reports_missing_package(self) -> None:
        def fake_find_spec(name: str):
            return None if name == "edge_tts" else object()

        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "x"}, clear=True), \
                mock.patch("engine.preflight.importlib.util.find_spec", side_effect=fake_find_spec), \
                mock.patch("engine.preflight.resolve_ffmpeg_executable", return_value=("ffmpeg", None)), \
                mock.patch("engine.preflight.subprocess.run", side_effect=self._probe_ok):
            report = build_preflight_report(
                translate_backend="block_v2",
                tts_provider="edge_tts",
            )
        self.assertFalse(report["ok"])
        checks = {c["name"]: c for c in report["checks"]}
        self.assertFalse(checks["edge_tts_package"]["ok"])
        self.assertTrue(checks["tts_network_contract"]["ok"])

    def test_azure_reports_missing_env(self) -> None:
        def fake_find_spec(name: str):
            return object() if name == "azure.cognitiveservices.speech" else None

        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "x"}, clear=True), \
                mock.patch("engine.preflight.importlib.util.find_spec", side_effect=fake_find_spec):
            report = build_preflight_report(
                translate_backend="block_v2",
                tts_provider="azure_tts",
            )
        self.assertFalse(report["ok"])
        checks = {c["name"]: c for c in report["checks"]}
        self.assertFalse(checks["azure_speech_config"]["ok"])

    def test_workspace_and_input_checks(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="phase9_preflight_"))
        try:
            jw = tmp / "job"
            (jw / "input").mkdir(parents=True)
            (jw / "input" / "source.mp4").write_bytes(b"x")
            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "x"}, clear=True), \
                    mock.patch("engine.preflight.probe_yt_dlp_health", return_value=(True, "ok", {"path": "yt-dlp.exe"})), \
                    mock.patch("engine.preflight.importlib.util.find_spec", return_value=object()), \
                    mock.patch("engine.preflight.resolve_ffmpeg_executable", return_value=("ffmpeg", None)), \
                    mock.patch("engine.preflight.resolve_ffprobe_executable", return_value="ffprobe"), \
                    mock.patch("engine.preflight.subprocess.run", side_effect=self._probe_ok):
                report = build_preflight_report(
                    job_workspace=jw,
                    translate_backend="block_v2",
                    tts_provider="edge_tts",
                    require_download=True,
                    require_input=True,
                    require_render=True,
                    require_long_video=True,
                )
            self.assertTrue(report["ok"])
            checks = {c["name"]: c for c in report["checks"]}
            self.assertTrue(checks["yt_dlp"]["ok"])
            self.assertTrue(checks["workspace_exists"]["ok"])
            self.assertTrue(checks["workspace_writable"]["ok"])
            self.assertTrue(checks["input_video"]["ok"])
            self.assertTrue(checks["ffprobe"]["ok"])
            self.assertTrue(report["capabilities"]["download_ready"])
            self.assertTrue(report["capabilities"]["render_ready"])
            self.assertTrue(report["capabilities"]["long_video_ready"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_require_download_reports_missing_yt_dlp(self) -> None:
        with mock.patch("engine.preflight.probe_yt_dlp_health", return_value=(False, "missing", {"path": None})), \
                mock.patch("engine.preflight.importlib.util.find_spec", return_value=object()), \
                mock.patch("engine.preflight.resolve_ffmpeg_executable", return_value=("ffmpeg", None)), \
                mock.patch("engine.preflight.subprocess.run", side_effect=self._probe_ok):
            report = build_preflight_report(
                translate_backend="legacy",
                tts_provider="edge_tts",
                require_download=True,
            )
        self.assertFalse(report["ok"])
        checks = {c["name"]: c for c in report["checks"]}
        self.assertFalse(checks["yt_dlp"]["ok"])
        self.assertFalse(report["capabilities"]["download_ready"])

    def test_ffmpeg_health_probe_failure_marks_report_not_ok(self) -> None:
        proc = SimpleNamespace(returncode=1, stdout="", stderr="bad ffmpeg")
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "x"}, clear=True), \
                mock.patch("engine.preflight.probe_yt_dlp_health", return_value=(True, "ok", {"path": "yt-dlp.exe"})), \
                mock.patch("engine.preflight.importlib.util.find_spec", return_value=object()), \
                mock.patch("engine.preflight.resolve_ffmpeg_executable", return_value=("ffmpeg", None)), \
                mock.patch("engine.preflight.resolve_ffprobe_executable", return_value="ffprobe"), \
                mock.patch("engine.preflight.subprocess.run", return_value=proc):
            report = build_preflight_report(
                translate_backend="block_v2",
                tts_provider="edge_tts",
                require_render=True,
            )
        self.assertFalse(report["ok"])
        checks = {c["name"]: c for c in report["checks"]}
        self.assertFalse(checks["ffmpeg"]["ok"])
        self.assertFalse(report["capabilities"]["render_ready"])


if __name__ == "__main__":
    unittest.main()
