"""Shared runtime app settings helpers.

This module is intentionally lightweight so engine code can read persisted
application-wide settings (for example Azure Speech credentials) without
depending on the desktop server package.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_OPENAI_TRANSLATION_MODEL = "gpt-5.4"


def app_settings_path() -> Path:
    return Path(__file__).resolve().parents[1] / "app_settings.json"


def load_runtime_app_settings() -> dict[str, Any]:
    path = app_settings_path()
    if not path.is_file():
        return {}
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return body if isinstance(body, dict) else {}


def normalize_openai_translation_model(value: Any) -> str:
    return str(value or "").strip()


def resolve_openai_translation_model(*, default: str = DEFAULT_OPENAI_TRANSLATION_MODEL) -> str:
    settings = load_runtime_app_settings()
    saved = normalize_openai_translation_model(settings.get("openai_translation_model"))
    if saved:
        return saved
    env = str(os.environ.get("OPENAI_TRANSLATION_MODEL") or "").strip()
    if env:
        return env
    return default


def normalize_azure_speech_settings(raw: Any) -> dict[str, Any]:
    data = raw if isinstance(raw, dict) else {}
    out: dict[str, Any] = {}
    for slot in ("primary", "secondary"):
        section = data.get(slot)
        section_dict = section if isinstance(section, dict) else {}
        cleaned: dict[str, str] = {}
        key = str(section_dict.get("key") or "").strip()
        region = str(section_dict.get("region") or "").strip()
        if key:
            cleaned["key"] = key
        if region:
            cleaned["region"] = region
        out[slot] = cleaned
    secondary_ready = bool(
        out["secondary"].get("key") and out["secondary"].get("region")
    )
    fallback_default = secondary_ready
    out["fallback_enabled"] = bool(data.get("fallback_enabled", fallback_default))
    return out


def merge_azure_speech_settings(current_raw: Any, patch_raw: Any) -> dict[str, Any]:
    current = normalize_azure_speech_settings(current_raw)
    patch = patch_raw if isinstance(patch_raw, dict) else {}
    if "fallback_enabled" in patch:
        current["fallback_enabled"] = bool(patch.get("fallback_enabled"))
    for slot in ("primary", "secondary"):
        if slot not in patch or not isinstance(patch.get(slot), dict):
            continue
        slot_patch = patch[slot]
        cleaned = dict(current.get(slot) or {})
        if "key" in slot_patch:
            key = str(slot_patch.get("key") or "").strip()
            if key:
                cleaned["key"] = key
            else:
                cleaned.pop("key", None)
        if "region" in slot_patch:
            region = str(slot_patch.get("region") or "").strip()
            if region:
                cleaned["region"] = region
            else:
                cleaned.pop("region", None)
        current[slot] = cleaned
    return normalize_azure_speech_settings(current)


def resolve_azure_speech_configs() -> list[dict[str, str]]:
    settings = load_runtime_app_settings()
    azure = normalize_azure_speech_settings(settings.get("azure_speech"))
    seen: set[tuple[str, str]] = set()
    configs: list[dict[str, str]] = []

    def add(slot: str, key: str, region: str, *, source: str) -> None:
        clean_key = str(key or "").strip()
        clean_region = str(region or "").strip()
        if not clean_key or not clean_region:
            return
        dedupe_key = (clean_key, clean_region.casefold())
        if dedupe_key in seen:
            return
        seen.add(dedupe_key)
        configs.append(
            {
                "key": clean_key,
                "region": clean_region,
                "slot": slot,
                "source": source,
                "label": f"{source}:{slot}",
            }
        )

    primary = azure.get("primary") if isinstance(azure.get("primary"), dict) else {}
    secondary = azure.get("secondary") if isinstance(azure.get("secondary"), dict) else {}
    add("primary", str(primary.get("key") or ""), str(primary.get("region") or ""), source="app")
    if azure.get("fallback_enabled"):
        add(
            "secondary",
            str(secondary.get("key") or ""),
            str(secondary.get("region") or ""),
            source="app",
        )

    add(
        "primary",
        os.environ.get("AZURE_SPEECH_KEY") or "",
        os.environ.get("AZURE_SPEECH_REGION") or "",
        source="env",
    )
    secondary_env_enabled = bool(azure.get("fallback_enabled"))
    if secondary_env_enabled:
        add(
            "secondary",
            os.environ.get("AZURE_SPEECH_KEY_SECONDARY")
            or os.environ.get("AZURE_SPEECH_KEY_2")
            or "",
            os.environ.get("AZURE_SPEECH_REGION_SECONDARY")
            or os.environ.get("AZURE_SPEECH_REGION_2")
            or "",
            source="env",
        )

    return configs
