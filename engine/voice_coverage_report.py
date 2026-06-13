"""
Voice coverage metrics after align: voiced time vs video duration and long silent gaps.
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import json
import subprocess
from pathlib import Path
from typing import Any

from engine.ffmpeg_bins import resolve_ffprobe_executable

REPORT_FILENAME = "voice_coverage_report.json"


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
        sec = float((proc.stdout or "").strip())
    except ValueError:
        return None
    return int(round(sec * 1000.0))


def _union_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    out: list[tuple[int, int]] = [intervals[0]]
    for s, e in intervals[1:]:
        ps, pe = out[-1]
        if s <= pe:
            out[-1] = (ps, max(pe, e))
        else:
            out.append((s, e))
    return out


def _silent_gaps_over_ms(
    merged: list[tuple[int, int]], *, total_ms: int, min_gap_ms: int
) -> list[dict[str, int]]:
    gaps: list[dict[str, int]] = []
    if total_ms <= 0:
        return gaps
    if not merged:
        if total_ms >= min_gap_ms:
            gaps.append({"start_ms": 0, "end_ms": total_ms, "duration_ms": total_ms})
        return gaps
    if merged[0][0] >= min_gap_ms:
        gaps.append({"start_ms": 0, "end_ms": merged[0][0], "duration_ms": merged[0][0]})
    for i in range(len(merged) - 1):
        a_end = merged[i][1]
        b_start = merged[i + 1][0]
        g = b_start - a_end
        if g >= min_gap_ms:
            gaps.append({"start_ms": a_end, "end_ms": b_start, "duration_ms": g})
    last_end = merged[-1][1]
    tail = total_ms - last_end
    if tail >= min_gap_ms:
        gaps.append({"start_ms": last_end, "end_ms": total_ms, "duration_ms": tail})
    return gaps


def build_voice_coverage_report(
    job_workspace: Path,
    alignment_manifest: dict[str, Any],
    *,
    gap_threshold_ms: int = 1200,
) -> dict[str, Any]:
    jw = job_workspace.expanduser().resolve()
    video = jw / "input" / "source.mp4"
    video_duration_ms = _probe_video_duration_ms(video)

    cues = alignment_manifest.get("cues") or []
    raw_iv: list[tuple[int, int]] = []
    for c in cues:
        try:
            ps = int(c.get("placed_start_ms"))
            pe = int(c.get("placed_end_ms"))
        except Exception:
            continue
        if pe > ps:
            raw_iv.append((ps, pe))

    merged = _union_intervals(raw_iv)
    total_voiced_ms = sum(max(0, b - a) for a, b in merged)

    if video_duration_ms and video_duration_ms > 0:
        voice_coverage_ratio = min(1.0, total_voiced_ms / float(video_duration_ms))
    else:
        voice_coverage_ratio = None

    silent_gaps = _silent_gaps_over_ms(merged, total_ms=video_duration_ms or 0, min_gap_ms=gap_threshold_ms)

    warnings: list[str] = []
    if voice_coverage_ratio is not None and voice_coverage_ratio < 0.22:
        warnings.append("low_voice_coverage_ratio")
    if len(silent_gaps) > 12:
        warnings.append("many_long_silent_gaps")
    max_gap = max((g["duration_ms"] for g in silent_gaps), default=0)
    if max_gap > 8000:
        warnings.append("very_long_silent_gap")

    recommend_mix_mode: str | None = None
    if voice_coverage_ratio is not None and voice_coverage_ratio < 0.35:
        recommend_mix_mode = "duck_original_speech"

    return {
        "version": 1,
        "cue_count": len(cues),
        "total_voiced_ms": int(total_voiced_ms),
        "video_duration_ms": video_duration_ms,
        "voice_coverage_ratio": voice_coverage_ratio,
        "silent_gaps_over_1200ms": silent_gaps,
        "gap_threshold_ms": gap_threshold_ms,
        "warnings": warnings,
        "recommend_mix_mode": recommend_mix_mode,
        "input_video": str(video.resolve()) if video.is_file() else None,
    }


def write_voice_coverage_report(job_workspace: Path, alignment_manifest: dict[str, Any]) -> Path | None:
    body = build_voice_coverage_report(job_workspace, alignment_manifest)
    out = job_workspace.expanduser().resolve() / "artifacts" / "aligned" / REPORT_FILENAME
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        write_json_atomic(out, body)
        return out
    except OSError:
        return None
