"""Phase G — 1:1 aspect + batch export collection."""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from engine import project_manager as pm
from engine.project_export import export_project_renders, _mp4_has_moov
from engine.run_render_stage import _target_dimensions

# Minimal but valid box layout: ftyp (16 bytes) + empty moov (8 bytes).
_VALID_MP4 = b"\x00\x00\x00\x10ftypisom\x00\x00\x00\x00" + b"\x00\x00\x00\x08moov"


class AspectAndExportTest(unittest.TestCase):
    def test_square_target_dimensions(self) -> None:
        # 1920x1080 -> square uses the short side (1080x1080).
        self.assertEqual(_target_dimensions(1920, 1080, "1:1"), (1080, 1080))
        self.assertEqual(_target_dimensions(720, 1280, "1:1"), (720, 720))

    def _make_project(self, root: Path) -> str:
        state = pm.init_project(root, "UA Proj")
        pr = Path(state.project_root)
        for vid in ("vid_a", "vid_b", "vid_c"):
            ws = pr / vid
            (ws / "artifacts" / "render").mkdir(parents=True, exist_ok=True)
            state.videos.append(pm.ProjectVideoEntry(
                video_id=vid, workspace=str(ws), added_at_unix=0.0, source_path=str(ws / "in.mp4"), duration_s=10.0,
            ))
        pm._write_state(state)
        # Only a and c are rendered (valid moov-complete mp4).
        for vid in ("vid_a", "vid_c"):
            (pr / vid / "artifacts" / "render" / "final.mp4").write_bytes(_VALID_MP4)
        return state.project_root

    def test_export_collects_rendered_only(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            pr = self._make_project(root)
            result = export_project_renders(pr)
            self.assertEqual(len(result["exported"]), 2)
            self.assertEqual(sorted(result["skipped"]), ["vid_b"])
            names = sorted(Path(p["path"]).name for p in result["exported"])
            self.assertEqual(names, ["UA-Proj_vid_a.mp4", "UA-Proj_vid_c.mp4"])
            for p in result["exported"]:
                self.assertTrue(Path(p["path"]).is_file())

    def test_mp4_moov_guard(self) -> None:
        with TemporaryDirectory() as d:
            good = Path(d) / "good.mp4"
            good.write_bytes(_VALID_MP4)
            self.assertTrue(_mp4_has_moov(good))
            # Truncated / mid-flush render (ftyp only, no moov) is rejected.
            bad = Path(d) / "bad.mp4"
            bad.write_bytes(b"\x00\x00\x00\x10ftypisom\x00\x00\x00\x00")
            self.assertFalse(_mp4_has_moov(bad))
            self.assertFalse(_mp4_has_moov(Path(d) / "missing.mp4"))

    def test_export_skips_incomplete_render(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            state = pm.init_project(root, "P")
            pr = Path(state.project_root)
            ws = pr / "v1"
            (ws / "artifacts" / "render").mkdir(parents=True)
            # A render still flushing (no moov) must be skipped, not exported corrupt.
            (ws / "artifacts" / "render" / "final.mp4").write_bytes(b"\x00\x00\x00\x10ftypisom\x00\x00\x00\x00")
            state.videos.append(pm.ProjectVideoEntry(video_id="v1", workspace=str(ws), added_at_unix=0.0, source_path="x", duration_s=5.0))
            pm._write_state(state)
            from engine import project_export
            with mock.patch.object(project_export, "_wait_ready", return_value=False):
                result = export_project_renders(pr)
            self.assertEqual(result["exported"], [])
            self.assertEqual(result["skipped"], ["v1"])

    def test_export_custom_dest(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            pr = self._make_project(root)
            dest = root / "out"
            result = export_project_renders(pr, dest=dest)
            self.assertEqual(Path(result["export_dir"]), dest.resolve())
            self.assertTrue((dest / "UA-Proj_vid_a.mp4").is_file())


if __name__ == "__main__":
    unittest.main()
