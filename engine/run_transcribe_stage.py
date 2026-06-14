"""
Transcribe input/source.mp4 to artifacts/transcribe/source.srt using faster-whisper (local, offline).
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from engine.ffmpeg_bins import resolve_ffmpeg_executable, resolve_ffprobe_executable
from engine.input_provenance import fingerprint_file
from engine.transcription_report import build_transcription_report, write_transcription_report


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Transcribe job workspace video to artifacts/transcribe/source.srt (faster-whisper)."
    )
    p.add_argument("--job-workspace", required=True, help="Job / video workspace root.")
    p.add_argument(
        "--model-size",
        default="medium",
        help="Whisper model: tiny/base/small/medium/large-v2/large-v3 or CTranslate2 path (default: medium).",
    )
    p.add_argument(
        "--language",
        "--transcribe-language",
        default="",
        dest="language",
        help="Source language (e.g. zh, en, vi). Empty = auto-detect. Alias: --transcribe-language.",
    )
    p.add_argument(
        "--device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="Inference device (default: auto).",
    )
    p.add_argument(
        "--compute-type",
        default="auto",
        choices=["auto", "int8", "int8_float16", "float16", "float32"],
        help="Model compute type (default: auto = float16 on CUDA, int8 on CPU).",
    )
    p.add_argument(
        "--beam-size",
        type=int,
        default=5,
        help="Decoding beam size (default: 5).",
    )
    p.add_argument(
        "--best-of",
        type=int,
        default=5,
        help="Number of candidates when sampling with non-zero temperature (default: 5).",
    )
    p.add_argument(
        "--no-speech-threshold",
        type=float,
        default=0.5,
        help="Lower = less likely to skip audible speech (default: 0.5; whisper default 0.6).",
    )
    p.add_argument(
        "--no-vad-filter",
        action="store_true",
        help="Disable VAD pre-filter (more recall, more risk of noise/hallucinations).",
    )
    p.add_argument(
        "--vad-threshold",
        type=float,
        default=0.35,
        help="VAD speech probability threshold when VAD on (default: 0.35, softer than 0.5).",
    )
    p.add_argument(
        "--vad-min-silence-ms",
        type=int,
        default=500,
        help="Min silence (ms) to split speech chunks when VAD on (default: 500; lower catches more cuts).",
    )
    p.add_argument(
        "--vad-min-speech-ms",
        type=int,
        default=0,
        help="Discard speech chunks shorter than this (ms); 0 keeps short utterances (default: 0).",
    )
    p.add_argument(
        "--vad-speech-pad-ms",
        type=int,
        default=240,
        help="Pad around each VAD speech chunk in ms (default: 240).",
    )
    p.add_argument(
        "--audio-preprocess",
        default="none",
        choices=["none", "mono_16k_wav", "enhance", "vocal_isolate"],
        help="FFmpeg preprocess before ASR: none | mono_16k_wav | enhance (HP/LP+dynaudnorm) | "
        "vocal_isolate (HP + light noise reduction). Requires ffmpeg.",
    )
    p.add_argument(
        "--long-gap-report-ms",
        type=int,
        default=2000,
        help="List timeline gaps longer than this (ms) in transcription_report.json (default: 2000).",
    )
    p.add_argument(
        "--extractor",
        default="audio_only",
        choices=["audio_only", "ocr_only", "hybrid"],
        help="Subtitle source: audio_only (ASR only, default), ocr_only (OCR only), hybrid (Phase B).",
    )
    p.add_argument(
        "--ocr-language",
        default="ch",
        help="OCR language when --extractor ocr_only/hybrid (default: ch).",
    )
    p.add_argument(
        "--ocr-roi",
        default="",
        help='OCR ROI JSON {"x":0.0,"y":0.78,"w":1.0,"h":0.20} (0..1 fractions).',
    )
    p.add_argument(
        "--ocr-sample-fps",
        type=float,
        default=2.5,
        help="OCR frame sampling rate (default 2.5).",
    )
    p.add_argument(
        "--ocr-min-confidence",
        type=float,
        default=0.6,
        help="OCR per-line minimum confidence (default 0.6).",
    )
    p.add_argument(
        "--ocr-min-cue-duration-ms",
        type=int,
        default=300,
        help="Drop OCR cues shorter than this (default 300ms).",
    )
    p.add_argument(
        "--ocr-frame-skip-similarity",
        type=float,
        default=0.98,
        help="Skip frames more similar than this to previous (default 0.98).",
    )
    p.add_argument(
        "--ocr-device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="OCR device (default: auto).",
    )
    p.add_argument(
        "--ocr-provider",
        default="paddleocr",
        help="OCR provider name (default paddleocr).",
    )
    p.add_argument(
        "--hybrid-ocr-mode",
        default="gaps",
        choices=["gaps", "full"],
        help="Hybrid extractor: 'gaps' (default) runs ASR first, then OCR only over audio "
        "gaps (much faster on CPU); 'full' runs ASR+OCR in parallel over the whole video.",
    )
    p.add_argument(
        "--hybrid-gap-pad-ms",
        type=int,
        default=300,
        help="Pad each ASR cue by this many ms on both sides before computing OCR gaps "
        "(default 300). Larger values reduce overlap with ASR at boundaries.",
    )
    p.add_argument(
        "--hybrid-gap-min-ms",
        type=int,
        default=600,
        help="Drop gaps shorter than this (default 600ms) — short silences rarely contain "
        "on-screen text worth OCR'ing.",
    )
    return p.parse_args(argv)


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


def _load_video_state(job_workspace: Path) -> dict:
    p = job_workspace / "video_state.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_video_state(job_workspace: Path, data: dict) -> None:
    p = job_workspace / "video_state.json"
    base = _load_video_state(job_workspace)
    payload = dict(data)
    inc_ap = payload.pop("artifact_paths", None)
    base.update(payload)
    if inc_ap is not None:
        merged = dict(base.get("artifact_paths") or {})
        merged.update(inc_ap)
        base["artifact_paths"] = merged
    write_json_atomic(p, base)


def _srt_timestamp(seconds: float) -> str:
    sec = max(0.0, float(seconds))
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    whole = int(s)
    ms = int(round((s - whole) * 1000))
    if ms >= 1000:
        whole += 1
        ms -= 1000
    if whole >= 60:
        m += whole // 60
        whole = whole % 60
    if m >= 60:
        h += m // 60
        m = m % 60
    return f"{h:02d}:{m:02d}:{whole:02d},{ms:03d}"


def _segments_to_srt_text(segments) -> str:
    lines: list[str] = []
    idx = 1
    for seg in segments:
        text = (seg.text or "").strip()
        if not text:
            continue
        start = _srt_timestamp(float(seg.start))
        end = _srt_timestamp(float(seg.end))
        lines.append(str(idx))
        idx += 1
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines).rstrip() + ("\n" if lines else "")


def _resolve_device(device: str) -> str:
    """Pick an inference device. ``auto`` prefers CUDA when visible.

    We intentionally do NOT probe bundled CUDA DLLs via ctypes here —
    CTranslate2 ships its own copies and loads them through its own
    search path, so a bare ``ctypes.CDLL("cublas64_12.dll")`` will often
    fail even on machines where CT2 init succeeds. Instead, if CUDA
    inference fails at load/transcribe time, ``_run_asr_to_srt`` retries
    on CPU (see ``_is_cuda_runtime_error``).
    """
    if device == "cpu":
        return "cpu"
    try:
        import ctranslate2

        has_cuda_device = ctranslate2.get_cuda_device_count() > 0
    except Exception:
        has_cuda_device = False
    if device == "cuda":
        if not has_cuda_device:
            print(
                "[transcribe] WARNING: --device cuda requested but no CUDA device "
                "visible; falling back to CPU.",
                file=sys.stderr,
            )
            return "cpu"
        return "cuda"
    return "cuda" if has_cuda_device else "cpu"


def _resolve_compute_type(device: str, requested: str) -> str:
    if requested and requested != "auto":
        return requested
    return "float16" if device == "cuda" else "int8"


def _format_asr_error_guidance(exc: BaseException, device: str) -> str:
    """Turn a raw DLL / runtime failure into an actionable message.

    WinError 127 / "specified procedure could not be found" almost always
    means a binary dependency is missing or version-mismatched. On CPU that
    typically points at the Intel MKL or libomp that ships with CTranslate2;
    on CUDA it's cuBLAS / cuDNN. Users reading the log straight from the UI
    benefit from a suggested fix instead of the raw Windows error code.
    """
    base = str(exc) or exc.__class__.__name__
    if device == "cuda":
        hint = (
            "CUDA runtime DLL missing/mismatched. Typical fixes: "
            "(1) install NVIDIA CUDA 12 runtime + cuDNN 9 matching your GPU driver, "
            "(2) add the CUDA bin folder to PATH, "
            "(3) or re-run with --device cpu to skip GPU."
        )
    else:
        hint = (
            "CTranslate2 CPU runtime deps appear broken on this machine "
            "(usually Intel MKL / libomp). Typical fixes: "
            "(1) reinstall ctranslate2: 'pip install --force-reinstall ctranslate2', "
            "(2) install MSVC 2015-2022 x64 redistributable, "
            "(3) check that no system-wide MKL / oneDNN overrides the one CT2 bundles."
        )
    return f"ASR load/transcribe failed on {device}: {base}\n{hint}"


def _is_cuda_runtime_error(exc: BaseException) -> bool:
    """Return True if ``exc`` is a CTranslate2 CUDA-runtime / DLL-load failure.

    Covers both ``RuntimeError: Library cublas64_12.dll is not found`` and
    the raw ``OSError [WinError 127]`` that Windows raises when an export
    in a CUDA dependency can't be resolved.
    """
    msg = str(exc) or ""
    needles = (
        "is not found or cannot be loaded",
        "cublas",
        "cudnn",
        "cudart",
        "WinError 127",
        "The specified procedure could not be found",
    )
    return any(n.lower() in msg.lower() for n in needles)


def _is_unsupported_compute_error(exc: BaseException) -> bool:
    """True when the device/backend rejects the requested compute type (e.g. a
    CUDA GPU without efficient float16). CTranslate2 message:
    'Requested float16 compute type, but the target device or backend do not
    support efficient float16 computation.'"""
    msg = (str(exc) or "").lower()
    return "compute type" in msg and ("do not support" in msg or "does not support" in msg or "not support efficient" in msg)


