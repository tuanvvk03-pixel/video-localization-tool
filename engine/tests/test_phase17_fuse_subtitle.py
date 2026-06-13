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

from engine.fuse_subtitle import (
    Cue,
    build_provenance,
    cues_to_srt,
    fuse_cues,
    fuse_files,
    parse_srt,
)


def _write_srt(path: Path, cues: list[Cue]) -> None:
    lines: list[str] = []
    for i, c in enumerate(cues, start=1):
        lines.append(str(i))
        lines.append(f"{_fmt(c.start_ms)} --> {_fmt(c.end_ms)}")
        lines.append(c.text)
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _fmt(ms: int) -> str:
    h = ms // 3_600_000
    rem = ms - h * 3_600_000
    mm = rem // 60_000
    rem -= mm * 60_000
    s = rem // 1000
    ms_part = rem - s * 1000
    return f"{h:02d}:{mm:02d}:{s:02d},{ms_part:03d}"


class FuseRulesTest(unittest.TestCase):
    def test_asr_only_cue_kept_when_no_ocr_overlap(self) -> None:
        asr = [Cue(1000, 2000, "hello world")]
        ocr: list[Cue] = []
        fused = fuse_cues(asr, ocr)
        self.assertEqual(len(fused), 1)
        self.assertEqual(fused[0].source, "asr")
        self.assertEqual(fused[0].text, "hello world")

    def test_ocr_only_cue_kept_when_no_asr_overlap(self) -> None:
        ocr = [Cue(1000, 2000, "你好世界")]
        fused = fuse_cues([], ocr)
        self.assertEqual(len(fused), 1)
        self.assertEqual(fused[0].source, "ocr")
        self.assertEqual(fused[0].text, "你好世界")

    def test_fused_match_keeps_ocr_text_with_low_diff(self) -> None:
        asr = [Cue(1000, 3000, "hello world")]
        ocr = [Cue(1100, 3000, "hello world")]
        fused = fuse_cues(asr, ocr, ocr_confidences={0: 0.92})
        self.assertEqual(len(fused), 1)
        self.assertEqual(fused[0].source, "fused_match")
        self.assertEqual(fused[0].text, "hello world")
        self.assertAlmostEqual(fused[0].ocr_confidence, 0.92)
        self.assertEqual(fused[0].start_ms, 1000)
        self.assertEqual(fused[0].end_ms, 3000)
        self.assertLess(fused[0].asr_text_diff, 0.15)

    def test_fused_drift_keeps_ocr_text_with_moderate_diff(self) -> None:
        # diff ~0.25 (3 of 11 chars changed)
        asr = [Cue(1000, 3000, "hello world")]
        ocr = [Cue(1100, 3000, "hella warld")]
        fused = fuse_cues(asr, ocr)
        self.assertEqual(len(fused), 1)
        self.assertEqual(fused[0].source, "fused_drift")
        self.assertEqual(fused[0].text, "hella warld")
        self.assertGreater(fused[0].asr_text_diff, 0.15)
        self.assertLessEqual(fused[0].asr_text_diff, 0.40)

    def test_fused_disagreement_keeps_both_texts_and_flags_review(self) -> None:
        asr = [Cue(1000, 3000, "completely different audio")]
        ocr = [Cue(1100, 3000, "你好世界中文")]
        fused = fuse_cues(asr, ocr)
        self.assertEqual(len(fused), 1)
        self.assertEqual(fused[0].source, "fused_disagreement")
        self.assertTrue(fused[0].needs_review)
        self.assertIn("你好世界中文", fused[0].text)
        self.assertIn("completely different audio", fused[0].text)
        self.assertGreater(fused[0].asr_text_diff, 0.40)

    def test_time_alignment_uses_min_start_max_end(self) -> None:
        asr = [Cue(1000, 2500, "hello")]
        ocr = [Cue(900, 2600, "hello")]
        fused = fuse_cues(asr, ocr)
        self.assertEqual(fused[0].start_ms, 900)
        self.assertEqual(fused[0].end_ms, 2600)

    def test_asr_cue_not_matched_to_any_ocr_cue_survives(self) -> None:
        asr = [
            Cue(1000, 2000, "first asr line"),
            Cue(5000, 6000, "standalone asr cue"),
        ]
        ocr = [Cue(1100, 2000, "first asr line")]
        fused = fuse_cues(asr, ocr)
        sources = [c.source for c in fused]
        self.assertIn("fused_match", sources)
        self.assertIn("asr", sources)
        asr_only = next(c for c in fused if c.source == "asr")
        self.assertEqual(asr_only.text, "standalone asr cue")

    def test_output_sorted_by_start_time(self) -> None:
        asr = [Cue(5000, 6000, "later asr")]
        ocr = [Cue(1000, 2000, "earlier ocr")]
        fused = fuse_cues(asr, ocr)
        self.assertEqual([c.start_ms for c in fused], [1000, 5000])

    def test_greedy_picks_best_overlap(self) -> None:
        # One OCR cue overlaps two ASR cues; it should claim the larger overlap.
        asr = [
            Cue(1000, 1200, "short overlap"),
            Cue(2000, 4000, "primary asr text"),
        ]
        ocr = [Cue(2100, 3900, "primary ocr text")]
        fused = fuse_cues(asr, ocr)
        # First asr (no match now) should survive as source="asr"
        sources = [c.source for c in fused]
        self.assertEqual(sources.count("asr"), 1)
        self.assertTrue(any(c.source.startswith("fused_") for c in fused))


