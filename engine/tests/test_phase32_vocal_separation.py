"""Phase E4 — keep-music mix mode (vocal separation via Demucs).

The real Demucs separation is verified manually (needs torch + the htdemucs
model). Here we pin: the mix_mode is accepted by settings + the run-mix CLI, and
vocal_separation degrades gracefully when Demucs isn't installed.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from engine import tts_settings
from engine import vocal_separation as vs
from engine.run_mix_stage import _parse_args


class KeepMusicSettingsTest(unittest.TestCase):
    def test_validate_accepts_keep_music_mode(self) -> None:
        out = tts_settings.validate_settings({"mix_mode": "keep_music_replace_voice"})
        self.assertEqual(out["mix_mode"], "keep_music_replace_voice")

    def test_validate_rejects_unknown_mode(self) -> None:
        with self.assertRaises(ValueError):
            tts_settings.validate_settings({"mix_mode": "bogus_mode"})

    def test_mix_cli_accepts_mode_and_device(self) -> None:
        ns = _parse_args(["--job-workspace", ".", "--mix-mode", "keep_music_replace_voice", "--demucs-device", "cuda"])
        self.assertEqual(ns.mix_mode, "keep_music_replace_voice")
        self.assertEqual(ns.demucs_device, "cuda")


class VocalSeparationGuardTest(unittest.TestCase):
    def test_missing_audio_raises(self) -> None:
        with self.assertRaises(vs.VocalSeparationError):
            vs.separate_instrumental(Path("nope.wav"), Path("out.wav"))

    def test_missing_demucs_raises_with_hint(self) -> None:
        with TemporaryDirectory() as d:
            src = Path(d) / "a.wav"
            src.write_bytes(b"RIFFxxxxWAVE")
            with mock.patch.object(vs, "demucs_available", return_value=False):
                with self.assertRaises(vs.VocalSeparationError) as ctx:
                    vs.separate_instrumental(src, Path(d) / "out.wav")
            self.assertIn("demucs", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
