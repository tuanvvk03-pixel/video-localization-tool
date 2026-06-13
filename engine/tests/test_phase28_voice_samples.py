"""Phase D2.3 — voice-sample (speaker reference) persistence.

Tests the validation + list/remove logic. The ffmpeg normalize path is verified
manually (env with ffmpeg); here we cover the parts that run without it.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from engine import voice_samples


class VoiceSamplesTest(unittest.TestCase):
    def test_list_empty(self) -> None:
        with TemporaryDirectory() as d:
            self.assertEqual(voice_samples.list_voice_samples(Path(d)), [])

    def test_list_reads_existing_wavs(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            sdir = jw / voice_samples.SAMPLES_REL_DIR
            sdir.mkdir(parents=True)
            (sdir / "alice.wav").write_bytes(b"RIFF....WAVE")
            (sdir / "bob.wav").write_bytes(b"RIFF....WAVE")
            (sdir / "ignore.txt").write_text("x")
            ids = {s["id"] for s in voice_samples.list_voice_samples(jw)}
            self.assertEqual(ids, {"alice", "bob"})

    def test_import_rejects_bad_extension(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            bad = jw / "clip.txt"
            bad.write_text("nope")
            with self.assertRaises(voice_samples.VoiceSampleError) as ctx:
                voice_samples.import_voice_sample(jw, bad)
            self.assertIn("one of", str(ctx.exception).lower())

    def test_import_rejects_missing_file(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            with self.assertRaises(voice_samples.VoiceSampleError) as ctx:
                voice_samples.import_voice_sample(jw, jw / "nope.wav")
            self.assertIn("does not exist", str(ctx.exception).lower())

    def test_remove_is_safe_and_scoped(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            sdir = jw / voice_samples.SAMPLES_REL_DIR
            sdir.mkdir(parents=True)
            (sdir / "alice.wav").write_bytes(b"x")
            voice_samples.remove_voice_sample(jw, "alice")
            self.assertFalse((sdir / "alice.wav").exists())
            # Path-traversal / unknown id must not blow up or escape.
            voice_samples.remove_voice_sample(jw, "../../etc/passwd")
            voice_samples.remove_voice_sample(jw, "missing")


if __name__ == "__main__":
    unittest.main()
