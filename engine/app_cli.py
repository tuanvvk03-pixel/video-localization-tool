"""Single-video workflow orchestrator for UI (Phase 3).

Collapses the 10-stage pipeline into the 3 product-level boundaries chosen in
PROJECT_HANDOFF §10 so a desktop UI can drive the flow with three shell-outs:

    init-job        Create a video workspace and place input video.
    run-until-edit  Transcribe + translate (block_v2) + seed edited_voice.srt;
                    stop at voice_edit_pending for user editing.
    run-after-edit  Mark voice_edited + finalize(voice) + TTS + align + mix + render.

All subcommands emit a single JSON object to stdout:
    {"ok": true, "data": {...}}
    {"ok": false, "error": {"code": "...", "message": "..."}}

The heavy lifting is delegated to engine.run_job and engine.voice_edit_api to avoid
duplicating pipeline logic. run-until-edit uses --translate-backend block_v2 because
only block_v2 produces artifacts/translate/translated_voice.srt (required to seed the
edit gate); pass --translate-backend legacy explicitly to override.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

from engine.preflight import build_preflight_report
from engine import run_job
from engine.input_provenance import fingerprint_file
from engine.video_download import (
    VideoDownloadError,
    init_job_from_url,
    probe_video_url,
)
from engine.voice_edit_api import (
    VoiceEditError,
    get_voice_edit_status,
    mark_voice_edited,
    seed_edited_voice,
)

_JOB_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _emit(payload: dict[str, Any]) -> None:
    # Windows consoles can default to a non-UTF8 codepage, which may raise
    # UnicodeEncodeError when printing titles/metadata with Unicode. Emit UTF-8
    # bytes when possible for stable machine-readable JSON.
    data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8", errors="replace")
    buf = getattr(sys.stdout, "buffer", None)
    if buf is not None:
        buf.write(data)
        buf.flush()
        return
    # Fallback (should be rare): decode back to text for stream-only stdout.
    sys.stdout.write(data.decode("utf-8", errors="replace"))
    sys.stdout.flush()


def _ok(data: dict[str, Any]) -> int:
    _emit({"ok": True, "data": data})
    return 0


def _err(code: str, message: str) -> int:
    _emit({"ok": False, "error": {"code": code, "message": message}})
    return 1


def _slug_job_id(name: str) -> str:
    s = _JOB_ID_RE.sub("-", name).strip("-._")
    return s or "job"


def _cmd_init_job(ns: argparse.Namespace) -> int:
    video = Path(ns.video).expanduser()
    if not video.is_file():
        return _err("video_not_found", f"Video file does not exist: {video}")

    workspace_root = Path(ns.workspace_root).expanduser().resolve()
    job_id = (ns.job_id or "").strip() or _slug_job_id(video.stem)
    jw = workspace_root / job_id

    if jw.exists() and any(jw.iterdir()) and not ns.force:
        return _err(
            "workspace_exists",
            f"Workspace already exists and is not empty: {jw}. Pass --force to reuse.",
        )

    (jw / "input").mkdir(parents=True, exist_ok=True)
    (jw / "artifacts").mkdir(parents=True, exist_ok=True)
    dst = jw / "input" / "source.mp4"

    try:
        shutil.copyfile(video, dst)
    except OSError as e:
        return _err("copy_failed", f"Could not copy video into workspace: {e}")

    fp = fingerprint_file(dst)
    return _ok(
        {
            "job_id": job_id,
            "job_workspace": str(jw.resolve()),
            "input_video_path": str(dst.resolve()),
            "input_video_fingerprint": fp,
        }
    )


def _cmd_probe_video_url(ns: argparse.Namespace) -> int:
    try:
        return _ok(probe_video_url(ns.url))
    except VideoDownloadError as e:
        return _err("video_probe_failed", str(e))


def _cmd_init_job_from_url(ns: argparse.Namespace) -> int:
    try:
        payload = init_job_from_url(
            url=ns.url,
            workspace_root=ns.workspace_root,
            job_id=ns.job_id,
            force=bool(ns.force),
        )
    except VideoDownloadError as e:
        msg = str(e)
        if "Workspace already exists" in msg:
            return _err("workspace_exists", msg)
        return _err("video_download_failed", msg)
    return _ok(payload)


def _run_job_argv(
    jw: Path,
    *,
    project_name: str,
    api_key: str,
    to_stage: str,
    finalize_mode: str,
    translate_backend: str,
    tts_provider: str,
    tts_voice: str,
    mix_mode: str,
    enable_translation_qa: bool,
    enable_source_cleanup: bool,
) -> list[str]:
    argv = [
        "--job-workspace",
        str(jw),
        "--project-name",
        project_name,
        "--to-stage",
        to_stage,
        "--finalize-mode",
        finalize_mode,
        "--translate-backend",
        translate_backend,
        "--tts-provider",
        tts_provider,
        "--mix-mode",
        mix_mode,
    ]
    if api_key.strip():
        argv.extend(["--api-key", api_key.strip()])
    if tts_voice.strip():
        argv.extend(["--tts-voice", tts_voice.strip()])
    if enable_translation_qa:
        argv.append("--enable-translation-qa")
    if enable_source_cleanup:
        argv.append("--enable-source-cleanup")
    return argv


def _cmd_run_until_edit(ns: argparse.Namespace) -> int:
    jw = Path(ns.job_workspace).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")

    argv = _run_job_argv(
        jw,
        project_name=ns.project_name,
        api_key=ns.api_key,
        to_stage="translated",
        finalize_mode="voice",
        translate_backend=ns.translate_backend,
        tts_provider="edge_tts",
        tts_voice="",
        mix_mode="replace_original_speech",
        enable_translation_qa=bool(ns.enable_translation_qa),
        enable_source_cleanup=bool(ns.enable_source_cleanup),
    )
    rc = run_job.main(argv)
    if rc != 0:
        return _err(
            "run_job_failed",
            f"run_job returned {rc}; see job_state.json / stderr for details.",
        )

    translated_voice = jw / "artifacts" / "translate" / "translated_voice.srt"
    if not translated_voice.is_file():
        return _err(
            "translated_voice_missing",
            "translate finished but translated_voice.srt is missing "
            "(use --translate-backend block_v2 to enable the voice-first flow).",
        )

    try:
        seed_edited_voice(jw, overwrite=False)
    except VoiceEditError as e:
        return _err("seed_failed", str(e))

    st = get_voice_edit_status(jw)
    return _ok(
        {
            "voice_edit_status": st.voice_edit_status,
            "voice_edited": st.voice_edited,
            "edited_voice_path": str(st.edited_voice_path.resolve())
            if st.edited_voice_path
            else None,
            "translated_voice_path": str(st.translated_voice_path.resolve())
            if st.translated_voice_path
            else None,
            "next_action": "edit_edited_voice_srt",
        }
    )


def _cmd_run_after_edit(ns: argparse.Namespace) -> int:
    jw = Path(ns.job_workspace).expanduser().resolve()
    if not jw.is_dir():
        return _err("workspace_missing", f"Job workspace not found: {jw}")

    edited = jw / "artifacts" / "edit" / "edited_voice.srt"
    if not edited.is_file():
        return _err(
            "edited_voice_missing",
            f"Missing {edited}. Seed + save the edit before running run-after-edit.",
        )

    try:
        mark_voice_edited(jw)
    except VoiceEditError as e:
        return _err("mark_failed", str(e))

    argv = _run_job_argv(
        jw,
        project_name=ns.project_name,
        api_key=ns.api_key,
        to_stage=ns.to_stage,
        finalize_mode="voice",
        translate_backend=ns.translate_backend,
        tts_provider=ns.tts_provider,
        tts_voice=ns.tts_voice,
        mix_mode=ns.mix_mode,
        enable_translation_qa=False,
        enable_source_cleanup=False,
    )
    rc = run_job.main(argv)
    if rc != 0:
        return _err(
            "run_job_failed",
            f"run_job returned {rc}; see job_state.json / stderr for details.",
        )

    final_srt = jw / "artifacts" / "translate" / "final_subtitle.srt"
    render_dir = jw / "artifacts" / "render"
    return _ok(
        {
            "final_subtitle_path": str(final_srt.resolve()) if final_srt.is_file() else None,
            "render_dir": str(render_dir.resolve()) if render_dir.is_dir() else None,
            "to_stage": ns.to_stage,
        }
    )


def _cmd_preflight(ns: argparse.Namespace) -> int:
    report = build_preflight_report(
        job_workspace=(ns.job_workspace or ""),
        translate_backend=ns.translate_backend,
        tts_provider=ns.tts_provider,
        api_key=ns.api_key,
        require_download=bool(ns.require_download),
        require_input=bool(ns.require_input),
        require_render=bool(ns.require_render),
        require_long_video=bool(ns.require_long_video),
    )
    if report["ok"]:
        return _ok(report)
    _emit({"ok": False, "error": {"code": "preflight_failed", "message": "Preflight checks failed."}, "data": report})
    return 1


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="engine.app_cli",
        description="Single-video workflow orchestrator for UI (Phase 3).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sp_init = sub.add_parser("init-job", help="Create a job workspace from a video path.")
    sp_init.add_argument("--video", required=True, help="Path to input video file.")
    sp_init.add_argument(
        "--workspace-root",
        required=True,
        help="Parent directory under which <job_id>/ workspace is created.",
    )
    sp_init.add_argument("--job-id", default="", help="Optional job id; defaults to a slug of the video filename.")
    sp_init.add_argument("--force", action="store_true", help="Reuse existing non-empty workspace.")
    sp_init.set_defaults(func=_cmd_init_job)

    sp_probe = sub.add_parser("probe-video-url", help="Probe a remote video URL via yt-dlp.")
    sp_probe.add_argument("--url", required=True)
    sp_probe.set_defaults(func=_cmd_probe_video_url)

    sp_init_url = sub.add_parser(
        "init-job-from-url",
        help="Download a remote video via yt-dlp and create a job workspace.",
    )
    sp_init_url.add_argument("--url", required=True)
    sp_init_url.add_argument("--workspace-root", required=True)
    sp_init_url.add_argument("--job-id", default="")
    sp_init_url.add_argument("--force", action="store_true")
    sp_init_url.set_defaults(func=_cmd_init_job_from_url)

    sp_until = sub.add_parser(
        "run-until-edit",
        help="Transcribe + translate (block_v2) + seed edited_voice.srt; stop at voice_edit_pending.",
    )
    sp_until.add_argument("--job-workspace", required=True)
    sp_until.add_argument("--project-name", required=True)
    sp_until.add_argument("--api-key", default="")
    sp_until.add_argument(
        "--translate-backend",
        default="block_v2",
        choices=["legacy", "block_v2"],
        help="block_v2 is required to produce translated_voice.srt (default).",
    )
    sp_until.add_argument("--enable-translation-qa", action="store_true")
    sp_until.add_argument("--enable-source-cleanup", action="store_true")
    sp_until.set_defaults(func=_cmd_run_until_edit)

    sp_after = sub.add_parser(
        "run-after-edit",
        help="Mark voice_edited + finalize(voice) + TTS + align + mix + render.",
    )
    sp_after.add_argument("--job-workspace", required=True)
    sp_after.add_argument("--project-name", required=True)
    sp_after.add_argument("--api-key", default="")
    sp_after.add_argument("--to-stage", default="rendered", choices=run_job.STAGE_ORDER)
    sp_after.add_argument(
        "--translate-backend",
        default="block_v2",
        choices=["legacy", "block_v2"],
    )
    sp_after.add_argument("--tts-provider", default="edge_tts")
    sp_after.add_argument("--tts-voice", default="")
    sp_after.add_argument(
        "--mix-mode",
        default="replace_original_speech",
        choices=["replace_original_speech", "duck_original_speech"],
    )
    sp_after.set_defaults(func=_cmd_run_after_edit)

    sp_preflight = sub.add_parser(
        "preflight",
        help="Runtime doctor: check backend dependencies and workspace readiness.",
    )
    sp_preflight.add_argument("--job-workspace", default="")
    sp_preflight.add_argument(
        "--translate-backend",
        default="block_v2",
        choices=["legacy", "block_v2"],
    )
    sp_preflight.add_argument("--tts-provider", default="edge_tts")
    sp_preflight.add_argument("--api-key", default="")
    sp_preflight.add_argument("--require-download", action="store_true")
    sp_preflight.add_argument("--require-input", action="store_true")
    sp_preflight.add_argument("--require-render", action="store_true")
    sp_preflight.add_argument("--require-long-video", action="store_true")
    sp_preflight.set_defaults(func=_cmd_preflight)

    sp_doctor = sub.add_parser(
        "doctor",
        help="Alias of preflight for production-style runtime checks.",
    )
    sp_doctor.add_argument("--job-workspace", default="")
    sp_doctor.add_argument(
        "--translate-backend",
        default="block_v2",
        choices=["legacy", "block_v2"],
    )
    sp_doctor.add_argument("--tts-provider", default="edge_tts")
    sp_doctor.add_argument("--api-key", default="")
    sp_doctor.add_argument("--require-download", action="store_true")
    sp_doctor.add_argument("--require-input", action="store_true")
    sp_doctor.add_argument("--require-render", action="store_true")
    sp_doctor.add_argument("--require-long-video", action="store_true")
    sp_doctor.set_defaults(func=_cmd_preflight)

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
