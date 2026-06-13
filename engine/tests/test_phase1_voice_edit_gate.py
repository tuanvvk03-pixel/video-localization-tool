"""Phase 1 acceptance: voice edit gate.

Covers PROJECT_HANDOFF Phase 1 criteria:
- seed creates artifacts/edit/edited_voice.srt + edit_manifest.json
- state transitions to voice_edit_pending after seed
- mark_voice_edited flips voice_edited=True
- finalize voice prefers edited_voice.srt over translated_voice.srt
- run_job.py blocks finalize/TTS when finalize_mode=voice and voice not edited
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.run_finalize_subtitle_stage import main as finalize_main
from engine.run_job import _voice_edit_completed
from engine.voice_edit_api import (
    get_voice_subtitle_source,
    mark_voice_edited,
    save_edited_voice,
    seed_edited_voice,
)


SAMPLE_VOICE_SRT = (
    "1\n00:00:00,000 --> 00:00:02,000\nXin chao the gioi\n\n"
    "2\n00:00:02,000 --> 00:00:04,000\nCau hai\n\n"
)


class Phase1VoiceEditGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase1_voice_edit_"))
        self.jw = self.tmp_root / "job"
        (self.jw / "artifacts" / "translate").mkdir(parents=True)
        (self.jw / "artifacts" / "transcribe").mkdir(parents=True)
        (self.jw / "input").mkdir(parents=True)
        (self.jw / "artifacts" / "translate" / "translated_voice.srt").write_text(
            SAMPLE_VOICE_SRT, encoding="utf-8"
        )
        (self.jw / "artifacts" / "translate" / "translated_auto.srt").write_text(
            SAMPLE_VOICE_SRT, encoding="utf-8"
        )
        (self.jw / "artifacts" / "transcribe" / "source.srt").write_text(
            "1\n00:00:00,000 --> 00:00:02,000\nhello\n\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def _state(self) -> dict:
        return json.loads((self.jw / "job_state.json").read_text(encoding="utf-8"))

    def test_seed_sets_voice_edit_pending_and_creates_artifacts(self) -> None:
        out = seed_edited_voice(self.jw)
        self.assertTrue(out.is_file())
        self.assertEqual(out.name, "edited_voice.srt")
        self.assertTrue((self.jw / "artifacts" / "edit" / "edit_manifest.json").is_file())

        js = self._state()
        self.assertEqual(js.get("status"), "voice_edit_pending")
        self.assertEqual(js.get("voice_edit_status"), "voice_edit_pending")
        self.assertFalse(js.get("voice_edited"))
        self.assertFalse(_voice_edit_completed(self.jw))

    def test_source_priority_prefers_edited_voice_after_seed(self) -> None:
        seed_edited_voice(self.jw)
        info = get_voice_subtitle_source(self.jw)
        self.assertEqual(info.mode, "edited_voice")

    def test_save_and_mark_voice_edited_flips_state(self) -> None:
        seed_edited_voice(self.jw)
        edited = SAMPLE_VOICE_SRT.replace("Xin chao the gioi", "Xin chao (da sua)")
        save_edited_voice(self.jw, edited_voice_text=edited)
        mark_voice_edited(self.jw)

        js = self._state()
        self.assertTrue(js.get("voice_edited"))
        self.assertEqual(js.get("voice_edit_status"), "voice_edited")
        self.assertTrue(_voice_edit_completed(self.jw))

    def test_reseed_existing_file_resets_state_to_pending(self) -> None:
        seed_edited_voice(self.jw)
        mark_voice_edited(self.jw)

        out = seed_edited_voice(self.jw, overwrite=False)
        self.assertTrue(out.is_file())

        js = self._state()
        self.assertEqual(js.get("status"), "voice_edit_pending")
        self.assertEqual(js.get("voice_edit_status"), "voice_edit_pending")
        self.assertFalse(js.get("voice_edited"))
        self.assertFalse(_voice_edit_completed(self.jw))

    def test_save_after_approval_resets_state_to_pending(self) -> None:
        seed_edited_voice(self.jw)
        mark_voice_edited(self.jw)

        edited = SAMPLE_VOICE_SRT.replace("Cau hai", "Cau hai (draft moi)")
        save_edited_voice(self.jw, edited_voice_text=edited)

        js = self._state()
        self.assertEqual(js.get("status"), "voice_edit_pending")
        self.assertEqual(js.get("voice_edit_status"), "voice_edit_pending")
        self.assertFalse(js.get("voice_edited"))
        self.assertFalse(_voice_edit_completed(self.jw))

    def test_finalize_voice_prefers_edited_voice_over_translated_voice(self) -> None:
        seed_edited_voice(self.jw)
        edited = SAMPLE_VOICE_SRT.replace("Xin chao the gioi", "Xin chao (da sua)")
        save_edited_voice(self.jw, edited_voice_text=edited)
        mark_voice_edited(self.jw)

        rc = finalize_main(["--job-workspace", str(self.jw), "--finalize-mode", "voice"])
        self.assertEqual(rc, 0)

        final_srt = (self.jw / "artifacts" / "translate" / "final_subtitle.srt").read_text(
            encoding="utf-8"
        )
        self.assertIn("(da sua)", final_srt)

        manifest = json.loads(
            (self.jw / "artifacts" / "translate" / "final_subtitle_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest.get("finalize_mode"), "voice")
        self.assertEqual(
            Path(manifest["selected_source_subtitle_path"]).name, "edited_voice.srt"
        )


if __name__ == "__main__":
    unittest.main()
