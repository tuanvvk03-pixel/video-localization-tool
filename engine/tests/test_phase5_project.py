"""Phase 5 acceptance: multi-video project + concurrency (≤ 5 workers)."""
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
    ProjectConfig,
    ProjectError,
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


def _write_sample_voice(jw: Path) -> None:
    (jw / "artifacts" / "translate").mkdir(parents=True, exist_ok=True)
    (jw / "artifacts" / "translate" / "translated_voice.srt").write_text(
        SAMPLE_VOICE_SRT, encoding="utf-8"
    )


class ProjectConfigTest(unittest.TestCase):
    def test_resolve_merges_override_onto_global(self) -> None:
        cfg = ProjectConfig(
            project_name="demo",
            tts_voice="vi-VN-HoaiMyNeural",
            per_video_overrides={"clipA": {"tts_voice": "vi-VN-NamMinh"}},
        )
        self.assertEqual(cfg.resolve_for("clipA")["tts_voice"], "vi-VN-NamMinh")
        self.assertEqual(cfg.resolve_for("clipB")["tts_voice"], "vi-VN-HoaiMyNeural")

    def test_resolve_ignores_unknown_override_keys(self) -> None:
        cfg = ProjectConfig(
            project_name="demo",
            per_video_overrides={"clipA": {"not_a_field": "x", "tts_voice": "vi"}},
        )
        resolved = cfg.resolve_for("clipA")
        self.assertNotIn("not_a_field", resolved)
        self.assertEqual(resolved["tts_voice"], "vi")


class ProjectLifecycleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase5_project_"))
        self.projects_root = self.root / "projects"
        self.projects_root.mkdir()
        self.video = self.root / "clip.mp4"
        self.video.write_bytes(b"x")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_init_project_writes_state_and_rejects_existing(self) -> None:
        state = init_project(self.projects_root, "demo project")
        self.assertTrue(Path(state.project_root).is_dir())
        self.assertTrue((Path(state.project_root) / "project_state.json").is_file())
        with self.assertRaises(ProjectError):
            init_project(self.projects_root, "demo project")
        reloaded = load_project(Path(state.project_root))
        self.assertEqual(reloaded.project_id, state.project_id)

    def test_add_video_enforces_optional_duration_cap(self) -> None:
        state = init_project(self.projects_root, "demo")
        with self.assertRaises(ProjectError) as ctx:
            add_video(
                Path(state.project_root),
                self.video,
                duration_probe=lambda _p: 6 * 60.0,
                max_duration_s=5 * 60.0,
            )
        self.assertIn("exceeds cap", str(ctx.exception))

    def test_add_video_accepts_short_clip_and_persists(self) -> None:
        state = init_project(self.projects_root, "demo")
        entry = add_video(
            Path(state.project_root),
            self.video,
            duration_probe=lambda _p: 180.0,
        )
        self.assertEqual(entry.duration_s, 180.0)
        self.assertTrue((Path(entry.workspace) / "input" / "source.mp4").is_file())
        reloaded = load_project(Path(state.project_root))
        self.assertEqual(len(reloaded.videos), 1)
        self.assertEqual(reloaded.videos[0].video_id, entry.video_id)

    def test_add_video_rejects_duplicate_id_without_force(self) -> None:
        state = init_project(self.projects_root, "demo")
        add_video(
            Path(state.project_root),
            self.video,
            video_id="clipA",
            duration_probe=lambda _p: 180.0,
        )
        with self.assertRaises(ProjectError):
            add_video(
                Path(state.project_root),
                self.video,
                video_id="clipA",
                duration_probe=lambda _p: 180.0,
            )

    def test_list_video_statuses_reflects_edit_gate(self) -> None:
        state = init_project(self.projects_root, "demo")
        entry = add_video(
            Path(state.project_root),
            self.video,
            video_id="clipA",
            duration_probe=lambda _p: 180.0,
        )
        _write_sample_voice(Path(entry.workspace))
        snapshots = list_video_statuses(Path(state.project_root))
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0]["voice_edit_status"], "not_started")
        self.assertFalse(snapshots[0]["voice_edited"])


class ConcurrencyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase5_concurrency_"))
        self.projects_root = self.root / "projects"
        self.projects_root.mkdir()
        self.state = init_project(self.projects_root, "demo")
        self.video = self.root / "clip.mp4"
        self.video.write_bytes(b"x")
        self.videos: list = []
        for i in range(7):
            entry = add_video(
                Path(self.state.project_root),
                self.video,
                video_id=f"clip{i:02d}",
                duration_probe=lambda _p: 120.0,
            )
            self.videos.append(entry)
            _write_sample_voice(Path(entry.workspace))

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_run_translate_phase_respects_max_parallel(self) -> None:
        active = 0
        peak = 0
        lock = threading.Lock()

        def fake_runner(argv: list[str]) -> int:
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            time.sleep(0.05)
            with lock:
                active -= 1
            return 0

        results = run_translate_phase(
            Path(self.state.project_root),
            runner=fake_runner,
        )
        self.assertEqual(len(results), 7)
        self.assertTrue(all(r["ok"] for r in results), msg=results)
        self.assertLessEqual(peak, MAX_PARALLEL_VIDEOS)
        # All videos seeded -> edited_voice.srt present.
        for v in self.videos:
            self.assertTrue(
                (Path(v.workspace) / "artifacts" / "edit" / "edited_voice.srt").is_file()
            )

    def test_run_translate_phase_caps_user_max_workers(self) -> None:
        active = 0
        peak = 0
        lock = threading.Lock()

        def fake_runner(argv: list[str]) -> int:
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            time.sleep(0.05)
            with lock:
                active -= 1
            return 0

        run_translate_phase(
            Path(self.state.project_root),
            runner=fake_runner,
            max_workers=20,
        )
        self.assertLessEqual(peak, MAX_PARALLEL_VIDEOS)

    def test_run_translate_phase_reports_missing_translated_voice(self) -> None:
        # Remove translated_voice.srt from one video to simulate legacy backend output.
        missing_path = (
            Path(self.videos[0].workspace) / "artifacts" / "translate" / "translated_voice.srt"
        )
        missing_path.unlink()

        def fake_runner(_argv: list[str]) -> int:
            return 0

        results = run_translate_phase(
            Path(self.state.project_root),
            runner=fake_runner,
        )
        by_id = {r["video_id"]: r for r in results}
        self.assertFalse(by_id[self.videos[0].video_id]["ok"])
        self.assertIn("translated_voice.srt missing", by_id[self.videos[0].video_id]["error"])
        self.assertTrue(all(by_id[v.video_id]["ok"] for v in self.videos[1:]))

    def test_run_render_phase_skips_videos_without_completed_voice_edit(self) -> None:
        # Seed edited_voice.srt only for half, but do not mark completion yet.
        edited_ids = [v.video_id for v in self.videos[:3]]
        for v in self.videos[:3]:
            edit_dir = Path(v.workspace) / "artifacts" / "edit"
            edit_dir.mkdir(parents=True, exist_ok=True)
            (edit_dir / "edited_voice.srt").write_text(SAMPLE_VOICE_SRT, encoding="utf-8")

        invoked: list[str] = []

        def fake_runner(argv: list[str]) -> int:
            idx = argv.index("--job-workspace") + 1
            invoked.append(argv[idx])
            return 0

        results = run_render_phase(
            Path(self.state.project_root),
            runner=fake_runner,
        )
        by_id = {r["video_id"]: r for r in results}
        for vid in edited_ids:
            self.assertFalse(by_id[vid]["ok"])
            self.assertTrue(by_id[vid].get("skipped"))
            self.assertEqual(by_id[vid].get("required_action"), "edit_edited_voice_srt")
        for v in self.videos[3:]:
            self.assertFalse(by_id[v.video_id]["ok"])
            self.assertTrue(by_id[v.video_id].get("skipped"))
        self.assertEqual(len(invoked), 0)

    def test_run_render_phase_runs_only_completed_voice_edit(self) -> None:
        edited_ids = [v.video_id for v in self.videos[:3]]
        for v in self.videos[:3]:
            edit_dir = Path(v.workspace) / "artifacts" / "edit"
            edit_dir.mkdir(parents=True, exist_ok=True)
            (edit_dir / "edited_voice.srt").write_text(SAMPLE_VOICE_SRT, encoding="utf-8")
            mark_voice_edited(Path(v.workspace))

        invoked: list[str] = []

        def fake_runner(argv: list[str]) -> int:
            idx = argv.index("--job-workspace") + 1
            invoked.append(argv[idx])
            return 0

        results = run_render_phase(
            Path(self.state.project_root),
            runner=fake_runner,
        )
        by_id = {r["video_id"]: r for r in results}
        for vid in edited_ids:
            self.assertTrue(by_id[vid]["ok"], msg=by_id[vid])
        for v in self.videos[3:]:
            self.assertFalse(by_id[v.video_id]["ok"])
            self.assertTrue(by_id[v.video_id].get("skipped"))
        self.assertEqual(len(invoked), len(edited_ids))

    def test_per_video_override_reaches_runner_argv(self) -> None:
        state = load_project(Path(self.state.project_root))
        state.config.per_video_overrides[self.videos[0].video_id] = {
            "tts_voice": "vi-VN-NamMinh"
        }
        project_manager._write_state(state)

        captured: dict[str, list[str]] = {}

        def fake_runner(argv: list[str]) -> int:
            idx = argv.index("--job-workspace") + 1
            captured[argv[idx]] = list(argv)
            return 0

        run_translate_phase(
            Path(self.state.project_root),
            runner=fake_runner,
            video_ids=[self.videos[0].video_id, self.videos[1].video_id],
        )
        argv_a = captured[self.videos[0].workspace]
        argv_b = captured[self.videos[1].workspace]
        self.assertIn("--tts-voice", argv_a)
        self.assertEqual(argv_a[argv_a.index("--tts-voice") + 1], "vi-VN-NamMinh")
        self.assertNotIn("--tts-voice", argv_b)


if __name__ == "__main__":
    unittest.main()
