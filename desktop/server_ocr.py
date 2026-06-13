"""OCR diagnostics and local-video inspection endpoint handlers.

handle_ocr_test_frame extracts a cropped frame and runs OCR on it;
handle_ocr_diagnostics reports installed OCR providers; handle_inspect_local_video
returns basic metadata for a local video path. Heavy engine/OCR imports stay
lazy (inside the handlers) so importing this module is cheap. Extracted from the
server monolith with behaviour identical to the previous inline handlers.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from desktop.server_shared import _err, _ok, _require
from engine.segment_manager import probe_video_duration


def handle_ocr_test_frame(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Extract a single cropped frame from input/source.mp4, run OCR on it, return text + thumbnail.

    Body keys: job_workspace (required), roi ({x,y,w,h} fractions; optional,
    defaults to bottom band), frame_time_s (float, default 1.0), ocr_language
    (default "ch"), ocr_device ("auto"|"cpu"|"cuda", default "auto").
    """
    import base64
    import tempfile as _tempfile
    from engine import run_ocr_stage
    from engine.ffmpeg_bins import resolve_ffmpeg_executable
    from engine.ocr import get_ocr_provider

    missing = _require(body, "job_workspace")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    input_mp4 = jw / "input" / "source.mp4"
    if not input_mp4.is_file():
        return _err("input_missing", f"Missing canonical input video: {input_mp4}")

    raw_roi = body.get("roi") or body.get("ocr_roi")
    if isinstance(raw_roi, dict):
        roi_str = json.dumps(raw_roi, ensure_ascii=False)
    elif isinstance(raw_roi, str):
        roi_str = raw_roi.strip()
    else:
        roi_str = ""
    try:
        roi = run_ocr_stage._parse_roi(roi_str)
    except ValueError as exc:
        return _err("invalid_roi", str(exc))

    try:
        frame_time_s = float(body.get("frame_time_s") if body.get("frame_time_s") is not None else 1.0)
    except (TypeError, ValueError):
        return _err("invalid_frame_time", "frame_time_s must be a number.")
    if frame_time_s < 0:
        frame_time_s = 0.0

    language = str(body.get("ocr_language") or body.get("language") or "ch").strip() or "ch"
    device = str(body.get("ocr_device") or body.get("device") or "auto").strip().lower() or "auto"
    if device not in {"auto", "cpu", "cuda"}:
        return _err("invalid_ocr_device", f"Unsupported ocr_device: {device!r}.")
    provider_name = str(body.get("ocr_provider") or "paddleocr").strip() or "paddleocr"

    try:
        duration_s, width, height = run_ocr_stage._probe_video(input_mp4)
    except RuntimeError as exc:
        return _err("probe_failed", str(exc))
    if duration_s and frame_time_s > duration_s:
        frame_time_s = max(0.0, duration_s - 0.05)

    ffmpeg, err = resolve_ffmpeg_executable()
    if ffmpeg is None:
        return _err("ffmpeg_missing", err or "ffmpeg not found.")

    crop_w = max(2, int(round(width * roi["w"])) // 2 * 2)
    crop_h = max(2, int(round(height * roi["h"])) // 2 * 2)
    crop_x = max(0, int(round(width * roi["x"])))
    crop_y = max(0, int(round(height * roi["y"])))
    if crop_x + crop_w > width:
        crop_w = (width - crop_x) // 2 * 2
    if crop_y + crop_h > height:
        crop_h = (height - crop_y) // 2 * 2
    vf = f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}"

    with _tempfile.TemporaryDirectory(prefix="ocr_test_frame_") as tmp:
        out_png = Path(tmp) / "frame.png"
        cmd = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{frame_time_s:.3f}",
            "-i",
            str(input_mp4),
            "-frames:v",
            "1",
            "-vf",
            vf,
            str(out_png),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode != 0 or not out_png.is_file():
            tail = (proc.stderr or proc.stdout or "")[-1500:]
            return _err("ffmpeg_failed", f"ffmpeg frame extraction failed: {tail}")
        try:
            thumb_bytes = out_png.read_bytes()
        except OSError as exc:
            return _err("thumb_read_failed", str(exc))

        try:
            provider = get_ocr_provider(provider_name, device=device)
        except Exception as exc:  # noqa: BLE001
            return _err("ocr_provider_unavailable", str(exc))
        try:
            result = provider.recognize_image(out_png, language=language)
        except Exception as exc:  # noqa: BLE001
            return _err("ocr_failed", str(exc))

    lines = [
        {
            "text": str(line.text or ""),
            "confidence": float(line.confidence or 0.0),
        }
        for line in result.lines
        if (line.text or "").strip()
    ]
    joined = "\n".join(ln["text"] for ln in lines)
    avg_conf = (sum(ln["confidence"] for ln in lines) / len(lines)) if lines else 0.0
    thumb_b64 = base64.b64encode(thumb_bytes).decode("ascii")
    return _ok(
        {
            "text": joined,
            "lines": lines,
            "confidence": round(avg_conf, 4),
            "roi": roi,
            "frame_time_s": round(frame_time_s, 3),
            "video_width": width,
            "video_height": height,
            "crop_px": {"x": crop_x, "y": crop_y, "w": crop_w, "h": crop_h},
            "thumb_base64": thumb_b64,
            "thumb_mime": "image/png",
            "ocr_provider": provider_name,
            "ocr_language": language,
            "ocr_device_requested": device,
            "ocr_device_used": provider.device_used(),
        }
    )


def handle_ocr_diagnostics(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Report which OCR providers are installed + device availability.

    Useful as a diagnostics card in settings. Returns the same shape across
    providers so the UI can render a small table.
    """
    import importlib.util

    providers: list[dict[str, Any]] = []

    paddle_spec = importlib.util.find_spec("paddle")
    paddleocr_spec = importlib.util.find_spec("paddleocr")
    paddle_cuda = False
    paddle_detail: dict[str, Any] = {}
    if paddle_spec is not None:
        try:
            import paddle  # type: ignore

            compiled = bool(paddle.device.is_compiled_with_cuda())
            try:
                cuda_count = int(paddle.device.cuda.device_count())
            except Exception:
                cuda_count = 0
            paddle_cuda = compiled and cuda_count > 0
            paddle_detail = {"compiled_with_cuda": compiled, "device_count": cuda_count}
        except Exception as exc:
            paddle_detail = {"probe_error": str(exc)[:200]}
    providers.append(
        {
            "name": "paddleocr",
            "installed": bool(paddle_spec is not None and paddleocr_spec is not None),
            "cuda_available": paddle_cuda,
            "install_hint": "pip install paddleocr paddlepaddle",
            "details": {
                "paddle_present": paddle_spec is not None,
                "paddleocr_present": paddleocr_spec is not None,
                **paddle_detail,
            },
        }
    )

    rapid_spec = importlib.util.find_spec("rapidocr_onnxruntime")
    rapid_cuda = False
    rapid_detail: dict[str, Any] = {}
    try:
        import onnxruntime as ort  # type: ignore

        onnx_providers = list(ort.get_available_providers())
        rapid_cuda = "CUDAExecutionProvider" in onnx_providers
        rapid_detail = {"onnx_providers": onnx_providers}
    except Exception as exc:
        rapid_detail = {"probe_error": str(exc)[:200]}
    providers.append(
        {
            "name": "rapidocr",
            "installed": rapid_spec is not None,
            "cuda_available": rapid_cuda,
            "install_hint": "pip install rapidocr_onnxruntime",
            "details": {
                "rapidocr_present": rapid_spec is not None,
                **rapid_detail,
            },
        }
    )

    any_installed = any(p["installed"] for p in providers)
    recommended = ""
    for p in providers:
        if p["installed"]:
            recommended = p["name"]
            break
    if not recommended:
        recommended = "paddleocr"

    return _ok(
        {
            "providers": providers,
            "any_installed": any_installed,
            "recommended": recommended,
        }
    )


def handle_inspect_local_video(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "path")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    raw = str(body["path"]).strip()
    if not raw:
        return _err("missing_field", "Missing required field: path")
    target = Path(raw).expanduser()
    try:
        resolved = target.resolve(strict=True)
    except (OSError, FileNotFoundError):
        return _err("video_not_found", f"Video not found: {target}")
    if not resolved.is_file():
        return _err("video_not_found", f"Video not found: {resolved}")

    try:
        size = int(resolved.stat().st_size)
    except OSError:
        size = 0
    try:
        duration_s = float(probe_video_duration(resolved))
    except Exception:
        duration_s = None
    return _ok(
        {
            "path": str(resolved),
            "name": resolved.name,
            "size": size,
            "duration_s": duration_s,
        }
    )
