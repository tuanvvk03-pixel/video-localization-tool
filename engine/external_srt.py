"""Import user-provided SRT into the canonical workspace transcribe artifact."""
from __future__ import annotations

from engine.json_store import write_json_atomic
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.input_provenance import fingerprint_file
from engine.srt_cues import cues_to_srt, parse_srt_cues


def normalize_srt_text(raw: str) -> str:
    """Strip BOM, normalize newlines, validate via parse_srt_cues, return canonical SRT text."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    cues = parse_srt_cues(text)
    if not cues:
        raise ValueError("SRT has no valid cues (expected at least one timestamp line with text).")
    return cues_to_srt(cues)


def _decode_subtitle_bytes(data: bytes) -> str:
    if not data:
        raise ValueError("SRT file is empty")
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return data.decode("utf-16")
        except UnicodeDecodeError as e:
            raise ValueError("Could not decode file as UTF-16") from e
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            return data.decode("utf-16-le")
        except UnicodeDecodeError:
            try:
                return data.decode("utf-16-be")
            except UnicodeDecodeError as e:
                raise ValueError(
                    "Could not decode subtitle file as UTF-8 or UTF-16; save the file as UTF-8."
                ) from e


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    write_json_atomic(path, data)


def _merge_artifact_paths(base: dict[str, Any], inc: dict[str, str]) -> None:
    ap = dict(base.get("artifact_paths") or {})
    ap.update(inc)
    base["artifact_paths"] = ap


def import_external_srt(*, job_workspace: Path, source_path: Path) -> dict[str, Any]:
    """
    Read an external .srt, normalize, write artifacts/transcribe/source.srt,
    write external_srt_manifest.json, and merge job_state.json / video_state.json.
    """
    job_workspace = job_workspace.expanduser().resolve()
    source_path = source_path.expanduser().resolve()
    if not job_workspace.is_dir():
        raise FileNotFoundError(f"Job workspace not found: {job_workspace}")
    if not source_path.is_file():
        raise FileNotFoundError(f"Source SRT not found: {source_path}")
    suffix = source_path.suffix.lower()
    if suffix != ".srt":
        raise ValueError(f"Only .srt files are supported for import (got {source_path.suffix!r}).")

    raw_bytes = source_path.read_bytes()
    original_size_bytes = len(raw_bytes)
    if original_size_bytes == 0:
        raise ValueError("SRT file is empty")

    decoded = _decode_subtitle_bytes(raw_bytes)
    normalized = normalize_srt_text(decoded)
    cues = parse_srt_cues(normalized)

    transcribe_dir = job_workspace / "artifacts" / "transcribe"
    transcribe_dir.mkdir(parents=True, exist_ok=True)
    out_srt = transcribe_dir / "source.srt"
    out_srt.write_text(normalized, encoding="utf-8", newline="\n")

    imported_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    manifest: dict[str, Any] = {
        "source_path": str(source_path.resolve()),
        "original_size_bytes": int(original_size_bytes),
        "cue_count": len(cues),
        "first_cue_start_ms": int(cues[0].start_ms),
        "last_cue_end_ms": int(cues[-1].end_ms),
        "imported_at": imported_at,
    }
    manifest_path = transcribe_dir / "external_srt_manifest.json"
    write_json_atomic(manifest_path, manifest)

    job_id = job_workspace.name
    out_resolved = str(out_srt.resolve())
    origin_resolved = str(source_path.resolve())

    job_state_path = job_workspace / "job_state.json"
    video_state_path = job_workspace / "video_state.json"

    job_state = _load_json(job_state_path)
    video_state = _load_json(video_state_path)

    job_id = str(job_state.get("job_id") or job_id)

    input_mp4 = job_workspace / "input" / "source.mp4"
    transcribe_input_video = str(input_mp4.resolve()) if input_mp4.is_file() else job_state.get(
        "transcribe_input_video"
    )

    vid_fp = None
    if input_mp4.is_file():
        try:
            vid_fp = fingerprint_file(input_mp4)
        except OSError:
            vid_fp = job_state.get("input_video_fingerprint_at_transcribe")

    job_updates: dict[str, Any] = {
        "job_id": job_id,
        "job_workspace": str(job_workspace),
        "status": "transcribed",
        "current_stage": "transcribed",
        "last_error": None,
        "subtitle_extractor": "external_srt",
        "transcription_engine": "external_srt",
        "transcribe_output_srt": out_resolved,
        "transcribe_input_video": transcribe_input_video,
    }
    if vid_fp is not None:
        job_updates["input_video_fingerprint_at_transcribe"] = vid_fp

    job_state.update(job_updates)
    _merge_artifact_paths(
        job_state,
        {
            "source_srt": out_resolved,
            "source_srt_origin": origin_resolved,
        },
    )
    _write_json(job_state_path, job_state)

    video_updates: dict[str, Any] = {
        "video_id": str(video_state.get("video_id") or job_id),
        "status": "transcribed",
        "current_stage": "transcribed",
        "last_error": None,
        "subtitle_extractor": "external_srt",
        "transcription_engine": "external_srt",
    }
    video_state.update(video_updates)
    _merge_artifact_paths(
        video_state,
        {
            "source_srt": out_resolved,
            "source_srt_origin": origin_resolved,
        },
    )
    _write_json(video_state_path, video_state)

    return manifest
