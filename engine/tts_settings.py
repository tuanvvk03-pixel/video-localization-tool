"""TTS/audio settings persistence — mirrors ``engine.subtitle_style`` layout.

Stores UI-editable TTS + audio-mix preferences so the desktop app can remember
them per project and per video without reaching into ``run_job`` CLI flags.

Schema (all fields optional — absent keys mean "inherit / backend default"):

    {
      "tts_provider": "edge_tts" | "azure_tts",
      "tts_voice": "<string>",           # e.g. "vi-VN-HoaiMyNeural"
      "speed_multiplier": <float, 0.5..2.0>,
      "tts_rate": <int, -50..+50>,       # percent offset passed to TTS backend
      "tts_pitch": <int, -50..+50>,      # percent offset passed to TTS backend
      "mix_mode": "replace_original_speech" | "duck_original_speech",
      "mix_duck_gain_db": <float, -30.0..0.0>  # original-speech level when ducking
    }

Storage locations (separate from ``style_override.json`` to keep semantics clean):
- Project-global: ``<project_root>/style/tts_settings.json``
- Per-video override: ``<video_workspace>/tts_override.json``

``resolve_tts_settings`` merges override onto global (override wins per field).
Callers are expected to pass the resolved dict through to ``run_job`` argv when
kicking off a pipeline — this module does not mutate run state itself.
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import json
from pathlib import Path
from typing import Any

PROJECT_TTS_REL = Path("style") / "tts_settings.json"
VIDEO_TTS_OVERRIDE_REL = Path("tts_override.json")

_PROVIDERS = {"edge_tts", "azure_tts"}
_MIX_MODES = {"replace_original_speech", "duck_original_speech"}
_RATE_MIN, _RATE_MAX = -50, 50
_PITCH_MIN, _PITCH_MAX = -50, 50
_SPEED_MIN, _SPEED_MAX = 0.5, 2.0
_MIX_DUCK_GAIN_MIN_DB, _MIX_DUCK_GAIN_MAX_DB = -30.0, 0.0


class TTSSettingsError(ValueError):
    pass


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise TTSSettingsError(f"Invalid JSON at {path}: {e}") from e
    if not isinstance(body, dict):
        raise TTSSettingsError(f"TTS settings file must be a JSON object: {path}")
    return body


def _write_json(path: Path, body: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, body)


def _coerce_int(value: Any, *, lo: int, hi: int, field: str) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError) as e:
        raise TTSSettingsError(f"{field} must be an integer") from e
    if n < lo or n > hi:
        raise TTSSettingsError(f"{field} must be within [{lo}, {hi}]")
    return n


def _coerce_float(value: Any, *, lo: float, hi: float, field: str) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError) as e:
        raise TTSSettingsError(f"{field} must be a number") from e
    if n < lo or n > hi:
        raise TTSSettingsError(f"{field} must be within [{lo}, {hi}]")
    return n


def speed_multiplier_to_tts_rate(value: float) -> int:
    rate = round((float(value) - 1.0) * 100.0)
    return max(_RATE_MIN, min(_RATE_MAX, int(rate)))


def tts_rate_to_speed_multiplier(value: int) -> float:
    speed = 1.0 + (int(value) / 100.0)
    speed = max(_SPEED_MIN, min(_SPEED_MAX, speed))
    return round(speed, 2)


def tts_rate_to_provider_arg(value: int) -> str:
    rate = int(value)
    return f"{rate:+d}%"


def validate_settings(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a cleaned settings dict. Unknown keys are dropped silently."""
    out: dict[str, Any] = {}

    provider = raw.get("tts_provider")
    if provider is not None:
        if not isinstance(provider, str) or provider.strip() not in _PROVIDERS:
            raise TTSSettingsError(
                f"tts_provider must be one of {sorted(_PROVIDERS)}"
            )
        out["tts_provider"] = provider.strip()

    voice = raw.get("tts_voice")
    if voice is not None:
        if not isinstance(voice, str) or not voice.strip():
            raise TTSSettingsError("tts_voice must be a non-empty string")
        out["tts_voice"] = voice.strip()

    if "speed_multiplier" in raw and raw["speed_multiplier"] is not None:
        speed = _coerce_float(
            raw["speed_multiplier"],
            lo=_SPEED_MIN,
            hi=_SPEED_MAX,
            field="speed_multiplier",
        )
        out["speed_multiplier"] = round(speed, 2)
        out["tts_rate"] = speed_multiplier_to_tts_rate(speed)
    elif "tts_rate" in raw and raw["tts_rate"] is not None:
        rate = _coerce_int(
            raw["tts_rate"], lo=_RATE_MIN, hi=_RATE_MAX, field="tts_rate"
        )
        out["tts_rate"] = rate
        out["speed_multiplier"] = tts_rate_to_speed_multiplier(rate)

    if "tts_pitch" in raw and raw["tts_pitch"] is not None:
        out["tts_pitch"] = _coerce_int(
            raw["tts_pitch"], lo=_PITCH_MIN, hi=_PITCH_MAX, field="tts_pitch"
        )

    mix = raw.get("mix_mode")
    if mix is not None:
        if not isinstance(mix, str) or mix.strip() not in _MIX_MODES:
            raise TTSSettingsError(
                f"mix_mode must be one of {sorted(_MIX_MODES)}"
            )
        out["mix_mode"] = mix.strip()

    if "mix_duck_gain_db" in raw and raw["mix_duck_gain_db"] is not None:
        gain = _coerce_float(
            raw["mix_duck_gain_db"],
            lo=_MIX_DUCK_GAIN_MIN_DB,
            hi=_MIX_DUCK_GAIN_MAX_DB,
            field="mix_duck_gain_db",
        )
        out["mix_duck_gain_db"] = round(gain, 2)

    return out


def load_project_tts_settings(project_root: str | Path) -> dict[str, Any]:
    raw = _read_json(Path(project_root) / PROJECT_TTS_REL) or {}
    return validate_settings(raw)


def load_video_tts_override(video_workspace: str | Path) -> dict[str, Any]:
    raw = _read_json(Path(video_workspace) / VIDEO_TTS_OVERRIDE_REL) or {}
    return validate_settings(raw)


def save_project_tts_settings(project_root: str | Path, settings: dict[str, Any]) -> Path:
    cleaned = validate_settings(settings)
    path = Path(project_root) / PROJECT_TTS_REL
    _write_json(path, cleaned)
    return path


def save_video_tts_override(video_workspace: str | Path, settings: dict[str, Any]) -> Path:
    cleaned = validate_settings(settings)
    path = Path(video_workspace) / VIDEO_TTS_OVERRIDE_REL
    _write_json(path, cleaned)
    return path


def resolve_tts_settings(
    video_workspace: str | Path,
    project_root: str | Path | None = None,
) -> dict[str, Any]:
    """Merge project-global with per-video override. Override wins per field."""
    merged: dict[str, Any] = {}
    if project_root is not None:
        merged.update(load_project_tts_settings(project_root))
    merged.update(load_video_tts_override(video_workspace))
    return merged
