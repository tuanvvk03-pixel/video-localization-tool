"""Pipeline progress + stage-label computation.

Turns a job/video state dict (+ optional workspace for filesystem signals) into
the ``/api/job-progress`` payload: stage labels, ranks, weighted overall percent
and lifecycle. Extracted from the server monolith with behaviour identical to the
previous inline code. Acyclic deps:

    server.py + server_dashboard ─> server_progress ─> server_import_config / server_extractor

The leading-underscore names are kept so existing call sites import them
unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from desktop.server_extractor import _VALID_EXTRACTORS
from desktop.server_import_config import _clean_import_config, _load_json_file
from engine import run_job

_STAGE_LABELS = {
    "imported": "Imported input",
    "input_required": "Waiting for input",
    "transcribed": "Transcribed source speech",
    "translated": "Translated subtitles",
    "translated_ready": "Translated subtitles",
    "voice_edit_pending": "Waiting for subtitle edit",
    "voice_edited": "Voice subtitle edited",
    "subtitle_finalized": "Finalized subtitle",
    "final_subtitle_ready": "Finalized subtitle",
    "tts_generated": "Generated TTS audio",
    "tts_manifest_required": "Waiting for TTS manifest",
    "tts_failed": "TTS failed",
    "aligned": "Aligned subtitles and audio",
    "mixed": "Mixed dubbed audio",
    "rendered": "Rendered final video",
    "done": "Completed",
}

_RUNNING_STAGE_LABELS = {
    "transcribed": "Transcribing source speech",
    "translated": "Translating subtitles",
    "subtitle_finalized": "Finalizing subtitle",
    "tts_generated": "Generating TTS audio",
    "aligned": "Aligning subtitles and audio",
    "mixed": "Mixing dubbed audio",
    "rendered": "Rendering final video",
}

_STAGE_WEIGHTS = {
    "imported": 1.0,
    "transcribed": 15.0,
    "translated": 25.0,
    "subtitle_finalized": 1.0,
    "tts_generated": 25.0,
    "aligned": 5.0,
    "mixed": 5.0,
    "rendered": 20.0,
    "done": 0.0,
}

_STAGE_ALIASES = {
    "translated_ready": "translated",
    "voice_edit_pending": "translated",
    "voice_edited": "translated",
    "final_subtitle_ready": "subtitle_finalized",
    "finalize_subtitle_required": "translated",
    "final_subtitle_required": "subtitle_finalized",
    "tts_manifest_required": "tts_generated",
    "compact_tts_failed": "tts_generated",
    "align_failed": "tts_generated",
    "mix_failed": "aligned",
    "render_failed": "mixed",
}


def _normalize_stage_name(stage: str) -> str:
    stage = str(stage or "").strip()
    if not stage:
        return ""
    if stage in run_job.STAGE_ORDER:
        return stage
    return _STAGE_ALIASES.get(stage, "")


def _safe_stage_rank(stage: str) -> int:
    normalized = _normalize_stage_name(stage)
    if not normalized:
        return -1
    try:
        return run_job.STAGE_ORDER.index(normalized)
    except ValueError:
        return -1


def _stage_label(stage: str, *, status: str = "") -> str:
    stage = str(stage or "").strip()
    if not stage:
        return "Waiting to start"
    if str(status or "").strip().lower() == "running":
        return _RUNNING_STAGE_LABELS.get(stage, _STAGE_LABELS.get(stage, stage.replace("_", " ").title()))
    return _STAGE_LABELS.get(stage, stage.replace("_", " ").title())


def _status_label(status: str, *, current_stage: str) -> str:
    status = str(status or "").strip().lower()
    if status == "failed":
        return "Failed"
    if status == "blocked":
        return "Needs user action"
    if status in {"rendered", "done"}:
        return "Completed"
    if current_stage:
        return "Running"
    return "Idle"


def _count_srt_cues(srt_path: Path) -> int:
    if not srt_path.is_file():
        return 0
    try:
        text = srt_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    return text.count("-->")


def _read_render_progress_us(progress_path: Path) -> int:
    if not progress_path.is_file():
        return 0
    try:
        text = progress_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    last = 0
    for line in text.splitlines():
        if line.startswith("out_time_us="):
            try:
                last = int(line.split("=", 1)[1].strip())
            except (ValueError, IndexError):
                continue
        elif line.startswith("out_time_ms="):
            # Older ffmpeg builds use out_time_ms but value is microseconds.
            try:
                last = int(line.split("=", 1)[1].strip())
            except (ValueError, IndexError):
                continue
    return max(0, last)


def _read_ocr_progress(progress_path: Path) -> tuple[int, int]:
    """Parse artifacts/transcribe/ocr_progress.txt; returns (processed, total)."""
    if not progress_path.is_file():
        return 0, 0
    processed = 0
    total = 0
    try:
        for line in progress_path.read_text(encoding="utf-8").splitlines():
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            try:
                v = int(val.strip())
            except ValueError:
                continue
            k = key.strip().lower()
            if k == "processed_frames":
                processed = v
            elif k == "total_frames":
                total = v
    except OSError:
        return 0, 0
    return processed, total


def _progress_subtitle_extractor(jw: Path | None, state: dict[str, Any]) -> str:
    """Best-effort extractor lookup so audio-only runs ignore stale OCR progress files."""
    extractor = str(state.get("subtitle_extractor") or "").strip().lower()
    if extractor in _VALID_EXTRACTORS:
        return extractor
    if jw is None:
        return ""
    vstate = _load_json_file(jw / "video_state.json")
    extractor = str(vstate.get("subtitle_extractor") or "").strip().lower()
    if extractor in _VALID_EXTRACTORS:
        return extractor
    raw_import = vstate.get("import_config")
    if isinstance(raw_import, dict):
        extractor = str(_clean_import_config(raw_import).get("subtitle_extractor") or "").strip().lower()
        if extractor in _VALID_EXTRACTORS:
            return extractor
    return ""


def _substage_fraction(jw: Path | None, stage: str, state: dict[str, Any]) -> float:
    """Return 0.0..1.0 progress within the running stage from filesystem signals."""
    if jw is None or not stage:
        return 0.0
    if stage == "transcribed":
        extractor = _progress_subtitle_extractor(jw, state)
        if extractor in ("audio_only", "external_srt"):
            return 0.0
        # OCR-involved runs emit artifacts/transcribe/ocr_progress.txt. When present,
        # surface it so the progress bar does not sit at 0% for minutes on CPU OCR.
        processed, total = _read_ocr_progress(
            jw / "artifacts" / "transcribe" / "ocr_progress.txt"
        )
        if total > 0:
            return max(0.0, min(1.0, processed / total))
        return 0.0
    if stage == "tts_generated":
        total = _count_srt_cues(jw / "artifacts" / "translate" / "final_subtitle.srt")
        if total <= 0:
            return 0.0
        cues_dir = jw / "artifacts" / "tts" / "cues"
        if not cues_dir.is_dir():
            return 0.0
        try:
            done = sum(1 for p in cues_dir.iterdir() if p.is_file() and p.suffix == ".wav")
        except OSError:
            return 0.0
        return max(0.0, min(1.0, done / total))
    if stage == "rendered":
        target_us = 0
        try:
            target_us = int(float(state.get("render_total_duration_sec") or 0.0) * 1_000_000)
        except (TypeError, ValueError):
            target_us = 0
        if target_us <= 0:
            manifest_path = jw / "artifacts" / "render" / "render_manifest.json"
            if manifest_path.is_file():
                try:
                    body = json.loads(manifest_path.read_text(encoding="utf-8"))
                    target_us = int(float(body.get("video_duration_sec") or 0.0) * 1_000_000)
                except (OSError, json.JSONDecodeError, TypeError, ValueError):
                    target_us = 0
        if target_us <= 0:
            return 0.0
        current_us = _read_render_progress_us(jw / "artifacts" / "render" / "render_progress.txt")
        if current_us <= 0:
            return 0.0
        return max(0.0, min(1.0, current_us / target_us))
    return 0.0


def _weighted_percent(
    target_rank: int,
    current_rank: int,
    is_running: bool,
    substage_fraction: float,
) -> int:
    if target_rank <= 0:
        return 100 if (current_rank >= 0 and not is_running) else 0
    weights = [_STAGE_WEIGHTS.get(run_job.STAGE_ORDER[i], 1.0) for i in range(target_rank + 1)]
    # Total weight covers stages 1..target_rank (entering stage N means stage 0..N-1 done).
    total = sum(weights[1:]) or 1.0
    if current_rank < 0:
        return 0
    if current_rank >= target_rank and not is_running:
        return 100
    completed = sum(weights[1 : min(current_rank, target_rank) + (0 if is_running else 1)])
    if is_running and 0 < current_rank <= target_rank:
        completed += weights[current_rank] * max(0.0, min(1.0, substage_fraction))
    pct = int(round(completed / total * 100))
    return max(0, min(99, pct)) if is_running else max(0, min(100, pct))


def _progress_payload(state: dict[str, Any], jw: Path | None = None) -> dict[str, Any]:
    current_stage = str(state.get("current_stage") or state.get("status") or "")
    status = str(state.get("status") or "")
    current_rank = _safe_stage_rank(current_stage)
    runner = state.get("runner") if isinstance(state.get("runner"), dict) else {}
    target_stage = str(runner.get("to_stage") or "")
    target_rank = _safe_stage_rank(target_stage)
    if target_rank < 0:
        target_rank = len(run_job.STAGE_ORDER) - 1
        target_stage = run_job.STAGE_ORDER[target_rank]

    stage_total = max(1, target_rank)
    display_rank = max(0, min(current_rank, target_rank)) if current_rank >= 0 else 0
    completed_rank = display_rank
    is_running = str(status).lower() == "running"
    if is_running and current_rank > 0:
        completed_rank = max(0, min(current_rank - 1, target_rank))

    normalized_running_stage = _normalize_stage_name(current_stage) if is_running else ""
    substage_fraction = _substage_fraction(jw, normalized_running_stage, state) if is_running else 0.0
    overall_percent = _weighted_percent(target_rank, current_rank, is_running, substage_fraction)

    if str(status).lower() == "failed":
        lifecycle = "failed"
    elif str(status).lower() == "blocked":
        lifecycle = "blocked"
    elif current_rank >= 0 and display_rank >= target_rank and not is_running:
        lifecycle = "completed"
        overall_percent = 100
    elif current_stage:
        lifecycle = "running"
    else:
        lifecycle = "idle"

    return {
        "current_stage": current_stage,
        "current_stage_rank": current_rank,
        "current_stage_label": _stage_label(current_stage, status=status),
        "stage_index": completed_rank if current_rank >= 0 else -1,
        "stage_total": stage_total,
        "target_stage": target_stage,
        "target_stage_label": _stage_label(target_stage),
        "target_stage_rank": target_rank,
        "overall_percent": overall_percent,
        "substage_percent": int(round(substage_fraction * 100)) if is_running else 0,
        "status": status,
        "status_label": _status_label(status, current_stage=current_stage),
        "lifecycle": lifecycle,
        "stage_order": run_job.STAGE_ORDER,
    }
