"""Application-settings endpoint handlers (language, OpenAI + Azure keys).

Owns app_settings.json read/write plus key masking. Extracted from the server
monolith with behaviour identical to the previous inline handlers.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from desktop.server_shared import _ok
from engine.json_store import write_json_atomic
from engine.runtime_app_settings import (
    merge_azure_speech_settings,
    normalize_azure_speech_settings,
    resolve_azure_speech_configs,
    resolve_openai_translation_model,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _app_settings_path() -> Path:
    return REPO_ROOT / "app_settings.json"


def _load_app_settings() -> dict[str, Any]:
    p = _app_settings_path()
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_app_settings(settings: dict[str, Any]) -> Path:
    p = _app_settings_path()
    write_json_atomic(p, settings)
    return p


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def handle_get_app_settings(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    settings = _load_app_settings()
    azure = normalize_azure_speech_settings(settings.get("azure_speech"))
    safe = {
        "language": settings.get("language", "vi"),
        "has_openai_key": bool(settings.get("openai_api_key")),
        "openai_key_masked": _mask_key(settings.get("openai_api_key", "")),
        "openai_translation_model": str(settings.get("openai_translation_model") or ""),
        "resolved_openai_translation_model": resolve_openai_translation_model(),
        "azure_speech": {
            "fallback_enabled": bool(azure.get("fallback_enabled")),
            "primary": {
                "has_key": bool((azure.get("primary") or {}).get("key")),
                "key_masked": _mask_key((azure.get("primary") or {}).get("key", "")),
                "region": str((azure.get("primary") or {}).get("region") or ""),
            },
            "secondary": {
                "has_key": bool((azure.get("secondary") or {}).get("key")),
                "key_masked": _mask_key((azure.get("secondary") or {}).get("key", "")),
                "region": str((azure.get("secondary") or {}).get("region") or ""),
            },
            "resolved_profiles": [cfg.get("label") for cfg in resolve_azure_speech_configs()],
        },
    }
    return _ok(safe)


def handle_save_app_settings(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    current = _load_app_settings()
    if "language" in body:
        lang = str(body["language"]).strip()
        if lang in ("vi", "en"):
            current["language"] = lang
    if "openai_api_key" in body:
        key = str(body["openai_api_key"]).strip()
        if key:
            current["openai_api_key"] = key
    if "openai_translation_model" in body:
        model = str(body.get("openai_translation_model") or "").strip()
        if model:
            current["openai_translation_model"] = model
        else:
            current.pop("openai_translation_model", None)
    if "azure_speech" in body:
        current["azure_speech"] = merge_azure_speech_settings(
            current.get("azure_speech"),
            body.get("azure_speech"),
        )
    _save_app_settings(current)
    azure = normalize_azure_speech_settings(current.get("azure_speech"))
    return _ok({
        "language": current.get("language", "vi"),
        "has_openai_key": bool(current.get("openai_api_key")),
        "openai_key_masked": _mask_key(current.get("openai_api_key", "")),
        "openai_translation_model": str(current.get("openai_translation_model") or ""),
        "resolved_openai_translation_model": resolve_openai_translation_model(),
        "azure_speech": {
            "fallback_enabled": bool(azure.get("fallback_enabled")),
            "primary": {
                "has_key": bool((azure.get("primary") or {}).get("key")),
                "key_masked": _mask_key((azure.get("primary") or {}).get("key", "")),
                "region": str((azure.get("primary") or {}).get("region") or ""),
            },
            "secondary": {
                "has_key": bool((azure.get("secondary") or {}).get("key")),
                "key_masked": _mask_key((azure.get("secondary") or {}).get("key", "")),
                "region": str((azure.get("secondary") or {}).get("region") or ""),
            },
            "resolved_profiles": [cfg.get("label") for cfg in resolve_azure_speech_configs()],
        },
    })


def handle_check_openai_key(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    settings = _load_app_settings()
    has_key = bool(settings.get("openai_api_key"))
    env_key = bool(os.environ.get("OPENAI_API_KEY"))
    return _ok({"has_key": has_key or env_key})
