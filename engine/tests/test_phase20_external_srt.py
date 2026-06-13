"""Phase 20: external SRT import helper + orchestrator skip + desktop endpoint."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class ExternalSrtHelperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase20_ext_srt_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_normalize_srt_text_strips_bom_and_crlf(self) -> None:
        from engine.external_srt import normalize_srt_text

        raw = "\ufeff1\r\n00:00:01,000 --> 00:00:02,000\r\nhello\r\n\r\n"
        out = normalize_srt_text(raw)
        self.assertNotIn("\r", out)
        self.assertNotIn("\ufeff", out)
        self.assertIn("00:00:01,000 --> 00:00:02,000", out)
        self.assertIn("hello", out)

    def test_import_external_srt_rejects_empty_file(self) -> None:
        from engine.external_srt import import_external_srt

        jw = self.root / "job_a"
        jw.mkdir()
        ext = self.root / "empty.srt"
        ext.write_bytes(b"")
        with self.assertRaises(ValueError):
            import_external_srt(job_workspace=jw, source_path=ext)

    def test_import_external_srt_rejects_non_srt(self) -> None:
        from engine.external_srt import import_external_srt

        jw = self.root / "job_b"
        jw.mkdir()
        ext = self.root / "bad.srt"
        ext.write_text("not a subtitle file\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            import_external_srt(job_workspace=jw, source_path=ext)

    def test_import_external_srt_writes_manifest_and_updates_states(self) -> None:
        from engine.external_srt import import_external_srt

        jw = self.root / "my_job"
        jw.mkdir()
        (jw / "input").mkdir()
        (jw / "input" / "source.mp4").write_bytes(b"\x00fake")

        ext = self.root / "capcut.srt"
        ext.write_text(
            "1\n00:00:01,000 --> 00:00:02,000\nline one\n\n"
            "2\n00:00:05,000 --> 00:00:06,000\nline two\n\n",
            encoding="utf-8",
        )

        manifest = import_external_srt(job_workspace=jw, source_path=ext)
        self.assertEqual(manifest["cue_count"], 2)
        self.assertEqual(manifest["first_cue_start_ms"], 1000)
        self.assertEqual(manifest["last_cue_end_ms"], 6000)
        self.assertEqual(manifest["original_size_bytes"], ext.stat().st_size)
        self.assertIn("imported_at", manifest)
        self.assertEqual(manifest["source_path"], str(ext.resolve()))

        mf_path = jw / "artifacts" / "transcribe" / "external_srt_manifest.json"
        self.assertTrue(mf_path.is_file())

    def test_import_external_srt_accepts_utf16_encoded_file(self) -> None:
        from engine.external_srt import import_external_srt

        jw = self.root / "utf16_job"
        jw.mkdir()
        (jw / "input").mkdir()
        (jw / "input" / "source.mp4").write_bytes(b"\x00fake")

        ext = self.root / "utf16.srt"
        text = "1\n00:00:00,000 --> 00:00:01,000\nhello\n\n"
        ext.write_bytes(text.encode("utf-16"))

        manifest = import_external_srt(job_workspace=jw, source_path=ext)
        self.assertEqual(manifest["cue_count"], 1)
        normalized = (jw / "artifacts" / "transcribe" / "source.srt").read_text(encoding="utf-8")
        self.assertIn("hello", normalized)

        job_state = json.loads((jw / "job_state.json").read_text(encoding="utf-8"))
        self.assertEqual(job_state.get("status"), "transcribed")
        self.assertEqual(job_state.get("subtitle_extractor"), "external_srt")
        self.assertEqual(job_state.get("transcription_engine"), "external_srt")
        self.assertIn("transcribe_output_srt", job_state)
        ap = job_state.get("artifact_paths") or {}
        self.assertIn("source_srt", ap)
        self.assertIn("source_srt_origin", ap)

        video_state = json.loads((jw / "video_state.json").read_text(encoding="utf-8"))
        self.assertEqual(video_state.get("status"), "transcribed")
        self.assertEqual(video_state.get("subtitle_extractor"), "external_srt")


class RunJobExternalSrtSkipTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase20_run_job_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_run_job_skips_transcribe_stage_when_external_srt(self) -> None:
        from engine import run_job, run_transcribe_stage

        jw = self.root / "jw1"
        jw.mkdir(parents=True)
        (jw / "artifacts" / "transcribe").mkdir(parents=True)
        (jw / "job_state.json").write_text(
            json.dumps({"job_id": "jw1", "subtitle_extractor": "external_srt"}),
            encoding="utf-8",
        )
        (jw / "artifacts" / "transcribe" / "source.srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nok\n\n", encoding="utf-8"
        )

        with mock.patch.object(run_transcribe_stage, "main") as transcribe_main:
            rc = run_job.main(
                [
                    "--job-workspace",
                    str(jw),
                    "--project-name",
                    "p",
                    "--to-stage",
                    "transcribed",
                ]
            )
        self.assertEqual(rc, 0)
        transcribe_main.assert_not_called()

    def test_run_job_external_srt_missing_source_blocks(self) -> None:
        from engine import run_job, run_transcribe_stage

        jw = self.root / "jw2"
        jw.mkdir(parents=True)
        (jw / "job_state.json").write_text(
            json.dumps({"job_id": "jw2", "subtitle_extractor": "external_srt"}),
            encoding="utf-8",
        )

        with mock.patch.object(run_transcribe_stage, "main") as transcribe_main:
            rc = run_job.main(
                [
                    "--job-workspace",
                    str(jw),
                    "--project-name",
                    "p",
                    "--to-stage",
                    "transcribed",
                ]
            )
        self.assertEqual(rc, 1)
        transcribe_main.assert_not_called()

    def test_run_job_external_srt_invokes_translate_when_to_stage_translated(self) -> None:
        from engine import run_job, run_transcribe_stage, run_translate_stage

        jw = self.root / "jw_translate"
        jw.mkdir(parents=True)
        (jw / "artifacts" / "transcribe").mkdir(parents=True)
        (jw / "job_state.json").write_text(
            json.dumps({"job_id": "jw_translate", "subtitle_extractor": "external_srt"}),
            encoding="utf-8",
        )
        (jw / "artifacts" / "transcribe" / "source.srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nok\n\n", encoding="utf-8"
        )

        with mock.patch.object(run_transcribe_stage, "main") as transcribe_main, mock.patch.object(
            run_translate_stage, "main", return_value=0
        ) as translate_main:
            rc = run_job.main(
                [
                    "--job-workspace",
                    str(jw),
                    "--project-name",
                    "p",
                    "--to-stage",
                    "translated",
                ]
            )
        self.assertEqual(rc, 0)
        transcribe_main.assert_not_called()
        translate_main.assert_called_once()
