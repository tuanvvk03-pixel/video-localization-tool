from __future__ import annotations

import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.tts.edge_tts_provider import EdgeTtsProvider


PROBLEMATIC_TEXT = "Tr\u1eddi \u0111\u1ea5t \u01a1i, sao b\u1ecf l\u1eafm \u1edbt v\u1eady?"


class EdgeTtsFallbackTest(unittest.IsolatedAsyncioTestCase):
    async def test_retries_with_text_transform_after_no_audio_received(self) -> None:
        out_root = Path(tempfile.mkdtemp(prefix="phase23_edge_tts_"))
        out_wav = out_root / "cue.wav"
        calls: list[str] = []

        class NoAudioReceived(Exception):
            pass

        class FakeCommunicate:
            def __init__(self, text: str, voice: str, rate: str) -> None:
                del voice, rate
                self.text = text
                calls.append(text)

            async def save(self, path: str) -> None:
                if self.text == PROBLEMATIC_TEXT:
                    raise NoAudioReceived(
                        "No audio was received. Please verify that your parameters are correct."
                    )
                Path(path).write_bytes(b"ID3FAKE")

        class FakeProc:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"", b""

        async def fake_exec(*args, **kwargs):
            del kwargs
            Path(args[-1]).write_bytes(b"RIFFFAKE")
            return FakeProc()

        fake_edge_module = types.SimpleNamespace(
            Communicate=FakeCommunicate,
            exceptions=types.SimpleNamespace(NoAudioReceived=NoAudioReceived),
        )

        try:
            with (
                mock.patch.dict(sys.modules, {"edge_tts": fake_edge_module}),
                mock.patch(
                    "engine.tts.edge_tts_provider.resolve_ffmpeg_executable",
                    return_value=("ffmpeg", None),
                ),
                mock.patch(
                    "engine.tts.edge_tts_provider.asyncio.create_subprocess_exec",
                    side_effect=fake_exec,
                ),
                mock.patch("engine.tts.edge_tts_provider._wav_duration_ms", return_value=321),
            ):
                provider = EdgeTtsProvider()
                duration_ms = await provider.synthesize_cue_to_wav(
                    PROBLEMATIC_TEXT,
                    out_wav,
                    voice="vi-VN-HoaiMyNeural",
                    rate="+0%",
                    diag_prefix="[test]",
                )
        finally:
            shutil.rmtree(out_root, ignore_errors=True)

        self.assertEqual(duration_ms, 321)
        self.assertGreaterEqual(len(calls), 2)
        self.assertEqual(calls[0], PROBLEMATIC_TEXT)
        self.assertTrue(any(call != PROBLEMATIC_TEXT for call in calls[1:]))


class TranscribeVadFallbackTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase23_transcribe_vad_"))
        self.jw = self.root / "job"
        (self.jw / "input").mkdir(parents=True)
        (self.jw / "input" / "source.mp4").write_bytes(b"\x00")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_missing_silero_vad_asset_retries_without_vad(self) -> None:
        from engine import run_transcribe_stage

        out_srt = self.jw / "artifacts" / "transcribe" / "source.srt"
        transcribe_calls: list[dict[str, object]] = []

        class FakeWhisperModel:
            def __init__(self, model_size: str, device: str, compute_type: str) -> None:
                del model_size, device, compute_type

            def transcribe(self, audio_path: str, **kwargs):
                del audio_path
                transcribe_calls.append(dict(kwargs))
                if kwargs.get("vad_filter"):
                    raise RuntimeError(
                        "[ONNXRuntimeError] : 3 : NO_SUCHFILE : Load model from "
                        "dist\\VLTool\\_internal\\faster_whisper\\assets\\silero_vad_v6.onnx "
                        "failed: File doesn't exist"
                    )
                segments = [SimpleNamespace(start=0.0, end=1.0, text="hello world")]
                return iter(segments), SimpleNamespace(language="en")

        fake_ns = SimpleNamespace(
            model_size="small",
            language="",
            device="cpu",
            compute_type="auto",
            beam_size=5,
            best_of=5,
            no_speech_threshold=0.5,
            no_vad_filter=False,
            vad_threshold=0.35,
            vad_min_silence_ms=500,
            vad_min_speech_ms=0,
            vad_speech_pad_ms=240,
            audio_preprocess="none",
            long_gap_report_ms=2000,
        )

        fake_report = {
            "warnings": [],
            "segment_count": 1,
            "transcription_coverage_ratio": 1.0,
        }

        with (
            mock.patch.dict(
                sys.modules,
                {"faster_whisper": types.SimpleNamespace(WhisperModel=FakeWhisperModel)},
            ),
            mock.patch.object(
                run_transcribe_stage,
                "build_transcription_report",
                return_value=dict(fake_report),
            ),
        ):
            meta = run_transcribe_stage._run_asr_to_srt(fake_ns, self.jw, out_srt)

        self.assertEqual(len(transcribe_calls), 2)
        self.assertTrue(transcribe_calls[0]["vad_filter"])
        self.assertFalse(transcribe_calls[1]["vad_filter"])
        self.assertTrue(out_srt.is_file())
        self.assertIn("hello world", out_srt.read_text(encoding="utf-8"))
        self.assertFalse(meta["report"]["vad_filter"])
        self.assertIsNone(meta["report"]["vad_parameters"])
        self.assertIn(
            "vad_asset_missing_retry_without_vad",
            meta["report"]["warnings"],
        )
        self.assertIn("silero_vad_v6.onnx", meta["report"]["vad_fallback_reason"])


if __name__ == "__main__":
    unittest.main()
