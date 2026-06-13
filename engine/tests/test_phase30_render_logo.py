"""Phase E1 — brand logo / watermark overlay in the render stage.

Covers the render_settings logo schema (validate/import/load/clear) and the
ffmpeg filtergraph builder (overlay + opacity + position). The actual ffmpeg
render is verified manually; here we pin the logic that runs without ffmpeg.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from engine import render_settings as rs
from engine.run_render_stage import _build_layout_filter_complex, _logo_overlay_position


class LogoSettingsTest(unittest.TestCase):
    def test_normalize_includes_logo_with_defaults(self) -> None:
        out = rs.normalize_render_settings({"aspect_ratio": "source", "logo_path": "assets/render_logo/brand.png"})
        self.assertEqual(out["logo_path"], "assets/render_logo/brand.png")
        self.assertEqual(out["logo_position"], rs.DEFAULT_LOGO_POSITION)
        self.assertEqual(out["logo_scale"], rs.DEFAULT_LOGO_SCALE)
        self.assertEqual(out["logo_opacity"], rs.DEFAULT_LOGO_OPACITY)
        self.assertEqual(out["logo_margin"], rs.DEFAULT_LOGO_MARGIN)

    def test_normalize_no_logo_block_when_absent(self) -> None:
        out = rs.normalize_render_settings({"aspect_ratio": "9:16"})
        self.assertNotIn("logo_path", out)
        self.assertNotIn("logo_position", out)

    def test_rejects_bad_position(self) -> None:
        with self.assertRaises(rs.RenderSettingsError):
            rs.normalize_render_settings({"logo_path": "x.png", "logo_position": "centre"})

    def test_rejects_out_of_range_scale_and_opacity(self) -> None:
        with self.assertRaises(rs.RenderSettingsError):
            rs.normalize_render_settings({"logo_path": "x.png", "logo_scale": 2.0})
        with self.assertRaises(rs.RenderSettingsError):
            rs.normalize_render_settings({"logo_path": "x.png", "logo_opacity": 1.5})

    def test_import_and_clear_logo(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            src = jw / "brand.png"
            src.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)  # ext+size only are checked
            settings = rs.import_render_logo_image(jw, src)
            self.assertTrue(str(settings["logo_path"]).endswith("brand.png"))
            self.assertEqual(settings["logo_position"], rs.DEFAULT_LOGO_POSITION)
            self.assertTrue((jw / settings["logo_path"]).is_file())
            # load reflects it
            loaded = rs.load_render_settings(jw)
            self.assertIn("logo_path", loaded)
            # clear removes file + fields
            cleared = rs.clear_render_logo(jw)
            self.assertNotIn("logo_path", cleared)
            self.assertFalse((jw / rs.RENDER_LOGO_REL_DIR).exists())

    def test_load_drops_logo_when_file_missing(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            rs.save_render_settings(jw, {"aspect_ratio": "source", "logo_path": "assets/render_logo/gone.png"})
            loaded = rs.load_render_settings(jw)
            self.assertNotIn("logo_path", loaded)

    def test_rejects_bad_extension_on_import(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            bad = jw / "brand.bmp"
            bad.write_bytes(b"x" * 32)
            with self.assertRaises(rs.RenderSettingsError):
                rs.import_render_logo_image(jw, bad)


class LogoFiltergraphTest(unittest.TestCase):
    def test_position_expressions(self) -> None:
        self.assertEqual(_logo_overlay_position("top-left", 10), "10:10")
        self.assertEqual(_logo_overlay_position("top-right", 10), "W-w-10:10")
        self.assertEqual(_logo_overlay_position("bottom-left", 10), "10:H-h-10")
        self.assertEqual(_logo_overlay_position("bottom-right", 10), "W-w-10:H-h-10")

    def test_filter_complex_contains_logo_overlay(self) -> None:
        fc, _ = _build_layout_filter_complex(
            target_w=1080,
            target_h=1920,
            background_input_index=None,
            burn_subtitle_path=None,
            style={},
            logo_input_index=2,
            logo_info={"position": "bottom-right", "scale": 0.2, "opacity": 0.8, "margin": 0.03},
        )
        self.assertIn("[2:v]scale=", fc)              # logo scaled
        self.assertIn("colorchannelmixer=aa=0.8000", fc)  # opacity applied
        self.assertIn("overlay=W-w-", fc)             # bottom-right placement
        self.assertIn("[vout]", fc)                   # terminal label preserved

    def test_filter_complex_without_logo_is_unchanged_shape(self) -> None:
        fc, _ = _build_layout_filter_complex(
            target_w=1280,
            target_h=720,
            background_input_index=None,
            burn_subtitle_path=None,
            style={},
        )
        self.assertNotIn("[logo]", fc)
        self.assertIn("[vbase]format=yuv420p[vout]", fc)


if __name__ == "__main__":
    unittest.main()
