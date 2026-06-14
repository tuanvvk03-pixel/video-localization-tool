"""Phase F1.1 — distribute shared project branding to each video workspace."""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from engine import project_branding as pb
from engine import render_settings as rs


class ProjectBrandingTest(unittest.TestCase):
    def test_no_branding_returns_none(self) -> None:
        with TemporaryDirectory() as d:
            pr = Path(d) / "proj"
            (pr).mkdir()
            vw = Path(d) / "vid"
            vw.mkdir()
            self.assertFalse(pb.has_project_branding(pr))
            self.assertIsNone(pb.apply_branding_to_video(pr, vw))

    def test_logo_and_trim_copied_to_video(self) -> None:
        with TemporaryDirectory() as d:
            pr = Path(d) / "proj"
            pr.mkdir()
            vw = Path(d) / "vid"
            vw.mkdir()
            # Author branding at project level (logo file + trim).
            logo_src = Path(d) / "brand.png"
            logo_src.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
            rs.import_render_logo_image(pr, logo_src)
            rs.update_render_settings(pr, {"aspect_ratio": "9:16", "tail_trim_sec": 2.0})
            self.assertTrue(pb.has_project_branding(pr))

            applied = pb.apply_branding_to_video(pr, vw)
            self.assertIsNotNone(applied)
            # Logo file copied into the video workspace at the same rel path.
            rel = applied["logo_path"]
            self.assertTrue((vw / rel).is_file())
            # Render settings written to the video workspace.
            vs = rs.load_render_settings(vw)
            self.assertIn("logo_path", vs)
            self.assertEqual(vs["aspect_ratio"], "9:16")
            self.assertEqual(vs["tail_trim_sec"], 2.0)

    def test_missing_file_reference_is_dropped(self) -> None:
        with TemporaryDirectory() as d:
            pr = Path(d) / "proj"
            pr.mkdir()
            vw = Path(d) / "vid"
            vw.mkdir()
            # Settings reference a logo that doesn't exist on disk.
            rs.save_render_settings(pr, {"aspect_ratio": "source", "logo_path": "assets/render_logo/ghost.png"})
            applied = pb.apply_branding_to_video(pr, vw)
            # has_project_branding/load drops the dangling logo, so nothing to apply.
            self.assertTrue(applied is None or "logo_path" not in applied)
            self.assertFalse((vw / "assets" / "render_logo" / "ghost.png").exists())


if __name__ == "__main__":
    unittest.main()
