"""Long-video orchestrator: plan -> split -> parallel segment pipelines -> merge.

Bridges the single-video pipeline (engine.run_job) with the segment manager so a
single "long" video flows through the same voice-edit gate as a short one:

    plan-split   -> probe duration, plan segments, init seg_NNN workspaces (ffmpeg split)
    until-edit   -> run transcribe+translate in parallel across segments, seed each
                    seg's edited_voice.srt, merge them into a parent-level
                    artifacts/edit/edited_voice.srt for the UI to edit.
    after-edit   -> distribute the parent edited_voice.srt back to each seg, mark
                    voice_edited, run finalize+TTS+align+mix+render in parallel,
                    concat renders into the parent's artifacts/render/<name>.

For videos whose duration is at or below SINGLE_VIDEO_THRESHOLD_S (5 min), the
planner yields a single seg_000 and the orchestration still works uniformly — a
short video just runs one worker.

Concurrency is capped by --max-workers (default 4). Each worker shells into
engine.run_job for a single seg workspace with no shared mutable state.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

from engine import run_job
from engine.render_settings import load_render_settings
from engine.segment_manager import (
    SegmentError,
    distribute_edited_voice_to_segments,
    init_segment_workspaces,
    load_segment_manifest,
    merge_segment_edited_voices,
    merge_segment_renders,
    plan_segments,
    probe_video_duration,
    seed_segment_edited_voices,
)
from engine.voice_edit_api import (
    VoiceEditError,
    get_voice_edit_status,
    mark_voice_edit_pending,
    mark_voice_edited,
)

MAX_PARALLEL_SEGMENTS = 4


class LongVideoError(RuntimeError):
    pass


def _voice_edit_completed(job_workspace: Path) -> bool:
    status = get_voice_edit_status(job_workspace)
    return bool(status.edited_voice_path) and (
        bool(status.voice_edited) or status.voice_edit_status == "voice_edited"
    )


def _resolve_workers(requested: int | None, segment_count: int) -> int:
    if requested is None or requested <= 0:
        n = MAX_PARALLEL_SEGMENTS
    else:
        n = int(requested)
    return max(1, min(n, segment_count))


def _run_job_argv(seg_ws: Path, cfg: dict[str, Any], *, to_stage: str) -> list[str]:
    argv = [
        "--job-workspace",
        str(seg_ws),
        "--project-name",
        str(cfg.get("project_name") or "project"),
        "--to-stage",
        to_stage,
        "--finalize-mode",
        "voice",
        "--translate-backend",
        str(cfg.get("translate_backend") or "block_v2"),
        "--tts-provider",
        str(cfg.get("tts_provider") or "edge_tts"),
        "--mix-mode",
        str(cfg.get("mix_mode") or "replace_original_speech"),
    ]
    if str(cfg.get("project_root") or "").strip():
        argv.extend(["--project-root", str(cfg["project_root"]).strip()])
    if str(cfg.get("api_key") or "").strip():
        argv.extend(["--api-key", str(cfg["api_key"]).strip()])
    if str(cfg.get("source_language") or "").strip():
        argv.extend(["--transcribe-language", str(cfg["source_language"]).strip()])
    if str(cfg.get("tts_voice") or "").strip():
        argv.extend(["--tts-voice", str(cfg["tts_voice"]).strip()])
    if str(cfg.get("tts_rate") or "").strip():
        argv.extend(["--tts-rate", str(cfg["tts_rate"]).strip()])
    if cfg.get("mix_duck_gain_db") is not None:
        argv.extend(["--duck-gain-db", str(cfg["mix_duck_gain_db"])])
    if str(cfg.get("render_subtitle_mode") or "").strip():
        argv.extend(["--render-subtitle-mode", str(cfg["render_subtitle_mode"]).strip()])
    if str(cfg.get("render_aspect_ratio") or "").strip():
        argv.extend(["--render-aspect-ratio", str(cfg["render_aspect_ratio"]).strip()])
    if str(cfg.get("render_background_image") or "").strip():
        argv.extend(["--render-background-image", str(cfg["render_background_image"]).strip()])
    if cfg.get("enable_translation_qa"):
        argv.append("--enable-translation-qa")
    if cfg.get("enable_source_cleanup"):
        argv.append("--enable-source-cleanup")
    return argv


def do_plan_split(
    parent_workspace: Path,
    *,
    video: Path | None = None,
    target_minutes: float = 4.0,
    max_minutes: float = 5.0,
    force: bool = False,
) -> dict[str, Any]:
    parent = parent_workspace.expanduser().resolve()
    src = (video or (parent / "input" / "source.mp4")).expanduser()
    if not src.is_file():
        raise LongVideoError(f"Missing source video: {src}")

    manifest_path = parent / "segments" / "manifest.json"
    if manifest_path.is_file() and not force:
        manifest = load_segment_manifest(parent)
        return {
            "reused": True,
            "parent_workspace": str(parent),
            "segment_count": len(manifest.segments),
            "duration_s": manifest.source_duration_s,
        }

    duration = probe_video_duration(src)
    plan = plan_segments(
        duration,
        target_s=float(target_minutes) * 60.0,
        max_s=float(max_minutes) * 60.0,
    )
    seg_dirs = init_segment_workspaces(parent, src, plan)
    return {
        "reused": False,
        "parent_workspace": str(parent),
        "source_video": str(src.resolve()),
        "duration_s": duration,
        "segment_count": len(seg_dirs),
        "segments": [
            {
                "index": p.index,
                "start_s": p.start_s,
                "end_s": p.end_s,
                "workspace": str(seg_dirs[i].resolve()),
            }
            for i, p in enumerate(plan)
        ],
    }


def _translate_one(
    entry: dict[str, Any],
    cfg: dict[str, Any],
    runner: Callable[[list[str]], int],
) -> dict[str, Any]:
    seg_ws = Path(entry["workspace"])
    argv = _run_job_argv(seg_ws, cfg, to_stage="translated")
    rc = runner(argv)
    if rc != 0:
        return {"index": entry["index"], "ok": False, "error": f"run_job rc={rc}"}
    translated_voice = seg_ws / "artifacts" / "translate" / "translated_voice.srt"
    if not translated_voice.is_file():
        # Legacy translate backend may only write translated_auto.srt; promote it
        # so downstream voice-edit flow can seed edited_voice.srt.
        translated_auto = seg_ws / "artifacts" / "translate" / "translated_auto.srt"
        if translated_auto.is_file():
            try:
                translated_voice.parent.mkdir(parents=True, exist_ok=True)
                translated_voice.write_text(translated_auto.read_text(encoding="utf-8"), encoding="utf-8")
            except OSError as e:
                return {"index": entry["index"], "ok": False, "error": f"could not promote translated_auto.srt: {e}"}
        if not translated_voice.is_file():
            return {
                "index": entry["index"],
                "ok": False,
                "error": "translated_voice.srt missing (need translate_backend=block_v2)",
            }
    return {"index": entry["index"], "ok": True}


def do_until_edit(
    parent_workspace: Path,
    *,
    cfg: dict[str, Any],
    max_workers: int | None = None,
    runner: Callable[[list[str]], int] | None = None,
) -> dict[str, Any]:
    parent = parent_workspace.expanduser().resolve()
    _runner = runner or run_job.main
    manifest = load_segment_manifest(parent)
    entries = manifest.segments
    if not entries:
        raise LongVideoError("Segment manifest has no segments.")

    workers = _resolve_workers(max_workers, len(entries))
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_translate_one, entry, cfg, _runner): entry for entry in entries
        }
        for fut in as_completed(futures):
            results.append(fut.result())
    results.sort(key=lambda r: int(r.get("index") or 0))

    failed = [r for r in results if not r.get("ok")]
    if failed:
        first = failed[0]
        return {
            "phase": "until_edit",
            "ok": False,
            "results": results,
            "error": (
                "one or more segments failed translate: "
                f"seg_{int(first.get('index') or 0):03d}: {first.get('error') or 'unknown error'}"
            ),
        }

    seed_segment_edited_voices(parent, overwrite=False)
    merged = merge_segment_edited_voices(parent)
    mark_voice_edit_pending(parent)
    return {
        "phase": "until_edit",
        "ok": True,
        "results": results,
        "parent_edited_voice_srt": str(merged.resolve()),
        "segment_count": len(entries),
        "workers": workers,
    }


def _render_one(
    entry: dict[str, Any],
    cfg: dict[str, Any],
    runner: Callable[[list[str]], int],
    to_stage: str,
) -> dict[str, Any]:
    seg_ws = Path(entry["workspace"])
    edited = seg_ws / "artifacts" / "edit" / "edited_voice.srt"
    if not edited.is_file():
        return {
            "index": entry["index"],
            "ok": False,
            "error": "edited_voice.srt missing for segment",
        }
    try:
        mark_voice_edited(seg_ws)
    except VoiceEditError as e:
        return {"index": entry["index"], "ok": False, "error": f"mark_failed: {e}"}
    argv = _run_job_argv(seg_ws, cfg, to_stage=to_stage)
    rc = runner(argv)
    if rc != 0:
        return {"index": entry["index"], "ok": False, "error": f"run_job rc={rc}"}
    return {"index": entry["index"], "ok": True}


def do_after_edit(
    parent_workspace: Path,
    *,
    cfg: dict[str, Any],
    to_stage: str = "rendered",
    max_workers: int | None = None,
    runner: Callable[[list[str]], int] | None = None,
    render_filename: str = "final.mp4",
    merge_render: bool = True,
) -> dict[str, Any]:
    if to_stage not in run_job.STAGE_ORDER:
        raise LongVideoError(f"invalid to_stage: {to_stage}")
    parent = parent_workspace.expanduser().resolve()
    _runner = runner or run_job.main
    manifest = load_segment_manifest(parent)
    entries = manifest.segments
    if not entries:
        raise LongVideoError("Segment manifest has no segments.")
    if not _voice_edit_completed(parent):
        raise LongVideoError(
            "Parent voice edit is not completed. Edit artifacts/edit/edited_voice.srt "
            "and mark voice_edited before running after-edit."
        )

    distribute_edited_voice_to_segments(parent)
    render_settings = load_render_settings(parent) or {}
    if render_settings:
        cfg = dict(cfg)
        aspect = str(render_settings.get("aspect_ratio") or "").strip()
        if aspect in {"16:9", "9:16"}:
            cfg["render_aspect_ratio"] = aspect
        background = str(render_settings.get("background_path") or "").strip()
        if background:
            bg_path = (parent / background).resolve()
            if bg_path.is_file():
                cfg["render_background_image"] = str(bg_path)

    workers = _resolve_workers(max_workers, len(entries))
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_render_one, entry, cfg, _runner, to_stage): entry for entry in entries
        }
        for fut in as_completed(futures):
            results.append(fut.result())
    results.sort(key=lambda r: int(r.get("index") or 0))

    failed = [r for r in results if not r.get("ok")]
    if failed:
        first = failed[0]
        return {
            "phase": "after_edit",
            "ok": False,
            "results": results,
            "error": (
                "one or more segments failed render: "
                f"seg_{int(first.get('index') or 0):03d}: {first.get('error') or 'unknown error'}"
            ),
        }

    merged_render: Path | None = None
    if merge_render and to_stage == "rendered":
        merged_render = merge_segment_renders(parent, render_filename=render_filename)
    return {
        "phase": "after_edit",
        "ok": True,
        "results": results,
        "merged_render_path": str(merged_render.resolve()) if merged_render else None,
        "segment_count": len(entries),
        "workers": workers,
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Long-video orchestrator (split, parallel per-segment pipelines, merge)."
    )
    p.add_argument(
        "--phase",
        required=True,
        choices=["plan-split", "until-edit", "after-edit"],
    )
    p.add_argument("--parent-workspace", required=True)
    p.add_argument("--video", default="", help="Override input video (default: <parent>/input/source.mp4).")
    p.add_argument("--target-minutes", type=float, default=4.0)
    p.add_argument("--max-minutes", type=float, default=5.0)
    p.add_argument("--force-replan", action="store_true", help="Re-split even if segments/manifest.json exists.")
    p.add_argument(
        "--max-workers",
        type=int,
        default=0,
        help=f"Parallel segment workers (default up to {MAX_PARALLEL_SEGMENTS}).",
    )
    p.add_argument("--to-stage", default="rendered", choices=run_job.STAGE_ORDER)
    p.add_argument("--render-filename", default="final.mp4")
    p.add_argument("--no-merge-render", action="store_true")

    # Pipeline config (passed to per-segment run_job)
    p.add_argument("--project-name", default="project")
    p.add_argument("--project-root", default="")
    p.add_argument("--api-key", default="")
    p.add_argument("--translate-backend", default="block_v2", choices=["legacy", "block_v2"])
    p.add_argument("--tts-provider", default="edge_tts")
    p.add_argument("--tts-voice", default="")
    p.add_argument("--tts-rate", default="")
    p.add_argument("--mix-mode", default="replace_original_speech",
                   choices=["replace_original_speech", "duck_original_speech", "keep_music_replace_voice"])
    p.add_argument("--duck-gain-db", type=float, default=None)
    p.add_argument("--render-subtitle-mode", default="burn", choices=["soft", "burn", "none"])
    p.add_argument("--enable-translation-qa", action="store_true")
    p.add_argument("--enable-source-cleanup", action="store_true")
    return p.parse_args(argv)


def _cfg_from_ns(ns: argparse.Namespace) -> dict[str, Any]:
    return {
        "project_name": ns.project_name,
        "project_root": ns.project_root,
        "api_key": ns.api_key,
        "translate_backend": ns.translate_backend,
        "tts_provider": ns.tts_provider,
        "tts_voice": ns.tts_voice,
        "tts_rate": ns.tts_rate,
        "mix_mode": ns.mix_mode,
        "mix_duck_gain_db": ns.duck_gain_db,
        "render_subtitle_mode": ns.render_subtitle_mode,
        "enable_translation_qa": bool(ns.enable_translation_qa),
        "enable_source_cleanup": bool(ns.enable_source_cleanup),
    }


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    parent = Path(ns.parent_workspace).expanduser().resolve()
    try:
        if ns.phase == "plan-split":
            video = Path(ns.video).expanduser() if ns.video else None
            payload = do_plan_split(
                parent,
                video=video,
                target_minutes=ns.target_minutes,
                max_minutes=ns.max_minutes,
                force=bool(ns.force_replan),
            )
        elif ns.phase == "until-edit":
            if not (parent / "segments" / "manifest.json").is_file():
                video = Path(ns.video).expanduser() if ns.video else None
                do_plan_split(
                    parent,
                    video=video,
                    target_minutes=ns.target_minutes,
                    max_minutes=ns.max_minutes,
                    force=False,
                )
            payload = do_until_edit(
                parent,
                cfg=_cfg_from_ns(ns),
                max_workers=(ns.max_workers or None),
            )
        else:  # after-edit
            payload = do_after_edit(
                parent,
                cfg=_cfg_from_ns(ns),
                to_stage=ns.to_stage,
                max_workers=(ns.max_workers or None),
                render_filename=ns.render_filename,
                merge_render=not ns.no_merge_render,
            )
    except (LongVideoError, SegmentError) as e:
        print(f"[run_long_video] {e}", file=sys.stderr)
        return 1

    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if payload.get("ok", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
