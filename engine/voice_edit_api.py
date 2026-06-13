from __future__ import annotations

from engine.json_store import write_json_atomic
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional

from engine.input_provenance import fingerprint_file
from engine.srt_cues import SRTCue, parse_srt_cues
from engine.subtitle_text import (
    copy_subtitle_artifact,
    read_subtitle_file,
    write_subtitle_file_utf8,
)


class VoiceEditError(RuntimeError):
    pass


VoiceSourceMode = Literal["edited_voice", "translated_voice", "missing"]


@dataclass(frozen=True)
class VoiceSourceInfo:
    mode: VoiceSourceMode
    path: Optional[Path]


EDITED_VOICE_REL = Path("artifacts") / "edit" / "edited_voice.srt"
EDIT_MANIFEST_REL = Path("artifacts") / "edit" / "edit_manifest.json"
TRANSLATED_VOICE_REL = Path("artifacts") / "translate" / "translated_voice.srt"
VOICE_OVERRIDES_REL = Path("artifacts") / "edit" / "voice_overrides.json"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _write_json(path: Path, body: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, body)


# ---- per-cue voice overrides (multi-voice) ---------------------------------
# Sidecar mapping a cue index -> {voice_id, rate, provider} so a single cue can
# use a different voice than the job default. Read by run_tts_stage; written from
# the Review screen. Empty/blank entries are dropped so "use shared voice" leaves
# no record.

def _clean_voice_overrides(raw: Any) -> dict[str, dict[str, str]]:
    """Validate a raw override map into ``{str(index): {voice_id, rate, provider}}``.

    Keeps only entries with at least one non-empty field; coerces values to str
    and indices to canonical base-10 strings. Anything malformed is skipped.
    """
    out: dict[str, dict[str, str]] = {}
    if not isinstance(raw, dict):
        return out
    for key, value in raw.items():
        try:
            idx = int(str(key).strip())
        except (TypeError, ValueError):
            continue
        if idx < 0 or not isinstance(value, dict):
            continue
        entry: dict[str, str] = {}
        for field in ("voice_id", "rate", "provider"):
            v = str(value.get(field) or "").strip()
            if v:
                entry[field] = v
        if entry:
            out[str(idx)] = entry
    return out


def load_voice_overrides(job_workspace: str | Path) -> dict[str, dict[str, str]]:
    """Return the cleaned per-cue voice overrides (string indices)."""
    jw = Path(job_workspace)
    return _clean_voice_overrides(_load_json(jw / VOICE_OVERRIDES_REL))


def load_voice_overrides_indexed(job_workspace: str | Path) -> dict[int, dict[str, str]]:
    """Same as ``load_voice_overrides`` but keyed by int index for the TTS stage."""
    return {int(k): v for k, v in load_voice_overrides(job_workspace).items()}


def save_voice_overrides(job_workspace: str | Path, raw: Any) -> dict[str, dict[str, str]]:
    """Write the cleaned overrides to the canonical sidecar; return the cleaned map."""
    jw = Path(job_workspace)
    cleaned = _clean_voice_overrides(raw)
    _write_json(jw / VOICE_OVERRIDES_REL, cleaned)
    return cleaned


def _merge_job_state(job_workspace: Path, updates: dict[str, Any]) -> None:
    p = job_workspace / "job_state.json"
    base = _load_json(p) or {}
    base.update(updates)
    _write_json(p, base)


def _merge_video_state(job_workspace: Path, updates: dict[str, Any]) -> None:
    p = job_workspace / "video_state.json"
    base = _load_json(p) or {}
    payload = dict(updates)
    inc_ap = payload.pop("artifact_paths", None)
    base.update(payload)
    if inc_ap is not None:
        merged = dict(base.get("artifact_paths") or {})
        merged.update(dict(inc_ap))
        base["artifact_paths"] = merged
    _write_json(p, base)


@dataclass(frozen=True)
class VoiceEditStatus:
    """Snapshot of voice-edit progress for UI consumption."""

    voice_edit_status: str  # "not_started" | "voice_edit_pending" | "voice_edited"
    voice_edited: bool
    edited_voice_path: Optional[Path]
    translated_voice_path: Optional[Path]
    edit_manifest_path: Optional[Path]
    source_mode: VoiceSourceMode


