"""Error classification for the desktop server.

Maps raw pipeline error text / log tails to a short, stable error code and a
human summary the UI can surface. Extracted from ``server.py`` as a first,
self-contained seam in the ongoing decomposition of that monolith — it has no
dependency on the HTTP layer or any module-level server state.
"""
from __future__ import annotations

import re

# Inline hex addresses (e.g. ``0x7ffd...``) are noise that defeats pattern
# matching and varies run-to-run; collapse them before classifying.
HEX_RE = re.compile(r"0x[0-9a-fA-F]+")

# Ordered: the first pattern that matches wins, so list more specific stages
# (ffmpeg, tts, llm) before the catch-all input/workspace patterns.
ERROR_PATTERNS: list[tuple[re.Pattern[str], tuple[str, str]]] = [
    (re.compile(r"ffmpeg|ffprobe|libass", re.IGNORECASE), ("FFMPEG", "FFmpeg/render pipeline failure.")),
    (re.compile(r"edge-tts|tts|voice", re.IGNORECASE), ("TTS", "Text-to-speech stage failed.")),
    (re.compile(r"openai|gpt|llm|translation qa|translate", re.IGNORECASE), ("LLM", "Translation/LLM stage failed.")),
    (re.compile(r"subtitle|srt|cue", re.IGNORECASE), ("SUBTITLE", "Subtitle input or formatting issue.")),
    (re.compile(r"workspace|project root|job workspace|path does not exist", re.IGNORECASE), ("WORKSPACE", "Workspace path or project layout issue.")),
    (re.compile(r"input|source\.mp4|video file|not found|missing", re.IGNORECASE), ("INPUT", "Missing input file or required artifact.")),
]


def sanitize_log_line(line: str) -> str:
    compact = re.sub(r"\s+", " ", str(line or "")).strip()
    if not compact:
        return ""
    return HEX_RE.sub("<hex>", compact)


def classify_error_details(
    message: str | None,
    log_tail: list[str] | None,
    *,
    fallback_code: str = "pipeline_error",
) -> dict[str, str]:
    parts = [str(message or "").strip()]
    parts.extend(sanitize_log_line(line) for line in (log_tail or []))
    haystack = "\n".join(part for part in parts if part)
    short_code = fallback_code.upper()
    summary = "Pipeline execution failed."
    for pattern, (candidate_code, candidate_summary) in ERROR_PATTERNS:
        if haystack and pattern.search(haystack):
            short_code = candidate_code
            summary = candidate_summary
            break
    return {"short_code": short_code, "summary": summary}
