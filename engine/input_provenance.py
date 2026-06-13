"""
Minimal file fingerprints and job input provenance for stale-artifact detection.

Fingerprint fields: absolute_path, basename, size_bytes, mtime_ns (no hashing in v1).
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

FINAL_SUBTITLE_MANIFEST_REL = Path("artifacts") / "translate" / "final_subtitle_manifest.json"

TRANSLATED_AUTO_BASENAME = "translated_auto.srt"
TRANSLATED_VOICE_BASENAME = "translated_voice.srt"
TRANSLATED_LEGACY_BASENAME = "translated.srt"
EDITED_VOICE_BASENAME = "edited_voice.srt"
EDITED_DISPLAY_BASENAME = "edited.srt"
TRANSLATED_MANUAL_BASENAME = "translated_manual.srt"
SOURCE_CLEANED_ZH_BASENAME = "source_cleaned_zh.srt"
SOURCE_CLEANUP_MANIFEST_BASENAME = "source_cleanup_manifest.json"

_LOG: Callable[..., None] = print


def set_provenance_log(fn: Callable[..., None] | None) -> None:
    global _LOG
    _LOG = fn or print


def fingerprint_file(path: Path) -> dict[str, Any] | None:
    p = path.expanduser().resolve()
    if not p.is_file():
        return None
    st = p.stat()
    mtime_ns = getattr(st, "st_mtime_ns", int(st.st_mtime * 1_000_000_000))
    return {
        "absolute_path": str(p),
        "basename": p.name,
        "size_bytes": int(st.st_size),
        "mtime_ns": int(mtime_ns),
    }


def fingerprints_equal(a: dict[str, Any] | None, b: dict[str, Any] | None) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return (
        a.get("absolute_path") == b.get("absolute_path")
        and a.get("basename") == b.get("basename")
        and a.get("size_bytes") == b.get("size_bytes")
        and a.get("mtime_ns") == b.get("mtime_ns")
    )


def pick_finalize_source_subtitle(
    job_workspace: Path, *, finalize_mode: str = "display"
) -> tuple[Path | None, str | None]:
    """
    Same priority as run_finalize_subtitle_stage.

    finalize_mode:
    - display: edited (display) > manual > auto > legacy translated.srt
    - voice: if translated_voice.srt exists, only edited_voice > translated_voice (no display
      subtitles in between). If translated_voice.srt is missing, fall back to the display chain.
    """
    jw = job_workspace.expanduser().resolve()
    translate_dir = jw / "artifacts" / "translate"
    edit_dir = jw / "artifacts" / "edit"
    mode = (finalize_mode or "display").strip().lower()
    if mode not in ("display", "voice"):
        mode = "display"

    display_chain: list[tuple[Path, str]] = [
        (translate_dir / EDITED_DISPLAY_BASENAME, "edited"),
        (edit_dir / EDITED_DISPLAY_BASENAME, "edited"),
        (translate_dir / TRANSLATED_MANUAL_BASENAME, "manual"),
        (translate_dir / TRANSLATED_AUTO_BASENAME, "auto"),
        (translate_dir / TRANSLATED_LEGACY_BASENAME, "auto"),
    ]

    if mode == "voice":
        voice_srt = translate_dir / TRANSLATED_VOICE_BASENAME
        if voice_srt.is_file():
            voice_chain: list[tuple[Path, str]] = [
                (edit_dir / EDITED_VOICE_BASENAME, "edited_voice"),
                # Backward-compat: older flows may place edited_voice under translate/.
                (translate_dir / EDITED_VOICE_BASENAME, "edited_voice_legacy_path"),
                (voice_srt, "voice_auto"),
            ]
            for path, tag in voice_chain:
                if path.is_file():
                    return path, tag
        for path, tag in display_chain:
            if path.is_file():
                return path, tag
        return None, None

    for path, tag in display_chain:
        if path.is_file():
            return path, tag
    return None, None


def get_effective_finalize_mode(job_workspace: Path) -> str:
    """
    Mode used when comparing finalize_source_subtitle fingerprints (must match how final_subtitle
    was produced). Reads final_subtitle_manifest.json; infers voice from path for older manifests.
    """
    jw = job_workspace.expanduser().resolve()
    mf = load_final_subtitle_manifest(jw)
    if not isinstance(mf, dict):
        return "display"
    m = mf.get("finalize_mode")
    if m == "voice" or m == "display":
        return str(m)
    sel = mf.get("selected_source_subtitle_path")
    if isinstance(sel, str):
        low = sel.replace("\\", "/").lower()
        if TRANSLATED_VOICE_BASENAME.lower() in low or EDITED_VOICE_BASENAME.lower() in low:
            return "voice"
    return "display"


def _runner_translate_source_mode(jw: Path) -> str:
    try:
        p = jw / "job_state.json"
        if p.is_file():
            st = json.loads(p.read_text(encoding="utf-8"))
            r = st.get("runner") or {}
            if isinstance(r.get("translate_source_mode"), str):
                return str(r["translate_source_mode"])
            if isinstance(st.get("translate_source_mode"), str):
                return str(st["translate_source_mode"])
    except Exception:
        pass
    return "raw"


def _resolve_translate_input_srt(jw: Path) -> Path:
    raw = jw / "artifacts" / "transcribe" / "source.srt"
    cl = jw / "artifacts" / "transcribe" / SOURCE_CLEANED_ZH_BASENAME
    if _runner_translate_source_mode(jw) == "cleaned" and cl.is_file():
        return cl
    return raw


def build_input_provenance_dict(
    job_workspace: Path, *, finalize_mode: str | None = None
) -> dict[str, Any]:
    """Live snapshot: video, transcribe source.srt, finalize pick, and display/voice lineage fps."""
    jw = job_workspace.expanduser().resolve()
    vid = jw / "input" / "source.mp4"
    src = jw / "artifacts" / "transcribe" / "source.srt"
    cleaned_src = jw / "artifacts" / "transcribe" / SOURCE_CLEANED_ZH_BASENAME
    translate_in = _resolve_translate_input_srt(jw)
    if finalize_mode is None:
        eff = get_effective_finalize_mode(jw)
    else:
        eff = finalize_mode if finalize_mode in ("display", "voice") else "display"
    fin_src, _mode = pick_finalize_source_subtitle(jw, finalize_mode=eff)
    disp_src, _ = pick_finalize_source_subtitle(jw, finalize_mode="display")
    voice_src, _ = pick_finalize_source_subtitle(jw, finalize_mode="voice")
    return {
        "input_video": fingerprint_file(vid),
        "transcribe_source_srt": fingerprint_file(src),
        "transcribe_source_cleaned_zh_srt": fingerprint_file(cleaned_src)
        if cleaned_src.is_file()
        else None,
        "translate_input_srt": fingerprint_file(translate_in) if translate_in.is_file() else None,
        "finalize_source_subtitle": fingerprint_file(fin_src) if fin_src else None,
        "finalize_display_lineage_subtitle": fingerprint_file(disp_src) if disp_src else None,
        "finalize_voice_lineage_subtitle": fingerprint_file(voice_src) if voice_src else None,
    }


def load_final_subtitle_manifest(job_workspace: Path) -> dict[str, Any] | None:
    p = job_workspace / FINAL_SUBTITLE_MANIFEST_REL
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _norm_prov(blob: Any) -> dict[str, Any]:
    if not isinstance(blob, dict):
        return {
            "input_video": None,
            "transcribe_source_srt": None,
            "translate_input_srt": None,
            "finalize_source_subtitle": None,
        }
    return {
        "input_video": blob.get("input_video"),
        "transcribe_source_srt": blob.get("transcribe_source_srt"),
        "translate_input_srt": blob.get("translate_input_srt"),
        "finalize_source_subtitle": blob.get("finalize_source_subtitle"),
    }


def classify_provenance_drift(
    stored: dict[str, Any] | None, current: dict[str, Any]
) -> str | None:
    """
    None = no drift.
    'video_changed' | 'subtitle_lineage_changed' | 'missing_provenance'
    """
    if stored is None:
        return "missing_provenance"
    s = _norm_prov(stored)
    c = _norm_prov(current)
    if not fingerprints_equal(
        s.get("input_video") if isinstance(s.get("input_video"), dict) else None,
        c.get("input_video") if isinstance(c.get("input_video"), dict) else None,
    ):
        return "video_changed"
    if not fingerprints_equal(
        s.get("transcribe_source_srt") if isinstance(s.get("transcribe_source_srt"), dict) else None,
        c.get("transcribe_source_srt") if isinstance(c.get("transcribe_source_srt"), dict) else None,
    ):
        return "subtitle_lineage_changed"
    if isinstance(stored, dict) and stored.get("translate_input_srt") is not None:
        st_t = s.get("translate_input_srt") if isinstance(s.get("translate_input_srt"), dict) else None
        cu_t = c.get("translate_input_srt") if isinstance(c.get("translate_input_srt"), dict) else None
        if not fingerprints_equal(st_t, cu_t):
            return "subtitle_lineage_changed"
    if not fingerprints_equal(
        s.get("finalize_source_subtitle")
        if isinstance(s.get("finalize_source_subtitle"), dict)
        else None,
        c.get("finalize_source_subtitle")
        if isinstance(c.get("finalize_source_subtitle"), dict)
        else None,
    ):
        return "subtitle_lineage_changed"
    return None


def stale_manifest_input_provenance_message(
    job_workspace: Path, manifest_path: Path
) -> str | None:
    """If manifest embeds input_provenance and it drifts vs live job inputs, return error text."""
    jw = job_workspace.expanduser().resolve()
    mp = manifest_path.expanduser().resolve()
    if not mp.is_file():
        return None
    try:
        mf = json.loads(mp.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    prov = mf.get("input_provenance")
    if not isinstance(prov, dict):
        return None
    mode = get_effective_finalize_mode(jw)
    drift = classify_provenance_drift(prov, build_input_provenance_dict(jw, finalize_mode=mode))
    if drift is None:
        return None
    try:
        rel = mp.relative_to(jw).as_posix()
    except ValueError:
        rel = str(mp)
    return f"Stale manifest {rel}: provenance drift ({drift}). Re-run upstream stages or run_job."


def stale_final_subtitle_message(job_workspace: Path) -> str | None:
    """If final_subtitle.srt should not be trusted for downstream, return error text."""
    jw = job_workspace.expanduser().resolve()
    final_srt = jw / "artifacts" / "translate" / "final_subtitle.srt"
    if not final_srt.is_file():
        return None
    mf = load_final_subtitle_manifest(jw)
    if mf is None:
        return (
            "Stale or legacy final_subtitle.srt: missing artifacts/translate/final_subtitle_manifest.json. "
            "Re-run finalize (e.g. python -m engine.run_finalize_subtitle_stage) or full run_job."
        )
    stored = mf.get("input_provenance")
    mode = get_effective_finalize_mode(jw)
    drift = classify_provenance_drift(
        stored if isinstance(stored, dict) else None,
        build_input_provenance_dict(jw, finalize_mode=mode),
    )
    if drift is None:
        return None
    old_v = (stored or {}).get("input_video") if isinstance(stored, dict) else None
    cur = build_input_provenance_dict(jw, finalize_mode=mode)
    return (
        f"Stale final_subtitle.srt: provenance drift ({drift}). "
        f"Manifest expected video fingerprint {old_v!r}; current job snapshot is {cur!r}. "
        "Run python -m engine.run_job with auto-invalidation, or re-finalize."
    )


def _unlink_quiet(p: Path) -> None:
    try:
        if p.is_file():
            p.unlink()
    except OSError:
        pass


def _rmtree_dir(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def _load_state_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_state_json(path: Path, body: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, body)


def _drop_artifact_paths(base: dict[str, Any], keys: tuple[str, ...]) -> None:
    artifact_paths = base.get("artifact_paths")
    if not isinstance(artifact_paths, dict):
        return
    for key in keys:
        artifact_paths.pop(key, None)
    if artifact_paths:
        base["artifact_paths"] = artifact_paths
    else:
        base.pop("artifact_paths", None)


def _rewind_voice_edit_state(job_workspace: Path, base: dict[str, Any]) -> dict[str, Any]:
    edited_voice = job_workspace / "artifacts" / "edit" / EDITED_VOICE_BASENAME
    if not edited_voice.is_file():
        return {
            "status": "translated",
            "current_stage": "translated",
            "voice_edit_status": None,
            "voice_edited": False,
            "required_action": None,
            "edited_voice_expected_path": None,
        }
    if bool(base.get("voice_edited")) or str(base.get("voice_edit_status") or "").strip() == "voice_edited":
        return {
            "status": "voice_edited",
            "current_stage": "voice_edited",
            "voice_edit_status": "voice_edited",
            "voice_edited": True,
            "required_action": None,
            "edited_voice_expected_path": str(edited_voice.resolve()),
        }
    return {
        "status": "voice_edit_pending",
        "current_stage": "voice_edit_pending",
        "voice_edit_status": "voice_edit_pending",
        "voice_edited": False,
        "required_action": "edit_edited_voice_srt",
        "edited_voice_expected_path": str(edited_voice.resolve()),
    }


def _clear_downstream_state(job_workspace: Path, *, from_transcribe: bool) -> None:
    jw = job_workspace.expanduser().resolve()
    job_state_path = jw / "job_state.json"
    video_state_path = jw / "video_state.json"

    job_state = _load_state_json(job_state_path)
    video_state = _load_state_json(video_state_path)

    common_job_clears = {
        "final_subtitle_path": None,
        "subtitle_source_mode": None,
        "finalize_source_srt": None,
        "tts_provider": None,
        "tts_voice": None,
        "tts_manifest_path": None,
        "tts_output_dir": None,
        "tts_cue_count": None,
        "aligned_voice_track_path": None,
        "alignment_manifest_path": None,
        "mixed_audio_path": None,
        "mix_manifest_path": None,
        "render_output_path": None,
        "render_manifest_path": None,
        "last_error": None,
    }
    common_video_clears = {
        "subtitle_source_mode": None,
        "finalize_source_srt": None,
        "tts_provider": None,
        "tts_voice": None,
        "last_error": None,
    }
    downstream_artifact_paths = (
        "final_subtitle_srt",
        "final_subtitle_manifest",
        "tts_manifest",
        "tts_cues_dir",
        "aligned_voice_track",
        "alignment_manifest",
        "mixed_audio",
        "mix_manifest",
        "rendered_mp4",
        "render_manifest",
    )

    job_state.update(common_job_clears)
    video_state.update(common_video_clears)
    _drop_artifact_paths(job_state, downstream_artifact_paths)
    _drop_artifact_paths(video_state, downstream_artifact_paths)

    if from_transcribe:
        job_state.update(
            {
                "status": "transcribed",
                "current_stage": "transcribed",
                "transcribe_output_srt": None,
                "translated_output_path": None,
                "translated_auto_srt_path": None,
                "translate_result_path": None,
                "input_video_fingerprint_at_transcribe": None,
                "voice_edit_status": None,
                "voice_edited": False,
                "edited_voice_path": None,
                "edit_manifest_path": None,
                "required_action": None,
                "edited_voice_expected_path": None,
            }
        )
        video_state.update(
            {
                "status": "transcribed",
                "current_stage": "transcribed",
                "translated_status": None,
                "translate_path": None,
                "voice_edit_status": None,
                "voice_edited": False,
                "required_action": None,
            }
        )
        upstream_artifact_paths = (
            "source_srt",
            "translated_auto_srt",
            "translated_voice_srt",
            "translated_manual_srt",
            "edited_srt",
            "edited_voice_srt",
            "edit_manifest",
        )
        _drop_artifact_paths(job_state, upstream_artifact_paths)
        _drop_artifact_paths(video_state, upstream_artifact_paths)
    else:
        job_state.update(_rewind_voice_edit_state(jw, job_state))
        video_state.update(_rewind_voice_edit_state(jw, video_state))

    _write_state_json(job_state_path, job_state)
    _write_state_json(video_state_path, video_state)


def invalidate_from_transcribe_downward(job_workspace: Path, *, reason: str) -> None:
    jw = job_workspace.expanduser().resolve()
    _LOG(
        f"[provenance] Invalidating downstream artifacts (transcribe_downward): {reason}",
        file=sys.stderr,
    )
    translate_dir = jw / "artifacts" / "translate"
    transcribe_dir = jw / "artifacts" / "transcribe"
    for name in (
        "source.srt",
        "source_cleaned_zh.srt",
        "source_cleanup_manifest.json",
        "transcription_report.json",
    ):
        _unlink_quiet(transcribe_dir / name)
    _rmtree_dir(transcribe_dir / ".work")
    for name in (
        "translated_auto.srt",
        "translated_voice.srt",
        "translated_manual.srt",
        "translated.srt",
        "edited.srt",
        "edited_voice.srt",
        "translation_qa.json",
        "final_subtitle.srt",
        "final_subtitle_manifest.json",
        "result.json",
    ):
        _unlink_quiet(translate_dir / name)
    edit_srt = jw / "artifacts" / "edit" / "edited.srt"
    _unlink_quiet(edit_srt)
    _unlink_quiet(jw / "artifacts" / "edit" / EDITED_VOICE_BASENAME)
    _unlink_quiet(jw / "artifacts" / "edit" / "edit_manifest.json")
    for sub in ("tts", "tts_compacted", "aligned", "mixed", "render"):
        _rmtree_dir(jw / "artifacts" / sub)
    _clear_downstream_state(jw, from_transcribe=True)


def invalidate_from_finalize_downward(job_workspace: Path, *, reason: str) -> None:
    jw = job_workspace.expanduser().resolve()
    _LOG(
        f"[provenance] Invalidating downstream artifacts (finalize_downward): {reason}",
        file=sys.stderr,
    )
    translate_dir = jw / "artifacts" / "translate"
    _unlink_quiet(translate_dir / "final_subtitle.srt")
    _unlink_quiet(translate_dir / "final_subtitle_manifest.json")
    for sub in ("tts", "tts_compacted", "aligned", "mixed", "render"):
        _rmtree_dir(jw / "artifacts" / sub)
    _clear_downstream_state(jw, from_transcribe=False)


def record_video_fingerprint_if_absent(job_workspace: Path) -> None:
    """When source.srt exists and video exists, snapshot video fp once (hand-placed transcript)."""
    jw = job_workspace.expanduser().resolve()
    state_path = jw / "job_state.json"
    base: dict[str, Any] = {}
    if state_path.is_file():
        try:
            base = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            base = {}
    if base.get("input_video_fingerprint_at_transcribe"):
        return
    src = jw / "artifacts" / "transcribe" / "source.srt"
    vid = jw / "input" / "source.mp4"
    if not src.is_file() or not vid.is_file():
        return
    fp = fingerprint_file(vid)
    if fp:
        base["input_video_fingerprint_at_transcribe"] = fp
        write_json_atomic(state_path, base)


def apply_run_job_provenance_gates(
    job_workspace: Path,
    *,
    to_rank: int,
    subtitle_finalized_rank: int,
    strict: bool,
    force_rebuild_downstream: bool,
) -> tuple[bool, str]:
    """
    Returns (invalidated, error_message). If error_message non-empty, caller should exit 1.
    """
    jw = job_workspace.expanduser().resolve()
    if force_rebuild_downstream and to_rank >= subtitle_finalized_rank:
        invalidate_from_finalize_downward(jw, reason="--force-rebuild-downstream")
        return True, ""

    st_path = jw / "job_state.json"
    state: dict[str, Any] = {}
    if st_path.is_file():
        try:
            state = json.loads(st_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            state = {}

    cur_vid = fingerprint_file(jw / "input" / "source.mp4")
    stored_vid_fp = state.get("input_video_fingerprint_at_transcribe")
    src_srt = jw / "artifacts" / "transcribe" / "source.srt"
    if (
        src_srt.is_file()
        and isinstance(stored_vid_fp, dict)
        and cur_vid is not None
        and not fingerprints_equal(stored_vid_fp, cur_vid)
    ):
        msg = (
            "Detected stale workspace: input/source.mp4 no longer matches "
            "input_video_fingerprint_at_transcribe (video changed since transcribe / hand-placed source.srt)."
        )
        if strict:
            print(f"[provenance] STRICT: {msg}", file=sys.stderr)
            print(
                f"[provenance] Current video fingerprint: {cur_vid!r}; stored: {stored_vid_fp!r}",
                file=sys.stderr,
            )
            return False, msg
        print(f"[provenance] {msg} Invalidating transcribe_downward...", file=sys.stderr)
        invalidate_from_transcribe_downward(jw, reason="input_video_changed_vs_transcribe_snapshot")
        return True, ""

    if to_rank < subtitle_finalized_rank:
        return False, ""

    final_srt = jw / "artifacts" / "translate" / "final_subtitle.srt"
    manifest_path = jw / FINAL_SUBTITLE_MANIFEST_REL
    if not final_srt.is_file():
        return False, ""

    # Match fingerprints to how final_subtitle was produced (manifest.finalize_mode), not the
    # CLI mode of this run — avoids false drift when translated_auto changes under voice finalize.
    mode = get_effective_finalize_mode(jw)
    current = build_input_provenance_dict(jw, finalize_mode=mode)
    if not manifest_path.is_file():
        msg = "final_subtitle.srt exists but final_subtitle_manifest.json is missing (stale/legacy)."
        if strict:
            print(f"[provenance] STRICT: {msg}", file=sys.stderr)
            return False, msg
        print(f"[provenance] {msg} Invalidating finalize_downward...", file=sys.stderr)
        invalidate_from_finalize_downward(jw, reason="missing_final_subtitle_manifest")
        return True, ""

    try:
        mf = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        mf = {}
    stored_prov = mf.get("input_provenance") if isinstance(mf.get("input_provenance"), dict) else None
    drift = classify_provenance_drift(stored_prov, current)
    if drift is None:
        return False, ""

    old = stored_prov or {}
    msg = (
        f"Detected stale final_subtitle / manifest: drift={drift}. "
        f"Manifest input_provenance={old!r} vs current={current!r}."
    )
    if strict:
        print(f"[provenance] STRICT: {msg}", file=sys.stderr)
        return False, msg

    if drift == "video_changed":
        print(f"[provenance] {msg} Invalidating transcribe_downward...", file=sys.stderr)
        invalidate_from_transcribe_downward(jw, reason="video_changed_vs_final_manifest")
    else:
        print(f"[provenance] {msg} Invalidating finalize_downward...", file=sys.stderr)
        invalidate_from_finalize_downward(jw, reason=drift)
    return True, ""
