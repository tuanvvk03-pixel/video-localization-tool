"""Transcription coverage metrics vs video duration (transcribe stage)."""
from __future__ import annotations

from engine.json_store import write_json_atomic
import json
from pathlib import Path
from typing import Any


def union_intervals_sec(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not intervals:
        return []
    iv = sorted(((float(a), float(b)) for a, b in intervals if b > a), key=lambda x: (x[0], x[1]))
    out: list[tuple[float, float]] = [iv[0]]
    for s, e in iv[1:]:
        ps, pe = out[-1]
        if s <= pe:
            out[-1] = (ps, max(pe, e))
        else:
            out.append((s, e))
    return out


def long_gaps_in_timeline(
    merged_sec: list[tuple[float, float]],
    *,
    total_sec: float,
    min_gap_sec: float,
) -> list[dict[str, float]]:
    gaps: list[dict[str, float]] = []
    if total_sec <= 0:
        return gaps
    if not merged_sec:
        if total_sec >= min_gap_sec:
            gaps.append(
                {
                    "start_sec": 0.0,
                    "end_sec": total_sec,
                    "duration_sec": total_sec,
                    "start_ms": 0,
                    "end_ms": int(round(total_sec * 1000.0)),
                    "duration_ms": int(round(total_sec * 1000.0)),
                }
            )
        return gaps
    if merged_sec[0][0] >= min_gap_sec:
        g0 = merged_sec[0][0]
        gaps.append(
            {
                "start_sec": 0.0,
                "end_sec": g0,
                "duration_sec": g0,
                "start_ms": 0,
                "end_ms": int(round(g0 * 1000.0)),
                "duration_ms": int(round(g0 * 1000.0)),
            }
        )
    for i in range(len(merged_sec) - 1):
        a_end = merged_sec[i][1]
        b_start = merged_sec[i + 1][0]
        g = b_start - a_end
        if g >= min_gap_sec:
            gaps.append(
                {
                    "start_sec": a_end,
                    "end_sec": b_start,
                    "duration_sec": g,
                    "start_ms": int(round(a_end * 1000.0)),
                    "end_ms": int(round(b_start * 1000.0)),
                    "duration_ms": int(round(g * 1000.0)),
                }
            )
    last_end = merged_sec[-1][1]
    tail = total_sec - last_end
    if tail >= min_gap_sec:
        gaps.append(
            {
                "start_sec": last_end,
                "end_sec": total_sec,
                "duration_sec": tail,
                "start_ms": int(round(last_end * 1000.0)),
                "end_ms": int(round(total_sec * 1000.0)),
                "duration_ms": int(round(tail * 1000.0)),
            }
        )
    return gaps


def build_transcription_report(
    *,
    segments: list[Any],
    video_duration_ms: int | None,
    long_gap_ms: int = 2000,
) -> dict[str, Any]:
    """segments: faster_whisper Segment-like with .start, .end, .text."""
    raw: list[tuple[float, float]] = []
    non_empty = 0
    for seg in segments:
        text = (getattr(seg, "text", None) or "").strip()
        if not text:
            continue
        non_empty += 1
        try:
            s = float(getattr(seg, "start", 0.0))
            e = float(getattr(seg, "end", 0.0))
        except Exception:
            continue
        if e > s:
            raw.append((s, e))

    merged = union_intervals_sec(raw)
    total_sec = sum(max(0.0, b - a) for a, b in merged)
    total_ms = int(round(total_sec * 1000.0))

    vd_ms = int(video_duration_ms) if video_duration_ms and video_duration_ms > 0 else None
    vd_sec = (vd_ms / 1000.0) if vd_ms else 0.0
    ratio = None
    if vd_ms and vd_ms > 0:
        ratio = min(1.0, total_ms / float(vd_ms))

    min_gap_sec = max(0.1, float(long_gap_ms) / 1000.0)
    gaps = long_gaps_in_timeline(merged, total_sec=vd_sec, min_gap_sec=min_gap_sec)

    warnings: list[str] = []
    if ratio is not None and ratio < 0.12:
        warnings.append("critical_low_transcription_coverage")
    elif ratio is not None and ratio < 0.22:
        warnings.append("low_transcription_coverage")
    if len(gaps) > 15:
        warnings.append("many_long_non_speech_gaps")

    return {
        "version": 1,
        "segment_count": non_empty,
        "total_transcribed_ms": total_ms,
        "video_duration_ms": vd_ms,
        "transcription_coverage_ratio": ratio,
        "long_gaps": gaps,
        "long_gap_threshold_ms": int(long_gap_ms),
        "warnings": warnings,
    }


def write_transcription_report(path: Path, body: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, body)
