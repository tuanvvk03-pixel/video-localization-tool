"""
Compact TTS cue WAVs by trimming leading/trailing silence (MVP).

Inputs:
- artifacts/tts/tts_manifest.json
- artifacts/tts/cues/*.wav

Outputs:
- artifacts/tts_compacted/cues/*.wav
- artifacts/tts_compacted/tts_compacted_manifest.json
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import argparse
import array
import json
import sys
import wave
from pathlib import Path

from engine.input_provenance import (
    build_input_provenance_dict,
    stale_manifest_input_provenance_message,
)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Trim silence from TTS cue WAV files (MVP).")
    p.add_argument("--job-workspace", required=True, help="Job / video workspace root.")
    p.add_argument("--head-pad-ms", type=int, default=30, help="Keep this padding before speech.")
    p.add_argument("--tail-pad-ms", type=int, default=60, help="Keep this padding after speech.")
    p.add_argument(
        "--silence-threshold",
        type=int,
        default=400,
        help="Absolute int16 amplitude threshold treated as silence (default 400).",
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
            "current_stage": "compact_tts_failed",
            "last_error": message,
        },
    )
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "failed",
            "current_stage": "compact_tts_failed",
            "last_error": message,
        },
    )
    print(message, file=sys.stderr)
    return 1


def _ms_to_frames(ms: int, sr: int) -> int:
    return int(max(0, ms) / 1000.0 * sr)


def _duration_ms(frames: int, sr: int) -> int:
    return int(frames / float(sr) * 1000.0)


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


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    job_workspace = Path(ns.job_workspace).expanduser().resolve()
    job_id = job_workspace.name

    tts_manifest = job_workspace / "artifacts" / "tts" / "tts_manifest.json"
    if not tts_manifest.is_file():
        msg = f"Missing TTS manifest: {tts_manifest}"
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

    try:
        mf = json.loads(tts_manifest.read_text(encoding="utf-8"))
    except Exception as e:
        return _fail(job_workspace, job_id, f"Failed to read tts_manifest.json: {e}")

    stale = stale_manifest_input_provenance_message(job_workspace, tts_manifest)
    if stale:
        return _fail(job_workspace, job_id, stale)

    cues = mf.get("cues") or []
    if not isinstance(cues, list) or not cues:
        return _fail(job_workspace, job_id, "TTS manifest has no cues to compact.")

    out_root = job_workspace / "artifacts" / "tts_compacted"
    out_cues_dir = out_root / "cues"
    out_cues_dir.mkdir(parents=True, exist_ok=True)
    out_manifest = out_root / "tts_compacted_manifest.json"

    head_pad_ms = int(ns.head_pad_ms)
    tail_pad_ms = int(ns.tail_pad_ms)
    thr = int(ns.silence_threshold)

    compacted_cues: list[dict] = []
    changed = 0

    for it in cues:
        idx = int(it.get("index"))
        text = str(it.get("text") or "")
        ap = str(it.get("audio_path") or "")
        provider = (it.get("provider") or mf.get("provider") or "")
        voice = (it.get("voice") or mf.get("voice") or "")
        rate = (it.get("rate") or mf.get("rate") or "")
        src_wav = (job_workspace / Path(ap)).resolve()
        if not src_wav.is_file():
            return _fail(job_workspace, job_id, f"Missing cue wav index={idx}: {src_wav}")

        try:
            with wave.open(str(src_wav), "rb") as w:
                sr = int(w.getframerate())
                ch = int(w.getnchannels())
                sw = int(w.getsampwidth())
                frames = int(w.getnframes())
                raw = w.readframes(frames)
        except Exception as e:
            return _fail(job_workspace, job_id, f"Failed reading cue wav index={idx}: {e}")

        if ch != 1 or sw != 2:
            return _fail(job_workspace, job_id, f"Unsupported wav format index={idx}: ch={ch} sw={sw}")

        samples = array.array("h")
        samples.frombytes(raw)
        orig_frames = len(samples)
        orig_ms = _duration_ms(orig_frames, sr)

        speech_start, speech_end = _find_speech_bounds(samples, thr)
        lead_trim_frames = speech_start
        trail_trim_frames = orig_frames - speech_end

        head_pad_frames = _ms_to_frames(head_pad_ms, sr)
        tail_pad_frames = _ms_to_frames(tail_pad_ms, sr)

        new_start = max(0, speech_start - head_pad_frames)
        new_end = min(orig_frames, speech_end + tail_pad_frames)

        compacted = samples[new_start:new_end]
        compact_frames = len(compacted)
        compact_ms = _duration_ms(compact_frames, sr)

        # Always write compacted cue (even if identical) to keep deterministic artifact set.
        dst_wav = out_cues_dir / f"cue_{idx:05d}.wav"
        try:
            with wave.open(str(dst_wav), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(sr)
                w.writeframes(compacted.tobytes())
        except Exception as e:
            return _fail(job_workspace, job_id, f"Failed writing compacted wav index={idx}: {e}")

        leading_trim_ms = _duration_ms(new_start, sr)
        trailing_trim_ms = _duration_ms(orig_frames - new_end, sr)
        if leading_trim_ms > 0 or trailing_trim_ms > 0:
            changed += 1

        compacted_rel = Path("artifacts") / "tts_compacted" / "cues" / dst_wav.name
        compacted_rel_s = compacted_rel.as_posix()

        compacted_cues.append(
            {
                "index": idx,
                "text": text,
                "provider": str(provider),
                "voice": str(voice),
                "rate": str(rate),
                "original_audio_path": ap.replace("\\", "/"),
                "compacted_audio_path": compacted_rel_s,
                "audio_path": compacted_rel_s,  # align-stage compatibility
                "original_duration_ms": orig_ms,
                "compacted_duration_ms": compact_ms,
                "audio_duration_ms": compact_ms,  # align-stage compatibility
                "leading_trim_ms": leading_trim_ms,
                "trailing_trim_ms": trailing_trim_ms,
                "head_pad_ms": head_pad_ms,
                "tail_pad_ms": tail_pad_ms,
                "silence_threshold": thr,
            }
        )

    manifest_body = {
        "version": 1,
        "source_manifest_path": "artifacts/tts/tts_manifest.json",
        "output_dir": "artifacts/tts_compacted",
        "cue_count": len(compacted_cues),
        "changed_cue_count": changed,
        "head_pad_ms": head_pad_ms,
        "tail_pad_ms": tail_pad_ms,
        "silence_threshold": thr,
        "cues": compacted_cues,
        "input_provenance": build_input_provenance_dict(job_workspace),
    }
    out_manifest.write_text(
        json.dumps(manifest_body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(
        f"[compact_tts] Wrote {len(compacted_cues)} compacted cue(s) to {out_root} (changed={changed}).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

