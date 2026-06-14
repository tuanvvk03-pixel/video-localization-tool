"""E3 — anti-dedup transforms applied to the localized video.

UA teams re-run competitor creatives at scale, so platforms' duplicate detection
must be sidestepped: small speed change, horizontal mirror, slight zoom/crop, and
mild color shifts make each render look different while staying watchable. These
run on the *localized* video (before any intro/outro concat) so the user's own
branding clips are never mirrored/distorted.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


class VideoTransformError(RuntimeError):
    pass


def _probe_dims(ffprobe: str, path: Path) -> tuple[int, int]:
    cmd = [
        ffprobe, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise VideoTransformError(f"ffprobe failed for {path}: {(proc.stderr or '').strip()}")
    try:
        st = (json.loads(proc.stdout or "{}").get("streams") or [{}])[0]
        w, h = int(st.get("width") or 0), int(st.get("height") or 0)
    except (ValueError, TypeError, json.JSONDecodeError, IndexError) as e:
        raise VideoTransformError(f"Could not parse dimensions for {path}: {e}") from e
    if w <= 0 or h <= 0:
        raise VideoTransformError(f"Invalid dimensions for {path}.")
    return w, h


def _has_audio(ffprobe: str, path: Path) -> bool:
    cmd = [ffprobe, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=index", "-of", "csv=p=0", str(path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode == 0 and bool((proc.stdout or "").strip())


def apply_transforms(
    in_video: str | Path,
    out_video: str | Path,
    *,
    ffmpeg: str,
    ffprobe: str,
    speed: float = 1.0,
    hflip: bool = False,
    zoom: float = 1.0,
    brightness: float = 0.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    crf: int = 18,
    preset: str = "medium",
) -> dict:
    src = Path(in_video)
    out = Path(out_video)
    if not src.is_file():
        raise VideoTransformError(f"Input video not found: {src}")

    speed = float(speed)
    zoom = float(zoom)
    vparts: list[str] = []
    if hflip:
        vparts.append("hflip")
    if abs(zoom - 1.0) > 1e-6:
        w, h = _probe_dims(ffprobe, src)
        vparts.append(f"crop=iw/{zoom:.6f}:ih/{zoom:.6f}:(iw-iw/{zoom:.6f})/2:(ih-ih/{zoom:.6f})/2,scale={w}:{h}")
    if abs(brightness) > 1e-6 or abs(contrast - 1.0) > 1e-6 or abs(saturation - 1.0) > 1e-6:
        vparts.append(f"eq=brightness={brightness:.4f}:contrast={contrast:.4f}:saturation={saturation:.4f}")
    if abs(speed - 1.0) > 1e-6:
        vparts.append(f"setpts=PTS/{speed:.6f}")
    if not vparts:
        raise VideoTransformError("No transforms requested.")
    vparts.append("format=yuv420p")

    change_audio = abs(speed - 1.0) > 1e-6 and _has_audio(ffprobe, src)
    filter_complex = f"[0:v]{','.join(vparts)}[v]"
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src)]
    if change_audio:
        filter_complex += f";[0:a]atempo={speed:.6f}[a]"
        cmd += ["-filter_complex", filter_complex, "-map", "[v]", "-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-filter_complex", filter_complex, "-map", "[v]", "-map", "0:a?", "-c:a", "copy"]
    cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]

    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0 or not out.is_file():
        tail = ((proc.stderr or "") + "\n" + (proc.stdout or ""))[-4000:]
        raise VideoTransformError(f"ffmpeg transform failed (exit {proc.returncode}):\n{tail}")
    return {
        "speed": speed, "hflip": bool(hflip), "zoom": zoom,
        "brightness": brightness, "contrast": contrast, "saturation": saturation,
        "output_path": str(out.resolve()),
    }
