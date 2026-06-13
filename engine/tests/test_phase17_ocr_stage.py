from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import run_ocr_stage
from engine.ocr.base import OcrFrameResult, OcrLine, OcrProvider


class _ScriptedProvider(OcrProvider):
    """Returns a pre-scripted text for each consecutive recognize_image call."""

    name = "scripted"

    def __init__(self, scripts: list[str]) -> None:
        self._scripts = list(scripts)
        self._calls = 0

    def device_used(self) -> str:
        return "cpu"

    def recognize_image(self, image_path: Path, *, language: str) -> OcrFrameResult:
        if self._calls >= len(self._scripts):
            text = ""
        else:
            text = self._scripts[self._calls]
        self._calls += 1
        if not text:
            return OcrFrameResult(lines=[], device_used="cpu")
        return OcrFrameResult(
            lines=[OcrLine(text=text, confidence=0.95, bbox=(0, 0, 10, 10))],
            device_used="cpu",
        )


class _FakeFrames:
    """Helper that fabricates ffmpeg-extracted PNG frames in cache_root."""

    def __init__(self, count: int) -> None:
        self.count = count

    def install(self) -> mock._patch:
        def fake_extract(video_path, *, out_dir, roi, width, height, sample_fps):
            out_dir.mkdir(parents=True, exist_ok=True)
            for i in range(1, self.count + 1):
                # PIL is optional; write tiny placeholder PNGs (header only is fine because
                # we also stub _phash to return None, so PIL never opens these files).
                (out_dir / f"frame_{i:06d}.png").write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(16))

        return mock.patch.object(run_ocr_stage, "_extract_frames", side_effect=fake_extract)


def _patch_probe(duration_s: float = 4.0, width: int = 1280, height: int = 720) -> mock._patch:
    return mock.patch.object(run_ocr_stage, "_probe_video", return_value=(duration_s, width, height))


class OcrStageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase17_ocr_"))
        self.jw = self.root / "job_001"
        (self.jw / "input").mkdir(parents=True)
        (self.jw / "input" / "source.mp4").write_bytes(b"\x00")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _run(self, *, scripts, sample_fps=2.0, skip_similarity=2.0, frame_count=None):
        # skip_similarity > 1.0 disables similarity skipping (always OCR).
        provider = _ScriptedProvider(scripts)
        n = frame_count if frame_count is not None else len(scripts)
        with _FakeFrames(n).install(), _patch_probe(), mock.patch.object(
            run_ocr_stage, "_phash", return_value=None
        ):
            return run_ocr_stage.run(
                job_workspace=self.jw,
                language="ch",
                roi={"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.20},
                sample_fps=sample_fps,
                skip_similarity=skip_similarity,
                min_cue_duration_ms=200,
                min_confidence=0.5,
                device="cpu",
                provider_name="scripted",
                keep_frames=False,
                provider=provider,
            ), provider

    # --- A2/A3: srt + manifest happy path ---

    def test_writes_srt_and_manifest_with_grouped_cue(self) -> None:
        manifest, _ = self._run(
            scripts=["你好世界", "你好世界", "你好世界", "再见"],
            sample_fps=2.0,
        )
        srt_path = self.jw / "artifacts" / "transcribe" / "source_ocr.srt"
        manifest_path = self.jw / "artifacts" / "transcribe" / "ocr_manifest.json"
        self.assertTrue(srt_path.is_file(), "source_ocr.srt should exist")
        self.assertTrue(manifest_path.is_file(), "ocr_manifest.json should exist")

        srt = srt_path.read_text(encoding="utf-8")
        self.assertIn("你好世界", srt)
        self.assertIn("再见", srt)
        # 4 frames -> at least 1 grouped cue for 你好世界 + 1 for 再见
        self.assertEqual(srt.count(" --> "), 2, srt)

        body = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(body["cue_count"], 2)
        self.assertEqual(body["frame_count_total"], 4)
        self.assertEqual(body["ocr_device_used"], "cpu")
        self.assertEqual(body["provider"], "scripted")
        self.assertEqual(body["roi"]["y"], 0.78)

    def test_drops_low_confidence_or_empty_text(self) -> None:
        # Empty strings -> no cue; provider returns no lines.
        manifest, _ = self._run(scripts=["", "", ""])
        srt = (self.jw / "artifacts" / "transcribe" / "source_ocr.srt").read_text(encoding="utf-8")
        self.assertEqual(srt, "")
        self.assertEqual(manifest["cue_count"], 0)

    def test_short_cue_filtered_when_under_min_duration(self) -> None:
        # 1 frame at 0.5 fps => period 2000ms; cue spans ~2000ms — passes.
        # Use higher fps so a single isolated frame is shorter than min_cue_duration_ms.
        provider = _ScriptedProvider(["孤立"])
        with _FakeFrames(1).install(), _patch_probe(), mock.patch.object(
            run_ocr_stage, "_phash", return_value=None
        ):
            manifest = run_ocr_stage.run(
                job_workspace=self.jw,
                language="ch",
                roi={"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.20},
                sample_fps=10.0,  # period = 100ms; single-frame cue ~100ms < min 300ms
                skip_similarity=2.0,
                min_cue_duration_ms=300,
                min_confidence=0.5,
                device="cpu",
                provider_name="scripted",
                keep_frames=False,
                provider=provider,
            )
        self.assertEqual(manifest["cue_count"], 0)

    # --- A3: skip-similarity reduces OCR calls ---

    def test_skip_similarity_reuses_previous_result(self) -> None:
        # phash returns the same int for every frame -> similarity = 1.0 -> skip every
        # subsequent frame. Provider should be called only once.
        provider = _ScriptedProvider(["共用文本"])
        with _FakeFrames(5).install(), _patch_probe(), mock.patch.object(
            run_ocr_stage, "_phash", return_value=0
        ):
            manifest = run_ocr_stage.run(
                job_workspace=self.jw,
                language="ch",
                roi={"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.20},
                sample_fps=2.0,
                skip_similarity=0.95,
                min_cue_duration_ms=100,
                min_confidence=0.5,
                device="cpu",
                provider_name="scripted",
                keep_frames=False,
                provider=provider,
            )
        # 5 sampled frames, but only frame 1 was OCR'd; the rest reuse the cached result.
        self.assertEqual(manifest["frame_count_total"], 5)
        self.assertEqual(manifest["frame_count_ocr_called"], 1)
        self.assertEqual(manifest["frame_count_skipped_similar"], 4)
        # Cues: all 5 frames carry the same text -> single grouped cue.
        self.assertEqual(manifest["cue_count"], 1)

    # --- A2: cleanup vs --keep-frames ---

    def test_cache_frames_cleaned_up_by_default(self) -> None:
        self._run(scripts=["abc", "abc"])
        cache = self.jw / "cache" / "ocr_frames"
        self.assertFalse(cache.exists(), f"cache should be cleaned up: {cache}")

    def test_keep_frames_preserves_cache(self) -> None:
        provider = _ScriptedProvider(["abc", "abc"])
        with _FakeFrames(2).install(), _patch_probe(), mock.patch.object(
            run_ocr_stage, "_phash", return_value=None
        ):
            run_ocr_stage.run(
                job_workspace=self.jw,
                language="ch",
                roi={"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.20},
                sample_fps=2.0,
                skip_similarity=2.0,
                min_cue_duration_ms=100,
                min_confidence=0.5,
                device="cpu",
                provider_name="scripted",
                keep_frames=True,
                provider=provider,
            )
        cache = self.jw / "cache" / "ocr_frames"
        self.assertTrue(cache.is_dir())
        self.assertGreaterEqual(len(list(cache.glob("frame_*.png"))), 2)

    def test_second_run_hits_cache_without_extracting_frames_or_loading_provider(self) -> None:
        first_provider = _ScriptedProvider(["cache me", "cache me"])
        with _FakeFrames(2).install(), _patch_probe(), mock.patch.object(
            run_ocr_stage, "_phash", return_value=None
        ):
            first_manifest = run_ocr_stage.run(
                job_workspace=self.jw,
                language="ch",
                roi={"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.20},
                sample_fps=2.0,
                skip_similarity=2.0,
                min_cue_duration_ms=100,
                min_confidence=0.5,
                device="cpu",
                provider_name="scripted",
                keep_frames=False,
                provider=first_provider,
            )
        self.assertFalse(first_manifest["cache_hit"])

        with _patch_probe(), mock.patch.object(
            run_ocr_stage,
            "_extract_frames",
            side_effect=AssertionError("cache hit should skip frame extraction"),
        ), mock.patch.object(
            run_ocr_stage,
            "get_ocr_provider",
            side_effect=AssertionError("cache hit should skip provider init"),
        ):
            second_manifest = run_ocr_stage.run(
                job_workspace=self.jw,
                language="ch",
                roi={"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.20},
                sample_fps=2.0,
                skip_similarity=2.0,
                min_cue_duration_ms=100,
                min_confidence=0.5,
                device="cpu",
                provider_name="scripted",
                keep_frames=False,
            )

        self.assertTrue(second_manifest["cache_hit"])
        self.assertEqual(second_manifest["cue_count"], first_manifest["cue_count"])
        state = json.loads((self.jw / "job_state.json").read_text(encoding="utf-8"))
        self.assertTrue(state["ocr_cache_hit"])
        progress = (self.jw / "artifacts" / "transcribe" / "ocr_progress.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn("processed_frames=2", progress)
        self.assertIn("total_frames=2", progress)

    # --- skip_ranges (hybrid gap-mode) ---

    def test_skip_ranges_bypasses_ocr_inside_range(self) -> None:
        # 10 frames at 2 fps -> period 500ms, midpoints at 250, 750, 1250, ...
        # skip_ranges = [(0, 2000)] should cover frames 0..3 (times 250, 750, 1250, 1750);
        # frames 4..9 (times 2250..4750) pass to OCR.
        provider = _ScriptedProvider(["gap_text"] * 10)
        with _FakeFrames(10).install(), _patch_probe(), mock.patch.object(
            run_ocr_stage, "_phash", return_value=None
        ):
            manifest = run_ocr_stage.run(
                job_workspace=self.jw,
                language="ch",
                roi={"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.20},
                sample_fps=2.0,
                skip_similarity=2.0,
                min_cue_duration_ms=100,
                min_confidence=0.5,
                device="cpu",
                provider_name="scripted",
                keep_frames=False,
                provider=provider,
                skip_ranges=[(0, 2000)],
            )
        self.assertEqual(manifest["frame_count_total"], 10)
        self.assertEqual(manifest["frame_count_skipped_covered"], 4)
        self.assertEqual(manifest["frame_count_ocr_called"], 6)
        # Cue only spans the uncovered tail (frame 4 at 2250ms onward).
        srt = (self.jw / "artifacts" / "transcribe" / "source_ocr.srt").read_text("utf-8")
        self.assertIn("gap_text", srt)
        self.assertIn("00:00:02,000 --> ", srt)  # cue starts after the skip range

    def test_skip_ranges_empty_list_behaves_like_none(self) -> None:
        provider = _ScriptedProvider(["a", "a", "a"])
        with _FakeFrames(3).install(), _patch_probe(), mock.patch.object(
            run_ocr_stage, "_phash", return_value=None
        ):
            manifest = run_ocr_stage.run(
                job_workspace=self.jw,
                language="ch",
                roi={"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.20},
                sample_fps=2.0,
                skip_similarity=2.0,
                min_cue_duration_ms=100,
                min_confidence=0.5,
                device="cpu",
                provider_name="scripted",
                keep_frames=False,
                provider=provider,
                skip_ranges=[],
            )
        self.assertEqual(manifest["frame_count_skipped_covered"], 0)
        self.assertEqual(manifest["frame_count_ocr_called"], 3)

    def test_skip_ranges_change_invalidates_cache(self) -> None:
        # First run: no skip_ranges. Second run with same params but skip_ranges=[(0, 10_000)]
        # should NOT reuse the first cache — cache key must include skip_ranges.
        first_provider = _ScriptedProvider(["a", "a"])
        with _FakeFrames(2).install(), _patch_probe(), mock.patch.object(
            run_ocr_stage, "_phash", return_value=None
        ):
            first = run_ocr_stage.run(
                job_workspace=self.jw,
                language="ch",
                roi={"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.20},
                sample_fps=2.0,
                skip_similarity=2.0,
                min_cue_duration_ms=100,
                min_confidence=0.5,
                device="cpu",
                provider_name="scripted",
                keep_frames=False,
                provider=first_provider,
            )
        second_provider = _ScriptedProvider(["b", "b"])
        with _FakeFrames(2).install(), _patch_probe(), mock.patch.object(
            run_ocr_stage, "_phash", return_value=None
        ):
            second = run_ocr_stage.run(
                job_workspace=self.jw,
                language="ch",
                roi={"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.20},
                sample_fps=2.0,
                skip_similarity=2.0,
                min_cue_duration_ms=100,
                min_confidence=0.5,
                device="cpu",
                provider_name="scripted",
                keep_frames=False,
                provider=second_provider,
                skip_ranges=[(0, 10_000)],
            )
        self.assertNotEqual(first["cache_key"], second["cache_key"])
        self.assertFalse(second["cache_hit"])
        self.assertEqual(second["frame_count_skipped_covered"], 2)

    def test_normalize_skip_ranges_merges_overlapping(self) -> None:
        out = run_ocr_stage._normalize_skip_ranges(
            [(100, 500), (400, 800), (2000, 2500), (50, 120)]
        )
        self.assertEqual(out, [(50, 800), (2000, 2500)])

    def test_normalize_skip_ranges_drops_invalid(self) -> None:
        out = run_ocr_stage._normalize_skip_ranges(
            [(100, 100), (-50, 200), (500, 400), None, (800, 900)]
        )
        # (100,100) zero-width dropped, (-50,200) clipped to (0,200), (500,400) dropped,
        # None dropped, (800,900) kept.
        self.assertEqual(out, [(0, 200), (800, 900)])

    # --- ROI parser ---

    def test_parse_roi_default_when_empty(self) -> None:
        roi = run_ocr_stage._parse_roi("")
        self.assertEqual(roi, {"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.20})

    def test_parse_roi_rejects_out_of_range(self) -> None:
        with self.assertRaises(ValueError):
            run_ocr_stage._parse_roi('{"x":0,"y":0.5,"w":1.0,"h":0.7}')  # y+h > 1
        with self.assertRaises(ValueError):
            run_ocr_stage._parse_roi('{"x":-0.1,"y":0,"w":0.5,"h":0.5}')

    def test_parse_roi_accepts_custom_band(self) -> None:
        roi = run_ocr_stage._parse_roi('{"x":0.05,"y":0.7,"w":0.9,"h":0.25}')
        self.assertAlmostEqual(roi["x"], 0.05)
        self.assertAlmostEqual(roi["y"], 0.7)


class OcrProviderRegistryTest(unittest.TestCase):
    def test_get_provider_unknown_name_raises(self) -> None:
        from engine.ocr import get_ocr_provider

        with self.assertRaises(ValueError):
            get_ocr_provider("nonexistent_engine")

    def test_get_provider_paddleocr_default(self) -> None:
        from engine.ocr import get_ocr_provider
        from engine.ocr.paddle_provider import PaddleOcrProvider

        provider = get_ocr_provider("paddleocr", device="cpu")
        self.assertIsInstance(provider, PaddleOcrProvider)
        self.assertEqual(provider.device_used(), "cpu")

    def test_get_provider_rapid_alias_maps_to_rapidocr(self) -> None:
        from engine.ocr import get_ocr_provider
        from engine.ocr.rapid_provider import RapidOcrProvider

        provider = get_ocr_provider("rapid", device="cpu")
        self.assertIsInstance(provider, RapidOcrProvider)
        self.assertEqual(provider.name, "rapidocr")


class OcrParseResultTest(unittest.TestCase):
    def test_parse_paddle_result_extracts_text_and_confidence(self) -> None:
        from engine.ocr.paddle_provider import _parse_paddle_result

        # Mimic PaddleOCR shape: [[ [bbox_pts, (text, conf)], ... ]]
        sample = [
            [
                [[[10, 20], [50, 20], [50, 40], [10, 40]], ("你好", 0.91)],
                [[[10, 50], [80, 50], [80, 70], [10, 70]], ("世界", 0.88)],
            ]
        ]
        lines = _parse_paddle_result(sample)
        self.assertEqual([ln.text for ln in lines], ["你好", "世界"])
        self.assertAlmostEqual(lines[0].confidence, 0.91)
        self.assertEqual(lines[0].bbox, (10.0, 20.0, 50.0, 40.0))


class TranscribeOcrOnlyModeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase17_xcb_"))
        self.jw = self.root / "job_xyz"
        (self.jw / "input").mkdir(parents=True)
        (self.jw / "input" / "source.mp4").write_bytes(b"\x00")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_ocr_only_extractor_skips_whisper_and_writes_source_srt(self) -> None:
        from engine import run_ocr_stage, run_transcribe_stage

        provider = _ScriptedProvider(["你好世界", "你好世界"])

        original_run = run_ocr_stage.run

        def patched_run(**kwargs):
            kwargs["provider"] = provider
            kwargs["sample_fps"] = 2.0
            kwargs["skip_similarity"] = 2.0
            kwargs["min_cue_duration_ms"] = 100
            return original_run(**kwargs)

        with _FakeFrames(2).install(), _patch_probe(), mock.patch.object(
            run_ocr_stage, "_phash", return_value=None
        ), mock.patch.object(run_ocr_stage, "run", side_effect=patched_run):
            rc = run_transcribe_stage.main(
                [
                    "--job-workspace",
                    str(self.jw),
                    "--extractor",
                    "ocr_only",
                    "--ocr-language",
                    "ch",
                    "--ocr-device",
                    "cpu",
                ]
            )
        self.assertEqual(rc, 0)
        out_srt = self.jw / "artifacts" / "transcribe" / "source.srt"
        ocr_srt = self.jw / "artifacts" / "transcribe" / "source_ocr.srt"
        self.assertTrue(out_srt.is_file())
        self.assertTrue(ocr_srt.is_file())
        self.assertEqual(out_srt.read_text(encoding="utf-8"), ocr_srt.read_text(encoding="utf-8"))

        state = json.loads((self.jw / "job_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["current_stage"], "transcribed")
        self.assertEqual(state["subtitle_extractor"], "ocr_only")
        self.assertTrue(state["transcription_engine"].startswith("ocr:"))

    def test_hybrid_extractor_fails_gracefully_when_both_engines_missing(self) -> None:
        # Without faster-whisper and paddleocr installed, hybrid mode should fail
        # with current_stage=transcribe_failed (not raise). End-to-end success is
        # covered by test_phase17_extractor_modes with mocked engines.
        from engine import run_transcribe_stage

        with mock.patch(
            "engine.run_transcribe_stage._run_asr_to_srt",
            side_effect=RuntimeError("faster_whisper missing"),
        ), mock.patch(
            "engine.run_ocr_stage.run", side_effect=RuntimeError("paddleocr missing")
        ):
            rc = run_transcribe_stage.main(
                ["--job-workspace", str(self.jw), "--extractor", "hybrid"]
            )
        self.assertEqual(rc, 1)
        state = json.loads((self.jw / "job_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["current_stage"], "transcribe_failed")


class OcrPreflightTest(unittest.TestCase):
    def test_require_ocr_flags_missing_paddleocr(self) -> None:
        from engine.preflight import build_preflight_report

        def fake_find_spec(name: str):
            # Allow everything EXCEPT paddle/paddleocr.
            if name in ("paddle", "paddleocr"):
                return None
            return object()

        with mock.patch("engine.preflight.importlib.util.find_spec", side_effect=fake_find_spec), \
                mock.patch(
                    "engine.preflight.resolve_ffmpeg_executable", return_value=("ffmpeg", None)
                ), \
                mock.patch(
                    "engine.preflight.subprocess.run",
                    return_value=SimpleNamespace(
                        returncode=0, stdout="ffmpeg version 6.1\n", stderr=""
                    ),
                ):
            report = build_preflight_report(
                translate_backend="legacy",
                tts_provider="edge_tts",
                require_ocr=True,
            )
        checks = {c["name"]: c for c in report["checks"]}
        self.assertIn("ocr_provider", checks)
        self.assertIn("paddleocr_package", checks)
        self.assertTrue(checks["ocr_provider"]["ok"])
        self.assertFalse(checks["paddleocr_package"]["ok"])
        self.assertFalse(report["capabilities"]["ocr_ready"])
        self.assertFalse(report["ok"])

    def test_no_ocr_checks_when_not_required(self) -> None:
        from engine.preflight import build_preflight_report

        with mock.patch(
            "engine.preflight.importlib.util.find_spec", return_value=object()
        ), mock.patch(
            "engine.preflight.resolve_ffmpeg_executable", return_value=("ffmpeg", None)
        ), mock.patch(
            "engine.preflight.subprocess.run",
            return_value=SimpleNamespace(
                returncode=0, stdout="ffmpeg version 6.1\n", stderr=""
            ),
        ):
            report = build_preflight_report(
                translate_backend="legacy",
                tts_provider="edge_tts",
            )
        names = {c["name"] for c in report["checks"]}
        self.assertNotIn("ocr_provider", names)
        self.assertNotIn("paddleocr_package", names)
        self.assertTrue(report["capabilities"]["ocr_ready"])

    def test_require_ocr_supports_rapidocr_provider(self) -> None:
        from engine.preflight import build_preflight_report

        def fake_find_spec(name: str):
            if name == "rapidocr_onnxruntime":
                return object()
            if name in {"edge_tts", "onnxruntime"}:
                return object()
            return None

        fake_ort = SimpleNamespace(get_available_providers=lambda: ["CPUExecutionProvider"])

        with mock.patch("engine.preflight.importlib.util.find_spec", side_effect=fake_find_spec), \
                mock.patch.dict("sys.modules", {"onnxruntime": fake_ort}, clear=False), \
                mock.patch(
                    "engine.preflight.resolve_ffmpeg_executable", return_value=("ffmpeg", None)
                ), \
                mock.patch(
                    "engine.preflight.subprocess.run",
                    return_value=SimpleNamespace(
                        returncode=0, stdout="ffmpeg version 6.1\n", stderr=""
                    ),
                ):
            report = build_preflight_report(
                translate_backend="legacy",
                tts_provider="edge_tts",
                require_ocr=True,
                ocr_provider="rapidocr",
            )

        checks = {c["name"]: c for c in report["checks"]}
        self.assertTrue(checks["ocr_provider"]["ok"])
        self.assertTrue(checks["rapidocr_package"]["ok"])
        self.assertTrue(report["capabilities"]["ocr_ready"])


if __name__ == "__main__":
    unittest.main()
