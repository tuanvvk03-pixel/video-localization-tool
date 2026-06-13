"""Minimal SRT cue parser for orchestration (no legacy dich dependency)."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class SRTCue:
    index: int
    start_ms: int
    end_ms: int
    text: str


_TS_LINE_RE = re.compile(
    r"^(\d{1,2}:\d{2}:\d{2})[,.](\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2})[,.](\d{3})"
)


def _hms_to_ms(hms: str, frac: str) -> int:
    h, m, s = hms.split(":")
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(frac)


def _parse_timestamp_line(line: str) -> tuple[int, int] | None:
    line = line.strip()
    m = _TS_LINE_RE.match(line)
    if not m:
        return None
    start = _hms_to_ms(m.group(1), m.group(2))
    end = _hms_to_ms(m.group(3), m.group(4))
    return start, end


def parse_srt_cues(content: str) -> list[SRTCue]:
    """
    Robust SRT parsing for TTS:
    - supports UTF-8 (BOM already handled upstream), CRLF/LF, blank lines between cues
    - supports multiline cue text
    - index line is optional; if missing, cues are indexed sequentially
    - timestamp line may contain trailing settings after end timestamp
    """
    text = content.replace("\r\n", "\n").replace("\r", "\n")
    # Guard against BOM char that slipped through as a Unicode char.
    text = text.lstrip("\ufeff").strip()
    if not text:
        return []

    tag_re = re.compile(r"<[^>]+>")
    lines = [ln.rstrip("\n") for ln in text.split("\n")]

    cues: list[SRTCue] = []
    seq_index = 1
    i = 0
    n = len(lines)

    while i < n:
        # Skip blank lines
        while i < n and lines[i].strip() == "":
            i += 1
        if i >= n:
            break

        # Optional index line
        idx: int | None = None
        maybe_idx = lines[i].strip()
        if maybe_idx.isdigit():
            try:
                idx = int(maybe_idx)
                i += 1
            except ValueError:
                idx = None

        if i >= n:
            break

        # Timestamp line is required
        ts_line = lines[i].strip()
        ts = _parse_timestamp_line(ts_line)
        if ts is None:
            # Not a valid cue start; advance one line and keep scanning.
            i += 1
            continue
        start_ms, end_ms = ts
        i += 1

        # Collect multiline text until blank line
        body: list[str] = []
        while i < n and lines[i].strip() != "":
            body.append(lines[i].strip())
            i += 1

        raw = " ".join(s for s in body if s).strip()
        raw = tag_re.sub("", raw).strip()
        if not raw:
            continue

        raw = unicodedata.normalize("NFC", raw)
        cue_index = idx if idx is not None else seq_index
        seq_index += 1
        cues.append(SRTCue(index=cue_index, start_ms=start_ms, end_ms=end_ms, text=raw))

    cues.sort(key=lambda c: (c.start_ms, c.index))
    return cues


def _ms_to_hms(ms: int) -> str:
    ms = max(0, int(ms))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, frac = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{frac:03d}"


def cues_to_srt(cues: list[SRTCue]) -> str:
    """Serialize cues back to canonical SRT (1-based sequential indices, CRLF-free)."""
    parts: list[str] = []
    for i, c in enumerate(cues, start=1):
        parts.append(str(i))
        parts.append(f"{_ms_to_hms(c.start_ms)} --> {_ms_to_hms(c.end_ms)}")
        parts.append(c.text)
        parts.append("")
    return "\n".join(parts) + ("\n" if parts else "")
