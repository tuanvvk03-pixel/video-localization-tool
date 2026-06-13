from __future__ import annotations

import importlib.util
import os
import socket
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from engine.ffmpeg_bins import resolve_ffmpeg_executable, resolve_ffprobe_executable
from engine.runtime_app_settings import resolve_azure_speech_configs
from engine.video_download import probe_yt_dlp_health


def _check(
    name: str,
    *,
    ok: bool,
    required: bool,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "name": name,
        "ok": bool(ok),
        "required": bool(required),
        "message": str(message),
    }
    if details:
        payload["details"] = details
    return payload


def _normalize_provider(name: str) -> str:
    key = (name or "").strip().lower().replace("-", "_")
    if key == "edge":
        return "edge_tts"
    if key == "azure":
        return "azure_tts"
    return key or "edge_tts"


def _check_workspace(job_workspace: Path | None, *, require_input: bool) -> list[dict[str, Any]]:
    if job_workspace is None:
        return []
    checks: list[dict[str, Any]] = []
    checks.append(
        _check(
            "workspace_exists",
            ok=job_workspace.is_dir(),
            required=True,
            message=(
                f"Workspace found: {job_workspace}"
                if job_workspace.is_dir()
                else f"Workspace not found: {job_workspace}"
            ),
            details={"path": str(job_workspace)},
        )
    )
    if job_workspace.is_dir():
        writable = True
        error = ""
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                prefix=".preflight_",
                suffix=".tmp",
                dir=str(job_workspace),
                delete=True,
            ) as fh:
                fh.write("ok")
                fh.flush()
        except OSError as e:
            writable = False
            error = str(e)
        checks.append(
            _check(
                "workspace_writable",
                ok=writable,
                required=True,
                message=(
                    f"Workspace is writable: {job_workspace}"
                    if writable
                    else f"Workspace is not writable: {job_workspace} ({error})"
                ),
                details={"path": str(job_workspace)},
            )
        )
    if require_input:
        input_video = job_workspace / "input" / "source.mp4"
        checks.append(
            _check(
                "input_video",
                ok=input_video.is_file(),
                required=True,
                message=(
                    f"Input video found: {input_video}"
                    if input_video.is_file()
                    else f"Missing input video: {input_video}"
                ),
                details={"path": str(input_video)},
            )
        )
    return checks


def _check_translate_backend(translate_backend: str, *, api_key: str) -> list[dict[str, Any]]:
    backend = (translate_backend or "legacy").strip().lower()
    if backend != "block_v2":
        return [
            _check(
                "translate_backend",
                ok=True,
                required=False,
                message=f"translate_backend={backend} does not require OpenAI API key preflight.",
                details={"backend": backend},
            )
        ]
    resolved = (api_key or os.environ.get("OPENAI_API_KEY", "") or "").strip()
    return [
        _check(
            "openai_api_key",
            ok=bool(resolved),
            required=True,
            message=(
                "OpenAI API key is configured for block_v2 translate."
                if resolved
                else "Missing API key: set --api-key or OPENAI_API_KEY for block_v2 translate."
            ),
            details={"backend": backend, "from_env": bool(not api_key and resolved)},
        )
    ]


