"""Phase F2 — bulk auto pipeline (project_manager.run_auto_phase).

Verifies the orchestration: translate -> auto-approve only the videos that
translated OK -> render just those. The heavy per-video pipeline (run_job) and
the individual phases are already covered elsewhere, so here we mock the phase
boundaries and assert the composition.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from engine import project_manager as pm


def _state_with(video_ids):
    videos = [SimpleNamespace(video_id=v, workspace=f"/ws/{v}") for v in video_ids]
    return SimpleNamespace(videos=videos, project_root="/proj")


class RunAutoPhaseTest(unittest.TestCase):
    def test_only_translated_ok_videos_are_approved_and_rendered(self) -> None:
        t_results = [
            {"video_id": "v1", "ok": True},
            {"video_id": "v2", "ok": False, "error": "boom"},
            {"video_id": "v3", "ok": True},
        ]
        marked: list[str] = []

        def fake_mark(jw):
            marked.append(Path(jw).name)

        edited_status = SimpleNamespace(edited_voice_path="x", voice_edited=False, voice_edit_status="voice_edit_pending")

        with (
            mock.patch.object(pm, "run_translate_phase", return_value=t_results) as rt,
            mock.patch.object(pm, "run_render_phase", return_value=[{"video_id": "v1", "ok": True}, {"video_id": "v3", "ok": True}]) as rr,
            mock.patch.object(pm, "load_project", return_value=_state_with(["v1", "v2", "v3"])),
            mock.patch.object(pm, "get_voice_edit_status", return_value=edited_status),
            mock.patch.object(pm, "_voice_edit_completed", return_value=False),
            mock.patch.object(pm, "mark_voice_edited", side_effect=fake_mark),
        ):
            out = pm.run_auto_phase(Path("/proj"), to_stage="rendered")

        self.assertTrue(rt.called)
        # Only v1 and v3 (translate ok) were approved + marked.
        self.assertEqual(out["approved"], ["v1", "v3"])
        self.assertEqual(sorted(marked), ["v1", "v3"])
        # render_phase received exactly the approved ids.
        _, kwargs = rr.call_args
        self.assertEqual(kwargs["video_ids"], ["v1", "v3"])
        self.assertEqual(kwargs["to_stage"], "rendered")

    def test_already_completed_video_is_approved_without_remark(self) -> None:
        with (
            mock.patch.object(pm, "run_translate_phase", return_value=[{"video_id": "v1", "ok": True}]),
            mock.patch.object(pm, "run_render_phase", return_value=[]) as rr,
            mock.patch.object(pm, "load_project", return_value=_state_with(["v1"])),
            mock.patch.object(pm, "get_voice_edit_status", return_value=SimpleNamespace(edited_voice_path="x")),
            mock.patch.object(pm, "_voice_edit_completed", return_value=True),
            mock.patch.object(pm, "mark_voice_edited", side_effect=AssertionError("should not re-mark")),
        ):
            out = pm.run_auto_phase(Path("/proj"))
        self.assertEqual(out["approved"], ["v1"])
        self.assertEqual(rr.call_args.kwargs["video_ids"], ["v1"])

    def test_approve_error_is_collected_not_raised(self) -> None:
        with (
            mock.patch.object(pm, "run_translate_phase", return_value=[{"video_id": "v1", "ok": True}]),
            mock.patch.object(pm, "run_render_phase", return_value=[]),
            mock.patch.object(pm, "load_project", return_value=_state_with(["v1"])),
            mock.patch.object(pm, "get_voice_edit_status", return_value=SimpleNamespace(edited_voice_path="x")),
            mock.patch.object(pm, "_voice_edit_completed", return_value=False),
            mock.patch.object(pm, "mark_voice_edited", side_effect=pm.VoiceEditError("nope")),
        ):
            out = pm.run_auto_phase(Path("/proj"))
        self.assertEqual(out["approved"], [])
        self.assertEqual(len(out["approve_errors"]), 1)
        self.assertEqual(out["approve_errors"][0]["video_id"], "v1")


if __name__ == "__main__":
    unittest.main()
