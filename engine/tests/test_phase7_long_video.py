"""Phase 7: long-video orchestrator + new segment edit-voice helpers.

Covers pure logic (merge/distribute of edited_voice) and the run_long_video_stage
orchestrator using an injected stub run_job.main so no ffmpeg/translate/TTS is
required.
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

from engine import run_long_video_stage
from engine.segment_manager import (
    SegmentError,
    distribute_edited_voice_to_segments,
    merge_segment_edited_voices,
    seed_segment_edited_voices,
)
from engine.srt_cues import parse_srt_cues
from engine.voice_edit_api import mark_voice_edited


def _fake_parent(tmp: Path, *, seg_count: int = 3, seg_len_s: float = 4.0) -> tuple[Path, list[Path]]:
    parent = tmp / "parent"
    (parent / "segments").mkdir(parents=True)
    seg_dirs: list[Path] = []
    for i in range(seg_count):
        sd = parent / "segments" / f"seg_{i:03d}"
        (sd / "artifacts" / "translate").mkdir(parents=True)
        (sd / "artifacts" / "edit").mkdir(parents=True)
        (sd / "input").mkdir(parents=True)
        seg_dirs.append(sd)
    manifest = {
        "version": 1,
        "source_video": str(parent / "input" / "source.mp4"),
        "source_duration_s": seg_count * seg_len_s,
        "segments": [
            {
                "index": i,
                "start_s": i * seg_len_s,
                "end_s": (i + 1) * seg_len_s,
                "workspace": str(seg_dirs[i]),
                "video": str(seg_dirs[i] / "input" / "source.mp4"),
            }
            for i in range(seg_count)
        ],
    }
    (parent / "segments" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return parent, seg_dirs


class SeedSegmentEditedVoicesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="phase7_seed_"))
        self.parent, self.seg_dirs = _fake_parent(self.tmp, seg_count=2)
        for i, sd in enumerate(self.seg_dirs):
            (sd / "artifacts" / "translate" / "translated_voice.srt").write_text(
                f"1\n00:00:00,000 --> 00:00:02,000\nseg{i}_voice\n\n",
                encoding="utf-8",
            )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_seeds_each_segment(self) -> None:
        outs = seed_segment_edited_voices(self.parent)
        self.assertEqual(len(outs), 2)
        for sd in self.seg_dirs:
            edited = sd / "artifacts" / "edit" / "edited_voice.srt"
            self.assertTrue(edited.is_file())
            self.assertIn("_voice", edited.read_text(encoding="utf-8"))


class MergeSegmentEditedVoicesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="phase7_merge_edit_"))
        self.parent, self.seg_dirs = _fake_parent(self.tmp, seg_count=3, seg_len_s=4.0)
        for i, sd in enumerate(self.seg_dirs):
            (sd / "artifacts" / "edit" / "edited_voice.srt").write_text(
                f"1\n00:00:00,000 --> 00:00:02,000\nE{i}_1\n\n"
                f"2\n00:00:02,000 --> 00:00:04,000\nE{i}_2\n\n",
                encoding="utf-8",
            )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_merge_shifts_and_writes_parent(self) -> None:
        out = merge_segment_edited_voices(self.parent)
        self.assertEqual(out, self.parent / "artifacts" / "edit" / "edited_voice.srt")
        cues = parse_srt_cues(out.read_text(encoding="utf-8"))
        self.assertEqual(len(cues), 6)
        self.assertEqual(cues[0].start_ms, 0)
        self.assertEqual(cues[2].start_ms, 4000)
        self.assertEqual(cues[4].start_ms, 8000)
        self.assertEqual(cues[-1].end_ms, 12_000)

    def test_merge_falls_back_to_translated_voice(self) -> None:
        (self.seg_dirs[1] / "artifacts" / "edit" / "edited_voice.srt").unlink()
        (self.seg_dirs[1] / "artifacts" / "translate" / "translated_voice.srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nFallback1\n\n",
            encoding="utf-8",
        )
        out = merge_segment_edited_voices(self.parent)
        cues = parse_srt_cues(out.read_text(encoding="utf-8"))
        texts = [c.text for c in cues]
        self.assertIn("Fallback1", texts)

    def test_merge_raises_when_both_missing(self) -> None:
        (self.seg_dirs[1] / "artifacts" / "edit" / "edited_voice.srt").unlink()
        with self.assertRaises(SegmentError):
            merge_segment_edited_voices(self.parent)


class DistributeEditedVoiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="phase7_dist_"))
        self.parent, self.seg_dirs = _fake_parent(self.tmp, seg_count=3, seg_len_s=4.0)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_slices_cues_into_right_segments(self) -> None:
        parent_srt = (
            "1\n00:00:00,500 --> 00:00:02,000\nEarly seg0\n\n"
            "2\n00:00:05,000 --> 00:00:06,500\nMid seg1\n\n"
            "3\n00:00:09,000 --> 00:00:11,000\nLate seg2\n\n"
        )
        outs = distribute_edited_voice_to_segments(self.parent, parent_srt_text=parent_srt)
        self.assertEqual(len(outs), 3)
        seg0 = parse_srt_cues(outs[0].read_text(encoding="utf-8"))
        seg1 = parse_srt_cues(outs[1].read_text(encoding="utf-8"))
        seg2 = parse_srt_cues(outs[2].read_text(encoding="utf-8"))
        self.assertEqual([c.text for c in seg0], ["Early seg0"])
        self.assertEqual([c.text for c in seg1], ["Mid seg1"])
        self.assertEqual([c.text for c in seg2], ["Late seg2"])
        # Shifted to seg-relative times.
        self.assertEqual(seg0[0].start_ms, 500)
        self.assertEqual(seg1[0].start_ms, 1000)  # 5000 - 4000
        self.assertEqual(seg2[0].start_ms, 1000)  # 9000 - 8000

    def test_cue_spanning_boundary_clamped(self) -> None:
        # Cue starts in seg0 (t=3s) but ends beyond seg0 (into seg1). Clamp end to seg0 duration.
        parent_srt = "1\n00:00:03,000 --> 00:00:05,500\nSpan\n\n"
        distribute_edited_voice_to_segments(self.parent, parent_srt_text=parent_srt)
        seg0 = parse_srt_cues((self.seg_dirs[0] / "artifacts" / "edit" / "edited_voice.srt").read_text("utf-8"))
        seg1 = parse_srt_cues((self.seg_dirs[1] / "artifacts" / "edit" / "edited_voice.srt").read_text("utf-8"))
        self.assertEqual(len(seg0), 1)
        self.assertEqual(seg0[0].end_ms, 4000)  # clamped to seg0 end
        self.assertEqual(len(seg1), 0)

    def test_empty_input_writes_empty_files(self) -> None:
        distribute_edited_voice_to_segments(self.parent, parent_srt_text="")
        for sd in self.seg_dirs:
            body = (sd / "artifacts" / "edit" / "edited_voice.srt").read_text(encoding="utf-8")
            self.assertEqual(parse_srt_cues(body), [])


class OrchestratorUntilEditTest(unittest.TestCase):
    """Run do_until_edit with a stub runner that fakes run_job success."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="phase7_orch_"))
        self.parent, self.seg_dirs = _fake_parent(self.tmp, seg_count=3, seg_len_s=4.0)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _fake_run_job(self, argv: list[str]) -> int:
        # Expect --job-workspace <path> --to-stage translated.
        jw = Path(argv[argv.index("--job-workspace") + 1])
        (jw / "artifacts" / "translate").mkdir(parents=True, exist_ok=True)
        (jw / "artifacts" / "translate" / "translated_voice.srt").write_text(
            f"1\n00:00:00,000 --> 00:00:02,000\ntv_{jw.name}\n\n",
            encoding="utf-8",
        )
        return 0

    def test_parallel_translate_then_merge(self) -> None:
        result = run_long_video_stage.do_until_edit(
            self.parent,
            cfg={"project_name": "p", "translate_backend": "block_v2"},
            max_workers=2,
            runner=self._fake_run_job,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["segment_count"], 3)
        parent_srt = Path(result["parent_edited_voice_srt"])
        self.assertTrue(parent_srt.is_file())
        cues = parse_srt_cues(parent_srt.read_text(encoding="utf-8"))
        self.assertEqual(len(cues), 3)
        self.assertEqual(cues[0].start_ms, 0)
        self.assertEqual(cues[1].start_ms, 4000)
        self.assertEqual(cues[2].start_ms, 8000)
        # Each seg has its own seeded edited_voice.srt.
        for sd in self.seg_dirs:
            self.assertTrue((sd / "artifacts" / "edit" / "edited_voice.srt").is_file())

    def test_translate_failure_propagates(self) -> None:
        def bad_runner(argv: list[str]) -> int:
            return 7

        result = run_long_video_stage.do_until_edit(
            self.parent,
            cfg={"project_name": "p"},
            runner=bad_runner,
        )
        self.assertFalse(result["ok"])
        self.assertTrue(all(not r["ok"] for r in result["results"]))


class OrchestratorAfterEditTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="phase7_after_"))
        self.parent, self.seg_dirs = _fake_parent(self.tmp, seg_count=2, seg_len_s=4.0)
        # Parent-level edited_voice.srt ready for distribution.
        (self.parent / "artifacts" / "edit").mkdir(parents=True, exist_ok=True)
        (self.parent / "artifacts" / "edit" / "edited_voice.srt").write_text(
            "1\n00:00:01,000 --> 00:00:02,000\nA\n\n"
            "2\n00:00:05,000 --> 00:00:06,000\nB\n\n",
            encoding="utf-8",
        )
        # Seed per-seg translated_voice so mark_voice_edited has something.
        for sd in self.seg_dirs:
            (sd / "artifacts" / "translate" / "translated_voice.srt").write_text(
                "1\n00:00:00,000 --> 00:00:01,000\nx\n\n", encoding="utf-8"
            )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_distributes_and_runs_without_merge(self) -> None:
        calls: list[str] = []
        mark_voice_edited(self.parent)

        def fake_runner(argv: list[str]) -> int:
            jw = Path(argv[argv.index("--job-workspace") + 1])
            calls.append(jw.name)
            (jw / "artifacts" / "render").mkdir(parents=True, exist_ok=True)
            (jw / "artifacts" / "render" / "final.mp4").write_bytes(b"")
            return 0

        result = run_long_video_stage.do_after_edit(
            self.parent,
            cfg={"project_name": "p"},
            to_stage="rendered",
            runner=fake_runner,
            merge_render=False,  # skip ffmpeg concat in unit test
        )
        self.assertTrue(result["ok"], msg=result)
        self.assertEqual(sorted(calls), ["seg_000", "seg_001"])
        self.assertIsNone(result["merged_render_path"])
        # Distribution wrote per-seg edited_voice files.
        seg0 = parse_srt_cues((self.seg_dirs[0] / "artifacts" / "edit" / "edited_voice.srt").read_text("utf-8"))
        seg1 = parse_srt_cues((self.seg_dirs[1] / "artifacts" / "edit" / "edited_voice.srt").read_text("utf-8"))
        self.assertEqual([c.text for c in seg0], ["A"])
        self.assertEqual([c.text for c in seg1], ["B"])

    def test_requires_parent_voice_edit_completion(self) -> None:
        with self.assertRaises(run_long_video_stage.LongVideoError):
            run_long_video_stage.do_after_edit(
                self.parent,
                cfg={"project_name": "p"},
                to_stage="mixed",
                runner=lambda _argv: 0,
                merge_render=False,
            )


if __name__ == "__main__":
    unittest.main()
