"""Phase 12 — new UI-support endpoints on desktop.server.

Covers list-jobs, list-segments, list-artifacts, TTS settings (get/save for
video + project), /api/reveal (handler-level only; does not actually launch
Explorer), and /media static serving via a short-lived HTTP server.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desktop import server as desktop_server  # noqa: E402


class _WorkspaceMixin:
    """Tiny helper that fabricates a job-like workspace on disk without running ffmpeg."""

    tmp_root: Path

    def _make_workspace(self, name: str, *, long_video: bool = False) -> Path:
        jw = self.tmp_root / name
        (jw / "artifacts" / "edit").mkdir(parents=True, exist_ok=True)
        (jw / "artifacts" / "translate").mkdir(parents=True, exist_ok=True)
        (jw / "input").mkdir(parents=True, exist_ok=True)
        (jw / "input" / "source.mp4").write_bytes(b"\x00FAKE")
        (jw / "artifacts" / "edit" / "edited_voice.srt").write_text(
            "1\n00:00:00,000 --> 00:00:02,000\nhi\n", encoding="utf-8"
        )
        (jw / "job_state.json").write_text(
            json.dumps(
                {
                    "job_id": name,
                    "status": "running" if not long_video else "blocked",
                    "current_stage": "translated" if not long_video else "voice_edit_pending",
                    "runner": {"to_stage": "rendered"},
                    "voice_edit_status": "voice_edit_pending",
                    "voice_edited": False,
                }
            ),
            encoding="utf-8",
        )
        if long_video:
            (jw / "segments").mkdir(parents=True, exist_ok=True)
            (jw / "segments" / "manifest.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "source_video": str((jw / "input" / "source.mp4").resolve()),
                        "source_duration_s": 720.0,
                        "segments": [
                            {
                                "index": 0,
                                "start_s": 0.0,
                                "end_s": 240.0,
                                "workspace": str((jw / "segments" / "seg_000").resolve()),
                                "video": str(
                                    (jw / "segments" / "seg_000" / "input" / "source.mp4").resolve()
                                ),
                            },
                            {
                                "index": 1,
                                "start_s": 240.0,
                                "end_s": 480.0,
                                "workspace": str((jw / "segments" / "seg_001").resolve()),
                                "video": str(
                                    (jw / "segments" / "seg_001" / "input" / "source.mp4").resolve()
                                ),
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            for idx in (0, 1):
                seg = jw / "segments" / f"seg_{idx:03d}"
                (seg / "input").mkdir(parents=True, exist_ok=True)
                (seg / "input" / "source.mp4").write_bytes(b"\x00SEG")
                (seg / "artifacts").mkdir(parents=True, exist_ok=True)
        return jw


class ListJobsEndpointTest(_WorkspaceMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase12_listjobs_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_missing_workspace_root_returns_400(self) -> None:
        status, payload = desktop_server.handle_list_jobs({})
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "missing_field")

    def test_returns_flat_rows_for_plain_workspaces(self) -> None:
        self._make_workspace("job-a")
        self._make_workspace("job-b", long_video=True)
        status, payload = desktop_server.handle_list_jobs(
            {"workspace_root": str(self.tmp_root)}
        )
        self.assertEqual(status, HTTPStatus.OK)
        jobs = {row["job_id"]: row for row in payload["data"]["jobs"]}
        self.assertIn("job-a", jobs)
        self.assertIn("job-b", jobs)
        self.assertEqual(jobs["job-a"]["type"], "single")
        self.assertEqual(jobs["job-b"]["type"], "long")
        self.assertEqual(payload["data"]["totals"]["total"], 2)

    def test_expands_project_children_into_rows(self) -> None:
        project_dir = self.tmp_root / "proj1"
        (project_dir / "videos").mkdir(parents=True, exist_ok=True)
        (project_dir / "project_state.json").write_text(
            json.dumps({"project_id": "proj1", "project_root": str(project_dir)}),
            encoding="utf-8",
        )
        # create a child video workspace inside the project
        self.tmp_root_backup = self.tmp_root
        self.tmp_root = project_dir / "videos"
        try:
            self._make_workspace("ep01")
            self._make_workspace("ep02")
        finally:
            self.tmp_root = self.tmp_root_backup

        status, payload = desktop_server.handle_list_jobs(
            {"workspace_root": str(self.tmp_root)}
        )
        self.assertEqual(status, HTTPStatus.OK)
        parents = {r["parent_project"] for r in payload["data"]["jobs"]}
        self.assertIn("proj1", parents)
        self.assertEqual(len(payload["data"]["projects"]), 1)
        self.assertEqual(payload["data"]["projects"][0]["video_count"], 2)


class ListSegmentsEndpointTest(_WorkspaceMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase12_seg_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_short_workspace_returns_empty_segments(self) -> None:
        jw = self._make_workspace("short-one")
        status, payload = desktop_server.handle_list_segments({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertFalse(payload["data"]["is_long_video"])
        self.assertEqual(payload["data"]["segments"], [])

    def test_long_workspace_returns_segment_rows(self) -> None:
        jw = self._make_workspace("long-one", long_video=True)
        status, payload = desktop_server.handle_list_segments({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["data"]["is_long_video"])
        self.assertEqual(len(payload["data"]["segments"]), 2)
        self.assertEqual(payload["data"]["segments"][0]["index"], 0)


class ListArtifactsEndpointTest(_WorkspaceMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase12_artifacts_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_reports_existing_and_missing_artifacts(self) -> None:
        jw = self._make_workspace("artifact-one")
        status, payload = desktop_server.handle_list_artifacts({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        by_rel = {e["rel_path"]: e for e in payload["data"]["canonical"]}
        self.assertTrue(by_rel["artifacts/edit/edited_voice.srt"]["exists"])
        self.assertIn("artifacts/aligned/alignment_manifest.json", by_rel)
        self.assertIn("artifacts/mixed/mix_manifest.json", by_rel)
        self.assertFalse(by_rel["artifacts/render/final.mp4"]["exists"])
        self.assertTrue(by_rel["job_state.json"]["exists"])


class TTSSettingsEndpointsTest(_WorkspaceMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase12_tts_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_video_tts_save_then_get_roundtrip(self) -> None:
        jw = self._make_workspace("tts-one")
        status, payload = desktop_server.handle_save_video_tts(
            {
                "job_workspace": str(jw),
                "settings": {
                    "tts_provider": "edge_tts",
                    "tts_voice": "vi-VN-HoaiMyNeural",
                    "speed_multiplier": 1.1,
                    "tts_pitch": -5,
                    "mix_mode": "duck_original_speech",
                },
            }
        )
        self.assertEqual(status, HTTPStatus.OK, payload)
        self.assertTrue((jw / "tts_override.json").is_file())
        status, payload = desktop_server.handle_get_video_tts({"job_workspace": str(jw)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["settings"]["tts_voice"], "vi-VN-HoaiMyNeural")
        self.assertEqual(payload["data"]["settings"]["tts_rate"], 10)
        self.assertEqual(payload["data"]["settings"]["speed_multiplier"], 1.1)
        self.assertEqual(payload["data"]["settings"]["mix_mode"], "duck_original_speech")

    def test_rejects_bad_provider(self) -> None:
        jw = self._make_workspace("tts-bad")
        status, payload = desktop_server.handle_save_video_tts(
            {"job_workspace": str(jw), "settings": {"tts_provider": "google"}}
        )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "invalid_tts_settings")

    def test_rejects_rate_out_of_range(self) -> None:
        jw = self._make_workspace("tts-rate")
        status, payload = desktop_server.handle_save_video_tts(
            {"job_workspace": str(jw), "settings": {"tts_rate": 999}}
        )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "invalid_tts_settings")

    def test_project_tts_roundtrip(self) -> None:
        pr = self.tmp_root / "proj"
        pr.mkdir(parents=True, exist_ok=True)
        status, payload = desktop_server.handle_save_project_tts(
            {
                "project_root": str(pr),
                "settings": {
                    "tts_voice": "vi-VN-NamMinhNeural",
                    "mix_mode": "replace_original_speech",
                    "tts_rate": -20,
                },
            }
        )
        self.assertEqual(status, HTTPStatus.OK, payload)
        self.assertTrue((pr / "style" / "tts_settings.json").is_file())
        status, payload = desktop_server.handle_get_project_tts({"project_root": str(pr)})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["settings"]["tts_voice"], "vi-VN-NamMinhNeural")
        self.assertEqual(payload["data"]["settings"]["speed_multiplier"], 0.8)


class RevealEndpointTest(_WorkspaceMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase12_reveal_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_rejects_unknown_path(self) -> None:
        status, payload = desktop_server.handle_reveal({"path": str(self.tmp_root / "missing")})
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "path_not_found")

    def test_opens_existing_directory(self) -> None:
        jw = self._make_workspace("reveal-one")
        captured: list[list[str]] = []

        class _FakePopen:
            def __init__(self, args, **_kwargs):
                captured.append(list(args))

        orig = desktop_server.subprocess.Popen
        desktop_server.subprocess.Popen = _FakePopen  # type: ignore[assignment]
        try:
            status, payload = desktop_server.handle_reveal({"path": str(jw)})
        finally:
            desktop_server.subprocess.Popen = orig  # type: ignore[assignment]
        self.assertEqual(status, HTTPStatus.OK, payload)
        self.assertEqual(len(captured), 1)


class MediaEndpointHTTPTest(_WorkspaceMixin, unittest.TestCase):
    """Spin up a short-lived ThreadingHTTPServer and fetch /media with a Range request."""

    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase12_media_"))
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), desktop_server._Handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.thread.join(timeout=2)
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def _get(self, path: str, *, headers: dict[str, str] | None = None) -> urllib.request.addinfourl:
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        return urllib.request.urlopen(req, timeout=3)

    def test_serves_source_mp4_from_workspace(self) -> None:
        jw = self._make_workspace("media-one")
        src = jw / "input" / "source.mp4"
        src.write_bytes(b"ABCDEFGHIJ")  # 10 bytes sentinel content
        rel = urllib.parse.quote("input/source.mp4", safe="")
        workspace = urllib.parse.quote(str(jw), safe="")
        with self._get(f"/media?workspace={workspace}&rel={rel}") as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.read(), b"ABCDEFGHIJ")

    def test_supports_byte_range_request(self) -> None:
        jw = self._make_workspace("media-range")
        src = jw / "input" / "source.mp4"
        src.write_bytes(b"0123456789")
        rel = urllib.parse.quote("input/source.mp4", safe="")
        workspace = urllib.parse.quote(str(jw), safe="")
        with self._get(
            f"/media?workspace={workspace}&rel={rel}",
            headers={"Range": "bytes=2-5"},
        ) as resp:
            self.assertEqual(resp.status, 206)
            self.assertEqual(resp.read(), b"2345")
            self.assertEqual(resp.headers["Content-Range"], "bytes 2-5/10")

    def test_rejects_path_traversal(self) -> None:
        jw = self._make_workspace("media-safe")
        (self.tmp_root / "outside.txt").write_text("secret", encoding="utf-8")
        workspace = urllib.parse.quote(str(jw), safe="")
        rel = urllib.parse.quote("../outside.txt", safe="")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self._get(f"/media?workspace={workspace}&rel={rel}")
        self.assertEqual(cm.exception.code, HTTPStatus.FORBIDDEN)

    def test_rejects_non_workspace_directory(self) -> None:
        other = self.tmp_root / "notaworkspace"
        other.mkdir(parents=True, exist_ok=True)
        (other / "data.bin").write_bytes(b"hello")
        workspace = urllib.parse.quote(str(other), safe="")
        rel = urllib.parse.quote("data.bin", safe="")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self._get(f"/media?workspace={workspace}&rel={rel}")
        self.assertEqual(cm.exception.code, HTTPStatus.FORBIDDEN)


class DefaultDownloadRootEndpointTest(unittest.TestCase):
    def test_returns_ok_with_downloads_path(self) -> None:
        status, payload = desktop_server.handle_default_download_root({})
        self.assertEqual(status, HTTPStatus.OK)
        path = Path(payload["data"]["workspace_root"])
        self.assertEqual(path.name, "Downloads")
        self.assertTrue(path.is_dir())


class UploadTranslationApiTest(_WorkspaceMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase12_upload_tr_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def _with_source_srt(self, name: str) -> Path:
        jw = self._make_workspace(name)
        transcribe = jw / "artifacts" / "transcribe"
        transcribe.mkdir(parents=True, exist_ok=True)
        srt = (
            "1\n00:00:00,000 --> 00:00:02,000\nAlpha\n\n"
            "2\n00:00:02,000 --> 00:00:04,000\nBeta\n"
        )
        (transcribe / "source.srt").write_text(srt, encoding="utf-8")
        return jw

    def test_success_writes_edited_and_marks_voice_edited(self) -> None:
        jw = self._with_source_srt("upl-ok")
        up = (
            "1\n00:00:00,000 --> 00:00:02,000\nX\n\n"
            "2\n00:00:02,000 --> 00:00:04,000\nY\n"
        )
        status, payload = desktop_server.handle_upload_translation(
            {"job_workspace": str(jw), "srt_text": up}
        )
        self.assertEqual(status, HTTPStatus.OK, payload)
        edited = jw / "artifacts" / "edit" / "edited_voice.srt"
        self.assertTrue(edited.is_file())
        text = edited.read_text(encoding="utf-8")
        self.assertIn("X", text)
        self.assertIn("Y", text)
        self.assertTrue(payload["data"]["voice_edited"])
        self.assertEqual(payload["data"]["voice_edit_status"], "voice_edited")

    def test_cue_count_mismatch_fails(self) -> None:
        jw = self._with_source_srt("upl-bad")
        status, payload = desktop_server.handle_upload_translation(
            {"job_workspace": str(jw), "srt_text": "1\n00:00:00,000 --> 00:00:02,000\nOnly\n"}
        )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "cue_count_mismatch")

    def test_missing_source_srt_fails(self) -> None:
        jw = self._make_workspace("no-source")
        status, payload = desktop_server.handle_upload_translation(
            {"job_workspace": str(jw), "srt_text": "1\n00:00:00,000 --> 00:00:02,000\nX\n"}
        )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "source_srt_missing")


if __name__ == "__main__":
    unittest.main()
