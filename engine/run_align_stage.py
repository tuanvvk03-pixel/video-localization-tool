"""
Align stage (MVP): place per-cue WAV at subtitle start times into a single voice track.

Inputs:
- artifacts/translate/final_subtitle.srt
- artifacts/tts/tts_manifest.json

Outputs:
- artifacts/aligned/voice_track_aligned.wav
- artifacts/aligned/alignment_manifest.json
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import argparse
import asyncio
import array
import json
import subprocess
import sys
import wave
from pathlib import Path

from engine.ffmpeg_bins import resolve_ffmpeg_executable
from engine.input_provenance import (
    build_input_provenance_dict,
    stale_final_subtitle_message,
    stale_manifest_input_provenance_message,
)
from engine.srt_cues import parse_srt_cues
from engine.subtitle_text import read_subtitle_file
from engine.tts import get_tts_provider
from engine.voice_coverage_report import write_voice_coverage_report


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Align cue WAVs into subtitle timing slots (MVP).")
    p.add_argument("--job-workspace", required=True, help="Job / video workspace root.")
    p.add_argument(
        "--min-gap-ms",
        type=int,
        default=60,
        help="Minimum gap between sequentially placed cues (default 60ms).",
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


def _fail(job_workspace: Path, job_id: str, message: str) -> int:
    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "failed",
            "current_stage": "align_failed",
            "last_error": message,
            "aligned_voice_track_path": None,
            "alignment_manifest_path": None,
        },
    )
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "failed",
            "current_stage": "align_failed",
            "last_error": message,
        },
    )
    print(message, file=sys.stderr)
    return 1


def _ms_to_frame(ms: int, sample_rate: int) -> int:
    return int((max(0, ms) / 1000.0) * sample_rate)


def _duration_ms(frames: int, sample_rate: int) -> int:
    return int(frames / float(sample_rate) * 1000.0)


def _find_speech_bounds(samples: array.array, thr: int) -> tuple[int, int]:
    """
    Return (start_idx, end_idx_exclusive) of speech region.
    If no speech detected, return full range (0, len(samples)).
    """
    n = len(samples)
    if n == 0:
        return 0, 0
    start = 0
    while start < n and abs(int(samples[start])) <= thr:
        start += 1
    end = n - 1
    while end >= 0 and abs(int(samples[end])) <= thr:
        end -= 1
    if start >= n or end < start:
        return 0, n
    return start, end + 1


def _compact_wav_to_pcm16_mono(
    *,
    src_wav: Path,
    dst_wav: Path,
    head_pad_ms: int,
    tail_pad_ms: int,
    silence_threshold: int,
    expected_sample_rate: int,
) -> tuple[int, int]:
    """
    Trim leading/trailing silence and write PCM16 mono WAV.
    Returns (compacted_duration_ms, sample_rate).
    """
    with wave.open(str(src_wav), "rb") as w:
        sr = int(w.getframerate())
        ch = int(w.getnchannels())
        sw = int(w.getsampwidth())
        frames = int(w.getnframes())
        raw = w.readframes(frames)

    if sr != expected_sample_rate:
        raise RuntimeError(f"sample_rate_mismatch got={sr} expected={expected_sample_rate}")
    if ch != 1 or sw != 2:
        raise RuntimeError(f"unsupported_wav_format ch={ch} sw={sw} (expected 1/2)")

    samples = array.array("h")
    samples.frombytes(raw)
    orig_frames = len(samples)

    speech_start, speech_end = _find_speech_bounds(samples, int(silence_threshold))
    head_pad_frames = int((max(0, head_pad_ms) / 1000.0) * sr)
    tail_pad_frames = int((max(0, tail_pad_ms) / 1000.0) * sr)
    new_start = max(0, speech_start - head_pad_frames)
    new_end = min(orig_frames, speech_end + tail_pad_frames)
    compacted = samples[new_start:new_end]

    dst_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dst_wav), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(sr)
        out.writeframes(compacted.tobytes())

    return _duration_ms(len(compacted), sr), sr


def _normalize_rate_string(rate: str) -> str:
    r = (rate or "").strip()
    if not r:
        return "+0%"
    if r.endswith("%"):
        return r if r.startswith(("+", "-")) else f"+{r}"
    if r[0].isdigit():
        return f"+{r}%"
    if r.startswith(("+", "-")) and r[1:].isdigit():
        return f"{r}%"
    return r


def _rate_add_percent(base_rate: str, add_pct: int) -> str:
    """
    Add a positive percentage onto a base rate string like "+0%" or "+10%".
    Falls back to +<add>% if parsing fails.
    """
    b = _normalize_rate_string(base_rate)
    try:
        s = b.strip()
        if not s.endswith("%"):
            raise ValueError("no_percent_suffix")
        n = int(s[:-1])  # handles + / -
        return f"{n + int(add_pct):+d}%"
    except Exception:
        return f"+{int(add_pct)}%"


async def _resynth_compacted_variant(
    *,
    provider_name: str,
    voice: str,
    text: str,
    out_wav_raw: Path,
    out_wav_compacted: Path,
    rate: str,
    diag_prefix: str,
    head_pad_ms: int,
    tail_pad_ms: int,
    silence_threshold: int,
    expected_sample_rate: int,
) -> int:
    provider = get_tts_provider(provider_name)
    raw_ms = await provider.synthesize_cue_to_wav(
        text,
        out_wav_raw,
        voice=voice,
        rate=rate,
        diag_prefix=diag_prefix,
    )
    compact_ms, _sr = _compact_wav_to_pcm16_mono(
        src_wav=out_wav_raw,
        dst_wav=out_wav_compacted,
        head_pad_ms=head_pad_ms,
        tail_pad_ms=tail_pad_ms,
        silence_threshold=silence_threshold,
        expected_sample_rate=expected_sample_rate,
    )
    # Prefer compacted duration for alignment decisions.
    _ = raw_ms
    return int(compact_ms)


def _compute_remaining_silence_ms(cues: list, *, cap_ms: int = 10_000) -> list[int]:
    """
    remaining_silence_from[i] = sum(max(0, start_{k+1}-end_k)) for k in [i..n-2].
    Used as an upper bound to "push suffix later within gaps".
    """
    n = len(cues)
    rem = [0] * (n + 1)
    acc = 0
    for i in range(n - 2, -1, -1):
        gap = int(cues[i + 1].start_ms) - int(cues[i].end_ms)
        if gap > 0:
            acc += gap
        if acc > cap_ms:
            acc = cap_ms
        rem[i] = acc
    return rem


def _probe_wav_duration_ms(path: Path) -> int:
    try:
        with wave.open(str(path), "rb") as w:
            sr = int(w.getframerate())
            frames = int(w.getnframes())
    except Exception:
        return 0
    if sr <= 0:
        return 0
    return int(frames / float(sr) * 1000.0)


def _atempo_filter_for_speed(speed: float) -> str:
    # speed > 1.0 means faster (shorter). atempo supports 0.5..2.0 per filter.
    s = float(speed)
    if s <= 0:
        return "atempo=1.0"
    parts: list[float] = []
    while s > 2.0:
        parts.append(2.0)
        s /= 2.0
    while s < 0.5:
        parts.append(0.5)
        s /= 0.5
    parts.append(s)
    return ",".join(f"atempo={p:.6f}" for p in parts)


def _speedup_wav_with_ffmpeg(*, src: Path, dst: Path, speed: float) -> tuple[bool, str | None]:
    ffmpeg, err = resolve_ffmpeg_executable()
    if ffmpeg is None:
        return False, err or "ffmpeg not found"
    dst.parent.mkdir(parents=True, exist_ok=True)
    filt = _atempo_filter_for_speed(speed)
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-filter:a",
        filt,
        "-ac",
        "1",
        "-ar",
        "24000",
        "-c:a",
        "pcm_s16le",
        str(dst),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        tail = ((proc.stderr or "") + "\n" + (proc.stdout or ""))[-4000:]
        return False, f"ffmpeg atempo failed (exit {proc.returncode}). tail:\n{tail}"
    return True, None


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    job_workspace = Path(ns.job_workspace).expanduser().resolve()
    job_id = job_workspace.name

    final_srt = job_workspace / "artifacts" / "translate" / "final_subtitle.srt"
    compacted_manifest = (
        job_workspace / "artifacts" / "tts_compacted" / "tts_compacted_manifest.json"
    )
    tts_manifest_path = job_workspace / "artifacts" / "tts" / "tts_manifest.json"
    if compacted_manifest.is_file():
        tts_manifest_path = compacted_manifest
    if not final_srt.is_file():
        msg = f"Missing canonical final subtitle: {final_srt}"
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "blocked",
                "current_stage": "final_subtitle_required",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1

    stale_fs = stale_final_subtitle_message(job_workspace)
    if stale_fs:
        return _fail(job_workspace, job_id, stale_fs)

    if not tts_manifest_path.is_file():
        msg = f"Missing TTS manifest: {tts_manifest_path}"
        _merge_job_state(
            job_workspace,
            {
                "job_id": job_id,
                "job_workspace": str(job_workspace),
                "status": "blocked",
                "current_stage": "tts_manifest_required",
                "last_error": msg,
            },
        )
        print(msg, file=sys.stderr)
        return 1

    stale = stale_manifest_input_provenance_message(job_workspace, tts_manifest_path)
    if stale:
        return _fail(job_workspace, job_id, stale)

    try:
        sub = read_subtitle_file(final_srt)
        cues = parse_srt_cues(sub.text)
    except Exception as e:
        return _fail(job_workspace, job_id, f"Failed to parse final_subtitle.srt: {e}")

    try:
        mf = json.loads(tts_manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        return _fail(job_workspace, job_id, f"Failed to read tts_manifest.json: {e}")

    mf_cues = mf.get("cues") or []
    if not isinstance(mf_cues, list) or not mf_cues:
        return _fail(job_workspace, job_id, "TTS manifest has no cues to align.")

    # Map by cue index; keep order stable by subtitle order.
    audio_by_index: dict[int, dict] = {}
    for it in mf_cues:
        try:
            idx = int(it.get("index"))
        except Exception:
            continue
        audio_by_index[idx] = dict(it)

    if not cues:
        return _fail(job_workspace, job_id, "No subtitle cues found in final_subtitle.srt.")

    aligned_dir = job_workspace / "artifacts" / "aligned"
    aligned_dir.mkdir(parents=True, exist_ok=True)
    out_wav = aligned_dir / "voice_track_aligned.wav"
    out_manifest = aligned_dir / "alignment_manifest.json"

    # Determine format from first available WAV
    sample_rate = 24000
    nchannels = 1
    sampwidth = 2

    first_path: Path | None = None
    for c in cues:
        item = audio_by_index.get(c.index)
        if item and item.get("audio_path"):
            first_path = (job_workspace / Path(str(item["audio_path"]))).resolve()
            if first_path.is_file():
                break

    if first_path is None or not first_path.is_file():
        return _fail(job_workspace, job_id, "Could not find any cue WAV files referenced by manifest.")

    try:
        with wave.open(str(first_path), "rb") as w:
            sample_rate = int(w.getframerate())
            nchannels = int(w.getnchannels())
            sampwidth = int(w.getsampwidth())
    except Exception as e:
        return _fail(job_workspace, job_id, f"Failed to open first cue wav: {first_path} ({e})")

    if nchannels != 1 or sampwidth != 2:
        return _fail(
            job_workspace,
            job_id,
            f"Unsupported cue WAV format (need mono 16-bit PCM). Got channels={nchannels} sampwidth={sampwidth}.",
        )

    # Compute total frames
    max_end_ms = 0
    for c in cues:
        item = audio_by_index.get(c.index)
        if not item:
            continue
        dur = int(item.get("audio_duration_ms") or 0)
        max_end_ms = max(max_end_ms, int(c.start_ms) + max(dur, 0), int(c.end_ms))
    total_frames = int((max_end_ms / 1000.0) * sample_rate) + int(sample_rate * 0.5)

    mix = array.array("i", [0]) * total_frames  # int32 accumulator
    alignment_cues: list[dict] = []

    # Overflow-aware timing policy (post-compact, pre-mix):
    # - Use compacted_duration_ms (or audio_duration_ms) as wav_ms
    # - Mild overflow: push later cues within remaining gaps
    # - Medium overflow: try re-synth with faster rate ladder and re-compact
    # - Hard overflow: mark in manifest for post-review
    remaining_silence_from = _compute_remaining_silence_ms(cues, cap_ms=20_000)

    # Compaction params: reuse values from compacted manifest when present, else defaults.
    head_pad_ms = int(mf.get("head_pad_ms") or 30)
    tail_pad_ms = int(mf.get("tail_pad_ms") or 60)
    silence_threshold = int(mf.get("silence_threshold") or 400)

    # Sequential placement state (no-overlap guarantee).
    min_gap_ms = max(0, int(ns.min_gap_ms))
    # Allow the first cue to start at its original start (usually 0ms).
    prev_placed_end_ms = -min_gap_ms
    cumulative_drift_ms = 0

    # Start-time shift applied to the *next* cues (ms) to avoid overlaps.
    suffix_shift = 0

    # Optional per-cue resynth variants stored under aligned artifacts.
    variants_dir = aligned_dir / "variants"
    variants_dir.mkdir(parents=True, exist_ok=True)

    # Optional per-cue speedup variants stored under aligned artifacts.
    speedups_dir = aligned_dir / "speedups"
    speedups_dir.mkdir(parents=True, exist_ok=True)

    for pos, c in enumerate(cues):
        item = audio_by_index.get(c.index)
        if not item:
            alignment_cues.append(
                {
                    "index": c.index,
                    "start_ms": c.start_ms,
                    "end_ms": c.end_ms,
                    "text": c.text,
                    "audio_path": None,
                    "audio_duration_ms": None,
                    "slot_duration_ms": max(0, c.end_ms - c.start_ms),
                    "overflow_ms": None,
                    "note": "missing_audio_for_cue_index",
                }
            )
            continue

        ap = str(item.get("audio_path") or "")
        wav_path = (job_workspace / Path(ap)).resolve()
        if not wav_path.is_file():
            return _fail(job_workspace, job_id, f"Missing cue wav for index={c.index}: {wav_path}")

        slot_ms = max(0, int(c.end_ms) - int(c.start_ms))
        audio_dur_ms = int(item.get("audio_duration_ms") or 0)
        wav_ms = audio_dur_ms
        overflow_ms = wav_ms - slot_ms

        provider_name = str(item.get("provider") or mf.get("provider") or "")
        voice = str(item.get("voice") or mf.get("voice") or "")
        base_rate = str(item.get("rate") or mf.get("rate") or "+0%")
        speech_rate_used = _normalize_rate_string(base_rate)
        hard_overflow = False
        retime_action = "none"
        selected_audio_path = ap.replace("\\", "/")
        selected_wav_path = wav_path

        if overflow_ms > 1800:
            hard_overflow = True
            retime_action = "hard_overflow"
        elif overflow_ms > 900:
            # Medium overflow: attempt per-cue re-synth at faster rates, and pick first that fits.
            retime_action = "hard_overflow"
            if not provider_name or not voice:
                # Can't re-synth without provider + voice; keep as-is but mark.
                retime_action = "hard_overflow"
            else:
                # Try to fit slot OR available remaining silence window.
                available_window_ms = slot_ms + int(remaining_silence_from[pos] or 0)
                ladder = [8, 14, 20]
                diag_prefix = f"[align cue={c.index} voice={voice}]"
                best: tuple[int, str, Path, str] | None = None  # (wav_ms, rate, wav_path, rel_path)
                for add in ladder:
                    rate_try = _rate_add_percent(base_rate, add)
                    raw_out = variants_dir / f"cue_{c.index:05d}_rate{rate_try.replace('%','p').replace('+','p').replace('-','m')}.raw.wav"
                    cmp_out = variants_dir / f"cue_{c.index:05d}_rate{rate_try.replace('%','p').replace('+','p').replace('-','m')}.wav"
                    try:
                        cmp_ms = asyncio.run(
                            _resynth_compacted_variant(
                                provider_name=provider_name,
                                voice=voice,
                                text=str(c.text or ""),
                                out_wav_raw=raw_out,
                                out_wav_compacted=cmp_out,
                                rate=rate_try,
                                diag_prefix=diag_prefix,
                                head_pad_ms=head_pad_ms,
                                tail_pad_ms=tail_pad_ms,
                                silence_threshold=silence_threshold,
                                expected_sample_rate=sample_rate,
                            )
                        )
                    except Exception as e:
                        print(f"{diag_prefix} resynth rate={rate_try!r} failed err={e}", file=sys.stderr)
                        continue
                    rel = (Path("artifacts") / "aligned" / "variants" / cmp_out.name).as_posix()
                    print(f"{diag_prefix} resynth rate={rate_try!r} ok compacted_ms={cmp_ms} wav={rel}", file=sys.stderr)
                    best = (int(cmp_ms), rate_try, cmp_out, rel)
                    if cmp_ms <= slot_ms or cmp_ms <= available_window_ms:
                        break
                if best is not None:
                    wav_ms, speech_rate_used, selected_wav_path, selected_audio_path = best
                    # Resynth exists but still must not overlap; treat as a kind of speedup.
                    retime_action = "speedup_14" if "14" in str(speech_rate_used) else "speedup_10" if "10" in str(speech_rate_used) else "speedup_6"

        # Mild overflow: attempt to push later cues using gaps (remaining_silence_from on suffix).
        if (not hard_overflow) and (overflow_ms > 250) and (overflow_ms <= 900):
            retime_action = "shift_only"

        try:
            with wave.open(str(selected_wav_path), "rb") as w:
                if int(w.getframerate()) != sample_rate or int(w.getnchannels()) != 1 or int(w.getsampwidth()) != 2:
                    return _fail(
                        job_workspace,
                        job_id,
                        f"Cue wav format mismatch index={c.index}: rate={w.getframerate()} ch={w.getnchannels()} sw={w.getsampwidth()} (expected {sample_rate}/1/2).",
                    )
                frames = w.getnframes()
                raw = w.readframes(frames)
        except Exception as e:
            return _fail(job_workspace, job_id, f"Failed reading cue wav index={c.index}: {e}")

        samples16 = array.array("h")
        samples16.frombytes(raw)

        original_start_ms = int(c.start_ms)

        # Baseline shift from existing suffix policy (kept), but final placement is sequential no-overlap.
        current_shift = int(suffix_shift)
        baseline_start_ms = original_start_ms + current_shift
        required_start_ms = int(prev_placed_end_ms) + int(min_gap_ms)
        placed_start_ms = max(int(baseline_start_ms), int(required_start_ms))
        overlap_prevented = placed_start_ms > baseline_start_ms

        # Mild per-cue speed fallback: try speedup ladder via ffmpeg atempo.
        drift_now_ms = int(placed_start_ms) - int(original_start_ms)
        try_speedup = (int(wav_ms) > int(slot_ms)) or (int(drift_now_ms) >= 600)
        speed_action = "none"
        if try_speedup:
            ladder2 = [
                (1.06, "speedup_6"),
                (1.10, "speedup_10"),
                (1.14, "speedup_14"),
            ]
            for speed, action in ladder2:
                out_wav_speed = speedups_dir / f"cue_{c.index:05d}_{action}.wav"
                ok, err = _speedup_wav_with_ffmpeg(src=selected_wav_path, dst=out_wav_speed, speed=speed)
                if not ok:
                    print(f"[align cue={c.index}] {action} failed: {err}", file=sys.stderr)
                    continue
                new_ms = _probe_wav_duration_ms(out_wav_speed)
                if new_ms <= 0:
                    continue
                if (new_ms < int(wav_ms)) and ((new_ms <= slot_ms) or (int(wav_ms) - new_ms >= 80)):
                    selected_wav_path = out_wav_speed
                    selected_audio_path = (Path("artifacts") / "aligned" / "speedups" / out_wav_speed.name).as_posix()
                    wav_ms = int(new_ms)
                    speech_rate_used = action
                    speed_action = action
                    break

        if speed_action != "none":
            retime_action = speed_action
        elif int(placed_start_ms) > int(original_start_ms) and retime_action == "none":
            retime_action = "shift_only"

        placed_end_ms = int(placed_start_ms) + int(wav_ms)
        shifted_by_ms = int(placed_start_ms) - int(original_start_ms)
        cumulative_drift_ms = int(shifted_by_ms)

        # NOTE: We intentionally do not "push suffix" anymore.
        # Sequential placement (prev_placed_end_ms + min_gap_ms) guarantees no overlap.

        start_frame = _ms_to_frame(placed_start_ms, sample_rate)
        if start_frame < 0:
            start_frame = 0
        end_frame = start_frame + len(samples16)
        if end_frame > len(mix):
            # Extend if needed (rare)
            mix.extend([0] * (end_frame - len(mix)))

        for j, s in enumerate(samples16):
            mix[start_frame + j] += int(s)

        overflow_ms = int(wav_ms) - int(slot_ms)
        if overflow_ms > 900:
            hard_overflow = True
            if retime_action == "none":
                retime_action = "hard_overflow"
        alignment_cues.append(
            {
                "index": c.index,
                "start_ms": c.start_ms,
                "end_ms": c.end_ms,
                "text": c.text,
                "audio_path": selected_audio_path,
                "audio_duration_ms": int(wav_ms),
                "slot_duration_ms": int(slot_ms),
                # Legacy field kept
                "slot_ms": int(slot_ms),
                "wav_ms": int(wav_ms),
                "overflow_ms": int(overflow_ms),
                "retime_action": retime_action,
                "speech_rate_used": speech_rate_used,
                "hard_overflow": bool(hard_overflow),
                "placed_start_frame": start_frame,
                "placed_end_frame": end_frame,
                "placed_start_ms": int(placed_start_ms),
                "placed_end_ms": int(placed_end_ms),
                "shifted_by_ms": int(shifted_by_ms),
                "overlap_prevented": bool(overlap_prevented),
                "cumulative_drift_ms": int(cumulative_drift_ms),
                # Legacy field kept
                "shift_ms": int(current_shift),
            }
        )
        prev_placed_end_ms = int(placed_end_ms)

    # Clip to int16
    out16 = array.array("h")
    out16.extend([0] * len(mix))
    for i, v in enumerate(mix):
        if v > 32767:
            v = 32767
        elif v < -32768:
            v = -32768
        out16[i] = int(v)

    try:
        with wave.open(str(out_wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            w.writeframes(out16.tobytes())
    except Exception as e:
        return _fail(job_workspace, job_id, f"Failed writing aligned voice track: {e}")

    tts_manifest_rel = (
        "artifacts/tts_compacted/tts_compacted_manifest.json"
        if tts_manifest_path == compacted_manifest
        else "artifacts/tts/tts_manifest.json"
    )
    manifest = {
        "version": 2,
        "sample_rate_hz": sample_rate,
        "voice_track_path": "artifacts/aligned/voice_track_aligned.wav",
        "tts_manifest_path": tts_manifest_rel,
        "final_subtitle_path": "artifacts/translate/final_subtitle.srt",
        "cue_count": len(alignment_cues),
        "cues": alignment_cues,
        "input_provenance": build_input_provenance_dict(job_workspace),
    }
    try:
        write_json_atomic(out_manifest, manifest)
    except Exception as e:
        return _fail(job_workspace, job_id, f"Failed writing alignment_manifest.json: {e}")

    cov_path = write_voice_coverage_report(job_workspace, manifest)
    if cov_path is not None:
        warns = []
        try:
            mf_cov = json.loads(cov_path.read_text(encoding="utf-8"))
            warns = mf_cov.get("warnings") or []
        except json.JSONDecodeError:
            pass
        if warns:
            print(
                f"[align] voice_coverage_report warnings: {warns} (see {cov_path.name})",
                file=sys.stderr,
            )

    aligned_resolved = str(out_wav.resolve())
    manifest_resolved = str(out_manifest.resolve())
    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "aligned",
            "current_stage": "aligned",
            "aligned_voice_track_path": aligned_resolved,
            "alignment_manifest_path": manifest_resolved,
            "last_error": None,
        },
    )
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "aligned",
            "current_stage": "aligned",
            "last_error": None,
            "artifact_paths": {
                "aligned_voice_track": aligned_resolved,
                "alignment_manifest": manifest_resolved,
            },
        },
    )
    print(f"[align] Wrote {aligned_resolved} and {manifest_resolved}.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

