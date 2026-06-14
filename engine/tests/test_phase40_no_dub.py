"""Phase A (no-dub) — no-speech videos render branding-only with original audio.

Auto-classification: an empty transcript -> no-dub. Verified live end-to-end
(9:16 + original audio + logo + outro on a real speechless clip); here we pin the
unit-level guards that run without ffmpeg.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from engine import project_manager as pm
from engine import run_job
from engine.run_render_stage import _parse_args as _render_args


_SRT = "1\n00:00:01,000 --> 00:00:02,000\nhello\n\n2\n00:00:03,000 --> 00:00:04,000\nworld\n"


class NoDubGuardsTest(unittest.TestCase):
    def test_count_source_cues(self) -> None:
        with TemporaryDirectory() as d:
            srt = Path(d) / "source.srt"
            srt.write_text(_SRT, encoding="utf-8")
            self.assertEqual(run_job._count_source_cues(srt), 2)
            empty = Path(d) / "empty.srt"
            empty.write_text("", encoding="utf-8")
            self.assertEqual(run_job._count_source_cues(empty), 0)
            self.assertEqual(run_job._count_source_cues(Path(d) / "missing.srt"), 0)

    def test_render_accepts_original_audio_source(self) -> None:
        ns = _render_args(["--job-workspace", ".", "--audio-source", "original"])
        self.assertEqual(ns.audio_source, "original")

    def test_job_is_no_dub_reads_flag(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            (jw / "job_state.json").write_text(json.dumps({"no_dub": True}), encoding="utf-8")
            self.assertTrue(pm._job_is_no_dub(jw))
            (jw / "job_state.json").write_text(json.dumps({"status": "rendered"}), encoding="utf-8")
            self.assertFalse(pm._job_is_no_dub(jw))
            self.assertFalse(pm._job_is_no_dub(Path(d) / "nope"))


if __name__ == "__main__":
    unittest.main()