def _is_missing_vad_asset_error(exc: BaseException) -> bool:
    """Return True when faster-whisper VAD failed because the bundled ONNX file is missing."""
    msg = (str(exc) or "").lower()
    has_vad_asset_ref = "silero_vad" in msg or "vad_v6.onnx" in msg
    has_missing_file_ref = (
        "no_suchfile" in msg
        or "file doesn't exist" in msg
        or "does not exist" in msg
        or "not found" in msg
    )
    return has_vad_asset_ref and has_missing_file_ref


def _probe_video_duration_ms(video_path: Path) -> int | None:
    ffprobe = resolve_ffprobe_executable()
    if not ffprobe or not video_path.is_file():
        return None
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        return None
    try:
        return int(round(float((proc.stdout or "").strip()) * 1000.0))
    except ValueError:
        return None


def _preprocess_audio_for_asr(
    input_mp4: Path,
    *,
    mode: str,
    work_dir: Path,
) -> Path:
    ffmpeg, err = resolve_ffmpeg_executable()
    if ffmpeg is None:
        raise RuntimeError(err or "ffmpeg not found (required for --audio-preprocess).")

    work_dir.mkdir(parents=True, exist_ok=True)
    out_wav = work_dir / "asr_input.wav"

    if mode == "mono_16k_wav":
        af = None
    elif mode == "enhance":
        af = "highpass=f=80,lowpass=f=8000,dynaudnorm=f=150:g=15"
    elif mode == "vocal_isolate":
        af = "highpass=f=100,afftdn=nf=-20,lowpass=f=10000,dynaudnorm=f=200:g=10"
    else:
        raise ValueError(f"unknown preprocess mode: {mode}")

    cmd: list[str] = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(input_mp4), "-vn"]
    if af:
        cmd.extend(["-af", af])
    cmd.extend(["-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(out_wav)])

    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-2000:]
        raise RuntimeError(f"ffmpeg preprocess failed (exit {proc.returncode}): {tail}")
    if not out_wav.is_file() or out_wav.stat().st_size < 100:
        raise RuntimeError("ffmpeg preprocess produced empty or missing WAV.")
    return out_wav


def _fail_input_required(job_workspace: Path, job_id: str, message: str) -> None:
    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "blocked",
            "current_stage": "input_required",
            "last_error": message,
            "transcribe_input_video": None,
            "transcribe_output_srt": None,
            "transcription_engine": None,
        },
    )
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "blocked",
            "current_stage": "input_required",
            "last_error": message,
        },
    )


