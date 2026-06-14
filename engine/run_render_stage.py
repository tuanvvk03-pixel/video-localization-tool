"""
Render stage (beta): mux source video + selected audio + optional subtitles to final mp4.

Inputs:
- input/source.mp4 (required)
- audio: artifacts/mixed/mixed_audio.wav (preferred) OR artifacts/aligned/voice_track_aligned.wav
- subtitles: artifacts/translate/final_subtitle.srt (optional depending on subtitle_mode)

Outputs:
- artifacts/render/<output-name> (default final.mp4)
- artifacts/render/render_manifest.json
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

from engine.ffmpeg_bins import resolve_ffmpeg_executable, resolve_ffprobe_executable
from engine.input_provenance import (
    build_input_provenance_dict,
    stale_final_subtitle_message,
    stale_manifest_input_provenance_message,
)
from engine.render_settings import RenderSettingsError, load_render_settings, transforms_active
from engine.subtitle_style import (
    SubtitleStyleError,
    resolve_subtitle_style,
    style_to_ass_force_style,
)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Render final mp4 (beta).")
    p.add_argument("--job-workspace", required=True, help="Job / video workspace root.")
    p.add_argument(
        "--audio-source",
        default="auto",
        choices=["auto", "mixed", "aligned"],
        help="Select audio input (default auto prefers mixed then aligned).",
    )
    p.add_argument(
        "--subtitle-mode",
        default="soft",
        choices=["soft", "burn", "none"],
        help="Subtitle mode (default soft).",
    )
    p.add_argument("--output-name", default="final.mp4")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--ffmpeg-bin", default="", help="Optional override path to ffmpeg executable.")
    p.add_argument("--ffprobe-bin", default="", help="Optional override path to ffprobe executable.")
    p.add_argument(
        "--project-root",
        default="",
        help="Optional project root for resolving style/global_subtitle_style.json (multi-video).",
    )
    p.add_argument(
        "--aspect-ratio",
        default="",
        choices=["", "source", "16:9", "9:16"],
        help="Optional final frame aspect ratio. Empty loads per-video render settings.",
    )
    p.add_argument(
        "--background-image",
        default="",
        help="Optional background image path for framed 16:9 / 9:16 renders.",
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


def _resolve_bin_override_or_env(bin_override: str, kind: str) -> tuple[str | None, str | None]:
    raw = (bin_override or "").strip()
    if raw:
        p = Path(raw).expanduser()
        if not p.is_file():
            return None, f"{kind} path does not exist: {raw!r}"
        return str(p.resolve()), None
    if kind == "ffmpeg":
        return resolve_ffmpeg_executable()
    found = resolve_ffprobe_executable()
    if not found:
        return None, (
            "ffprobe not found: set FFPROBE_BIN or pass --ffprobe-bin, or install ffprobe and add it to PATH."
        )
    return found, None


def _probe_duration_sec(ffprobe: str, media_path: Path) -> float | None:
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(media_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        return None
    s = (proc.stdout or "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def _probe_video_dimensions(ffprobe: str, video_path: Path) -> tuple[int, int] | None:
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        str(video_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        return None
    try:
        body = json.loads(proc.stdout or "{}")
        stream = (body.get("streams") or [{}])[0]
        w = int(stream.get("width") or 0)
        h = int(stream.get("height") or 0)
    except (TypeError, ValueError, json.JSONDecodeError, IndexError):
        return None
    if w <= 0 or h <= 0:
        return None
    return w, h


def _even(value: float) -> int:
    n = max(2, int(round(float(value))))
    return n if n % 2 == 0 else n + 1


def _target_dimensions(width: int, height: int, aspect_ratio: str) -> tuple[int, int]:
    if aspect_ratio == "16:9":
        short = min(width, height)
        return _even(short * 16.0 / 9.0), _even(short)
    if aspect_ratio == "9:16":
        short = min(width, height)
        return _even(short), _even(short * 16.0 / 9.0)
    return _even(width), _even(height)


def _resolve_layout_settings(
    job_workspace: Path,
    *,
    cli_aspect_ratio: str,
    cli_background_image: str,
) -> tuple[dict[str, object], Path | None, Path | None, dict[str, object] | None]:
    state = load_render_settings(job_workspace) or {}
    aspect = (cli_aspect_ratio or str(state.get("aspect_ratio") or "source")).strip()
    if aspect not in {"source", "16:9", "9:16"}:
        raise RenderSettingsError("aspect_ratio must be one of: source, 16:9, 9:16.")

    bg_raw = (cli_background_image or str(state.get("background_path") or "")).strip()
    bg_path: Path | None = None
    if bg_raw:
        candidate = Path(bg_raw).expanduser()
        if not candidate.is_absolute():
            candidate = job_workspace / candidate
        bg_path = candidate.resolve()
        if not bg_path.is_file():
            raise RenderSettingsError(f"Background image not found: {bg_path}")

    logo_raw = str(state.get("logo_path") or "").strip()
    logo_path: Path | None = None
    logo_info: dict[str, object] | None = None
    if logo_raw:
        cand = Path(logo_raw).expanduser()
        if not cand.is_absolute():
            cand = job_workspace / cand
        logo_path = cand.resolve()
        if not logo_path.is_file():
            raise RenderSettingsError(f"Logo image not found: {logo_path}")
        logo_info = {
            "position": str(state.get("logo_position") or "top-right"),
            "scale": float(state.get("logo_scale") or 0.15),
            "opacity": float(state.get("logo_opacity") or 1.0),
            "margin": float(state.get("logo_margin") or 0.03),
        }

    settings: dict[str, object] = {
        "aspect_ratio": aspect,
        "background_path": str(bg_path) if bg_path is not None else None,
        "background_original_filename": state.get("background_original_filename"),
        "logo_path": str(logo_path) if logo_path is not None else None,
        "logo_original_filename": state.get("logo_original_filename"),
    }
    if logo_info is not None:
        settings.update({f"logo_{k}": v for k, v in logo_info.items()})
    return settings, bg_path, logo_path, logo_info


def _resolve_branding(job_workspace: Path) -> tuple[Path | None, Path | None, float, float]:
    """Resolve E2 intro/outro clip paths + head/tail trim from render settings."""
    state = load_render_settings(job_workspace) or {}

    def _clip(key: str) -> Path | None:
        raw = str(state.get(key) or "").strip()
        if not raw:
            return None
        cand = Path(raw).expanduser()
        if not cand.is_absolute():
            cand = job_workspace / cand
        p = cand.resolve()
        if not p.is_file():
            raise RenderSettingsError(f"{key} not found: {p}")
        return p

    intro = _clip("intro_clip_path")
    outro = _clip("outro_clip_path")
    head = max(0.0, float(state.get("head_trim_sec") or 0.0))
    tail = max(0.0, float(state.get("tail_trim_sec") or 0.0))
    return intro, outro, head, tail


def _resolve_transforms(job_workspace: Path) -> dict[str, object] | None:
    """Resolve E3 anti-dedup transform params from render settings, or None."""
    s = load_render_settings(job_workspace) or {}
    if not transforms_active(s):
        return None
    return {
        "speed": float(s.get("transform_speed") or 1.0),
        "hflip": bool(s.get("transform_hflip")),
        "zoom": float(s.get("transform_zoom") or 1.0),
        "brightness": float(s.get("transform_brightness") or 0.0),
        "contrast": float(s.get("transform_contrast") or 1.0),
        "saturation": float(s.get("transform_saturation") or 1.0),
    }


def _sanitize_cmd(cmd: list[str]) -> str:
    return " ".join(shlex.quote(c) for c in cmd)


def _subtitles_filter_path(path: Path) -> str:
    # ffmpeg subtitles filter prefers forward slashes; drive letter ':' must be escaped.
    s = str(path.resolve()).replace("\\", "/")
    s = s.replace(":", "\\:")
    # Escape single quotes in path
    s = s.replace("'", "\\'")
    return s


def _build_burn_subtitle_filter(subtitle_path: Path, style: dict[str, object]) -> tuple[str, dict[str, object]]:
    burn_style = dict(style)
    if not burn_style.get("subtitle_background_color"):
        burn_style["subtitle_background_color"] = "#000000"
    sub_arg = _subtitles_filter_path(subtitle_path)
    sub_filter = f"subtitles=filename='{sub_arg}':charenc=UTF-8"
    force_style = style_to_ass_force_style(burn_style)
    if force_style:
        sub_filter += f":force_style='{force_style}'"
    return sub_filter, burn_style


def _logo_overlay_position(position: str, margin_px: int) -> str:
    m = max(0, int(margin_px))
    if position == "top-left":
        return f"{m}:{m}"
    if position == "bottom-left":
        return f"{m}:H-h-{m}"
    if position == "bottom-right":
        return f"W-w-{m}:H-h-{m}"
    # default top-right
    return f"W-w-{m}:{m}"


def _build_layout_filter_complex(
    *,
    target_w: int,
    target_h: int,
    background_input_index: int | None,
    burn_subtitle_path: Path | None,
    style: dict[str, object],
    logo_input_index: int | None = None,
    logo_info: dict[str, object] | None = None,
) -> tuple[str, dict[str, object] | None]:
    if background_input_index is None:
        parts = [
            (
                f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
                f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:color=black,"
                "setsar=1[vbase]"
            )
        ]
    else:
        parts = [
            (
                f"[{background_input_index}:v]scale={target_w}:{target_h}:"
                f"force_original_aspect_ratio=increase,crop={target_w}:{target_h},"
                "setsar=1[bg]"
            ),
            (
                f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
                "setsar=1[fg]"
            ),
            "[bg][fg]overlay=(W-w)/2:(H-h)/2:shortest=1[vbase]",
        ]

    cur = "vbase"
    burn_style: dict[str, object] | None = None
    if burn_subtitle_path is not None:
        sub_filter, burn_style = _build_burn_subtitle_filter(burn_subtitle_path, style)
        parts.append(f"[{cur}]{sub_filter}[vsub]")
        cur = "vsub"

    if logo_input_index is not None and logo_info is not None:
        scale = float(logo_info.get("scale") or 0.15)
        opacity = float(logo_info.get("opacity") or 1.0)
        margin = float(logo_info.get("margin") or 0.03)
        position = str(logo_info.get("position") or "top-right")
        logo_w = _even(max(2.0, target_w * scale))
        margin_px = int(round(target_w * margin))
        parts.append(
            f"[{logo_input_index}:v]scale={logo_w}:-1,format=rgba,"
            f"colorchannelmixer=aa={opacity:.4f}[logo]"
        )
        parts.append(f"[{cur}][logo]overlay={_logo_overlay_position(position, margin_px)}:shortest=1[vlogo]")
        cur = "vlogo"

    parts.append(f"[{cur}]format=yuv420p[vout]")
    return ";".join(parts), burn_style


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    job_workspace = Path(ns.job_workspace).expanduser().resolve()
    job_id = job_workspace.name

    started_at = time.time()

    ffmpeg, ffmpeg_err = _resolve_bin_override_or_env(ns.ffmpeg_bin, "ffmpeg")
    if ffmpeg is None:
        msg = ffmpeg_err or "ffmpeg not found."
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "failed",
                "current_stage": "render_failed",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1
    ffprobe, ffprobe_err = _resolve_bin_override_or_env(ns.ffprobe_bin, "ffprobe")
    if ffprobe is None:
        msg = ffprobe_err or "ffprobe not found."
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "failed",
                "current_stage": "render_failed",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1

    source_video = job_workspace / "input" / "source.mp4"
    if not source_video.is_file():
        msg = f"Missing canonical source video: {source_video}"
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "blocked",
                "current_stage": "input_required",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1

    mixed_audio = job_workspace / "artifacts" / "mixed" / "mixed_audio.wav"
    aligned_audio = job_workspace / "artifacts" / "aligned" / "voice_track_aligned.wav"
    audio_mode = ns.audio_source
    selected_audio: Path | None = None
    if audio_mode == "mixed":
        selected_audio = mixed_audio if mixed_audio.is_file() else None
    elif audio_mode == "aligned":
        selected_audio = aligned_audio if aligned_audio.is_file() else None
    else:
        selected_audio = mixed_audio if mixed_audio.is_file() else (aligned_audio if aligned_audio.is_file() else None)
        audio_mode = "mixed" if (selected_audio == mixed_audio) else ("aligned" if selected_audio else "auto")

    if selected_audio is None:
        msg = (
            "Missing audio input: expected artifacts/mixed/mixed_audio.wav or "
            "artifacts/aligned/voice_track_aligned.wav."
        )
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "failed",
                "current_stage": "render_failed",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1

    prov_check = (
        job_workspace / "artifacts" / "mixed" / "mix_manifest.json"
        if selected_audio == mixed_audio
        else job_workspace / "artifacts" / "aligned" / "alignment_manifest.json"
    )
    stale = stale_manifest_input_provenance_message(job_workspace, prov_check)
    if stale:
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "failed",
                "current_stage": "render_failed",
                "last_error": stale,
            },
        )
        print(stale, file=sys.stderr)
        return 1

    subtitle_mode = ns.subtitle_mode
    final_srt = job_workspace / "artifacts" / "translate" / "final_subtitle.srt"
    selected_subtitle: Path | None = final_srt if final_srt.is_file() else None
    if subtitle_mode != "none" and selected_subtitle is None:
        print(
            f"[render] WARNING: subtitle_mode={subtitle_mode} but missing {final_srt}; continuing without subtitles.",
            file=sys.stderr,
        )
        subtitle_mode = "none"

    if selected_subtitle is not None:
        sub_stale = stale_final_subtitle_message(job_workspace)
        if sub_stale:
            _merge_job_state(
                job_workspace,
                {
                    "job_id": job_id,
                    "job_workspace": str(job_workspace),
                    "status": "failed",
                    "current_stage": "render_failed",
                    "last_error": sub_stale,
                },
            )
            print(sub_stale, file=sys.stderr)
            return 1

    render_dir = job_workspace / "artifacts" / "render"
    render_dir.mkdir(parents=True, exist_ok=True)
    out_path = render_dir / (ns.output_name or "final.mp4")
    if out_path.exists() and not ns.overwrite:
        msg = f"Output exists (use --overwrite): {out_path}"
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "failed",
                "current_stage": "render_failed",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1

    video_dur = _probe_duration_sec(ffprobe, source_video)
    if video_dur is None or video_dur <= 0:
        msg = f"Could not probe video duration with ffprobe: {source_video}"
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "failed",
                "current_stage": "render_failed",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1

    audio_dur = _probe_duration_sec(ffprobe, selected_audio)

    project_root = (ns.project_root or "").strip()
    try:
        resolved_style = resolve_subtitle_style(
            job_workspace,
            project_root=(Path(project_root).expanduser().resolve() if project_root else None),
        )
    except SubtitleStyleError as e:
        msg = f"Invalid subtitle style: {e}"
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "failed",
                "current_stage": "render_failed",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1

    try:
        layout_settings, background_image, logo_image, logo_info = _resolve_layout_settings(
            job_workspace,
            cli_aspect_ratio=ns.aspect_ratio,
            cli_background_image=ns.background_image,
        )
    except RenderSettingsError as e:
        msg = f"Invalid render layout settings: {e}"
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "failed",
                "current_stage": "render_failed",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1

    source_dimensions = _probe_video_dimensions(ffprobe, source_video)
    if source_dimensions is None:
        msg = f"Could not probe source video dimensions with ffprobe: {source_video}"
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "failed",
                "current_stage": "render_failed",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1
    source_w, source_h = source_dimensions
    aspect_ratio = str(layout_settings.get("aspect_ratio") or "source")
    target_w, target_h = _target_dimensions(source_w, source_h, aspect_ratio)
    layout_transform = aspect_ratio in {"16:9", "9:16"} or background_image is not None
    logo_enabled = logo_image is not None
    # A logo overlay also requires a re-encode filtergraph (can't -c:v copy).
    needs_filtergraph = layout_transform or logo_enabled
    layout_settings.update(
        {
            "source_width": source_w,
            "source_height": source_h,
            "target_width": target_w,
            "target_height": target_h,
            "enabled": bool(layout_transform),
            "logo_enabled": bool(logo_enabled),
        }
    )

    overwrite_flag = "-y" if ns.overwrite else "-n"

    # Audio policy: pad if short, trim if long; never shorten video due to audio.
    audio_filter = f"apad,atrim=0:{video_dur:.6f}"
    # Build command in the safe order:
    # global args -> all inputs (-i ...) -> output/mapping args -> output path.
    global_args: list[str] = [
        ffmpeg,
        overwrite_flag,
        "-hide_banner",
        "-loglevel",
        "error",
    ]

    input_args: list[str] = [
        "-i",
        str(source_video),
        "-i",
        str(selected_audio),
    ]
    next_input_index = 2
    background_input_index: int | None = None
    if layout_transform and background_image is not None:
        background_input_index = next_input_index
        input_args.extend(["-loop", "1", "-i", str(background_image)])
        next_input_index += 1

    logo_input_index: int | None = None
    if logo_enabled and logo_image is not None:
        logo_input_index = next_input_index
        input_args.extend(["-loop", "1", "-i", str(logo_image)])
        next_input_index += 1

    has_sub_input = subtitle_mode != "none" and selected_subtitle is not None
    subtitle_input_index: int | None = None
    if has_sub_input:
        subtitle_input_index = next_input_index
        input_args.extend(["-i", str(selected_subtitle)])
        next_input_index += 1

    output_args: list[str] = []

    output_args.extend(
        [
            "-af",
            audio_filter,
            "-t",
            f"{video_dur:.6f}",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
        ]
    )

    if needs_filtergraph:
        filter_complex, _burn_style = _build_layout_filter_complex(
            target_w=target_w,
            target_h=target_h,
            background_input_index=background_input_index,
            burn_subtitle_path=(selected_subtitle if subtitle_mode == "burn" else None),
            style=resolved_style,
            logo_input_index=logo_input_index,
            logo_info=logo_info,
        )
        output_args.extend(
            [
                "-filter_complex",
                filter_complex,
                "-map",
                "[vout]",
                "-map",
                "1:a:0",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
            ]
        )
        if subtitle_mode == "soft" and has_sub_input and subtitle_input_index is not None:
            output_args.extend(["-map", f"{subtitle_input_index}:s:0", "-c:s", "mov_text"])
    elif subtitle_mode == "soft":
        output_args.extend(["-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy"])
        if has_sub_input and subtitle_input_index is not None:
            output_args.extend(["-map", f"{subtitle_input_index}:s:0", "-c:s", "mov_text"])
    elif subtitle_mode == "none":
        output_args.extend(["-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy"])
    else:
        # burn
        if selected_subtitle is None:
            msg = "Burn subtitle mode requested but final_subtitle.srt is missing."
            _merge_job_state(
                job_workspace,
                {
                    "job_id": job_id,
                    "job_workspace": str(job_workspace),
                    "status": "failed",
                    "current_stage": "render_failed",
                    "last_error": msg,
                },
            )
            print(msg, file=sys.stderr)
            return 1
        sub_filter, burn_style = _build_burn_subtitle_filter(selected_subtitle, resolved_style)
        output_args.extend(
            [
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-vf",
                sub_filter,
            ]
        )

    progress_path = render_dir / "render_progress.txt"
    try:
        progress_path.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        pass
    output_args.extend(["-progress", str(progress_path)])

    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "running",
            "current_stage": "rendered",
            "render_total_duration_sec": float(video_dur),
        },
    )

    cmd: list[str] = global_args + input_args + output_args + [str(out_path)]

    print(f"[render] Running ffmpeg command:\n{_sanitize_cmd(cmd)}", file=sys.stderr)

    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        tail = ((proc.stderr or "") + "\n" + (proc.stdout or ""))[-8000:]
        msg = f"ffmpeg failed (exit {proc.returncode}). tail:\n{tail}"
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "failed",
                "current_stage": "render_failed",
                "last_error": msg,
            },
        )
        _write_video_state(
            job_workspace,
            {
                "video_id": job_id,
                "status": "failed",
                "current_stage": "render_failed",
                "last_error": msg,
            },
        )
        _write_manifest(
            render_dir,
            {
                "status": "failed",
                "last_error": msg,
            },
            started_at,
            time.time(),
            source_video,
            selected_audio,
            selected_subtitle,
            audio_mode,
            subtitle_mode,
            ffmpeg,
            ffprobe,
            video_dur,
            audio_dur,
            out_path,
            cmd,
            build_input_provenance_dict(job_workspace),
            subtitle_style=resolved_style,
            render_layout=layout_settings,
        )
        print(msg, file=sys.stderr)
        return 1

    # E3 — anti-dedup transforms on the localized render. Applied BEFORE the
    # intro/outro concat so the user's own branding clips are never mirrored.
    transforms = _resolve_transforms(job_workspace)
    if transforms:
        from engine.video_transform import VideoTransformError, apply_transforms

        pre_tx = render_dir / "final_pretransform.mp4"
        try:
            if pre_tx.exists():
                pre_tx.unlink()
            out_path.replace(pre_tx)
            apply_transforms(pre_tx, out_path, ffmpeg=ffmpeg, ffprobe=ffprobe, **transforms)  # type: ignore[arg-type]
            layout_settings["transform"] = transforms
            print(f"[render] Applied anti-dedup transforms -> {out_path}", file=sys.stderr)
        except (VideoTransformError, OSError) as e:
            try:
                if not out_path.exists() and pre_tx.exists():
                    pre_tx.replace(out_path)
            except OSError:
                pass
            msg = f"Transform failed: {e}"
            _merge_job_state(
                job_workspace,
                {"job_id": job_id, "job_workspace": str(job_workspace), "status": "failed",
                 "current_stage": "render_failed", "last_error": msg},
            )
            _write_video_state(
                job_workspace,
                {"video_id": job_id, "status": "failed", "current_stage": "render_failed", "last_error": msg},
            )
            print(msg, file=sys.stderr)
            return 1

    # E2 — optional post-render assembly: trim head/tail of the localized video
    # and concat the user's intro/outro. Output stays at out_path (final.mp4); the
    # pre-assembly localized render is preserved as final_localized.mp4.
    try:
        intro_clip, outro_clip, head_trim, tail_trim = _resolve_branding(job_workspace)
    except RenderSettingsError as e:
        intro_clip = outro_clip = None
        head_trim = tail_trim = 0.0
        print(f"[render] WARNING: branding settings ignored: {e}", file=sys.stderr)
    if intro_clip is not None or outro_clip is not None or head_trim > 0 or tail_trim > 0:
        from engine.video_assemble import VideoAssembleError, assemble_branded_video

        localized_path = render_dir / "final_localized.mp4"
        try:
            if localized_path.exists():
                localized_path.unlink()
            out_path.replace(localized_path)
            branding_manifest = assemble_branded_video(
                main_video=localized_path,
                out_path=out_path,
                ffmpeg=ffmpeg,
                ffprobe=ffprobe,
                intro_clip=intro_clip,
                outro_clip=outro_clip,
                head_trim_sec=head_trim,
                tail_trim_sec=tail_trim,
            )
            layout_settings["branding"] = branding_manifest
            print(f"[render] Branding assembly done -> {out_path}", file=sys.stderr)
        except (VideoAssembleError, OSError) as e:
            # Restore the localized render so the job still has a final.mp4.
            try:
                if not out_path.exists() and localized_path.exists():
                    localized_path.replace(out_path)
            except OSError:
                pass
            msg = f"Branding assembly failed: {e}"
            _merge_job_state(
                job_workspace,
                {
                    "job_id": job_id,
                    "job_workspace": str(job_workspace),
                    "status": "failed",
                    "current_stage": "render_failed",
                    "last_error": msg,
                },
            )
            _write_video_state(
                job_workspace,
                {"video_id": job_id, "status": "failed", "current_stage": "render_failed", "last_error": msg},
            )
            print(msg, file=sys.stderr)
            return 1

    finished_at = time.time()
    manifest_path = _write_manifest(
        render_dir,
        {"status": "rendered", "last_error": None},
        started_at,
        finished_at,
        source_video,
        selected_audio,
        selected_subtitle,
        audio_mode,
        subtitle_mode,
        ffmpeg,
        ffprobe,
        video_dur,
        audio_dur,
        out_path,
        cmd,
        build_input_provenance_dict(job_workspace),
        subtitle_style=resolved_style,
        render_layout=layout_settings,
    )

    out_resolved = str(out_path.resolve())
    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "rendered",
            "current_stage": "rendered",
            "render_output_path": out_resolved,
            "render_manifest_path": str(manifest_path.resolve()),
            "last_error": None,
        },
    )
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "rendered",
            "current_stage": "rendered",
            "last_error": None,
            "artifact_paths": {"rendered_mp4": out_resolved, "render_manifest": str(manifest_path.resolve())},
        },
    )

    print(f"[render] Wrote {out_resolved}.", file=sys.stderr)
    return 0


def _write_manifest(
    render_dir: Path,
    status_block: dict,
    started_at: float,
    finished_at: float,
    source_video: Path,
    selected_audio: Path,
    selected_subtitle: Path | None,
    audio_source_mode: str,
    subtitle_mode: str,
    ffmpeg_bin: str,
    ffprobe_bin: str,
    video_duration_sec: float | None,
    audio_duration_sec: float | None,
    output_path: Path,
    ffmpeg_cmd: list[str],
    input_provenance: dict,
    subtitle_style: dict | None = None,
    render_layout: dict | None = None,
) -> Path:
    mp = render_dir / "render_manifest.json"
    body = {
        "source_video": str(source_video.resolve()),
        "selected_audio": str(selected_audio.resolve()),
        "selected_subtitle": str(selected_subtitle.resolve()) if selected_subtitle else None,
        "audio_source_mode": audio_source_mode,
        "subtitle_mode": subtitle_mode,
        "subtitle_style": subtitle_style or {},
        "render_layout": render_layout or {},
        "ffmpeg_bin": ffmpeg_bin,
        "ffprobe_bin": ffprobe_bin,
        "video_duration_sec": video_duration_sec,
        "audio_duration_sec": audio_duration_sec,
        "output_path": str(output_path.resolve()),
        "started_at": started_at,
        "finished_at": finished_at,
        "ffmpeg_command": _sanitize_cmd(ffmpeg_cmd),
        "input_provenance": input_provenance,
        **status_block,
    }
    write_json_atomic(mp, body)
    return mp


if __name__ == "__main__":
    raise SystemExit(main())

