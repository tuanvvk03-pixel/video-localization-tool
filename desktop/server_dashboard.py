"""Dashboard + diagnostics listing handlers.

Owns the workspace/project scan (/api/list-jobs), the long-video segment rail
(/api/list-segments) and the canonical-artifact enumeration (/api/list-artifacts),
plus the per-job summary row helper. Extracted from the server monolith with
behaviour identical to the previous inline code. Acyclic deps:

    server.py ─> server_dashboard ─> server_progress / server_shared
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from desktop.server_progress import _progress_payload
from desktop.server_shared import _err, _ok, _require
from engine.voice_edit_api import get_voice_edit_status


def _iter_child_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    out: list[Path] = []
    try:
        for child in root.iterdir():
            if child.is_dir():
                out.append(child)
    except OSError:
        return []
    return out


def _dashboard_transcription_source(state: dict[str, Any], vstate: dict[str, Any]) -> str:
    """Short key for dashboard i18n: asr_local | imported_srt | legacy_ocr."""
    te = str(vstate.get("transcription_engine") or state.get("transcription_engine") or "").strip().lower()
    se = str(vstate.get("subtitle_extractor") or state.get("subtitle_extractor") or "").strip().lower()
    raw_ic = vstate.get("import_config")
    if isinstance(raw_ic, dict) and not se:
        se = str(raw_ic.get("subtitle_extractor") or "").strip().lower()
    if te == "external_srt" or se == "external_srt":
        return "imported_srt"
    if se in {"ocr_only", "hybrid"}:
        return "legacy_ocr"
    if te.startswith("ocr:"):
        return "legacy_ocr"
    return "asr_local"


def _job_summary(jw: Path, *, parent_project: str | None = None) -> dict[str, Any]:
    """Derive a lightweight row for the Dashboard table from a video workspace."""
    state_path = jw / "job_state.json"
    state: dict[str, Any] = {}
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state = {}

    vstate_path = jw / "video_state.json"
    vstate: dict[str, Any] = {}
    if vstate_path.is_file():
        try:
            vstate = json.loads(vstate_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            vstate = {}

    progress = _progress_payload(state, jw=jw)
    is_long = (jw / "segments" / "manifest.json").is_file()
    try:
        voice_status = get_voice_edit_status(jw)
        voice_edit_status = voice_status.voice_edit_status
        voice_edited = voice_status.voice_edited
    except Exception:  # noqa: BLE001
        voice_edit_status = str(state.get("voice_edit_status") or "")
        voice_edited = bool(state.get("voice_edited"))

    updated_unix: float = 0.0
    for candidate in (state_path, vstate_path, jw / "run.log"):
        try:
            if candidate.is_file():
                updated_unix = max(updated_unix, candidate.stat().st_mtime)
        except OSError:
            continue

    return {
        "job_id": jw.name,
        "job_workspace": str(jw.resolve()),
        "parent_project": parent_project,
        "type": "long" if is_long else "single",
        "status": progress["status"],
        "status_label": progress["status_label"],
        "current_stage": progress["current_stage"],
        "current_stage_label": progress["current_stage_label"],
        "overall_percent": progress["overall_percent"],
        "lifecycle": progress["lifecycle"],
        "voice_edit_status": voice_edit_status,
        "voice_edited": voice_edited,
        "last_error": state.get("last_error") or vstate.get("last_error"),
        "updated_unix": updated_unix,
        "transcription_engine": str(vstate.get("transcription_engine") or state.get("transcription_engine") or ""),
        "subtitle_extractor": str(vstate.get("subtitle_extractor") or state.get("subtitle_extractor") or ""),
        "transcription_source": _dashboard_transcription_source(state, vstate),
    }


def _is_video_workspace(path: Path) -> bool:
    return (
        (path / "job_state.json").is_file()
        or (path / "video_state.json").is_file()
        or (path / "input" / "source.mp4").is_file()
    )


def handle_list_jobs(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Scan a workspace/projects root and return a flat list of jobs for the dashboard.

    Layout understood:
    - <root>/<job_id>/                             single or long workspace
    - <root>/<project_id>/project_state.json       multi-video project
    - <root>/<project_id>/videos/<video_id>/       child video workspace
    """
    missing = _require(body, "workspace_root")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    root = Path(str(body["workspace_root"])).expanduser().resolve()
    if not root.is_dir():
        return _err("workspace_missing", f"Workspace root not found: {root}")

    rows: list[dict[str, Any]] = []
    projects: list[dict[str, Any]] = []

    for child in _iter_child_dirs(root):
        project_state = child / "project_state.json"
        if project_state.is_file():
            try:
                proj_raw = json.loads(project_state.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                proj_raw = {}
            project_id = str(proj_raw.get("project_id") or child.name)
            videos_root = child / "videos"
            video_rows: list[dict[str, Any]] = []
            for video_dir in _iter_child_dirs(videos_root):
                if _is_video_workspace(video_dir):
                    video_rows.append(_job_summary(video_dir, parent_project=project_id))
            rows.extend(video_rows)
            projects.append(
                {
                    "project_id": project_id,
                    "project_root": str(child.resolve()),
                    "video_count": len(video_rows),
                }
            )
            continue
        if _is_video_workspace(child):
            rows.append(_job_summary(child))

    rows.sort(key=lambda r: r["updated_unix"], reverse=True)

    totals: dict[str, int] = {"total": len(rows), "running": 0, "queued": 0, "blocked": 0, "completed": 0, "failed": 0}
    for row in rows:
        lifecycle = row["lifecycle"]
        if lifecycle in totals:
            totals[lifecycle] += 1
        elif lifecycle == "idle":
            totals["queued"] += 1

    return _ok(
        {
            "workspace_root": str(root),
            "totals": totals,
            "projects": projects,
            "jobs": rows,
        }
    )


def handle_list_segments(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Return segment rail data for a long-video parent workspace."""
    missing = _require(body, "job_workspace")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    manifest_path = jw / "segments" / "manifest.json"
    if not manifest_path.is_file():
        return _ok(
            {
                "is_long_video": False,
                "source_duration_s": 0.0,
                "segments": [],
            }
        )
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return _err("invalid_manifest", f"Could not read segments/manifest.json: {e}")

    out_segments: list[dict[str, Any]] = []
    for seg in raw.get("segments") or []:
        seg_ws = Path(str(seg.get("workspace") or ""))
        seg_row = {
            "index": int(seg.get("index") or 0),
            "start_s": float(seg.get("start_s") or 0.0),
            "end_s": float(seg.get("end_s") or 0.0),
            "workspace": str(seg_ws),
            "video": str(seg.get("video") or ""),
        }
        if seg_ws.is_dir():
            seg_row.update(_job_summary(seg_ws))
        out_segments.append(seg_row)

    return _ok(
        {
            "is_long_video": True,
            "source_duration_s": float(raw.get("source_duration_s") or 0.0),
            "source_video": str(raw.get("source_video") or ""),
            "segments": out_segments,
        }
    )


_ARTIFACT_LABELS: dict[str, str] = {
    "artifacts/download/download_manifest.json": "Download manifest",
    "artifacts/transcribe/source.srt": "ASR source subtitle",
    "artifacts/transcribe/source_cleaned_zh.srt": "Cleaned Chinese source",
    "artifacts/translate/translated_auto.srt": "Automatic translation",
    "artifacts/translate/translated_voice.srt": "TTS-oriented translation",
    "artifacts/translate/translated_manual.srt": "Manual translation",
    "artifacts/translate/final_subtitle.srt": "Final subtitle",
    "artifacts/translate/final_subtitle_manifest.json": "Final subtitle manifest",
    "artifacts/edit/edited_voice.srt": "Edited voice subtitle",
    "artifacts/edit/edit_manifest.json": "Edit manifest",
    "artifacts/tts/tts_manifest.json": "TTS manifest",
    "artifacts/aligned/alignment_manifest.json": "Alignment manifest",
    "artifacts/mixed/mix_manifest.json": "Mix manifest",
    "artifacts/render/final.mp4": "Final rendered video",
    "artifacts/render/render_manifest.json": "Render manifest",
    "job_state.json": "Job state",
    "video_state.json": "Video state",
    "style_override.json": "Per-video subtitle style override",
    "tts_override.json": "Per-video TTS override",
}


def handle_list_artifacts(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Enumerate canonical artifacts that exist on disk for a given workspace."""
    missing = _require(body, "job_workspace")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")

    canonical: list[dict[str, Any]] = []
    for rel, label in _ARTIFACT_LABELS.items():
        p = jw / rel
        entry: dict[str, Any] = {
            "rel_path": rel,
            "label": label,
            "exists": p.is_file(),
            "path": str(p.resolve()),
            "size_bytes": 0,
            "modified_unix": 0.0,
        }
        if p.is_file():
            try:
                stat = p.stat()
                entry["size_bytes"] = int(stat.st_size)
                entry["modified_unix"] = float(stat.st_mtime)
            except OSError:
                pass
        canonical.append(entry)

    extras: list[dict[str, Any]] = []
    tts_cues_dir = jw / "artifacts" / "tts" / "cues"
    if tts_cues_dir.is_dir():
        try:
            wavs = sorted(p for p in tts_cues_dir.iterdir() if p.suffix.lower() == ".wav")
        except OSError:
            wavs = []
        extras.append(
            {
                "rel_path": "artifacts/tts/cues/",
                "label": "TTS cue WAVs",
                "path": str(tts_cues_dir.resolve()),
                "exists": True,
                "count": len(wavs),
            }
        )

    return _ok(
        {
            "job_workspace": str(jw),
            "canonical": canonical,
            "extras": extras,
        }
    )
