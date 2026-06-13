"""Phase B end-to-end tests for the three --extractor modes on run_transcribe_stage.

All external engines (faster_whisper, PaddleOCR, ffmpeg frame extraction) are mocked:
- `_run_asr_to_srt` is patched to write a fixed SRT and return a small metadata dict.
- `run_ocr_stage.run` is patched to write a fixed SRT and return a manifest dict.

We then assert job_state.json, video_state.json, and canonical artifact files.
Parallel execution (B6) is verified by making both mocks sleep and checking wall-clock
is closer to max(t_asr, t_ocr) than sum(t_asr, t_ocr).
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


_ASR_SRT = (
    "1\n00:00:01,000 --> 00:00:02,000\nhello world\n\n"
    "2\n00:00:05,000 --> 00:00:06,000\nfinal asr line\n"
)

_OCR_SRT = (
    "1\n00:00:01,050 --> 00:00:02,100\nhello world\n\n"
    "2\n00:00:08,000 --> 00:00:09,000\nocr only line\n"
)


def _make_fake_asr(srt_body: str = _ASR_SRT, *, sleep_s: float = 0.0):
    def _fake(ns, job_workspace: Path, out_srt: Path, *, report_path=None):
        if sleep_s:
            time.sleep(sleep_s)
        out_srt.parent.mkdir(parents=True, exist_ok=True)
        out_srt.write_text(srt_body, encoding="utf-8")
        report = {"segment_count": srt_body.count("-->"), "transcription_coverage_ratio": 1.0}
        if report_path is not None:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report), encoding="utf-8")
        return {
            "device": "cpu",
            "compute_type": "int8",
            "language": None,
            "segment_count": report["segment_count"],
            "report": report,
        }

    return _fake


def _make_fake_ocr(srt_body: str = _OCR_SRT, *, sleep_s: float = 0.0):
    def _fake(**kwargs):
        if sleep_s:
            time.sleep(sleep_s)
        jw: Path = kwargs["job_workspace"]
        transcribe_dir = jw / "artifacts" / "transcribe"
        transcribe_dir.mkdir(parents=True, exist_ok=True)
        (transcribe_dir / "source_ocr.srt").write_text(srt_body, encoding="utf-8")
        manifest = {
            "provider": "scripted",
            "language": kwargs.get("language", "ch"),
            "cue_count": srt_body.count("-->"),
            "ocr_device_used": "cpu",
            "roi": kwargs.get("roi"),
        }
        (transcribe_dir / "ocr_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )
        return manifest

    return _fake


class ExtractorModesEndToEndTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase17_modes_"))
        self.jw = self.root / "job_zzz"
        (self.jw / "input").mkdir(parents=True)
        (self.jw / "input" / "source.mp4").write_bytes(b"\x00")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_audio_only_writes_source_srt_via_asr_helper(self) -> None:
        from engine import run_transcribe_stage

        with mock.patch.object(
            run_transcribe_stage, "_run_asr_to_srt", side_effect=_make_fake_asr()
        ):
            rc = run_transcribe_stage.main(
                ["--job-workspace", str(self.jw), "--extractor", "audio_only"]
            )
        self.assertEqual(rc, 0)
        out_srt = self.jw / "artifacts" / "transcribe" / "source.srt"
        self.assertTrue(out_srt.is_file())
        self.assertIn("hello world", out_srt.read_text(encoding="utf-8"))
        state = json.loads((self.jw / "job_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["subtitle_extractor"], "audio_only")
        self.assertEqual(state["transcription_engine"], "faster_whisper")

    def test_ocr_only_writes_source_srt_via_ocr_helper(self) -> None:
        from engine import run_transcribe_stage, run_ocr_stage

        with mock.patch.object(run_ocr_stage, "run", side_effect=_make_fake_ocr()):
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
        self.assertEqual(out_srt.read_text(encoding="utf-8"), ocr_srt.read_text(encoding="utf-8"))
        state = json.loads((self.jw / "job_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["subtitle_extractor"], "ocr_only")
        self.assertTrue(state["transcription_engine"].startswith("ocr:"))

    def test_hybrid_writes_source_srt_plus_provenance(self) -> None:
        from engine import run_transcribe_stage, run_ocr_stage

        with mock.patch.object(
            run_transcribe_stage, "_run_asr_to_srt", side_effect=_make_fake_asr()
        ), mock.patch.object(run_ocr_stage, "run", side_effect=_make_fake_ocr()):
            rc = run_transcribe_stage.main(
                ["--job-workspace", str(self.jw), "--extractor", "hybrid"]
            )
        self.assertEqual(rc, 0)

        transcribe_dir = self.jw / "artifacts" / "transcribe"
        self.assertTrue((transcribe_dir / "source.srt").is_file())
        self.assertTrue((transcribe_dir / "source_audio.srt").is_file())
        self.assertTrue((transcribe_dir / "source_ocr.srt").is_file())
        self.assertTrue((transcribe_dir / "source_provenance.json").is_file())

        prov = json.loads((transcribe_dir / "source_provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(prov["extractor"], "hybrid")
        self.assertEqual(prov["asr_cue_count"], 2)
        self.assertEqual(prov["ocr_cue_count"], 2)
        # One fused_match (hello world), two standalone (final asr line, ocr only line).
        self.assertEqual(prov["final_cue_count"], 3)
        sources = sorted(c["source"] for c in prov["cues"])
        self.assertEqual(sources, ["asr", "fused_match", "ocr"])

        state = json.loads((self.jw / "job_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["subtitle_extractor"], "hybrid")
        self.assertTrue(state["transcription_engine"].startswith("hybrid:"))

    def test_hybrid_survives_ocr_failure_with_asr_only(self) -> None:
        from engine import run_transcribe_stage, run_ocr_stage

        with mock.patch.object(
            run_transcribe_stage, "_run_asr_to_srt", side_effect=_make_fake_asr()
        ), mock.patch.object(
            run_ocr_stage, "run", side_effect=RuntimeError("OCR engine crashed")
        ):
            rc = run_transcribe_stage.main(
                ["--job-workspace", str(self.jw), "--extractor", "hybrid"]
            )
        # Hybrid still succeeds with ASR-only results fused (no OCR cues).
        self.assertEqual(rc, 0)
        prov = json.loads(
            (self.jw / "artifacts" / "transcribe" / "source_provenance.json").read_text("utf-8")
        )
        self.assertEqual(prov["ocr_cue_count"], 0)
        self.assertEqual(prov["asr_cue_count"], 2)
        self.assertEqual(prov["final_cue_count"], 2)
        for cue in prov["cues"]:
            self.assertEqual(cue["source"], "asr")

    def test_hybrid_fails_when_both_engines_error(self) -> None:
        from engine import run_transcribe_stage, run_ocr_stage

        with mock.patch.object(
            run_transcribe_stage, "_run_asr_to_srt",
            side_effect=RuntimeError("whisper boom"),
        ), mock.patch.object(
            run_ocr_stage, "run", side_effect=RuntimeError("paddle boom")
        ):
            rc = run_transcribe_stage.main(
                ["--job-workspace", str(self.jw), "--extractor", "hybrid"]
            )
        self.assertEqual(rc, 1)
        state = json.loads((self.jw / "job_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["current_stage"], "transcribe_failed")

    def test_hybrid_full_mode_runs_asr_and_ocr_in_parallel(self) -> None:
        """B6: wall-clock for parallel ('full') mode must be < sum of sequential times."""
        from engine import run_transcribe_stage, run_ocr_stage

        sleep_s = 0.3

        with mock.patch.object(
            run_transcribe_stage, "_run_asr_to_srt",
            side_effect=_make_fake_asr(sleep_s=sleep_s),
        ), mock.patch.object(
            run_ocr_stage, "run", side_effect=_make_fake_ocr(sleep_s=sleep_s)
        ):
            t0 = time.monotonic()
            rc = run_transcribe_stage.main(
                [
                    "--job-workspace", str(self.jw),
                    "--extractor", "hybrid",
                    "--hybrid-ocr-mode", "full",
                ]
            )
            elapsed = time.monotonic() - t0

        self.assertEqual(rc, 0)
        # Sequential would be ~2*sleep; parallel should be closer to sleep.
        # Leave generous headroom: accept < 1.6*sleep (vs 2.0*sleep sequential).
        self.assertLess(
            elapsed,
            1.6 * sleep_s,
            msg=f"hybrid(full) did not run ASR+OCR in parallel: elapsed={elapsed:.3f}s",
        )

    def test_hybrid_full_threads_overlap_detected_by_concurrent_peak(self) -> None:
        """Stronger parallelism check for --hybrid-ocr-mode full."""
        from engine import run_transcribe_stage, run_ocr_stage

        in_flight = 0
        peak = 0
        lock = threading.Lock()

        def _busy(duration_s: float):
            nonlocal in_flight, peak
            with lock:
                in_flight += 1
                peak = max(peak, in_flight)
            time.sleep(duration_s)
            with lock:
                in_flight -= 1

        def asr_side(ns, jw, out_srt, *, report_path=None):
            _busy(0.25)
            return _make_fake_asr()(ns, jw, out_srt, report_path=report_path)

        def ocr_side(**kwargs):
            _busy(0.25)
            return _make_fake_ocr()(**kwargs)

        with mock.patch.object(run_transcribe_stage, "_run_asr_to_srt", side_effect=asr_side), \
                mock.patch.object(run_ocr_stage, "run", side_effect=ocr_side):
            rc = run_transcribe_stage.main(
                [
                    "--job-workspace", str(self.jw),
                    "--extractor", "hybrid",
                    "--hybrid-ocr-mode", "full",
                ]
            )
        self.assertEqual(rc, 0)
        self.assertEqual(peak, 2, f"ASR and OCR should have been in-flight together; peak={peak}")

    def test_hybrid_gaps_mode_runs_asr_before_ocr_and_passes_skip_ranges(self) -> None:
        """gaps mode: ASR finishes before OCR starts; skip_ranges reach run_ocr_stage.run."""
        from engine import run_transcribe_stage, run_ocr_stage

        order: list[str] = []
        captured_kwargs: dict = {}

        def asr_side(ns, jw, out_srt, *, report_path=None):
            order.append("asr_start")
            result = _make_fake_asr()(ns, jw, out_srt, report_path=report_path)
            order.append("asr_end")
            return result

        def ocr_side(**kwargs):
            order.append("ocr_start")
            captured_kwargs.update(kwargs)
            result = _make_fake_ocr()(**kwargs)
            order.append("ocr_end")
            return result

        with mock.patch.object(run_transcribe_stage, "_run_asr_to_srt", side_effect=asr_side), \
                mock.patch.object(run_ocr_stage, "run", side_effect=ocr_side), \
                mock.patch.object(
                    run_transcribe_stage, "_probe_video_duration_ms", return_value=10_000
                ):
            rc = run_transcribe_stage.main(
                ["--job-workspace", str(self.jw), "--extractor", "hybrid"]
            )
        self.assertEqual(rc, 0)
        # ASR must finish before OCR starts.
        self.assertEqual(order[:2], ["asr_start", "asr_end"])
        self.assertEqual(order[2], "ocr_start")
        # skip_ranges kwarg must be a non-empty list of (start,end) tuples derived from ASR.
        skip = captured_kwargs.get("skip_ranges")
        self.assertIsInstance(skip, list)
        self.assertTrue(skip, "gaps mode should pass a non-empty skip_ranges")
        for s, e in skip:
            self.assertLess(s, e)

    def test_hybrid_gaps_mode_falls_back_to_full_ocr_when_asr_fails(self) -> None:
        """If ASR fails in gaps mode, OCR still runs with skip_ranges=None (full scan)."""
        from engine import run_transcribe_stage, run_ocr_stage

        captured_kwargs: dict = {}

        def ocr_side(**kwargs):
            captured_kwargs.update(kwargs)
            return _make_fake_ocr()(**kwargs)

        with mock.patch.object(
            run_transcribe_stage, "_run_asr_to_srt",
            side_effect=RuntimeError("whisper missing"),
        ), mock.patch.object(run_ocr_stage, "run", side_effect=ocr_side):
            rc = run_transcribe_stage.main(
                ["--job-workspace", str(self.jw), "--extractor", "hybrid"]
            )
        self.assertEqual(rc, 0)
        # skip_ranges should be None (or empty) — OCR scans the whole video.
        self.assertFalse(captured_kwargs.get("skip_ranges"))


class HybridHelperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase17_helpers_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_asr_covered_ranges_ms_pads_and_merges(self) -> None:
        from engine import run_transcribe_stage

        srt = self.root / "a.srt"
        # Two cues: (1000,2000) and (2100,3000). With pad=200 they become
        # (800,2200) and (1900,3200) which merge into (800, 3200).
        srt.write_text(
            "1\n00:00:01,000 --> 00:00:02,000\nalpha\n\n"
            "2\n00:00:02,100 --> 00:00:03,000\nbeta\n",
            encoding="utf-8",
        )
        ranges = run_transcribe_stage._asr_covered_ranges_ms(srt, pad_ms=200)
        self.assertEqual(ranges, [(800, 3200)])

    def test_asr_covered_ranges_ms_empty_for_missing_file(self) -> None:
        from engine import run_transcribe_stage

        missing = self.root / "does_not_exist.srt"
        self.assertEqual(run_transcribe_stage._asr_covered_ranges_ms(missing), [])

    def test_filter_short_gaps_absorbs_tiny_gaps(self) -> None:
        from engine import run_transcribe_stage

        # Gap of 300ms between (0,1000) and (1300,2000) < min_gap 500 -> merge.
        merged = run_transcribe_stage._filter_short_gaps(
            [(0, 1000), (1300, 2000), (5000, 6000)],
            video_duration_ms=6500,
            min_gap_ms=500,
        )
        # (0,2000) merged; (5000,6000) kept as-is; tail gap 500ms to end is NOT < 500.
        self.assertEqual(merged, [(0, 2000), (5000, 6000)])

    def test_filter_short_gaps_extends_to_video_end_when_tail_is_short(self) -> None:
        from engine import run_transcribe_stage

        merged = run_transcribe_stage._filter_short_gaps(
            [(0, 5000)], video_duration_ms=5200, min_gap_ms=500
        )
        self.assertEqual(merged, [(0, 5200)])


if __name__ == "__main__":
    unittest.main()