def _probe_executable(command: str, label: str) -> tuple[bool, str, dict[str, Any]]:
    try:
        proc = subprocess.run(
            [command, "-version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
    except OSError as e:
        return False, f"{label} exists but could not be executed: {e}", {"path": command}
    except subprocess.TimeoutExpired:
        return False, f"{label} did not respond to -version within 5s.", {"path": command}

    head = ""
    if proc.stdout:
        head = proc.stdout.splitlines()[0].strip()
    elif proc.stderr:
        head = proc.stderr.splitlines()[0].strip()
    details: dict[str, Any] = {"path": command, "returncode": int(proc.returncode)}
    if head:
        details["version_line"] = head
    if proc.returncode != 0:
        msg = f"{label} is present but failed health probe (-version exit {proc.returncode})."
        if head:
            msg = f"{msg} {head}"
        return False, msg, details
    return True, f"{label} executable is healthy: {head or command}", details


def _check_tts_provider(tts_provider: str) -> list[dict[str, Any]]:
    provider = _normalize_provider(tts_provider)
    checks: list[dict[str, Any]] = [
        _check(
            "tts_provider",
            ok=provider in {"edge_tts", "azure_tts"},
            required=True,
            message=(
                f"TTS provider {provider!r} is supported."
                if provider in {"edge_tts", "azure_tts"}
                else f"Unknown TTS provider {tts_provider!r}."
            ),
            details={"provider": provider},
        )
    ]
    network_message = {
        "edge_tts": "edge_tts requires outbound network access at runtime.",
        "azure_tts": "azure_tts requires outbound network access at runtime.",
    }.get(provider)
    if network_message:
        checks.append(
            _check(
                "tts_network_contract",
                ok=True,
                required=False,
                message=network_message,
                details={"provider": provider, "network_required": True},
            )
        )
    if provider == "edge_tts":
        checks.append(
            _check(
                "edge_tts_package",
                ok=importlib.util.find_spec("edge_tts") is not None,
                required=True,
                message=(
                    "edge-tts package is installed."
                    if importlib.util.find_spec("edge_tts") is not None
                    else "edge-tts is not installed. Install with: pip install edge-tts"
                ),
            )
        )
        ffmpeg, err = resolve_ffmpeg_executable()
        ffmpeg_ok = ffmpeg is not None
        ffmpeg_msg = (
            f"ffmpeg available for edge-tts: {ffmpeg}"
            if ffmpeg is not None
            else (err or "ffmpeg not found.")
        )
        ffmpeg_details: dict[str, Any] = {"path": ffmpeg}
        if ffmpeg is not None:
            ffmpeg_ok, ffmpeg_msg, ffmpeg_details = _probe_executable(ffmpeg, "ffmpeg")
        checks.append(
            _check(
                "ffmpeg_for_tts",
                ok=ffmpeg_ok,
                required=True,
                message=ffmpeg_msg,
                details=ffmpeg_details,
            )
        )
    elif provider == "azure_tts":
        checks.append(
            _check(
                "azure_speech_package",
                ok=importlib.util.find_spec("azure.cognitiveservices.speech") is not None,
                required=True,
                message=(
                    "azure-cognitiveservices-speech package is installed."
                    if importlib.util.find_spec("azure.cognitiveservices.speech") is not None
                    else "azure-cognitiveservices-speech is not installed."
                ),
            )
        )
        azure_configs = resolve_azure_speech_configs()
        checks.append(
            _check(
                "azure_speech_config",
                ok=bool(azure_configs),
                required=True,
                message=(
                    f"Azure Speech credentials are configured ({len(azure_configs)} profile(s))."
                    if azure_configs
                    else (
                        "Missing Azure Speech config. Save Azure credentials in App Settings "
                        "or set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION."
                    )
                ),
                details={
                    "profile_count": len(azure_configs),
                    "profiles": [cfg.get("label") for cfg in azure_configs],
                },
            )
        )
    return checks


def _check_render_stack(*, require_render: bool, require_long_video: bool) -> list[dict[str, Any]]:
    if not (require_render or require_long_video):
        return []
    ffmpeg, ffmpeg_err = resolve_ffmpeg_executable()
    ffprobe = resolve_ffprobe_executable()

    ffmpeg_ok = ffmpeg is not None
    ffmpeg_msg = f"ffmpeg available: {ffmpeg}" if ffmpeg is not None else (ffmpeg_err or "ffmpeg not found.")
    ffmpeg_details: dict[str, Any] = {"path": ffmpeg}
    if ffmpeg is not None:
        ffmpeg_ok, ffmpeg_msg, ffmpeg_details = _probe_executable(ffmpeg, "ffmpeg")

    ffprobe_ok = ffprobe is not None
    ffprobe_msg = (
        f"ffprobe available: {ffprobe}"
        if ffprobe is not None
        else "ffprobe not found: set FFPROBE_BIN or add ffprobe to PATH."
    )
    ffprobe_details: dict[str, Any] = {"path": ffprobe}
    if ffprobe is not None:
        ffprobe_ok, ffprobe_msg, ffprobe_details = _probe_executable(ffprobe, "ffprobe")

    return [
        _check(
            "ffmpeg",
            ok=ffmpeg_ok,
            required=True,
            message=ffmpeg_msg,
            details=ffmpeg_details,
        ),
        _check(
            "ffprobe",
            ok=ffprobe_ok,
            required=True,
            message=ffprobe_msg,
            details=ffprobe_details,
        ),
    ]


def _check_ocr_provider(*, require_ocr: bool, ocr_provider: str = "paddleocr") -> list[dict[str, Any]]:
    if not require_ocr:
        return []
    from engine.ocr import canonical_provider_name

    canonical = canonical_provider_name(ocr_provider)
    checks: list[dict[str, Any]] = [
        _check(
            "ocr_provider",
            ok=bool(canonical),
            required=True,
            message=(
                f"OCR provider {canonical!r} is supported."
                if canonical
                else f"Unknown OCR provider {ocr_provider!r}. Supported: paddleocr, rapidocr."
            ),
            details={"provider": canonical or (ocr_provider or "").strip().lower()},
        )
    ]
    if canonical == "rapidocr":
        pkg_ok = importlib.util.find_spec("rapidocr_onnxruntime") is not None
        checks.append(
            _check(
                "rapidocr_package",
                ok=pkg_ok,
                required=True,
                message=(
                    "rapidocr_onnxruntime is installed."
                    if pkg_ok
                    else (
                        "rapidocr_onnxruntime missing. Install with: "
                        "pip install rapidocr_onnxruntime"
                    )
                ),
                details={"rapidocr_present": pkg_ok},
            )
        )
        cuda_available = False
        cuda_detail: dict[str, Any] = {}
        try:
            import onnxruntime as ort  # type: ignore

            providers = list(ort.get_available_providers())
            cuda_available = "CUDAExecutionProvider" in providers
            cuda_detail = {"onnx_providers": providers}
        except Exception as exc:
            cuda_detail = {"probe_error": str(exc)[:200]}
        checks.append(
            _check(
                "ocr_device_probe",
                ok=True,
                required=False,
                message=(
                    f"RapidOCR will use {'GPU' if cuda_available else 'CPU'} (auto-detected)."
                    if pkg_ok
                    else "RapidOCR not installed; device probe skipped."
                ),
                details={"cuda_available": cuda_available, **cuda_detail},
            )
        )
        return checks

    # Default: paddleocr path
    paddle_ok = importlib.util.find_spec("paddle") is not None
    paddleocr_ok = importlib.util.find_spec("paddleocr") is not None
    checks.append(
        _check(
            "paddleocr_package",
            ok=paddle_ok and paddleocr_ok,
            required=True,
            message=(
                "paddleocr + paddlepaddle are installed."
                if paddle_ok and paddleocr_ok
                else (
                    "paddleocr/paddlepaddle missing. Install with: "
                    "pip install paddleocr paddlepaddle"
                )
            ),
            details={
                "paddle_present": paddle_ok,
                "paddleocr_present": paddleocr_ok,
            },
        )
    )
    cuda_available = False
    cuda_detail = {}
    if paddle_ok:
        try:
            import paddle  # type: ignore

            compiled = bool(paddle.device.is_compiled_with_cuda())
            count = 0
            try:
                count = int(paddle.device.cuda.device_count())
            except Exception:
                count = 0
            cuda_available = compiled and count > 0
            cuda_detail = {"compiled_with_cuda": compiled, "device_count": count}
        except Exception as exc:
            cuda_detail = {"probe_error": str(exc)[:200]}
    checks.append(
        _check(
            "ocr_device_probe",
            ok=True,
            required=False,
            message=(
                f"PaddleOCR will use {'GPU' if cuda_available else 'CPU'} (auto-detected)."
                if paddle_ok
                else "PaddleOCR not installed; device probe skipped."
            ),
            details={"cuda_available": cuda_available, **cuda_detail},
        )
    )
    return checks


def _check_download_stack(*, require_download: bool) -> list[dict[str, Any]]:
    if not require_download:
        return []
    yt_ok, yt_msg, yt_details = probe_yt_dlp_health()
    return [
        _check(
            "yt_dlp",
            ok=yt_ok,
            required=True,
            message=yt_msg,
            details=yt_details,
        )
    ]


def _capability_ok(checks: list[dict[str, Any]], *names: str) -> bool:
    named = {
        str(check.get("name")): bool(check.get("ok"))
        for check in checks
        if isinstance(check, dict) and isinstance(check.get("name"), str)
    }
    return all(named.get(name, False) for name in names)


def _build_capabilities(
    checks: list[dict[str, Any]],
    *,
    translate_backend: str,
    tts_provider: str,
    require_download: bool,
    require_render: bool,
    require_long_video: bool,
    require_ocr: bool,
) -> dict[str, Any]:
    backend = (translate_backend or "block_v2").strip().lower()
    provider = _normalize_provider(tts_provider)
    translate_ready = True if backend != "block_v2" else _capability_ok(checks, "openai_api_key")
    if provider == "edge_tts":
        tts_ready = _capability_ok(checks, "tts_provider", "edge_tts_package", "ffmpeg_for_tts")
    elif provider == "azure_tts":
        tts_ready = _capability_ok(checks, "tts_provider", "azure_speech_package", "azure_speech_config")
    else:
        tts_ready = False
    render_ready = not require_render or _capability_ok(checks, "ffmpeg", "ffprobe")
    long_video_ready = not require_long_video or _capability_ok(checks, "ffmpeg", "ffprobe")
    download_ready = not require_download or _capability_ok(checks, "yt_dlp")
    ocr_ready = not require_ocr or (
        _capability_ok(checks, "ocr_provider", "paddleocr_package")
        or _capability_ok(checks, "ocr_provider", "rapidocr_package")
    )
    return {
        "download_ready": download_ready,
        "translate_ready": translate_ready,
        "tts_ready": tts_ready,
        "render_ready": render_ready,
        "long_video_ready": long_video_ready,
        "ocr_ready": ocr_ready,
        "provider_requires_network": provider in {"edge_tts", "azure_tts"},
    }


def build_preflight_report(
    *,
    job_workspace: str | Path | None = None,
    translate_backend: str = "block_v2",
    tts_provider: str = "edge_tts",
    api_key: str = "",
    require_download: bool = False,
    require_input: bool = False,
    require_render: bool = False,
    require_long_video: bool = False,
    require_ocr: bool = False,
    ocr_provider: str = "paddleocr",
) -> dict[str, Any]:
    workspace_path = None
    if job_workspace:
        workspace_path = Path(job_workspace).expanduser().resolve()

    checks: list[dict[str, Any]] = []
    checks.extend(_check_workspace(workspace_path, require_input=require_input))
    checks.extend(_check_download_stack(require_download=require_download))
    checks.extend(_check_translate_backend(translate_backend, api_key=api_key))
    checks.extend(_check_tts_provider(tts_provider))
    checks.extend(
        _check_render_stack(require_render=require_render, require_long_video=require_long_video)
    )
    checks.extend(_check_ocr_provider(require_ocr=require_ocr, ocr_provider=ocr_provider))
    ok = all(check["ok"] for check in checks if check.get("required", False))
    capabilities = _build_capabilities(
        checks,
        translate_backend=translate_backend,
        tts_provider=tts_provider,
        require_download=require_download,
        require_render=require_render,
        require_long_video=require_long_video,
        require_ocr=require_ocr,
    )
    return {
        "ok": ok,
        "profile": "runtime_doctor",
        "job_workspace": str(workspace_path) if workspace_path else None,
        "translate_backend": (translate_backend or "block_v2").strip().lower(),
        "tts_provider": _normalize_provider(tts_provider),
        "require_download": bool(require_download),
        "require_input": bool(require_input),
        "require_render": bool(require_render),
        "require_long_video": bool(require_long_video),
        "require_ocr": bool(require_ocr),
        "ocr_provider": (ocr_provider or "paddleocr").strip().lower(),
        "hostname": socket.gethostname(),
        "capabilities": capabilities,
        "checks": checks,
    }
