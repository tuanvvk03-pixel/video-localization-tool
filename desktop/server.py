"""Local HTTP shell for the single-video workflow (Phase 3 UI MVP).

Runs a zero-dependency stdlib HTTP server that serves a single-page editor and
proxies JSON requests to the Phase 2/3 backend APIs:
    engine.voice_edit_api    (status, load, save, mark_voice_edited, seed)
    engine.app_cli           (init_job via _cmd_init_job helpers)
    engine.run_job           (full pipeline for run-until-edit / run-after-edit)

Run:
    python -m desktop.server [--host 127.0.0.1] [--port 8765] [--workspace-root <dir>]

All endpoints return {"ok": true, "data": ...} or {"ok": false, "error": {"code","message"}}.
Long-running endpoints (/api/run-until-edit, /api/run-after-edit) block the request —
the UI shows a spinner until they finish.
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import argparse
import asyncio
import contextlib
import contextvars
import filecmp
import hashlib
import io
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from desktop.server_errors import classify_error_details  # noqa: E402
from desktop.job_manager import (  # noqa: E402
    RC_CANCELLED,
    RC_TIMEOUT,
    JobBusyError,
    JobManager,
    ProcessRegistry,
    supervise_process,
)
from desktop.server_shared import (  # noqa: E402
    _err,
    _err_with_log,
    _ok,
    _path_or_none,
    _require,
    _tail_log,
    require_job_workspace,
)
from desktop.server_bgm import (  # noqa: E402
    handle_bgm_remove,
    handle_bgm_save,
    handle_bgm_status,
    handle_bgm_upload,
)

# Managed-mode client (Google login, wallet, managed translate, billing). Optional:
# if httpx isn't installed the app still runs fully in BYOK mode.
try:
    from desktop import cloud_account as _cloud  # noqa: E402
except Exception:  # noqa: BLE001
    _cloud = None  # type: ignore[assignment]
from engine import run_job  # noqa: E402
from engine.external_srt import import_external_srt  # noqa: E402
from engine import run_long_video_stage  # noqa: E402
from engine.input_provenance import (  # noqa: E402
    fingerprint_file,
    invalidate_from_transcribe_downward,
)
from engine.preflight import build_preflight_report  # noqa: E402
from engine.project_manager import (  # noqa: E402
    ProjectError,
    load_project,
)
from desktop.server_project import (  # noqa: E402
    handle_add_video_to_project,
    handle_get_project,
    handle_init_project,
    handle_save_video_override,
)
from engine.runtime_app_settings import (  # noqa: E402
    resolve_openai_translation_model,
)
from desktop.server_render import (  # noqa: E402
    handle_render_background_remove,
    handle_render_background_upload,
    handle_render_intro_remove,
    handle_render_intro_upload,
    handle_render_logo_remove,
    handle_render_logo_upload,
    handle_render_outro_remove,
    handle_render_outro_upload,
    handle_render_settings_save,
    handle_render_settings_status,
)
from engine.segment_manager import (  # noqa: E402
    SINGLE_VIDEO_THRESHOLD_S,
    SegmentError,
    load_segment_manifest,
    merge_srts_with_offsets,
    merge_segment_final_subtitles,
    probe_video_duration,
)
from engine.srt_cues import SRTCue, cues_to_srt  # noqa: E402
from engine.srt_cues import parse_srt_cues  # noqa: E402
from engine.subtitle_text import read_subtitle_file  # noqa: E402
from engine.voice_edit_api import (  # noqa: E402
    VoiceEditError,
    get_voice_edit_status,
    load_voice_overrides,
    load_voice_subtitle_cues,
    mark_voice_edited,
    save_edited_voice,
    save_voice_overrides,
    seed_edited_voice,
)
from engine.video_download import (  # noqa: E402
    VideoDownloadError,
    default_url_download_workspace_root,
    init_job_from_url,
    probe_video_url,
)
from desktop.server_style import (  # noqa: E402
    handle_get_project_style,
    handle_get_video_style,
    handle_save_project_style,
    handle_save_video_style,
)
from engine.tts import get_tts_provider  # noqa: E402
from engine.tts_settings import (  # noqa: E402
    TTSSettingsError,
    tts_rate_to_provider_arg,
    validate_settings as validate_tts_settings,
)
from desktop.server_tts import (  # noqa: E402
    handle_get_project_tts,
    handle_get_video_tts,
    handle_save_project_tts,
    handle_save_video_tts,
)
from desktop.server_voices import (  # noqa: E402
    handle_list_system_fonts,
    handle_list_voices,
    handle_refresh_voices,
    handle_toggle_voice,
)
from desktop.server_pickers import (  # noqa: E402
    handle_pick_file,
    handle_pick_files,
    handle_pick_folder,
    handle_pick_srt_file,
    handle_reveal,
)
from desktop.server_app_settings import (  # noqa: E402
    _load_app_settings,
    handle_check_openai_key,
    handle_get_app_settings,
    handle_save_app_settings,
)
from desktop.server_ocr import (  # noqa: E402
    handle_inspect_local_video,
    handle_ocr_diagnostics,
    handle_ocr_test_frame,
)
from desktop.server_extractor import (  # noqa: E402
    _VALID_EXTRACTORS,
    _VALID_OCR_PROVIDERS,
    _normalize_extractor_settings,
    _normalize_ocr_provider,
    _normalize_source_language,
)
from desktop.server_import_config import (  # noqa: E402
    _clean_import_config,
    _load_import_config,
    _load_json_file,
    _resolve_job_workspace_for_body,
    _save_import_config,
    handle_get_import_config,
    handle_import_external_srt,
    handle_save_import_config,
)
from desktop.server_progress import (  # noqa: E402
    _count_srt_cues,
    _normalize_stage_name,
    _progress_payload,
    _progress_subtitle_extractor,
    _read_ocr_progress,
    _read_render_progress_us,
    _safe_stage_rank,
    _stage_label,
    _status_label,
    _substage_fraction,
    _weighted_percent,
)
from desktop.server_dashboard import (  # noqa: E402
    _is_video_workspace,
    _job_summary,
    handle_list_artifacts,
    handle_list_jobs,
    handle_list_segments,
)
from desktop.server_events import iter_job_event_frames  # noqa: E402
from desktop.server_voice_samples import (  # noqa: E402
    handle_list_voice_samples,
    handle_remove_voice_sample,
    handle_upload_voice_sample,
)
from engine.run_tts_stage import DEFAULT_TTS_VOICE  # noqa: E402

STATIC_DIR = Path(__file__).resolve().parent / "static"
_JOB_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")

# Background runner for the long pipeline jobs (run-until-edit / run-after-edit).
# Keyed by job-workspace path so a workspace can only run one job at a time.
JOB_MANAGER = JobManager(max_workers=4)

# Live child processes for async runs, so /api/cancel-job can hard-kill them.
PROC_REGISTRY = ProcessRegistry()

# When set (async path only), _run_job_common runs run_job as a child process
# instead of in-process, enabling real cancellation and timeout. Sync/CLI/test
# callers leave it unset and keep the original in-process execution.
_RUN_CONTEXT: "contextvars.ContextVar[Optional[dict[str, Any]]]" = contextvars.ContextVar(
    "vl_run_context", default=None
)

# Hard wall-clock cap for a single async run before it is force-killed.
JOB_TIMEOUT_S = float(os.environ.get("VL_JOB_TIMEOUT_S") or 3600)

# Error classification lives in a dedicated module (first extraction from this
# monolith). Re-bound to the historical private name so existing call sites
# stay untouched.
_classify_error_details = classify_error_details

# Upper bound on a POST body. Even though the server binds to localhost, an
# oversized or malformed Content-Length must not let a single request read an
# unbounded payload into memory. 64 MiB is far above any legitimate request
# (the largest bodies are SRT text / inline subtitle uploads).
MAX_REQUEST_BODY_BYTES = 64 * 1024 * 1024
# Cap how much of an error string we echo back so a runaway message (e.g. a huge
# subprocess dump) can't bloat the JSON response.
MAX_ERROR_MESSAGE_CHARS = 4000

_DEFAULT_TTS_PREVIEW_TEXT = "Phụ đề đang hiện ở đây"


def _slug(name: str) -> str:
    s = _JOB_ID_RE.sub("-", name).strip("-._")
    return s or "job"


def _default_jobs_root() -> Path:
    return (REPO_ROOT / "Job").resolve()


def _auto_job_id_for_video(video: Path) -> str:
    stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    return f"{stamp}_{_slug(video.stem)}"


def _preview_cache_paths(jw: Path, *, provider: str, voice: str, rate: str, text: str) -> tuple[Path, Path, str]:
    cache_key = hashlib.sha256(f"{provider}|{voice}|{rate}|{text}".encode("utf-8")).hexdigest()[:16]
    cache_dir = jw / "_voice_preview_cache"
    return cache_dir / f"{cache_key}.wav", cache_dir / f"{cache_key}.json", cache_key


def _cleanup_preview_cache(cache_dir: Path, *, max_wavs: int = 200) -> None:
    try:
        wavs = [p for p in cache_dir.glob("*.wav") if p.is_file()]
    except OSError:
        return
    if len(wavs) <= max_wavs:
        return
    wavs.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0)
    for wav in wavs[: max(0, len(wavs) - max_wavs)]:
        with contextlib.suppress(OSError):
            wav.unlink()
        with contextlib.suppress(OSError):
            wav.with_suffix(".json").unlink()


def _read_preview_cache_meta(meta_path: Path) -> dict[str, Any]:
    if not meta_path.is_file():
        return {}
    try:
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _workspace_rel_path(path: Path, workspace: Path) -> str:
    try:
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _tts_rate_arg_from_payload(body: dict[str, Any]) -> str:
    raw_rate = body.get("tts_rate")
    if isinstance(raw_rate, str):
        s = raw_rate.strip()
        if not s:
            return ""
        if s.endswith("%"):
            s = s[:-1]
        if s.startswith("+"):
            s = s[1:]
        cleaned = validate_tts_settings({"tts_rate": s})
        return tts_rate_to_provider_arg(int(cleaned["tts_rate"]))
    raw = {
        "tts_rate": raw_rate,
        "speed_multiplier": body.get("speed_multiplier"),
    }
    cleaned = validate_tts_settings(raw)
    if "tts_rate" not in cleaned:
        return ""
    return tts_rate_to_provider_arg(int(cleaned["tts_rate"]))


class _Tee(io.TextIOBase):
    """Write to two text streams at once — used to fan out stdout/stderr to run.log."""

    def __init__(self, primary: Any, secondary: Any) -> None:
        self._primary = primary
        self._secondary = secondary

    def write(self, s: str) -> int:  # type: ignore[override]
        try:
            self._primary.write(s)
        except Exception:  # noqa: BLE001
            pass
        try:
            self._secondary.write(s)
            self._secondary.flush()
        except Exception:  # noqa: BLE001
            pass
        return len(s)

    def flush(self) -> None:  # type: ignore[override]
        for s in (self._primary, self._secondary):
            try:
                s.flush()
            except Exception:  # noqa: BLE001
                pass


def _ping_server(url: str, timeout: float = 1.0) -> bool:
    req = urllib.request.Request(f"{url.rstrip('/')}/api/ping", method="POST", data=b"{}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (OSError, ValueError, urllib.error.URLError):
        return False
    return bool(payload.get("ok")) and payload.get("data", {}).get("status") == "ok"


def _build_init_job_payload(
    *,
    video: Path,
    workspace_root: Path,
    used_default_workspace_root: bool,
    job_id: str,
    job_workspace: Path,
    dst: Path,
) -> dict[str, Any]:
    duration_s: float | None = None
    try:
        duration_s = float(probe_video_duration(dst))
    except (OSError, SegmentError, ValueError):
        duration_s = None
    return {
        "job_id": job_id,
        "workspace_root": str(workspace_root),
        "used_default_workspace_root": used_default_workspace_root,
        "job_workspace": str(job_workspace.resolve()),
        "input_video_path": str(dst.resolve()),
        "input_video_fingerprint": fingerprint_file(dst),
        "source_name": video.name,
        "source_duration_s": duration_s,
    }


def _can_reuse_existing_workspace(job_workspace: Path, video: Path) -> bool:
    dst = job_workspace / "input" / "source.mp4"
    if not dst.is_file():
        return False
    try:
        if video.resolve() == dst.resolve():
            return True
    except OSError:
        pass
    try:
        return filecmp.cmp(video, dst, shallow=False)
    except OSError:
        return False


def handle_init_job(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "video")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    video = Path(str(body["video"])).expanduser()
    if not video.is_file():
        return _err("video_not_found", f"Video file does not exist: {video}")
    raw_workspace_root = str(body.get("workspace_root") or "").strip()
    used_default_workspace_root = not raw_workspace_root
    workspace_root = (
        _default_jobs_root()
        if used_default_workspace_root
        else Path(raw_workspace_root).expanduser()
    )
    try:
        # resolve() without strict so we can create it if missing
        workspace_root = workspace_root.resolve()
    except OSError:
        workspace_root = (
            _default_jobs_root()
            if used_default_workspace_root
            else Path(raw_workspace_root).expanduser()
        )
    if workspace_root.exists() and not workspace_root.is_dir():
        return _err(
            "workspace_root_not_dir",
            f"Workspace root must be a directory, not a file: {workspace_root}",
        )
    try:
        workspace_root.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return _err("workspace_root_create_failed", f"Could not create workspace root: {e}")
    raw_job_id = str(body.get("job_id") or "").strip()
    job_id = raw_job_id or (
        _auto_job_id_for_video(video)
        if used_default_workspace_root
        else _slug(video.stem)
    )
    jw = workspace_root / job_id
    force = bool(body.get("force"))
    if jw.exists() and any(jw.iterdir()) and not force:
        if _can_reuse_existing_workspace(jw, video):
            dst = jw / "input" / "source.mp4"
            return _ok(
                _build_init_job_payload(
                    video=video,
                    workspace_root=workspace_root,
                    used_default_workspace_root=used_default_workspace_root,
                    job_id=job_id,
                    job_workspace=jw,
                    dst=dst,
                )
            )
        return _err(
            "workspace_exists",
            f"Workspace already exists and is not empty: {jw}. Pass force=true to reuse.",
        )
    (jw / "input").mkdir(parents=True, exist_ok=True)
    (jw / "artifacts").mkdir(parents=True, exist_ok=True)
    dst = jw / "input" / "source.mp4"
    try:
        # Windows sometimes errors when copying onto an existing path, especially
        # when reusing a workspace. In force-reuse mode, allow overwriting.
        src_resolved = video.resolve()
        try:
            dst_resolved = dst.resolve(strict=True)
        except (OSError, FileNotFoundError):
            dst_resolved = dst.resolve()

        if src_resolved == dst_resolved:
            # User picked the already-imported source inside this workspace.
            # Treat as a no-op copy.
            pass
        else:
            if force and dst.exists():
                try:
                    dst.unlink()
                except OSError:
                    # If we cannot remove it, we will fall back to copyfile which
                    # will surface the real error.
                    pass
            shutil.copyfile(video, dst)
    except OSError as e:
        return _err("copy_failed", str(e))
    return _ok(
        _build_init_job_payload(
            video=video,
            workspace_root=workspace_root,
            used_default_workspace_root=used_default_workspace_root,
            job_id=job_id,
            job_workspace=jw,
            dst=dst,
        )
    )


def handle_default_download_root(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    _ = body
    root = default_url_download_workspace_root()
    return _ok({"workspace_root": str(root)})


def handle_probe_video_url(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "url")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    try:
        return _ok(probe_video_url(str(body["url"])))
    except VideoDownloadError as e:
        return _err("video_probe_failed", str(e))


def handle_init_job_from_url(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "url", "workspace_root")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    try:
        payload = init_job_from_url(
            url=str(body["url"]),
            workspace_root=str(body["workspace_root"]),
            job_id=str(body.get("job_id") or ""),
            force=bool(body.get("force")),
        )
    except VideoDownloadError as e:
        msg = str(e)
        if "Workspace already exists" in msg:
            return _err("workspace_exists", msg)
        return _err("video_download_failed", msg)
    return _ok(payload)


def _status_payload(jw: Path) -> dict[str, Any]:
    st = get_voice_edit_status(jw)
    is_long = (jw / "segments" / "manifest.json").is_file()
    js = _load_json_file(jw / "job_state.json")
    vs = _load_json_file(jw / "video_state.json")
    transcription_engine = str(vs.get("transcription_engine") or js.get("transcription_engine") or "")
    subtitle_extractor = str(vs.get("subtitle_extractor") or js.get("subtitle_extractor") or "")
    ext_manifest = _load_json_file(jw / "artifacts" / "transcribe" / "external_srt_manifest.json")
    ext_origin = None
    if isinstance(ext_manifest, dict):
        ext_origin = ext_manifest.get("source_path")
    return {
        "job_workspace": str(jw),
        "voice_edit_status": st.voice_edit_status,
        "voice_edited": st.voice_edited,
        "source_mode": st.source_mode,
        "edited_voice_path": _path_or_none(st.edited_voice_path),
        "translated_voice_path": _path_or_none(st.translated_voice_path),
        "edit_manifest_path": _path_or_none(st.edit_manifest_path),
        "is_long_video": is_long,
        "transcription_engine": transcription_engine,
        "subtitle_extractor": subtitle_extractor,
        "external_srt_origin": ext_origin,
    }


_SOURCE_TEXT_PREFERENCES = (
    ("source_cleaned_zh", Path("artifacts") / "transcribe" / "source_cleaned_zh.srt"),
    ("source", Path("artifacts") / "transcribe" / "source.srt"),
)
_REFERENCE_VOICE_REL = Path("artifacts") / "translate" / "translated_voice.srt"


def _serialize_cues(cues: list[SRTCue]) -> list[dict[str, Any]]:
    return [
        {"index": c.index, "start_ms": c.start_ms, "end_ms": c.end_ms, "text": c.text}
        for c in cues
    ]


def _load_source_provenance(jw: Path) -> dict[str, Any] | None:
    """Return the fuse provenance manifest if the transcribe stage emitted one."""
    prov_path = jw / "artifacts" / "transcribe" / "source_provenance.json"
    if not prov_path.is_file():
        return None
    try:
        data = json.loads(prov_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _load_optional_srt_cues(path: Path | None) -> list[SRTCue]:
    if path is None or not path.is_file():
        return []
    try:
        return parse_srt_cues(read_subtitle_file(path).text)
    except OSError:
        return []


def _pick_source_text_subtitle(jw: Path) -> tuple[str, Path | None]:
    for mode, rel in _SOURCE_TEXT_PREFERENCES:
        path = jw / rel
        if path.is_file():
            return mode, path
    return "missing", None


def _should_use_long_video_flow(jw: Path) -> tuple[bool, str | None]:
    """
    Decide whether to use the long-video flow for this workspace.

    - If segments/manifest.json exists => treat as long-video parent workspace.
    - Else probe input/source.mp4 duration via ffprobe:
        - duration <= 5 min => short/single flow
        - duration > 5 min  => long-video flow
    """
    if (jw / "segments" / "manifest.json").is_file():
        return True, None
    src = jw / "input" / "source.mp4"
    if not src.is_file():
        # Preserve legacy behavior for unit tests / partial workspaces:
        # if input video is missing, do not block at the router layer.
        return False, None
    try:
        dur_s = float(probe_video_duration(src))
    except SegmentError as e:
        # If we cannot probe duration (e.g. ffprobe missing), fall back to the
        # short flow instead of blocking the UI endpoints.
        return False, None
    return dur_s > float(SINGLE_VIDEO_THRESHOLD_S), None


def _transcribe_args() -> list[str]:
    """Transcription (ASR) flags for a desktop run. ASR is the core feature, so
    the defaults favour ACCURACY (large-v3 + beam search) over speed. Overridable
    via App Settings: transcribe_model_size / transcribe_device /
    transcribe_beam_size / transcribe_best_of."""
    s = _load_app_settings()
    model = str(s.get("transcribe_model_size") or "large-v3").strip() or "large-v3"
    device = str(s.get("transcribe_device") or "cpu").strip() or "cpu"
    try:
        beam = max(1, int(s.get("transcribe_beam_size") or 5))
    except (TypeError, ValueError):
        beam = 5
    try:
        best_of = max(1, int(s.get("transcribe_best_of") or 5))
    except (TypeError, ValueError):
        best_of = 5
    return [
        "--transcribe-model-size", model,
        "--transcribe-device", device,
        "--transcribe-beam-size", str(beam),
        "--transcribe-best-of", str(best_of),
    ]


def _resolve_openai_api_key(body: dict[str, Any]) -> str:
    direct = str(body.get("api_key") or "").strip()
    if direct:
        return direct
    settings = _load_app_settings()
    saved = str(settings.get("openai_api_key") or "").strip()
    if saved:
        return saved
    return str(os.environ.get("OPENAI_API_KEY") or "").strip()


def _long_cfg_from_body(body: dict[str, Any], *, project_name: str) -> dict[str, Any]:
    cfg = {
        "project_name": project_name,
        "project_root": str(body.get("project_root") or ""),
        "api_key": str(body.get("api_key") or ""),
        "source_language": _normalize_source_language(body.get("source_language")),
        "translate_backend": str(body.get("translate_backend") or "block_v2"),
        "tts_provider": str(body.get("tts_provider") or "edge_tts"),
        "tts_voice": str(body.get("tts_voice") or ""),
        "tts_rate": _tts_rate_arg_from_payload(body),
        "mix_mode": str(body.get("mix_mode") or "replace_original_speech"),
        "render_subtitle_mode": str(body.get("subtitle_mode") or "burn"),
        "enable_translation_qa": bool(body.get("enable_translation_qa")),
        "enable_source_cleanup": bool(body.get("enable_source_cleanup")),
    }
    if body.get("mix_duck_gain_db") is not None:
        try:
            cfg["mix_duck_gain_db"] = float(validate_tts_settings(
                {"mix_duck_gain_db": body.get("mix_duck_gain_db")}
            )["mix_duck_gain_db"])
        except TTSSettingsError:
            pass
    return cfg


def handle_status(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "job_workspace")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    return _ok(_status_payload(jw))


def handle_load(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "job_workspace")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    mode, cues = load_voice_subtitle_cues(jw)
    source_text_mode, source_text_path = _pick_source_text_subtitle(jw)
    source_cues = _load_optional_srt_cues(source_text_path)
    if mode == "missing":
        if not source_cues:
            return _err("voice_subtitle_missing", "No voice subtitle found yet.")
        mode = "source_text"
        cues = list(source_cues)
    reference_path = jw / _REFERENCE_VOICE_REL
    reference_cues = _load_optional_srt_cues(reference_path)
    reference_mode = "translated_voice" if reference_cues else mode
    if not reference_cues:
        reference_cues = list(cues)
    return _ok(
        {
            "source_mode": mode,
            "cues": _serialize_cues(cues),
            "source_text_mode": source_text_mode,
            "source_cues": _serialize_cues(source_cues),
            "reference_mode": reference_mode,
            "reference_cues": _serialize_cues(reference_cues),
            "source_provenance": _load_source_provenance(jw),
        }
    )


def _cues_from_payload(raw: Any) -> list[SRTCue]:
    out: list[SRTCue] = []
    if not isinstance(raw, list):
        raise ValueError("cues must be a list")
    for i, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"cue #{i} is not an object")
        try:
            start = int(item["start_ms"])
            end = int(item["end_ms"])
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f"cue #{i} has invalid start_ms/end_ms") from e
        text = str(item.get("text") or "").strip()
        if not text:
            raise ValueError(f"cue #{i} has empty text")
        out.append(SRTCue(index=int(item.get("index") or i), start_ms=start, end_ms=end, text=text))
    return out


def handle_save(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "job_workspace", "cues")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    try:
        cues = _cues_from_payload(body["cues"])
    except ValueError as e:
        return _err("invalid_cues", str(e))
    if not cues:
        return _err("invalid_cues", "cues is empty")
    srt_text = cues_to_srt(cues)
    try:
        out = save_edited_voice(jw, edited_voice_text=srt_text, note=body.get("note") or None)
    except VoiceEditError as e:
        return _err("save_failed", str(e))
    return _ok({"edited_voice_path": str(out.resolve()), "cue_count": len(cues)})


def handle_get_voice_overrides(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    jw, err = require_job_workspace(body)
    if err is not None:
        return err
    return _ok({"overrides": load_voice_overrides(jw)})


def handle_save_voice_overrides(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    jw, err = require_job_workspace(body)
    if err is not None:
        return err
    cleaned = save_voice_overrides(jw, body.get("overrides"))
    return _ok({"overrides": cleaned})


def handle_mark_edited(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "job_workspace")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    try:
        mark_voice_edited(jw)
    except VoiceEditError as e:
        return _err("mark_failed", str(e))
    return _ok(_status_payload(jw))


def handle_upload_translation(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Replace edited_voice.srt from raw SRT text; cue count must match transcribed source.srt."""
    missing = _require(body, "job_workspace", "srt_text")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    source_srt = jw / "artifacts" / "transcribe" / "source.srt"
    if not source_srt.is_file():
        return _err("source_srt_missing", f"Missing {source_srt} (need transcribe output to validate cue count).")
    try:
        src_res = read_subtitle_file(source_srt)
        src_cues = parse_srt_cues(src_res.text)
    except OSError as e:
        return _err("source_srt_read_failed", str(e))
    if not src_cues:
        return _err("source_srt_empty", "source.srt has no cues to match against.")
    raw = str(body.get("srt_text") or "")
    up_cues = parse_srt_cues(raw)
    if not up_cues:
        return _err("invalid_srt", "Uploaded SRT has no valid cues.")
    if len(up_cues) != len(src_cues):
        return _err(
            "cue_count_mismatch",
            f"Cue count must match source.srt: expected {len(src_cues)}, got {len(up_cues)}.",
        )
    canonical = cues_to_srt(up_cues)
    try:
        save_edited_voice(jw, edited_voice_text=canonical, note=str(body.get("note") or "upload_translation"))
        mark_voice_edited(jw)
    except VoiceEditError as e:
        return _err("upload_failed", str(e))
    return _ok({**_status_payload(jw), "cue_count": len(up_cues)})