def _fail_transcribe(job_workspace: Path, job_id: str, message: str) -> None:
    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "failed",
            "current_stage": "transcribe_failed",
            "last_error": message,
        },
    )
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "failed",
            "current_stage": "transcribe_failed",
            "last_error": message,
        },
    )


def _run_asr_to_srt(
    ns,
    job_workspace: Path,
    out_srt: Path,
    *,
    report_path: Path | None = None,
) -> dict:
    """Run faster-whisper on input/source.mp4 and write SRT to out_srt.

    Returns a metadata dict including the report body (not written unless
    report_path is provided). Raises RuntimeError on failure so the caller
    can decide how to surface it (ocr_only, hybrid, audio_only all differ).
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise RuntimeError(
            f"faster-whisper is not installed. Install with: pip install faster-whisper ({e})"
        ) from e

    input_mp4 = job_workspace / "input" / "source.mp4"
    transcribe_dir = job_workspace / "artifacts" / "transcribe"
    work_dir = transcribe_dir / ".work"

    dev = _resolve_device(ns.device)
    compute_type = _resolve_compute_type(dev, ns.compute_type)
    lang = (ns.language or "").strip() or None
    video_duration_ms = _probe_video_duration_ms(input_mp4)

    audio_input: Path | str = input_mp4
    preprocess_mode = (ns.audio_preprocess or "none").strip().lower()
    if preprocess_mode != "none":
        temp_wav = _preprocess_audio_for_asr(input_mp4, mode=preprocess_mode, work_dir=work_dir)
        audio_input = temp_wav
        print(
            f"[transcribe] audio_preprocess={preprocess_mode} wav={temp_wav}",
            file=sys.stderr,
        )

    requested_vad_filter = not bool(ns.no_vad_filter)
    requested_vad_parameters = None
    if requested_vad_filter:
        requested_vad_parameters = {
            "threshold": float(ns.vad_threshold),
            "min_speech_duration_ms": int(ns.vad_min_speech_ms),
            "min_silence_duration_ms": int(ns.vad_min_silence_ms),
            "speech_pad_ms": int(ns.vad_speech_pad_ms),
        }

    transcribe_kw: dict = {
        "language": lang,
        "beam_size": int(ns.beam_size),
        "best_of": int(ns.best_of),
        "no_speech_threshold": float(ns.no_speech_threshold),
        "vad_filter": requested_vad_filter,
    }
    if requested_vad_parameters is not None:
        transcribe_kw["vad_parameters"] = requested_vad_parameters

    def _load_and_transcribe(device_: str, compute_: str):
        model_ = WhisperModel(ns.model_size, device=device_, compute_type=compute_)
        effective_vad_filter = bool(transcribe_kw.get("vad_filter"))
        effective_vad_parameters = requested_vad_parameters
        vad_fallback_reason: str | None = None
        try:
            segs_iter, info_ = model_.transcribe(str(audio_input), **transcribe_kw)
            segments_ = list(segs_iter)
        except Exception as exc:
            if requested_vad_filter and _is_missing_vad_asset_error(exc):
                vad_fallback_reason = str(exc)
                print(
                    "[transcribe] WARNING: faster-whisper VAD asset is missing; "
                    "retrying transcription without VAD filter.",
                    file=sys.stderr,
                )
                fallback_kw = dict(transcribe_kw)
                fallback_kw["vad_filter"] = False
                fallback_kw.pop("vad_parameters", None)
                segs_iter, info_ = model_.transcribe(str(audio_input), **fallback_kw)
                segments_ = list(segs_iter)
                effective_vad_filter = False
                effective_vad_parameters = None
            else:
                raise
        return (
            model_,
            segments_,
            info_,
            effective_vad_filter,
            effective_vad_parameters,
            vad_fallback_reason,
        )

    # Device/compute fallback ladder. A CUDA GPU may reject float16 (older cards
    # / CT2 build) — step down to int8_float16, then int8, then CPU. CUDA runtime
    # / DLL failures also fall through to CPU.
    if dev == "cuda":
        candidates: list[tuple[str, str]] = [
            (dev, compute_type),
            ("cuda", "int8_float16"),
            ("cuda", "int8"),
            ("cpu", _resolve_compute_type("cpu", ns.compute_type)),
        ]
    else:
        candidates = [(dev, compute_type)]
    seen: set[tuple[str, str]] = set()
    candidates = [c for c in candidates if not (c in seen or seen.add(c))]

    result = None
    last_exc: BaseException | None = None
    for idx, (cand_dev, cand_ct) in enumerate(candidates):
        try:
            result = _load_and_transcribe(cand_dev, cand_ct)
            dev, compute_type = cand_dev, cand_ct
            if idx > 0:
                print(
                    f"[transcribe] using device={dev} compute_type={compute_type} after fallback.",
                    file=sys.stderr,
                )
            break
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            fallbackable = _is_cuda_runtime_error(exc) or _is_unsupported_compute_error(exc)
            if not fallbackable:
                raise
            if idx < len(candidates) - 1:
                print(
                    f"[transcribe] WARNING: device={cand_dev} compute_type={cand_ct} failed "
                    f"({str(exc)[:160]}); trying next fallback.",
                    file=sys.stderr,
                )
    if result is None:
        raise RuntimeError(_format_asr_error_guidance(last_exc or RuntimeError("transcribe failed"), dev))
    (
        model,
        segments,
        _info,
        effective_vad_filter,
        effective_vad_parameters,
        vad_fallback_reason,
    ) = result

    report_body = build_transcription_report(
        segments=segments,
        video_duration_ms=video_duration_ms,
        long_gap_ms=int(ns.long_gap_report_ms),
    )
    report_body["model_size"] = ns.model_size
    report_body["device"] = dev
    report_body["compute_type"] = compute_type
    report_body["language"] = lang
    report_body["vad_filter"] = effective_vad_filter
    report_body["vad_parameters"] = effective_vad_parameters
    if vad_fallback_reason is not None:
        report_body["vad_fallback_reason"] = vad_fallback_reason
        warnings = list(report_body.get("warnings") or [])
        if "vad_asset_missing_retry_without_vad" not in warnings:
            warnings.append("vad_asset_missing_retry_without_vad")
        report_body["warnings"] = warnings
    report_body["audio_preprocess"] = preprocess_mode
    report_body["no_speech_threshold"] = float(ns.no_speech_threshold)

    if report_path is not None:
        try:
            write_transcription_report(report_path, report_body)
        except OSError as e:
            print(f"[transcribe] warning: could not write report: {e}", file=sys.stderr)

    out_srt.parent.mkdir(parents=True, exist_ok=True)
    out_srt.write_text(_segments_to_srt_text(segments), encoding="utf-8")

    return {
        "device": dev,
        "compute_type": compute_type,
        "language": lang,
        "segment_count": len(segments),
        "report": report_body,
    }


def _emit_coverage_warnings(report_body: dict, report_path: Path) -> None:
    warns = report_body.get("warnings") or []
    ratio = report_body.get("transcription_coverage_ratio")
    if "critical_low_transcription_coverage" in warns:
        print(
            f"[transcribe] WARNING: transcription coverage very low "
            f"(ratio={ratio!r}, segments={report_body.get('segment_count')}). "
            "Try: --no-vad-filter, larger --model-size, --audio-preprocess enhance, "
            "or set --language zh explicitly.",
            file=sys.stderr,
        )
    elif "low_transcription_coverage" in warns:
        print(
            f"[transcribe] WARNING: low transcription coverage "
            f"(ratio={ratio!r}). See {report_path.name} (long_gaps).",
            file=sys.stderr,
        )


def _run_ocr_only_mode(ns, job_workspace: Path, job_id: str) -> int:
    """Phase A: OCR-only extractor — runs OCR, copies source_ocr.srt -> source.srt."""
    from engine import run_ocr_stage

    input_mp4 = job_workspace / "input" / "source.mp4"
    transcribe_dir = job_workspace / "artifacts" / "transcribe"
    transcribe_dir.mkdir(parents=True, exist_ok=True)
    out_srt = transcribe_dir / "source.srt"

    try:
        roi = run_ocr_stage._parse_roi(ns.ocr_roi)
    except ValueError as exc:
        _fail_transcribe(job_workspace, job_id, f"Invalid --ocr-roi: {exc}")
        print(f"[transcribe] {exc}", file=sys.stderr)
        return 2

    try:
        manifest = run_ocr_stage.run(
            job_workspace=job_workspace,
            language=(ns.ocr_language or "ch").strip(),
            roi=roi,
            sample_fps=float(ns.ocr_sample_fps),
            skip_similarity=float(ns.ocr_frame_skip_similarity),
            min_cue_duration_ms=int(ns.ocr_min_cue_duration_ms),
            min_confidence=float(ns.ocr_min_confidence),
            device=ns.ocr_device,
            provider_name=ns.ocr_provider,
            keep_frames=False,
        )
    except FileNotFoundError as exc:
        _fail_input_required(job_workspace, job_id, str(exc))
        print(f"[transcribe] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        _fail_transcribe(job_workspace, job_id, f"OCR extractor failed: {exc}")
        print(f"[transcribe] OCR extractor failed: {exc}", file=sys.stderr)
        return 1

    src_srt = transcribe_dir / "source_ocr.srt"
    if not src_srt.is_file():
        _fail_transcribe(job_workspace, job_id, f"OCR stage did not produce {src_srt}.")
        return 1
    shutil.copyfile(src_srt, out_srt)

    in_resolved = str(input_mp4.resolve())
    out_resolved = str(out_srt.resolve())
    vid_fp = fingerprint_file(input_mp4)

    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "transcribed",
            "current_stage": "transcribed",
            "last_error": None,
            "transcribe_input_video": in_resolved,
            "transcribe_output_srt": out_resolved,
            "transcription_engine": f"ocr:{manifest.get('provider', ns.ocr_provider)}",
            "subtitle_extractor": "ocr_only",
            "input_video_fingerprint_at_transcribe": vid_fp,
        },
    )
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "transcribed",
            "current_stage": "transcribed",
            "last_error": None,
            "transcription_engine": f"ocr:{manifest.get('provider', ns.ocr_provider)}",
            "artifact_paths": {
                "source_srt": out_resolved,
                "source_ocr_srt": str(src_srt.resolve()),
                "ocr_manifest": str((transcribe_dir / "ocr_manifest.json").resolve()),
            },
        },
    )

    print(
        f"[transcribe] (ocr_only) wrote {out_resolved} ({manifest.get('cue_count')} cues, "
        f"device={manifest.get('ocr_device_used')}).",
        file=sys.stderr,
    )
    return 0


def _asr_covered_ranges_ms(srt_path: Path, *, pad_ms: int = 0) -> list[tuple[int, int]]:
    """Parse ASR SRT and return merged (start_ms, end_ms) ranges padded on both sides.

    An empty or unreadable SRT yields an empty list (caller should treat as
    "no audio coverage, run OCR over the whole video").
    """
    from engine.srt_cues import parse_srt_cues

    if not srt_path.is_file():
        return []
    try:
        content = srt_path.read_text(encoding="utf-8")
    except OSError:
        return []
    cues = parse_srt_cues(content)
    if not cues:
        return []
    pad = max(0, int(pad_ms))
    raw: list[tuple[int, int]] = []
    for c in cues:
        s = max(0, c.start_ms - pad)
        e = c.end_ms + pad
        if e > s:
            raw.append((s, e))
    if not raw:
        return []
    raw.sort()
    merged: list[tuple[int, int]] = [raw[0]]
    for s, e in raw[1:]:
        ps, pe = merged[-1]
        if s <= pe:
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))
    return merged


def _filter_short_gaps(
    covered: list[tuple[int, int]],
    *,
    video_duration_ms: int | None,
    min_gap_ms: int,
) -> list[tuple[int, int]]:
    """Extend `covered` ranges by absorbing gaps shorter than ``min_gap_ms``.

    The OCR loop treats frames inside ``covered`` as already-handled. A short
    gap between two ASR cues is unlikely to contain on-screen text worth a slow
    OCR pass, so we fold it into the neighbouring covered range.
    """
    if not covered or min_gap_ms <= 0:
        return list(covered)
    merged: list[tuple[int, int]] = [covered[0]]
    for s, e in covered[1:]:
        ps, pe = merged[-1]
        if s - pe < min_gap_ms:
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))
    if video_duration_ms is not None and merged:
        last_s, last_e = merged[-1]
        if video_duration_ms - last_e < min_gap_ms:
            merged[-1] = (last_s, video_duration_ms)
    return merged


def _run_hybrid_mode(ns, job_workspace: Path, job_id: str) -> int:
    """Phase B: hybrid extractor.

    Two submodes:
      * ``gaps`` (default, faster): run ASR first; pass ASR-covered time ranges
        as ``skip_ranges`` to OCR so only audio gaps are scanned. Fuse after.
      * ``full``: legacy parallel mode — ASR and OCR both scan the full video.

    In both modes the final canonical SRT is produced by fusing source_audio.srt
    and source_ocr.srt.
    """
    from engine import run_ocr_stage
    from engine.fuse_subtitle import fuse_files

    input_mp4 = job_workspace / "input" / "source.mp4"
    transcribe_dir = job_workspace / "artifacts" / "transcribe"
    transcribe_dir.mkdir(parents=True, exist_ok=True)
    asr_srt = transcribe_dir / "source_audio.srt"
    ocr_srt = transcribe_dir / "source_ocr.srt"
    out_srt = transcribe_dir / "source.srt"
    provenance_path = transcribe_dir / "source_provenance.json"
    report_path = transcribe_dir / "transcription_report.json"

    try:
        roi = run_ocr_stage._parse_roi(ns.ocr_roi)
    except ValueError as exc:
        _fail_transcribe(job_workspace, job_id, f"Invalid --ocr-roi: {exc}")
        print(f"[transcribe] {exc}", file=sys.stderr)
        return 2

    hybrid_mode = (getattr(ns, "hybrid_ocr_mode", "gaps") or "gaps").strip().lower()
    gap_pad_ms = int(getattr(ns, "hybrid_gap_pad_ms", 300) or 0)
    gap_min_ms = int(getattr(ns, "hybrid_gap_min_ms", 600) or 0)

    def _do_asr() -> dict:
        return _run_asr_to_srt(ns, job_workspace, asr_srt, report_path=report_path)

    def _do_ocr(skip_ranges: list[tuple[int, int]] | None) -> dict:
        return run_ocr_stage.run(
            job_workspace=job_workspace,
            language=(ns.ocr_language or "ch").strip(),
            roi=roi,
            sample_fps=float(ns.ocr_sample_fps),
            skip_similarity=float(ns.ocr_frame_skip_similarity),
            min_cue_duration_ms=int(ns.ocr_min_cue_duration_ms),
            min_confidence=float(ns.ocr_min_confidence),
            device=ns.ocr_device,
            provider_name=ns.ocr_provider,
            keep_frames=False,
            skip_ranges=skip_ranges,
        )

    asr_meta: dict | None = None
    ocr_manifest: dict | None = None
    asr_error: Exception | None = None
    ocr_error: Exception | None = None

    if hybrid_mode == "gaps":
        # Sequential: ASR first, then OCR over audio gaps.
        try:
            asr_meta = _do_asr()
        except Exception as exc:
            asr_error = exc
            print(f"[transcribe] hybrid(gaps): ASR failed: {exc}", file=sys.stderr)

        if asr_meta is not None:
            covered = _asr_covered_ranges_ms(asr_srt, pad_ms=gap_pad_ms)
            video_duration_ms = _probe_video_duration_ms(input_mp4)
            covered = _filter_short_gaps(
                covered,
                video_duration_ms=video_duration_ms,
                min_gap_ms=gap_min_ms,
            )
            total_covered = sum(e - s for s, e in covered)
            print(
                f"[transcribe] hybrid(gaps): ASR covered {len(covered)} ranges "
                f"(~{total_covered / 1000.0:.1f}s); OCR will scan only the gaps.",
                file=sys.stderr,
            )
            try:
                ocr_manifest = _do_ocr(covered)
            except Exception as exc:
                ocr_error = exc
                print(f"[transcribe] hybrid(gaps): OCR failed: {exc}", file=sys.stderr)
        else:
            # No ASR coverage available — fall back to full OCR scan.
            print(
                "[transcribe] hybrid(gaps): ASR unavailable; falling back to full OCR scan.",
                file=sys.stderr,
            )
            try:
                ocr_manifest = _do_ocr(None)
            except Exception as exc:
                ocr_error = exc
                print(f"[transcribe] hybrid(gaps): OCR failed: {exc}", file=sys.stderr)
    else:
        # Legacy parallel mode.
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="hybrid_extract") as pool:
            asr_future = pool.submit(_do_asr)
            ocr_future = pool.submit(_do_ocr, None)
            try:
                asr_meta = asr_future.result()
            except Exception as exc:
                asr_error = exc
                print(f"[transcribe] hybrid(full): ASR failed: {exc}", file=sys.stderr)
            try:
                ocr_manifest = ocr_future.result()
            except Exception as exc:
                ocr_error = exc
                print(f"[transcribe] hybrid(full): OCR failed: {exc}", file=sys.stderr)

    if asr_error and ocr_error:
        msg = f"Hybrid extractor failed: ASR={asr_error}; OCR={ocr_error}"
        _fail_transcribe(job_workspace, job_id, msg)
        return 1

    if asr_meta is not None:
        _emit_coverage_warnings(asr_meta["report"], report_path)

    prov = fuse_files(
        asr_srt,
        ocr_srt,
        out_srt=out_srt,
        out_provenance=provenance_path,
        extractor_label="hybrid",
    )

    in_resolved = str(input_mp4.resolve())
    out_resolved = str(out_srt.resolve())
    vid_fp = fingerprint_file(input_mp4)
    provider_label = str((ocr_manifest or {}).get("provider") or ns.ocr_provider or "paddleocr").strip()
    engine_label = f"hybrid:faster_whisper+{provider_label}"

    artifact_paths: dict = {
        "source_srt": out_resolved,
        "source_provenance": str(provenance_path.resolve()),
    }
    if asr_srt.is_file():
        artifact_paths["source_audio_srt"] = str(asr_srt.resolve())
    if ocr_srt.is_file():
        artifact_paths["source_ocr_srt"] = str(ocr_srt.resolve())
    if ocr_manifest is not None:
        artifact_paths["ocr_manifest"] = str((transcribe_dir / "ocr_manifest.json").resolve())

    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "transcribed",
            "current_stage": "transcribed",
            "last_error": None,
            "transcribe_input_video": in_resolved,
            "transcribe_output_srt": out_resolved,
            "transcription_engine": engine_label,
            "subtitle_extractor": "hybrid",
            "input_video_fingerprint_at_transcribe": vid_fp,
        },
    )
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "transcribed",
            "current_stage": "transcribed",
            "last_error": None,
            "transcription_engine": engine_label,
            "artifact_paths": artifact_paths,
        },
    )

    print(
        f"[transcribe] (hybrid) wrote {out_resolved} "
        f"({prov['final_cue_count']} cues; asr={prov['asr_cue_count']} ocr={prov['ocr_cue_count']}).",
        file=sys.stderr,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    job_workspace = Path(ns.job_workspace).expanduser().resolve()
    job_id = job_workspace.name

    input_mp4 = job_workspace / "input" / "source.mp4"
    transcribe_dir = job_workspace / "artifacts" / "transcribe"
    out_srt = transcribe_dir / "source.srt"
    report_path = transcribe_dir / "transcription_report.json"
    work_dir = transcribe_dir / ".work"

    if not input_mp4.is_file():
        msg = f"Missing canonical input video: {input_mp4}"
        _fail_input_required(job_workspace, job_id, msg)
        print(msg, file=sys.stderr)
        return 1

    extractor = (getattr(ns, "extractor", "audio_only") or "audio_only").strip().lower()
    if extractor == "ocr_only":
        return _run_ocr_only_mode(ns, job_workspace, job_id)
    if extractor == "hybrid":
        return _run_hybrid_mode(ns, job_workspace, job_id)

    try:
        asr_meta = _run_asr_to_srt(ns, job_workspace, out_srt, report_path=report_path)
    except Exception as e:
        msg = f"Transcription failed: {e}"
        _fail_transcribe(job_workspace, job_id, msg)
        print(msg, file=sys.stderr)
        return 1

    report_body = asr_meta["report"]
    segments_count = asr_meta["segment_count"]
    dev = asr_meta["device"]
    ratio = report_body.get("transcription_coverage_ratio")
    _emit_coverage_warnings(report_body, report_path)

    in_resolved = str(input_mp4.resolve())
    out_resolved = str(out_srt.resolve())
    vid_fp = fingerprint_file(input_mp4)

    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "transcribed",
            "current_stage": "transcribed",
            "last_error": None,
            "transcribe_input_video": in_resolved,
            "transcribe_output_srt": out_resolved,
            "transcription_engine": "faster_whisper",
            "subtitle_extractor": "audio_only",
            "input_video_fingerprint_at_transcribe": vid_fp,
        },
    )
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "transcribed",
            "current_stage": "transcribed",
            "last_error": None,
            "transcription_engine": "faster_whisper",
            "artifact_paths": {"source_srt": out_resolved},
        },
    )

    print(
        f"[transcribe] Wrote {out_resolved} ({segments_count} raw segments, "
        f"{report_body.get('segment_count')} non-empty, device={dev}, "
        f"coverage_ratio={ratio!r}). Report: {report_path.name}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
