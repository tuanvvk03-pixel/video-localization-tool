"""
Headless CLI: invoke legacy TranslationPipelineV43 per docs/03_job_contract.md.
Does not import legacy until CWD is legacy/dich_v4/dich.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import traceback
from pathlib import Path

from engine.runtime_app_settings import resolve_openai_translation_model

# Repo root = parent of the `engine/` package directory
_REPO_ROOT = Path(__file__).resolve().parent.parent
_LEGACY_ROOT = _REPO_ROOT / "legacy" / "dich_v4" / "dich"


def _legacy_root() -> Path:
    return _LEGACY_ROOT


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run legacy translate pipeline (TranslationPipelineV43) without GUI."
    )
    p.add_argument(
        "--input-file",
        required=True,
        help="Path to source .srt or .txt (ProcessOptions.input_file).",
    )
    p.add_argument(
        "--api-key",
        default=os.environ.get("OPENAI_API_KEY", ""),
        help="OpenAI API key (default: env OPENAI_API_KEY).",
    )
    p.add_argument("--model", default=resolve_openai_translation_model())
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
    p.add_argument(
        "--target-pov",
        default="first_person",
        choices=["first_person", "third_person"],
    )
    p.add_argument("--chunk-unit-count", type=int, default=30)
    p.add_argument("--project-mode", default="new", choices=["new", "existing"])
    p.add_argument("--project-name", default="")
    p.add_argument("--existing-project-dir", default="")

    for name, default in [
        ("enable-cache", True),
        ("enable-refine", True),
        ("enable-qa", True),
        ("auto-retry-failed-units", True),
        ("enable-source-repair", True),
        ("repair-only-noisy-lines", True),
        ("mark-unrecoverable-lines", True),
        ("bilingual-output", False),
        ("preserve-names", True),
        ("preserve-line-breaks", True),
    ]:
        arg = f"--{name}"
        no_arg = f"--no-{name}"
        p.add_argument(arg, dest=name.replace("-", "_"), action="store_true")
        p.add_argument(no_arg, dest=name.replace("-", "_"), action="store_false")
        p.set_defaults(**{name.replace("-", "_"): default})

    p.add_argument(
        "--output-json",
        default="",
        help="Write the same JSON object to this file (UTF-8).",
    )
    p.add_argument(
        "--copy-output",
        default="",
        help="After success, copy legacy output file to this path (e.g. artifacts/translate/translated_auto.srt).",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress pipeline progress logs (stderr); JSON still goes to stdout.",
    )
    return p.parse_args(argv)


def _validate_before_run(ns: argparse.Namespace) -> dict | None:
    """Return error payload or None if OK."""
    input_path = Path(ns.input_file).expanduser()
    try:
        input_path = input_path.resolve()
    except OSError as e:
        return {
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "message": f"Invalid input path: {e}",
            "detail": str(ns.input_file),
        }
    if not input_path.is_file():
        return {
            "success": False,
            "error_code": "MISSING_INPUT",
            "message": "Input file does not exist or is not a file.",
            "detail": str(input_path),
        }

    api_key = (ns.api_key or "").strip()
    if not api_key:
        return {
            "success": False,
            "error_code": "INVOCATION_ERROR",
            "message": "Missing API key: set --api-key or OPENAI_API_KEY.",
            "detail": "",
        }

    if ns.project_mode == "new":
        if not (ns.project_name or "").strip():
            return {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": 'project_mode is "new" but --project-name is empty.',
                "detail": "",
            }
    else:
        ep = (ns.existing_project_dir or "").strip()
        if not ep:
            return {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": 'project_mode is "existing" but --existing-project-dir is empty.',
                "detail": "",
            }
        ep_path = Path(ep).expanduser().resolve()
        if not ep_path.is_dir():
            return {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": "existing_project_dir is not a directory.",
                "detail": str(ep_path),
            }

    return None


def _build_options_dict(ns: argparse.Namespace, input_file_resolved: str) -> dict:
    existing = (ns.existing_project_dir or "").strip()
    if ns.project_mode == "existing" and existing:
        existing = str(Path(existing).expanduser().resolve())

    return {
        "api_key": (ns.api_key or "").strip(),
        "model": ns.model,
        "input_file": input_file_resolved,
        "target_language": ns.target_language,
        "mode": ns.mode,
        "style": ns.style,
        "target_pov": ns.target_pov,
        "chunk_unit_count": ns.chunk_unit_count,
        "project_mode": ns.project_mode,
        "project_name": (ns.project_name or "").strip(),
        "existing_project_dir": existing,
        "enable_cache": ns.enable_cache,
        "enable_refine": ns.enable_refine,
        "enable_qa": ns.enable_qa,
        "auto_retry_failed_units": ns.auto_retry_failed_units,
        "enable_source_repair": ns.enable_source_repair,
        "repair_only_noisy_lines": ns.repair_only_noisy_lines,
        "mark_unrecoverable_lines": ns.mark_unrecoverable_lines,
        "bilingual_output": ns.bilingual_output,
        "preserve_names": ns.preserve_names,
        "preserve_line_breaks": ns.preserve_line_breaks,
    }


def _run_in_legacy_cwd(ns: argparse.Namespace) -> dict:
    """Returns success or failure contract dict."""
    err = _validate_before_run(ns)
    if err is not None:
        return err

    input_resolved = str(Path(ns.input_file).expanduser().resolve())

    legacy = _legacy_root()
    if not legacy.is_dir():
        return {
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "message": "Legacy package directory not found.",
            "detail": str(legacy),
        }

    old_cwd = Path.cwd()
    inserted = False
    try:
        os.chdir(legacy)
        root_str = str(legacy)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)
            inserted = True

        from core.models import ProcessOptions  # noqa: PLC0415 — after chdir
        from core.pipeline import TranslationPipelineV43  # noqa: PLC0415

        try:
            options = ProcessOptions(**_build_options_dict(ns, input_resolved))
        except Exception as e:  # pydantic ValidationError etc.
            return {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid ProcessOptions.",
                "detail": str(e),
            }

        logger = (lambda _m: None) if ns.quiet else (lambda m: print(m, file=sys.stderr))
        pipeline = TranslationPipelineV43(options, logger=logger)
        try:
            raw = pipeline.run()
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            return {
                "success": False,
                "error_code": "PIPELINE_ERROR",
                "message": str(e),
                "detail": traceback.format_exc(),
            }

        failed = raw.get("failed_chunks", [])
        if not isinstance(failed, list):
            failed = list(failed) if failed is not None else []

        legacy_out = str(raw["output_path"])
        return {
            "success": True,
            "output_path": legacy_out,
            "legacy_output_path": legacy_out,
            "project_dir": raw["project_dir"],
            "project_memory_dir": raw["project_memory_dir"],
            "review_count": int(raw.get("review_count", 0)),
            "total_units": int(raw.get("total_units", 0)),
            "failed_chunks": failed,
        }
    finally:
        try:
            os.chdir(old_cwd)
        except OSError:
            # Avoid masking pipeline errors if restoring CWD fails (e.g. drive unavailable).
            pass
        if inserted:
            try:
                sys.path.remove(root_str)
            except ValueError:
                pass


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    try:
        result = _run_in_legacy_cwd(ns)
    except BaseException as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        result = {
            "success": False,
            "error_code": "PIPELINE_ERROR",
            "message": str(e),
            "detail": traceback.format_exc(),
        }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)

    if ns.output_json:
        out_path = Path(ns.output_json).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")

    if result.get("success") and ns.copy_output:
        src = Path(result["legacy_output_path"])
        dst = Path(ns.copy_output).expanduser()
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        result["output_path"] = str(dst.resolve())

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
