"""
Mix stage: produce artifacts/mixed/mixed_audio.wav.

Mix modes:
- replace_original_speech (default): output only aligned Vietnamese voice track.
- duck_original_speech: keep original audio as background, but strongly duck it during Vietnamese speech.

Speech activity is derived from artifacts/aligned/alignment_manifest.json cues (placed_* frames).
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import argparse
import json
import shutil
import subprocess
import sys
from math import log10, pow
from pathlib import Path

from engine.ffmpeg_bins import resolve_ffmpeg_executable, resolve_ffprobe_executable
from engine.input_provenance import (
    build_input_provenance_dict,
    stale_manifest_input_provenance_message,
)
from engine.voice_coverage_report import REPORT_FILENAME

BACKGROUND_BASE_GAIN = 0.28
VOICE_BOOST_GAIN = 1.8
VOICE_LIMIT = 0.96
FINAL_LIMIT = 0.97
BGM_LOOP_TOLERANCE_S = 0.05
# E4 — instrumental music bed gain when keeping the original music (vocals removed).
MUSIC_BED_GAIN = 0.6


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mix aligned voice track into a mixed audio output.")
    p.add_argument("--job-workspace", required=True, help="Job / video workspace root.")
    p.add_argument(
        "--mix-mode",
        default="replace_original_speech",
        choices=["replace_original_speech", "duck_original_speech", "keep_music_replace_voice"],
        help="Mix policy (default replace_original_speech). keep_music_replace_voice uses "
        "Demucs to remove the original vocals and keep the music bed.",
    )
    p.add_argument(
        "--demucs-device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="Device for Demucs vocal separation (keep_music_replace_voice mode).",
    )
    # Backward compatible alias (deprecated)
    p.add_argument(
        "--mode",
        default="",
        help="Deprecated alias for --mix-mode. Supported: voice_only -> replace_original_speech",
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
    p.add_argument("--bgm", default="", help="Optional normalized BGM WAV path.")
    p.add_argument("--bgm-volume-db", type=float, default=-20.0, help="BGM gain in dB.")
    p.add_argument(
        "--bgm-loop",
        action="store_true",
        help="Force BGM stream looping. Short BGM loops automatically to cover the video duration.",
    )
    p.add_argument("--bgm-fade-in-ms", type=int, default=500, help="BGM fade-in in ms.")
    p.add_argument("--bgm-fade-out-ms", type=int, default=1000, help="BGM fade-out in ms.")
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


def _ms_from_frames(frames: int, sample_rate_hz: int) -> int:
    sr = max(1, int(sample_rate_hz))
    return int(round((max(0, int(frames)) / float(sr)) * 1000.0))


def _build_duck_segments_from_alignment_manifest(
    manifest: dict,
    *,
    merge_gap_ms: int,
) -> list[tuple[int, int]]:
    sr = int(manifest.get("sample_rate_hz") or 0) or 24000
    cues = manifest.get("cues") or []
    raw: list[tuple[int, int]] = []
    for cue in cues:
        try:
            psf = int(cue.get("placed_start_frame"))
            pef = int(cue.get("placed_end_frame"))
        except Exception:
            continue
        if pef <= psf:
            continue
        s_ms = _ms_from_frames(psf, sr)
        e_ms = _ms_from_frames(pef, sr)
        if e_ms <= s_ms:
            continue
        raw.append((s_ms, e_ms))

    raw.sort(key=lambda x: (x[0], x[1]))
    if not raw:
        return []

    gap = max(0, int(merge_gap_ms))
    merged: list[tuple[int, int]] = []
    cur_s, cur_e = raw[0]
    for s, e in raw[1:]:
        if s <= cur_e + gap:
            cur_e = max(cur_e, e)
        else:
            merged.append((cur_s, cur_e))
            cur_s, cur_e = s, e
    merged.append((cur_s, cur_e))
    return merged


def _duck_gain_linear(db: float) -> float:
    # db is negative for attenuation
    return float(pow(10.0, float(db) / 20.0))


def _ffmpeg_duck_volume_expr(
    segments_ms: list[tuple[int, int]],
    *,
    duck_gain_db: float,
    fade_ms: int,
) -> str:
    g = _duck_gain_linear(duck_gain_db)
    # Clamp to a safe range (avoid exact 0 for some filters)
    if g < 0.0001:
        g = 0.0001
    if g > 1.0:
        g = 1.0
    f = max(0.0, float(int(fade_ms)) / 1000.0)

    expr = "1"
    for s_ms, e_ms in segments_ms:
        s = max(0.0, float(int(s_ms)) / 1000.0)
        e = max(s, float(int(e_ms)) / 1000.0)
        if e <= s:
            continue
        # If segment is too short, fade duration must not exceed half segment.
        f_eff = min(f, max(0.0, (e - s) / 2.0))
        if f_eff <= 0.0:
            seg = f"if(between(t\\,{s:.6f}\\,{e:.6f})\\,{g:.6f}\\,1)"
        else:
            seg = (
                "if(between(t\\,{s}\\,{e})\\,"
                "if(between(t\\,{s}\\,{sf})\\,1-({one_minus_g})*((t-{s})/{f})\\,"
                "if(between(t\\,{ef}\\,{e})\\,{g}+({one_minus_g})*((t-{ef})/{f})\\,"
                "{g}))\\,"
                "1)"
            ).format(
                s=f"{s:.6f}",
                e=f"{e:.6f}",
                sf=f"{(s + f_eff):.6f}",
                ef=f"{(e - f_eff):.6f}",
                f=f"{f_eff:.6f}",
                g=f"{g:.6f}",
                one_minus_g=f"{(1.0 - g):.6f}",
            )
        expr = f"min({expr}\\,{seg})"
    return expr


def _compose_background_volume_expr(base_expr: str, *, base_gain: float) -> str:
    gain = max(0.0001, min(1.0, float(base_gain)))
    return f"{gain:.6f}*({base_expr})"


def _probe_duration_s(path: Path) -> float:
    ffprobe = resolve_ffprobe_executable()
    if not ffprobe:
        return 0.0
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        return 0.0
    try:
        return max(0.0, float((proc.stdout or "0").strip()))
    except ValueError:
        return 0.0


def _bgm_filter_chain(
    *,
    input_label: str = "2:a",
    duration_s: float,
    volume_db: float,
    fade_in_ms: int,
    fade_out_ms: int,
) -> str:
    duration = max(0.001, float(duration_s))
    fade_in = max(0.0, min(float(fade_in_ms) / 1000.0, duration / 2.0))
    fade_out = max(0.0, min(float(fade_out_ms) / 1000.0, duration / 2.0))
    parts = [f"[{input_label}]"]
    # The BGM input may be stream-looped before decoding when it is shorter than
    # the target. apad is still kept as a harmless fallback before the final trim.
    parts.append("apad,")
    parts.append(f"atrim=0:{duration:.6f},asetpts=PTS-STARTPTS,")
    if fade_in > 0:
        parts.append(f"afade=t=in:st=0:d={fade_in:.6f},")
    if fade_out > 0:
        fade_start = max(0.0, duration - fade_out)
        parts.append(f"afade=t=out:st={fade_start:.6f}:d={fade_out:.6f},")
    parts.append(f"volume={float(volume_db):.2f}dB,aresample=async=1:first_pts=0[bgm]")
    return "".join(parts)


def _extract_audio_wav(ffmpeg: str, source_video: Path, out_wav: Path) -> None:
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(source_video), "-vn", "-ac", "2", "-ar", "44100",
        "-c:a", "pcm_s16le", str(out_wav),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0 or not out_wav.is_file():
        tail = ((proc.stderr or "") + "\n" + (proc.stdout or ""))[-4000:]
        raise RuntimeError(f"Failed extracting source audio for separation:\n{tail}")


def _prepare_instrumental(
    *, ffmpeg: str, source_video: Path, mixed_dir: Path, device: str
) -> tuple[Path, dict]:
    """Extract the source audio and run Demucs to get a vocals-removed music bed."""
    from engine.vocal_separation import VocalSeparationError, separate_instrumental

    if not source_video.is_file():
        raise RuntimeError(f"Missing source video for keep_music_replace_voice: {source_video}")
    orig_audio = mixed_dir / "_source_audio.wav"
    _extract_audio_wav(ffmpeg, source_video, orig_audio)
    instrumental = mixed_dir / "instrumental.wav"
    try:
        sep = separate_instrumental(orig_audio, instrumental, device=device)
    except VocalSeparationError as e:
        raise RuntimeError(str(e))
    finally:
        try:
            orig_audio.unlink(missing_ok=True)
        except OSError:
            pass
    return instrumental, sep


def _mix_with_bgm(
    *,
    ffmpeg: str,
    source_video: Path,
    aligned_voice: Path,
    bgm_path: Path,
    mixed_audio: Path,
    mix_mode: str,
    duration_s: float,
    bgm_volume_db: float,
    bgm_loop: bool,
    bgm_fade_in_ms: int,
    bgm_fade_out_ms: int,
    duck_gain_db: float,
    duck_fade_ms: int,
    duck_merge_gap_ms: int,
    align_manifest: Path,
) -> tuple[int, bool]:
    bgm_chain = _bgm_filter_chain(
        duration_s=duration_s,
        volume_db=bgm_volume_db,
        fade_in_ms=bgm_fade_in_ms,
        fade_out_ms=bgm_fade_out_ms,
    )
    if mix_mode == "replace_original_speech":
        filter_complex = (
            f"{bgm_chain};"
            f"[1:a]volume={VOICE_BOOST_GAIN:.3f},alimiter=limit={VOICE_LIMIT:.2f},"
            "aresample=async=1:first_pts=0[voice];"
            f"[bgm][voice]amix=inputs=2:normalize=0:dropout_transition=0:duration=first,"
            f"alimiter=limit={FINAL_LIMIT:.2f}[m]"
        )
    elif mix_mode == "duck_original_speech":
        try:
            align_body = json.loads(align_manifest.read_text(encoding="utf-8"))
        except Exception as e:
            raise RuntimeError(f"Failed reading alignment_manifest.json: {e}")
        segments = _build_duck_segments_from_alignment_manifest(
            align_body, merge_gap_ms=int(duck_merge_gap_ms)
        )
        vol_expr = _ffmpeg_duck_volume_expr(
            segments,
            duck_gain_db=float(duck_gain_db),
            fade_ms=int(duck_fade_ms),
        )
        background_expr = _compose_background_volume_expr(
            vol_expr,
            base_gain=BACKGROUND_BASE_GAIN,
        )
        filter_complex = (
            f"[0:a]volume='{background_expr}',aresample=async=1:first_pts=0[bg];"
            f"{bgm_chain};"
            f"[1:a]volume={VOICE_BOOST_GAIN:.3f},alimiter=limit={VOICE_LIMIT:.2f},"
            "aresample=async=1:first_pts=0[voice];"
            f"[bg][bgm][voice]amix=inputs=3:normalize=0:dropout_transition=0:duration=first,"
            f"alimiter=limit={FINAL_LIMIT:.2f}[m]"
        )
    elif mix_mode == "keep_music_replace_voice":
        # input 0 is the Demucs instrumental (vocals removed) — a constant music bed.
        filter_complex = (
            f"[0:a]volume={MUSIC_BED_GAIN:.3f},aresample=async=1:first_pts=0[bed];"
            f"{bgm_chain};"
            f"[1:a]volume={VOICE_BOOST_GAIN:.3f},alimiter=limit={VOICE_LIMIT:.2f},"
            "aresample=async=1:first_pts=0[voice];"
            f"[bed][bgm][voice]amix=inputs=3:normalize=0:dropout_transition=0:duration=first,"
            f"alimiter=limit={FINAL_LIMIT:.2f}[m]"
        )
    else:
        raise RuntimeError(f"Unsupported mix_mode: {mix_mode!r}")
    input_args = [
        "-i",
        str(source_video),
        "-i",
        str(aligned_voice),
    ]
    if bgm_loop:
        input_args.extend(["-stream_loop", "-1"])
    input_args.extend(["-i", str(bgm_path)])

    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        *input_args,
        "-filter_complex",
        filter_complex,
        "-map",
        "[m]",
        "-c:a",
        "pcm_s16le",
        str(mixed_audio),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        tail = ((proc.stderr or "") + "\n" + (proc.stdout or ""))[-8000:]
        raise RuntimeError(f"ffmpeg BGM mix failed (exit {proc.returncode}). tail:\n{tail}")
    return (0, mix_mode in ("duck_original_speech", "keep_music_replace_voice"))


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    job_workspace = Path(ns.job_workspace).expanduser().resolve()
    job_id = job_workspace.name

    aligned_voice = job_workspace / "artifacts" / "aligned" / "voice_track_aligned.wav"
    align_manifest = job_workspace / "artifacts" / "aligned" / "alignment_manifest.json"
    source_video = job_workspace / "input" / "source.mp4"

    mix_mode = (ns.mix_mode or "").strip()
    if (ns.mode or "").strip():
        legacy = ns.mode.strip()
        if legacy == "voice_only":
            mix_mode = "replace_original_speech"
        else:
            mix_mode = legacy
    stale = stale_manifest_input_provenance_message(job_workspace, align_manifest)
    if stale:
        msg = stale
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "failed",
                "current_stage": "mix_failed",
                "last_error": msg,
            },
        )
        _write_video_state(
            job_workspace,
            {
                "video_id": job_id,
                "status": "failed",
                "current_stage": "mix_failed",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1

    cov_path = job_workspace / "artifacts" / "aligned" / REPORT_FILENAME
    if cov_path.is_file():
        try:
            cov = json.loads(cov_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cov = {}
        cw = cov.get("warnings") or []
        if cw:
            print(f"[mix] voice_coverage warnings: {cw} ({cov_path.name})", file=sys.stderr)
        if (
            mix_mode == "replace_original_speech"
            and cov.get("recommend_mix_mode") == "duck_original_speech"
        ):
            print(
                "[mix] Voice coverage looks low: consider re-running with "
                "--mix-mode duck_original_speech so original audio fills long gaps.",
                file=sys.stderr,
            )

    if not aligned_voice.is_file():
        msg = f"Missing aligned voice track: {aligned_voice}"
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "blocked",
                "current_stage": "aligned_required",
                "last_error": msg,
                "mixed_audio_path": None,
                "mix_manifest_path": None,
            },
        )
        _write_video_state(
            job_workspace,
            {
                "video_id": job_id,
                "status": "blocked",
                "current_stage": "aligned_required",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1

    mixed_dir = job_workspace / "artifacts" / "mixed"
    mixed_dir.mkdir(parents=True, exist_ok=True)
    mixed_audio = mixed_dir / "mixed_audio.wav"
    mix_manifest = mixed_dir / "mix_manifest.json"
    bgm_path: Path | None = None
    mix_duration_s: float | None = None
    bgm_duration_s: float | None = None
    bgm_auto_looped = False
    bgm_stream_loop = False
    if str(ns.bgm or "").strip():
        candidate = Path(str(ns.bgm)).expanduser()
        if not candidate.is_absolute():
            candidate = job_workspace / candidate
        bgm_path = candidate.resolve()
        if not bgm_path.is_file():
            msg = f"Missing BGM file: {bgm_path}"
            _merge_job_state(
                job_workspace,
                {
                    "job_id": job_id,
                    "job_workspace": str(job_workspace),
                    "status": "failed",
                    "current_stage": "mix_failed",
                    "last_error": msg,
                },
            )
            _write_video_state(
                job_workspace,
                {
                    "video_id": job_id,
                    "status": "failed",
                    "current_stage": "mix_failed",
                    "last_error": msg,
                },
            )
            print(msg, file=sys.stderr)
            return 1

    try:
        instrumental_path: Path | None = None
        separation_manifest: dict | None = None
        if mix_mode == "keep_music_replace_voice":
            ffmpeg, ffmpeg_err = resolve_ffmpeg_executable()
            if ffmpeg is None:
                raise RuntimeError(ffmpeg_err or "ffmpeg not found")
            print("[mix] keep_music_replace_voice: separating vocals with Demucs...", file=sys.stderr)
            instrumental_path, separation_manifest = _prepare_instrumental(
                ffmpeg=ffmpeg, source_video=source_video, mixed_dir=mixed_dir, device=ns.demucs_device,
            )

        if bgm_path is not None:
            if mix_mode == "duck_original_speech" and not source_video.is_file():
                raise RuntimeError(f"Missing source video for duck mode: {source_video}")
            ffmpeg, ffmpeg_err = resolve_ffmpeg_executable()
            if ffmpeg is None:
                raise RuntimeError(ffmpeg_err or "ffmpeg not found")
            duration_source = source_video if source_video.is_file() else aligned_voice
            duration_s = _probe_duration_s(duration_source) or _probe_duration_s(aligned_voice)
            if duration_s <= 0:
                raise RuntimeError("Could not determine mix duration for BGM.")
            bgm_duration = _probe_duration_s(bgm_path)
            if bgm_duration <= 0:
                raise RuntimeError(f"Could not determine BGM duration: {bgm_path}")
            mix_duration_s = float(duration_s)
            bgm_duration_s = float(bgm_duration)
            bgm_auto_looped = bgm_duration_s + BGM_LOOP_TOLERANCE_S < mix_duration_s
            bgm_stream_loop = bool(ns.bgm_loop) or bgm_auto_looped
            if mix_mode == "keep_music_replace_voice":
                ffmpeg_source = instrumental_path  # type: ignore[assignment]
            else:
                ffmpeg_source = source_video if source_video.is_file() else aligned_voice
            _mix_with_bgm(
                ffmpeg=ffmpeg,
                source_video=ffmpeg_source,
                aligned_voice=aligned_voice,
                bgm_path=bgm_path,
                mixed_audio=mixed_audio,
                mix_mode=mix_mode,
                duration_s=duration_s,
                bgm_volume_db=float(ns.bgm_volume_db),
                bgm_loop=bgm_stream_loop,
                bgm_fade_in_ms=int(ns.bgm_fade_in_ms),
                bgm_fade_out_ms=int(ns.bgm_fade_out_ms),
                duck_gain_db=float(ns.duck_gain_db),
                duck_fade_ms=int(ns.duck_fade_ms),
                duck_merge_gap_ms=int(ns.duck_merge_gap_ms),
                align_manifest=align_manifest,
            )
        elif mix_mode == "replace_original_speech":
            shutil.copy2(aligned_voice, mixed_audio)
        elif mix_mode == "duck_original_speech":
            if not source_video.is_file():
                raise RuntimeError(f"Missing source video for duck mode: {source_video}")
            ffmpeg, ffmpeg_err = resolve_ffmpeg_executable()
            if ffmpeg is None:
                raise RuntimeError(ffmpeg_err or "ffmpeg not found")

            try:
                align_body = json.loads(align_manifest.read_text(encoding="utf-8"))
            except Exception as e:
                raise RuntimeError(f"Failed reading alignment_manifest.json: {e}")

            segments = _build_duck_segments_from_alignment_manifest(
                align_body, merge_gap_ms=int(ns.duck_merge_gap_ms)
            )
            vol_expr = _ffmpeg_duck_volume_expr(
                segments,
                duck_gain_db=float(ns.duck_gain_db),
                fade_ms=int(ns.duck_fade_ms),
            )
            background_expr = _compose_background_volume_expr(
                vol_expr,
                base_gain=BACKGROUND_BASE_GAIN,
            )
            filter_complex = (
                f"[0:a]volume='{background_expr}',aresample=async=1:first_pts=0[bg];"
                f"[1:a]volume={VOICE_BOOST_GAIN:.3f},alimiter=limit={VOICE_LIMIT:.2f},"
                "aresample=async=1:first_pts=0[voice];"
                f"[bg][voice]amix=inputs=2:normalize=0:dropout_transition=0:duration=longest,"
                f"alimiter=limit={FINAL_LIMIT:.2f}[m]"
            )
            cmd = [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(source_video),
                "-i",
                str(aligned_voice),
                "-filter_complex",
                filter_complex,
                "-map",
                "[m]",
                "-c:a",
                "pcm_s16le",
                str(mixed_audio),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if proc.returncode != 0:
                tail = ((proc.stderr or "") + "\n" + (proc.stdout or ""))[-8000:]
                raise RuntimeError(f"ffmpeg duck mix failed (exit {proc.returncode}). tail:\n{tail}")
        elif mix_mode == "keep_music_replace_voice":
            ffmpeg, ffmpeg_err = resolve_ffmpeg_executable()
            if ffmpeg is None:
                raise RuntimeError(ffmpeg_err or "ffmpeg not found")
            # [0:a] = Demucs instrumental (vocals removed), [1:a] = new aligned voice.
            filter_complex = (
                f"[0:a]volume={MUSIC_BED_GAIN:.3f},aresample=async=1:first_pts=0[bed];"
                f"[1:a]volume={VOICE_BOOST_GAIN:.3f},alimiter=limit={VOICE_LIMIT:.2f},"
                "aresample=async=1:first_pts=0[voice];"
                f"[bed][voice]amix=inputs=2:normalize=0:dropout_transition=0:duration=longest,"
                f"alimiter=limit={FINAL_LIMIT:.2f}[m]"
            )
            cmd = [
                ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(instrumental_path),
                "-i", str(aligned_voice),
                "-filter_complex", filter_complex,
                "-map", "[m]", "-c:a", "pcm_s16le", str(mixed_audio),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if proc.returncode != 0:
                tail = ((proc.stderr or "") + "\n" + (proc.stdout or ""))[-8000:]
                raise RuntimeError(f"ffmpeg keep_music mix failed (exit {proc.returncode}). tail:\n{tail}")
        else:
            raise RuntimeError(f"Unsupported mix_mode: {mix_mode!r}")
    except OSError as e:
        msg = f"Mix failed: {e}"
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "failed",
                "current_stage": "mix_failed",
                "last_error": msg,
            },
        )
        _write_video_state(
            job_workspace,
            {
                "video_id": job_id,
                "status": "failed",
                "current_stage": "mix_failed",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1
    except Exception as e:
        msg = f"Mix failed: {e}"
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "failed",
                "current_stage": "mix_failed",
                "last_error": msg,
            },
        )
        _write_video_state(
            job_workspace,
            {
                "video_id": job_id,
                "status": "failed",
                "current_stage": "mix_failed",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1

    duck_segments_count = 0
    used_original_audio = mix_mode in ("duck_original_speech", "keep_music_replace_voice")
    if mix_mode == "duck_original_speech":
        try:
            align_body2 = json.loads(align_manifest.read_text(encoding="utf-8"))
            duck_segments_count = len(
                _build_duck_segments_from_alignment_manifest(
                    align_body2, merge_gap_ms=int(ns.duck_merge_gap_ms)
                )
            )
        except Exception:
            duck_segments_count = 0

    bgm_duration_policy: str | None = None
    if bgm_path is not None:
        if bgm_auto_looped:
            bgm_duration_policy = "loop_to_duration"
        elif (
            bgm_duration_s is not None
            and mix_duration_s is not None
            and bgm_duration_s > mix_duration_s + BGM_LOOP_TOLERANCE_S
        ):
            bgm_duration_policy = "trim_to_duration"
        else:
            bgm_duration_policy = "match_duration"

    manifest_body = {
        "version": 2,
        "mix_mode": mix_mode,
        "used_aligned_voice_track": "artifacts/aligned/voice_track_aligned.wav",
        "used_original_audio": "input/source.mp4" if used_original_audio else None,
        "used_bgm": str(bgm_path) if bgm_path is not None else None,
        "bgm_volume_db": float(ns.bgm_volume_db) if bgm_path is not None else None,
        "bgm_loop": bgm_stream_loop if bgm_path is not None else None,
        "bgm_loop_requested": bool(ns.bgm_loop) if bgm_path is not None else None,
        "bgm_auto_looped": bgm_auto_looped if bgm_path is not None else None,
        "bgm_duration_sec": bgm_duration_s if bgm_path is not None else None,
        "mix_duration_sec": mix_duration_s if bgm_path is not None else None,
        "bgm_duration_policy": bgm_duration_policy,
        "bgm_fade_in_ms": int(ns.bgm_fade_in_ms) if bgm_path is not None else None,
        "bgm_fade_out_ms": int(ns.bgm_fade_out_ms) if bgm_path is not None else None,
        "duck_segments_count": int(duck_segments_count),
        "vocal_separation": separation_manifest,
        "original_audio_gain_db_when_ducked": float(ns.duck_gain_db) if used_original_audio else None,
        "original_audio_base_gain_db": (
            round(20.0 * log10(BACKGROUND_BASE_GAIN), 2)
            if used_original_audio
            else None
        ),
        "dub_voice_boost_gain_db": (
            round(20.0 * log10(VOICE_BOOST_GAIN), 2)
            if used_original_audio
            else None
        ),
        "status": "mixed",
        # Backward-compat fields (kept for older readers)
        "mode": mix_mode,
        "policy": {
            "original_audio": ("ducked" if used_original_audio else "muted"),
            "voice_track": "aligned_only",
        },
        "inputs": {
            "aligned_voice_track": "artifacts/aligned/voice_track_aligned.wav",
            "original_audio": "input/source.mp4" if used_original_audio else None,
            "bgm": str(bgm_path) if bgm_path is not None else None,
            "alignment_manifest": "artifacts/aligned/alignment_manifest.json",
        },
        "outputs": {"mixed_audio": "artifacts/mixed/mixed_audio.wav"},
        "input_provenance": build_input_provenance_dict(job_workspace),
    }
    mix_manifest.write_text(
        json.dumps(manifest_body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    mixed_resolved = str(mixed_audio.resolve())
    manifest_resolved = str(mix_manifest.resolve())
    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "mixed",
            "current_stage": "mixed",
            "mixed_audio_path": mixed_resolved,
            "mix_manifest_path": manifest_resolved,
            "last_error": None,
        },
    )
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "mixed",
            "current_stage": "mixed",
            "last_error": None,
            "artifact_paths": {
                "mixed_audio": mixed_resolved,
                "mix_manifest": manifest_resolved,
            },
        },
    )
    print(f"[mix] Wrote {mixed_resolved} and {manifest_resolved} (mix_mode={mix_mode}).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

