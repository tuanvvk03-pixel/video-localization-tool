"""Per-video import-config persistence + external-SRT import handlers.

Owns the import_config read/clean/save helpers (stored on video_state.json) and
the /api/get-import-config, /api/save-import-config and /api/import-external-srt
handlers. Extracted from the server monolith with behaviour identical to the
previous inline code. Acyclic deps:

    server.py + server_progress ─> server_import_config ─> server_extractor / server_shared

``_load_json_file`` lives here as the shared JSON reader (also used by the
status + progress code in server.py, which import it back).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from desktop.server_extractor import _VALID_EXTRACTORS, _normalize_ocr_provider
from desktop.server_shared import _err, _ok, _require
from engine.external_srt import import_external_srt
from engine.json_store import write_json_atomic
from engine.project_manager import ProjectError, load_project


def _load_json_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _clean_import_config(raw: Any) -> dict[str, Any]:
    data = raw if isinstance(raw, dict) else {}
    extractor = str(data.get("subtitle_extractor") or "audio_only").strip().lower()
    if extractor not in _VALID_EXTRACTORS:
        extractor = "audio_only"
    if extractor in {"ocr_only", "hybrid"}:
        sys.stderr.write(
            f"[desktop.server] import_config subtitle_extractor={extractor!r} is deprecated; "
            "coercing to audio_only.\n"
        )
        extractor = "audio_only"
    external_srt_path = str(data.get("external_srt_path") or "").strip()
    if extractor != "external_srt":
        external_srt_path = ""
    ocr_provider = _normalize_ocr_provider(data.get("ocr_provider")) or "paddleocr"
    ocr_language = str(data.get("ocr_language") or "").strip().lower()
    ocr_device = str(data.get("ocr_device") or "").strip().lower()
    if ocr_device not in {"", "auto", "cpu", "cuda"}:
        ocr_device = ""
    raw_roi = data.get("ocr_roi")
    ocr_roi: dict[str, float] | None = None
    if isinstance(raw_roi, dict):
        try:
            candidate = {k: float(raw_roi.get(k)) for k in ("x", "y", "w", "h")}
            if all(0.0 <= v <= 1.0 for v in candidate.values()) and candidate["w"] > 0 and candidate["h"] > 0:
                ocr_roi = candidate
        except (TypeError, ValueError):
            ocr_roi = None
    if extractor == "external_srt":
        return {
            "use_auto_translate": bool(data.get("use_auto_translate", True)),
            "translate_backend": str(data.get("translate_backend") or "block_v2"),
            "tts_provider": str(data.get("tts_provider") or "edge_tts"),
            "subtitle_extractor": "external_srt",
            "external_srt_path": external_srt_path,
            "ocr_provider": "",
            "ocr_language": "",
            "ocr_device": "",
            "ocr_roi": None,
        }
    return {
        "use_auto_translate": bool(data.get("use_auto_translate", True)),
        "translate_backend": str(data.get("translate_backend") or "block_v2"),
        "tts_provider": str(data.get("tts_provider") or "edge_tts"),
        "subtitle_extractor": extractor,
        "external_srt_path": "",
        "ocr_provider": ocr_provider,
        "ocr_language": ocr_language,
        "ocr_device": ocr_device,
        "ocr_roi": ocr_roi,
    }


def _load_import_config(job_workspace: Path) -> dict[str, Any]:
    vstate = _load_json_file(job_workspace / "video_state.json")
    raw = vstate.get("import_config")
    if isinstance(raw, dict):
        return _clean_import_config(raw)
    legacy = {
        "use_auto_translate": vstate.get("use_auto_translate", True),
        "translate_backend": vstate.get("translate_backend") or "block_v2",
        "tts_provider": vstate.get("tts_provider") or "edge_tts",
    }
    return _clean_import_config(legacy)


def _save_import_config(job_workspace: Path, raw: Any) -> dict[str, Any]:
    cfg = _clean_import_config(raw)
    path = job_workspace / "video_state.json"
    base = _load_json_file(path)
    base["import_config"] = cfg
    base["use_auto_translate"] = cfg["use_auto_translate"]
    base["translate_backend"] = cfg["translate_backend"]
    base["tts_provider"] = cfg["tts_provider"]
    write_json_atomic(path, base)
    return cfg


def handle_get_import_config(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "job_workspace")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    return _ok({"config": _load_import_config(jw)})


def handle_save_import_config(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "job_workspace")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    return _ok({"config": _save_import_config(jw, body.get("config"))})


def _resolve_job_workspace_for_body(body: dict[str, Any]) -> Path | None:
    raw_jw = str(body.get("job_workspace") or "").strip()
    if raw_jw:
        try:
            return Path(raw_jw).expanduser().resolve()
        except OSError:
            return None
    pr = str(body.get("project_root") or "").strip()
    vid = str(body.get("video_id") or "").strip()
    if not pr or not vid:
        return None
    try:
        project_root = Path(pr).expanduser().resolve()
    except OSError:
        return None
    try:
        state = load_project(project_root)
    except ProjectError:
        return None
    for v in state.videos:
        if v.video_id == vid:
            try:
                return Path(v.workspace).expanduser().resolve()
            except OSError:
                return None
    return None


def handle_import_external_srt(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "srt_path")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = _resolve_job_workspace_for_body(body)
    if jw is None:
        return _err("missing_field", "Provide job_workspace or project_root + video_id")
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    try:
        sp = Path(str(body["srt_path"]).strip()).expanduser().resolve()
    except OSError:
        return _err("srt_not_found", f"SRT path is not readable: {body.get('srt_path')!r}")
    if not sp.is_file():
        return _err("srt_not_found", f"SRT file does not exist: {sp}")
    if sp.suffix.lower() != ".srt":
        return _err("invalid_srt_extension", "Only .srt files can be imported in this build.")
    try:
        manifest = import_external_srt(job_workspace=jw, source_path=sp)
    except FileNotFoundError as e:
        return _err("import_failed", str(e))
    except ValueError as e:
        return _err("invalid_srt", str(e))
    except OSError as e:
        return _err("import_failed", str(e))
    out_srt = (jw / "artifacts" / "transcribe" / "source.srt").resolve()
    return _ok(
        {
            "manifest": manifest,
            "cue_count": int(manifest.get("cue_count") or 0),
            "source_srt": str(out_srt),
        }
    )
