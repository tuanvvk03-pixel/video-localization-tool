"""
Clean Chinese ASR subtitles: artifacts/transcribe/source.srt -> source_cleaned_zh.srt (does not overwrite source.srt).
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import argparse
import json
import os
import sys
import time
from pathlib import Path

from engine.block_translate import render_srt
from engine.cleanup_source_zh import CleanupSourceZHError, cleanup_zh_cues_in_blocks
from engine.runtime_app_settings import resolve_openai_translation_model
from engine.srt_cues import parse_srt_cues
from engine.subtitle_text import log_subtitle_read_issues, read_subtitle_file, write_subtitle_file_utf8

SOURCE_SRT_REL = Path("artifacts") / "transcribe" / "source.srt"
CLEANED_SRT_REL = Path("artifacts") / "transcribe" / "source_cleaned_zh.srt"
MANIFEST_REL = Path("artifacts") / "transcribe" / "source_cleanup_manifest.json"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Clean Chinese source.srt ASR into source_cleaned_zh.srt (OpenAI)."
    )
    p.add_argument("--job-workspace", required=True)
    p.add_argument("--api-key", default="", help="Or set OPENAI_API_KEY.")
    p.add_argument("--model", default=resolve_openai_translation_model())
    p.add_argument("--block-size", type=int, default=12, help="Cues per block (8–20).")
    p.add_argument("--block-context-cues", type=int, default=2)
    return p.parse_args(argv)


def _rel_posix(path: Path, job_workspace: Path) -> str:
    try:
        return path.resolve().relative_to(job_workspace.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


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


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    job_workspace = Path(ns.job_workspace).expanduser().resolve()
    job_id = job_workspace.name

    source_srt = job_workspace / SOURCE_SRT_REL
    cleaned_srt = job_workspace / CLEANED_SRT_REL
    manifest_path = job_workspace / MANIFEST_REL
    transcribe_dir = job_workspace / "artifacts" / "transcribe"
    transcribe_dir.mkdir(parents=True, exist_ok=True)

    if not source_srt.is_file():
        print(f"[cleanup_source] Missing {source_srt}", file=sys.stderr)
        return 1

    api_key = (ns.api_key or os.environ.get("OPENAI_API_KEY", "") or "").strip()
    # In managed mode the server holds the key (cleanup routes through the cloud),
    # so a local key isn't required.
    managed = False
    try:
        from desktop.cloud_account import managed_enabled

        managed = managed_enabled()
    except Exception:  # noqa: BLE001
        managed = False
    if not api_key and not managed:
        print("[cleanup_source] Missing API key: --api-key or OPENAI_API_KEY", file=sys.stderr)
        return 1

    try:
        sub = read_subtitle_file(source_srt)
        log_subtitle_read_issues(
            sub, stage_tag="cleanup_source", path_display=str(source_srt.resolve())
        )
        cues = parse_srt_cues(sub.text)
    except Exception as e:
        print(f"[cleanup_source] Failed to read/parse source.srt: {e}", file=sys.stderr)
        return 1

    if not cues:
        print("[cleanup_source] No cues in source.srt", file=sys.stderr)
        return 1

    bs = max(8, min(20, int(ns.block_size)))
    try:
        results, meta = cleanup_zh_cues_in_blocks(
            cues=cues,
            api_key=api_key,
            model=ns.model,
            block_size=bs,
            context_cues=int(ns.block_context_cues),
        )
    except CleanupSourceZHError as e:
        print(f"[cleanup_source] {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[cleanup_source] Cleanup failed: {e}", file=sys.stderr)
        return 1

    text_by_index = {int(r.index): r.cleaned_text for r in results}
    srt_body = render_srt(cues, text_by_index)
    try:
        write_subtitle_file_utf8(cleaned_srt, srt_body)
    except OSError as e:
        print(f"[cleanup_source] Could not write cleaned SRT: {e}", file=sys.stderr)
        return 1

    changed_n = sum(1 for r in results if r.changed)
    qa_summary = {
        "changed_count": changed_n,
        "low_confidence_count": sum(1 for r in results if r.low_confidence),
        "suspicious_asr_count": sum(1 for r in results if r.suspicious_asr),
        "heavy_rewrite_count": sum(1 for r in results if r.heavy_rewrite),
        "likely_numeric_fix_count": sum(1 for r in results if r.likely_numeric_fix),
    }

    manifest_body = {
        "version": 1,
        "language": "zh",
        "model": ns.model,
        "source_path": _rel_posix(source_srt, job_workspace),
        "cleaned_path": _rel_posix(cleaned_srt, job_workspace),
        "cue_count": len(results),
        "block_count": meta.get("block_count", 0),
        "qa_summary": qa_summary,
        "meta": meta,
        "cues": [
            {
                "index": r.index,
                "raw_text": r.raw_text,
                "cleaned_text": r.cleaned_text,
                "changed": r.changed,
                "low_confidence": r.low_confidence,
                "suspicious_asr": r.suspicious_asr,
                "heavy_rewrite": r.heavy_rewrite,
                "likely_numeric_fix": r.likely_numeric_fix,
            }
            for r in results
        ],
        "recorded_at_unix": time.time(),
    }

    try:
        manifest_path.write_text(
            json.dumps(manifest_body, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as e:
        print(f"[cleanup_source] Could not write manifest: {e}", file=sys.stderr)
        return 1

    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "source_cleanup_manifest_path": str(manifest_path.resolve()),
            "source_cleaned_zh_srt_path": str(cleaned_srt.resolve()),
        },
    )

    print(
        f"[cleanup_source] Wrote {cleaned_srt} ({len(results)} cues, changed={changed_n}). "
        f"Manifest: {manifest_path.name}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
