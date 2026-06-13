"""Background music settings and mix-stage integration tests."""
from __future__ import annotations

import json
import math
import shutil
import subprocess
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import run_mix_stage  # noqa: E402
from engine.ffmpeg_bins import resolve_ffmpeg_executable, resolve_ffprobe_executable  # noqa: E402


def _write_tone(path: Path, *, seconds: float, freq: float = 440.0, sample_rate: int = 24000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = int(seconds * sample_rate)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(frames):
            sample = int(12000 * math.sin(2.0 * math.pi * freq * (i / sample_rate)))
            wf.writeframes(struct.pack("<h", sample))


def _probe_duration(path: Path) -> float:
    ffprobe = resolve_ffprobe_executable()
    if not ffprobe:
        return 0.0
    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return 0.0
    try:
        return float((proc.stdout or "0").strip())
    except ValueError:
        return 0.0


class BgmMixStageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase21_bgm_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_mix_stage_with_bgm_writes_audio_and_manifest(self) -> None:
        ffmpeg, _ = resolve_ffmpeg_executable()
        ffprobe = resolve_ffprobe_executable()
        if not ffmpeg or not ffprobe:
            self.skipTest("ffmpeg/ffprobe not available")

        jw = self.tmp_root / "job"
        aligned = jw / "artifacts" / "aligned" / "voice_track_aligned.wav"
        bgm = jw / "assets" / "bgm" / "bgm_normalized.wav"
        _write_tone(aligned, seconds=0.8, freq=500)
        _write_tone(bgm, seconds=0.2, freq=220)
        (jw / "artifacts" / "aligned" / "alignment_manifest.json").write_text(
            json.dumps({"sample_rate_hz": 24000, "cues": []}, ensure_ascii=False),
            encoding="utf-8",
        )

        code = run_mix_stage.main(
            [
                "--job-workspace",
                str(jw),
                "--mix-mode",
                "replace_original_speech",
                "--bgm",
                "assets/bgm/bgm_normalized.wav",
                "--bgm-volume-db",
                "-24",
                "--bgm-loop",
                "--bgm-fade-in-ms",
                "100",
                "--bgm-fade-out-ms",
                "100",
            ]
        )

        self.assertEqual(code, 0)
        self.assertTrue((jw / "artifacts" / "mixed" / "mixed_audio.wav").is_file())
        manifest = json.loads(
            (jw / "artifacts" / "mixed" / "mix_manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["mix_mode"], "replace_original_speech")
        self.assertEqual(manifest["bgm_volume_db"], -24.0)
        self.assertTrue(manifest["bgm_loop"])
        self.assertTrue(str(manifest["inputs"]["bgm"]).endswith("bgm_normalized.wav"))

    def test_short_bgm_loops_automatically_without_loop_flag(self) -> None:
        ffmpeg, _ = resolve_ffmpeg_executable()
        ffprobe = resolve_ffprobe_executable()
        if not ffmpeg or not ffprobe:
            self.skipTest("ffmpeg/ffprobe not available")

        jw = self.tmp_root / "short_bgm"
        aligned = jw / "artifacts" / "aligned" / "voice_track_aligned.wav"
        bgm = jw / "assets" / "bgm" / "bgm_normalized.wav"
        _write_tone(aligned, seconds=0.9, freq=500)
        _write_tone(bgm, seconds=0.2, freq=220)
        (jw / "artifacts" / "aligned" / "alignment_manifest.json").write_text(
            json.dumps({"sample_rate_hz": 24000, "cues": []}, ensure_ascii=False),
            encoding="utf-8",
        )

        code = run_mix_stage.main(
            [
                "--job-workspace",
                str(jw),
                "--mix-mode",
                "replace_original_speech",
                "--bgm",
                "assets/bgm/bgm_normalized.wav",
                "--bgm-volume-db",
                "-24",
                "--bgm-fade-in-ms",
                "0",
                "--bgm-fade-out-ms",
                "0",
            ]
        )

        self.assertEqual(code, 0)
        out = jw / "artifacts" / "mixed" / "mixed_audio.wav"
        self.assertAlmostEqual(_probe_duration(out), 0.9, delta=0.08)
        manifest = json.loads(
            (jw / "artifacts" / "mixed" / "mix_manifest.json").read_text(encoding="utf-8")
        )
        self.assertTrue(manifest["bgm_loop"])
        self.assertFalse(manifest["bgm_loop_requested"])
        self.assertTrue(manifest["bgm_auto_looped"])
        self.assertEqual(manifest["bgm_duration_policy"], "loop_to_duration")

    def test_long_bgm_is_trimmed_to_mix_duration(self) -> None:
        ffmpeg, _ = resolve_ffmpeg_executable()
        ffprobe = resolve_ffprobe_executable()
        if not ffmpeg or not ffprobe:
            self.skipTest("ffmpeg/ffprobe not available")

        jw = self.tmp_root / "long_bgm"
        aligned = jw / "artifacts" / "aligned" / "voice_track_aligned.wav"
        bgm = jw / "assets" / "bgm" / "bgm_normalized.wav"
        _write_tone(aligned, seconds=0.8, freq=500)
        _write_tone(bgm, seconds=1.4, freq=220)
        (jw / "artifacts" / "aligned" / "alignment_manifest.json").write_text(
            json.dumps({"sample_rate_hz": 24000, "cues": []}, ensure_ascii=False),
            encoding="utf-8",
        )

        code = run_mix_stage.main(
            [
                "--job-workspace",
                str(jw),
                "--mix-mode",
                "replace_original_speech",
                "--bgm",
                "assets/bgm/bgm_normalized.wav",
                "--bgm-volume-db",
                "-24",
                "--bgm-fade-in-ms",
                "0",
                "--bgm-fade-out-ms",
                "0",
            ]
        )

        self.assertEqual(code, 0)
        out = jw / "artifacts" / "mixed" / "mixed_audio.wav"
        self.assertAlmostEqual(_probe_duration(out), 0.8, delta=0.08)
        manifest = json.loads(
            (jw / "artifacts" / "mixed" / "mix_manifest.json").read_text(encoding="utf-8")
        )
        self.assertFalse(manifest["bgm_loop"])
        self.assertFalse(manifest["bgm_auto_looped"])
        self.assertEqual(manifest["bgm_duration_policy"], "trim_to_duration")


if __name__ == "__main__":
    unittest.main()