def get_voice_edit_status(job_workspace: str | Path) -> VoiceEditStatus:
    """Aggregate status from video_state.json/job_state.json + filesystem for UI."""
    jw = Path(job_workspace).expanduser().resolve()
    vs = _load_json(jw / "video_state.json") or {}
    js = _load_json(jw / "job_state.json") or {}

    edited = jw / EDITED_VOICE_REL
    translated_voice = jw / TRANSLATED_VOICE_REL
    manifest = jw / EDIT_MANIFEST_REL

    status = ""
    for st in (vs, js):
        st_val = str(st.get("voice_edit_status") or "").strip()
        if st_val:
            status = st_val
            break
    if not status:
        status = "voice_edit_pending" if edited.is_file() else "not_started"

    voice_edited = bool(vs.get("voice_edited") or js.get("voice_edited"))

    info = get_voice_subtitle_source(jw)
    return VoiceEditStatus(
        voice_edit_status=status,
        voice_edited=voice_edited,
        edited_voice_path=edited if edited.is_file() else None,
        translated_voice_path=translated_voice if translated_voice.is_file() else None,
        edit_manifest_path=manifest if manifest.is_file() else None,
        source_mode=info.mode,
    )


def load_voice_subtitle_cues(
    job_workspace: str | Path,
) -> tuple[VoiceSourceMode, list[SRTCue]]:
    """
    Return (mode, cues) for the current voice subtitle source. UI uses this to populate the editor.

    mode: "edited_voice" | "translated_voice" | "missing"
    """
    info = get_voice_subtitle_source(job_workspace)
    if info.path is None:
        return info.mode, []
    res = read_subtitle_file(info.path)
    return info.mode, parse_srt_cues(res.text)


def get_voice_subtitle_source(job_workspace: str | Path) -> VoiceSourceInfo:
    """
    Return current voice subtitle source for app (priority):
    - artifacts/edit/edited_voice.srt
    - artifacts/translate/translated_voice.srt
    """
    jw = Path(job_workspace).expanduser().resolve()
    edited = jw / EDITED_VOICE_REL
    if edited.is_file():
        return VoiceSourceInfo(mode="edited_voice", path=edited)
    translated_voice = jw / TRANSLATED_VOICE_REL
    if translated_voice.is_file():
        return VoiceSourceInfo(mode="translated_voice", path=translated_voice)
    return VoiceSourceInfo(mode="missing", path=None)


def seed_edited_voice(
    job_workspace: str | Path,
    *,
    overwrite: bool = False,
    note: str | None = None,
) -> Path:
    """
    Seed artifacts/edit/edited_voice.srt from artifacts/translate/translated_voice.srt
    and write artifacts/edit/edit_manifest.json.
    """
    jw = Path(job_workspace).expanduser().resolve()
    src = jw / TRANSLATED_VOICE_REL
    if not src.is_file():
        raise VoiceEditError(f"Missing voice subtitle to seed from: {src}")

    dst = jw / EDITED_VOICE_REL
    copied = False
    binary_copy = False
    if dst.exists() and not overwrite:
        dst.parent.mkdir(parents=True, exist_ok=True)
    else:
        cr = copy_subtitle_artifact(src, dst, stage_tag="seed_voice_edit")
        copied = True
        binary_copy = bool(cr.used_binary_copy)

    seeded_fp = fingerprint_file(src)
    dst_fp = fingerprint_file(dst)
    manifest_path = jw / EDIT_MANIFEST_REL
    now = time.time()
    body: dict[str, Any] = _load_json(manifest_path) or {}
    save_count = int(body.get("save_count") or 0)
    body = {
        "version": 1,
        "seeded_from_path": str(src.resolve()),
        "seeded_from_fingerprint": seeded_fp,
        "edited_voice_path": str(dst.resolve()),
        "edited_voice_fingerprint": dst_fp,
        "seeded_at_unix": body.get("seeded_at_unix") or now,
        "last_saved_at_unix": now if copied or not body.get("last_saved_at_unix") else body.get("last_saved_at_unix"),
        "save_count": save_count,
        "binary_copy": binary_copy if copied else bool(body.get("binary_copy") or False),
        "notes": note or body.get("notes") or None,
    }
    _write_json(manifest_path, body)

    mark_voice_edit_pending(jw)
    return dst


