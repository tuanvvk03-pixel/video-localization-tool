"""Phase E2 — post-render assembly guard logic (engine.video_assemble).

The real ffmpeg trim+concat is verified manually (mixed resolution/fps + missing
audio + trim). Here we pin the input validation that runs without ffmpeg.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from engine import render_settings as rs
from engine import video_assemble as va


class BrandingSettingsTest(unittest.TestCase):
    def test_normalize_clips_and_trim(self) -> None:
        out = rs.normalize_render_settings({
            "aspect_ratio": "source",
            "intro_clip_path": "assets/render_intro/in.mp4",
            "outro_clip_path": "assets/render_outro/out.mp4",
            "head_trim_sec": 1.5, "tail_trim_sec": 2,
        })
        self.assertEqual(out["intro_clip_path"], "assets/render_intro/in.mp4")
        self.assertEqual(out["outro_clip_path"], "assets/render_outro/out.mp4")
        self.assertEqual(out["head_trim_sec"], 1.5)
        self.assertEqual(out["tail_trim_sec"], 2.0)

    def test_zero_trim_is_omitted(self) -> None:
        out = rs.normalize_render_settings({"aspect_ratio": "source", "head_trim_sec": 0, "tail_trim_sec": 0})
        self.assertNotIn("head_trim_sec", out)
        self.assertNotIn("tail_trim_sec", out)

    def test_negative_trim_rejected(self) -> None:
        with self.assertRaises(rs.RenderSettingsError):
            rs.normalize_render_settings({"head_trim_sec": -1})

    def test_import_clip_rejects_bad_extension(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            bad = jw / "clip.txt"
            bad.write_bytes(b"x" * 16)
            with self.assertRaises(rs.RenderSettingsError):
                rs.import_render_outro_clip(jw, bad)

    def test_import_and_clear_outro(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            clip = jw / "myoutro.mp4"
            clip.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"0" * 64)
            settings = rs.import_render_outro_clip(jw, clip)
            self.assertTrue(str(settings["outro_clip_path"]).endswith("myoutro.mp4"))
            self.assertTrue((jw / settings["outro_clip_path"]).is_file())
            cleared = rs.clear_render_outro(jw)
            self.assertNotIn("outro_clip_path", cleared)
            self.assertFalse((jw / rs.RENDER_OUTRO_REL_DIR).exists())

    def test_load_drops_missing_clip(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            rs.save_render_settings(jw, {"aspect_ratio": "source", "intro_clip_path": "assets/render_intro/gone.mp4"})
            loaded = rs.load_render_settings(jw)
            self.assertNotIn("intro_clip_path", loaded)


class AssembleGuardTest(unittest.TestCase):
    def test_missing_main_raises(self) -> None:
        with self.assertRaises(va.VideoAssembleError):
            va.assemble_branded_video(
                main_video=Path("nope.mp4"), out_path=Path("out.mp4"),
                ffmpeg="ffmpeg", ffprobe="ffprobe", outro_clip=None,
            )

    def test_nothing_after_trim_raises(self) -> None:
        with TemporaryDirectory() as d:
            main = Path(d) / "main.mp4"
            main.write_bytes(b"x")
            # main is 10s; trimming 6+6 leaves nothing
            with mock.patch.object(va, "_probe_video", return_value=(1920, 1080, 30.0, 10.0)):
                with self.assertRaises(va.VideoAssembleError) as ctx:
                    va.assemble_branded_video(
                        main_video=main, out_path=Path(d) / "o.mp4",
                        ffmpeg="ffmpeg", ffprobe="ffprobe",
                        head_trim_sec=6.0, tail_trim_sec=6.0,
                    )
            self.assertIn("trimming", str(ctx.exception).lower())

    def test_no_op_raises(self) -> None:
        with TemporaryDirectory() as d:
            main = Path(d) / "main.mp4"
            main.write_bytes(b"x")
            with mock.patch.object(va, "_probe_video", return_value=(1920, 1080, 30.0, 10.0)):
                with self.assertRaises(va.VideoAssembleError) as ctx:
                    va.assemble_branded_video(
                        main_video=main, out_path=Path(d) / "o.mp4",
                        ffmpeg="ffmpeg", ffprobe="ffprobe",
                    )
            self.assertIn("no assembly", str(ctx.exception).lower())

    def test_missing_intro_clip_raises(self) -> None:
        with TemporaryDirectory() as d:
            main = Path(d) / "main.mp4"
            main.write_bytes(b"x")
            with mock.patch.object(va, "_probe_video", return_value=(1920, 1080, 30.0, 10.0)):
                with self.assertRaises(va.VideoAssembleError) as ctx:
                    va.assemble_branded_video(
                        main_video=main, out_path=Path(d) / "o.mp4",
                        ffmpeg="ffmpeg", ffprobe="ffprobe",
                        intro_clip=Path(d) / "ghost_intro.mp4",
                    )
            self.assertIn("intro", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
