"""Merge ASR (source_audio.srt) and OCR (source_ocr.srt) into canonical source.srt.

Implements the rule set from docs/10_ocr_subtitle_extraction_roadmap.md section 5:

  diff <= match_threshold  (default 0.15) -> keep OCR text, source="fused_match"
  diff <= drift_threshold  (default 0.40) -> keep OCR text, source="fused_drift"
  diff >  drift_threshold              -> keep both (OCR first), source="fused_disagreement",
                                           needs_review=true

Cues that overlap but do not find a pairing are kept as-is with source="asr" or "ocr".
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

_SRT_TIMESTAMP_RE = re.compile(r"(\d+):(\d{2}):(\d{2}),(\d{3})")


@dataclass
class Cue:
    start_ms: int
    end_ms: int
    text: str


@dataclass
class FusedCue:
    start_ms: int
    end_ms: int
    text: str
    source: str
    ocr_confidence: float | None = None
    asr_text_diff: float | None = None
    ocr_text: str | None = None
    asr_text: str | None = None
    needs_review: bool = False


def _ts_to_ms(m: re.Match[str]) -> int:
    h, mm, s, ms = (int(m.group(i)) for i in (1, 2, 3, 4))
    return h * 3_600_000 + mm * 60_000 + s * 1000 + ms


def _ms_to_ts(ms: int) -> str:
    ms = max(0, int(ms))
    h = ms // 3_600_000
    rem = ms - h * 3_600_000
    mm = rem // 60_000
    rem -= mm * 60_000
    s = rem // 1000
    ms_part = rem - s * 1000
    return f"{h:02d}:{mm:02d}:{s:02d},{ms_part:03d}"


def parse_srt(path: Path) -> list[Cue]:
    """Tolerant SRT parser; returns [] if the file is missing or empty."""
    if not path.is_file():
        return []
    raw = path.read_text(encoding="utf-8", errors="replace")
    text = raw.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []
    out: list[Cue] = []
    for block in re.split(r"\n\s*\n", text):
        lines = [ln for ln in block.splitlines() if ln.strip() != ""]
        if len(lines) < 2:
            continue
        ts_idx = 1 if lines[0].strip().isdigit() else 0
        if ts_idx >= len(lines):
            continue
        matches = list(_SRT_TIMESTAMP_RE.finditer(lines[ts_idx]))
        if len(matches) < 2:
            continue
        start = _ts_to_ms(matches[0])
        end = _ts_to_ms(matches[1])
        body = "\n".join(lines[ts_idx + 1 :]).strip()
        if not body:
            continue
        out.append(Cue(start_ms=start, end_ms=end, text=body))
    out.sort(key=lambda c: (c.start_ms, c.end_ms))
    return out


def _levenshtein_normalized(a: str, b: str) -> float:
    if not a and not b:
        return 0.0
    if not a or not b:
        return 1.0
    if a == b:
        return 0.0
    la, lb = len(a), len(b)
    if la < lb:
        a, b = b, a
        la, lb = lb, la
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i] + [0] * lb
        for j, cb in enumerate(b, start=1):
            ins = curr[j - 1] + 1
            dele = prev[j] + 1
            sub = prev[j - 1] + (0 if ca == cb else 1)
            curr[j] = min(ins, dele, sub)
        prev = curr
    return prev[lb] / float(max(la, 1))


def _overlap_ms(a: Cue, b: Cue) -> int:
    start = max(a.start_ms, b.start_ms)
    end = min(a.end_ms, b.end_ms)
    return max(0, end - start)


def fuse_cues(
    asr_cues: list[Cue],
    ocr_cues: list[Cue],
    *,
    ocr_confidences: dict[int, float] | None = None,
    match_threshold: float = 0.15,
    drift_threshold: float = 0.40,
) -> list[FusedCue]:
    """For each OCR cue, greedily claim the ASR cue with the largest time overlap.

    - No overlap -> source="ocr"
    - Overlap + diff <= match_threshold -> source="fused_match", OCR text kept
    - Overlap + match < diff <= drift_threshold -> source="fused_drift", OCR text kept
    - Overlap + diff > drift_threshold -> source="fused_disagreement", both texts kept, needs_review
    - ASR cues never matched -> source="asr"
    """
    confs = ocr_confidences or {}
    used_asr: set[int] = set()
    fused: list[FusedCue] = []

    for oi, ocr in enumerate(ocr_cues):
        best_ai = -1
        best_overlap = 0
        for ai, asr in enumerate(asr_cues):
            if ai in used_asr:
                continue
            ov = _overlap_ms(ocr, asr)
            if ov > best_overlap:
                best_overlap = ov
                best_ai = ai
        ocr_conf = confs.get(oi)
        if best_ai < 0 or best_overlap <= 0:
            fused.append(
                FusedCue(
                    start_ms=ocr.start_ms,
                    end_ms=ocr.end_ms,
                    text=ocr.text,
                    source="ocr",
                    ocr_confidence=ocr_conf,
                )
            )
            continue

        asr = asr_cues[best_ai]
        used_asr.add(best_ai)
        diff = _levenshtein_normalized(ocr.text, asr.text)
        start = min(ocr.start_ms, asr.start_ms)
        end = max(ocr.end_ms, asr.end_ms)
        diff_rounded = round(diff, 3)

        if diff <= match_threshold:
            fused.append(
                FusedCue(
                    start_ms=start,
                    end_ms=end,
                    text=ocr.text,
                    source="fused_match",
                    ocr_confidence=ocr_conf,
                    asr_text_diff=diff_rounded,
                )
            )
        elif diff <= drift_threshold:
            fused.append(
                FusedCue(
                    start_ms=start,
                    end_ms=end,
                    text=ocr.text,
                    source="fused_drift",
                    ocr_confidence=ocr_conf,
                    asr_text_diff=diff_rounded,
                    ocr_text=ocr.text,
                    asr_text=asr.text,
                )
            )
        else:
            merged_text = f"{ocr.text}\n{asr.text}"
            fused.append(
                FusedCue(
                    start_ms=start,
                    end_ms=end,
                    text=merged_text,
                    source="fused_disagreement",
                    ocr_confidence=ocr_conf,
                    asr_text_diff=diff_rounded,
                    ocr_text=ocr.text,
                    asr_text=asr.text,
                    needs_review=True,
                )
            )

    for ai, asr in enumerate(asr_cues):
        if ai in used_asr:
            continue
        fused.append(
            FusedCue(
                start_ms=asr.start_ms,
                end_ms=asr.end_ms,
                text=asr.text,
                source="asr",
            )
        )

    fused.sort(key=lambda c: (c.start_ms, c.end_ms))
    return fused


def cues_to_srt(cues: list[FusedCue]) -> str:
    out: list[str] = []
    for i, c in enumerate(cues, start=1):
        out.append(str(i))
        out.append(f"{_ms_to_ts(c.start_ms)} --> {_ms_to_ts(c.end_ms)}")
        out.append(c.text)
        out.append("")
    return "\n".join(out).rstrip() + ("\n" if out else "")


def build_provenance(
    fused: list[FusedCue],
    *,
    asr_cue_count: int,
    ocr_cue_count: int,
    extractor: str = "hybrid",
) -> dict:
    entries: list[dict] = []
    for i, c in enumerate(fused, start=1):
        entry: dict = {"index": i, "source": c.source}
        if c.ocr_confidence is not None:
            entry["ocr_confidence"] = c.ocr_confidence
        if c.asr_text_diff is not None:
            entry["asr_text_diff"] = c.asr_text_diff
        if c.source == "fused_drift":
            entry["text_drift"] = True
            if c.ocr_text is not None:
                entry["ocr_text"] = c.ocr_text
            if c.asr_text is not None:
                entry["asr_text"] = c.asr_text
        elif c.source == "fused_disagreement":
            entry["ocr_text"] = c.ocr_text or ""
            entry["asr_text"] = c.asr_text or ""
            entry["needs_review"] = True
        entries.append(entry)
    return {
        "extractor": extractor,
        "asr_cue_count": asr_cue_count,
        "ocr_cue_count": ocr_cue_count,
        "final_cue_count": len(fused),
        "cues": entries,
    }


def fuse_files(
    asr_srt: Path,
    ocr_srt: Path,
    *,
    out_srt: Path,
    out_provenance: Path,
    match_threshold: float = 0.15,
    drift_threshold: float = 0.40,
    extractor_label: str = "hybrid",
) -> dict:
    """Read SRT files, fuse, write merged SRT + provenance JSON. Returns provenance dict."""
    asr_cues = parse_srt(asr_srt)
    ocr_cues = parse_srt(ocr_srt)
    fused = fuse_cues(
        asr_cues,
        ocr_cues,
        match_threshold=match_threshold,
        drift_threshold=drift_threshold,
    )
    out_srt.parent.mkdir(parents=True, exist_ok=True)
    out_srt.write_text(cues_to_srt(fused), encoding="utf-8")
    prov = build_provenance(
        fused,
        asr_cue_count=len(asr_cues),
        ocr_cue_count=len(ocr_cues),
        extractor=extractor_label,
    )
    out_provenance.write_text(
        json.dumps(prov, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return prov