class ProvenanceTest(unittest.TestCase):
    def test_provenance_entries_include_source_and_diff(self) -> None:
        asr = [Cue(1000, 2000, "same")]
        ocr = [Cue(1000, 2000, "same")]
        fused = fuse_cues(asr, ocr, ocr_confidences={0: 0.88})
        prov = build_provenance(fused, asr_cue_count=1, ocr_cue_count=1)
        self.assertEqual(prov["extractor"], "hybrid")
        self.assertEqual(prov["asr_cue_count"], 1)
        self.assertEqual(prov["ocr_cue_count"], 1)
        self.assertEqual(prov["final_cue_count"], 1)
        entry = prov["cues"][0]
        self.assertEqual(entry["index"], 1)
        self.assertEqual(entry["source"], "fused_match")
        self.assertIn("asr_text_diff", entry)
        self.assertAlmostEqual(entry["ocr_confidence"], 0.88)

    def test_disagreement_entry_marks_needs_review(self) -> None:
        asr = [Cue(1000, 2000, "completely different")]
        ocr = [Cue(1000, 2000, "不同")]
        fused = fuse_cues(asr, ocr)
        prov = build_provenance(fused, asr_cue_count=1, ocr_cue_count=1)
        entry = prov["cues"][0]
        self.assertEqual(entry["source"], "fused_disagreement")
        self.assertTrue(entry["needs_review"])
        self.assertIn("ocr_text", entry)
        self.assertIn("asr_text", entry)


class SrtIoTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase17_fuse_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_parse_srt_handles_windows_newlines_and_blank_lines(self) -> None:
        p = self.root / "sample.srt"
        # write_bytes to bypass universal-newline translation and keep \r\n exact.
        p.write_bytes(
            b"1\r\n00:00:01,000 --> 00:00:02,000\r\nHello world\r\n\r\n"
            b"2\r\n00:00:03,000 --> 00:00:04,000\r\nSecond line\r\n"
        )
        cues = parse_srt(p)
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0].text, "Hello world")
        self.assertEqual(cues[1].start_ms, 3000)

    def test_parse_srt_returns_empty_for_missing_file(self) -> None:
        self.assertEqual(parse_srt(self.root / "nope.srt"), [])

    def test_cues_to_srt_roundtrip(self) -> None:
        from engine.fuse_subtitle import FusedCue

        fused = [
            FusedCue(1000, 2000, "hello", "asr"),
            FusedCue(3000, 4500, "world", "ocr"),
        ]
        srt = cues_to_srt(fused)
        self.assertIn("00:00:01,000 --> 00:00:02,000", srt)
        self.assertIn("00:00:04,500", srt)
        self.assertIn("world", srt)

    def test_fuse_files_writes_srt_and_provenance(self) -> None:
        asr_srt = self.root / "source_audio.srt"
        ocr_srt = self.root / "source_ocr.srt"
        out_srt = self.root / "source.srt"
        out_prov = self.root / "source_provenance.json"

        _write_srt(
            asr_srt,
            [
                Cue(1000, 2000, "hello world"),
                Cue(5000, 6000, "alone asr"),
            ],
        )
        _write_srt(
            ocr_srt,
            [
                Cue(1050, 2100, "hello world"),
                Cue(8000, 9000, "alone ocr"),
            ],
        )
        prov = fuse_files(asr_srt, ocr_srt, out_srt=out_srt, out_provenance=out_prov)

        self.assertTrue(out_srt.is_file())
        self.assertTrue(out_prov.is_file())
        saved = json.loads(out_prov.read_text(encoding="utf-8"))
        self.assertEqual(saved["asr_cue_count"], 2)
        self.assertEqual(saved["ocr_cue_count"], 2)
        self.assertEqual(saved["final_cue_count"], 3)  # match + asr_only + ocr_only

        sources = sorted(c["source"] for c in saved["cues"])
        self.assertEqual(sources, ["asr", "fused_match", "ocr"])
        self.assertEqual(prov, saved)

        merged = out_srt.read_text(encoding="utf-8")
        self.assertEqual(merged.count(" --> "), 3)


class FuseStageCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase17_fuse_cli_"))
        self.jw = self.root / "job_demo"
        (self.jw / "artifacts" / "transcribe").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_cli_writes_canonical_outputs(self) -> None:
        from engine import run_fuse_subtitle_stage

        transcribe_dir = self.jw / "artifacts" / "transcribe"
        _write_srt(transcribe_dir / "source_audio.srt", [Cue(1000, 2000, "abc")])
        _write_srt(transcribe_dir / "source_ocr.srt", [Cue(1000, 2000, "abc")])

        rc = run_fuse_subtitle_stage.main(["--job-workspace", str(self.jw)])
        self.assertEqual(rc, 0)
        self.assertTrue((transcribe_dir / "source.srt").is_file())
        self.assertTrue((transcribe_dir / "source_provenance.json").is_file())

    def test_cli_fails_when_both_srts_missing(self) -> None:
        from engine import run_fuse_subtitle_stage

        rc = run_fuse_subtitle_stage.main(["--job-workspace", str(self.jw)])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
