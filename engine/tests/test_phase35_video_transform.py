"""Phase E3 — anti-dedup transforms (settings + guard logic).

The real ffmpeg transform is verified manually (speed/hflip/zoom/eq). Here we pin
the render_settings schema + transforms_active + the no-op guard.
"""
from __future__ import annotations

import unittest
from pathlib import Path

from engine import render_settings as rs
from engine import video_transform as vt


class TransformSettingsTest(unittest.TestCase):
    def test_active_emits_only_non_default(self) -> None:
        out = rs.normalize_render_settings({
            "aspect_ratio": "source",
            "transform_speed": 1.05, "transform_hflip": True, "transform_zoom": 1.0,
            "transform_contrast": 1.0, "transform_brightness": 0.1,
        })
        self.assertEqual(out["transform_speed"], 1.05)
        self.assertTrue(out["transform_hflip"])
        self.assertEqual(out["transform_brightness"], 0.1)
        # No-op fields are dropped.
        self.assertNotIn("transform_zoom", out)
        self.assertNotIn("transform_contrast", out)
        self.assertTrue(rs.transforms_active(out))

    def test_all_default_is_inactive(self) -> None:
        out = rs.normalize_render_settings({"aspect_ratio": "9:16"})
        self.assertFalse(rs.transforms_active(out))
        for k in ("transform_speed", "transform_hflip", "transform_zoom"):
            self.assertNotIn(k, out)

    def test_out_of_range_rejected(self) -> None:
        with self.assertRaises(rs.RenderSettingsError):
            rs.normalize_render_settings({"transform_speed": 5.0})

    def test_transforms_active_none(self) -> None:
        self.assertFalse(rs.transforms_active(None))
        self.assertFalse(rs.transforms_active({}))

    def test_no_transform_raises(self) -> None:
        # apply_transforms with all no-ops should refuse rather than waste a re-encode.
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as d:
            src = Path(d) / "x.mp4"
            src.write_bytes(b"\x00" * 32)
            with self.assertRaises(vt.VideoTransformError) as ctx:
                vt.apply_transforms(src, Path(d) / "o.mp4", ffmpeg="ffmpeg", ffprobe="ffprobe")
            self.assertIn("no transform", str(ctx.exception).lower())

    def test_missing_input_raises(self) -> None:
        with self.assertRaises(vt.VideoTransformError):
            vt.apply_transforms(Path("nope.mp4"), Path("o.mp4"), ffmpeg="ffmpeg", ffprobe="ffprobe", hflip=True)


if __name__ == "__main__":
    unittest.main()
