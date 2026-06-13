"""Voice-catalog and system-font endpoint handlers.

Owns the voices_catalog.json read/write helpers, system-font enumeration, and
the /api/list-voices, /api/voices/toggle, /api/voices/refresh and
/api/list-system-fonts handlers. Extracted from the server monolith with
behaviour identical to the previous inline code. (The TTS *preview* endpoint and
its audio cache stay in server.py — they do not share these helpers.)
"""
from __future__ import annotations

import json
import os
import re
import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any

from desktop.server_shared import _err, _ok
from engine.json_store import write_json_atomic

REPO_ROOT = Path(__file__).resolve().parents[1]

_FONT_EXTS = {".ttf", ".otf", ".ttc", ".otc"}
_FONT_STYLE_SUFFIXES = (
    "regular",
    "bold",
    "italic",
    "medium",
    "light",
    "semibold",
    "demibold",
    "black",
    "thin",
    "oblique",
    "condensed",
)


def _voices_catalog_path() -> Path:
    return REPO_ROOT / "engine" / "voices_catalog.json"


def _load_voice_catalog() -> list[dict[str, Any]]:
    path = _voices_catalog_path()
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    voices = raw.get("voices") if isinstance(raw, dict) else None
    if not isinstance(voices, list):
        return []
    out: list[dict[str, Any]] = []
    for entry in voices:
        if isinstance(entry, dict):
            out.append(dict(entry))
    return out


def _load_voice_catalog_raw() -> dict[str, Any]:
    path = _voices_catalog_path()
    if not path.is_file():
        return {"version": 1, "voices": []}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "voices": []}
    return raw if isinstance(raw, dict) else {"version": 1, "voices": []}


def _write_voice_catalog_raw(raw: dict[str, Any]) -> None:
    path = _voices_catalog_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, raw)


def _font_search_roots() -> list[Path]:
    home = Path.home()
    if sys.platform.startswith("win"):
        windir = Path(os.environ.get("WINDIR") or "C:/Windows")
        return [windir / "Fonts"]
    if sys.platform == "darwin":
        return [
            Path("/System/Library/Fonts"),
            Path("/Library/Fonts"),
            home / "Library" / "Fonts",
        ]
    return [
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
        home / ".fonts",
        home / ".local" / "share" / "fonts",
    ]


def _guess_font_family(path: Path) -> str:
    tokens = re.split(r"[-_\s]+", path.stem)
    while tokens and tokens[-1].lower() in _FONT_STYLE_SUFFIXES:
        tokens.pop()
    family = " ".join(tokens).strip()
    return family or path.stem


def _list_system_fonts() -> list[dict[str, str]]:
    seen: dict[str, dict[str, str]] = {}
    for root in _font_search_roots():
        if not root.exists():
            continue
        iterator = root.rglob("*") if root.is_dir() else []
        try:
            for path in iterator:
                if not path.is_file() or path.suffix.lower() not in _FONT_EXTS:
                    continue
                family = _guess_font_family(path)
                key = family.casefold()
                if key in seen:
                    continue
                seen[key] = {
                    "family": family,
                    "file": str(path.resolve()),
                }
        except OSError:
            continue
    return sorted(seen.values(), key=lambda item: item["family"].casefold())


def handle_list_system_fonts(_body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return _ok({"fonts": _list_system_fonts()})


def handle_list_voices(_body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return _ok({"voices": _load_voice_catalog()})


def handle_toggle_voice(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    voice_id = str(body.get("voice_id") or "").strip()
    provider = str(body.get("provider") or "edge_tts").strip() or "edge_tts"
    if not voice_id:
        return _err("missing_field", "Missing required field: voice_id")
    enabled = bool(body.get("enabled"))

    raw = _load_voice_catalog_raw()
    voices = raw.get("voices")
    if not isinstance(voices, list):
        voices = []
        raw["voices"] = voices

    found = False
    for item in voices:
        if not isinstance(item, dict):
            continue
        if str(item.get("provider") or "") == provider and str(item.get("voice_id") or "") == voice_id:
            item["enabled"] = enabled
            found = True
            break
    if not found:
        return _err("voice_not_found", f"Voice not found: {provider}/{voice_id}", HTTPStatus.NOT_FOUND)
    raw["enabled_count"] = sum(
        1 for item in voices if isinstance(item, dict) and item.get("enabled") is not False
    )
    _write_voice_catalog_raw(raw)
    return _ok({"voices": _load_voice_catalog()})


def handle_refresh_voices(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    locales_raw = str(body.get("locales") or "").strip()
    locales = {part.strip() for part in locales_raw.split(",") if part.strip()} or None
    try:
        from engine.tools.refresh_voices_catalog import refresh_catalog

        refresh_catalog(_voices_catalog_path(), locales)
    except Exception as e:  # noqa: BLE001
        return _err("voices_refresh_failed", str(e), HTTPStatus.INTERNAL_SERVER_ERROR)
    return _ok({"voices": _load_voice_catalog()})
