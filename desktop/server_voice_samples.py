"""Voice-sample (speaker reference) endpoint handlers for XTTS cloning.

Thin request/response adapters over engine.voice_samples. The Review screen
uploads a clip (local path from the file picker), and the cue's clone voice is
the absolute path of the normalized sample.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from desktop.server_shared import _err, _ok, _require, require_job_workspace
from engine.voice_samples import (
    VoiceSampleError,
    import_voice_sample,
    list_voice_samples,
    remove_voice_sample,
)


def handle_list_voice_samples(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    jw, error = require_job_workspace(body)
    if error:
        return error
    return _ok({"samples": list_voice_samples(jw)})


def handle_upload_voice_sample(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    missing = _require(body, "job_workspace", "sample_path")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    jw = Path(str(body["job_workspace"])).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")
    try:
        sample = import_voice_sample(jw, str(body["sample_path"]))
    except (VoiceSampleError, OSError, ValueError) as e:
        return _err("invalid_voice_sample", str(e))
    return _ok({"sample": sample, "samples": list_voice_samples(jw)})


def handle_remove_voice_sample(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    jw, error = require_job_workspace(body)
    if error:
        return error
    remove_voice_sample(jw, str(body.get("id") or ""))
    return _ok({"samples": list_voice_samples(jw)})
