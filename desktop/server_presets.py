"""F3 — config preset endpoint handlers (thin adapters over engine.presets)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from desktop.server_shared import _err, _ok, _require
from engine.presets import PresetError, apply_preset, delete_preset, list_presets, save_preset
from engine.project_manager import ProjectError, load_project, set_project_config


def handle_presets_list(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return _ok({"presets": list_presets()})


def handle_presets_save(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "name", "project_root")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    pr = Path(str(body["project_root"])).expanduser().resolve()
    if not pr.is_dir():
        return _err("project_not_found", f"Project directory not found: {pr}")
    try:
        state = load_project(pr)
    except ProjectError as e:
        return _err("project_not_found", str(e))
    tts = {
        "tts_provider": state.config.tts_provider,
        "tts_voice": state.config.tts_voice,
        "mix_mode": state.config.mix_mode,
        "translate_backend": state.config.translate_backend,
    }
    try:
        preset = save_preset(str(body["name"]), tts=tts, source_root=pr)
    except (PresetError, OSError, ValueError) as e:
        return _err("preset_save_failed", str(e))
    return _ok({"preset": preset, "presets": list_presets()})


def handle_presets_apply(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "preset_id", "project_root")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    pr = Path(str(body["project_root"])).expanduser().resolve()
    if not pr.is_dir():
        return _err("project_not_found", f"Project directory not found: {pr}")
    try:
        res = apply_preset(str(body["preset_id"]), pr)
        if res.get("tts"):
            set_project_config(pr, res["tts"])
    except (PresetError, ProjectError, OSError, ValueError) as e:
        return _err("preset_apply_failed", str(e))
    return _ok(res)


def handle_presets_delete(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "preset_id")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    try:
        delete_preset(str(body["preset_id"]))
    except (PresetError, OSError) as e:
        return _err("preset_delete_failed", str(e))
    return _ok({"presets": list_presets()})
