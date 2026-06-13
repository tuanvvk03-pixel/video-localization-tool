from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import run_render_stage  # noqa: E402
from engine.ffmpeg_bins import resolve_ffmpeg_executable, resolve_ffprobe_executable  # noqa: E402


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise AssertionError((proc.stderr or proc.stdout or "command failed")[-4000:])


def _probe_dimensions(path: Path) -> tuple[int, int]:
    ffprobe = resolve_ffprobe_executable()
    if not ffprobe:
        return 0, 0
    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return 0, 0
    body = json.loads(proc.stdout or "{}")
    stream = (body.get("streams") or [{}])[0]
    return int(stream.get("width") or 0), int(stream.get("height") or 0)


class RenderLayoutStageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="phase22_render_layout_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_render_can_frame_landscape_source_as_vertical_with_background(self) -> None:
        ffmpeg, _ = resolve_ffmpeg_executable()
        ffprobe = resolve_ffprobe_executable()
        if not ffmpeg or not ffprobe:
            self.skipTest("ffmpeg/ffprobe not available")

        jw = self.tmp / "job"
        (jw / "input").mkdir(parents=True)
        (jw / "artifacts" / "aligned").mkdir(parents=True)
        (jw / "assets" / "render_background").mkdir(parents=True)
        source = jw / "input" / "source.mp4"
        audio = jw / "artifacts" / "aligned" / "voice_track_aligned.wav"
        background = jw / "assets" / "render_background" / "background.png"
        _run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=320x180:d=1.0",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=1.0",
                "-shortest",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                str(source),
            ]
        )
        _run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=660:duration=1.0",
                "-ac",
                "2",
                "-ar",
                "48000",
                "-c:a",
                "pcm_s16le",
                str(audio),
            ]
        )
        _run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=c=blue:s=180x320:d=0.1",
                "-frames:v",
                "1",
                str(background),
            ]
        )
        (jw / "artifacts" / "aligned" / "alignment_manifest.json").write_text(
            json.dumps({"sample_rate_hz": 24000, "cues": []}), encoding="utf-8"
        )

        code = run_render_stage.main(
            [
                "--job-workspace",
                str(jw),
                "--subtitle-mode",
                "none",
                "--aspect-ratio",
                "9:16",
                "--background-image",
                "assets/render_background/background.png",
                "--overwrite",
            ]
        )

        self.assertEqual(code, 0)
        out = jw / "artifacts" / "render" / "final.mp4"
        self.assertEqual(_probe_dimensions(out), (180, 320))
        manifest = json.loads((jw / "artifacts" / "render" / "render_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["render_layout"]["aspect_ratio"], "9:16")
        self.assertTrue(manifest["render_layout"]["enabled"])
        self.assertEqual(manifest["render_layout"]["target_width"], 180)
        self.assertEqual(manifest["render_layout"]["target_height"], 320)


if __name__ == "__main__":
    unittest.main()
