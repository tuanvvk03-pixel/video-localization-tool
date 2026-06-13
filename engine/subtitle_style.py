"""Phase 6 — Subtitle styling.

Schema (per docs/02_pipeline_spec.md §6, docs/03_job_contract.md):

    {
      "subtitle_font": "<string>",                # optional, e.g. "Arial"
      "subtitle_background_color": "#RRGGBB",     # optional, also accepts #RRGGBBAA
      "bold": <bool>,                             # optional
      "italic": <bool>,                           # optional
      "align": "left" | "center" | "right",      # optional
      "margin_v": <int>,                          # optional, 0-500 px (ASS MarginV; larger = higher from bottom for bottom align)
      "font_size": <int>,                         # optional, 10-120 (ASS Fontsize); omit for libass default
    }

Storage locations:
- Project-global: ``<project_root>/style/global_subtitle_style.json``
- Per-video override: ``<video_workspace>/style_override.json``

``resolve_subtitle_style`` merges override onto global (override wins per field).
``style_to_ass_force_style`` produces an ffmpeg ``subtitles`` filter ``force_style``
string so the render stage can burn the style into video.
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import json
import re
from pathlib import Path
from typing import Any

PROJECT_STYLE_REL = Path("style") / "global_subtitle_style.json"
VIDEO_STYLE_OVERRIDE_REL = Path("style_override.json")

_STYLE_KEYS = (
    "subtitle_font",
    "subtitle_background_color",
    "bold",
    "italic",
    "align",
    "margin_v",
    "font_size",
)
_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_ALIGN_VALUES = {"left", "center", "right"}
_ASS_ALIGNMENT = {"left": 1, "center": 2, "right": 3}


class SubtitleStyleError(ValueError):
    pass


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SubtitleStyleError(f"Invalid JSON at {path}: {e}") from e
    if not isinstance(body, dict):
        raise SubtitleStyleError(f"Style file must be a JSON object: {path}")
    return body


def _write_json(path: Path, body: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, body)


def validate_style(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a cleaned style dict. Unknown keys are dropped; missing keys stay absent."""
    out: dict[str, Any] = {}
    font = raw.get("subtitle_font")
    if font is not None:
        if not isinstance(font, str) or not font.strip():
            raise SubtitleStyleError("subtitle_font must be a non-empty string")
        out["subtitle_font"] = font.strip()
    bg = raw.get("subtitle_background_color")
    if bg is not None:
        if not isinstance(bg, str) or not _HEX_RE.match(bg.strip()):
            raise SubtitleStyleError(
                "subtitle_background_color must be hex (#RRGGBB or #RRGGBBAA)"
            )
        out["subtitle_background_color"] = bg.strip()
    for field in ("bold", "italic"):
        if field in raw and raw[field] is not None:
            if not isinstance(raw[field], bool):
                raise SubtitleStyleError(f"{field} must be a boolean")
            out[field] = bool(raw[field])
    align = raw.get("align")
    if align is not None:
        if not isinstance(align, str) or align.strip() not in _ALIGN_VALUES:
            raise SubtitleStyleError(
                f"align must be one of {sorted(_ALIGN_VALUES)}"
            )
        out["align"] = align.strip()
    mv = raw.get("margin_v")
    if mv is not None and mv != "":
        if isinstance(mv, bool):
            raise SubtitleStyleError("margin_v must be an integer")
        try:
            mv_int = int(mv)
        except (TypeError, ValueError) as e:
            raise SubtitleStyleError("margin_v must be an integer") from e
        if mv_int < 0 or mv_int > 500:
            raise SubtitleStyleError("margin_v must be between 0 and 500 (pixels)")
        out["margin_v"] = mv_int
    fs = raw.get("font_size")
    if fs is not None and fs != "":
        if isinstance(fs, bool):
            raise SubtitleStyleError("font_size must be an integer")
        try:
            fs_int = int(fs)
        except (TypeError, ValueError) as e:
            raise SubtitleStyleError("font_size must be an integer") from e
        if fs_int < 10 or fs_int > 120:
            raise SubtitleStyleError("font_size must be between 10 and 120 (points)")
        out["font_size"] = fs_int
    return out


def load_project_style(project_root: str | Path) -> dict[str, Any]:
    raw = _read_json(Path(project_root) / PROJECT_STYLE_REL) or {}
    return validate_style(raw)


def load_video_style_override(video_workspace: str | Path) -> dict[str, Any]:
    raw = _read_json(Path(video_workspace) / VIDEO_STYLE_OVERRIDE_REL) or {}
    return validate_style(raw)


