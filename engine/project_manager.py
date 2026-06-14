"""Multi-video project orchestration (Phase 5).

A *project* is a named directory holding multiple video_workspaces plus a
shared config with optional per-video overrides:

    <projects_root>/<project_id>/
        project_state.json
        videos/
            <video_id>/               # standard video_workspace (Phase 1-3)
                input/source.mp4
                video_state.json
                artifacts/...

Videos of any duration are accepted. Videos longer than SINGLE_VIDEO_THRESHOLD_S
are flagged ``is_long=True`` and routed through ``run_long_video_stage`` (split →
parallel per-segment pipelines → merge) instead of ``run_job`` directly.

Concurrency: run_translate_phase / run_render_phase drive at most MAX_PARALLEL_VIDEOS
workers via ThreadPoolExecutor. Each worker shells into engine.run_job for a single
video_workspace — no shared mutable state between workers. Long videos run an inner
ThreadPoolExecutor of up to ``long_video_workers`` (default 2) per video to cap the
fan-out at MAX_PARALLEL_VIDEOS * long_video_workers concurrent segment jobs.
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import json
import re
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from engine import run_job, run_long_video_stage
from engine.segment_manager import (
    SINGLE_VIDEO_THRESHOLD_S,
    SegmentError,
    load_segment_manifest,
)
from engine.voice_edit_api import (
    VoiceEditError,
    get_voice_edit_status,
    mark_voice_edited,
    seed_edited_voice,
)

MAX_PARALLEL_VIDEOS = 5
LONG_VIDEO_INNER_WORKERS_DEFAULT = 2
_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")


class ProjectError(RuntimeError):
    pass


def _slug(name: str) -> str:
    s = _ID_RE.sub("-", name).strip("-._")
    return s or "item"


@dataclass
class ProjectConfig:
    """Shared pipeline options plus per-video overrides."""

    project_name: str
    api_key: str = ""
    translate_backend: str = "block_v2"
    tts_provider: str = "edge_tts"
    tts_voice: str = ""
    mix_mode: str = "replace_original_speech"
    enable_source_cleanup: bool = False
    enable_translation_qa: bool = False
    per_video_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)

    def resolve_for(self, video_id: str) -> dict[str, Any]:
        """Return config dict for a single video (global + overrides for video_id)."""
        base: dict[str, Any] = {
            "project_name": self.project_name,
            "api_key": self.api_key,
            "translate_backend": self.translate_backend,
            "tts_provider": self.tts_provider,
            "tts_voice": self.tts_voice,
            "mix_mode": self.mix_mode,
            "enable_source_cleanup": self.enable_source_cleanup,
            "enable_translation_qa": self.enable_translation_qa,
        }
        override = self.per_video_overrides.get(video_id) or {}
        for k, v in override.items():
            if k in base:
                base[k] = v
        return base


@dataclass
class ProjectVideoEntry:
    video_id: str
    workspace: str
    added_at_unix: float
    source_path: str
    duration_s: float
    is_long: bool = False


@dataclass
class ProjectState:
    project_id: str
    project_root: str
    config: ProjectConfig
    videos: list[ProjectVideoEntry] = field(default_factory=list)
    version: int = 1


def _state_path(project_root: Path) -> Path:
    return project_root / "project_state.json"


def _write_state(state: ProjectState) -> None:
    path = _state_path(Path(state.project_root))
    payload = {
        "version": state.version,
        "project_id": state.project_id,
        "project_root": state.project_root,
        "config": asdict(state.config),
        "videos": [asdict(v) for v in state.videos],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, payload)


_SHARED_CONFIG_KEYS = {
    "translate_backend", "tts_provider", "tts_voice", "mix_mode",
    "enable_source_cleanup", "enable_translation_qa", "api_key",
}


def set_project_config(project_root: Path, patch: dict[str, Any]) -> dict[str, Any]:
    """Update shared project config fields (used by preset apply). Unknown keys ignored."""
    state = load_project(project_root)
    for k, v in (patch or {}).items():
        if k in _SHARED_CONFIG_KEYS and v is not None:
            setattr(state.config, k, v)
    _write_state(state)
    return asdict(state.config)


def load_project(project_root: Path) -> ProjectState:
    path = _state_path(project_root)
    if not path.is_file():
        raise ProjectError(f"Not a project (missing {path.name}): {project_root}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    cfg_raw = dict(raw.get("config") or {})
    cfg = ProjectConfig(
        project_name=str(cfg_raw.get("project_name") or raw.get("project_id") or "project"),
        api_key=str(cfg_raw.get("api_key") or ""),
        translate_backend=str(cfg_raw.get("translate_backend") or "block_v2"),
        tts_provider=str(cfg_raw.get("tts_provider") or "edge_tts"),
        tts_voice=str(cfg_raw.get("tts_voice") or ""),
        mix_mode=str(cfg_raw.get("mix_mode") or "replace_original_speech"),
        enable_source_cleanup=bool(cfg_raw.get("enable_source_cleanup")),
        enable_translation_qa=bool(cfg_raw.get("enable_translation_qa")),
        per_video_overrides=dict(cfg_raw.get("per_video_overrides") or {}),
    )
    videos = [
        ProjectVideoEntry(
            video_id=str(v["video_id"]),
            workspace=str(v["workspace"]),
            added_at_unix=float(v.get("added_at_unix") or 0.0),
            source_path=str(v.get("source_path") or ""),
            duration_s=float(v.get("duration_s") or 0.0),
            is_long=bool(v.get("is_long") or False),
        )
        for v in (raw.get("videos") or [])
    ]
    return ProjectState(
        project_id=str(raw["project_id"]),
        project_root=str(raw["project_root"]),
        config=cfg,
        videos=videos,
        version=int(raw.get("version") or 1),
    )


def init_project(
    projects_root: Path,
    project_name: str,
    *,
    project_id: str = "",
    config_overrides: dict[str, Any] | None = None,
    force: bool = False,
) -> ProjectState:
    projects_root = projects_root.expanduser().resolve()
    project_id = (project_id or "").strip() or _slug(project_name)
    project_root = projects_root / project_id
    if project_root.exists() and any(project_root.iterdir()) and not force:
        raise ProjectError(f"Project already exists and not empty: {project_root}")
    (project_root / "videos").mkdir(parents=True, exist_ok=True)

    cfg_dict: dict[str, Any] = {
        "project_name": project_name,
        **(config_overrides or {}),
    }
    cfg = ProjectConfig(
        project_name=str(cfg_dict.get("project_name") or project_name),
        api_key=str(cfg_dict.get("api_key") or ""),
        translate_backend=str(cfg_dict.get("translate_backend") or "block_v2"),
        tts_provider=str(cfg_dict.get("tts_provider") or "edge_tts"),
        tts_voice=str(cfg_dict.get("tts_voice") or ""),
        mix_mode=str(cfg_dict.get("mix_mode") or "replace_original_speech"),
        enable_source_cleanup=bool(cfg_dict.get("enable_source_cleanup")),
        enable_translation_qa=bool(cfg_dict.get("enable_translation_qa")),
        per_video_overrides=dict(cfg_dict.get("per_video_overrides") or {}),
    )
    state = ProjectState(
        project_id=project_id,
        project_root=str(project_root),
        config=cfg,
    )
    _write_state(state)
    return state


def add_video(
    project_root: Path,
    video_path: Path,
    *,
    video_id: str = "",
    duration_probe: Callable[[Path], float] | None = None,
    max_duration_s: float | None = None,
    override: dict[str, Any] | None = None,
    force: bool = False,
) -> ProjectVideoEntry:
    """
    Copy ``video_path`` into the project as a new video_workspace and register it.

    ``duration_probe`` defaults to engine.segment_manager.probe_video_duration; pass a
    stub in tests to avoid requiring ffprobe. Videos longer than
    ``SINGLE_VIDEO_THRESHOLD_S`` are accepted and flagged ``is_long=True`` so the
    translate/render phases route them through the long-video orchestrator. Pass
    ``max_duration_s`` to enforce a hard cap (e.g. for short-only projects).
    """
    state = load_project(project_root)
    video_path = video_path.expanduser()
    if not video_path.is_file():
        raise ProjectError(f"Video file not found: {video_path}")

    if duration_probe is None:
        from engine.segment_manager import probe_video_duration  # lazy

        duration_probe = probe_video_duration
    duration = float(duration_probe(video_path))
    if duration <= 0:
        raise ProjectError(f"Invalid duration for {video_path}: {duration}")
    if max_duration_s is not None and duration > max_duration_s:
        raise ProjectError(
            f"Video duration {duration:.1f}s exceeds cap {max_duration_s:.1f}s."
        )

    is_long = duration > SINGLE_VIDEO_THRESHOLD_S

    vid = (video_id or "").strip() or _slug(video_path.stem)
    if any(v.video_id == vid for v in state.videos) and not force:
        raise ProjectError(f"video_id already exists in project: {vid}")

    jw = Path(state.project_root) / "videos" / vid
    (jw / "input").mkdir(parents=True, exist_ok=True)
    (jw / "artifacts").mkdir(parents=True, exist_ok=True)
    dst = jw / "input" / "source.mp4"
    try:
        shutil.copyfile(video_path, dst)
    except OSError as e:
        raise ProjectError(f"Could not copy video: {e}") from e

    entry = ProjectVideoEntry(
        video_id=vid,
        workspace=str(jw.resolve()),
        added_at_unix=time.time(),
        source_path=str(video_path.resolve()),
        duration_s=duration,
        is_long=is_long,
    )
    state.videos = [v for v in state.videos if v.video_id != vid] + [entry]
    _write_state(state)
    return entry


def _video_status_snapshot(entry: ProjectVideoEntry) -> dict[str, Any]:
    jw = Path(entry.workspace)
    st = get_voice_edit_status(jw)
    vstate_path = jw / "video_state.json"
    vstate: dict[str, Any] = {}
    if vstate_path.is_file():
        try:
            vstate = json.loads(vstate_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            vstate = {}
    segment_count: int | None = None
    if entry.is_long:
        try:
            manifest = load_segment_manifest(jw)
            segment_count = len(manifest.segments)
        except SegmentError:
            segment_count = None
    return {
        "video_id": entry.video_id,
        "workspace": entry.workspace,
        "duration_s": entry.duration_s,
        "is_long": entry.is_long,
        "segment_count": segment_count,
        "voice_edit_status": st.voice_edit_status,
        "voice_edited": st.voice_edited,
        "pipeline_status": vstate.get("status"),
        "current_stage": vstate.get("current_stage"),
    }


def list_video_statuses(project_root: Path) -> list[dict[str, Any]]:
    state = load_project(project_root)
    return [_video_status_snapshot(v) for v in state.videos]


def _run_job_argv(jw: Path, cfg: dict[str, Any], *, to_stage: str) -> list[str]:
    argv = [
        "--job-workspace",
        str(jw),
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
    project_root = str(cfg.get("project_root") or "").strip()
    if project_root:
        argv.extend(["--project-root", project_root])
    api_key = str(cfg.get("api_key") or "").strip()
    if api_key:
        argv.extend(["--api-key", api_key])
    tts_voice = str(cfg.get("tts_voice") or "").strip()
    if tts_voice:
        argv.extend(["--tts-voice", tts_voice])
    if cfg.get("enable_translation_qa"):
        argv.append("--enable-translation-qa")
    if cfg.get("enable_source_cleanup"):
        argv.append("--enable-source-cleanup")
    return argv


def _resolve_max_workers(requested: int | None) -> int:
    if requested is None or requested <= 0:
        return MAX_PARALLEL_VIDEOS
    return min(int(requested), MAX_PARALLEL_VIDEOS)


def _voice_edit_completed(job_workspace: Path) -> bool:
    st = get_voice_edit_status(job_workspace)
    return bool(st.edited_voice_path) and (
        bool(st.voice_edited) or st.voice_edit_status == "voice_edited"
    )


def _run_translate_one(
    entry: ProjectVideoEntry,
    cfg: dict[str, Any],
    runner: Callable[[list[str]], int],
    long_video_workers: int,
) -> dict[str, Any]:
    jw = Path(entry.workspace)
    if entry.is_long:
        try:
            run_long_video_stage.do_plan_split(jw)
            result = run_long_video_stage.do_until_edit(
                jw,
                cfg=cfg,
                max_workers=long_video_workers,
                runner=runner,
            )
        except (run_long_video_stage.LongVideoError, SegmentError) as e:
            return {"video_id": entry.video_id, "ok": False, "error": f"long_video_failed: {e}"}
        if not result.get("ok"):
            return {
                "video_id": entry.video_id,
                "ok": False,
                "error": result.get("error") or "long_video_until_edit_failed",
                "segment_results": result.get("results"),
            }
        return {
            "video_id": entry.video_id,
            "ok": True,
            "is_long": True,
            "segment_count": result.get("segment_count"),
        }

    argv = _run_job_argv(jw, cfg, to_stage="translated")
    rc = runner(argv)
    if rc != 0:
        return {"video_id": entry.video_id, "ok": False, "error": f"run_job rc={rc}"}
    translated_voice = jw / "artifacts" / "translate" / "translated_voice.srt"
    if not translated_voice.is_file():
        return {
            "video_id": entry.video_id,
            "ok": False,
            "error": "translated_voice.srt missing (need translate_backend=block_v2)",
        }
    try:
        seed_edited_voice(jw, overwrite=False)
    except VoiceEditError as e:
        return {"video_id": entry.video_id, "ok": False, "error": f"seed_failed: {e}"}
    return {"video_id": entry.video_id, "ok": True}


def _run_render_one(
    entry: ProjectVideoEntry,
    cfg: dict[str, Any],
    runner: Callable[[list[str]], int],
    to_stage: str,
    long_video_workers: int,
) -> dict[str, Any]:
    jw = Path(entry.workspace)
    st = get_voice_edit_status(jw)
    if st.edited_voice_path is None:
        return {
            "video_id": entry.video_id,
            "ok": False,
            "error": "edited_voice.srt missing (user has not saved an edit yet)",
            "skipped": True,
        }
    if not _voice_edit_completed(jw):
        return {
            "video_id": entry.video_id,
            "ok": False,
            "error": (
                "voice edit not completed (edit artifacts/edit/edited_voice.srt and "
                "mark voice_edited before render)"
            ),
            "skipped": True,
            "required_action": "edit_edited_voice_srt",
            "voice_edit_status": st.voice_edit_status,
        }

    if entry.is_long:
        try:
            result = run_long_video_stage.do_after_edit(
                jw,
                cfg=cfg,
                to_stage=to_stage,
                max_workers=long_video_workers,
                runner=runner,
            )
        except (run_long_video_stage.LongVideoError, SegmentError) as e:
            return {"video_id": entry.video_id, "ok": False, "error": f"long_video_failed: {e}"}
        if not result.get("ok"):
            return {
                "video_id": entry.video_id,
                "ok": False,
                "error": result.get("error") or "long_video_after_edit_failed",
                "segment_results": result.get("results"),
            }
        return {
            "video_id": entry.video_id,
            "ok": True,
            "is_long": True,
            "segment_count": result.get("segment_count"),
            "merged_render_path": result.get("merged_render_path"),
        }

    argv = _run_job_argv(jw, cfg, to_stage=to_stage)
    rc = runner(argv)
    if rc != 0:
        return {"video_id": entry.video_id, "ok": False, "error": f"run_job rc={rc}"}
    return {"video_id": entry.video_id, "ok": True}


def run_translate_phase(
    project_root: Path,
    *,
    max_workers: int | None = None,
    runner: Callable[[list[str]], int] | None = None,
    video_ids: list[str] | None = None,
    long_video_workers: int = LONG_VIDEO_INNER_WORKERS_DEFAULT,
) -> list[dict[str, Any]]:
    """
    Run transcribe + translate + seed edited_voice for all (or selected) project videos.

    ``runner`` is injectable for tests; defaults to engine.run_job.main.
    """
    state = load_project(project_root)
    _runner = runner or run_job.main
    entries = state.videos
    if video_ids is not None:
        wanted = set(video_ids)
        entries = [v for v in entries if v.video_id in wanted]
    if not entries:
        return []

    workers = _resolve_max_workers(max_workers)
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                _run_translate_one,
                entry,
                {**state.config.resolve_for(entry.video_id), "project_root": state.project_root},
                _runner,
                long_video_workers,
            ): entry
            for entry in entries
        }
        for fut in as_completed(futures):
            results.append(fut.result())
    results.sort(key=lambda r: str(r.get("video_id") or ""))
    return results


def run_render_phase(
    project_root: Path,
    *,
    to_stage: str = "rendered",
    max_workers: int | None = None,
    runner: Callable[[list[str]], int] | None = None,
    video_ids: list[str] | None = None,
    long_video_workers: int = LONG_VIDEO_INNER_WORKERS_DEFAULT,
) -> list[dict[str, Any]]:
    """
    For every project video whose voice edit is explicitly completed: run finalize +
    TTS + align + mix + render (up to ``to_stage``).
    """
    if to_stage not in run_job.STAGE_ORDER:
        raise ProjectError(f"invalid to_stage: {to_stage}")
    state = load_project(project_root)
    _runner = runner or run_job.main
    entries = state.videos
    if video_ids is not None:
        wanted = set(video_ids)
        entries = [v for v in entries if v.video_id in wanted]
    if not entries:
        return []

    workers = _resolve_max_workers(max_workers)
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                _run_render_one,
                entry,
                {**state.config.resolve_for(entry.video_id), "project_root": state.project_root},
                _runner,
                to_stage,
                long_video_workers,
            ): entry
            for entry in entries
        }
        for fut in as_completed(futures):
            results.append(fut.result())
    results.sort(key=lambda r: str(r.get("video_id") or ""))
    return results


def run_auto_phase(
    project_root: Path,
    *,
    to_stage: str = "rendered",
    max_workers: int | None = None,
    runner: Callable[[list[str]], int] | None = None,
    video_ids: list[str] | None = None,
    long_video_workers: int = LONG_VIDEO_INNER_WORKERS_DEFAULT,
) -> dict[str, Any]:
    """Bulk auto pipeline (F2): translate + seed -> auto-approve voice edit -> render.

    The no-manual-review path for batch processing: each video that translates +
    seeds OK is automatically marked voice_edited, then rendered in parallel.
    Videos that fail translate are left untouched for inspection (not rendered).
    """
    t_results = run_translate_phase(
        project_root,
        max_workers=max_workers,
        runner=runner,
        video_ids=video_ids,
        long_video_workers=long_video_workers,
    )
    ok_ids = {str(r.get("video_id")) for r in t_results if r.get("ok")}

    approved: list[str] = []
    approve_errors: list[dict[str, str]] = []
    state = load_project(project_root)
    for entry in state.videos:
        if entry.video_id not in ok_ids:
            continue
        jw = Path(entry.workspace)
        try:
            if get_voice_edit_status(jw).edited_voice_path is not None and not _voice_edit_completed(jw):
                mark_voice_edited(jw)
            approved.append(entry.video_id)
        except VoiceEditError as e:
            approve_errors.append({"video_id": entry.video_id, "error": str(e)})

    # F1.1 — push shared project branding (logo/outro/intro/trim) onto each
    # video about to render, so a batch is branded consistently in one place.
    try:
        from engine.project_branding import apply_branding_to_video, has_project_branding

        if approved and has_project_branding(project_root):
            approved_set = set(approved)
            for entry in state.videos:
                if entry.video_id in approved_set:
                    try:
                        apply_branding_to_video(project_root, Path(entry.workspace))
                    except OSError as e:
                        approve_errors.append({"video_id": entry.video_id, "error": f"branding_failed: {e}"})
    except Exception:  # noqa: BLE001 - branding is best-effort, never block rendering
        pass

    r_results = run_render_phase(
        project_root,
        to_stage=to_stage,
        max_workers=max_workers,
        runner=runner,
        video_ids=approved,
        long_video_workers=long_video_workers,
    )
    return {
        "translate": t_results,
        "approved": approved,
        "approve_errors": approve_errors,
        "render": r_results,
    }
