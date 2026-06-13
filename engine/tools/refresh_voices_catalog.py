"""Refresh engine/voices_catalog.json from the official edge-tts voice list."""
from __future__ import annotations

from engine.json_store import write_json_atomic
import argparse
import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = REPO_ROOT / "engine" / "voices_catalog.json"

DEFAULT_ENABLED_VOICES: dict[str, set[str] | None] = {
    "vi-VN": None,
    "en-US": {
        "en-US-JennyNeural",
        "en-US-AriaNeural",
        "en-US-GuyNeural",
        "en-US-AnaNeural",
        "en-US-AvaNeural",
        "en-US-EmmaNeural",
        "en-US-MichelleNeural",
        "en-US-AndrewNeural",
        "en-US-BrianNeural",
        "en-US-ChristopherNeural",
    },
    "en-GB": {
        "en-GB-SoniaNeural",
        "en-GB-RyanNeural",
        "en-GB-LibbyNeural",
    },
    "zh-CN": {
        "zh-CN-XiaoxiaoNeural",
        "zh-CN-YunxiNeural",
        "zh-CN-YunyangNeural",
        "zh-CN-XiaoyiNeural",
    },
    "ja-JP": {
        "ja-JP-NanamiNeural",
        "ja-JP-KeitaNeural",
    },
    "ko-KR": {
        "ko-KR-SunHiNeural",
        "ko-KR-InJoonNeural",
    },
}

LOCALE_LABELS_VI = {
    "vi-VN": "Tiếng Việt",
    "en-US": "Tiếng Anh (Mỹ)",
    "en-GB": "Tiếng Anh (Anh)",
    "zh-CN": "Tiếng Trung",
    "ja-JP": "Tiếng Nhật",
    "ko-KR": "Tiếng Hàn",
}

LOCALE_LABELS_EN = {
    "vi-VN": "Vietnamese",
    "en-US": "English (US)",
    "en-GB": "English (UK)",
    "zh-CN": "Chinese (Mainland)",
    "ja-JP": "Japanese",
    "ko-KR": "Korean",
}

GENDER_LABELS_VI = {
    "female": "Nữ",
    "male": "Nam",
}

GENDER_LABELS_EN = {
    "female": "Female",
    "male": "Male",
}

KNOWN_SHORT_NAMES = {
    "vi-VN-HoaiMyNeural": "Hoài My",
    "vi-VN-NamMinhNeural": "Nam Minh",
    "en-US-JennyNeural": "Jenny",
    "en-US-AriaNeural": "Aria",
    "en-US-GuyNeural": "Guy",
    "en-US-DavisNeural": "Davis",
    "en-US-TonyNeural": "Tony",
    "en-US-NancyNeural": "Nancy",
    "en-US-AnaNeural": "Ana",
    "en-US-AvaNeural": "Ava",
    "en-US-EmmaNeural": "Emma",
    "en-US-MichelleNeural": "Michelle",
    "en-US-AndrewNeural": "Andrew",
    "en-US-BrianNeural": "Brian",
    "en-US-ChristopherNeural": "Christopher",
    "en-GB-SoniaNeural": "Sonia",
    "en-GB-RyanNeural": "Ryan",
    "en-GB-LibbyNeural": "Libby",
    "zh-CN-XiaoxiaoNeural": "Xiaoxiao",
    "zh-CN-YunxiNeural": "Yunxi",
    "zh-CN-YunyangNeural": "Yunyang",
    "zh-CN-XiaoyiNeural": "Xiaoyi",
    "ja-JP-NanamiNeural": "Nanami",
    "ja-JP-KeitaNeural": "Keita",
    "ko-KR-SunHiNeural": "SunHi",
    "ko-KR-InJoonNeural": "InJoon",
}

_CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z])(?=[A-Z])")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--catalog",
        default=str(DEFAULT_CATALOG_PATH),
        help="Path to voices_catalog.json. Defaults to engine/voices_catalog.json.",
    )
    p.add_argument(
        "--locales",
        default="",
        help="Optional comma-separated locale filter, e.g. vi-VN,en-US,zh-CN.",
    )
    return p.parse_args(argv)


def _load_existing_catalog(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"version": 1, "voices": []}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "voices": []}
    return raw if isinstance(raw, dict) else {"version": 1, "voices": []}


def _existing_voice_map(raw: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for item in raw.get("voices") or []:
        if not isinstance(item, dict):
            continue
        provider = str(item.get("provider") or "").strip()
        voice_id = str(item.get("voice_id") or "").strip()
        if provider and voice_id:
            out[(provider, voice_id)] = dict(item)
    return out


async def _list_edge_voices() -> list[dict[str, Any]]:
    import edge_tts

    voices = await edge_tts.list_voices()
    return [v for v in voices if isinstance(v, dict)]


def _split_locales(raw: str) -> set[str] | None:
    locales = {part.strip() for part in raw.split(",") if part.strip()}
    return locales or None


def _voice_short_name(voice_id: str) -> str:
    if voice_id in KNOWN_SHORT_NAMES:
        return KNOWN_SHORT_NAMES[voice_id]
    tail = voice_id.split("-")[-1]
    if tail.endswith("Neural"):
        tail = tail[:-6]
    spaced = _CAMEL_BOUNDARY_RE.sub(" ", tail).strip()
    return spaced or voice_id


def _style_tags(edge_entry: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    voice_tag = edge_entry.get("VoiceTag")
    if isinstance(voice_tag, dict):
        for key in ("ContentCategories", "VoicePersonalities"):
            raw = voice_tag.get(key)
            if isinstance(raw, list):
                tags.extend(str(item).strip().lower() for item in raw if str(item).strip())
            elif isinstance(raw, str) and raw.strip():
                tags.append(raw.strip().lower())
    raw_styles = edge_entry.get("StyleList")
    if isinstance(raw_styles, list):
        tags.extend(str(item).strip().lower() for item in raw_styles if str(item).strip())
    seen: set[str] = set()
    out: list[str] = []
    for tag in tags:
        key = tag.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(tag)
    return out or ["neutral"]


def _default_enabled(locale: str, voice_id: str) -> bool:
    rule = DEFAULT_ENABLED_VOICES.get(locale)
    if rule is None:
        return locale in DEFAULT_ENABLED_VOICES
    return voice_id in rule


def _locale_label(locale: str) -> tuple[str, str]:
    return LOCALE_LABELS_VI.get(locale, locale), LOCALE_LABELS_EN.get(locale, locale)


def _gender_labels(gender: str) -> tuple[str, str]:
    key = gender.lower()
    return GENDER_LABELS_VI.get(key, gender.title()), GENDER_LABELS_EN.get(key, gender.title())


def _resolved_enabled(
    *,
    existing: dict[str, Any] | None,
    default_enabled: bool,
    refresh_generated_defaults: bool,
) -> bool:
    if not existing or "enabled" not in existing:
        return default_enabled
    if refresh_generated_defaults and "default_enabled" not in existing:
        return default_enabled
    return existing.get("enabled") is not False


def _edge_catalog_entry(
    edge_entry: dict[str, Any],
    existing: dict[str, Any] | None,
    *,
    refresh_generated_defaults: bool,
) -> dict[str, Any]:
    voice_id = str(edge_entry.get("ShortName") or "").strip()
    locale = str(edge_entry.get("Locale") or "").strip()
    gender = str(edge_entry.get("Gender") or "").strip().lower()
    short_name = _voice_short_name(voice_id)
    locale_label_vi, locale_label_en = _locale_label(locale)
    gender_label_vi, gender_label_en = _gender_labels(gender)
    default_enabled = _default_enabled(locale, voice_id)
    enabled = _resolved_enabled(
        existing=existing,
        default_enabled=default_enabled,
        refresh_generated_defaults=refresh_generated_defaults,
    )
    first_style = _style_tags(edge_entry)[0]
    entry = {
        "provider": "edge_tts",
        "voice_id": voice_id,
        "label": f"{locale_label_en} - {short_name} ({gender_label_en}, {first_style})",
        "locale": locale,
        "locale_label": locale_label_vi,
        "locale_label_en": locale_label_en,
        "gender": gender,
        "gender_label": gender_label_vi,
        "gender_label_en": gender_label_en,
        "short_name": short_name,
        "style_tags": _style_tags(edge_entry),
        "default_enabled": default_enabled,
        "enabled": enabled,
    }
    return {**entry, **{k: v for k, v in (existing or {}).items() if k not in entry}, "enabled": enabled}


def _enrich_existing_entry(entry: dict[str, Any]) -> dict[str, Any]:
    voice_id = str(entry.get("voice_id") or "").strip()
    locale = str(entry.get("locale") or "").strip()
    gender = str(entry.get("gender") or "").strip().lower()
    out = dict(entry)
    if locale:
        locale_label_vi, locale_label_en = _locale_label(locale)
        out.setdefault("locale_label", locale_label_vi)
        out.setdefault("locale_label_en", locale_label_en)
    if gender:
        gender_label_vi, gender_label_en = _gender_labels(gender)
        out.setdefault("gender_label", gender_label_vi)
        out.setdefault("gender_label_en", gender_label_en)
    if voice_id:
        out.setdefault("short_name", _voice_short_name(voice_id))
    if not isinstance(out.get("style_tags"), list):
        out["style_tags"] = ["neutral"]
    return out


def _sort_key(entry: dict[str, Any]) -> tuple[str, int, str, str]:
    gender_order = {"female": 0, "male": 1}
    return (
        str(entry.get("locale") or ""),
        gender_order.get(str(entry.get("gender") or "").lower(), 9),
        str(entry.get("provider") or ""),
        str(entry.get("voice_id") or ""),
    )


def refresh_catalog(path: Path, locales: set[str] | None = None) -> dict[str, Any]:
    raw = _load_existing_catalog(path)
    existing = _existing_voice_map(raw)
    selected_locales = locales
    refresh_generated_defaults = raw.get("source") == "edge_tts.list_voices"
    fetched = asyncio.run(_list_edge_voices())
    refreshed: dict[tuple[str, str], dict[str, Any]] = {}

    for edge_entry in fetched:
        voice_id = str(edge_entry.get("ShortName") or "").strip()
        locale = str(edge_entry.get("Locale") or "").strip()
        if not voice_id or not locale:
            continue
        if selected_locales and locale not in selected_locales:
            continue
        key = ("edge_tts", voice_id)
        refreshed[key] = _edge_catalog_entry(
            edge_entry,
            existing.get(key),
            refresh_generated_defaults=refresh_generated_defaults,
        )

    merged = dict(existing)
    merged.update(refreshed)
    voices = [_enrich_existing_entry(item) for item in merged.values()]
    voices.sort(key=_sort_key)

    enabled_count = sum(1 for item in voices if item.get("enabled") is not False)
    out = {
        "version": int(raw.get("version") or 1),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "edge_tts.list_voices",
        "notes": (
            "Generated by python -m engine.tools.refresh_voices_catalog. "
            "Existing enabled flags are preserved; new Edge voices use the default whitelist."
        ),
        "enabled_count": enabled_count,
        "voices": voices,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, out)
    return out


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    path = Path(ns.catalog).expanduser().resolve()
    catalog = refresh_catalog(path, _split_locales(ns.locales))
    total = len(catalog.get("voices") or [])
    enabled = int(catalog.get("enabled_count") or 0)
    print(f"Refreshed {path}: {total} voices ({enabled} enabled)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
