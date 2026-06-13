"""Phase 3 desktop shell: HTTP handler unit tests (no live HTTP server).

Tests exercise desktop.server handler functions directly (they take a dict, return
(status, payload)) plus verify static files exist and end-to-end HTTP plumbing via
a short-lived ThreadingHTTPServer instance.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http import HTTPStatus
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desktop import server as desktop_server
from desktop import server_app_settings as desktop_server_app_settings
from desktop import server_ocr as desktop_server_ocr
from desktop import server_voices as desktop_server_voices
from engine.srt_cues import cues_to_srt, parse_srt_cues


SAMPLE_VOICE_SRT = (
    "1\n00:00:00,000 --> 00:00:02,000\nXin chao the gioi\n\n"
    "2\n00:00:02,000 --> 00:00:04,000\nCau hai\n\n"
)


class DesktopServerHandlersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase3_desktop_"))
        self.workspace_root = self.tmp_root / "workspaces"
        self.workspace_root.mkdir()
        self.fake_video = self.tmp_root / "sample clip.mp4"
        self.fake_video.write_bytes(b"\x00FAKE")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def _init(self) -> Path:
        status, payload = desktop_server.handle_init_job(
            {"video": str(self.fake_video), "workspace_root": str(self.workspace_root)}
        )
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["ok"])
        return Path(payload["data"]["job_workspace"])

    def _seed_voice(self, jw: Path) -> None:
        (jw / "artifacts" / "translate").mkdir(parents=True, exist_ok=True)
        (jw / "artifacts" / "transcribe").mkdir(parents=True, exist_ok=True)
        (jw / "artifacts" / "translate" / "translated_voice.srt").write_text(
            SAMPLE_VOICE_SRT, encoding="utf-8"
        )
        (jw / "artifacts" / "transcribe" / "source.srt").write_text(
            (
                "1\n00:00:00,000 --> 00:00:02,000\nNi hao shi jie\n\n"
                "2\n00:00:02,000 --> 00:00:04,000\nJu er\n\n"
            ),
            encoding="utf-8",
        )

    def test_init_job_missing_fields(self) -> None:
        status, payload = desktop_server.handle_init_job({})
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "missing_field")

    def test_init_job_video_not_found(self) -> None:
        status, payload = desktop_server.handle_init_job(
            {"video": str(self.tmp_root / "nope.mp4"), "workspace_root": str(self.workspace_root)}
        )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "video_not_found")

    def test_init_job_defaults_workspace_root_when_missing(self) -> None:
        orig_root = desktop_server._default_jobs_root
        orig_job_id = desktop_server._auto_job_id_for_video
        desktop_server._default_jobs_root = lambda: self.tmp_root / "Job"  # type: ignore[assignment]
        desktop_server._auto_job_id_for_video = lambda _video: "20260416_180000_sample-clip"  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_init_job({"video": str(self.fake_video)})
        finally:
            desktop_server._default_jobs_root = orig_root  # type: ignore[assignment]
            desktop_server._auto_job_id_for_video = orig_job_id  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["ok"])
        data = payload["data"]
        self.assertEqual(data["job_id"], "20260416_180000_sample-clip")
        self.assertTrue(data["used_default_workspace_root"])
        self.assertEqual(Path(data["workspace_root"]), self.tmp_root / "Job")
        self.assertTrue((self.tmp_root / "Job" / "20260416_180000_sample-clip" / "input" / "source.mp4").is_file())

    def test_init_job_copies_and_fingerprints(self) -> None:
        original = desktop_server.probe_video_duration
        desktop_server.probe_video_duration = lambda _p: 123.4  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_init_job(
                {"video": str(self.fake_video), "workspace_root": str(self.workspace_root)}
            )
        finally:
            desktop_server.probe_video_duration = original  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["ok"])
        jw = Path(payload["data"]["job_workspace"])
        self.assertTrue((jw / "input" / "source.mp4").is_file())
        self.assertEqual(payload["data"]["source_name"], self.fake_video.name)
        self.assertEqual(payload["data"]["source_duration_s"], 123.4)
        self.assertEqual(payload["data"]["workspace_root"], str(self.workspace_root.resolve()))
        self.assertFalse(payload["data"]["used_default_workspace_root"])

    def test_init_job_reuses_existing_workspace_for_same_source(self) -> None:
        status, payload = desktop_server.handle_init_job(
            {
                "video": str(self.fake_video),
                "workspace_root": str(self.workspace_root),
                "job_id": "sample-clip",
            }
        )
        self.assertEqual(status, HTTPStatus.OK)
        first_workspace = payload["data"]["job_workspace"]

        status, payload = desktop_server.handle_init_job(
            {
                "video": str(self.fake_video),
                "workspace_root": str(self.workspace_root),
                "job_id": "sample-clip",
            }
        )
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["job_workspace"], first_workspace)

    def test_save_import_config_round_trips(self) -> None:
        jw = self._init()
        status, payload = desktop_server.handle_save_import_config(
            {
                "job_workspace": str(jw),
                "config": {
                    "use_auto_translate": False,
                    "translate_backend": "legacy",
                    "tts_provider": "azure_tts",
                },
            }
        )
        self.assertEqual(status, HTTPStatus.OK)
        self.assertFalse(payload["data"]["config"]["use_auto_translate"])
        self.assertEqual(payload["data"]["config"]["translate_backend"], "legacy")
        self.assertEqual(payload["data"]["config"]["tts_provider"], "azure_tts")

        status, payload = desktop_server.handle_get_import_config({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertFalse(payload["data"]["config"]["use_auto_translate"])
        self.assertEqual(payload["data"]["config"]["translate_backend"], "legacy")
        self.assertEqual(payload["data"]["config"]["tts_provider"], "azure_tts")

    def test_bgm_status_save_and_remove(self) -> None:
        jw = self._init()
        bgm_dir = jw / "assets" / "bgm"
        bgm_dir.mkdir(parents=True)
        (bgm_dir / "bgm_normalized.wav").write_bytes(b"fake wav")
        (jw / "video_state.json").write_text(
            json.dumps(
                {
                    "bgm": {
                        "normalized_path": "assets/bgm/bgm_normalized.wav",
                        "original_filename": "music.wav",
                        "duration_ms": 1234,
                        "volume_db": -20,
                        "loop": True,
                        "fade_in_ms": 500,
                        "fade_out_ms": 1000,
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        status, payload = desktop_server.handle_bgm_status({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["bgm"]["original_filename"], "music.wav")

        status, payload = desktop_server.handle_bgm_save(
            {
                "job_workspace": str(jw),
                "bgm": {
                    "normalized_path": "assets/bgm/bgm_normalized.wav",
                    "volume_db": -12,
                    "loop": False,
                    "fade_in_ms": 250,
                    "fade_out_ms": 750,
                },
            }
        )
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["bgm"]["volume_db"], -12)
        self.assertFalse(payload["data"]["bgm"]["loop"])

        status, payload = desktop_server.handle_bgm_remove({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertIsNone(payload["data"]["bgm"])
        self.assertFalse(bgm_dir.exists())

    def test_bgm_upload_rejects_unsupported_extension_before_ffmpeg(self) -> None:
        jw = self._init()
        bad = self.tmp_root / "notes.txt"
        bad.write_text("not audio", encoding="utf-8")

        status, payload = desktop_server.handle_bgm_upload(
            {"job_workspace": str(jw), "bgm_path": str(bad)}
        )

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "invalid_bgm")
        self.assertIn("mp3", payload["error"]["message"])

    def test_render_settings_save_background_upload_and_remove(self) -> None:
        jw = self._init()
        status, payload = desktop_server.handle_render_settings_save(
            {"job_workspace": str(jw), "render": {"aspect_ratio": "9:16"}}
        )
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["render"]["aspect_ratio"], "9:16")

        image = self.tmp_root / "poster.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\nfake")
        status, payload = desktop_server.handle_render_background_upload(
            {"job_workspace": str(jw), "image_path": str(image)}
        )
        self.assertEqual(status, HTTPStatus.OK)
        render = payload["data"]["render"]
        self.assertEqual(render["aspect_ratio"], "9:16")
        self.assertTrue(render["background_path"].startswith("assets/render_background/"))

        status, payload = desktop_server.handle_render_settings_status({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["render"]["background_original_filename"], "poster.png")

        status, payload = desktop_server.handle_render_background_remove({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertNotIn("background_path", payload["data"]["render"])

    def test_inspect_local_video_returns_preview_metadata(self) -> None:
        original = desktop_server_ocr.probe_video_duration
        desktop_server_ocr.probe_video_duration = lambda _p: 42.5  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_inspect_local_video(
                {"path": str(self.fake_video)}
            )
        finally:
            desktop_server_ocr.probe_video_duration = original  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["name"], self.fake_video.name)
        self.assertEqual(payload["data"]["size"], self.fake_video.stat().st_size)
        self.assertEqual(payload["data"]["duration_s"], 42.5)

    def test_inspect_local_video_tolerates_probe_failure(self) -> None:
        original = desktop_server_ocr.probe_video_duration

        def _boom(_p):
            raise RuntimeError("ffprobe missing")

        desktop_server_ocr.probe_video_duration = _boom  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_inspect_local_video(
                {"path": str(self.fake_video)}
            )
        finally:
            desktop_server_ocr.probe_video_duration = original  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["ok"])
        self.assertIsNone(payload["data"]["duration_s"])

    def test_probe_video_url_endpoint_returns_payload(self) -> None:
        orig = desktop_server.probe_video_url
        desktop_server.probe_video_url = lambda _url: {  # type: ignore[assignment]
            "title": "Demo Video",
            "video_id": "abc123",
        }
        try:
            status, payload = desktop_server.handle_probe_video_url(
                {"url": "https://example.com/watch?v=abc123"}
            )
        finally:
            desktop_server.probe_video_url = orig  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["video_id"], "abc123")

    def test_init_job_from_url_endpoint_returns_payload(self) -> None:
        orig = desktop_server.init_job_from_url
        desktop_server.init_job_from_url = lambda **_kwargs: {  # type: ignore[assignment]
            "job_id": "demo-video",
            "job_workspace": str(self.workspace_root / "demo-video"),
            "input_video_path": str(self.workspace_root / "demo-video" / "input" / "source.mp4"),
        }
        try:
            status, payload = desktop_server.handle_init_job_from_url(
                {
                    "url": "https://example.com/watch?v=abc123",
                    "workspace_root": str(self.workspace_root),
                }
            )
        finally:
            desktop_server.init_job_from_url = orig  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["job_id"], "demo-video")

    def test_status_on_fresh_workspace(self) -> None:
        jw = self._init()
        self._seed_voice(jw)
        status, payload = desktop_server.handle_status({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["voice_edit_status"], "not_started")
        self.assertEqual(payload["data"]["source_mode"], "translated_voice")

    def test_load_returns_cues(self) -> None:
        jw = self._init()
        self._seed_voice(jw)
        status, payload = desktop_server.handle_load({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(len(payload["data"]["cues"]), 2)
        self.assertEqual(payload["data"]["cues"][0]["text"], "Xin chao the gioi")
        self.assertEqual(payload["data"]["source_text_mode"], "source")
        self.assertEqual(payload["data"]["source_cues"][0]["text"], "Ni hao shi jie")
        self.assertEqual(payload["data"]["reference_mode"], "translated_voice")
        self.assertEqual(payload["data"]["reference_cues"][1]["text"], "Cau hai")

    def test_load_falls_back_to_source_text_when_voice_missing(self) -> None:
        jw = self._init()
        (jw / "artifacts" / "transcribe").mkdir(parents=True, exist_ok=True)
        (jw / "artifacts" / "transcribe" / "source.srt").write_text(
            (
                "1\n00:00:00,000 --> 00:00:02,000\nNguon dong 1\n\n"
                "2\n00:00:02,000 --> 00:00:04,000\nNguon dong 2\n\n"
            ),
            encoding="utf-8",
        )
        status, payload = desktop_server.handle_load({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["source_mode"], "source_text")
        self.assertEqual(payload["data"]["reference_mode"], "source_text")
        self.assertEqual(payload["data"]["cues"][0]["text"], "Nguon dong 1")
        self.assertEqual(payload["data"]["source_cues"][1]["text"], "Nguon dong 2")

    def test_run_until_edit_manual_stops_after_transcribe(self) -> None:
        jw = self._init()
        original_should_use_long = desktop_server._should_use_long_video_flow
        original_invalidate = desktop_server.invalidate_from_transcribe_downward
        original_run_job_common = desktop_server._run_job_common
        calls: list[tuple[Path, str]] = []

        def _fake_invalidate(job_workspace: Path, *, reason: str) -> None:
            calls.append((Path(job_workspace), reason))

        def _fake_run_job_common(
            job_workspace: Path,
            *,
            project_name: str,
            api_key: str,
            source_language: str,
            to_stage: str,
            translate_backend: str,
            tts_provider: str,
            tts_voice: str,
            tts_rate: str,
            mix_mode: str,
            enable_translation_qa: bool,
            enable_source_cleanup: bool,
            project_root: str = "",
            render_subtitle_mode: str = "soft",
            **kwargs,
        ) -> int:
            self.assertEqual(project_name, "demo")
            self.assertEqual(to_stage, "transcribed")
            self.assertEqual(translate_backend, "legacy")
            self.assertEqual(source_language, "")
            source_srt = Path(job_workspace) / "artifacts" / "transcribe" / "source.srt"
            source_srt.parent.mkdir(parents=True, exist_ok=True)
            source_srt.write_text(
                "1\n00:00:00,000 --> 00:00:01,000\nOnly transcribed\n\n",
                encoding="utf-8",
            )
            return 0

        desktop_server._should_use_long_video_flow = lambda _jw: (False, None)  # type: ignore[assignment]
        desktop_server.invalidate_from_transcribe_downward = _fake_invalidate  # type: ignore[assignment]
        desktop_server._run_job_common = _fake_run_job_common  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_run_until_edit(
                {
                    "job_workspace": str(jw),
                    "project_name": "demo",
                    "use_auto_translate": False,
                    "translate_backend": "legacy",
                }
            )
        finally:
            desktop_server._should_use_long_video_flow = original_should_use_long  # type: ignore[assignment]
            desktop_server.invalidate_from_transcribe_downward = original_invalidate  # type: ignore[assignment]
            desktop_server._run_job_common = original_run_job_common  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["voice_edit_status"], "not_started")
        self.assertEqual(len(calls), 1)
        self.assertTrue((jw / "artifacts" / "transcribe" / "source.srt").is_file())

    def test_run_until_edit_auto_uses_saved_key_and_source_language(self) -> None:
        jw = self._init()
        original_should_use_long = desktop_server._should_use_long_video_flow
        original_run_job_common = desktop_server._run_job_common
        original_load_app_settings = desktop_server._load_app_settings
        seen: dict[str, str] = {}

        def _fake_run_job_common(
            job_workspace: Path,
            *,
            project_name: str,
            api_key: str,
            source_language: str,
            to_stage: str,
            translate_backend: str,
            tts_provider: str,
            tts_voice: str,
            tts_rate: str,
            mix_mode: str,
            enable_translation_qa: bool,
            enable_source_cleanup: bool,
            project_root: str = "",
            render_subtitle_mode: str = "soft",
            **kwargs,
        ) -> int:
            seen["api_key"] = api_key
            seen["source_language"] = source_language
            self.assertEqual(project_name, "demo")
            self.assertEqual(to_stage, "translated")
            self.assertEqual(translate_backend, "block_v2")
            translated = Path(job_workspace) / "artifacts" / "translate" / "translated_voice.srt"
            translated.parent.mkdir(parents=True, exist_ok=True)
            translated.write_text(SAMPLE_VOICE_SRT, encoding="utf-8")
            return 0

        desktop_server._should_use_long_video_flow = lambda _jw: (False, None)  # type: ignore[assignment]
        desktop_server._run_job_common = _fake_run_job_common  # type: ignore[assignment]
        desktop_server._load_app_settings = lambda: {"openai_api_key": "sk-test-saved"}  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_run_until_edit(
                {
                    "job_workspace": str(jw),
                    "project_name": "demo",
                    "source_language": "ja",
                }
            )
        finally:
            desktop_server._should_use_long_video_flow = original_should_use_long  # type: ignore[assignment]
            desktop_server._run_job_common = original_run_job_common  # type: ignore[assignment]
            desktop_server._load_app_settings = original_load_app_settings  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(seen["api_key"], "sk-test-saved")
        self.assertEqual(seen["source_language"], "ja")
        self.assertEqual(payload["data"]["voice_edit_status"], "voice_edit_pending")

    def test_run_until_edit_auto_legacy_promotes_translated_auto_to_voice(self) -> None:
        jw = self._init()
        original_should_use_long = desktop_server._should_use_long_video_flow
        original_run_job_common = desktop_server._run_job_common
        original_load_app_settings = desktop_server._load_app_settings

        def _fake_run_job_common(
            job_workspace: Path,
            *,
            project_name: str,
            api_key: str,
            source_language: str,
            to_stage: str,
            translate_backend: str,
            tts_provider: str,
            tts_voice: str,
            tts_rate: str,
            mix_mode: str,
            enable_translation_qa: bool,
            enable_source_cleanup: bool,
            project_root: str = "",
            render_subtitle_mode: str = "soft",
            **kwargs,
        ) -> int:
            self.assertEqual(project_name, "demo")
            self.assertEqual(to_stage, "translated")
            self.assertEqual(translate_backend, "legacy")
            translate_dir = Path(job_workspace) / "artifacts" / "translate"
            translate_dir.mkdir(parents=True, exist_ok=True)
            # legacy backend may only create translated_auto.srt
            (translate_dir / "translated_auto.srt").write_text(SAMPLE_VOICE_SRT, encoding="utf-8")
            return 0

        desktop_server._should_use_long_video_flow = lambda _jw: (False, None)  # type: ignore[assignment]
        desktop_server._run_job_common = _fake_run_job_common  # type: ignore[assignment]
        desktop_server._load_app_settings = lambda: {"openai_api_key": "sk-test-saved"}  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_run_until_edit(
                {
                    "job_workspace": str(jw),
                    "project_name": "demo",
                    "translate_backend": "legacy",
                    "use_auto_translate": True,
                }
            )
        finally:
            desktop_server._should_use_long_video_flow = original_should_use_long  # type: ignore[assignment]
            desktop_server._run_job_common = original_run_job_common  # type: ignore[assignment]
            desktop_server._load_app_settings = original_load_app_settings  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["voice_edit_status"], "voice_edit_pending")
        self.assertTrue((jw / "artifacts" / "translate" / "translated_voice.srt").is_file())
        self.assertTrue((jw / "artifacts" / "edit" / "edited_voice.srt").is_file())

    def test_run_until_edit_auto_requires_api_key(self) -> None:
        jw = self._init()
        original_load_app_settings = desktop_server._load_app_settings
        original_env_key = desktop_server.os.environ.get("OPENAI_API_KEY")
        original_managed = desktop_server._managed_mode_on
        desktop_server._load_app_settings = lambda: {}  # type: ignore[assignment]
        desktop_server.os.environ.pop("OPENAI_API_KEY", None)
        # BYOK path: force managed mode off so a stray .cloud_session.json from a
        # real login doesn't bypass the OpenAI-key requirement under test.
        desktop_server._managed_mode_on = lambda: False  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_run_until_edit(
                {"job_workspace": str(jw), "project_name": "demo"}
            )
        finally:
            desktop_server._load_app_settings = original_load_app_settings  # type: ignore[assignment]
            desktop_server._managed_mode_on = original_managed  # type: ignore[assignment]
            if original_env_key is None:
                desktop_server.os.environ.pop("OPENAI_API_KEY", None)
            else:
                desktop_server.os.environ["OPENAI_API_KEY"] = original_env_key
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "api_key_required")

    def test_save_serializes_cues_back_to_srt(self) -> None:
        jw = self._init()
        self._seed_voice(jw)
        (jw / "artifacts" / "edit").mkdir(parents=True, exist_ok=True)
        status, payload = desktop_server.handle_save(
            {
                "job_workspace": str(jw),
                "cues": [
                    {"index": 1, "start_ms": 0, "end_ms": 2000, "text": "Xin chao (da sua)"},
                    {"index": 2, "start_ms": 2000, "end_ms": 4000, "text": "Cau hai"},
                ],
            }
        )
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["cue_count"], 2)
        edited = (jw / "artifacts" / "edit" / "edited_voice.srt").read_text(encoding="utf-8")
        self.assertIn("(da sua)", edited)
        # Round-trip: server-written SRT parses cleanly.
        cues = parse_srt_cues(edited)
        self.assertEqual(len(cues), 2)

    def test_save_rejects_empty_cue_text(self) -> None:
        jw = self._init()
        self._seed_voice(jw)
        status, payload = desktop_server.handle_save(
            {
                "job_workspace": str(jw),
                "cues": [{"index": 1, "start_ms": 0, "end_ms": 2000, "text": "   "}],
            }
        )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "invalid_cues")

    def test_mark_edited_flips_state(self) -> None:
        jw = self._init()
        self._seed_voice(jw)
        (jw / "artifacts" / "edit").mkdir(parents=True, exist_ok=True)
        (jw / "artifacts" / "edit" / "edited_voice.srt").write_text(
            SAMPLE_VOICE_SRT, encoding="utf-8"
        )
        status, payload = desktop_server.handle_mark_edited({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["voice_edit_status"], "voice_edited")
        self.assertTrue(payload["data"]["voice_edited"])

    def test_save_after_approval_resets_pending_state(self) -> None:
        jw = self._init()
        self._seed_voice(jw)
        (jw / "artifacts" / "edit").mkdir(parents=True, exist_ok=True)
        (jw / "artifacts" / "edit" / "edited_voice.srt").write_text(
            SAMPLE_VOICE_SRT, encoding="utf-8"
        )
        status, payload = desktop_server.handle_mark_edited({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["data"]["voice_edited"])

        status, payload = desktop_server.handle_save(
            {
                "job_workspace": str(jw),
                "cues": [
                    {"index": 1, "start_ms": 0, "end_ms": 2000, "text": "Xin chao the gioi"},
                    {"index": 2, "start_ms": 2000, "end_ms": 4000, "text": "Cau hai (draft moi)"},
                ],
            }
        )
        self.assertEqual(status, HTTPStatus.OK)

        status, payload = desktop_server.handle_status({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["voice_edit_status"], "voice_edit_pending")
        self.assertFalse(payload["data"]["voice_edited"])

    def test_run_after_edit_refuses_without_edited_voice(self) -> None:
        jw = self._init()
        status, payload = desktop_server.handle_run_after_edit(
            {"job_workspace": str(jw), "project_name": "demo"}
        )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "edited_voice_missing")

    def test_run_after_edit_marks_long_video_before_orchestrator(self) -> None:
        jw = self._init()
        (jw / "artifacts" / "edit").mkdir(parents=True, exist_ok=True)
        (jw / "artifacts" / "edit" / "edited_voice.srt").write_text(
            SAMPLE_VOICE_SRT, encoding="utf-8"
        )
        (jw / "segments").mkdir(parents=True, exist_ok=True)
        (jw / "segments" / "manifest.json").write_text(
            json.dumps({"version": 1, "source_duration_s": 600.0, "segments": []}),
            encoding="utf-8",
        )

        seen: dict[str, bool] = {}
        orig = desktop_server.run_long_video_stage.do_after_edit

        def fake_after_edit(*args, **kwargs):
            status = desktop_server.get_voice_edit_status(jw)
            seen["voice_edited"] = bool(status.voice_edited)
            return {
                "ok": True,
                "merged_render_path": None,
                "segment_count": 0,
                "workers": 1,
            }

        desktop_server.run_long_video_stage.do_after_edit = fake_after_edit  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_run_after_edit(
                {"job_workspace": str(jw), "project_name": "demo", "to_stage": "mixed"}
            )
        finally:
            desktop_server.run_long_video_stage.do_after_edit = orig  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["ok"])
        self.assertTrue(seen.get("voice_edited"))

    def test_run_after_edit_passes_mix_duck_gain_to_run_job(self) -> None:
        jw = self._init()
        (jw / "artifacts" / "edit").mkdir(parents=True, exist_ok=True)
        (jw / "artifacts" / "edit" / "edited_voice.srt").write_text(
            SAMPLE_VOICE_SRT, encoding="utf-8"
        )
        seen: dict[str, float | None] = {"gain": None}
        orig = desktop_server._run_job_common

        def fake_run_job_common(
            job_workspace: Path,
            *,
            project_name: str,
            api_key: str,
            source_language: str,
            to_stage: str,
            translate_backend: str,
            tts_provider: str,
            tts_voice: str,
            tts_rate: str,
            mix_mode: str,
            enable_translation_qa: bool,
            enable_source_cleanup: bool,
            project_root: str = "",
            render_subtitle_mode: str = "burn",
            mix_duck_gain_db: float | None = None,
            **kwargs,
        ) -> int:
            del job_workspace, project_name, api_key, source_language
            del to_stage, translate_backend, tts_provider, tts_voice, tts_rate
            del mix_mode, enable_translation_qa, enable_source_cleanup
            del project_root, render_subtitle_mode, kwargs
            seen["gain"] = mix_duck_gain_db
            return 0

        desktop_server._run_job_common = fake_run_job_common  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_run_after_edit(
                {
                    "job_workspace": str(jw),
                    "project_name": "demo",
                    "to_stage": "mixed",
                    "mix_mode": "duck_original_speech",
                    "mix_duck_gain_db": -9.5,
                }
            )
        finally:
            desktop_server._run_job_common = orig  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK, payload)
        self.assertEqual(seen["gain"], -9.5)

    def test_app_settings_round_trip_azure_speech_profiles(self) -> None:
        settings_path = self.tmp_root / "app_settings.json"
        orig = desktop_server_app_settings._app_settings_path
        desktop_server_app_settings._app_settings_path = lambda: settings_path  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_save_app_settings(
                {
                    "language": "vi",
                    "openai_translation_model": "gpt-5.4",
                    "azure_speech": {
                        "fallback_enabled": True,
                        "primary": {
                            "key": "primary-secret-1234",
                            "region": "southeastasia",
                        },
                        "secondary": {
                            "key": "backup-secret-5678",
                            "region": "eastasia",
                        },
                    },
                }
            )
            self.assertEqual(status, HTTPStatus.OK, payload)
            self.assertTrue(payload["data"]["azure_speech"]["primary"]["has_key"])
            self.assertEqual(payload["data"]["openai_translation_model"], "gpt-5.4")
            self.assertEqual(
                payload["data"]["azure_speech"]["primary"]["region"],
                "southeastasia",
            )

            status, payload = desktop_server.handle_get_app_settings({})
            self.assertEqual(status, HTTPStatus.OK, payload)
            self.assertEqual(payload["data"]["openai_translation_model"], "gpt-5.4")
            self.assertEqual(
                payload["data"]["azure_speech"]["secondary"]["region"],
                "eastasia",
            )
            self.assertTrue(payload["data"]["azure_speech"]["fallback_enabled"])
        finally:
            desktop_server_app_settings._app_settings_path = orig  # type: ignore[assignment]

    def test_run_until_edit_reports_run_job_failure(self) -> None:
        jw = self._init()
        orig = desktop_server.run_job.main
        desktop_server.run_job.main = lambda _argv: 2  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_run_until_edit(
                {"job_workspace": str(jw), "project_name": "demo"}
            )
        finally:
            desktop_server.run_job.main = orig  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "run_job_failed")

    def test_run_until_edit_failure_includes_short_error_code(self) -> None:
        jw = self._init()
        (jw / "run.log").write_text("ffmpeg exited with code 1\n", encoding="utf-8")
        orig = desktop_server.run_job.main
        desktop_server.run_job.main = lambda _argv: 2  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_run_until_edit(
                {"job_workspace": str(jw), "project_name": "demo"}
            )
        finally:
            desktop_server.run_job.main = orig  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["short_code"], "FFMPEG")

    def test_preflight_endpoint_returns_report(self) -> None:
        jw = self._init()
        orig = desktop_server.build_preflight_report
        desktop_server.build_preflight_report = lambda **kwargs: {  # type: ignore[assignment]
            "ok": True,
            "job_workspace": kwargs.get("job_workspace"),
            "checks": [{"name": "demo", "ok": True, "required": True}],
        }
        try:
            status, payload = desktop_server.handle_preflight(
                {"job_workspace": str(jw), "require_input": True}
            )
        finally:
            desktop_server.build_preflight_report = orig  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["job_workspace"], str(jw))
        self.assertIs(desktop_server.ROUTES["/api/doctor"], desktop_server.handle_preflight)

    def test_list_system_fonts_endpoint_returns_fonts(self) -> None:
        orig = desktop_server_voices._list_system_fonts
        desktop_server_voices._list_system_fonts = lambda: [  # type: ignore[assignment]
            {"family": "Arial", "file": "C:/Windows/Fonts/arial.ttf"}
        ]
        try:
            status, payload = desktop_server.handle_list_system_fonts({})
        finally:
            desktop_server_voices._list_system_fonts = orig  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["fonts"][0]["family"], "Arial")

    def test_list_voices_endpoint_returns_catalog(self) -> None:
        orig = desktop_server_voices._load_voice_catalog
        desktop_server_voices._load_voice_catalog = lambda: [  # type: ignore[assignment]
            {"provider": "edge_tts", "voice_id": "vi-VN-HoaiMyNeural", "enabled": True}
        ]
        try:
            status, payload = desktop_server.handle_list_voices({})
        finally:
            desktop_server_voices._load_voice_catalog = orig  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["voices"][0]["voice_id"], "vi-VN-HoaiMyNeural")

    def test_toggle_voice_updates_catalog_enabled_flag(self) -> None:
        catalog_path = self.tmp_root / "voices_catalog.json"
        catalog_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "voices": [
                        {
                            "provider": "edge_tts",
                            "voice_id": "vi-VN-HoaiMyNeural",
                            "enabled": True,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        orig = desktop_server_voices._voices_catalog_path
        desktop_server_voices._voices_catalog_path = lambda: catalog_path  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_toggle_voice(
                {"provider": "edge_tts", "voice_id": "vi-VN-HoaiMyNeural", "enabled": False}
            )
        finally:
            desktop_server_voices._voices_catalog_path = orig  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK, payload)
        saved = json.loads(catalog_path.read_text(encoding="utf-8"))
        self.assertFalse(saved["voices"][0]["enabled"])
        self.assertFalse(payload["data"]["voices"][0]["enabled"])

    def test_tts_preview_writes_preview_wav(self) -> None:
        jw = self._init()

        class _FakeProvider:
            async def synthesize_cue_to_wav(self, text, out_wav, *, voice, rate, diag_prefix=""):
                out_wav.write_bytes(b"RIFF....WAVE")
                return 321

        orig = desktop_server.get_tts_provider
        desktop_server.get_tts_provider = lambda _name: _FakeProvider()  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_tts_preview(
                {
                    "job_workspace": str(jw),
                    "tts_provider": "edge_tts",
                    "tts_voice": "vi-VN-HoaiMyNeural",
                    "speed_multiplier": 1.25,
                }
            )
        finally:
            desktop_server.get_tts_provider = orig  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK, payload)
        self.assertTrue((jw / payload["data"]["rel_path"]).is_file())
        self.assertEqual(payload["data"]["duration_ms"], 321)
        self.assertEqual(payload["data"]["rate"], "+25%")

    def test_tts_preview_reuses_cache_for_same_voice_rate_text(self) -> None:
        jw = self._init()
        calls = {"count": 0}

        class _FakeProvider:
            async def synthesize_cue_to_wav(self, text, out_wav, *, voice, rate, diag_prefix=""):
                calls["count"] += 1
                out_wav.write_bytes(b"RIFF....WAVE")
                return 111

        orig = desktop_server.get_tts_provider
        desktop_server.get_tts_provider = lambda _name: _FakeProvider()  # type: ignore[assignment]
        try:
            body = {
                "job_workspace": str(jw),
                "tts_provider": "edge_tts",
                "tts_voice": "vi-VN-HoaiMyNeural",
                "speed_multiplier": 1,
                "text": "Xin chao",
            }
            first_status, first_payload = desktop_server.handle_tts_preview(body)
            second_status, second_payload = desktop_server.handle_tts_preview(body)
        finally:
            desktop_server.get_tts_provider = orig  # type: ignore[assignment]
        self.assertEqual(first_status, HTTPStatus.OK, first_payload)
        self.assertEqual(second_status, HTTPStatus.OK, second_payload)
        self.assertEqual(calls["count"], 1)
        self.assertFalse(first_payload["data"]["cached"])
        self.assertTrue(second_payload["data"]["cached"])
        self.assertEqual(first_payload["data"]["rel_path"], second_payload["data"]["rel_path"])
        self.assertEqual(second_payload["data"]["duration_ms"], 111)

    def test_job_progress_uses_target_stage_scale_and_classifies_errors(self) -> None:
        jw = self._init()
        (jw / "job_state.json").write_text(
            json.dumps(
                {
                    "status": "failed",
                    "current_stage": "tts_failed",
                    "last_error": "edge-tts request timed out",
                    "runner": {"to_stage": "rendered"},
                }
            ),
            encoding="utf-8",
        )
        (jw / "run.log").write_text("edge-tts request timed out\n", encoding="utf-8")
        status, payload = desktop_server.handle_job_progress({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        data = payload["data"]
        self.assertEqual(data["target_stage"], "rendered")
        self.assertEqual(data["target_stage_rank"], 7)
        self.assertEqual(data["stage_total"], 7)
        self.assertEqual(data["current_stage_label"], "TTS failed")
        self.assertEqual(data["status_label"], "Failed")
        self.assertEqual(data["lifecycle"], "failed")
        self.assertEqual(data["error"]["short_code"], "TTS")
        self.assertEqual(data["error"]["summary"], "Text-to-speech stage failed.")

    def test_job_progress_reports_active_running_stage(self) -> None:
        jw = self._init()
        (jw / "job_state.json").write_text(
            json.dumps(
                {
                    "status": "running",
                    "current_stage": "translated",
                    "runner": {"to_stage": "rendered"},
                }
            ),
            encoding="utf-8",
        )
        status, payload = desktop_server.handle_job_progress({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        data = payload["data"]
        self.assertEqual(data["current_stage_label"], "Translating subtitles")
        self.assertEqual(data["status_label"], "Running")
        self.assertEqual(data["stage_index"], 1)
        # Weighted scale: weight of completed stage transcribed(15) over total target weight 96 → 16%.
        self.assertEqual(data["overall_percent"], 16)
        self.assertEqual(data["substage_percent"], 0)

    def test_job_progress_includes_tts_cue_substage(self) -> None:
        jw = self._init()
        (jw / "job_state.json").write_text(
            json.dumps(
                {
                    "status": "running",
                    "current_stage": "tts_generated",
                    "runner": {"to_stage": "rendered"},
                }
            ),
            encoding="utf-8",
        )
        translate_dir = jw / "artifacts" / "translate"
        translate_dir.mkdir(parents=True, exist_ok=True)
        # 4 cues in the final subtitle.
        srt = (
            "1\n00:00:00,000 --> 00:00:01,000\na\n\n"
            "2\n00:00:01,000 --> 00:00:02,000\nb\n\n"
            "3\n00:00:02,000 --> 00:00:03,000\nc\n\n"
            "4\n00:00:03,000 --> 00:00:04,000\nd\n\n"
        )
        (translate_dir / "final_subtitle.srt").write_text(srt, encoding="utf-8")
        cues_dir = jw / "artifacts" / "tts" / "cues"
        cues_dir.mkdir(parents=True, exist_ok=True)
        # 1 of 4 cues already synthesized -> substage 25%.
        (cues_dir / "cue_00001.wav").write_bytes(b"x")
        status, payload = desktop_server.handle_job_progress({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        data = payload["data"]
        self.assertEqual(data["substage_percent"], 25)
        # Completed: transcribed(15)+translated(25)+subtitle_finalized(1)=41, +0.25*tts(25)=6.25 → 47.25/96 ≈ 49%.
        self.assertEqual(data["overall_percent"], 49)

    def test_static_files_exist(self) -> None:
        self.assertTrue((desktop_server.STATIC_DIR / "index.html").is_file())
        self.assertTrue((desktop_server.STATIC_DIR / "app.js").is_file())
        self.assertTrue((desktop_server.STATIC_DIR / "app.css").is_file())
        self.assertTrue((desktop_server.STATIC_DIR / "next" / "import.js").is_file())
        self.assertTrue((desktop_server.STATIC_DIR / "next" / "settings.js").is_file())
        self.assertTrue((desktop_server.STATIC_DIR / "next" / "review.js").is_file())
        self.assertTrue((desktop_server.STATIC_DIR / "next" / "render.js").is_file())
        self.assertTrue((desktop_server.STATIC_DIR / "next" / "diagnostics.js").is_file())
        self.assertTrue((desktop_server.STATIC_DIR / "editShellBridge.js").is_file())
        self.assertTrue((desktop_server.STATIC_DIR / "editWizardGate.js").is_file())

    def test_cues_to_srt_round_trip(self) -> None:
        cues = parse_srt_cues(SAMPLE_VOICE_SRT)
        out = cues_to_srt(cues)
        again = parse_srt_cues(out)
        self.assertEqual(
            [(c.start_ms, c.end_ms, c.text) for c in cues],
            [(c.start_ms, c.end_ms, c.text) for c in again],
        )


class DesktopServerHttpLiveTest(unittest.TestCase):
    """Boot the real HTTP server on a random port and hit one endpoint end-to-end."""

    def test_http_index_and_init_job(self) -> None:
        from http.server import ThreadingHTTPServer

        tmp_root = Path(tempfile.mkdtemp(prefix="phase3_http_"))
        video = tmp_root / "live.mp4"
        video.write_bytes(b"x")
        workspace_root = tmp_root / "w"
        workspace_root.mkdir()
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), desktop_server._Handler)
            port = httpd.server_address[1]
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                # GET /
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=3) as resp:
                    body = resp.read().decode("utf-8")
                    self.assertIn("VL Studio", body)

                # POST /api/init-job
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/init-job",
                    data=json.dumps(
                        {"video": str(video), "workspace_root": str(workspace_root)}
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(payload["ok"])
                self.assertTrue(Path(payload["data"]["job_workspace"]).is_dir())
            finally:
                httpd.shutdown()
                httpd.server_close()
                thread.join(timeout=2)
        finally:
            shutil.rmtree(tmp_root, ignore_errors=True)
            # also clean newly created workspaces from pytest isolation
            time.sleep(0)


class DesktopServerBrowserReadyTest(unittest.TestCase):
    def test_ping_server_returns_true_for_ok_payload(self) -> None:
        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b'{"ok": true, "data": {"status": "ok"}}'

        original = desktop_server.urllib.request.urlopen
        desktop_server.urllib.request.urlopen = lambda *args, **kwargs: _Resp()  # type: ignore[assignment]
        try:
            self.assertTrue(desktop_server._ping_server("http://127.0.0.1:8765"))
        finally:
            desktop_server.urllib.request.urlopen = original  # type: ignore[assignment]

    def test_ping_server_returns_false_on_url_error(self) -> None:
        def _raise(*args, **kwargs):
            raise urllib.error.URLError("connection refused")

        original = desktop_server.urllib.request.urlopen
        desktop_server.urllib.request.urlopen = _raise  # type: ignore[assignment]
        try:
            self.assertFalse(desktop_server._ping_server("http://127.0.0.1:8765"))
        finally:
            desktop_server.urllib.request.urlopen = original  # type: ignore[assignment]


if __name__ == "__main__":
    unittest.main()
