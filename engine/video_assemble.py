"""E2 — post-render assembly: trim the localized video and bolt on intro/outro.

The render stage produces a localized ``final.mp4``. For the UA workflow we then
optionally:
  - trim the head (original hook) and/or tail (competitor outro) of that video,
  - prepend the user's intro clip and/or append their outro clip.

Intro/outro clips usually differ in resolution / fps / audio layout, so every
segment is normalized to the main video's geometry (scale+pad), fps, SAR and a
common audio format before a single ffmpeg ``concat`` filter joins them. Clips
without an audio track get synthesized silence so concat stays balanced.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

_AR = 48000  # common audio sample rate for concat
_ACH = "stereo"


class VideoAssembleError(RuntimeError):
    pass


def _probe_video(ffprobe: str, path: Path) -> tuple[int, int, float, float]:
    """Return (width, height, fps, duration_sec)."""
    cmd = [
        ffprobe, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate:format=duration",
        "-of", "json", str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise VideoAssembleError(f"ffprobe failed for {path}: {(proc.stderr or '').strip()}")
    try:
        body = json.loads(proc.stdout or "{}")
        st = (body.get("streams") or [{}])[0]
        w = int(st.get("width") or 0)
        h = int(st.get("height") or 0)
        num, _, den = str(st.get("r_frame_rate") or "30/1").partition("/")
        fps = (float(num) / float(den)) if den and float(den) != 0 else float(num or 30)
        dur = float((body.get("format") or {}).get("duration") or 0.0)
    except (ValueError, TypeError, json.JSONDecodeError, IndexError) as e:
        raise VideoAssembleError(f"Could not parse ffprobe output for {path}: {e}") from e
    if w <= 0 or h <= 0:
        raise VideoAssembleError(f"Invalid video dimensions for {path}.")
    return w, h, (fps if fps > 0 else 30.0), max(0.0, dur)


def _has_audio(ffprobe: str, path: Path) -> bool:
    cmd = [ffprobe, "-v", "error", "-select_streams", "a:0",
           "-show_entries", "stream=index", "-of", "csv=p=0", str(path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode == 0 and bool((proc.stdout or "").strip())


def assemble_branded_video(
    *,
    main_video: Path,
    out_path: Path,
    ffmpeg: str,
    ffprobe: str,
    intro_clip: Path | None = None,
    outro_clip: Path | None = None,
    head_trim_sec: float = 0.0,
    tail_trim_sec: float = 0.0,
    crf: int = 18,
    preset: str = "medium",
) -> dict:
    """Trim ``main_video`` head/tail and concat intro + main + outro into out_path.

    Returns a small manifest dict. Raises VideoAssembleError on bad input.
    """
    main_video = Path(main_video)
    if not main_video.is_file():
        raise VideoAssembleError(f"Main video not found: {main_video}")
    head = max(0.0, float(head_trim_sec or 0.0))
    tail = max(0.0, float(tail_trim_sec or 0.0))

    target_w, target_h, target_fps, main_dur = _probe_video(ffprobe, main_video)
    kept = main_dur - head - tail
    if kept <= 0.05:
        raise VideoAssembleError(
            f"Nothing left after trimming: duration={main_dur:.2f}s, head={head:.2f}s, tail={tail:.2f}s."
        )

    # Ordered segments: (path, is_main). Only the main is trimmed.
    segments: list[tuple[Path, bool]] = []
    if intro_clip is not None:
        if not Path(intro_clip).is_file():
            raise VideoAssembleError(f"Intro clip not found: {intro_clip}")
        segments.append((Path(intro_clip), False))
    segments.append((main_video, True))
    if outro_clip is not None:
        if not Path(outro_clip).is_file():
            raise VideoAssembleError(f"Outro clip not found: {outro_clip}")
        segments.append((Path(outro_clip), False))

    if len(segments) == 1 and head == 0.0 and tail == 0.0:
        raise VideoAssembleError("No assembly needed (no intro/outro and no trim).")

    inputs: list[str] = []
    filto: list[str] = []
    concat_labels: list[str] = []

    n_seg = len(segments)
    for i, (path, is_main) in enumerate(segments):
        inputs.extend(["-i", str(path)])

    # Geometry/fps/format normalization applied to every segment's video.
    vnorm = (
        f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
        f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"setsar=1,fps={target_fps:.6f},format=yuv420p"
    )
    anorm = f"aresample={_AR},aformat=sample_fmts=fltp:channel_layouts={_ACH}"

    # Build per-segment video/audio chains. For segments lacking audio we add a
    # silent anullsrc input sized to that segment's duration.
    next_silence_index = n_seg
    extra_silence_inputs: list[str] = []
    for i, (path, is_main) in enumerate(segments):
        if is_main and (head > 0.0 or tail > 0.0):
            end = main_dur - tail
            filto_v = (
                f"[{i}:v]trim=start={head:.6f}:end={end:.6f},setpts=PTS-STARTPTS,{vnorm}[v{i}]"
            )
        else:
            filto_v = f"[{i}:v]{vnorm}[v{i}]"
        filto.append(filto_v)

        if _has_audio(ffprobe, path):
            if is_main and (head > 0.0 or tail > 0.0):
                end = main_dur - tail
                filto.append(
                    f"[{i}:a]atrim=start={head:.6f}:end={end:.6f},asetpts=PTS-STARTPTS,{anorm}[a{i}]"
                )
            else:
                filto.append(f"[{i}:a]{anorm}[a{i}]")
        else:
            # synthesize silence for this segment's (possibly trimmed) duration
            _w, _h, _f, seg_dur = _probe_video(ffprobe, path)
            if is_main:
                seg_dur = max(0.05, main_dur - head - tail)
            extra_silence_inputs.extend(
                ["-f", "lavfi", "-t", f"{seg_dur:.6f}", "-i", f"anullsrc=r={_AR}:cl={_ACH}"]
            )
            filto.append(f"[{next_silence_index}:a]{anorm}[a{i}]")
            next_silence_index += 1

        concat_labels.append(f"[v{i}][a{i}]")

    filter_complex = ";".join(filto) + ";" + "".join(concat_labels) + f"concat=n={n_seg}:v=1:a=1[v][a]"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = (
        [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
        + inputs
        + extra_silence_inputs
        + [
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
            str(out_path),
        ]
    )
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0 or not out_path.is_file():
        tail_log = ((proc.stderr or "") + "\n" + (proc.stdout or ""))[-4000:]
        raise VideoAssembleError(f"ffmpeg assemble failed (exit {proc.returncode}):\n{tail_log}")

    return {
        "output_path": str(out_path.resolve()),
        "segments": [str(p.resolve()) for p, _ in segments],
        "target_width": target_w,
        "target_height": target_h,
        "target_fps": round(target_fps, 3),
        "head_trim_sec": head,
        "tail_trim_sec": tail,
        "intro": str(Path(intro_clip).resolve()) if intro_clip else None,
        "outro": str(Path(outro_clip).resolve()) if outro_clip else None,
    }
