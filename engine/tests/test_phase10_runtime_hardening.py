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

from engine.input_provenance import (
    invalidate_from_finalize_downward,
    invalidate_from_transcribe_downward,
)
from engine.run_job import main as run_job_main
from engine.workspace_lock import acquire_workspace_lock


class RuntimeHardeningTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase10_hardening_"))
        self.jw = self.root / "job"
        (self.jw / "input").mkdir(parents=True)
        (self.jw / "artifacts" / "transcribe").mkdir(parents=True)
        (self.jw / "artifacts" / "translate").mkdir(parents=True)
        (self.jw / "artifacts" / "edit").mkdir(parents=True)
        (self.jw / "input" / "source.mp4").write_bytes(b"x")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _write_states(self) -> None:
        (self.jw / "job_state.json").write_text(
            json.dumps(
                {
                    "status": "rendered",
                    "current_stage": "rendered",
                    "voice_edit_status": "voice_edited",
                    "voice_edited": True,
                    "edited_voice_path": str(
                        (self.jw / "artifacts" / "edit" / "edited_voice.srt").resolve()
                    ),
                    "edit_manifest_path": str(
                        (self.jw / "artifacts" / "edit" / "edit_manifest.json").resolve()
                    ),
                    "final_subtitle_path": str(
                        (self.jw / "artifacts" / "translate" / "final_subtitle.srt").resolve()
                    ),
                    "tts_manifest_path": str(
                        (self.jw / "artifacts" / "tts" / "tts_manifest.json").resolve()
                    ),
                }
            ),
            encoding="utf-8",
        )
        (self.jw / "video_state.json").write_text(
            json.dumps(
                {
                    "status": "rendered",
                    "current_stage": "rendered",
                    "voice_edit_status": "voice_edited",
                    "voice_edited": True,
                    "subtitle_source_mode": "edited_voice",
                    "finalize_source_srt": str(
                        (self.jw / "artifacts" / "edit" / "edited_voice.srt").resolve()
                    ),
                    "artifact_paths": {
                        "source_srt": str(
                            (self.jw / "artifacts" / "transcribe" / "source.srt").resolve()
                        ),
                        "translated_voice_srt": str(
                            (
                                self.jw
                                / "artifacts"
                                / "translate"
                                / "translated_voice.srt"
                            ).resolve()
                        ),
                        "edited_voice_srt": str(
                            (self.jw / "artifacts" / "edit" / "edited_voice.srt").resolve()
                        ),
                        "edit_manifest": str(
                            (self.jw / "artifacts" / "edit" / "edit_manifest.json").resolve()
                        ),
                        "final_subtitle_srt": str(
                            (
                                self.jw / "artifacts" / "translate" / "final_subtitle.srt"
                            ).resolve()
                        ),
                        "tts_manifest": str(
                            (self.jw / "artifacts" / "tts" / "tts_manifest.json").resolve()
                        ),
                    },
                }
            ),
            encoding="utf-8",
        )

    def test_workspace_lock_blocks_second_run_without_mutating_state(self) -> None:
        stderr = io.StringIO()
        with acquire_workspace_lock(self.jw, owner="run_job"):
            with contextlib.redirect_stderr(stderr):
                rc = run_job_main(
                    [
                        "--job-workspace",
                        str(self.jw),
                        "--project-name",
                        "demo",
                        "--to-stage",
                        "imported",
                    ]
                )
        self.assertEqual(rc, 3)
        self.assertIn("Workspace is busy", stderr.getvalue())
        self.assertFalse((self.jw / "job_state.json").is_file())

    def test_invalidate_from_transcribe_downward_clears_voice_edit_state_everywhere(self) -> None:
        (self.jw / "artifacts" / "transcribe" / "source.srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nhello\n\n", encoding="utf-8"
        )
        (self.jw / "artifacts" / "translate" / "translated_voice.srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nxin chao\n\n", encoding="utf-8"
        )
        (self.jw / "artifacts" / "translate" / "final_subtitle.srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nxin chao\n\n", encoding="utf-8"
        )
        (self.jw / "artifacts" / "edit" / "edited_voice.srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nxin chao da sua\n\n", encoding="utf-8"
        )
        (self.jw / "artifacts" / "edit" / "edit_manifest.json").write_text(
            json.dumps({"version": 1}), encoding="utf-8"
        )
        (self.jw / "artifacts" / "tts").mkdir(parents=True)
        (self.jw / "artifacts" / "tts" / "tts_manifest.json").write_text(
            json.dumps({"version": 1}), encoding="utf-8"
        )
        self._write_states()

        invalidate_from_transcribe_downward(self.jw, reason="test")

        job_state = json.loads((self.jw / "job_state.json").read_text(encoding="utf-8"))
        video_state = json.loads((self.jw / "video_state.json").read_text(encoding="utf-8"))
        self.assertEqual(job_state.get("status"), "transcribed")
        self.assertEqual(job_state.get("current_stage"), "transcribed")
        self.assertIsNone(job_state.get("voice_edit_status"))
        self.assertFalse(job_state.get("voice_edited"))
        self.assertIsNone(job_state.get("edited_voice_path"))
        self.assertIsNone(job_state.get("edit_manifest_path"))
        self.assertEqual(video_state.get("status"), "transcribed")
        self.assertEqual(video_state.get("current_stage"), "transcribed")
        self.assertIsNone(video_state.get("voice_edit_status"))
        self.assertFalse(video_state.get("voice_edited"))
        self.assertNotIn("edited_voice_srt", video_state.get("artifact_paths", {}))
        self.assertNotIn("edit_manifest", video_state.get("artifact_paths", {}))
        self.assertNotIn("final_subtitle_srt", video_state.get("artifact_paths", {}))
        self.assertFalse((self.jw / "artifacts" / "edit" / "edited_voice.srt").exists())
        self.assertFalse((self.jw / "artifacts" / "edit" / "edit_manifest.json").exists())
        self.assertFalse((self.jw / "artifacts" / "tts").exists())

    def test_invalidate_from_finalize_downward_preserves_completed_voice_edit(self) -> None:
        (self.jw / "artifacts" / "edit" / "edited_voice.srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nxin chao da sua\n\n", encoding="utf-8"
        )
        (self.jw / "artifacts" / "edit" / "edit_manifest.json").write_text(
            json.dumps({"version": 1}), encoding="utf-8"
        )
        (self.jw / "artifacts" / "translate" / "final_subtitle.srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nxin chao da sua\n\n", encoding="utf-8"
        )
        (self.jw / "artifacts" / "translate" / "final_subtitle_manifest.json").write_text(
            json.dumps({"version": 1}), encoding="utf-8"
        )
        (self.jw / "artifacts" / "tts").mkdir(parents=True)
        (self.jw / "artifacts" / "tts" / "tts_manifest.json").write_text(
            json.dumps({"version": 1}), encoding="utf-8"
        )
        self._write_states()

        invalidate_from_finalize_downward(self.jw, reason="test")

        job_state = json.loads((self.jw / "job_state.json").read_text(encoding="utf-8"))
        video_state = json.loads((self.jw / "video_state.json").read_text(encoding="utf-8"))
        self.assertEqual(job_state.get("status"), "voice_edited")
        self.assertEqual(job_state.get("current_stage"), "voice_edited")
        self.assertEqual(job_state.get("voice_edit_status"), "voice_edited")
        self.assertTrue(job_state.get("voice_edited"))
        self.assertEqual(video_state.get("status"), "voice_edited")
        self.assertEqual(video_state.get("current_stage"), "voice_edited")
        self.assertEqual(video_state.get("voice_edit_status"), "voice_edited")
        self.assertTrue(video_state.get("voice_edited"))
        self.assertNotIn("final_subtitle_srt", video_state.get("artifact_paths", {}))
        self.assertNotIn("tts_manifest", video_state.get("artifact_paths", {}))
        self.assertTrue((self.jw / "artifacts" / "edit" / "edited_voice.srt").is_file())
        self.assertFalse((self.jw / "artifacts" / "translate" / "final_subtitle.srt").exists())
        self.assertFalse((self.jw / "artifacts" / "tts").exists())


if __name__ == "__main__":
    unittest.main()