def save_edited_voice(
    job_workspace: str | Path,
    *,
    edited_voice_text: str | None = None,
    edited_voice_source_path: str | Path | None = None,
    note: str | None = None,
) -> Path:
    """
    Save artifacts/edit/edited_voice.srt either from provided text or by copying from a path.
    Also updates edit_manifest.json (increments save_count).
    """
    jw = Path(job_workspace).expanduser().resolve()
    dst = jw / EDITED_VOICE_REL
    dst.parent.mkdir(parents=True, exist_ok=True)

    if edited_voice_source_path is not None:
        src = Path(edited_voice_source_path).expanduser()
        try:
            src = src.resolve()
        except OSError as e:
            raise VoiceEditError(f"Invalid edited_voice_source_path: {e}") from e
        if not src.is_file():
            raise VoiceEditError(f"edited_voice_source_path is not a file: {src}")
        if src.suffix.lower() != ".srt":
            raise VoiceEditError(f"Expected .srt file, got {src.suffix!r}: {src}")
        copy_subtitle_artifact(src, dst, stage_tag="save_voice_edit")
    else:
        if edited_voice_text is None:
            raise VoiceEditError("Provide either edited_voice_text or edited_voice_source_path.")
        write_subtitle_file_utf8(dst, str(edited_voice_text))

    manifest_path = jw / EDIT_MANIFEST_REL
    base = _load_json(manifest_path) or {"version": 1}
    save_count = int(base.get("save_count") or 0) + 1
    now = time.time()
    base.update(
        {
            "version": 1,
            "edited_voice_path": str(dst.resolve()),
            "edited_voice_fingerprint": fingerprint_file(dst),
            "last_saved_at_unix": now,
            "save_count": save_count,
        }
    )
    if note is not None:
        base["notes"] = note
    _write_json(manifest_path, base)

    job_id = jw.name
    _merge_job_state(
        jw,
        {
            "job_id": job_id,
            "job_workspace": str(jw),
            "edited_voice_path": str(dst.resolve()),
            "edit_manifest_path": str(manifest_path.resolve()),
            "last_error": None,
        },
    )
    _merge_video_state(
        jw,
        {
            "video_id": job_id,
            "last_error": None,
            "artifact_paths": {
                "edited_voice_srt": str(dst.resolve()),
                "edit_manifest": str(manifest_path.resolve()),
            },
        },
    )
    # Saving draft text re-opens the human review gate until the user explicitly
    # approves the latest edited_voice.srt for downstream TTS/render.
    mark_voice_edit_pending(jw)
    return dst


def mark_voice_edit_pending(job_workspace: str | Path) -> None:
    """Mark a workspace as waiting for human voice edit completion."""
    jw = Path(job_workspace).expanduser().resolve()
    edited = jw / EDITED_VOICE_REL
    if not edited.is_file():
        raise VoiceEditError(f"Missing edited voice subtitle: {edited}")
    manifest_path = jw / EDIT_MANIFEST_REL
    job_id = jw.name
    updates = {
        "job_id": job_id,
        "job_workspace": str(jw),
        "status": "voice_edit_pending",
        "current_stage": "voice_edit_pending",
        "voice_edit_status": "voice_edit_pending",
        "voice_edited": False,
        "edited_voice_path": str(edited.resolve()),
        "last_error": None,
    }
    if manifest_path.is_file():
        updates["edit_manifest_path"] = str(manifest_path.resolve())
    _merge_job_state(jw, updates)
    _merge_video_state(
        jw,
        {
            "video_id": job_id,
            "status": "voice_edit_pending",
            "current_stage": "voice_edit_pending",
            "voice_edit_status": "voice_edit_pending",
            "voice_edited": False,
            "last_error": None,
            "artifact_paths": {
                "edited_voice_srt": str(edited.resolve()),
                **(
                    {"edit_manifest": str(manifest_path.resolve())}
                    if manifest_path.is_file()
                    else {}
                ),
            },
        },
    )


def mark_voice_edited(job_workspace: str | Path) -> None:
    """Mark voice edit as completed (app can call this after save)."""
    jw = Path(job_workspace).expanduser().resolve()
    edited = jw / EDITED_VOICE_REL
    if not edited.is_file():
        raise VoiceEditError(f"Missing edited voice subtitle: {edited}")
    job_id = jw.name
    _merge_job_state(
        jw,
        {
            "job_id": job_id,
            "job_workspace": str(jw),
            "status": "voice_edited",
            "current_stage": "voice_edited",
            "voice_edit_status": "voice_edited",
            "voice_edited": True,
            "last_error": None,
        },
    )
    _merge_video_state(
        jw,
        {
            "video_id": job_id,
            "status": "voice_edited",
            "current_stage": "voice_edited",
            "voice_edit_status": "voice_edited",
            "voice_edited": True,
            "last_error": None,
        },
    )

