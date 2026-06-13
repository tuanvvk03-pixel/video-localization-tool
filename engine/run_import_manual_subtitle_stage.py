"""
Stub: copy user-provided SRT to artifacts/translate/translated_manual.srt (manual translation path).
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import argparse
import json
import sys
from pathlib import Path

from engine.subtitle_text import copy_subtitle_artifact


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Import manual translated SRT into job workspace (translated_manual.srt)."
    )
    p.add_argument("--job-workspace", required=True, help="Job / video workspace root.")
    p.add_argument(
        "--manual-srt-path",
        required=True,
        help="Path to the user's translated .srt file.",
    )
    return p.parse_args(argv)


def _load_job_state(job_workspace: Path) -> dict:
    p = job_workspace / "job_state.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _merge_job_state(job_workspace: Path, updates: dict) -> None:
    path = job_workspace / "job_state.json"
    base = _load_job_state(job_workspace)
    base.update(updates)
    write_json_atomic(path, base)


def _load_video_state(job_workspace: Path) -> dict:
    p = job_workspace / "video_state.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_video_state(job_workspace: Path, data: dict) -> None:
    p = job_workspace / "video_state.json"
    base = _load_video_state(job_workspace)
    payload = dict(data)
    inc_ap = payload.pop("artifact_paths", None)
    base.update(payload)
    if inc_ap is not None:
        merged = dict(base.get("artifact_paths") or {})
        merged.update(inc_ap)
        base["artifact_paths"] = merged
    write_json_atomic(p, base)


def _fail(
    job_workspace: Path,
    job_id: str,
    message: str,
) -> None:
    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "translated_manual_srt_path": None,
            "translation_mode": None,
            "status": "failed",
            "current_stage": "manual_subtitle_import_failed",
            "last_error": message,
        },
    )
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "translation_mode": None,
            "translated_manual_srt_path": None,
            "status": "failed",
            "current_stage": "manual_subtitle_import_failed",
            "last_error": message,
        },
    )


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    job_workspace = Path(ns.job_workspace).expanduser().resolve()
    job_id = job_workspace.name

    try:
        manual = Path(ns.manual_srt_path).expanduser().resolve()
    except OSError as e:
        msg = f"Invalid manual SRT path: {e}"
        _fail(job_workspace, job_id, msg)
        print(msg, file=sys.stderr)
        return 1

    if not manual.is_file():
        msg = f"Manual SRT not found or not a file: {manual}"
        _fail(job_workspace, job_id, msg)
        print(msg, file=sys.stderr)
        return 1

    if manual.suffix.lower() != ".srt":
        msg = f"Expected .srt file, got suffix {manual.suffix!r}: {manual}"
        _fail(job_workspace, job_id, msg)
        print(msg, file=sys.stderr)
        return 1

    translate_dir = job_workspace / "artifacts" / "translate"
    translate_dir.mkdir(parents=True, exist_ok=True)
    dest = translate_dir / "translated_manual.srt"

    try:
        cr = copy_subtitle_artifact(manual, dest, stage_tag="import_manual_subtitle")
    except OSError as e:
        msg = f"Copy failed: {e}"
        _fail(job_workspace, job_id, msg)
        print(msg, file=sys.stderr)
        return 1

    dest_resolved = str(dest.resolve())
    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "translated_manual_srt_path": dest_resolved,
            "translation_mode": "manual",
            "status": "manual_subtitle_imported",
            "current_stage": "manual_subtitle_imported",
            "last_error": None,
        },
    )
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "translation_mode": "manual",
            "translated_manual_srt_path": dest_resolved,
            "translate_path": "manual",
            "status": "manual_subtitle_imported",
            "current_stage": "manual_subtitle_imported",
            "last_error": None,
            "artifact_paths": {"translated_manual_srt": dest_resolved},
        },
    )

    print(
        f"[import_manual_subtitle] Copied {manual} -> {dest_resolved} (binary_copy={cr.used_binary_copy}).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
