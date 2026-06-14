"""F3 — reusable config presets (voice/mix + branding + transforms).

A preset captures everything you'd want to reapply across projects: the shared
TTS config (provider/voice/mix) plus the full branding/transform render template
(logo/intro/outro files + aspect + trim + anti-dedup transforms). Presets live
under ``<repo>/Presets/<id>/`` and reuse engine.render_settings for the render
template (same layout as a project root: ``video_state.json`` + ``assets/``).
"""
from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path
from typing import Any

from engine.render_settings import load_render_settings, save_render_settings

REPO_ROOT = Path(__file__).resolve().parents[1]
PRESETS_DIR = REPO_ROOT / "Presets"
_TTS_KEYS = ("tts_provider", "tts_voice", "mix_mode", "translate_backend")
_ASSET_SUBDIRS = ("render_logo", "render_intro", "render_outro", "render_background")


class PresetError(ValueError):
    pass


def _safe_id(name: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", str(name).strip()).strip("-._")
    return (stem or "preset")[:80]


def _clean_tts(tts: Any) -> dict[str, str]:
    d = tts if isinstance(tts, dict) else {}
    return {k: str(d.get(k) or "").strip() for k in _TTS_KEYS if str(d.get(k) or "").strip()}


def list_presets() -> list[dict[str, Any]]:
    if not PRESETS_DIR.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for d in sorted(PRESETS_DIR.iterdir()):
        meta = d / "preset.json"
        if not (d.is_dir() and meta.is_file()):
            continue
        try:
            body = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        out.append({
            "id": d.name,
            "name": str(body.get("name") or d.name),
            "tts": _clean_tts(body.get("tts")),
            "render": load_render_settings(d) or {},
            "created_at": body.get("created_at"),
        })
    return out


def save_preset(name: str, *, tts: dict[str, Any], source_root: str | Path) -> dict[str, Any]:
    nm = str(name or "").strip()
    if not nm:
        raise PresetError("Preset name is empty.")
    src = Path(source_root).expanduser().resolve()
    pid = _safe_id(nm)
    pdir = PRESETS_DIR / pid
    shutil.rmtree(pdir, ignore_errors=True)
    pdir.mkdir(parents=True, exist_ok=True)

    # Copy branding asset files from the source (project root) into the preset.
    for sub in _ASSET_SUBDIRS:
        s = src / "assets" / sub
        if s.is_dir():
            shutil.copytree(s, pdir / "assets" / sub)
    # Copy the render template (logo/outro/trim/transform settings).
    save_render_settings(pdir, load_render_settings(src) or {"aspect_ratio": "source"})

    (pdir / "preset.json").write_text(
        json.dumps({"name": nm, "tts": _clean_tts(tts), "created_at": time.time()}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"id": pid, "name": nm, "tts": _clean_tts(tts), "render": load_render_settings(pdir) or {}}


def apply_preset(preset_id: str, target_root: str | Path) -> dict[str, Any]:
    pid = _safe_id(preset_id)
    pdir = PRESETS_DIR / pid
    meta = pdir / "preset.json"
    if not meta.is_file():
        raise PresetError(f"Preset not found: {preset_id}")
    target = Path(target_root).expanduser().resolve()
    if not target.is_dir():
        raise PresetError(f"Target not found: {target}")

    # Copy preset asset files into the target (replacing any existing branding).
    for sub in _ASSET_SUBDIRS:
        dst = target / "assets" / sub
        shutil.rmtree(dst, ignore_errors=True)
        s = pdir / "assets" / sub
        if s.is_dir():
            shutil.copytree(s, dst)
    settings = load_render_settings(pdir) or {"aspect_ratio": "source"}
    save_render_settings(target, settings)

    body = json.loads(meta.read_text(encoding="utf-8"))
    return {"tts": _clean_tts(body.get("tts")), "render": load_render_settings(target) or {}}


def delete_preset(preset_id: str) -> None:
    pdir = PRESETS_DIR / _safe_id(preset_id)
    if pdir.is_dir():
        shutil.rmtree(pdir, ignore_errors=True)
