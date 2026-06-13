"""
Root single-video pipeline runner.

This runner drives the production backend flow from workspace inputs through
`rendered` using file-based orchestration:
transcribe -> optional cleanup zh -> translate -> finalize -> TTS -> align -> mix -> render.

Canonical workspace inputs/outputs:
- input video: input/source.mp4
- transcribe output: artifacts/transcribe/source.srt
- translate output: artifacts/translate/translated_auto.srt
- voice-first edit path: artifacts/translate/translated_voice.srt -> artifacts/edit/edited_voice.srt
- finalized subtitle: artifacts/translate/final_subtitle.srt

Compatibility notes:
- Manual subtitle import still uses dedicated CLIs; run_job keeps auto-translate defaults.
- `done` is kept for CLI compatibility and currently aliases the implemented terminal stage `rendered`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from engine.json_store import write_json_atomic
from engine import (
    run_align_stage,
    run_cleanup_source_stage,
    run_compact_tts_stage,
    run_finalize_subtitle_stage,
    run_mix_stage,
    run_render_stage,
    run_transcribe_stage,
    run_translate_stage,
    run_tts_stage,
)
from engine.bgm_settings import load_bgm_state
from engine.input_provenance import (
    apply_run_job_provenance_gates,
    record_video_fingerprint_if_absent,
)
from engine.srt_cues import parse_srt_cues
from engine.workspace_lock import (
    WorkspaceLockError,
    acquire_workspace_lock,
    describe_lock_details,
)

# `done` is a compatibility alias for the current terminal stage `rendered`.
STAGE_ORDER = [
    "imported",
    "transcribed",
    "translated",
    "subtitle_finalized",
    "tts_generated",
    "aligned",
    "mixed",
    "rendered",
    "done",
]


def _rank(stage: str) -> int:
    return STAGE_ORDER.index(stage)


def _load_state(job_workspace: Path) -> dict:
    p = job_workspace / "job_state.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _merge_job_state(job_workspace: Path, updates: dict) -> None:
    path = job_workspace / "job_state.json"
    base = _load_state(job_workspace)
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


def _merge_video_state(job_workspace: Path, updates: dict) -> None:
    path = job_workspace / "video_state.json"
    base = _load_video_state(job_workspace)
    payload = dict(updates)
    inc_ap = payload.pop("artifact_paths", None)
    base.update(payload)
    if inc_ap is not None:
        merged = dict(base.get("artifact_paths") or {})
        merged.update(dict(inc_ap))
        base["artifact_paths"] = merged
    write_json_atomic(path, base)


def _voice_edit_completed(job_workspace: Path) -> bool:
    """
    Voice-first gate condition:
    - Completed ONLY if state explicitly indicates voice_edited (do not treat the file existence as completed;
      it might only be seeded and not human-edited yet).
    """
    js = _load_state(job_workspace)
    vs = _load_video_state(job_workspace)
    for st in (vs, js):
        if bool(st.get("voice_edited")):
            return True
        if (st.get("voice_edit_status") or "") == "voice_edited":
            return True
    return False


def _block_voice_edit_pending(job_workspace: Path, job_id: str, runner_meta: dict, message: str) -> None:
    edited_voice = job_workspace / "artifacts" / "edit" / "edited_voice.srt"
    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "blocked",
            "current_stage": "voice_edit_pending",
            "voice_edit_status": "voice_edit_pending",
            "last_error": message,
            "required_action": "edit_edited_voice_srt",
            "edited_voice_expected_path": str(edited_voice.resolve()),
            "runner": runner_meta,
        },
    )
    _merge_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "blocked",
            "current_stage": "voice_edit_pending",
            "voice_edit_status": "voice_edit_pending",
            "last_error": message,
            "required_action": "edit_edited_voice_srt",
            "artifact_paths": {"edited_voice_srt": str(edited_voice.resolve())},
        },
    )


def _mark_stage_running(job_workspace: Path, job_id: str, runner_meta: dict, stage: str) -> None:
    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "running",
            "current_stage": stage,
            "last_error": None,
            "runner": runner_meta,
        },
    )
    _merge_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "running",
            "current_stage": stage,
            "last_error": None,
        },
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Root single-video pipeline runner: transcribe/cleanup/translate/finalize/TTS/align/mix/render."
        )
    )
    p.add_argument("--job-workspace", required=True)
    p.add_argument("--api-key", default="", help="Optional; else OPENAI_API_KEY.")
    p.add_argument("--project-name", required=True)
    p.add_argument(
        "--project-root",
        default="",
        help="Optional project root; used by render stage to resolve style/global_subtitle_style.json.",
    )
    p.add_argument(
        "--render-subtitle-mode",
        default="burn",
        choices=["soft", "burn", "none"],
        help="Subtitle mode for final render (soft=mux, burn=hardsub with style, none=no subs).",
    )
    p.add_argument(
        "--render-aspect-ratio",
        default="",
        choices=["", "source", "16:9", "9:16"],
        help="Optional final render aspect ratio override.",
    )
    p.add_argument(
        "--render-background-image",
        default="",
        help="Optional final render background image override.",
    )
    p.add_argument(
        "--from-stage",
        default="imported",
        choices=STAGE_ORDER,
        help="Requested start stage (stored in job_state; v1 uses partially).",
    )
    p.add_argument(
        "--to-stage",
        default="translated",
        choices=STAGE_ORDER,
        help=(
            "Target stage (default translated). `done` is retained for compatibility and currently "
            "maps to the implemented terminal stage `rendered`."
        ),
    )
    p.add_argument(
        "--transcribe-model-size",
        default="medium",
        help="Passed to run_transcribe_stage --model-size (default medium; use large-v3 for harder audio).",
    )
    p.add_argument(
        "--transcribe-language",
        default="",
        help="Optional language code for faster-whisper (empty = auto-detect), e.g. zh.",
    )
    p.add_argument(
        "--transcribe-device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="Device for faster-whisper when auto-transcribing.",
    )
    p.add_argument(
        "--transcribe-audio-preprocess",
        default="none",
        choices=["none", "mono_16k_wav", "enhance", "vocal_isolate"],
        help="FFmpeg preprocess before ASR (requires ffmpeg).",
    )
    p.add_argument(
        "--transcribe-beam-size",
        type=int,
        default=5,
        help="Passed to run_transcribe_stage --beam-size (default 5). Lower is faster.",
    )
    p.add_argument(
        "--transcribe-best-of",
        type=int,
        default=5,
        help="Passed to run_transcribe_stage --best-of (default 5). Lower is faster.",
    )
    p.add_argument(
        "--transcribe-no-vad-filter",
        action="store_true",
        help="Pass --no-vad-filter to transcribe (more dialogue recall, noisier).",
    )
    p.add_argument(
        "--transcribe-vad-threshold",
        type=float,
        default=None,
        help="Optional VAD threshold override for transcribe (softer = lower, e.g. 0.3).",
    )
    p.add_argument(
        "--extractor",
        default="audio_only",
        choices=["audio_only", "ocr_only", "hybrid", "external_srt"],
        help=(
            "Subtitle extractor forwarded to run_transcribe_stage (default audio_only). "
            "external_srt skips ASR when job_state/subtitle_extractor is external_srt and "
            "artifacts/transcribe/source.srt is present (see engine.external_srt)."
        ),
    )
    p.add_argument(
        "--ocr-language",
        default="ch",
        help="OCR language code when --extractor ocr_only/hybrid (default ch).",
    )
    p.add_argument(
        "--ocr-roi",
        default="",
        help='OCR ROI JSON {"x":..,"y":..,"w":..,"h":..} forwarded to run_transcribe_stage.',
    )
    p.add_argument(
        "--ocr-device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="OCR device forwarded to run_transcribe_stage (default auto).",
    )
    p.add_argument(
        "--ocr-provider",
        default="",
        help="OCR provider name forwarded to run_transcribe_stage (paddleocr|rapidocr).",
    )
    p.add_argument(
        "--tts-provider",
        default="edge_tts",
        help="Passed to run_tts_stage when --to-stage >= tts_generated.",
    )
    p.add_argument(
        "--tts-voice",
        default="",
        help="Optional TTS voice id (edge-tts default if empty: vi-VN-HoaiMyNeural).",
    )
    p.add_argument(
        "--tts-rate",
        default="",
        help='Optional TTS rate (e.g. edge-tts "+10%%"; default provider +0%%).',
    )
    p.add_argument(
        "--strict-input-match",
        action="store_true",
        help="Fail with a clear error when input fingerprints drift vs manifests (no auto-invalidate).",
    )
    p.add_argument(
        "--force-rebuild-downstream",
        action="store_true",
        help="Before finalize+stages, delete final_subtitle downstream artifacts (tts/align/mix/render).",
    )
    p.add_argument(
        "--mix-mode",
        default="replace_original_speech",
        choices=["replace_original_speech", "duck_original_speech"],
        help="Mix policy for dub (default replace_original_speech).",
    )
    p.add_argument(
        "--duck-gain-db",
        type=float,
        default=-20.0,
        help="Only for duck_original_speech: gain (dB) applied to original audio during speech.",
    )
    p.add_argument(
        "--duck-fade-ms",
        type=int,
        default=120,
        help="Only for duck_original_speech: fade in/out duration (ms) for duck envelope edges.",
    )
    p.add_argument(
        "--duck-merge-gap-ms",
        type=int,
        default=150,
        help="Only for duck_original_speech: merge adjacent speech segments within this gap.",
    )
    p.add_argument("--bgm", default="", help="Optional BGM path override for run_mix_stage.")
    p.add_argument("--bgm-volume-db", type=float, default=None, help="Optional BGM gain override in dB.")
    p.add_argument("--bgm-loop", action="store_true", help="Loop BGM override.")
    p.add_argument("--bgm-fade-in-ms", type=int, default=None, help="Optional BGM fade-in override in ms.")
    p.add_argument("--bgm-fade-out-ms", type=int, default=None, help="Optional BGM fade-out override in ms.")
    p.add_argument(
        "--translate-backend",
        default="legacy",
        choices=["legacy", "block_v2"],
        help="Passed to run_translate_stage --backend (default legacy).",
    )
    p.add_argument(
        "--finalize-mode",
        default="display",
        choices=["display", "voice"],
        help="Passed to run_finalize_subtitle_stage: display (subtitle) vs voice (TTS/dub source).",
    )
    p.add_argument(
        "--enable-translation-qa",
        action="store_true",
        help="Pass --enable-qa-manifest to translate (block_v2: translation_qa.json + targeted voice rewrites).",
    )
    p.add_argument(
        "--enable-source-cleanup",
        action="store_true",
        help="Run engine.run_cleanup_source_stage after transcribe and before translate.",
    )
    p.add_argument(
        "--translate-source-mode",
        default="auto",
        choices=["auto", "raw", "cleaned"],
        help="auto: cleaned if --enable-source-cleanup else raw. Passed to run_translate_stage --source-mode.",
    )
    return p.parse_args(argv)


def _effective_translate_source_mode(ns: argparse.Namespace) -> str:
    v = getattr(ns, "translate_source_mode", "auto")
    if v == "auto":
        return "cleaned" if getattr(ns, "enable_source_cleanup", False) else "raw"
    return str(v)


def _blocked_input_required(
    job_workspace: Path,
    job_id: str,
    runner_meta: dict,
    message: str,
) -> None:
    translate_dir = job_workspace / "artifacts" / "translate"
    translate_dir.mkdir(parents=True, exist_ok=True)
    result_json_path = translate_dir / "result.json"
    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "blocked",
            "current_stage": "input_required",
            "last_error": message,
            "translate_result_path": str(result_json_path),
            "translated_output_path": None,
            "runner": runner_meta,
        },
    )


def _external_srt_mode(job_workspace: Path, ns: argparse.Namespace) -> bool:
    st = _load_state(job_workspace)
    if str(st.get("subtitle_extractor") or "").strip().lower() == "external_srt":
        return True
    ext = str(getattr(ns, "extractor", "audio_only") or "audio_only").strip().lower()
    return ext == "external_srt"


def _ensure_source_srt(
    job_workspace: Path,
    job_id: str,
    runner_meta: dict,
    ns: argparse.Namespace,
) -> tuple[bool, int]:
    """Ensure artifacts/transcribe/source.srt exists (use existing file or run transcribe from input/source.mp4)."""
    source_srt = job_workspace / "artifacts" / "transcribe" / "source.srt"
    if _external_srt_mode(job_workspace, ns):
        if not source_srt.is_file():
            msg = (
                "subtitle_extractor is external_srt but artifacts/transcribe/source.srt is missing. "
                "Import an SRT file first (POST /api/import-external-srt) or restore source.srt."
            )
            _blocked_input_required(job_workspace, job_id, runner_meta, msg)
            return False, 1
        try:
            content = source_srt.read_text(encoding="utf-8")
        except OSError as e:
            msg = f"external_srt: could not read source.srt: {e}"
            _blocked_input_required(job_workspace, job_id, runner_meta, msg)
            return False, 1
        if not parse_srt_cues(content):
            msg = "external_srt: source.srt exists but contains no valid cues."
            _blocked_input_required(job_workspace, job_id, runner_meta, msg)
            return False, 1
        return True, 0

    if source_srt.is_file():
        return True, 0

    input_mp4 = job_workspace / "input" / "source.mp4"
    if not input_mp4.is_file():
        msg = (
            f"Missing artifacts/transcribe/source.srt and input/source.mp4 under {job_workspace}. "
            "Add one of them to continue."
        )
        _blocked_input_required(job_workspace, job_id, runner_meta, msg)
        return False, 1

    targv = [
        "--job-workspace",
        str(job_workspace),
        "--model-size",
        ns.transcribe_model_size,
        "--device",
        ns.transcribe_device,
        "--beam-size",
        str(int(ns.transcribe_beam_size)),
        "--best-of",
        str(int(ns.transcribe_best_of)),
    ]
    if (ns.transcribe_language or "").strip():
        targv.extend(["--language", ns.transcribe_language.strip()])
    ap = getattr(ns, "transcribe_audio_preprocess", "none") or "none"
    if str(ap).strip().lower() != "none":
        targv.extend(["--audio-preprocess", str(ap).strip().lower()])
    if getattr(ns, "transcribe_no_vad_filter", False):
        targv.append("--no-vad-filter")
    vth = getattr(ns, "transcribe_vad_threshold", None)
    if vth is not None:
        targv.extend(["--vad-threshold", str(float(vth))])

    extractor = str(getattr(ns, "extractor", "audio_only") or "audio_only").strip().lower()
    if extractor not in {"audio_only", "ocr_only", "hybrid", "external_srt"}:
        extractor = "audio_only"
    if extractor == "external_srt":
        extractor = "audio_only"
    targv.extend(["--extractor", extractor])
    if extractor in {"ocr_only", "hybrid"}:
        ocr_provider = str(getattr(ns, "ocr_provider", "") or "").strip().lower().replace("-", "_")
        if ocr_provider and ocr_provider not in {"paddleocr", "paddle", "paddle_ocr", "rapidocr", "rapid_ocr", "rapid"}:
            ocr_provider = ""
        if ocr_provider:
            canonical = "rapidocr" if "rapid" in ocr_provider else "paddleocr"
            targv.extend(["--ocr-provider", canonical])
        ocr_lang = str(getattr(ns, "ocr_language", "") or "").strip()
        if ocr_lang:
            targv.extend(["--ocr-language", ocr_lang])
        ocr_roi = str(getattr(ns, "ocr_roi", "") or "").strip()
        if ocr_roi:
            targv.extend(["--ocr-roi", ocr_roi])
        ocr_device = str(getattr(ns, "ocr_device", "") or "").strip()
        if ocr_device and ocr_device != "auto":
            targv.extend(["--ocr-device", ocr_device])

    _mark_stage_running(job_workspace, job_id, runner_meta, "transcribed")
    code = run_transcribe_stage.main(targv)
    if code != 0:
        return False, code
    if not source_srt.is_file():
        msg = "Transcription finished but artifacts/transcribe/source.srt is missing."
        _blocked_input_required(job_workspace, job_id, runner_meta, msg)
        return False, 1
    return True, 0


def _mark_transcribed_if_needed(job_workspace: Path, job_id: str, runner_meta: dict) -> None:
    """Merge runner + transcribed status; set transcribe_output_srt if missing (e.g. hand-placed source.srt)."""
    source_srt = job_workspace / "artifacts" / "transcribe" / "source.srt"
    out_path = str(source_srt.resolve())
    base = _load_state(job_workspace)
    updates: dict = {
        "job_id": job_id,
        "job_workspace": str(job_workspace),
        "status": "transcribed",
        "current_stage": "transcribed",
        "last_error": None,
        "runner": runner_meta,
    }
    if not base.get("transcribe_output_srt"):
        updates["transcribe_output_srt"] = out_path
    _merge_job_state(job_workspace, updates)
    record_video_fingerprint_if_absent(job_workspace)


def _run_pipeline(ns: argparse.Namespace, job_workspace: Path) -> int:
    job_id = job_workspace.name

    runner_meta = {
        "stage_order": list(STAGE_ORDER),
        "from_stage": ns.from_stage,
        "to_stage": ns.to_stage,
        "translate_backend": ns.translate_backend,
        "finalize_mode": ns.finalize_mode,
        "enable_translation_qa": bool(ns.enable_translation_qa),
        "enable_source_cleanup": bool(ns.enable_source_cleanup),
        "translate_source_mode": _effective_translate_source_mode(ns),
    }
    _merge_job_state(job_workspace, {"runner": runner_meta})

    to_rank = _rank(ns.to_stage)
    transcribed_rank = _rank("transcribed")
    translated_rank = _rank("translated")
    subtitle_finalized_rank = _rank("subtitle_finalized")
    tts_generated_rank = _rank("tts_generated")
    aligned_rank = _rank("aligned")
    mixed_rank = _rank("mixed")
    rendered_rank = _rank("rendered")
    edited_voice = job_workspace / "artifacts" / "edit" / "edited_voice.srt"
    skip_translate_for_voice_export = (
        ns.finalize_mode == "voice"
        and to_rank >= subtitle_finalized_rank
        and edited_voice.is_file()
        and _voice_edit_completed(job_workspace)
    )

    # Stop before translate: no translate_cli
    if to_rank < translated_rank:
        if to_rank <= _rank("imported"):
            _merge_job_state(
                job_workspace,
                {
                    "job_id": job_id,
                    "job_workspace": str(job_workspace),
                    "status": "imported",
                    "current_stage": "imported",
                    "last_error": None,
                    "runner": runner_meta,
                },
            )
            print(f"[run_job] Marked imported (to_stage={ns.to_stage}).")
            return 0

        # to_stage == transcribed
        ok, code = _ensure_source_srt(job_workspace, job_id, runner_meta, ns)
        if not ok:
            print("[run_job] Blocked or transcribe failed; see job_state.json.", file=sys.stderr)
            return code
        _mark_transcribed_if_needed(job_workspace, job_id, runner_meta)
        print(
            "[run_job] transcribed: source.srt ready (translate not run; to_stage < translated)."
        )
        return 0

    # to_stage >= translated: source.srt/provenance must still be valid, even when export-after-edit
    # reuses the approved edited_voice.srt and skips a fresh translate pass.
    for _attempt in range(4):
        ok, code = _ensure_source_srt(job_workspace, job_id, runner_meta, ns)
        if not ok:
            print("[run_job] Blocked or transcribe failed; see job_state.json.", file=sys.stderr)
            return code
        _mark_transcribed_if_needed(job_workspace, job_id, runner_meta)
        inv, err = apply_run_job_provenance_gates(
            job_workspace,
            to_rank=to_rank,
            subtitle_finalized_rank=subtitle_finalized_rank,
            strict=bool(ns.strict_input_match),
            force_rebuild_downstream=bool(ns.force_rebuild_downstream) and _attempt == 0,
        )
        if err:
            print(f"[run_job] Provenance gate: {err}", file=sys.stderr)
            return 1
        if not inv:
            break
    else:
        print("[run_job] Provenance gate loop exceeded retries.", file=sys.stderr)
        return 1

    if not skip_translate_for_voice_export:
        targv: list[str] = [
            "--job-workspace",
            str(job_workspace),
            "--project-name",
            ns.project_name,
            "--backend",
            ns.translate_backend,
        ]
        if (ns.api_key or "").strip():
            targv.extend(["--api-key", (ns.api_key or "").strip()])
        if ns.enable_translation_qa:
            targv.append("--enable-qa-manifest")
        targv.extend(["--source-mode", _effective_translate_source_mode(ns)])

        if getattr(ns, "enable_source_cleanup", False):
            cargv = ["--job-workspace", str(job_workspace)]
            if (ns.api_key or "").strip():
                cargv.extend(["--api-key", (ns.api_key or "").strip()])
            _mark_stage_running(job_workspace, job_id, runner_meta, "translated")
            ccode = run_cleanup_source_stage.main(cargv)
            if ccode != 0:
                print("[run_job] Source cleanup stage failed; see stderr.", file=sys.stderr)
                _merge_job_state(job_workspace, {"runner": runner_meta})
                return ccode

        _mark_stage_running(job_workspace, job_id, runner_meta, "translated")
        code = run_translate_stage.main(targv)

        if code != 0:
            print(
                "[run_job] Translate stage failed; see job_state.json and translate_cli logs.",
                file=sys.stderr,
            )
            _merge_job_state(job_workspace, {"runner": runner_meta})
            return code
    else:
        print(
            "[run_job] Reusing approved artifacts/edit/edited_voice.srt; skipping translate stage.",
            file=sys.stderr,
        )

    # Voice-first edit gate (PM spec): do not proceed to finalize/TTS/render until user edits edited_voice.srt.
    # Keep backward compatibility: only enforce when --finalize-mode voice.
    if ns.finalize_mode == "voice" and to_rank >= subtitle_finalized_rank:
        # Only gate true voice-first workspaces (translated_voice exists).
        # If translated_voice is missing, allow legacy fallback paths handled by finalize policy.
        translated_voice = job_workspace / "artifacts" / "translate" / "translated_voice.srt"
        if translated_voice.is_file() and not _voice_edit_completed(job_workspace):
            msg = (
                "Voice flow is blocked: waiting for human edit completion. "
                "Edit artifacts/edit/edited_voice.srt and mark voice_edited (voice_edit_status=voice_edited) "
                "before finalize/TTS/render can continue."
            )
            _block_voice_edit_pending(job_workspace, job_id, runner_meta, msg)
            print(f"[run_job] {msg}", file=sys.stderr)
            return 2

    if to_rank >= subtitle_finalized_rank:
        fargv = [
            "--job-workspace",
            str(job_workspace),
            "--finalize-mode",
            ns.finalize_mode,
        ]
        _mark_stage_running(job_workspace, job_id, runner_meta, "subtitle_finalized")
        fcode = run_finalize_subtitle_stage.main(fargv)
        if fcode != 0:
            print(
                "[run_job] Finalize subtitle stage failed; see job_state.json.",
                file=sys.stderr,
            )
            _merge_job_state(job_workspace, {"runner": runner_meta})
            return fcode

    if to_rank >= tts_generated_rank:
        targv: list[str] = [
            "--job-workspace",
            str(job_workspace),
            "--tts-provider",
            ns.tts_provider,
        ]
        if (ns.tts_voice or "").strip():
            targv.extend(["--voice", ns.tts_voice.strip()])
        if (ns.tts_rate or "").strip():
            targv.extend(["--rate", ns.tts_rate.strip()])
        _mark_stage_running(job_workspace, job_id, runner_meta, "tts_generated")
        tcode = run_tts_stage.main(targv)
        if tcode != 0:
            print("[run_job] TTS stage failed; see job_state.json.", file=sys.stderr)
            _merge_job_state(job_workspace, {"runner": runner_meta})
            return tcode

    if to_rank >= aligned_rank:
        _mark_stage_running(job_workspace, job_id, runner_meta, "aligned")
        cargv = ["--job-workspace", str(job_workspace)]
        ccode = run_compact_tts_stage.main(cargv)
        if ccode != 0:
            print("[run_job] Compact TTS stage failed; see job_state.json.", file=sys.stderr)
            _merge_job_state(job_workspace, {"runner": runner_meta})
            return ccode
        aargv = ["--job-workspace", str(job_workspace)]
        acode = run_align_stage.main(aargv)
        if acode != 0:
            print("[run_job] Align stage failed; see job_state.json.", file=sys.stderr)
            _merge_job_state(job_workspace, {"runner": runner_meta})
            return acode

    if to_rank >= mixed_rank:
        bgm_state = load_bgm_state(job_workspace) or {}
        bgm_path = str(ns.bgm or "").strip() or str(bgm_state.get("normalized_path") or "").strip()
        bgm_volume = ns.bgm_volume_db
        if bgm_volume is None and bgm_state:
            bgm_volume = float(bgm_state.get("volume_db", -20))
        bgm_fade_in = ns.bgm_fade_in_ms
        if bgm_fade_in is None and bgm_state:
            bgm_fade_in = int(bgm_state.get("fade_in_ms", 500))
        bgm_fade_out = ns.bgm_fade_out_ms
        if bgm_fade_out is None and bgm_state:
            bgm_fade_out = int(bgm_state.get("fade_out_ms", 1000))
        bgm_loop = bool(ns.bgm_loop or bgm_state.get("loop", False))
        margv = [
            "--job-workspace",
            str(job_workspace),
            "--mix-mode",
            ns.mix_mode,
            "--duck-gain-db",
            str(ns.duck_gain_db),
            "--duck-fade-ms",
            str(ns.duck_fade_ms),
            "--duck-merge-gap-ms",
            str(ns.duck_merge_gap_ms),
        ]
        if bgm_path:
            margv.extend(["--bgm", bgm_path])
            margv.extend(["--bgm-volume-db", str(-20.0 if bgm_volume is None else bgm_volume)])
            margv.extend(["--bgm-fade-in-ms", str(500 if bgm_fade_in is None else bgm_fade_in)])
            margv.extend(["--bgm-fade-out-ms", str(1000 if bgm_fade_out is None else bgm_fade_out)])
            if bgm_loop:
                margv.append("--bgm-loop")
        _mark_stage_running(job_workspace, job_id, runner_meta, "mixed")
        mcode = run_mix_stage.main(margv)
        if mcode != 0:
            print("[run_job] Mix stage failed; see job_state.json.", file=sys.stderr)
            _merge_job_state(job_workspace, {"runner": runner_meta})
            return mcode

    if to_rank >= rendered_rank:
        rargv = [
            "--job-workspace",
            str(job_workspace),
            "--overwrite",
            "--subtitle-mode",
            ns.render_subtitle_mode,
        ]
        if (ns.render_aspect_ratio or "").strip():
            rargv.extend(["--aspect-ratio", ns.render_aspect_ratio.strip()])
        if (ns.render_background_image or "").strip():
            rargv.extend(["--background-image", ns.render_background_image.strip()])
        if (ns.project_root or "").strip():
            rargv.extend(["--project-root", ns.project_root.strip()])
        _mark_stage_running(job_workspace, job_id, runner_meta, "rendered")
        rcode = run_render_stage.main(rargv)
        if rcode != 0:
            print("[run_job] Render stage failed; see job_state.json.", file=sys.stderr)
            _merge_job_state(job_workspace, {"runner": runner_meta})
            return rcode

    if to_rank >= rendered_rank:
        if ns.to_stage == "done":
            print(
                "[run_job] Render completed; terminal stage `done` currently aliases `rendered`."
            )
        else:
            print("[run_job] Render completed (see artifacts/render/).")
    elif to_rank >= mixed_rank:
        if to_rank > mixed_rank:
            print(
                "[run_job] Through mix; later stages (rendered → done) are not implemented in this runner."
            )
        else:
            print("[run_job] Translate, finalize, TTS, align, and mix completed (see artifacts/mixed/).")
    elif to_rank >= aligned_rank:
        if to_rank > aligned_rank:
            print(
                "[run_job] Through align; later stages (mixed → done) are not implemented in this runner."
            )
        else:
            print("[run_job] Translate, finalize, TTS, and align completed (see artifacts/aligned/).")
    elif to_rank >= tts_generated_rank:
        if to_rank > tts_generated_rank:
            print(
                "[run_job] Through TTS; later stages (aligned → done) are not implemented in this runner."
            )
        else:
            print("[run_job] Translate, finalize, and TTS completed (see artifacts/tts/).")
    elif to_rank >= subtitle_finalized_rank:
        print("[run_job] Translate and finalize subtitle completed (final_subtitle.srt).")
    else:
        print("[run_job] Translate stage completed (run_translate_stage).")

    # Refresh runner meta after child may have merged state
    _merge_job_state(job_workspace, {"runner": runner_meta})

    return 0


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    job_workspace = Path(ns.job_workspace).expanduser().resolve()
    try:
        with acquire_workspace_lock(job_workspace, owner="run_job"):
            return _run_pipeline(ns, job_workspace)
    except WorkspaceLockError as e:
        detail = describe_lock_details(e.details)
        print(
            f"[run_job] Workspace is busy; another run is already active for {job_workspace} "
            f"({detail}).",
            file=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
