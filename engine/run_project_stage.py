"""JSON CLI for multi-video project orchestration (Phase 5).

Subcommands (JSON envelope {ok, data|error}):
    init             Create a project directory.
    add-video        Copy a video into the project as a new video_workspace.
    list             Per-video status snapshot.
    run-translate    Parallel translate + seed (≤ 5 workers) across all project videos.
    run-render       Parallel finalize + TTS + render for voice_edited videos.
    set-override     Set a per-video config override.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from engine import project_manager
from engine.project_manager import (
    MAX_PARALLEL_VIDEOS,
    ProjectError,
    add_video,
    init_project,
    list_video_statuses,
    load_project,
    run_render_phase,
    run_translate_phase,
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


def _cmd_init(ns: argparse.Namespace) -> int:
    overrides: dict[str, Any] = {}
    if ns.api_key:
        overrides["api_key"] = ns.api_key
    if ns.tts_voice:
        overrides["tts_voice"] = ns.tts_voice
    if ns.mix_mode:
        overrides["mix_mode"] = ns.mix_mode
    if ns.enable_source_cleanup:
        overrides["enable_source_cleanup"] = True
    if ns.enable_translation_qa:
        overrides["enable_translation_qa"] = True
    try:
        state = init_project(
            Path(ns.projects_root),
            ns.project_name,
            project_id=ns.project_id,
            config_overrides=overrides,
            force=bool(ns.force),
        )
    except ProjectError as e:
        return _err("init_failed", str(e))
    return _ok(
        {
            "project_id": state.project_id,
            "project_root": state.project_root,
            "config": asdict(state.config),
        }
    )


def _cmd_add_video(ns: argparse.Namespace) -> int:
    cap = float(getattr(ns, "max_duration_s", 0.0) or 0.0)
    try:
        entry = add_video(
            Path(ns.project_root),
            Path(ns.video),
            video_id=ns.video_id,
            max_duration_s=(cap if cap > 0 else None),
            force=bool(ns.force),
        )
    except ProjectError as e:
        return _err("add_video_failed", str(e))
    return _ok(asdict(entry))


def _cmd_list(ns: argparse.Namespace) -> int:
    try:
        statuses = list_video_statuses(Path(ns.project_root))
    except ProjectError as e:
        return _err("list_failed", str(e))
    return _ok({"videos": statuses})


def _cmd_run_translate(ns: argparse.Namespace) -> int:
    try:
        results = run_translate_phase(
            Path(ns.project_root),
            max_workers=ns.max_workers,
            video_ids=ns.video_ids or None,
            long_video_workers=int(ns.long_video_workers),
        )
    except ProjectError as e:
        return _err("run_translate_failed", str(e))
    return _ok({"results": results, "max_workers": MAX_PARALLEL_VIDEOS})


def _cmd_run_render(ns: argparse.Namespace) -> int:
    try:
        results = run_render_phase(
            Path(ns.project_root),
            to_stage=ns.to_stage,
            max_workers=ns.max_workers,
            video_ids=ns.video_ids or None,
            long_video_workers=int(ns.long_video_workers),
        )
    except ProjectError as e:
        return _err("run_render_failed", str(e))
    return _ok({"results": results, "to_stage": ns.to_stage})


def _cmd_set_override(ns: argparse.Namespace) -> int:
    try:
        state = load_project(Path(ns.project_root))
    except ProjectError as e:
        return _err("load_failed", str(e))
    if not any(v.video_id == ns.video_id for v in state.videos):
        return _err("unknown_video", f"video_id not in project: {ns.video_id}")
    try:
        override = json.loads(ns.override_json)
    except json.JSONDecodeError as e:
        return _err("invalid_override", f"override-json must be a JSON object: {e}")
    if not isinstance(override, dict):
        return _err("invalid_override", "override-json must be a JSON object")
    state.config.per_video_overrides[ns.video_id] = override
    project_manager._write_state(state)  # noqa: SLF001 - intentional internal use
    return _ok(
        {
            "video_id": ns.video_id,
            "effective_config": state.config.resolve_for(ns.video_id),
        }
    )


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="engine.run_project_stage",
        description="Multi-video project orchestration (Phase 5).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sp_init = sub.add_parser("init", help="Create a new project.")
    sp_init.add_argument("--projects-root", required=True)
    sp_init.add_argument("--project-name", required=True)
    sp_init.add_argument("--project-id", default="")
    sp_init.add_argument("--api-key", default="")
    sp_init.add_argument("--tts-voice", default="")
    sp_init.add_argument("--mix-mode", default="")
    sp_init.add_argument("--enable-source-cleanup", action="store_true")
    sp_init.add_argument("--enable-translation-qa", action="store_true")
    sp_init.add_argument("--force", action="store_true")
    sp_init.set_defaults(func=_cmd_init)

    sp_add = sub.add_parser(
        "add-video",
        help="Add a video. Videos longer than 5 min are routed through the long-video orchestrator.",
    )
    sp_add.add_argument("--project-root", required=True)
    sp_add.add_argument("--video", required=True)
    sp_add.add_argument("--video-id", default="")
    sp_add.add_argument(
        "--max-duration-s",
        type=float,
        default=0.0,
        help="Optional hard cap on duration; 0 disables (default).",
    )
    sp_add.add_argument("--force", action="store_true")
    sp_add.set_defaults(func=_cmd_add_video)

    sp_list = sub.add_parser("list", help="Per-video status snapshot.")
    sp_list.add_argument("--project-root", required=True)
    sp_list.set_defaults(func=_cmd_list)

    sp_rt = sub.add_parser("run-translate", help="Parallel translate + seed.")
    sp_rt.add_argument("--project-root", required=True)
    sp_rt.add_argument("--max-workers", type=int, default=0)
    sp_rt.add_argument("--video-ids", nargs="*", default=[])
    sp_rt.add_argument(
        "--long-video-workers",
        type=int,
        default=2,
        help="Inner segment workers per long video (default 2).",
    )
    sp_rt.set_defaults(func=_cmd_run_translate)

    sp_rr = sub.add_parser("run-render", help="Parallel finalize + TTS + render for edited videos.")
    sp_rr.add_argument("--project-root", required=True)
    sp_rr.add_argument("--to-stage", default="rendered")
    sp_rr.add_argument("--max-workers", type=int, default=0)
    sp_rr.add_argument("--video-ids", nargs="*", default=[])
    sp_rr.add_argument(
        "--long-video-workers",
        type=int,
        default=2,
        help="Inner segment workers per long video (default 2).",
    )
    sp_rr.set_defaults(func=_cmd_run_render)

    sp_so = sub.add_parser("set-override", help="Set a per-video config override.")
    sp_so.add_argument("--project-root", required=True)
    sp_so.add_argument("--video-id", required=True)
    sp_so.add_argument(
        "--override-json",
        required=True,
        help='JSON object of fields to override, e.g. \'{"tts_voice": "vi-VN-NamMinh"}\'.',
    )
    sp_so.set_defaults(func=_cmd_set_override)

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