def handle_read_subtitle_file(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Read a local subtitle/text file and return its normalized text.

    Used by desktop-only screens that need to load SRT content from an absolute OS path.
    """
    missing = _require(body, "path")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    raw = str(body.get("path") or "").strip()
    if not raw:
        return _err("missing_field", "Missing required field: path")
    path = Path(raw).expanduser()
    try:
        resolved = path.resolve(strict=True)
    except (OSError, FileNotFoundError):
        return _err("path_not_found", f"Path not found: {path}")
    if not resolved.is_file():
        return _err("path_not_found", f"Path not found: {resolved}")

    try:
        res = read_subtitle_file(resolved)
    except Exception as e:
        return _err("read_failed", f"Could not read subtitle file: {e}")

    return _ok({"path": str(resolved), "name": resolved.name, "text": res.text})


def handle_translate_srt(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Translate arbitrary SRT text and return translated SRT strings.

    This endpoint is workspace-independent: it accepts raw SRT text and runs the same
    translator backend used by the pipeline to produce a voice-oriented translation.
    """
    missing = _require(body, "srt_text")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")

    raw = str(body.get("srt_text") or "")
    cues = parse_srt_cues(raw)
    if not cues:
        return _err("invalid_srt", "Input SRT has no valid cues.")

    translate_backend = str(body.get("translate_backend") or "block_v2").strip().lower()
    if translate_backend not in {"block_v2", "legacy"}:
        translate_backend = "block_v2"

    api_key = _resolve_openai_api_key(body)
    if not api_key and not _managed_mode_on():
        return _err(
            "api_key_required",
            "OpenAI API key is required to translate SRT. Save it in App Settings or pass api_key.",
        )

    # NOTE: For this dedicated translate screen we currently support block_v2 only.
    # legacy backend expects file-based project context via translate_cli; we keep this endpoint minimal.
    if translate_backend != "block_v2":
        return _err(
            "translate_backend_unsupported",
            "translate_backend=legacy is not supported for SRT-only translation. Use block_v2.",
        )

    try:
        model = str(body.get("model") or resolve_openai_translation_model()).strip() or resolve_openai_translation_model()
        block_size = int(body.get("block_size") or 30)
        context_cues = int(body.get("context_cues") or 2)
        qa_enabled = bool(body.get("enable_translation_qa", False))
    except Exception:
        model = resolve_openai_translation_model()
        block_size = 30
        context_cues = 2
        qa_enabled = False

    try:
        # Lazy import so desktop/server.py can still start without openai installed
        # until the user uses this endpoint.
        from engine.block_translate import translate_blocks_two_pass, render_srt  # noqa: PLC0415

        results, qa_items, meta = translate_blocks_two_pass(
            cues=cues,
            api_key=api_key,
            model=model,
            glossary_path=(REPO_ROOT / "data" / "glossary_global.json"),
            block_size=block_size,
            context_cues=context_cues,
            qa_enabled=qa_enabled,
        )
        voice_map = {idx: r.voice for idx, r in results.items()}
        display_map = {idx: r.display for idx, r in results.items()}
        voice_srt = render_srt(cues, voice_map)
        display_srt = render_srt(cues, display_map)
    except Exception as e:
        return _err("translate_failed", f"Translate failed: {e}")

    return _ok(
        {
            "translate_backend": "block_v2",
            "model": model,
            "cue_count": len(cues),
            "voice_srt": voice_srt,
            "display_srt": display_srt,
            "qa": [
                {
                    "index": int(it.index),
                    "needs_review": bool(it.needs_review),
                    "score": float(it.score),
                    "flags": list(it.flags),
                }
                for it in (qa_items or [])
            ],
            "meta": meta or {},
        }
    )


def _run_job_common(
    jw: Path,
    *,
    project_name: str,
    api_key: str,
    source_language: str,
    to_stage: str,
    translate_backend: str,
    tts_provider: str,
    tts_voice: str,
    tts_rate: str,
    mix_mode: str,
    enable_translation_qa: bool,
    enable_source_cleanup: bool,
    project_root: str = "",
    render_subtitle_mode: str = "burn",
    mix_duck_gain_db: float | None = None,
    subtitle_extractor: str = "audio_only",
    ocr_provider: str = "",
    ocr_language: str = "",
    ocr_roi: str = "",
    ocr_device: str = "",
) -> int:
    subtitle_extractor = (subtitle_extractor or "audio_only").strip().lower()
    if subtitle_extractor in {"ocr_only", "hybrid"}:
        sys.stderr.write(
            f"[desktop.server] Deprecated subtitle_extractor={subtitle_extractor!r} "
            "in run pipeline; using audio_only.\n"
        )
        subtitle_extractor = "audio_only"
        ocr_provider = ""
        ocr_language = ""
        ocr_roi = ""
        ocr_device = ""
    argv = [
        "--job-workspace",
        str(jw),
        "--project-name",
        project_name,
        "--to-stage",
        to_stage,
        # Accuracy-first ASR (large-v3 + beam search); tunable in App Settings.
        *_transcribe_args(),
        "--finalize-mode",
        "voice",
        "--translate-backend",
        translate_backend,
        "--tts-provider",
        tts_provider,
        "--mix-mode",
        mix_mode,
        "--render-subtitle-mode",
        render_subtitle_mode,
    ]
    if api_key.strip():
        argv.extend(["--api-key", api_key.strip()])
    if source_language.strip():
        argv.extend(["--transcribe-language", source_language.strip()])
    if tts_voice.strip():
        argv.extend(["--tts-voice", tts_voice.strip()])
    if tts_rate.strip():
        argv.extend(["--tts-rate", tts_rate.strip()])
    if mix_duck_gain_db is not None:
        argv.extend(["--duck-gain-db", str(mix_duck_gain_db)])
    if enable_translation_qa:
        argv.append("--enable-translation-qa")
    if enable_source_cleanup:
        argv.append("--enable-source-cleanup")
    if project_root.strip():
        argv.extend(["--project-root", project_root.strip()])
    extractor = (subtitle_extractor or "audio_only").strip().lower()
    if extractor not in {"audio_only", "ocr_only", "hybrid", "external_srt"}:
        extractor = "audio_only"
    cli_extractor = "audio_only" if extractor == "external_srt" else extractor
    argv.extend(["--extractor", cli_extractor])
    if cli_extractor in {"ocr_only", "hybrid"}:
        prov = _normalize_ocr_provider(ocr_provider)
        if prov:
            argv.extend(["--ocr-provider", prov])
        if ocr_language.strip():
            argv.extend(["--ocr-language", ocr_language.strip()])
        if ocr_roi.strip():
            argv.extend(["--ocr-roi", ocr_roi.strip()])
        dev = (ocr_device or "").strip().lower()
        if dev and dev != "auto":
            argv.extend(["--ocr-device", dev])
    run_ctx = _RUN_CONTEXT.get()
    if run_ctx is not None:
        return _run_job_subprocess(jw, argv, run_ctx, to_stage)

    log_path = jw / "run.log"
    try:
        log_fh = open(log_path, "a", encoding="utf-8")
    except OSError:
        log_fh = None
    try:
        if log_fh is not None:
            log_fh.write(f"\n=== run {to_stage} ===\n")
            log_fh.flush()
            with contextlib.redirect_stdout(_Tee(sys.stdout, log_fh)), \
                    contextlib.redirect_stderr(_Tee(sys.stderr, log_fh)):
                return run_job.main(argv)
        return run_job.main(argv)
    finally:
        if log_fh is not None:
            try:
                log_fh.close()
            except OSError:
                pass


def _run_job_subprocess(
    jw: Path, argv: list[str], run_ctx: dict[str, Any], to_stage: str
) -> int:
    """Run `python -m engine.run_job <argv>` as a child process under supervision.

    Output is appended to run.log (the UI's progress source); the process is
    registered so /api/cancel-job can force-kill it, and a wall-clock timeout
    terminates a hung run. Returns run_job's exit code, or RC_CANCELLED /
    RC_TIMEOUT when we stopped it (the handlers treat any non-zero rc as failed).
    """
    log_path = jw / "run.log"
    try:
        log_fh = open(log_path, "a", encoding="utf-8")
    except OSError:
        log_fh = None
    popen_kwargs: dict[str, Any] = {
        "cwd": str(REPO_ROOT),
        "stdout": log_fh if log_fh is not None else subprocess.DEVNULL,
        "stderr": subprocess.STDOUT,
    }
    if not sys.platform.startswith("win"):
        # New session so terminate_process_tree can signal the whole group.
        popen_kwargs["start_new_session"] = True
    try:
        if log_fh is not None:
            log_fh.write(f"\n=== run {to_stage} (subprocess) ===\n")
            log_fh.flush()
        proc = subprocess.Popen(
            [sys.executable, "-m", "engine.run_job", *argv], **popen_kwargs
        )
        rc = supervise_process(
            proc,
            cancel_event=run_ctx.get("cancel_event"),
            timeout_s=run_ctx.get("timeout_s"),
            registry=PROC_REGISTRY,
            job_id=run_ctx.get("job_id"),
        )
        if log_fh is not None:
            if rc == RC_CANCELLED:
                log_fh.write("[desktop.server] job cancelled by request.\n")
            elif rc == RC_TIMEOUT:
                log_fh.write(
                    f"[desktop.server] job force-killed after timeout "
                    f"({run_ctx.get('timeout_s')}s).\n"
                )
            log_fh.flush()
        return rc
    finally:
        if log_fh is not None:
            try:
                log_fh.close()
            except OSError:
                pass


def _run_long_video_until_transcribed(body: dict[str, Any], job_workspace: Path) -> tuple[int, dict[str, Any]]:
    try:
        run_long_video_stage.do_plan_split(
            job_workspace,
            video=None,
            target_minutes=float(body.get("target_minutes") or 4.0),
            max_minutes=float(body.get("max_minutes") or 5.0),
            force=bool(body.get("force_replan")),
        )
        manifest = load_segment_manifest(job_workspace)
    except (SegmentError, run_long_video_stage.LongVideoError) as e:
        return _err_with_log(job_workspace, "long_video_failed", str(e))

    texts: list[str] = []
    offsets_ms: list[int] = []
    for entry in manifest.segments:
        seg_ws = Path(str(entry.get("workspace") or "")).expanduser().resolve()
        invalidate_from_transcribe_downward(
            seg_ws,
            reason="desktop_manual_review_mode_segment_rebuild",
        )
        rc = _run_job_common(
            seg_ws,
            project_name=str(body["project_name"]),
            api_key=str(body.get("api_key") or ""),
            source_language=_normalize_source_language(body.get("source_language")),
            to_stage="transcribed",
            translate_backend=str(body.get("translate_backend") or "block_v2"),
            tts_provider="edge_tts",
            tts_voice="",
            tts_rate="",
            mix_mode="replace_original_speech",
            enable_translation_qa=bool(body.get("enable_translation_qa")),
            enable_source_cleanup=bool(body.get("enable_source_cleanup")),
            project_root=str(body.get("project_root") or ""),
            subtitle_extractor=str(body.get("subtitle_extractor") or "audio_only"),
            ocr_provider=str(body.get("ocr_provider") or ""),
            ocr_language=str(body.get("ocr_language") or ""),
            ocr_roi=str(body.get("ocr_roi") or ""),
            ocr_device=str(body.get("ocr_device") or ""),
        )
        if rc != 0:
            return _err_with_log(
                job_workspace,
                "long_video_failed",
                f"segment {int(entry.get('index') or 0)} transcribe failed (run_job rc={rc})",
            )
        source_srt = seg_ws / "artifacts" / "transcribe" / "source.srt"
        if not source_srt.is_file():
            return _err(
                "source_srt_missing",
                f"Segment {int(entry.get('index') or 0)} missing source.srt after transcription.",
            )
        texts.append(read_subtitle_file(source_srt).text)
        offsets_ms.append(int(float(entry.get("start_s") or 0.0) * 1000))

    invalidate_from_transcribe_downward(
        job_workspace,
        reason="desktop_manual_review_mode_parent_rebuild",
    )
    merged_source = merge_srts_with_offsets(texts, offsets_ms)
    parent_source_srt = job_workspace / "artifacts" / "transcribe" / "source.srt"
    parent_source_srt.parent.mkdir(parents=True, exist_ok=True)
    parent_source_srt.write_text(merged_source, encoding="utf-8")

    rc = _run_job_common(
        job_workspace,
        project_name=str(body["project_name"]),
        api_key=str(body.get("api_key") or ""),
        source_language=_normalize_source_language(body.get("source_language")),
        to_stage="transcribed",
        translate_backend=str(body.get("translate_backend") or "block_v2"),
        tts_provider="edge_tts",
        tts_voice="",
        tts_rate="",
        mix_mode="replace_original_speech",
        enable_translation_qa=bool(body.get("enable_translation_qa")),
        enable_source_cleanup=bool(body.get("enable_source_cleanup")),
        project_root=str(body.get("project_root") or ""),
    )
    if rc != 0:
        return _err_with_log(job_workspace, "run_job_failed", f"run_job returned {rc}")
    return _ok(
        {
            **_status_payload(job_workspace),
            "segment_count": len(manifest.segments),
        }
    )


def _wants_async(body: dict[str, Any]) -> bool:
    """Opt-in background execution. Sync (default) keeps the legacy contract so
    existing tests/CLI callers still get the final result inline."""
    return bool(body.get("async") or body.get("background"))


def _dispatch_job(
    body: dict[str, Any],
    jw: Path,
    work_fn: Callable[[dict[str, Any], Path], tuple[int, dict[str, Any]]],
) -> tuple[int, dict[str, Any]]:
    """Run work_fn inline (sync) or hand it to JOB_MANAGER (async).

    In async mode the heavy run happens off the request thread; the response is
    a job id the UI polls via /api/job-progress. A workspace already running a
    job is rejected with 409 rather than starting a second concurrent run.
    """
    if not _wants_async(body):
        return work_fn(body, jw)
    snapshot = dict(body)

    def work(cancel: Any) -> tuple[int, dict[str, Any]]:
        # Tell _run_job_common (running in this same pool thread) to execute
        # run_job as a cancellable/timeoutable child process.
        token = _RUN_CONTEXT.set(
            {"job_id": str(jw), "cancel_event": cancel, "timeout_s": JOB_TIMEOUT_S}
        )
        try:
            return work_fn(snapshot, jw)
        finally:
            _RUN_CONTEXT.reset(token)

    try:
        JOB_MANAGER.submit(str(jw), work)
    except JobBusyError:
        return _err(
            "job_busy",
            "A job is already running for this workspace.",
            HTTPStatus.CONFLICT,
        )
    return _ok({"job_id": str(jw), "state": "running", "async": True})


def handle_run_until_edit(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "job_workspace", "project_name")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    return _dispatch_job(body, jw, _run_until_edit_work)


def _run_until_edit_work(body: dict[str, Any], jw: Path) -> tuple[int, dict[str, Any]]:
    body = dict(body)
    use_auto_translate = bool(body.get("use_auto_translate", True))
    source_language = _normalize_source_language(body.get("source_language"))
    api_key = _resolve_openai_api_key(body)
    body["source_language"] = source_language
    body["api_key"] = api_key
    extractor_cfg = _normalize_extractor_settings(body)
    body.update(extractor_cfg)

    use_long, why_not = _should_use_long_video_flow(jw)
    if why_not:
        return _err_with_log(jw, "duration_probe_failed", why_not)

    if use_auto_translate and not api_key and not _managed_mode_on():
        return _err(
            "api_key_required",
            "OpenAI API key is required before automatic translation can run. Open App Settings to save the key first.",
        )

    if not use_auto_translate:
        if use_long:
            return _run_long_video_until_transcribed(body, jw)
        invalidate_from_transcribe_downward(jw, reason="desktop_manual_review_mode")
        rc = _run_job_common(
            jw,
            project_name=str(body["project_name"]),
            api_key=api_key,
            source_language=source_language,
            to_stage="transcribed",
            translate_backend=str(body.get("translate_backend") or "block_v2"),
            tts_provider="edge_tts",
            tts_voice="",
            tts_rate="",
            mix_mode="replace_original_speech",
            enable_translation_qa=bool(body.get("enable_translation_qa")),
            enable_source_cleanup=bool(body.get("enable_source_cleanup")),
            project_root=str(body.get("project_root") or ""),
            subtitle_extractor=extractor_cfg["subtitle_extractor"],
            ocr_provider=extractor_cfg["ocr_provider"],
            ocr_language=extractor_cfg["ocr_language"],
            ocr_roi=extractor_cfg["ocr_roi"],
            ocr_device=extractor_cfg["ocr_device"],
        )
        if rc != 0:
            return _err_with_log(jw, "run_job_failed", f"run_job returned {rc}")
        return _ok(_status_payload(jw))

    if use_long:
        try:
            run_long_video_stage.do_plan_split(
                jw,
                video=None,
                target_minutes=float(body.get("target_minutes") or 4.0),
                max_minutes=float(body.get("max_minutes") or 5.0),
                force=bool(body.get("force_replan")),
            )
            result = run_long_video_stage.do_until_edit(
                jw,
                cfg=_long_cfg_from_body(body, project_name=str(body["project_name"])),
                max_workers=int(body.get("max_workers") or 0) or None,
            )
        except (SegmentError, run_long_video_stage.LongVideoError) as e:
            return _err_with_log(jw, "long_video_failed", str(e))
        if not result.get("ok", False):
            return _err_with_log(
                jw,
                "long_video_failed",
                str(result.get("error") or "one or more segments failed"),
            )
        return _ok(
            {
                **_status_payload(jw),
                "segment_count": result.get("segment_count"),
                "workers": result.get("workers"),
            }
        )

    rc = _run_job_common(
        jw,
        project_name=str(body["project_name"]),
        api_key=api_key,
        source_language=source_language,
        to_stage="translated",
        translate_backend=str(body.get("translate_backend") or "block_v2"),
        tts_provider="edge_tts",
        tts_voice="",
        tts_rate="",
        mix_mode="replace_original_speech",
        enable_translation_qa=bool(body.get("enable_translation_qa")),
        enable_source_cleanup=bool(body.get("enable_source_cleanup")),
        subtitle_extractor=extractor_cfg["subtitle_extractor"],
        ocr_language=extractor_cfg["ocr_language"],
        ocr_roi=extractor_cfg["ocr_roi"],
        ocr_device=extractor_cfg["ocr_device"],
    )
    if rc != 0:
        return _err_with_log(jw, "run_job_failed", f"run_job returned {rc}")

    translated_voice = jw / "artifacts" / "translate" / "translated_voice.srt"
    if not translated_voice.is_file():
        # Legacy backend may only write translated_auto.srt. For desktop UI we still
        # need translated_voice.srt to seed the voice-edit flow; fall back by copying.
        translated_auto = jw / "artifacts" / "translate" / "translated_auto.srt"
        if translated_auto.is_file():
            try:
                translated_voice.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(translated_auto, translated_voice)
            except OSError as e:
                return _err("translated_voice_copy_failed", f"Could not create translated_voice.srt from translated_auto.srt: {e}")
        else:
            return _err(
                "translated_voice_missing",
                "translated_voice.srt not produced (use translate_backend=block_v2).",
            )
    try:
        seed_edited_voice(jw, overwrite=False)
    except VoiceEditError as e:
        return _err("seed_failed", str(e))
    return _ok(_status_payload(jw))


def handle_run_after_edit(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "job_workspace", "project_name")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    return _dispatch_job(body, jw, _run_after_edit_work)


def _run_after_edit_work(body: dict[str, Any], jw: Path) -> tuple[int, dict[str, Any]]:
    edited = jw / "artifacts" / "edit" / "edited_voice.srt"
    if not edited.is_file():
        return _err("edited_voice_missing", f"Missing {edited}. Save the edit first.")

    use_long, why_not = _should_use_long_video_flow(jw)
    if why_not:
        return _err_with_log(jw, "duration_probe_failed", why_not)

    to_stage = str(body.get("to_stage") or "rendered")
    if to_stage not in run_job.STAGE_ORDER:
        return _err("invalid_to_stage", f"to_stage must be one of {run_job.STAGE_ORDER}")
    try:
        tts_rate = _tts_rate_arg_from_payload(body)
    except TTSSettingsError as e:
        return _err("invalid_tts_settings", str(e))
    try:
        mix_duck_gain_db = (
            float(validate_tts_settings({"mix_duck_gain_db": body.get("mix_duck_gain_db")})["mix_duck_gain_db"])
            if body.get("mix_duck_gain_db") is not None
            else None
        )
    except TTSSettingsError as e:
        return _err("invalid_tts_settings", str(e))

    if use_long:
        try:
            mark_voice_edited(jw)
            long_body = dict(body)
            if tts_rate:
                long_body["tts_rate"] = tts_rate
            result = run_long_video_stage.do_after_edit(
                jw,
                cfg=_long_cfg_from_body(long_body, project_name=str(body["project_name"])),
                to_stage=to_stage,
                max_workers=int(body.get("max_workers") or 0) or None,
        render_filename=str(body.get("render_filename") or "final.mp4"),
        merge_render=not bool(body.get("no_merge_render")),
    )
        except (VoiceEditError, SegmentError, run_long_video_stage.LongVideoError) as e:
            return _err_with_log(jw, "long_video_failed", str(e))
        if not result.get("ok", False):
            return _err_with_log(
                jw,
                "long_video_failed",
                str(result.get("error") or "one or more segments failed"),
            )

        final_subtitle_path: str | None = None
        try:
            subtitle_finalized_rank = run_job.STAGE_ORDER.index("subtitle_finalized")
            to_rank = run_job.STAGE_ORDER.index(to_stage)
            if to_rank >= subtitle_finalized_rank:
                merged_srt = merge_segment_final_subtitles(jw)
                final_subtitle_path = str(merged_srt.resolve())
        except Exception:  # noqa: BLE001
            final_subtitle_path = None

        render_dir = jw / "artifacts" / "render"
        return _ok(
            {
                "final_subtitle_path": final_subtitle_path,
                "render_dir": _path_or_none(render_dir if render_dir.is_dir() else None),
                "merged_render_path": result.get("merged_render_path"),
                "to_stage": to_stage,
                "segment_count": result.get("segment_count"),
                "workers": result.get("workers"),
            }
        )

    try:
        mark_voice_edited(jw)
    except VoiceEditError as e:
        return _err("mark_failed", str(e))

    rc = _run_job_common(
        jw,
        project_name=str(body["project_name"]),
        api_key=str(body.get("api_key") or ""),
        source_language="",
        to_stage=to_stage,
        translate_backend=str(body.get("translate_backend") or "block_v2"),
        tts_provider=str(body.get("tts_provider") or "edge_tts"),
        tts_voice=str(body.get("tts_voice") or ""),
        tts_rate=tts_rate,
        mix_mode=str(body.get("mix_mode") or "replace_original_speech"),
        enable_translation_qa=False,
        enable_source_cleanup=False,
        project_root=str(body.get("project_root") or ""),
        render_subtitle_mode=str(body.get("subtitle_mode") or "burn"),
        mix_duck_gain_db=mix_duck_gain_db,
    )
    if rc != 0:
        return _err_with_log(jw, "run_job_failed", f"run_job returned {rc}")
    final_srt = jw / "artifacts" / "translate" / "final_subtitle.srt"
    render_dir = jw / "artifacts" / "render"
    return _ok(
        {
            "final_subtitle_path": _path_or_none(final_srt if final_srt.is_file() else None),
            "render_dir": _path_or_none(render_dir if render_dir.is_dir() else None),
            "to_stage": to_stage,
        }
    )


def handle_tts_preview(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "job_workspace")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")

    text = str(body.get("text") or _DEFAULT_TTS_PREVIEW_TEXT).strip() or _DEFAULT_TTS_PREVIEW_TEXT
    provider_name = str(body.get("tts_provider") or "edge_tts").strip() or "edge_tts"
    voice = str(body.get("tts_voice") or DEFAULT_TTS_VOICE).strip() or DEFAULT_TTS_VOICE
    try:
        rate_arg = _tts_rate_arg_from_payload(body)
    except TTSSettingsError as e:
        return _err("invalid_tts_settings", str(e))

    rate = rate_arg or "+0%"
    out_wav, meta_path, cache_key = _preview_cache_paths(
        jw,
        provider=provider_name,
        voice=voice,
        rate=rate,
        text=text,
    )
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    if out_wav.is_file() and out_wav.stat().st_size > 0:
        meta = _read_preview_cache_meta(meta_path)
        with contextlib.suppress(OSError):
            now = time.time()
            os.utime(out_wav, (now, now))
            if meta_path.is_file():
                os.utime(meta_path, (now, now))
        _cleanup_preview_cache(out_wav.parent)
        return _ok(
            {
                "job_workspace": str(jw),
                "rel_path": _workspace_rel_path(out_wav, jw),
                "duration_ms": int(meta.get("duration_ms") or 0),
                "provider": provider_name,
                "voice": voice,
                "rate": rate,
                "cached": True,
                "cache_key": cache_key,
                "cache_bust": int(out_wav.stat().st_mtime * 1000),
            }
        )

    try:
        provider = get_tts_provider(provider_name)
        duration_ms = asyncio.run(
            provider.synthesize_cue_to_wav(
                text,
                out_wav,
                voice=voice,
                rate=rate,
                diag_prefix="[tts-preview]",
            )
        )
    except Exception as e:  # noqa: BLE001
        return _err("tts_preview_failed", str(e))

    with contextlib.suppress(OSError, TypeError, ValueError):
        meta_path.write_text(
            json.dumps(
                {
                    "duration_ms": int(duration_ms),
                    "provider": provider_name,
                    "voice": voice,
                    "rate": rate,
                    "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "created_at": time.time(),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    _cleanup_preview_cache(out_wav.parent)

    return _ok(
        {
            "job_workspace": str(jw),
            "rel_path": _workspace_rel_path(out_wav, jw),
            "duration_ms": duration_ms,
            "provider": provider_name,
            "voice": voice,
            "rate": rate,
            "cached": False,
            "cache_key": cache_key,
            "cache_bust": int(out_wav.stat().st_mtime * 1000) if out_wav.exists() else int(time.time() * 1000),
        }
    )


def _managed_mode_on() -> bool:
    """True when the cloud client is available AND the user is signed in — i.e.
    translation should go through the managed backend (no local OpenAI key needed)."""
    return bool(_cloud is not None and _cloud.managed_enabled())


def _cloud_unavailable() -> tuple[int, dict[str, Any]]:
    return _err("cloud_unavailable", "Chế độ quản lý chưa sẵn sàng (thiếu thư viện httpx).")


def handle_account_status(_body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Login + entitlement snapshot the frontend polls to render account/gating UI."""
    if _cloud is None:
        return _ok({"available": False, "authed": False, "managed": False})
    acc = _cloud.account()
    authed = acc.is_authed()
    out: dict[str, Any] = {
        "available": True,
        "authed": authed,
        "managed": _cloud.managed_enabled(),
        "base_url": _cloud.base_url(),
    }
    if authed:
        try:
            out["entitlement"] = acc.entitlement()
        except _cloud.CloudError as e:  # type: ignore[union-attr]
            out["entitlement_error"] = str(e)
            if getattr(e, "status", 0) == 401:
                out["authed"] = False
    return _ok(out)


def _account_call(fn_name: str, body: dict[str, Any], *required: str):
    """Shared wrapper for the email/password account endpoints: validate required
    fields, dispatch to the matching CloudAccount method, normalize errors so the
    UI can branch on the backend's error code (e.g. 'email_unverified')."""
    if _cloud is None:
        return _cloud_unavailable()
    missing = [k for k in required if not str(body.get(k) or "").strip()]
    if missing:
        return _err("missing_field", f"Thiếu: {', '.join(missing)}")
    args = {k: str(body.get(k) or "").strip() for k in required}
    if "email" in args:
        args["email"] = args["email"].lower()
    # optional display_name for register
    if fn_name == "register" and body.get("display_name"):
        args["display_name"] = str(body.get("display_name")).strip()
    try:
        method = getattr(_cloud.account(), fn_name)
        return _ok(method(**args))
    except _cloud.CloudError as e:  # type: ignore[union-attr]
        code = getattr(e, "code", "") or "account_error"
        status = HTTPStatus.BAD_REQUEST
        if getattr(e, "status", 0) in (401, 403, 409):
            status = e.status
        return _err(code, str(e), status)


def handle_account_register(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Create an account → emails a 6-digit code (no session until verified)."""
    return _account_call("register", body, "email", "password")


def handle_account_verify(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Confirm the emailed code → signs the user in (cookies persisted)."""
    return _account_call("verify_email", body, "email", "code")


def handle_account_login(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Email + password sign-in. Returns error code 'email_unverified' when the
    code step is still pending so the UI can switch to the verify screen."""
    return _account_call("login", body, "email", "password")


def handle_account_resend(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return _account_call("resend_code", body, "email")


def handle_account_forgot(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return _account_call("forgot_password", body, "email")


def handle_account_reset(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return _account_call("reset_password", body, "email", "code", "new_password")


def handle_account_logout(_body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    if _cloud is None:
        return _cloud_unavailable()
    _cloud.account().logout()
    return _ok({"authed": False})


def handle_account_checkout(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Create a SePay checkout for a video plan → {qr_code_url, payment_code, ...}."""
    if _cloud is None:
        return _cloud_unavailable()
    plan_code = str(body.get("plan_code") or "").strip()
    if not plan_code:
        return _err("missing_field", "plan_code là bắt buộc.")
    try:
        return _ok(_cloud.account().checkout(plan_code))
    except _cloud.CloudError as e:  # type: ignore[union-attr]
        return _err(getattr(e, "code", "") or "checkout_failed", str(e))


def handle_account_billing(_body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Billing/subscription snapshot — the purchase UI polls this until active."""
    if _cloud is None:
        return _cloud_unavailable()
    try:
        return _ok(_cloud.account().billing_me())
    except _cloud.CloudError as e:  # type: ignore[union-attr]
        return _err(getattr(e, "code", "") or "billing_failed", str(e))


def handle_ping(_body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return _ok({"status": "ok", "service": "video-localization-tool"})


def handle_preflight(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    job_workspace = str(body.get("job_workspace") or "").strip()
    report = build_preflight_report(
        job_workspace=(job_workspace or None),
        translate_backend=str(body.get("translate_backend") or "block_v2"),
        tts_provider=str(body.get("tts_provider") or "edge_tts"),
        api_key=str(body.get("api_key") or ""),
        require_download=bool(body.get("require_download")),
        require_input=bool(body.get("require_input")),
        require_render=bool(body.get("require_render")),
        require_long_video=bool(body.get("require_long_video")),
        require_ocr=bool(body.get("require_ocr")),
    )
    if report["ok"]:
        return _ok(report)
    return (
        HTTPStatus.BAD_REQUEST,
        {
            "ok": False,
            "error": {"code": "preflight_failed", "message": "Preflight checks failed."},
            "data": report,
        },
    )


def handle_job_progress(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "job_workspace")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    state_path = jw / "job_state.json"
    state: dict[str, Any] = {}
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state = {}
    progress = _progress_payload(state, jw=jw)
    last_error = state.get("last_error")
    tail = _tail_log(jw, max_lines=20)
    record = JOB_MANAGER.get(str(jw))
    return _ok(
        {
            **progress,
            "last_error": last_error,
            "error": _classify_error_details(str(last_error or ""), tail) if last_error else None,
            "log_tail": tail,
            # Background-run lifecycle for the async path; null when the job ran
            # inline (sync) or this workspace has never been submitted.
            "job": record.public_dict() if record is not None else None,
        }
    )


def handle_cancel_job(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "job_workspace")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    requested = JOB_MANAGER.request_cancel(str(jw))
    # Hard-kill the running child process tree (ffmpeg/whisper included), not
    # just the cooperative flag, so an in-flight run actually stops.
    terminated = PROC_REGISTRY.terminate(str(jw))
    if not requested and not terminated:
        return _err("job_not_found", f"No tracked job for workspace: {jw}", HTTPStatus.NOT_FOUND)
    return _ok(
        {
            "job_id": str(jw),
            "cancel_requested": True,
            "process_terminated": terminated,
        }
    )


ROUTES: dict[str, Callable[[dict[str, Any]], tuple[int, dict[str, Any]]]] = {
    "/api/ping": handle_ping,
    "/api/account/status": handle_account_status,
    "/api/account/register": handle_account_register,
    "/api/account/verify": handle_account_verify,
    "/api/account/login": handle_account_login,
    "/api/account/resend-code": handle_account_resend,
    "/api/account/forgot-password": handle_account_forgot,
    "/api/account/reset-password": handle_account_reset,
    "/api/account/logout": handle_account_logout,
    "/api/account/checkout": handle_account_checkout,
    "/api/account/billing": handle_account_billing,
    "/api/preflight": handle_preflight,
    "/api/doctor": handle_preflight,
    "/api/job-progress": handle_job_progress,
    "/api/init-job": handle_init_job,
    "/api/default-download-root": handle_default_download_root,
    "/api/probe-video-url": handle_probe_video_url,
    "/api/init-job-from-url": handle_init_job_from_url,
    "/api/status": handle_status,
    "/api/load": handle_load,
    "/api/save": handle_save,
    "/api/upload-translation": handle_upload_translation,
    "/api/translate-srt": handle_translate_srt,
    "/api/read-subtitle-file": handle_read_subtitle_file,
    "/api/mark-edited": handle_mark_edited,
    "/api/get-voice-overrides": handle_get_voice_overrides,
    "/api/save-voice-overrides": handle_save_voice_overrides,
    "/api/voice-samples/list": handle_list_voice_samples,
    "/api/voice-samples/upload": handle_upload_voice_sample,
    "/api/voice-samples/remove": handle_remove_voice_sample,
    "/api/run-until-edit": handle_run_until_edit,
    "/api/run-after-edit": handle_run_after_edit,
    "/api/cancel-job": handle_cancel_job,
    "/api/get-video-style": handle_get_video_style,
    "/api/save-video-style": handle_save_video_style,
    "/api/get-project-style": handle_get_project_style,
    "/api/save-project-style": handle_save_project_style,
    "/api/list-system-fonts": handle_list_system_fonts,
    "/api/list-voices": handle_list_voices,
    "/api/voices/toggle": handle_toggle_voice,
    "/api/voices/refresh": handle_refresh_voices,
    "/api/tts-preview": handle_tts_preview,
    "/api/list-jobs": handle_list_jobs,
    "/api/list-segments": handle_list_segments,
    "/api/list-artifacts": handle_list_artifacts,
    "/api/get-video-tts": handle_get_video_tts,
    "/api/save-video-tts": handle_save_video_tts,
    "/api/get-project-tts": handle_get_project_tts,
    "/api/save-project-tts": handle_save_project_tts,
    "/api/bgm/status": handle_bgm_status,
    "/api/bgm/upload": handle_bgm_upload,
    "/api/bgm/save": handle_bgm_save,
    "/api/bgm/remove": handle_bgm_remove,
    "/api/render-settings/status": handle_render_settings_status,
    "/api/render-settings/save": handle_render_settings_save,
    "/api/render-background/upload": handle_render_background_upload,
    "/api/render-background/remove": handle_render_background_remove,
    "/api/render-logo/upload": handle_render_logo_upload,
    "/api/render-logo/remove": handle_render_logo_remove,
    "/api/render-intro/upload": handle_render_intro_upload,
    "/api/render-intro/remove": handle_render_intro_remove,
    "/api/render-outro/upload": handle_render_outro_upload,
    "/api/render-outro/remove": handle_render_outro_remove,
    "/api/get-import-config": handle_get_import_config,
    "/api/save-import-config": handle_save_import_config,
    "/api/import-external-srt": handle_import_external_srt,
    "/api/pick-srt-file": handle_pick_srt_file,
    "/api/reveal": handle_reveal,
    "/api/get-app-settings": handle_get_app_settings,
    "/api/save-app-settings": handle_save_app_settings,
    "/api/check-openai-key": handle_check_openai_key,
    "/api/pick-folder": handle_pick_folder,
    "/api/pick-file": handle_pick_file,
    "/api/pick-files": handle_pick_files,
    "/api/init-project": handle_init_project,
    "/api/add-video-to-project": handle_add_video_to_project,
    "/api/save-video-override": handle_save_video_override,
    "/api/get-project": handle_get_project,
    "/api/inspect-local-video": handle_inspect_local_video,
    "/api/ocr-test-frame": handle_ocr_test_frame,
    "/api/ocr-diagnostics": handle_ocr_diagnostics,
}


class _Handler(BaseHTTPRequestHandler):
    server_version = "VideoLocalization/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: N802 (stdlib override)
        sys.stderr.write(f"[desktop.server] {self.address_string()} - {fmt % args}\n")

    def _write_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _write_static(self, path: Path, content_type: str) -> None:
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _serve_media(self, query: str) -> None:
        """Serve a whitelisted artifact file from a workspace with byte-range support.

        URL shape: ``/media?workspace=<abs>&rel=<relative path inside workspace>``
        Only files inside a directory that looks like a video workspace are allowed.
        """
        params = urllib.parse.parse_qs(query, keep_blank_values=False)
        workspace_raw = (params.get("workspace") or [""])[0]
        rel_raw = (params.get("rel") or [""])[0]
        if not workspace_raw or not rel_raw:
            self.send_error(HTTPStatus.BAD_REQUEST, "missing workspace or rel")
            return
        try:
            workspace = Path(workspace_raw).expanduser().resolve(strict=True)
        except (OSError, FileNotFoundError):
            self.send_error(HTTPStatus.NOT_FOUND, "workspace not found")
            return
        if not workspace.is_dir() or not _is_video_workspace(workspace):
            self.send_error(HTTPStatus.FORBIDDEN, "workspace not recognized")
            return
        rel_path = Path(rel_raw)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            self.send_error(HTTPStatus.FORBIDDEN, "illegal relative path")
            return
        try:
            target = (workspace / rel_path).resolve(strict=True)
        except (OSError, FileNotFoundError):
            self.send_error(HTTPStatus.NOT_FOUND, "file not found")
            return
        try:
            target.relative_to(workspace)
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN, "escape attempt")
            return
        if not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "not a file")
            return

        size = target.stat().st_size
        content_type, _ = mimetypes.guess_type(target.name)
        content_type = content_type or "application/octet-stream"

        range_header = self.headers.get("Range") or ""
        start, end = 0, size - 1
        status = HTTPStatus.OK
        if range_header.startswith("bytes="):
            try:
                spec = range_header.split("=", 1)[1].split(",", 1)[0].strip()
                s_str, e_str = spec.split("-", 1)
                if s_str:
                    start = int(s_str)
                if e_str:
                    end = int(e_str)
                else:
                    end = size - 1
                if start < 0 or end < start or end >= size:
                    raise ValueError("out of range")
                status = HTTPStatus.PARTIAL_CONTENT
            except (ValueError, IndexError):
                start, end = 0, size - 1
                status = HTTPStatus.OK

        length = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        if status == HTTPStatus.PARTIAL_CONTENT:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        try:
            with target.open("rb") as fh:
                fh.seek(start)
                remaining = length
                chunk = 64 * 1024
                while remaining > 0:
                    buf = fh.read(min(chunk, remaining))
                    if not buf:
                        break
                    self.wfile.write(buf)
                    remaining -= len(buf)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _serve_job_events(self, query: str) -> None:
        """Stream live job progress + log tail as Server-Sent Events.

        URL shape: ``/api/job-events?job_workspace=<abs>``. Validated like /media
        (must look like a video workspace). Holds the connection open in this
        request thread, pushing a frame whenever the progress payload changes,
        until the job reaches a terminal lifecycle (or the client disconnects).
        """
        params = urllib.parse.parse_qs(query, keep_blank_values=False)
        workspace_raw = (params.get("job_workspace") or params.get("workspace") or [""])[0]
        if not workspace_raw:
            self.send_error(HTTPStatus.BAD_REQUEST, "missing job_workspace")
            return
        try:
            jw = Path(workspace_raw).expanduser().resolve(strict=True)
        except (OSError, FileNotFoundError):
            self.send_error(HTTPStatus.NOT_FOUND, "workspace not found")
            return
        if not jw.is_dir() or not _is_video_workspace(jw):
            self.send_error(HTTPStatus.FORBIDDEN, "workspace not recognized")
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.send_header("Connection", "keep-alive")
        # Disable proxy buffering so frames flush immediately.
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        try:
            for frame in iter_job_event_frames(jw, max_runtime_s=JOB_TIMEOUT_S):
                self.wfile.write(frame)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlsplit(self.path)
        route = parsed.path
        if route == "/media":
            self._serve_media(parsed.query)
            return
        if route == "/api/job-events":
            self._serve_job_events(parsed.query)
            return
        if route in ("/", "/index.html"):
            self._write_static(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return
        if route.startswith("/"):
            rel = route.lstrip("/")
            rel_path = Path(rel)
            if rel_path.is_absolute() or ".." in rel_path.parts:
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            target = (STATIC_DIR / rel_path).resolve()
            try:
                target.relative_to(STATIC_DIR.resolve())
            except ValueError:
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            if target.is_file():
                ctype, _ = mimetypes.guess_type(target.name)
                ctype = ctype or "application/octet-stream"
                if target.suffix == ".js":
                    ctype = "application/javascript; charset=utf-8"
                elif target.suffix == ".css":
                    ctype = "text/css; charset=utf-8"
                elif target.suffix == ".json":
                    ctype = "application/json; charset=utf-8"
                elif target.suffix == ".html":
                    ctype = "text/html; charset=utf-8"
                self._write_static(target, ctype)
                return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        handler = ROUTES.get(self.path)
        if handler is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length > MAX_REQUEST_BODY_BYTES:
            self._write_json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                {
                    "ok": False,
                    "error": {
                        "code": "request_too_large",
                        "message": f"Request body exceeds {MAX_REQUEST_BODY_BYTES} bytes.",
                    },
                },
            )
            return
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
            if not isinstance(body, dict):
                raise ValueError("request body must be a JSON object")
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as e:
            self._write_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": {"code": "invalid_json", "message": str(e)}},
            )
            return
        try:
            status, payload = handler(body)
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            message = str(e)[:MAX_ERROR_MESSAGE_CHARS]
            details = _classify_error_details(message, [], fallback_code="unhandled")
            self._write_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "error": {"code": "unhandled", "message": message, **details}},
            )
            return
        self._write_json(status, payload)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Desktop shell for video localization tool.")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not auto-open the browser after the server starts.",
    )
    return p.parse_args(argv)


def _open_browser_when_ready(
    url: str,
    *,
    ping_timeout: float = 15.0,
    poll_interval: float = 0.25,
) -> None:
    """Open the default browser only after the local server answers /api/ping."""

    def _run() -> None:
        deadline = time.time() + ping_timeout
        while time.time() < deadline:
            if _ping_server(url, timeout=min(1.0, poll_interval + 0.5)):
                break
            time.sleep(poll_interval)
        else:
            return
        try:
            webbrowser.open(url, new=1, autoraise=True)
        except Exception:  # noqa: BLE001
            pass

    threading.Thread(target=_run, name="browser-launcher", daemon=True).start()


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    httpd = ThreadingHTTPServer((ns.host, ns.port), _Handler)
    url = f"http://{ns.host}:{ns.port}"
    print(f"[desktop.server] serving on {url}", file=sys.stderr)
    if not ns.no_browser:
        _open_browser_when_ready(url)
        print("[desktop.server] opening browser (pass --no-browser to skip)", file=sys.stderr)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("[desktop.server] stopping", file=sys.stderr)
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
