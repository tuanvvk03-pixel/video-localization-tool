"""Phase 20: desktop server endpoints for external SRT (roadmap 5.2)."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from http import HTTPStatus
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class DesktopImportExternalSrtTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase20_desktop_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_handle_import_external_srt_success(self) -> None:
        from desktop import server as desktop_server

        jw = self.root / "job_ok"
        jw.mkdir()
        ext = self.root / "in.srt"
        ext.write_text("1\n00:00:00,000 --> 00:00:01,000\nx\n\n", encoding="utf-8")
        st, payload = desktop_server.handle_import_external_srt(
            {"job_workspace": str(jw), "srt_path": str(ext)}
        )
        self.assertEqual(st, HTTPStatus.OK)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["cue_count"], 1)

    def test_handle_import_external_srt_missing_file(self) -> None:
        from desktop import server as desktop_server

        jw = self.root / "job_nf"
        jw.mkdir()
        st, payload = desktop_server.handle_import_external_srt(
            {"job_workspace": str(jw), "srt_path": str(self.root / "missing.srt")}
        )
        self.assertEqual(st, HTTPStatus.BAD_REQUEST)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "srt_not_found")

    def test_handle_import_external_srt_invalid_srt(self) -> None:
        from desktop import server as desktop_server

        jw = self.root / "job_inv"
        jw.mkdir()
        ext = self.root / "bad2.srt"
        ext.write_text("no timestamps here\n", encoding="utf-8")
        st, payload = desktop_server.handle_import_external_srt(
            {"job_workspace": str(jw), "srt_path": str(ext)}
        )
        self.assertEqual(st, HTTPStatus.BAD_REQUEST)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "invalid_srt")

    def test_normalize_extractor_external_srt_clears_ocr(self) -> None:
        from desktop import server as desktop_server

        cfg = desktop_server._normalize_extractor_settings(
            {
                "subtitle_extractor": "external_srt",
                "ocr_provider": "paddleocr",
                "ocr_language": "ch",
                "ocr_device": "cuda",
                "ocr_roi": '{"x":0,"y":0,"w":1,"h":1}',
            }
        )
        self.assertEqual(cfg["subtitle_extractor"], "external_srt")
        self.assertEqual(cfg["ocr_provider"], "")
        self.assertEqual(cfg["ocr_language"], "")
        self.assertEqual(cfg["ocr_device"], "")
        self.assertEqual(cfg["ocr_roi"], "")


class JobSummaryTranscriptionSourceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase20_jsum_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_imported_srt_from_state(self) -> None:
        from desktop import server as desktop_server

        jw = self.root / "v1"
        jw.mkdir()
        (jw / "job_state.json").write_text(
            json.dumps(
                {
                    "subtitle_extractor": "external_srt",
                    "transcription_engine": "external_srt",
                }
            ),
            encoding="utf-8",
        )
        row = desktop_server._job_summary(jw)
        self.assertEqual(row["transcription_source"], "imported_srt")

    def test_asr_local_default(self) -> None:
        from desktop import server as desktop_server

        jw = self.root / "v2"
        jw.mkdir()
        (jw / "job_state.json").write_text(json.dumps({"status": "imported"}), encoding="utf-8")
        row = desktop_server._job_summary(jw)
        self.assertEqual(row["transcription_source"], "asr_local")

    def test_legacy_ocr_on_disk(self) -> None:
        from desktop import server as desktop_server

        jw = self.root / "v3"
        jw.mkdir()
        (jw / "video_state.json").write_text(
            json.dumps({"subtitle_extractor": "hybrid"}),
            encoding="utf-8",
        )
        row = desktop_server._job_summary(jw)
        self.assertEqual(row["transcription_source"], "legacy_ocr")
