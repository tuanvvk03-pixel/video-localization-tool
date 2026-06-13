from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desktop import server as desktop_server
from engine.preflight import build_preflight_report
from engine.project_manager import add_video, init_project, run_render_phase, run_translate_phase
from engine.voice_edit_api import mark_voice_edited


def _emit(payload: dict[str, Any]) -> int:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if payload.get("ok") else 1


def _check_path_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise RuntimeError(f"Missing expected {label}: {path}")


def _cmd_preflight(ns: argparse.Namespace) -> int:
    report = build_preflight_report(
        job_workspace=(ns.job_workspace or ""),
        translate_backend=ns.translate_backend,
        tts_provider=ns.tts_provider,
        api_key=ns.api_key,
        require_input=bool(ns.require_input),
        require_render=bool(ns.require_render),
        require_long_video=bool(ns.require_long_video),
    )
    return _emit(report)


def _cmd_single(ns: argparse.Namespace) -> int:
    workspace_root = Path(ns.workspace_root or tempfile.mkdtemp(prefix="backend_smoke_single_"))
    init_status, init_payload = desktop_server.handle_init_job(
        {
            "video": str(Path(ns.video).expanduser().resolve()),
            "workspace_root": str(workspace_root),
            "job_id": ns.job_id,
            "force": bool(ns.force),
        }
    )
    if init_status >= 400:
        return _emit(init_payload)
    jw = Path(init_payload["data"]["job_workspace"])

    until_status, until_payload = desktop_server.handle_run_until_edit(
        {
            "job_workspace": str(jw),
            "project_name": ns.project_name,
            "api_key": ns.api_key,
            "translate_backend": ns.translate_backend,
            "enable_source_cleanup": bool(ns.enable_source_cleanup),
            "enable_translation_qa": bool(ns.enable_translation_qa),
            "target_minutes": float(ns.target_minutes),
            "max_minutes": float(ns.max_minutes),
            "max_workers": int(ns.max_workers),
        }
    )
    if until_status >= 400:
        return _emit(until_payload)

    edited_voice = jw / "artifacts" / "edit" / "edited_voice.srt"
    _check_path_exists(edited_voice, "edited_voice.srt")

    after_payload: dict[str, Any] | None = None
    if ns.to_stage != "translated":
        if not ns.accept_seeded_edit_for_smoke:
            return _emit(
                {
                    "ok": False,
                    "error": (
                        "single smoke reached voice_edit_pending. Pass "
                        "--accept-seeded-edit-for-smoke to continue automatically."
                    ),
                    "data": {
                        "job_workspace": str(jw),
                        "edited_voice_path": str(edited_voice.resolve()),
                    },
                }
            )
        mark_voice_edited(jw)
        after_status, after_payload = desktop_server.handle_run_after_edit(
            {
                "job_workspace": str(jw),
                "project_name": ns.project_name,
                "api_key": ns.api_key,
                "translate_backend": ns.translate_backend,
                "tts_voice": ns.tts_voice,
                "mix_mode": ns.mix_mode,
                "subtitle_mode": ns.subtitle_mode,
                "to_stage": ns.to_stage,
                "max_workers": int(ns.max_workers),
            }
        )
        if after_status >= 400:
            return _emit(after_payload)

    payload: dict[str, Any] = {
        "ok": True,
        "mode": "single",
        "job_workspace": str(jw),
        "until_edit": until_payload["data"],
    }
    if after_payload is not None:
        payload["after_edit"] = after_payload["data"]
    return _emit(payload)


