"""Subtitle-extractor + OCR setting normalization.

Shared by the import-config, progress and run handlers. Extracted from the
server monolith with behaviour identical to the previous inline code. Depends
only on ``engine.ocr`` (lazily), so the dependency graph stays acyclic:

    server.py + server_import_config + server_progress ─> server_extractor

The leading-underscore names are kept so existing call sites import them
unchanged.
"""
from __future__ import annotations

import json
import sys
from typing import Any

_VALID_EXTRACTORS = {"audio_only", "ocr_only", "hybrid", "external_srt"}
_VALID_OCR_PROVIDERS = {"paddleocr", "rapidocr"}


def _normalize_ocr_provider(raw: Any) -> str:
    """Return a canonical ocr_provider string ('' if unknown/empty)."""
    from engine.ocr import canonical_provider_name

    return canonical_provider_name(str(raw or ""))


def _normalize_extractor_settings(body: dict[str, Any]) -> dict[str, str]:
    """Pull subtitle_extractor / ocr_* from a request payload and normalize values.

    Returns a dict with keys `subtitle_extractor`, `ocr_provider`, `ocr_language`,
    `ocr_roi` (JSON string or empty), `ocr_device`. Invalid values collapse to
    audio_only / empty defaults so the downstream CLI ignores OCR entirely.
    """
    raw_extractor = str(body.get("subtitle_extractor") or "audio_only").strip().lower()
    coerced_from_deprecated = raw_extractor in {"ocr_only", "hybrid"}
    extractor = raw_extractor
    if extractor not in _VALID_EXTRACTORS:
        extractor = "audio_only"
    if coerced_from_deprecated:
        sys.stderr.write(
            f"[desktop.server] subtitle_extractor={raw_extractor!r} is deprecated; using audio_only.\n"
        )
        extractor = "audio_only"
    if extractor == "external_srt":
        return {
            "subtitle_extractor": "external_srt",
            "ocr_provider": "",
            "ocr_language": "",
            "ocr_roi": "",
            "ocr_device": "",
        }
    if coerced_from_deprecated:
        return {
            "subtitle_extractor": "audio_only",
            "ocr_provider": "",
            "ocr_language": "",
            "ocr_roi": "",
            "ocr_device": "",
        }
    provider = _normalize_ocr_provider(body.get("ocr_provider"))
    language = str(body.get("ocr_language") or "").strip().lower()
    device = str(body.get("ocr_device") or "").strip().lower()
    if device not in {"", "auto", "cpu", "cuda"}:
        device = ""
    raw_roi = body.get("ocr_roi")
    roi_str = ""
    if isinstance(raw_roi, str):
        roi_str = raw_roi.strip()
    elif isinstance(raw_roi, dict):
        try:
            roi_str = json.dumps(raw_roi, ensure_ascii=False)
        except (TypeError, ValueError):
            roi_str = ""
    return {
        "subtitle_extractor": extractor,
        "ocr_provider": provider,
        "ocr_language": language,
        "ocr_roi": roi_str,
        "ocr_device": device,
    }


def _normalize_source_language(value: Any) -> str:
    lang = str(value or "").strip().lower()
    if lang in {"", "auto"}:
        return ""
    if lang in {"zh", "en", "ja", "ko"}:
        return lang
    return ""
