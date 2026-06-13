"""
Task 3A: minimal translate-stage orchestrator for one job workspace.
Invokes engine.translate_cli via subprocess (no duplicate translation logic).
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from engine.runtime_app_settings import resolve_openai_translation_model
from engine.subtitle_text import normalize_subtitle_file_utf8

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Canonical auto-translate output (docs/03_job_contract.md)
TRANSLATED_AUTO_FILENAME = "translated_auto.srt"
TRANSLATED_VOICE_FILENAME = "translated_voice.srt"
LEGACY_TRANSLATED_FILENAME = "translated.srt"


def _default_job_id(job_workspace: Path) -> str:
    return job_workspace.name


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run translate stage for a job workspace (calls engine.translate_cli)."
    )
    p.add_argument(
        "--job-workspace",
        required=True,
        help="Root directory of the job (contains artifacts/).",
    )
    p.add_argument(
        "--job-id",
        default="",
        help="Stable job id for job_state.json (default: last segment of job-workspace).",
    )
    p.add_argument("--api-key", default="", help="OpenAI API key (optional if OPENAI_API_KEY is set).")
    p.add_argument("--project-name", required=True, help="Legacy project name (ProjectMemoryStore slug).")
    p.add_argument("--model", default=resolve_openai_translation_model())
    p.add_argument(
        "--backend",
        default="legacy",
        choices=["legacy", "block_v2"],
        help="Translation backend (default legacy). block_v2 enables block-based 2-pass translation.",
    )
    p.add_argument("--target-language", default="Vietnamese")
    p.add_argument(
        "--mode",
        default="translate",
        choices=["translate", "rewrite_pov", "translate_then_rewrite"],
    )
    p.add_argument(
        "--style",
        default="literal",
        choices=["literal", "natural", "subtitle", "novel"],
    )
    p.add_argument("--chunk-unit-count", type=int, default=30)
    p.add_argument("--block-size", type=int, default=12, help="block_v2: cues per block (8–20 recommended).")
    p.add_argument("--block-context-cues", type=int, default=2, help="block_v2: context cues before/after.")
    p.add_argument(
        "--glossary-path",
        default=str((Path(__file__).resolve().parent / "translation_glossary.json").resolve()),
        help="block_v2: path to glossary JSON.",
    )
    p.add_argument("--enable-qa-manifest", action="store_true", help="block_v2: write translation_qa.json.")
    p.add_argument(
        "--project-mode",
        default="new",
        choices=["new", "existing"],
        help="Maps to translate_cli --project-mode.",
    )
    p.add_argument(
        "--existing-project-dir",
        default="",
        help="Required when --project-mode=existing.",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Pass --quiet to translate_cli (suppress pipeline logs on stderr).",
    )
    p.add_argument(
        "--source-mode",
        default="raw",
        choices=["raw", "cleaned"],
        help="Transcribe input: raw=artifacts/transcribe/source.srt; cleaned=source_cleaned_zh.srt.",
    )
    return p.parse_args(argv)


def _load_existing_state(job_workspace: Path) -> dict:
    p = job_workspace / "job_state.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_job_state(job_workspace: Path, updates: dict) -> None:
    path = job_workspace / "job_state.json"
    base = _load_existing_state(job_workspace)
    base.update(updates)
    write_json_atomic(path, base)


def _merge_runner_field(job_workspace: Path, key: str, value) -> None:
    base = _load_existing_state(job_workspace)
    runner = dict(base.get("runner") or {})
    runner[key] = value
    _write_job_state(job_workspace, {"runner": runner})


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
    base.update(data)
    write_json_atomic(p, base)


def _note_video_state_failure(job_workspace: Path, job_id: str, last_error: str) -> None:
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "failed",
            "current_stage": "translate_failed",
            "last_error": last_error,
        },
    )


def _migrate_legacy_translated_srt(translate_dir: Path) -> None:
    """If only legacy translated.srt exists, copy to translated_auto.srt (docs compatibility)."""
    auto = translate_dir / TRANSLATED_AUTO_FILENAME
    legacy = translate_dir / LEGACY_TRANSLATED_FILENAME
    if legacy.is_file() and not auto.is_file():
        shutil.copy2(legacy, auto)
        normalize_subtitle_file_utf8(auto, "translate_stage")


def _failure_state(
    job_id: str,
    job_workspace: Path,
    translate_result_path: Path,
    last_error: str,
) -> dict:
    return {
        "job_id": job_id,
        "job_workspace": str(job_workspace),
        "status": "failed",
        "current_stage": "translate_failed",
        "translate_result_path": str(translate_result_path),
        "translated_output_path": None,
        "translated_auto_srt_path": None,
        "project_dir": None,
        "project_memory_dir": None,
        "review_count": None,
        "total_units": None,
        "failed_chunks": None,
        "last_error": last_error,
    }


def _success_state(
    job_id: str,
    job_workspace: Path,
    translate_result_path: Path,
    tr: dict,
) -> dict:
    out = tr.get("output_path") or ""
    return {
        "job_id": job_id,
        "job_workspace": str(job_workspace),
        # Keep 'translated' keys for legacy readers; promote 'translated_ready' as the new stable stage.
        "status": "translated_ready",
        "current_stage": "translated_ready",
        "translated_status": "translated",
        "translate_result_path": str(translate_result_path),
        "translated_output_path": out,
        "translated_auto_srt_path": out,
        "artifacts_contract": "video_v1",
        "project_dir": tr.get("project_dir"),
        "project_memory_dir": tr.get("project_memory_dir"),
        "review_count": tr.get("review_count"),
        "total_units": tr.get("total_units"),
        "failed_chunks": tr.get("failed_chunks"),
        "last_error": None,
    }


def _parse_translate_stdout(stdout: str) -> dict | None:
    raw = (stdout or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    job_workspace = Path(ns.job_workspace).expanduser().resolve()
    job_id = (ns.job_id or "").strip() or _default_job_id(job_workspace)

    if ns.project_mode == "existing" and not (ns.existing_project_dir or "").strip():
        err = 'project_mode is "existing" but --existing-project-dir is empty.'
        translate_dir = job_workspace / "artifacts" / "translate"
        translate_dir.mkdir(parents=True, exist_ok=True)
        result_json_path = translate_dir / "result.json"
        _write_job_state(
            job_workspace,
            _failure_state(job_id, job_workspace, result_json_path, err),
        )
        _note_video_state_failure(job_workspace, job_id, err)
        print(err, file=sys.stderr)
        return 1

    source_srt_raw = job_workspace / "artifacts" / "transcribe" / "source.srt"
    source_srt_cleaned = job_workspace / "artifacts" / "transcribe" / "source_cleaned_zh.srt"
    sm = (ns.source_mode or "raw").strip().lower()
    if sm == "cleaned":
        if not source_srt_cleaned.is_file():
            err = (
                f"Missing cleaned source for --source-mode cleaned: {source_srt_cleaned}. "
                "Run: python -m engine.run_cleanup_source_stage --job-workspace <path>"
            )
            translate_dir = job_workspace / "artifacts" / "translate"
            translate_dir.mkdir(parents=True, exist_ok=True)
            result_json_path = translate_dir / "result.json"
            _write_job_state(
                job_workspace,
                _failure_state(job_id, job_workspace, result_json_path, err),
            )
            _note_video_state_failure(job_workspace, job_id, err)
            print(err, file=sys.stderr)
            return 1
        translate_input_srt = source_srt_cleaned
    else:
        translate_input_srt = source_srt_raw

    translate_dir = job_workspace / "artifacts" / "translate"
    result_json_path = translate_dir / "result.json"
    translated_auto_srt = translate_dir / TRANSLATED_AUTO_FILENAME
    translated_voice_srt = translate_dir / TRANSLATED_VOICE_FILENAME
    translation_qa_path = translate_dir / "translation_qa.json"

    translate_dir.mkdir(parents=True, exist_ok=True)
    _migrate_legacy_translated_srt(translate_dir)

    if not translate_input_srt.is_file():
        err = f"Missing canonical input: {translate_input_srt}"
        _write_job_state(
            job_workspace,
            _failure_state(job_id, job_workspace, result_json_path, err),
        )
        _note_video_state_failure(job_workspace, job_id, err)
        print(err, file=sys.stderr)
        return 1

    print(
        f"[translate] source_mode={sm} input={translate_input_srt}",
        file=sys.stderr,
    )

    # New backend: block-based 2-pass translation with optional QA manifest.
    if ns.backend == "block_v2":
        try:
            from engine.block_translate import (
                BlockTranslateError,
                translate_blocks_two_pass,
                write_translation_outputs,
            )
            from engine.subtitle_text import read_subtitle_file
            from engine.srt_cues import parse_srt_cues
        except Exception as e:
            msg = f"block_v2 backend unavailable: {e}"
            _write_job_state(job_workspace, _failure_state(job_id, job_workspace, result_json_path, msg))
            _note_video_state_failure(job_workspace, job_id, msg)
            print(msg, file=sys.stderr)
            return 1

        api_key = (ns.api_key or os.environ.get("OPENAI_API_KEY", "") or "").strip()
        # Managed mode: the platform backend holds the OpenAI key and meters
        # tokens (block_translate routes the call through account().translate),
        # so a local key isn't required. Mirrors run_cleanup_source_stage.
        managed = False
        try:
            from desktop.cloud_account import managed_enabled

            managed = managed_enabled()
        except Exception:  # noqa: BLE001
            managed = False
        if not api_key and not managed:
            msg = "Missing API key: set --api-key or OPENAI_API_KEY (required for block_v2)."
            _write_job_state(job_workspace, _failure_state(job_id, job_workspace, result_json_path, msg))
            _note_video_state_failure(job_workspace, job_id, msg)
            print(msg, file=sys.stderr)
            return 1

        try:
            src_text = read_subtitle_file(translate_input_srt).text
            cues = parse_srt_cues(src_text)
            if not cues:
                raise RuntimeError("No cues parsed from translate input SRT")
        except Exception as e:
            msg = f"Failed reading/parsing translate input for block_v2: {e}"
            _write_job_state(job_workspace, _failure_state(job_id, job_workspace, result_json_path, msg))
            _note_video_state_failure(job_workspace, job_id, msg)
            print(msg, file=sys.stderr)
            return 1

        n_cues = len(cues)
        block_sz = max(8, min(24, int(ns.block_size)))
        if n_cues >= 350:
            block_sz = max(block_sz, 18)
        if n_cues >= 650:
            block_sz = max(block_sz, 20)
        if n_cues >= 1000:
            block_sz = max(block_sz, 22)
        block_sz = min(24, block_sz)
        if block_sz != int(ns.block_size):
            print(
                f"[translate] block_v2 cue_count={n_cues} -> using block_size={block_sz} "
                f"(CLI default was {int(ns.block_size)}) to reduce API round-trips on long subtitles.",
                file=sys.stderr,
                flush=True,
            )
        else:
            print(
                f"[translate] block_v2 cue_count={n_cues} block_size={block_sz} "
                f"context_cues={int(ns.block_context_cues)} (~{max(1, (n_cues + block_sz - 1) // block_sz)} blocks, "
                "2 API calls per block for translate+polish).",
                file=sys.stderr,
                flush=True,
            )

        try:
            results, qa_items, meta = translate_blocks_two_pass(
                cues=cues,
                api_key=api_key,
                model=ns.model,
                glossary_path=Path(ns.glossary_path).expanduser(),
                block_size=block_sz,
                context_cues=int(ns.block_context_cues),
                qa_enabled=bool(ns.enable_qa_manifest),
            )
            from engine.voice_pronoun_normalize import (
                DEFAULT_BLOCK_GAP_MS,
                merge_pronoun_qa_into_per_cue_qa,
                normalize_voice_pronouns_in_blocks,
                pronoun_blocks_to_json,
            )

            pron_res = normalize_voice_pronouns_in_blocks(
                cues, {idx: res.voice for idx, res in results.items()}
            )
            results = {
                idx: replace(
                    res,
                    voice=(pron_res.text_by_index.get(int(idx)) or res.voice).strip(),
                )
                for idx, res in results.items()
            }
            write_translation_outputs(
                out_display_srt=translated_auto_srt,
                out_voice_srt=translated_voice_srt,
                cues=cues,
                results=results,
            )
            if ns.enable_qa_manifest:
                qa_rows = [
                    {
                        "index": int(it.index),
                        "flags": list(it.flags),
                        "needs_review": bool(it.needs_review),
                        "score": float(it.score),
                        "details": dict(it.details),
                    }
                    for it in qa_items
                ]
                qa_rows = merge_pronoun_qa_into_per_cue_qa(qa_rows, pron_res.cue_flags)
                qa_body = {
                    "version": 1,
                    "status": "ok",
                    "backend": "block_v2",
                    "model": ns.model,
                    "qa": qa_rows,
                    "meta": meta,
                    "pronoun_pass": {
                        "version": 1,
                        "block_gap_ms": DEFAULT_BLOCK_GAP_MS,
                        "blocks": pronoun_blocks_to_json(pron_res.blocks),
                    },
                }
                translation_qa_path.write_text(
                    json.dumps(qa_body, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

            tr = {
                "success": True,
                "output_path": str(translated_auto_srt.resolve()),
                "translated_voice_srt_path": str(translated_voice_srt.resolve()),
                "backend": "block_v2",
                "model": ns.model,
                "meta": meta,
                "translate_source_mode": sm,
                "translate_input_srt_path": str(translate_input_srt.resolve()),
            }
            write_json_atomic(result_json_path, tr)
        except BlockTranslateError as e:
            msg = str(e)
            _write_job_state(job_workspace, _failure_state(job_id, job_workspace, result_json_path, msg))
            _note_video_state_failure(job_workspace, job_id, msg)
            print(msg, file=sys.stderr)
            return 1
        except Exception as e:
            msg = f"block_v2 translation failed: {e}"
            _write_job_state(job_workspace, _failure_state(job_id, job_workspace, result_json_path, msg))
            _note_video_state_failure(job_workspace, job_id, msg)
            print(msg, file=sys.stderr)
            return 1

        base_state = _success_state(job_id, job_workspace, result_json_path, tr)
        base_state["translate_source_mode"] = sm
        base_state["voice_edit_status"] = "voice_edit_pending"
        _write_job_state(job_workspace, base_state)
        _merge_runner_field(job_workspace, "translate_source_mode", sm)
        normalize_subtitle_file_utf8(translated_auto_srt, "translate_stage")
        normalize_subtitle_file_utf8(translated_voice_srt, "translate_stage")
        auto_resolved = str(translated_auto_srt.resolve())
        voice_resolved = str(translated_voice_srt.resolve())
        _write_video_state(
            job_workspace,
            {
                "video_id": job_id,
                "translate_path": "auto",
                "current_stage": "translated_ready",
                "status": "translated_ready",
                "translated_status": "translated",
                "voice_edit_status": "voice_edit_pending",
                "last_error": None,
                "artifact_paths": {
                    "source_srt": str(translate_input_srt.resolve()),
                    "translated_auto_srt": auto_resolved,
                    "translated_voice_srt": voice_resolved,
                    "translated_manual_srt": None,
                    "edited_srt": None,
                    "final_subtitle_srt": None,
                },
            },
        )
        return 0

    cmd: list[str] = [
        sys.executable,
        "-m",
        "engine.translate_cli",
        "--input-file",
        str(translate_input_srt),
        "--output-json",
        str(result_json_path),
        "--copy-output",
        str(translated_auto_srt),
        "--project-name",
        ns.project_name,
        "--model",
        ns.model,
        "--target-language",
        ns.target_language,
        "--mode",
        ns.mode,
        "--style",
        ns.style,
        "--chunk-unit-count",
        str(ns.chunk_unit_count),
        "--project-mode",
        ns.project_mode,
    ]
    if ns.api_key.strip():
        cmd.extend(["--api-key", ns.api_key.strip()])
    if ns.project_mode == "existing" and ns.existing_project_dir.strip():
        cmd.extend(["--existing-project-dir", ns.existing_project_dir.strip()])
    if ns.quiet:
        cmd.append("--quiet")

    env = os.environ.copy()
    proc = subprocess.run(
        cmd,
        cwd=str(_REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    tr: dict | None = None
    if result_json_path.is_file():
        try:
            tr = json.loads(result_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            tr = None
    if tr is None:
        tr = _parse_translate_stdout(proc.stdout or "")

    if tr is None:
        tail = (proc.stderr or "")[-4000:]
        msg = f"Could not parse translate result (exit {proc.returncode}). stderr tail: {tail}"
        _write_job_state(
            job_workspace,
            _failure_state(job_id, job_workspace, result_json_path, msg),
        )
        _note_video_state_failure(job_workspace, job_id, msg)
        print(msg, file=sys.stderr)
        return 1

    ok = bool(tr.get("success")) and proc.returncode == 0
    if not ok:
        code = tr.get("error_code", "UNKNOWN")
        msg = tr.get("message", "translate stage failed")
        detail = tr.get("detail", "")
        last_error = f"[{code}] {msg}"
        if detail:
            d = detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False)
            last_error = f"{last_error} | {d[:8000]}"
        _write_job_state(
            job_workspace,
            _failure_state(job_id, job_workspace, result_json_path, last_error),
        )
        _note_video_state_failure(job_workspace, job_id, last_error)
        print(last_error, file=sys.stderr)
        return 1

    base_ok = _success_state(job_id, job_workspace, result_json_path, tr)
    base_ok["translate_source_mode"] = sm
    if isinstance(tr, dict):
        tr["translate_source_mode"] = sm
        tr["translate_input_srt_path"] = str(translate_input_srt.resolve())
        try:
            result_json_path.write_text(
                json.dumps(tr, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass
    _write_job_state(job_workspace, base_ok)
    _merge_runner_field(job_workspace, "translate_source_mode", sm)
    for name in (TRANSLATED_AUTO_FILENAME, LEGACY_TRANSLATED_FILENAME):
        normalize_subtitle_file_utf8(translate_dir / name, "translate_stage")
    auto_resolved = str(translated_auto_srt.resolve())
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "translate_path": "auto",
                "current_stage": "translated_ready",
                "status": "translated_ready",
                "translated_status": "translated",
            "last_error": None,
            "artifact_paths": {
                "source_srt": str(translate_input_srt.resolve()),
                "translated_auto_srt": auto_resolved,
                "translated_voice_srt": None,
                "translated_manual_srt": None,
                "edited_srt": None,
                "final_subtitle_srt": None,
            },
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
