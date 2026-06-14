"""Phase F4 — parallel cue synthesis for the network edge_tts path."""
from __future__ import annotations

import asyncio
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from engine import run_tts_stage
from engine.srt_cues import parse_srt_cues

_SRT = "\n\n".join(
    f"{i}\n00:00:0{i},000 --> 00:00:0{i},900\nline {i}" for i in range(1, 6)
) + "\n"


class _FakeProvider:
    async def synthesize_cue_to_wav(self, text, out_wav, *, voice, rate, diag_prefix, provider_config=None):
        await asyncio.sleep(0)  # yield so the semaphore actually interleaves
        Path(out_wav).write_bytes(b"RIFF....WAVE")
        return 100


class TtsParallelTest(unittest.TestCase):
    def test_concurrency_env_clamp(self) -> None:
        with mock.patch.dict("os.environ", {"VL_TTS_CONCURRENCY": "99"}):
            self.assertEqual(run_tts_stage._tts_concurrency(), 8)
        with mock.patch.dict("os.environ", {"VL_TTS_CONCURRENCY": "0"}):
            self.assertEqual(run_tts_stage._tts_concurrency(), 1)
        with mock.patch.dict("os.environ", {"VL_TTS_CONCURRENCY": "bad"}):
            self.assertEqual(run_tts_stage._tts_concurrency(), 4)

    def test_parallel_edge_preserves_order(self) -> None:
        cues = parse_srt_cues(_SRT)
        self.assertEqual(len(cues), 5)
        with TemporaryDirectory() as d:
            jw = Path(d)
            cues_dir = jw / "cues"
            cues_dir.mkdir()
            with (
                mock.patch.object(run_tts_stage, "get_tts_provider", return_value=_FakeProvider()),
                mock.patch.dict("os.environ", {"VL_TTS_CONCURRENCY": "4"}),
            ):
                manifest = asyncio.run(run_tts_stage._synthesize_all(
                    jw, cues, "edge_tts", "vi-VN-HoaiMyNeural", "+0%", cues_dir,
                    previous_cue_entries={},
                ))
        # All cues present and in ascending index order despite parallel execution.
        self.assertEqual([m["index"] for m in manifest], [1, 2, 3, 4, 5])
        self.assertTrue(all(m["audio_duration_ms"] == 100 for m in manifest))

    def test_overrides_force_sequential(self) -> None:
        cues = parse_srt_cues(_SRT)
        with TemporaryDirectory() as d:
            jw = Path(d)
            cues_dir = jw / "cues"
            cues_dir.mkdir()
            with mock.patch.object(run_tts_stage, "get_tts_provider", return_value=_FakeProvider()):
                manifest = asyncio.run(run_tts_stage._synthesize_all(
                    jw, cues, "edge_tts", "v", "+0%", cues_dir,
                    previous_cue_entries={},
                    voice_overrides={2: {"voice_id": "other"}},
                ))
        self.assertEqual([m["index"] for m in manifest], [1, 2, 3, 4, 5])
        self.assertEqual(manifest[1]["voice"], "other")


if __name__ == "__main__":
    unittest.main()
