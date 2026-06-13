"""Phase E2 — post-render assembly guard logic (engine.video_assemble).

The real ffmpeg trim+concat is verified manually (mixed resolution/fps + missing
audio + trim). Here we pin the input validation that runs without ffmpeg.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from engine import video_assemble as va


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
