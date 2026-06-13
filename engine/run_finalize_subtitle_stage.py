"""
Pick best subtitle artifact and copy to artifacts/translate/final_subtitle.srt.
display: edited > translated_manual > translated_auto > legacy translated.srt
voice: edited_voice > translated_voice (only while translated_voice.srt exists); else display chain.
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import argparse
import json
import sys
import time
from pathlib import Path

from engine.input_provenance import (
    FINAL_SUBTITLE_MANIFEST_REL,
    build_input_provenance_dict,
    fingerprint_file,
    pick_finalize_source_subtitle,
)
from engine.subtitle_text import copy_subtitle_artifact

TRANSLATED_AUTO_FILENAME = "translated_auto.srt"
TRANSLATED_VOICE_FILENAME = "translated_voice.srt"
LEGACY_TRANSLATED_FILENAME = "translated.srt"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Finalize subtitle: copy best SRT to artifacts/translate/final_subtitle.srt."
    )
    p.add_argument("--job-workspace", required=True, help="Job / video workspace root.")
    p.add_argument(
        "--finalize-mode",
        default="display",
        choices=["display", "voice"],
        help="Select subtitle source policy: display (default) or voice (prefer translated_voice/edited_voice).",
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


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    job_workspace = Path(ns.job_workspace).expanduser().resolve()
    job_id = job_workspace.name

    translate_dir = job_workspace / "artifacts" / "translate"
    translate_dir.mkdir(parents=True, exist_ok=True)
    final_path = translate_dir / "final_subtitle.srt"

    fm = str(ns.finalize_mode or "display")
    src, mode = pick_finalize_source_subtitle(job_workspace, finalize_mode=fm)
    if src is None or mode is None:
        if fm == "voice":
            msg = (
                "No subtitle source found for voice finalize. Expected "
                "artifacts/edit/edited_voice.srt (preferred) or artifacts/translate/translated_voice.srt "
                "(from block_v2 translate); "
                "if translated_voice.srt is missing, display chain: edited.srt, translated_manual.srt, "
                f"{TRANSLATED_AUTO_FILENAME}, or legacy {LEGACY_TRANSLATED_FILENAME}."
            )
        else:
            msg = (
                "No subtitle source found. Expected one of: "
                "artifacts/translate/edited.srt, artifacts/edit/edited.srt, "
                "artifacts/translate/translated_manual.srt, "
                f"artifacts/translate/{TRANSLATED_AUTO_FILENAME}, "
                f"or legacy artifacts/translate/{LEGACY_TRANSLATED_FILENAME}."
            )
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "final_subtitle_path": None,
                "subtitle_source_mode": None,
                "status": "blocked",
                "current_stage": "finalize_subtitle_required",
                "last_error": msg,
            },
        )
        _write_video_state(
            job_workspace,
            {
                "video_id": job_id,
                "status": "blocked",
                "current_stage": "finalize_subtitle_required",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1

    try:
        cr = copy_subtitle_artifact(src, final_path, stage_tag="finalize_subtitle")
    except OSError as e:
        msg = f"Finalize copy failed: {e}"
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "failed",
                "current_stage": "finalize_subtitle_failed",
                "last_error": msg,
            },
        )
        _write_video_state(
            job_workspace,
            {
                "video_id": job_id,
                "status": "failed",
                "current_stage": "finalize_subtitle_failed",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1
    final_resolved = str(final_path.resolve())
    src_resolved = str(src.resolve())
    print(
        f"[finalize_subtitle] Copy {src_resolved} -> {final_resolved} (binary_copy={cr.used_binary_copy}).",
        file=sys.stderr,
    )

    prov = build_input_provenance_dict(job_workspace, finalize_mode=fm)
    fin_fp = fingerprint_file(src)
    if fin_fp:
        prov["finalize_source_subtitle"] = fin_fp
    manifest_path = job_workspace / FINAL_SUBTITLE_MANIFEST_REL
    manifest_body = {
        "version": 1,
        "finalize_mode": fm,
        "selected_source_subtitle_path": src_resolved,
        "input_provenance": prov,
        "recorded_at_unix": time.time(),
    }
    try:
        manifest_path.write_text(
            json.dumps(manifest_body, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as e:
        msg = f"Could not write final subtitle manifest: {e}"
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "failed",
                "current_stage": "finalize_subtitle_failed",
                "last_error": msg,
            },
        )
        _write_video_state(
            job_workspace,
            {
                "video_id": job_id,
                "status": "failed",
                "current_stage": "finalize_subtitle_failed",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1

    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "final_subtitle_path": final_resolved,
            "subtitle_source_mode": mode,
            "status": "final_subtitle_ready",
            "current_stage": "subtitle_finalized",
            "last_error": None,
        },
    )

    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "current_stage": "subtitle_finalized",
            "status": "final_subtitle_ready",
            "last_error": None,
            "subtitle_source_mode": mode,
            "artifact_paths": {
                "final_subtitle_srt": final_resolved,
                "final_subtitle_manifest": str(manifest_path.resolve()),
            },
            "finalize_source_srt": src_resolved,
        },
    )

    print(
        f"[finalize_subtitle] Copied {src_resolved} -> {final_resolved} (mode={mode}).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
