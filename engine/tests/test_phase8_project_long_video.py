"""Phase 8: multi-video projects integrate the long-video orchestrator.

Long videos (duration > SINGLE_VIDEO_THRESHOLD_S) are accepted by add_video and
routed through run_long_video_stage during translate/render phases. ffmpeg/ffprobe
are avoided by pre-seeding segments/manifest.json so do_plan_split reuses it.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import project_manager
from engine.project_manager import (
    MAX_PARALLEL_VIDEOS,
    add_video,
    init_project,
    list_video_statuses,
    load_project,
    run_render_phase,
    run_translate_phase,
)
from engine.voice_edit_api import mark_voice_edited


SAMPLE_VOICE_SRT = (
    "1\n00:00:00,000 --> 00:00:02,000\nXin chao\n\n"
    "2\n00:00:02,000 --> 00:00:04,000\nCau hai\n\n"
)


def _seed_segments(jw: Path, *, seg_count: int, seg_len_s: float = 240.0) -> list[Path]:
    segments_root = jw / "segments"
    segments_root.mkdir(parents=True, exist_ok=True)
    seg_dirs: list[Path] = []
    entries = []
    for i in range(seg_count):
        sd = segments_root / f"seg_{i:03d}"
        (sd / "input").mkdir(parents=True, exist_ok=True)
        (sd / "artifacts" / "translate").mkdir(parents=True, exist_ok=True)
        (sd / "artifacts" / "edit").mkdir(parents=True, exist_ok=True)
        (sd / "input" / "source.mp4").write_bytes(b"x")
        seg_dirs.append(sd)
        entries.append({
            "index": i,
            "start_s": i * seg_len_s,
            "end_s": (i + 1) * seg_len_s,
            "workspace": str(sd.resolve()),
            "video": str((sd / "input" / "source.mp4").resolve()),
        })
    manifest = {
        "version": 1,
        "source_video": str((jw / "input" / "source.mp4").resolve()),
        "source_duration_s": seg_count * seg_len_s,
        "segments": entries,
    }
    (segments_root / "manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    return seg_dirs


class AddLongVideoTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase8_add_"))
        self.projects_root = self.root / "projects"
        self.projects_root.mkdir()
        self.video = self.root / "long.mp4"
        self.video.write_bytes(b"x")
        self.state = init_project(self.projects_root, "demo")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_add_long_video_flags_is_long(self) -> None:
        entry = add_video(
            Path(self.state.project_root),
            self.video,
            duration_probe=lambda _p: 600.0,  # 10 min
        )
        self.assertTrue(entry.is_long)
        self.assertEqual(entry.duration_s, 600.0)
        reloaded = load_project(Path(self.state.project_root))
        self.assertTrue(reloaded.videos[0].is_long)

    def test_add_short_video_keeps_is_long_false(self) -> None:
        entry = add_video(
            Path(self.state.project_root),
            self.video,
            duration_probe=lambda _p: 120.0,
        )
        self.assertFalse(entry.is_long)

    def test_max_duration_cap_still_enforced_when_set(self) -> None:
        with self.assertRaises(project_manager.ProjectError):
            add_video(
                Path(self.state.project_root),
                self.video,
                duration_probe=lambda _p: 600.0,
                max_duration_s=300.0,
            )


class LongVideoTranslatePhaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase8_translate_"))
        self.projects_root = self.root / "projects"
        self.projects_root.mkdir()
        self.video = self.root / "long.mp4"
        self.video.write_bytes(b"x")
        self.state = init_project(self.projects_root, "demo")
        self.short_entry = add_video(
            Path(self.state.project_root),
            self.video,
            video_id="short01",
            duration_probe=lambda _p: 120.0,
        )
        (Path(self.short_entry.workspace) / "artifacts" / "translate").mkdir(
            parents=True, exist_ok=True
        )
        (Path(self.short_entry.workspace) / "artifacts" / "translate" / "translated_voice.srt").write_text(
            SAMPLE_VOICE_SRT, encoding="utf-8"
        )
        self.long_entry = add_video(
            Path(self.state.project_root),
            self.video,
            video_id="long01",
            duration_probe=lambda _p: 720.0,  # 12 min
        )
        self.long_seg_dirs = _seed_segments(
            Path(self.long_entry.workspace), seg_count=3, seg_len_s=240.0
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_long_video_dispatches_to_orchestrator_and_merges_edit_srt(self) -> None:
        invoked: list[str] = []
        lock = threading.Lock()

        def fake_runner(argv: list[str]) -> int:
            jw_idx = argv.index("--job-workspace") + 1
            jw = Path(argv[jw_idx])
            with lock:
                invoked.append(str(jw))
            translate_dir = jw / "artifacts" / "translate"
            translate_dir.mkdir(parents=True, exist_ok=True)
            # Each segment writes its own translated_voice.srt.
            (translate_dir / "translated_voice.srt").write_text(
                SAMPLE_VOICE_SRT, encoding="utf-8"
            )
            return 0

        results = run_translate_phase(
            Path(self.state.project_root),
            runner=fake_runner,
        )
        by_id = {r["video_id"]: r for r in results}
        self.assertTrue(by_id["short01"]["ok"], msg=by_id["short01"])
        self.assertTrue(by_id["long01"]["ok"], msg=by_id["long01"])
        self.assertTrue(by_id["long01"].get("is_long"))
        self.assertEqual(by_id["long01"].get("segment_count"), 3)
        # Long video runner must be invoked once per segment, never on the parent jw.
        long_jw = self.long_entry.workspace
        self.assertNotIn(long_jw, invoked)
        for sd in self.long_seg_dirs:
            self.assertIn(str(sd), invoked)
        # Parent edited_voice.srt is merged from seg edits.
        merged = Path(self.long_entry.workspace) / "artifacts" / "edit" / "edited_voice.srt"
        self.assertTrue(merged.is_file())
        # Each segment's edited_voice.srt was seeded.
        for sd in self.long_seg_dirs:
            self.assertTrue((sd / "artifacts" / "edit" / "edited_voice.srt").is_file())

    def test_long_video_segment_failure_surfaces_error(self) -> None:
        def fake_runner(argv: list[str]) -> int:
            jw_idx = argv.index("--job-workspace") + 1
            jw = Path(argv[jw_idx])
            translate_dir = jw / "artifacts" / "translate"
            translate_dir.mkdir(parents=True, exist_ok=True)
            # Skip segment 1 to simulate failure (no translated_voice.srt).
            if jw.name == "seg_001":
                return 0
            (translate_dir / "translated_voice.srt").write_text(
                SAMPLE_VOICE_SRT, encoding="utf-8"
            )
            return 0

        results = run_translate_phase(
            Path(self.state.project_root),
            runner=fake_runner,
            video_ids=["long01"],
        )
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]["ok"])
        self.assertIn("translated_voice", results[0]["error"])


class LongVideoRenderPhaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase8_render_"))
        self.projects_root = self.root / "projects"
        self.projects_root.mkdir()
        self.video = self.root / "long.mp4"
        self.video.write_bytes(b"x")
        self.state = init_project(self.projects_root, "demo")
        self.long_entry = add_video(
            Path(self.state.project_root),
            self.video,
            video_id="long01",
            duration_probe=lambda _p: 720.0,
        )
        self.seg_dirs = _seed_segments(
            Path(self.long_entry.workspace), seg_count=3, seg_len_s=240.0
        )
        # Pre-seed parent edited_voice.srt as if user had edited.
        parent_edit_dir = Path(self.long_entry.workspace) / "artifacts" / "edit"
        parent_edit_dir.mkdir(parents=True, exist_ok=True)
        (parent_edit_dir / "edited_voice.srt").write_text(
            "1\n00:00:00,000 --> 00:00:02,000\nA\n\n"
            "2\n00:04:00,000 --> 00:04:02,000\nB\n\n"
            "3\n00:08:00,000 --> 00:08:02,000\nC\n\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_long_video_after_edit_dispatched_to_segments(self) -> None:
        invoked: list[str] = []
        lock = threading.Lock()
        mark_voice_edited(Path(self.long_entry.workspace))

        def fake_runner(argv: list[str]) -> int:
            jw_idx = argv.index("--job-workspace") + 1
            stage_idx = argv.index("--to-stage") + 1
            jw = Path(argv[jw_idx])
            stage = argv[stage_idx]
            with lock:
                invoked.append(f"{jw.name}:{stage}")
            return 0

        # Use to_stage='mixed' so do_after_edit skips the ffmpeg merge step.
        results = run_render_phase(
            Path(self.state.project_root),
            to_stage="mixed",
            runner=fake_runner,
            video_ids=["long01"],
        )
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["ok"], msg=results[0])
        self.assertTrue(results[0].get("is_long"))
        self.assertEqual(results[0].get("segment_count"), 3)
        self.assertIsNone(results[0].get("merged_render_path"))
        # Each segment received the edited slice and was invoked.
        for sd in self.seg_dirs:
            self.assertTrue((sd / "artifacts" / "edit" / "edited_voice.srt").is_file())
            self.assertIn(f"{sd.name}:mixed", invoked)

    def test_long_video_render_phase_skips_until_parent_voice_edit_completed(self) -> None:
        results = run_render_phase(
            Path(self.state.project_root),
            to_stage="mixed",
            runner=lambda _argv: 0,
            video_ids=["long01"],
        )
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]["ok"])
        self.assertTrue(results[0].get("skipped"))
        self.assertEqual(results[0].get("required_action"), "edit_edited_voice_srt")


class LongVideoConcurrencyCapTest(unittest.TestCase):
    """Multiple long videos in parallel must respect MAX_PARALLEL_VIDEOS * long_video_workers."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase8_concurrency_"))
        self.projects_root = self.root / "projects"
        self.projects_root.mkdir()
        self.video = self.root / "long.mp4"
        self.video.write_bytes(b"x")
        self.state = init_project(self.projects_root, "demo")
        self.entries = []
        for i in range(3):
            e = add_video(
                Path(self.state.project_root),
                self.video,
                video_id=f"long{i:02d}",
                duration_probe=lambda _p: 720.0,
            )
            self.entries.append(e)
            _seed_segments(Path(e.workspace), seg_count=3, seg_len_s=240.0)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_inner_workers_cap_caps_concurrent_segments_per_video(self) -> None:
        active_per_parent: dict[str, int] = {}
        peak_per_parent: dict[str, int] = {}
        lock = threading.Lock()

        def fake_runner(argv: list[str]) -> int:
            jw_idx = argv.index("--job-workspace") + 1
            jw = Path(argv[jw_idx])
            parent = jw.parent.parent.name  # seg_dir -> segments -> long_id
            with lock:
                active_per_parent[parent] = active_per_parent.get(parent, 0) + 1
                peak_per_parent[parent] = max(
                    peak_per_parent.get(parent, 0), active_per_parent[parent]
                )
            time.sleep(0.05)
            with lock:
                active_per_parent[parent] -= 1
            (jw / "artifacts" / "translate").mkdir(parents=True, exist_ok=True)
            (jw / "artifacts" / "translate" / "translated_voice.srt").write_text(
                SAMPLE_VOICE_SRT, encoding="utf-8"
            )
            return 0

        run_translate_phase(
            Path(self.state.project_root),
            runner=fake_runner,
            long_video_workers=2,
        )
        for parent, peak in peak_per_parent.items():
            self.assertLessEqual(peak, 2, msg=f"{parent} peak={peak}")


if __name__ == "__main__":
    unittest.main()
