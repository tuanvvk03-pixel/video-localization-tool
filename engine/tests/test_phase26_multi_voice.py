"""Phase D1 — per-cue multi-voice override (sidecar + run_tts_stage)."""
from __future__ import annotations

import asyncio
import unittest
import wave
from pathlib import Path
from tempfile import TemporaryDirectory

from engine import run_tts_stage, voice_edit_api
from engine.srt_cues import parse_srt_cues

_SRT = """1
00:00:01,000 --> 00:00:02,000
Hello one

2
00:00:03,000 --> 00:00:04,000
Hello two
"""


def _write_wav(path: Path, ms: int = 100) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rate = 24000
    nframes = int(rate * ms / 1000)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * nframes)


class _FakeProvider:
    """Records each synth call's voice/rate and writes a valid 100ms WAV."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def synthesize_cue_to_wav(self, text, out_wav, *, voice, rate, diag_prefix="", provider_config=None):
        self.calls.append({"voice": voice, "rate": rate, "wav": Path(out_wav).name})
        _write_wav(Path(out_wav), 100)
        return 100


class VoiceOverridePersistenceTest(unittest.TestCase):
    def test_clean_drops_empty_and_bad_entries(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            cleaned = voice_edit_api.save_voice_overrides(
                jw,
                {
                    "3": {"voice_id": "en-US-Jenny", "rate": "+5%"},
                    "4": {"voice_id": "", "rate": ""},  # all blank -> dropped
                    "notanint": {"voice_id": "x"},  # bad key -> dropped
                    "5": {"voice_id": "  vi-VN-HoaiMy  ", "provider": "edge_tts"},  # trimmed
                },
            )
            self.assertEqual(set(cleaned), {"3", "5"})
            self.assertEqual(cleaned["3"], {"voice_id": "en-US-Jenny", "rate": "+5%"})
            self.assertEqual(cleaned["5"], {"voice_id": "vi-VN-HoaiMy", "provider": "edge_tts"})
            self.assertEqual(voice_edit_api.load_voice_overrides(jw), cleaned)
            self.assertEqual(voice_edit_api.load_voice_overrides_indexed(jw), {3: cleaned["3"], 5: cleaned["5"]})

    def test_load_missing_returns_empty(self) -> None:
        with TemporaryDirectory() as d:
            self.assertEqual(voice_edit_api.load_voice_overrides(Path(d)), {})


class SynthesizeOverrideTest(unittest.TestCase):
    def _run(self, fake, cues, cues_dir, jw, *, prev, overrides):
        orig = run_tts_stage.get_tts_provider
        run_tts_stage.get_tts_provider = lambda _name: fake  # type: ignore[assignment]
        try:
            return asyncio.run(
                run_tts_stage._synthesize_all(
                    jw, cues, "edge_tts", "voiceA", "+0%", cues_dir,
                    previous_cue_entries=prev, voice_overrides=overrides,
                )
            )
        finally:
            run_tts_stage.get_tts_provider = orig  # type: ignore[assignment]

    def test_override_cue_uses_override_voice_and_cache_is_per_cue(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            cues_dir = jw / "artifacts" / "tts" / "cues"
            cues = parse_srt_cues(_SRT)
            self.assertEqual([c.index for c in cues], [1, 2])

            # Run 1: cue 2 overridden to voiceB.
            fake1 = _FakeProvider()
            manifest1 = self._run(fake1, cues, cues_dir, jw, prev={}, overrides={2: {"voice_id": "voiceB"}})
            self.assertEqual([c["voice"] for c in manifest1], ["voiceA", "voiceB"])
            self.assertEqual([c["voice"] for c in fake1.calls], ["voiceA", "voiceB"])

            # Run 2: same overrides + prior manifest -> both cues skip (cache hit).
            prev = {c["index"]: c for c in manifest1}
            fake2 = _FakeProvider()
            manifest2 = self._run(fake2, cues, cues_dir, jw, prev=prev, overrides={2: {"voice_id": "voiceB"}})
            self.assertEqual(fake2.calls, [], "cache hit should re-synth nothing")
            self.assertEqual([c["voice"] for c in manifest2], ["voiceA", "voiceB"])

            # Run 3: change ONLY cue 2's override -> only cue 2 re-synthesizes.
            prev = {c["index"]: c for c in manifest2}
            fake3 = _FakeProvider()
            manifest3 = self._run(fake3, cues, cues_dir, jw, prev=prev, overrides={2: {"voice_id": "voiceC"}})
            self.assertEqual([c["voice"] for c in fake3.calls], ["voiceC"], "only the edited cue re-synths")
            self.assertEqual([c["voice"] for c in manifest3], ["voiceA", "voiceC"])


if __name__ == "__main__":
    unittest.main()
