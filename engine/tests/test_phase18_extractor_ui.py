"""Phase 18 — Extractor UI integration tests.

Covers the new /api/ocr-test-frame endpoint, source_provenance surfacing
on /api/load, extractor forwarding through _run_job_common /
handle_run_until_edit, import_config roundtrip for extractor fields, and
run_job.main forwarding --extractor/--ocr-* to run_transcribe_stage.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from http import HTTPStatus
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desktop import server as desktop_server  # noqa: E402
from engine import run_job, run_ocr_stage  # noqa: E402
from engine.ocr.base import OcrFrameResult, OcrLine  # noqa: E402


class _WorkspaceMixin:
    tmp_root: Path

    def _make_workspace(self, name: str = "job-a") -> Path:
        jw = self.tmp_root / name
        (jw / "input").mkdir(parents=True, exist_ok=True)
        (jw / "input" / "source.mp4").write_bytes(b"\x00FAKE")
        (jw / "artifacts" / "transcribe").mkdir(parents=True, exist_ok=True)
        return jw


class _StubProvider:
    def __init__(self, *, text: str = "你好世界", confidence: float = 0.9, device: str = "cpu") -> None:
        self._text = text
        self._confidence = confidence
        self._device = device

    def recognize_image(self, image_path: Path, *, language: str) -> OcrFrameResult:
        if not self._text:
            return OcrFrameResult(lines=[], device_used=self._device)
        line = OcrLine(text=self._text, confidence=self._confidence, bbox=(0, 0, 10, 10))
        return OcrFrameResult(lines=[line], device_used=self._device)

    def device_used(self) -> str:
        return self._device


def _fake_ffmpeg_run(*args, **kwargs):
    # ffmpeg writes a tiny PNG to the -vf crop output path (last positional arg).
    cmd = args[0]
    out_png = Path(cmd[-1])
    out_png.parent.mkdir(parents=True, exist_ok=True)
    out_png.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(16))
    return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")


class OcrTestFrameEndpointTest(_WorkspaceMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase18_ocrtest_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_missing_job_workspace_returns_400(self) -> None:
        status, payload = desktop_server.handle_ocr_test_frame({})
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "missing_field")

    def test_missing_input_video_returns_input_missing(self) -> None:
        jw = self.tmp_root / "empty"
        jw.mkdir(parents=True)
        status, payload = desktop_server.handle_ocr_test_frame({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "input_missing")

    def test_invalid_roi_returns_invalid_roi(self) -> None:
        jw = self._make_workspace()
        status, payload = desktop_server.handle_ocr_test_frame(
            {"job_workspace": str(jw), "roi": {"x": 1.5, "y": 0.0, "w": 0.5, "h": 0.5}}
        )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "invalid_roi")

    def test_invalid_device_returns_invalid_ocr_device(self) -> None:
        jw = self._make_workspace()
        status, payload = desktop_server.handle_ocr_test_frame(
            {"job_workspace": str(jw), "ocr_device": "tpu"}
        )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "invalid_ocr_device")

    def test_happy_path_returns_text_and_thumbnail(self) -> None:
        jw = self._make_workspace()
        provider = _StubProvider(text="晚安", confidence=0.88, device="cpu")
        with mock.patch.object(
            run_ocr_stage, "_probe_video", return_value=(12.5, 1280, 720)
        ), mock.patch(
            "desktop.server.subprocess.run", side_effect=_fake_ffmpeg_run
        ), mock.patch(
            "engine.ffmpeg_bins.resolve_ffmpeg_executable", return_value=("/usr/bin/ffmpeg", None)
        ), mock.patch(
            "engine.ocr.get_ocr_provider", return_value=provider
        ):
            status, payload = desktop_server.handle_ocr_test_frame(
                {
                    "job_workspace": str(jw),
                    "roi": {"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.20},
                    "frame_time_s": 2.5,
                    "ocr_language": "ch",
                    "ocr_device": "cpu",
                }
            )
        self.assertEqual(status, HTTPStatus.OK, payload)
        data = payload["data"]
        self.assertEqual(data["text"], "晚安")
        self.assertEqual(len(data["lines"]), 1)
        self.assertEqual(data["lines"][0]["text"], "晚安")
        self.assertAlmostEqual(data["confidence"], 0.88, places=3)
        self.assertEqual(data["video_width"], 1280)
        self.assertEqual(data["video_height"], 720)
        self.assertEqual(data["ocr_language"], "ch")
        self.assertEqual(data["ocr_device_requested"], "cpu")
        self.assertEqual(data["ocr_device_used"], "cpu")
        self.assertTrue(data["thumb_base64"])
        self.assertEqual(data["thumb_mime"], "image/png")
        self.assertIn("crop_px", data)
        for key in ("x", "y", "w", "h"):
            self.assertIn(key, data["crop_px"])

    def test_empty_text_returns_empty_lines(self) -> None:
        jw = self._make_workspace()
        provider = _StubProvider(text="", device="cpu")
        with mock.patch.object(
            run_ocr_stage, "_probe_video", return_value=(12.5, 1280, 720)
        ), mock.patch(
            "desktop.server.subprocess.run", side_effect=_fake_ffmpeg_run
        ), mock.patch(
            "engine.ffmpeg_bins.resolve_ffmpeg_executable", return_value=("/usr/bin/ffmpeg", None)
        ), mock.patch(
            "engine.ocr.get_ocr_provider", return_value=provider
        ):
            status, payload = desktop_server.handle_ocr_test_frame(
                {"job_workspace": str(jw), "roi": {"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.20}}
            )
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["text"], "")
        self.assertEqual(payload["data"]["lines"], [])
        self.assertEqual(payload["data"]["confidence"], 0.0)

    def test_ffmpeg_failure_returns_ffmpeg_failed(self) -> None:
        jw = self._make_workspace()

        def failing(*args, **kwargs):
            cmd = args[0]
            return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="boom")

        with mock.patch.object(
            run_ocr_stage, "_probe_video", return_value=(12.5, 1280, 720)
        ), mock.patch(
            "desktop.server.subprocess.run", side_effect=failing
        ), mock.patch(
            "engine.ffmpeg_bins.resolve_ffmpeg_executable", return_value=("/usr/bin/ffmpeg", None)
        ):
            status, payload = desktop_server.handle_ocr_test_frame(
                {"job_workspace": str(jw)}
            )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "ffmpeg_failed")


class HandleLoadProvenanceTest(_WorkspaceMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase18_load_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def _seed_source_srt(self, jw: Path) -> None:
        (jw / "artifacts" / "transcribe").mkdir(parents=True, exist_ok=True)
        (jw / "artifacts" / "transcribe" / "source.srt").write_text(
            "1\n00:00:00,000 --> 00:00:02,000\nhello\n",
            encoding="utf-8",
        )

    def test_returns_none_when_provenance_file_missing(self) -> None:
        jw = self._make_workspace()
        self._seed_source_srt(jw)
        status, payload = desktop_server.handle_load({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK, payload)
        self.assertIn("source_provenance", payload["data"])
        self.assertIsNone(payload["data"]["source_provenance"])

    def test_returns_parsed_provenance_when_present(self) -> None:
        jw = self._make_workspace()
        self._seed_source_srt(jw)
        prov = {
            "mode": "hybrid",
            "cues": [
                {"index": 1, "start_ms": 0, "end_ms": 2000, "source": "asr", "text": "hello"},
            ],
        }
        (jw / "artifacts" / "transcribe" / "source_provenance.json").write_text(
            json.dumps(prov), encoding="utf-8"
        )
        status, payload = desktop_server.handle_load({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["source_provenance"], prov)

    def test_ignores_invalid_provenance_json(self) -> None:
        jw = self._make_workspace()
        self._seed_source_srt(jw)
        (jw / "artifacts" / "transcribe" / "source_provenance.json").write_text(
            "{not-json", encoding="utf-8"
        )
        status, payload = desktop_server.handle_load({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertIsNone(payload["data"]["source_provenance"])


class ExtractorSettingsNormalizationTest(unittest.TestCase):
    def test_defaults_to_audio_only_when_missing(self) -> None:
        out = desktop_server._normalize_extractor_settings({})
        self.assertEqual(out["subtitle_extractor"], "audio_only")
        self.assertEqual(out["ocr_language"], "")
        self.assertEqual(out["ocr_roi"], "")
        self.assertEqual(out["ocr_device"], "")

    def test_invalid_extractor_collapses_to_audio_only(self) -> None:
        out = desktop_server._normalize_extractor_settings({"subtitle_extractor": "magic"})
        self.assertEqual(out["subtitle_extractor"], "audio_only")

    def test_roi_dict_is_serialized_to_json_string(self) -> None:
        out = desktop_server._normalize_extractor_settings(
            {
                "subtitle_extractor": "audio_only",
                "ocr_language": "CH",
                "ocr_device": "CPU",
                "ocr_roi": {"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.2},
            }
        )
        self.assertEqual(out["subtitle_extractor"], "audio_only")
        self.assertEqual(out["ocr_language"], "ch")
        self.assertEqual(out["ocr_device"], "cpu")
        parsed = json.loads(out["ocr_roi"])
        self.assertEqual(parsed, {"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.2})

    def test_deprecated_hybrid_normalizes_to_audio_only(self) -> None:
        out = desktop_server._normalize_extractor_settings(
            {"subtitle_extractor": "hybrid", "ocr_language": "ch"},
        )
        self.assertEqual(out["subtitle_extractor"], "audio_only")

    def test_deprecated_hybrid_clears_ocr_fields(self) -> None:
        """Desktop UI only offers audio_only + external_srt; legacy hybrid must not forward OCR."""
        out = desktop_server._normalize_extractor_settings(
            {
                "subtitle_extractor": "hybrid",
                "ocr_language": "ch",
                "ocr_device": "cuda",
                "ocr_roi": '{"x":0,"y":0,"w":1,"h":1}',
            },
        )
        self.assertEqual(out["subtitle_extractor"], "audio_only")
        self.assertEqual(out["ocr_language"], "")
        self.assertEqual(out["ocr_device"], "")
        self.assertEqual(out["ocr_roi"], "")

    def test_external_srt_mode_keeps_extractor_and_clears_ocr(self) -> None:
        out = desktop_server._normalize_extractor_settings(
            {
                "subtitle_extractor": "external_srt",
                "ocr_language": "ch",
            },
        )
        self.assertEqual(out["subtitle_extractor"], "external_srt")
        self.assertEqual(out["ocr_language"], "")

    def test_invalid_device_collapses_to_empty(self) -> None:
        out = desktop_server._normalize_extractor_settings({"ocr_device": "tpu"})
        self.assertEqual(out["ocr_device"], "")

    def test_provider_alias_is_canonicalized(self) -> None:
        out = desktop_server._normalize_extractor_settings(
            {"subtitle_extractor": "audio_only", "ocr_provider": "rapid"}
        )
        self.assertEqual(out["ocr_provider"], "rapidocr")


class OcrProgressFractionTest(_WorkspaceMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase18_progress_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_audio_only_ignores_stale_ocr_progress_file(self) -> None:
        jw = self._make_workspace()
        (jw / "video_state.json").write_text(
            json.dumps({"import_config": {"subtitle_extractor": "audio_only"}}),
            encoding="utf-8",
        )
        (jw / "artifacts" / "transcribe" / "ocr_progress.txt").write_text(
            "processed_frames=7\ntotal_frames=10\n",
            encoding="utf-8",
        )
        frac = desktop_server._substage_fraction(jw, "transcribed", {})
        self.assertEqual(frac, 0.0)

    def test_hybrid_uses_ocr_progress_file(self) -> None:
        jw = self._make_workspace()
        (jw / "video_state.json").write_text(
            json.dumps({"import_config": {"subtitle_extractor": "hybrid"}}),
            encoding="utf-8",
        )
        (jw / "artifacts" / "transcribe" / "ocr_progress.txt").write_text(
            "processed_frames=3\ntotal_frames=10\n",
            encoding="utf-8",
        )
        frac = desktop_server._substage_fraction(jw, "transcribed", {})
        self.assertEqual(frac, 0.0)


class OcrDiagnosticsEndpointTest(unittest.TestCase):
    def test_reports_provider_installation_and_cuda_support(self) -> None:
        fake_paddle = ModuleType("paddle")
        fake_paddle.device = SimpleNamespace(
            is_compiled_with_cuda=lambda: True,
            cuda=SimpleNamespace(device_count=lambda: 1),
        )
        fake_ort = ModuleType("onnxruntime")
        fake_ort.get_available_providers = lambda: ["CPUExecutionProvider", "CUDAExecutionProvider"]

        def fake_find_spec(name: str):
            if name in {"paddle", "paddleocr", "rapidocr_onnxruntime"}:
                return object()
            return None

        with mock.patch("importlib.util.find_spec", side_effect=fake_find_spec), mock.patch.dict(
            sys.modules,
            {"paddle": fake_paddle, "onnxruntime": fake_ort},
            clear=False,
        ):
            status, payload = desktop_server.handle_ocr_diagnostics({})

        self.assertEqual(status, HTTPStatus.OK, payload)
        data = payload["data"]
        self.assertTrue(data["any_installed"])
        providers = {item["name"]: item for item in data["providers"]}
        self.assertTrue(providers["paddleocr"]["installed"])
        self.assertTrue(providers["paddleocr"]["cuda_available"])
        self.assertTrue(providers["rapidocr"]["installed"])
        self.assertTrue(providers["rapidocr"]["cuda_available"])
        self.assertIn("pip install paddleocr paddlepaddle", providers["paddleocr"]["install_hint"])


class RunJobCommonExtractorFlagsTest(_WorkspaceMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase18_runcommon_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_hybrid_extractor_forwards_all_flags(self) -> None:
        jw = self._make_workspace()
        captured: dict[str, list[str]] = {}

        def fake_main(argv):
            captured["argv"] = list(argv)
            return 0

        with mock.patch.object(desktop_server.run_job, "main", side_effect=fake_main):
            rc = desktop_server._run_job_common(
                jw,
                project_name="proj",
                api_key="",
                source_language="zh",
                to_stage="transcribed",
                translate_backend="block_v2",
                tts_provider="edge_tts",
                tts_voice="",
                tts_rate="",
                mix_mode="replace_original_speech",
                enable_translation_qa=False,
                enable_source_cleanup=False,
                subtitle_extractor="hybrid",
                ocr_provider="rapid",
                ocr_language="ch",
                ocr_roi='{"x":0.0,"y":0.78,"w":1.0,"h":0.2}',
                ocr_device="cuda",
            )
        self.assertEqual(rc, 0)
        argv = captured["argv"]
        self.assertIn("--extractor", argv)
        self.assertEqual(argv[argv.index("--extractor") + 1], "audio_only")
        self.assertNotIn("--ocr-provider", argv)
        self.assertNotIn("--ocr-language", argv)

    def test_audio_only_default_omits_ocr_flags(self) -> None:
        jw = self._make_workspace()
        captured: dict[str, list[str]] = {}

        def fake_main(argv):
            captured["argv"] = list(argv)
            return 0

        with mock.patch.object(desktop_server.run_job, "main", side_effect=fake_main):
            rc = desktop_server._run_job_common(
                jw,
                project_name="proj",
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
        self.assertEqual(rc, 0)
        argv = captured["argv"]
        self.assertIn("--extractor", argv)
        self.assertEqual(argv[argv.index("--extractor") + 1], "audio_only")
        self.assertNotIn("--ocr-language", argv)
        self.assertNotIn("--ocr-roi", argv)
        self.assertNotIn("--ocr-device", argv)

    def test_auto_device_is_dropped_from_argv(self) -> None:
        jw = self._make_workspace()
        captured: dict[str, list[str]] = {}

        def fake_main(argv):
            captured["argv"] = list(argv)
            return 0

        with mock.patch.object(desktop_server.run_job, "main", side_effect=fake_main):
            desktop_server._run_job_common(
                jw,
                project_name="proj",
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
                subtitle_extractor="ocr_only",
                ocr_language="ch",
                ocr_device="auto",
            )
        argv = captured["argv"]
        self.assertEqual(argv[argv.index("--extractor") + 1], "audio_only")
        self.assertNotIn("--ocr-device", argv)


class HandleRunUntilEditForwardsExtractorTest(_WorkspaceMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase18_rue_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_forwards_extractor_cfg_when_manual_review(self) -> None:
        jw = self._make_workspace()
        captured: dict[str, dict] = {}

        def fake_run(jw_arg, **kwargs):
            captured["kwargs"] = kwargs
            return 0

        with mock.patch.object(
            desktop_server, "_run_job_common", side_effect=fake_run
        ), mock.patch.object(
            desktop_server, "_should_use_long_video_flow", return_value=(False, None)
        ), mock.patch.object(
            desktop_server, "invalidate_from_transcribe_downward", return_value=None
        ), mock.patch.object(
            desktop_server, "_status_payload", return_value={"ok": True}
        ):
            status, payload = desktop_server.handle_run_until_edit(
                {
                    "job_workspace": str(jw),
                    "project_name": "proj",
                    "use_auto_translate": False,
                    "subtitle_extractor": "hybrid",
                    "ocr_language": "ch",
                    "ocr_device": "cpu",
                    "ocr_roi": {"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.2},
                }
            )
        self.assertEqual(status, HTTPStatus.OK, payload)
        kwargs = captured["kwargs"]
        self.assertEqual(kwargs["subtitle_extractor"], "audio_only")
        self.assertEqual(kwargs.get("ocr_language"), "")
        self.assertEqual(kwargs.get("ocr_device"), "")
        self.assertEqual(kwargs.get("ocr_roi"), "")


class ImportConfigPersistenceTest(_WorkspaceMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase18_ic_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_save_then_load_roundtrip_preserves_extractor_fields(self) -> None:
        jw = self._make_workspace()
        cfg_in = {
            "use_auto_translate": False,
            "translate_backend": "block_v2",
            "tts_provider": "edge_tts",
            "subtitle_extractor": "hybrid",
            "ocr_language": "ch",
            "ocr_device": "cpu",
            "ocr_roi": {"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.2},
        }
        desktop_server._save_import_config(jw, cfg_in)
        loaded = desktop_server._load_import_config(jw)
        self.assertEqual(loaded["subtitle_extractor"], "audio_only")
        self.assertEqual(loaded["ocr_language"], "ch")
        self.assertEqual(loaded["ocr_device"], "cpu")
        self.assertEqual(loaded["ocr_roi"], {"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.2})
        self.assertFalse(loaded["use_auto_translate"])

    def test_invalid_roi_is_dropped_on_clean(self) -> None:
        cleaned = desktop_server._clean_import_config(
            {
                "subtitle_extractor": "ocr_only",
                "ocr_roi": {"x": 1.5, "y": 0.0, "w": 0.5, "h": 0.5},
            }
        )
        self.assertEqual(cleaned["subtitle_extractor"], "audio_only")
        self.assertIsNone(cleaned["ocr_roi"])

    def test_invalid_extractor_collapses_to_audio_only(self) -> None:
        cleaned = desktop_server._clean_import_config({"subtitle_extractor": "voodoo"})
        self.assertEqual(cleaned["subtitle_extractor"], "audio_only")


class RunJobExtractorForwardingTest(unittest.TestCase):
    """run_job.main should forward --extractor / --ocr-* into run_transcribe_stage.main."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase18_runjob_"))
        self.jw = self.root / "job"
        (self.jw / "input").mkdir(parents=True, exist_ok=True)
        (self.jw / "input" / "source.mp4").write_bytes(b"\x00")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _build_ns(self, **overrides) -> SimpleNamespace:
        ns = SimpleNamespace(
            transcribe_model_size="small",
            transcribe_device="cpu",
            transcribe_beam_size=1,
            transcribe_best_of=1,
            transcribe_language="",
            transcribe_audio_preprocess="none",
            transcribe_no_vad_filter=False,
            transcribe_vad_threshold=None,
            extractor="audio_only",
            ocr_provider="paddleocr",
            ocr_language="",
            ocr_roi="",
            ocr_device="auto",
        )
        for k, v in overrides.items():
            setattr(ns, k, v)
        return ns

    def _capture_targv(self, ns) -> list[str]:
        captured: dict[str, list[str]] = {}

        def fake_main(argv):
            captured["argv"] = list(argv)
            src = self.jw / "artifacts" / "transcribe" / "source.srt"
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_text("1\n00:00:00,000 --> 00:00:02,000\nhi\n", encoding="utf-8")
            return 0

        with mock.patch.object(
            run_job.run_transcribe_stage, "main", side_effect=fake_main
        ), mock.patch.object(
            run_job, "_mark_stage_running", return_value=None
        ):
            ok, rc = run_job._ensure_source_srt(self.jw, "job-1", {"to_stage": "transcribed"}, ns)
        self.assertTrue(ok)
        self.assertEqual(rc, 0)
        return captured["argv"]

    def test_audio_only_forwards_single_flag(self) -> None:
        argv = self._capture_targv(self._build_ns())
        self.assertIn("--extractor", argv)
        self.assertEqual(argv[argv.index("--extractor") + 1], "audio_only")
        self.assertNotIn("--ocr-language", argv)
        self.assertNotIn("--ocr-roi", argv)
        self.assertNotIn("--ocr-device", argv)

    def test_ocr_only_forwards_ocr_flags(self) -> None:
        argv = self._capture_targv(
            self._build_ns(
                extractor="ocr_only",
                ocr_language="ch",
                ocr_roi='{"x":0.0,"y":0.78,"w":1.0,"h":0.2}',
                ocr_device="cpu",
            )
        )
        self.assertEqual(argv[argv.index("--extractor") + 1], "ocr_only")
        self.assertEqual(argv[argv.index("--ocr-language") + 1], "ch")
        self.assertEqual(
            argv[argv.index("--ocr-roi") + 1],
            '{"x":0.0,"y":0.78,"w":1.0,"h":0.2}',
        )
        self.assertEqual(argv[argv.index("--ocr-device") + 1], "cpu")

    def test_hybrid_with_auto_device_omits_ocr_device_flag(self) -> None:
        argv = self._capture_targv(
            self._build_ns(
                extractor="hybrid",
                ocr_provider="rapid",
                ocr_language="ch",
                ocr_roi="",
                ocr_device="auto",
            )
        )
        self.assertEqual(argv[argv.index("--extractor") + 1], "hybrid")
        self.assertEqual(argv[argv.index("--ocr-provider") + 1], "rapidocr")
        self.assertIn("--ocr-language", argv)
        self.assertNotIn("--ocr-roi", argv)
        self.assertNotIn("--ocr-device", argv)


if __name__ == "__main__":
    unittest.main()
