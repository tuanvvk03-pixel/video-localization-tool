"""Phase D2 — XTTS voice-cloning provider (optional dependency).

Synthesis itself needs the heavy ``TTS``/torch + a GPU and is verified manually
(scripts/xtts_smoke.py). Here we pin the parts that must work on a plain desktop
WITHOUT TTS installed: the provider is registered, and using it fails with a
clear, actionable error instead of a crash.
"""
from __future__ import annotations

import asyncio
import unittest
import wave
from pathlib import Path
from tempfile import TemporaryDirectory

from engine.tts import get_tts_provider
from engine.tts.xtts_provider import XttsProvider

try:
    import TTS  # type: ignore  # noqa: F401

    _HAS_TTS = True
except Exception:  # noqa: BLE001
    _HAS_TTS = False


def _write_wav(path: Path, ms: int = 200) -> None:
    rate = 24000
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(rate * ms / 1000))


class XttsFactoryTest(unittest.TestCase):
    def test_registered_under_xtts_and_aliases(self) -> None:
        for name in ("xtts", "coqui", "xtts_v2", "XTTS"):
            self.assertIsInstance(get_tts_provider(name), XttsProvider)


class XttsGracefulErrorTest(unittest.TestCase):
    def _synth(self, voice: str, out: Path) -> None:
        asyncio.run(
            XttsProvider().synthesize_cue_to_wav("xin chào", out, voice=voice, rate="")
        )

    def test_empty_voice_raises_actionable(self) -> None:
        with TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError) as ctx:
                self._synth("", Path(d) / "o.wav")
            self.assertIn("speaker reference", str(ctx.exception).lower())

    def test_missing_speaker_file_raises(self) -> None:
        with TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError) as ctx:
                self._synth(str(Path(d) / "nope.wav"), Path(d) / "o.wav")
            self.assertIn("not found", str(ctx.exception).lower())

    @unittest.skipIf(_HAS_TTS, "TTS installed: would load a real model (GPU)")
    def test_without_tts_installed_gives_install_hint(self) -> None:
        with TemporaryDirectory() as d:
            speaker = Path(d) / "speaker.wav"
            _write_wav(speaker)
            with self.assertRaises(RuntimeError) as ctx:
                self._synth(str(speaker), Path(d) / "o.wav")
            msg = str(ctx.exception).lower()
            self.assertIn("pip install", msg)
            self.assertIn("tts", msg)


if __name__ == "__main__":
    unittest.main()