def _cmd_multi(ns: argparse.Namespace) -> int:
    if not ns.videos:
        return _emit({"ok": False, "error": "Provide at least one --video for multi smoke."})
    projects_root = Path(ns.projects_root or tempfile.mkdtemp(prefix="backend_smoke_multi_"))
    state = init_project(
        projects_root,
        ns.project_name,
        config_overrides={
            "api_key": ns.api_key,
            "translate_backend": ns.translate_backend,
            "tts_provider": ns.tts_provider,
            "tts_voice": ns.tts_voice,
            "mix_mode": ns.mix_mode,
            "enable_source_cleanup": bool(ns.enable_source_cleanup),
            "enable_translation_qa": bool(ns.enable_translation_qa),
        },
        force=bool(ns.force),
    )
    pr = Path(state.project_root)
    added: list[str] = []
    for video in ns.videos:
        entry = add_video(
            pr,
            Path(video).expanduser().resolve(),
            max_duration_s=(float(ns.max_duration_s) if ns.max_duration_s > 0 else None),
        )
        added.append(entry.video_id)

    translate_results = run_translate_phase(
        pr,
        max_workers=(int(ns.max_workers) or None),
        long_video_workers=int(ns.long_video_workers),
    )
    if not all(r.get("ok") for r in translate_results):
        return _emit({"ok": False, "mode": "multi", "project_root": str(pr), "translate_results": translate_results})

    render_results: list[dict[str, Any]] | None = None
    if ns.to_stage != "translated":
        if not ns.accept_seeded_edit_for_smoke:
            return _emit(
                {
                    "ok": False,
                    "error": (
                        "multi smoke reached voice_edit_pending. Pass "
                        "--accept-seeded-edit-for-smoke to continue automatically."
                    ),
                    "data": {"project_root": str(pr), "video_ids": added},
                }
            )
        for video_id in added:
            mark_voice_edited(pr / "videos" / video_id)
        render_results = run_render_phase(
            pr,
            to_stage=ns.to_stage,
            max_workers=(int(ns.max_workers) or None),
            long_video_workers=int(ns.long_video_workers),
        )
        if not all(r.get("ok") for r in render_results):
            return _emit({"ok": False, "mode": "multi", "project_root": str(pr), "render_results": render_results})

    payload: dict[str, Any] = {
        "ok": True,
        "mode": "multi",
        "project_root": str(pr),
        "video_ids": added,
        "translate_results": translate_results,
    }
    if render_results is not None:
        payload["render_results"] = render_results
    return _emit(payload)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Backend smoke runner for short/long/multi flows.")
    sub = p.add_subparsers(dest="command", required=True)

    sp_pre = sub.add_parser("preflight", help="Run backend preflight checks.")
    sp_pre.add_argument("--job-workspace", default="")
    sp_pre.add_argument("--translate-backend", default="block_v2", choices=["legacy", "block_v2"])
    sp_pre.add_argument("--tts-provider", default="edge_tts")
    sp_pre.add_argument("--api-key", default="")
    sp_pre.add_argument("--require-input", action="store_true")
    sp_pre.add_argument("--require-render", action="store_true")
    sp_pre.add_argument("--require-long-video", action="store_true")
    sp_pre.set_defaults(func=_cmd_preflight)

    sp_single = sub.add_parser(
        "single",
        help="Run single-video smoke using desktop backend handlers (auto-routes short/long).",
    )
    sp_single.add_argument("--video", required=True)
    sp_single.add_argument("--workspace-root", default="")
    sp_single.add_argument("--job-id", default="")
    sp_single.add_argument("--project-name", required=True)
    sp_single.add_argument("--api-key", default="")
    sp_single.add_argument("--translate-backend", default="block_v2", choices=["legacy", "block_v2"])
    sp_single.add_argument("--enable-source-cleanup", action="store_true")
    sp_single.add_argument("--enable-translation-qa", action="store_true")
    sp_single.add_argument("--target-minutes", type=float, default=4.0)
    sp_single.add_argument("--max-minutes", type=float, default=5.0)
    sp_single.add_argument("--max-workers", type=int, default=0)
    sp_single.add_argument("--to-stage", default="translated")
    sp_single.add_argument("--tts-voice", default="")
    sp_single.add_argument("--mix-mode", default="replace_original_speech")
    sp_single.add_argument("--subtitle-mode", default="soft")
    sp_single.add_argument("--force", action="store_true")
    sp_single.add_argument(
        "--accept-seeded-edit-for-smoke",
        action="store_true",
        help="Explicitly mark the seeded edited_voice.srt as voice_edited to continue automated smoke.",
    )
    sp_single.set_defaults(func=_cmd_single)

    sp_multi = sub.add_parser("multi", help="Run multi-video smoke on a project workspace.")
    sp_multi.add_argument("--projects-root", default="")
    sp_multi.add_argument("--project-name", required=True)
    sp_multi.add_argument("--video", dest="videos", action="append", default=[])
    sp_multi.add_argument("--api-key", default="")
    sp_multi.add_argument("--translate-backend", default="block_v2", choices=["legacy", "block_v2"])
    sp_multi.add_argument("--tts-provider", default="edge_tts")
    sp_multi.add_argument("--tts-voice", default="")
    sp_multi.add_argument("--mix-mode", default="replace_original_speech")
    sp_multi.add_argument("--enable-source-cleanup", action="store_true")
    sp_multi.add_argument("--enable-translation-qa", action="store_true")
    sp_multi.add_argument("--max-workers", type=int, default=0)
    sp_multi.add_argument("--long-video-workers", type=int, default=2)
    sp_multi.add_argument("--to-stage", default="translated")
    sp_multi.add_argument("--max-duration-s", type=float, default=0.0)
    sp_multi.add_argument("--force", action="store_true")
    sp_multi.add_argument(
        "--accept-seeded-edit-for-smoke",
        action="store_true",
        help="Explicitly mark each seeded edited_voice.srt as voice_edited to continue automated smoke.",
    )
    sp_multi.set_defaults(func=_cmd_multi)
    return p


def main(argv: list[str] | None = None) -> int:
    ns = _build_parser().parse_args(argv)
    try:
        return int(ns.func(ns))
    except Exception as e:  # noqa: BLE001
        return _emit({"ok": False, "error": str(e)})


if __name__ == "__main__":
    raise SystemExit(main())
