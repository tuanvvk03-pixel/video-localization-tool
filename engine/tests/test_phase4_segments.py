"""Phase 4 acceptance: segment planning + SRT merging.

Tests cover pure functions (no ffmpeg required). ffmpeg-dependent behaviour
(probe/split/concat) is covered by integration tests run manually against real
videos — those are intentionally out of scope here.
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

from engine.segment_manager import (
    SegmentError,
    SegmentPlan,
    SINGLE_VIDEO_THRESHOLD_S,
    load_segment_manifest,
    merge_segment_final_subtitles,
    merge_srts_with_offsets,
    plan_segments,
    shift_cues,
)
from engine.srt_cues import parse_srt_cues


class PlanSegmentsTest(unittest.TestCase):
    def test_under_threshold_single_segment(self) -> None:
        for d in (30.0, 120.0, 299.0, float(SINGLE_VIDEO_THRESHOLD_S)):
            plan = plan_segments(d)
            self.assertEqual(len(plan), 1, msg=f"d={d}")
            self.assertEqual(plan[0].start_s, 0.0)
            self.assertAlmostEqual(plan[0].end_s, d)

    def test_ten_minutes_splits_into_chunks_under_max(self) -> None:
        plan = plan_segments(10 * 60)
        # 10 min / round(10/4)=2 -> 5 min each (equal to max, acceptable).
        self.assertGreaterEqual(len(plan), 2)
        self._assert_contiguous(plan, total=600.0)
        for seg in plan:
            self.assertLessEqual(seg.duration_s, 5 * 60 + 0.001)

    def test_twenty_minutes_stays_under_max(self) -> None:
        plan = plan_segments(20 * 60)
        self.assertGreaterEqual(len(plan), 4)
        self._assert_contiguous(plan, total=1200.0)
        for seg in plan:
            self.assertLessEqual(seg.duration_s, 5 * 60 + 0.001)

    def test_just_over_threshold_splits(self) -> None:
        plan = plan_segments(6 * 60)
        self.assertEqual(len(plan), 2)
        self._assert_contiguous(plan, total=360.0)

    def test_invalid_duration_raises(self) -> None:
        with self.assertRaises(SegmentError):
            plan_segments(0)
        with self.assertRaises(SegmentError):
            plan_segments(-5)

    def _assert_contiguous(self, plan: list[SegmentPlan], *, total: float) -> None:
        self.assertAlmostEqual(plan[0].start_s, 0.0)
        for a, b in zip(plan, plan[1:]):
            self.assertAlmostEqual(a.end_s, b.start_s)
        self.assertAlmostEqual(plan[-1].end_s, total)


class ShiftCuesTest(unittest.TestCase):
    def test_shift_preserves_text_and_clamps_nonnegative(self) -> None:
        cues = parse_srt_cues(
            "1\n00:00:01,000 --> 00:00:03,000\nHello\n\n"
            "2\n00:00:03,000 --> 00:00:05,000\nWorld\n\n"
        )
        shifted = shift_cues(cues, 2000)
        self.assertEqual(shifted[0].start_ms, 3000)
        self.assertEqual(shifted[1].end_ms, 7000)
        self.assertEqual(shifted[0].text, "Hello")

        clamped = shift_cues(cues, -10_000)
        self.assertEqual(clamped[0].start_ms, 0)
        self.assertEqual(clamped[0].end_ms, 0)


class MergeSrtsTest(unittest.TestCase):
    def test_concatenate_two_segments_with_offsets(self) -> None:
        seg_a = (
            "1\n00:00:00,000 --> 00:00:02,000\nSeg A1\n\n"
            "2\n00:00:02,000 --> 00:00:04,000\nSeg A2\n\n"
        )
        seg_b = (
            "1\n00:00:00,000 --> 00:00:02,000\nSeg B1\n\n"
            "2\n00:00:02,000 --> 00:00:04,000\nSeg B2\n\n"
        )
        merged = merge_srts_with_offsets([seg_a, seg_b], [0, 4000])
        cues = parse_srt_cues(merged)
        self.assertEqual([c.text for c in cues], ["Seg A1", "Seg A2", "Seg B1", "Seg B2"])
        self.assertEqual([c.index for c in cues], [1, 2, 3, 4])
        self.assertEqual(cues[2].start_ms, 4000)
        self.assertEqual(cues[3].end_ms, 8000)

    def test_mismatched_offsets_raises(self) -> None:
        with self.assertRaises(SegmentError):
            merge_srts_with_offsets(["a"], [0, 1000])

    def test_empty_segments_are_dropped(self) -> None:
        merged = merge_srts_with_offsets(["", "1\n00:00:00,000 --> 00:00:01,000\nX\n\n"], [0, 5000])
        cues = parse_srt_cues(merged)
        self.assertEqual(len(cues), 1)
        self.assertEqual(cues[0].start_ms, 5000)


class MergeFinalSubtitleIntegrationTest(unittest.TestCase):
    """Exercise merge_segment_final_subtitles using fake per-segment workspaces."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase4_merge_"))
        self.parent = self.root / "parent"
        (self.parent / "segments").mkdir(parents=True)
        self.seg_dirs: list[Path] = []
        for i in range(3):
            seg_dir = self.parent / "segments" / f"seg_{i:03d}"
            (seg_dir / "artifacts" / "translate").mkdir(parents=True)
            (seg_dir / "input").mkdir(parents=True)
            (seg_dir / "artifacts" / "translate" / "final_subtitle.srt").write_text(
                f"1\n00:00:00,000 --> 00:00:02,000\nS{i}_1\n\n"
                f"2\n00:00:02,000 --> 00:00:04,000\nS{i}_2\n\n",
                encoding="utf-8",
            )
            self.seg_dirs.append(seg_dir)

        manifest = {
            "version": 1,
            "source_video": str(self.parent / "input" / "source.mp4"),
            "source_duration_s": 12.0,
            "segments": [
                {
                    "index": i,
                    "start_s": float(i * 4),
                    "end_s": float((i + 1) * 4),
                    "workspace": str(self.seg_dirs[i]),
                    "video": str(self.seg_dirs[i] / "input" / "source.mp4"),
                }
                for i in range(3)
            ],
        }
        (self.parent / "segments" / "manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_merge_final_subtitles_shifts_and_writes_parent(self) -> None:
        out = merge_segment_final_subtitles(self.parent)
        self.assertEqual(out, self.parent / "artifacts" / "translate" / "final_subtitle.srt")
        cues = parse_srt_cues(out.read_text(encoding="utf-8"))
        self.assertEqual(len(cues), 6)
        self.assertEqual([c.index for c in cues], [1, 2, 3, 4, 5, 6])
        self.assertEqual(cues[2].start_ms, 4000)  # seg_001 first cue offset=4000
        self.assertEqual(cues[4].start_ms, 8000)  # seg_002 first cue offset=8000
        self.assertEqual(cues[-1].end_ms, 12_000)

    def test_merge_raises_if_segment_missing_srt(self) -> None:
        (self.seg_dirs[1] / "artifacts" / "translate" / "final_subtitle.srt").unlink()
        with self.assertRaises(SegmentError):
            merge_segment_final_subtitles(self.parent)

    def test_load_manifest_round_trip(self) -> None:
        manifest = load_segment_manifest(self.parent)
        self.assertEqual(len(manifest.segments), 3)
        self.assertEqual(manifest.source_duration_s, 12.0)


if __name__ == "__main__":
    unittest.main()
