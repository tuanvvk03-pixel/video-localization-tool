"""JSON CLI for UI editor (Phase 2).

Subcommands emit a single JSON object to stdout:
    {"ok": true, "data": {...}}                 on success
    {"ok": false, "error": {"code": "...", "message": "..."}}  on failure

Subcommands:
  status        Return voice-edit state snapshot + artifact paths.
  load          Return current voice subtitle cues ([{index,start_ms,end_ms,text}, ...]).
  seed          Seed artifacts/edit/edited_voice.srt from translated_voice.srt.
  save          Save edited SRT (content from --from-file or stdin).
  mark-edited   Mark voice_edited=true after user finishes editing.

All subcommands take --job-workspace <path>.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import Any

from engine.voice_edit_api import (
    VoiceEditError,
    get_voice_edit_status,
    load_voice_subtitle_cues,
    mark_voice_edited,
    save_edited_voice,
    seed_edited_voice,
)


def _emit(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    sys.stdout.flush()


def _ok(data: dict[str, Any]) -> int:
    _emit({"ok": True, "data": data})
    return 0


def _err(code: str, message: str) -> int:
    _emit({"ok": False, "error": {"code": code, "message": message}})
    return 1


def _path_or_none(p: Path | None) -> str | None:
    return str(p.resolve()) if p is not None else None


def _cmd_status(ns: argparse.Namespace) -> int:
    jw = Path(ns.job_workspace).expanduser().resolve()
    st = get_voice_edit_status(jw)
    return _ok(
        {
            "job_workspace": str(jw),
            "voice_edit_status": st.voice_edit_status,
            "voice_edited": st.voice_edited,
            "source_mode": st.source_mode,
            "edited_voice_path": _path_or_none(st.edited_voice_path),
            "translated_voice_path": _path_or_none(st.translated_voice_path),
            "edit_manifest_path": _path_or_none(st.edit_manifest_path),
        }
    )


def _cmd_load(ns: argparse.Namespace) -> int:
    jw = Path(ns.job_workspace).expanduser().resolve()
    mode, cues = load_voice_subtitle_cues(jw)
    if mode == "missing":
        return _err(
            "voice_subtitle_missing",
            "No voice subtitle found. Run translate (voice) or seed first.",
        )
    return _ok(
        {
            "source_mode": mode,
            "cues": [dataclasses.asdict(c) for c in cues],
        }
    )


def _cmd_seed(ns: argparse.Namespace) -> int:
    jw = Path(ns.job_workspace).expanduser().resolve()
    try:
        out = seed_edited_voice(
            jw,
            overwrite=bool(ns.overwrite),
            note=(ns.note.strip() or None) if ns.note else None,
        )
    except VoiceEditError as e:
        return _err("seed_failed", str(e))
    return _ok({"edited_voice_path": str(out.resolve())})


def _cmd_save(ns: argparse.Namespace) -> int:
    jw = Path(ns.job_workspace).expanduser().resolve()
    if ns.from_file:
        try:
            out = save_edited_voice(
                jw,
                edited_voice_source_path=Path(ns.from_file).expanduser(),
                note=(ns.note.strip() or None) if ns.note else None,
            )
        except VoiceEditError as e:
            return _err("save_failed", str(e))
    else:
        try:
            text = sys.stdin.read()
        except OSError as e:
            return _err("stdin_read_failed", str(e))
        if not text.strip():
            return _err("empty_payload", "Expected SRT content on stdin or --from-file.")
        try:
            out = save_edited_voice(
                jw,
                edited_voice_text=text,
                note=(ns.note.strip() or None) if ns.note else None,
            )
        except VoiceEditError as e:
            return _err("save_failed", str(e))
    return _ok({"edited_voice_path": str(out.resolve())})


def _cmd_mark_edited(ns: argparse.Namespace) -> int:
    jw = Path(ns.job_workspace).expanduser().resolve()
    try:
        mark_voice_edited(jw)
    except VoiceEditError as e:
        return _err("mark_failed", str(e))
    st = get_voice_edit_status(jw)
    return _ok(
        {
            "voice_edit_status": st.voice_edit_status,
            "voice_edited": st.voice_edited,
        }
    )


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="engine.voice_edit_cli",
        description="JSON backend for UI voice-edit flow (Phase 2).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    def _add_jw(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--job-workspace", required=True, help="Video workspace root.")

    sp_status = sub.add_parser("status", help="Return voice-edit state snapshot.")
    _add_jw(sp_status)
    sp_status.set_defaults(func=_cmd_status)

    sp_load = sub.add_parser("load", help="Return current voice subtitle cues.")
    _add_jw(sp_load)
    sp_load.set_defaults(func=_cmd_load)

    sp_seed = sub.add_parser("seed", help="Seed edited_voice.srt from translated_voice.srt.")
    _add_jw(sp_seed)
    sp_seed.add_argument("--overwrite", action="store_true")
    sp_seed.add_argument("--note", default="")
    sp_seed.set_defaults(func=_cmd_seed)

    sp_save = sub.add_parser("save", help="Save edited SRT (stdin or --from-file).")
    _add_jw(sp_save)
    sp_save.add_argument("--from-file", default="", help="Path to SRT file to import.")
    sp_save.add_argument("--note", default="")
    sp_save.set_defaults(func=_cmd_save)

    sp_mark = sub.add_parser("mark-edited", help="Mark voice_edited=true.")
    _add_jw(sp_mark)
    sp_mark.set_defaults(func=_cmd_mark_edited)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    ns = parser.parse_args(argv)
    try:
        return int(ns.func(ns))
    except OSError as e:
        return _err("os_error", str(e))


if __name__ == "__main__":
    raise SystemExit(main())
