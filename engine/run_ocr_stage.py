"""
Legacy module — not used by the current desktop UI flow (2026 pivot to ASR + import SRT).
You may still invoke this stage directly via CLI for research or batch OCR experiments.

Extract subtitles from a video by OCR over sampled frames.

Inputs:
- input/source.mp4 (required)

Outputs:
- artifacts/transcribe/source_ocr.srt
- artifacts/transcribe/ocr_manifest.json
- artifacts/transcribe/ocr_progress.txt    (live progress: processed_frames=N\ntotal_frames=M)

The stage is intentionally provider-agnostic: it consumes an `OcrProvider` (default
PaddleOCR) and a deterministic frame-sampling pipeline driven by ffmpeg.
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from engine.ffmpeg_bins import resolve_ffmpeg_executable, resolve_ffprobe_executable
from engine.ocr import canonical_provider_name, get_ocr_provider
from engine.ocr.base import OcrFrameResult, OcrProvider


_DEFAULT_ROI = {"x": 0.0, "y": 0.78, "w": 1.0, "h": 0.20}


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="OCR-based subtitle extraction stage.")
    p.add_argument("--job-workspace", required=True, help="Job / video workspace root.")
    p.add_argument("--language", default="ch", help="OCR language (paddle codes: ch, en, vi, japan...).")
    p.add_argument(
        "--roi",
        default="",
        help='ROI JSON {"x":0.0,"y":0.78,"w":1.0,"h":0.20} — values 0..1 of frame size.',
    )
    p.add_argument("--sample-fps", type=float, default=2.5, help="Frames per second to sample (default 2.5).")
    p.add_argument(
        "--frame-skip-similarity",
        type=float,
        default=0.98,
        help="Skip frame if pHash similarity to previous kept frame >= this (default 0.98).",
    )
    p.add_argument("--min-cue-duration-ms", type=int, default=300, help="Drop cues shorter than this (default 300ms).")
    p.add_argument("--min-confidence", type=float, default=0.6, help="Drop OCR lines below this confidence.")
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"], help="OCR device (default auto).")
    p.add_argument("--provider", default="paddleocr", help="OCR provider name (default paddleocr).")
    p.add_argument("--keep-frames", action="store_true", help="Keep cache/ocr_frames/ for debugging.")
    return p.parse_args(argv)


@dataclass
class _SampledFrame:
    index: int
    time_ms: int
    path: Path


def _load_job_state(job_workspace: Path) -> dict:
    p = job_workspace / "job_state.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _merge_job_state(job_workspace: Path, updates: dict) -> None:
    path = job_workspace / "job_state.json"
    base = _load_job_state(job_workspace)
    base.update(updates)
    write_json_atomic(path, base)


def _parse_roi(raw: str) -> dict[str, float]:
    if not raw:
        return dict(_DEFAULT_ROI)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--roi is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("--roi must be a JSON object with keys x,y,w,h.")
    out = {}
    for key in ("x", "y", "w", "h"):
        if key not in data:
            raise ValueError(f"--roi missing key {key!r}.")
        try:
            val = float(data[key])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"--roi.{key} not numeric: {data[key]!r}") from exc
        if val < 0.0 or val > 1.0:
            raise ValueError(f"--roi.{key}={val} out of range [0,1].")
        out[key] = val
    if out["x"] + out["w"] > 1.0001:
        raise ValueError(f"--roi x+w={out['x']+out['w']} exceeds 1.0.")
    if out["y"] + out["h"] > 1.0001:
        raise ValueError(f"--roi y+h={out['y']+out['h']} exceeds 1.0.")
    if out["w"] <= 0 or out["h"] <= 0:
        raise ValueError("--roi width/height must be > 0.")
    return out


def _probe_video(video_path: Path) -> tuple[float, int, int]:
    """Returns (duration_seconds, width, height)."""
    ffprobe = resolve_ffprobe_executable()
    if not ffprobe:
        raise RuntimeError("ffprobe not found: set FFPROBE_BIN or install ffprobe.")
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height:format=duration",
        "-of",
        "json",
        str(video_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {(proc.stderr or proc.stdout or '').strip()[:300]}")
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe JSON parse failed: {exc}") from exc
    streams = data.get("streams") or []
    if not streams:
        raise RuntimeError("ffprobe found no video streams.")
    width = int(streams[0].get("width") or 0)
    height = int(streams[0].get("height") or 0)
    duration = float((data.get("format") or {}).get("duration") or 0.0)
    if width <= 0 or height <= 0 or duration <= 0:
        raise RuntimeError(f"ffprobe returned invalid metadata: w={width} h={height} dur={duration}")
    return duration, width, height


def _extract_frames(
    video_path: Path,
    *,
    out_dir: Path,
    roi: dict[str, float],
    width: int,
    height: int,
    sample_fps: float,
) -> None:
    ffmpeg, err = resolve_ffmpeg_executable()
    if ffmpeg is None:
        raise RuntimeError(err or "ffmpeg not found.")

    out_dir.mkdir(parents=True, exist_ok=True)
    crop_w = max(2, int(round(width * roi["w"])) // 2 * 2)
    crop_h = max(2, int(round(height * roi["h"])) // 2 * 2)
    crop_x = max(0, int(round(width * roi["x"])))
    crop_y = max(0, int(round(height * roi["y"])))
    if crop_x + crop_w > width:
        crop_w = (width - crop_x) // 2 * 2
    if crop_y + crop_h > height:
        crop_h = (height - crop_y) // 2 * 2

    vf = f"fps={sample_fps:.6g},crop={crop_w}:{crop_h}:{crop_x}:{crop_y}"
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        vf,
        "-vsync",
        "vfr",
        str(out_dir / "frame_%06d.png"),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-2000:]
        raise RuntimeError(f"ffmpeg frame extraction failed (exit {proc.returncode}): {tail}")


def _list_sampled_frames(out_dir: Path, sample_fps: float) -> list[_SampledFrame]:
    frames = sorted(out_dir.glob("frame_*.png"))
    period_ms = 1000.0 / max(sample_fps, 0.001)
    out: list[_SampledFrame] = []
    for i, p in enumerate(frames):
        # frame N in 1-based ffmpeg numbering -> midpoint at (N-0.5)*period_ms
        t_ms = int(round((i + 0.5) * period_ms))
        out.append(_SampledFrame(index=i, time_ms=t_ms, path=p))
    return out


def _phash(path: Path, *, size: int = 16) -> int | None:
    """Tiny dHash on a 16x16 downscale; returns None if PIL not installed."""
    try:
        from PIL import Image
    except Exception:
        return None
    try:
        with Image.open(path) as im:
            im = im.convert("L").resize((size + 1, size), Image.BILINEAR)
            pixels = list(im.getdata())
    except Exception:
        return None
    bits = 0
    for row in range(size):
        base = row * (size + 1)
        for col in range(size):
            left = pixels[base + col]
            right = pixels[base + col + 1]
            bits = (bits << 1) | (1 if left > right else 0)
    return bits


def _hamming_similarity(a: int | None, b: int | None, *, total_bits: int = 16 * 16) -> float:
    if a is None or b is None:
        return 0.0
    diff = a ^ b
    distance = bin(diff).count("1")
    return 1.0 - (distance / float(total_bits))


def _norm_text(s: str) -> str:
    return " ".join((s or "").split())


def _levenshtein_normalized(a: str, b: str) -> float:
    if not a and not b:
        return 0.0
    if not a or not b:
        return 1.0
    if a == b:
        return 0.0
    la, lb = len(a), len(b)
    if la < lb:
        a, b = b, a
        la, lb = lb, la
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i] + [0] * lb
        for j, cb in enumerate(b, start=1):
            ins = curr[j - 1] + 1
            dele = prev[j] + 1
            sub = prev[j - 1] + (0 if ca == cb else 1)
            curr[j] = min(ins, dele, sub)
        prev = curr
    return prev[lb] / float(max(la, 1))


@dataclass
class _Cue:
    start_ms: int
    end_ms: int
    text: str
    confidence: float


def _group_into_cues(
    samples: Iterable[tuple[_SampledFrame, OcrFrameResult]],
    *,
    sample_fps: float,
    min_confidence: float,
    min_cue_duration_ms: int,
    text_drift_threshold: float = 0.10,
) -> list[_Cue]:
    period_ms = int(round(1000.0 / max(sample_fps, 0.001)))
    cues: list[_Cue] = []
    cur_text: str | None = None
    cur_start: int = 0
    cur_end: int = 0
    cur_confs: list[float] = []

    def flush() -> None:
        nonlocal cur_text, cur_confs
        if cur_text is None:
            return
        text = cur_text.strip()
        avg_conf = sum(cur_confs) / len(cur_confs) if cur_confs else 0.0
        duration = cur_end - cur_start
        if (
            text
            and len(text) >= 2
            and avg_conf >= min_confidence
            and duration >= min_cue_duration_ms
        ):
            cues.append(_Cue(start_ms=cur_start, end_ms=cur_end, text=text, confidence=avg_conf))
        cur_text = None
        cur_confs = []

    for frame, result in samples:
        text = _norm_text(result.joined_text)
        conf = float(result.mean_confidence)
        if not text or conf < min_confidence:
            flush()
            continue
        if cur_text is None:
            cur_text = text
            cur_start = max(0, frame.time_ms - period_ms // 2)
            cur_end = frame.time_ms + period_ms // 2
            cur_confs = [conf]
            continue
        diff = _levenshtein_normalized(cur_text, text)
        if diff <= text_drift_threshold:
            cur_end = frame.time_ms + period_ms // 2
            cur_confs.append(conf)
            if conf > (cur_confs[0] if cur_confs else 0.0):
                cur_text = text
        else:
            flush()
            cur_text = text
            cur_start = max(0, frame.time_ms - period_ms // 2)
            cur_end = frame.time_ms + period_ms // 2
            cur_confs = [conf]
    flush()
    return cues


def _srt_timestamp(ms: int) -> str:
    ms = max(0, int(ms))
    h = ms // 3_600_000
    rem = ms - h * 3_600_000
    m = rem // 60_000
    rem -= m * 60_000
    s = rem // 1000
    ms_part = rem - s * 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms_part:03d}"


def _cues_to_srt(cues: list[_Cue]) -> str:
    out: list[str] = []
    for i, cue in enumerate(cues, start=1):
        out.append(str(i))
        out.append(f"{_srt_timestamp(cue.start_ms)} --> {_srt_timestamp(cue.end_ms)}")
        out.append(cue.text)
        out.append("")
    return "\n".join(out).rstrip() + ("\n" if out else "")


def _write_progress(progress_path: Path, processed: int, total: int) -> None:
    try:
        progress_path.write_text(
            f"processed_frames={processed}\ntotal_frames={total}\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def _fail(job_workspace: Path, job_id: str, message: str) -> None:
    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "failed",
            "current_stage": "ocr_failed",
            "last_error": message,
        },
    )


def _video_fingerprint_short(video_path: Path) -> str:
    h = hashlib.sha1()
    h.update(str(video_path.resolve()).encode("utf-8"))
    try:
        st = video_path.stat()
        h.update(str(st.st_size).encode("utf-8"))
        h.update(str(int(st.st_mtime)).encode("utf-8"))
    except OSError:
        pass
    return h.hexdigest()[:16]


def _cache_key(
    *,
    fingerprint: str,
    provider_name: str,
    language: str,
    device: str,
    roi: dict[str, float],
    sample_fps: float,
    skip_similarity: float,
    min_cue_duration_ms: int,
    min_confidence: float,
    skip_ranges: list[tuple[int, int]] | None = None,
) -> str:
    payload = json.dumps(
        {
            "fp": fingerprint,
            "provider": (provider_name or "").strip().lower(),
            "lang": (language or "").strip().lower(),
            "device": (device or "").strip().lower(),
            "roi": {k: round(float(roi.get(k, 0.0)), 6) for k in ("x", "y", "w", "h")},
            "sample_fps": round(float(sample_fps), 4),
            "skip_similarity": round(float(skip_similarity), 4),
            "min_cue_duration_ms": int(min_cue_duration_ms),
            "min_confidence": round(float(min_confidence), 4),
            "skip_ranges": [[int(s), int(e)] for s, e in (skip_ranges or [])],
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:20]


def _normalize_skip_ranges(
    ranges: list[tuple[int, int]] | None,
) -> list[tuple[int, int]]:
    """Sort, clip, and merge overlapping (start_ms, end_ms) ranges."""
    if not ranges:
        return []
    cleaned: list[tuple[int, int]] = []
    for r in ranges:
        if r is None:
            continue
        try:
            s = int(r[0])
            e = int(r[1])
        except (TypeError, ValueError, IndexError):
            continue
        if e <= s:
            continue
        cleaned.append((max(0, s), e))
    if not cleaned:
        return []
    cleaned.sort()
    merged: list[tuple[int, int]] = [cleaned[0]]
    for s, e in cleaned[1:]:
        ps, pe = merged[-1]
        if s <= pe:
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))
    return merged


def _time_in_ranges(t_ms: int, ranges: list[tuple[int, int]]) -> bool:
    """Linear scan — range count is small (tens to low hundreds)."""
    for s, e in ranges:
        if t_ms < s:
            return False
        if t_ms <= e:
            return True
    return False


def _cache_dir(job_workspace: Path, key: str) -> Path:
    return job_workspace / "cache" / "ocr_cache" / key


def _try_load_cache(cache_dir: Path) -> dict | None:
    srt_path = cache_dir / "source_ocr.srt"
    manifest_path = cache_dir / "ocr_manifest.json"
    if not (srt_path.is_file() and manifest_path.is_file()):
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(manifest, dict):
        return None
    return manifest


def _save_cache(
    cache_dir: Path,
    *,
    srt_text: str,
    manifest: dict,
) -> None:
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "source_ocr.srt").write_text(srt_text, encoding="utf-8")
        (cache_dir / "ocr_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def run(
    *,
    job_workspace: Path,
    language: str,
    roi: dict[str, float],
    sample_fps: float,
    skip_similarity: float,
    min_cue_duration_ms: int,
    min_confidence: float,
    device: str,
    provider_name: str,
    keep_frames: bool,
    provider: OcrProvider | None = None,
    skip_ranges: list[tuple[int, int]] | None = None,
) -> dict:
    """Programmatic entry-point used by the CLI and by tests (with a mock provider).

    ``skip_ranges`` is an optional list of (start_ms, end_ms) regions that
    should be treated as already covered (e.g. by ASR in hybrid mode). Frames
    whose timestamp falls inside one of these ranges are not sent to the OCR
    provider — they are recorded as empty results so the cue grouper splits
    around them. This lets hybrid mode OCR only the audio-gap regions.
    """
    job_id = job_workspace.name
    input_mp4 = job_workspace / "input" / "source.mp4"
    if not input_mp4.is_file():
        raise FileNotFoundError(f"Missing canonical input video: {input_mp4}")

    skip_ranges_norm = _normalize_skip_ranges(skip_ranges)

    provider_label = canonical_provider_name(provider_name)
    if provider is not None and getattr(provider, "name", ""):
        provider_label = canonical_provider_name(provider.name) or str(provider.name).strip().lower()
    if not provider_label:
        provider_label = str(provider_name or "").strip().lower().replace("-", "_")
    if not provider_label:
        provider_label = "paddleocr"

    transcribe_dir = job_workspace / "artifacts" / "transcribe"
    transcribe_dir.mkdir(parents=True, exist_ok=True)
    out_srt = transcribe_dir / "source_ocr.srt"
    manifest_path = transcribe_dir / "ocr_manifest.json"
    progress_path = transcribe_dir / "ocr_progress.txt"

    duration_s, width, height = _probe_video(input_mp4)
    fingerprint = _video_fingerprint_short(input_mp4)
    cache_key = _cache_key(
        fingerprint=fingerprint,
        provider_name=provider_label,
        language=language,
        device=device,
        roi=roi,
        sample_fps=sample_fps,
        skip_similarity=skip_similarity,
        min_cue_duration_ms=min_cue_duration_ms,
        min_confidence=min_confidence,
        skip_ranges=skip_ranges_norm,
    )
    cache_dir = _cache_dir(job_workspace, cache_key)
    cached = _try_load_cache(cache_dir)
    if cached is not None:
        cached_srt = (cache_dir / "source_ocr.srt").read_text(encoding="utf-8")
        out_srt.write_text(cached_srt, encoding="utf-8")
        manifest = dict(cached)
        manifest["cache_hit"] = True
        manifest["cache_key"] = cache_key
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        total = int(manifest.get("frame_count_total") or 1) or 1
        _write_progress(progress_path, total, total)
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "ocr_provider": provider_label,
                "ocr_language": language,
                "ocr_roi": roi,
                "ocr_device_requested": device,
                "ocr_device_used": str(manifest.get("ocr_device_used") or "cpu"),
                "ocr_output_srt": str(out_srt.resolve()),
                "ocr_cache_hit": True,
            },
        )
        return manifest

    cache_root = job_workspace / "cache" / "ocr_frames"
    if cache_root.exists():
        shutil.rmtree(cache_root, ignore_errors=True)
    cache_root.mkdir(parents=True, exist_ok=True)

    _write_progress(progress_path, 0, max(1, int(duration_s * sample_fps)))

    _extract_frames(
        input_mp4,
        out_dir=cache_root,
        roi=roi,
        width=width,
        height=height,
        sample_fps=sample_fps,
    )
    sampled = _list_sampled_frames(cache_root, sample_fps)
    total_frames = len(sampled)
    _write_progress(progress_path, 0, max(total_frames, 1))

    if provider is None:
        provider = get_ocr_provider(provider_label, device=device)

    started = time.time()
    last_hash: int | None = None
    last_kept_result: OcrFrameResult | None = None
    samples_for_grouping: list[tuple[_SampledFrame, OcrFrameResult]] = []

    skipped_similar = 0
    skipped_covered = 0
    ocr_calls = 0
    last_progress_write = 0.0
    last_console_log = started
    console_log_interval_s = 10.0
    coverage_note = ""
    if skip_ranges_norm:
        covered_ms = sum(e - s for s, e in skip_ranges_norm)
        coverage_note = (
            f" skip_ranges={len(skip_ranges_norm)} covering ~{covered_ms / 1000.0:.1f}s"
        )
    print(
        f"[ocr] processing {total_frames} sampled frames (provider={provider_label}, "
        f"device={provider.device_used() if hasattr(provider, 'device_used') else 'unknown'}){coverage_note}.",
        file=sys.stderr,
        flush=True,
    )
    empty_covered_result = OcrFrameResult(lines=[], device_used="skipped_covered")
    for idx, frame in enumerate(sampled):
        in_skip = skip_ranges_norm and _time_in_ranges(frame.time_ms, skip_ranges_norm)
        if in_skip:
            # ASR (or another extractor) already covers this time window.
            # Emit an empty result so the grouper breaks any running cue and
            # reset the dedup chain so the first frame after the gap is OCR'd.
            samples_for_grouping.append((frame, empty_covered_result))
            skipped_covered += 1
            last_hash = None
            last_kept_result = None
        else:
            cur_hash = _phash(frame.path)
            sim = _hamming_similarity(last_hash, cur_hash)
            if last_kept_result is not None and sim >= skip_similarity:
                samples_for_grouping.append((frame, last_kept_result))
                skipped_similar += 1
            else:
                try:
                    result = provider.recognize_image(frame.path, language=language)
                except Exception as exc:
                    raise RuntimeError(f"OCR failed on {frame.path.name}: {exc}") from exc
                ocr_calls += 1
                samples_for_grouping.append((frame, result))
                last_kept_result = result
            last_hash = cur_hash

        now = time.time()
        if now - last_progress_write > 0.4 or idx + 1 == total_frames:
            _write_progress(progress_path, idx + 1, max(total_frames, 1))
            last_progress_write = now
        if now - last_console_log >= console_log_interval_s or idx + 1 == total_frames:
            done = idx + 1
            pct = (done / max(total_frames, 1)) * 100.0
            elapsed_s = now - started
            fps = done / elapsed_s if elapsed_s > 0 else 0.0
            remaining = max(total_frames - done, 0)
            eta_s = remaining / fps if fps > 0 else 0.0
            print(
                f"[ocr] {done}/{total_frames} frames "
                f"({pct:5.1f}%, {fps:.2f} fps, eta {eta_s:5.1f}s, "
                f"ocr_calls={ocr_calls}, skipped_similar={skipped_similar}, "
                f"skipped_covered={skipped_covered})",
                file=sys.stderr,
                flush=True,
            )
            last_console_log = now

    cues = _group_into_cues(
        samples_for_grouping,
        sample_fps=sample_fps,
        min_confidence=min_confidence,
        min_cue_duration_ms=min_cue_duration_ms,
    )

    srt_text = _cues_to_srt(cues)
    out_srt.write_text(srt_text, encoding="utf-8")

    elapsed = time.time() - started
    manifest = {
        "provider": provider_label,
        "language": language,
        "roi": roi,
        "sample_fps": sample_fps,
        "frame_skip_similarity": skip_similarity,
        "min_cue_duration_ms": min_cue_duration_ms,
        "min_confidence": min_confidence,
        "ocr_device_requested": device,
        "ocr_device_used": provider.device_used(),
        "video_fingerprint_short": fingerprint,
        "video_width": width,
        "video_height": height,
        "video_duration_sec": duration_s,
        "frame_count_total": total_frames,
        "frame_count_skipped_similar": skipped_similar,
        "frame_count_skipped_covered": skipped_covered,
        "frame_count_ocr_called": ocr_calls,
        "skip_ranges_ms": [[int(s), int(e)] for s, e in skip_ranges_norm],
        "cue_count": len(cues),
        "elapsed_sec": round(elapsed, 3),
        "cache_hit": False,
        "cache_key": cache_key,
    }
    write_json_atomic(manifest_path, manifest)
    _save_cache(cache_dir, srt_text=srt_text, manifest=manifest)

    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "ocr_provider": provider_label,
            "ocr_language": language,
            "ocr_roi": roi,
            "ocr_device_requested": device,
            "ocr_device_used": provider.device_used(),
            "ocr_output_srt": str(out_srt.resolve()),
            "ocr_cache_hit": False,
        },
    )

    if not keep_frames:
        shutil.rmtree(cache_root, ignore_errors=True)

    return manifest


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    job_workspace = Path(ns.job_workspace).expanduser().resolve()
    job_id = job_workspace.name

    try:
        roi = _parse_roi(ns.roi)
    except ValueError as exc:
        _fail(job_workspace, job_id, str(exc))
        print(f"[ocr] {exc}", file=sys.stderr)
        return 2

    try:
        manifest = run(
            job_workspace=job_workspace,
            language=ns.language,
            roi=roi,
            sample_fps=float(ns.sample_fps),
            skip_similarity=float(ns.frame_skip_similarity),
            min_cue_duration_ms=int(ns.min_cue_duration_ms),
            min_confidence=float(ns.min_confidence),
            device=ns.device,
            provider_name=ns.provider,
            keep_frames=bool(ns.keep_frames),
        )
    except FileNotFoundError as exc:
        _fail(job_workspace, job_id, str(exc))
        print(f"[ocr] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        _fail(job_workspace, job_id, f"OCR stage failed: {exc}")
        print(f"[ocr] OCR stage failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"[ocr] Wrote {manifest['cue_count']} cues from {manifest['frame_count_ocr_called']} OCR calls "
        f"(skipped {manifest['frame_count_skipped_similar']} similar frames; "
        f"device={manifest['ocr_device_used']}; elapsed={manifest['elapsed_sec']}s).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