def _merge_style_dict(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Merge ``patch`` into ``base`` for known style keys only.

    - ``None`` in ``patch`` removes that key (e.g. clear ``font_size`` back to renderer default).
    - Empty ``subtitle_background_color`` string removes background.
    """
    merged = dict(base)
    for key, val in patch.items():
        if key not in _STYLE_KEYS:
            continue
        if val is None:
            merged.pop(key, None)
            continue
        if key == "subtitle_background_color" and isinstance(val, str) and not val.strip():
            merged.pop(key, None)
            continue
        merged[key] = val
    return merged


def save_project_style(project_root: str | Path, style: dict[str, Any]) -> Path:
    existing = load_project_style(project_root)
    merged = _merge_style_dict(existing, style)
    cleaned = validate_style(merged)
    path = Path(project_root) / PROJECT_STYLE_REL
    _write_json(path, cleaned)
    return path


def save_video_style_override(video_workspace: str | Path, style: dict[str, Any]) -> Path:
    existing = load_video_style_override(video_workspace)
    merged = _merge_style_dict(existing, style)
    cleaned = validate_style(merged)
    path = Path(video_workspace) / VIDEO_STYLE_OVERRIDE_REL
    _write_json(path, cleaned)
    return path


def resolve_subtitle_style(
    video_workspace: str | Path,
    project_root: str | Path | None = None,
) -> dict[str, Any]:
    """Merge project-global with per-video override. Override wins per field."""
    merged: dict[str, Any] = {}
    if project_root is not None:
        merged.update(load_project_style(project_root))
    merged.update(load_video_style_override(video_workspace))
    return merged


def _hex_to_ass_color(hex_color: str) -> str:
    """Convert ``#RRGGBB``/``#RRGGBBAA`` to ASS ``&HAABBGGRR`` hex literal.

    ASS alpha is *transparency* (00 = opaque, FF = fully transparent). If the input
    provides no alpha, we use 00 (opaque background).
    """
    s = hex_color.strip().lstrip("#")
    if len(s) == 6:
        rr, gg, bb, aa = s[0:2], s[2:4], s[4:6], "00"
    else:  # 8 chars; validated upstream
        rr, gg, bb, input_aa = s[0:2], s[2:4], s[4:6], s[6:8]
        # Input alpha is opacity; ASS alpha is transparency -> invert.
        aa = f"{0xFF - int(input_aa, 16):02X}"
    return f"&H{aa.upper()}{bb.upper()}{gg.upper()}{rr.upper()}"


def hex_to_ffmpeg_color(hex_color: str, *, min_opacity: float = 0.0) -> str:
    """Convert ``#RRGGBB``/``#RRGGBBAA`` to an ffmpeg color literal."""
    s = hex_color.strip().lstrip("#")
    if len(s) == 6:
        rr, gg, bb, opacity = s[0:2], s[2:4], s[4:6], 1.0
    else:
        rr, gg, bb = s[0:2], s[2:4], s[4:6]
        opacity = int(s[6:8], 16) / 255.0
    opacity = max(0.0, min(1.0, max(min_opacity, opacity)))
    return f"0x{rr.upper()}{gg.upper()}{bb.upper()}@{opacity:.3f}"


def style_to_ass_force_style(style: dict[str, Any]) -> str:
    """Return an ffmpeg ``subtitles`` filter ``force_style`` string (may be empty)."""
    parts: list[str] = []
    font = style.get("subtitle_font")
    if isinstance(font, str) and font.strip():
        parts.append(f"FontName={font.strip()}")
    bg = style.get("subtitle_background_color")
    if isinstance(bg, str) and _HEX_RE.match(bg.strip()):
        parts.append(f"BackColour={_hex_to_ass_color(bg)}")
        # BorderStyle=4 draws a filled rectangle behind the subtitle line using BackColour.
        # BorderStyle=3 with Outline=0 often yields no visible box in libass when burning SRT.
        parts.append("BorderStyle=4")
        parts.append("Outline=0")
        parts.append("Shadow=0")
    if "bold" in style:
        parts.append(f"Bold={1 if style.get('bold') else 0}")
    if "italic" in style:
        parts.append(f"Italic={1 if style.get('italic') else 0}")
    align = style.get("align")
    if isinstance(align, str) and align in _ASS_ALIGNMENT:
        parts.append(f"Alignment={_ASS_ALIGNMENT[align]}")
    mv = style.get("margin_v")
    if isinstance(mv, int) and 0 <= mv <= 500:
        parts.append(f"MarginV={mv}")
    fs = style.get("font_size")
    if isinstance(fs, int) and 10 <= fs <= 120:
        parts.append(f"Fontsize={fs}")
    return ",".join(parts)
