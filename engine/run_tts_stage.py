"""
TTS stage: one WAV per final_subtitle.srt cue + tts_manifest.json (edge-tts MVP).

Typical pipeline: Chinese (or other) source audio -> Vietnamese subtitles (translate)
-> Vietnamese speech (default edge-tts voice vi-VN-HoaiMyNeural). Override with --voice.
"""
from __future__ import annotations

from engine.json_store import write_json_atomic
import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Optional

from engine.ffmpeg_bins import resolve_ffmpeg_executable
from engine.input_provenance import build_input_provenance_dict, stale_final_subtitle_message
from engine.runtime_app_settings import resolve_azure_speech_configs
from engine.srt_cues import SRTCue, parse_srt_cues
from engine.subtitle_text import log_subtitle_read_issues, read_subtitle_file
from engine.tts import get_tts_provider
from engine.voice_edit_api import load_voice_overrides_indexed

FINAL_SRT_REL = Path("artifacts") / "translate" / "final_subtitle.srt"
DEFAULT_TTS_VOICE = "vi-VN-HoaiMyNeural"


def _short_err(e: BaseException, *, limit: int = 180) -> str:
    s = str(e) or e.__class__.__name__
    s = s.replace("\r", " ").replace("\n", " ").strip()
    if len(s) > limit:
        return s[:limit] + "..."
    return s


def _is_transient_azure_error(e: BaseException) -> bool:
    """
    Heuristic matching for Azure Speech transient failures seen in production.

    Requirement examples:
    - Timeout while synthesizing
    - frame interval threshold exceeded
    - websocket / connection reset
    - temporary network/service interruption
    """
    msg = (str(e) or "").lower()
    patterns = (
        "timeout while synthesizing",
        "timeout",
        "frame interval threshold exceeded",
        "threshold exceeded",
        "websocket",
        "connection reset",
        "connection was forcibly closed",
        "broken pipe",
        "econnreset",
        "temporar",
        "temporary network",
        "service unavailable",
        "server busy",
        "network",
        "disconnected",
        "connection aborted",
        "connection error",
        "transport",
        "socket",
        "tls",
        "handshake",
        "503",
        "504",
        "429",
    )
    return any(p in msg for p in patterns)


def _wav_duration_ms(path: Path) -> int:
    import wave

    with wave.open(str(path), "rb") as w:
        frames = w.getnframes()
        rate = w.getframerate() or 24000
        if frames <= 0 or rate <= 0:
            raise ValueError("invalid wav: no frames/rate")
        return int(frames / float(rate) * 1000.0)


def _existing_valid_wav_duration_ms(out_wav: Path) -> Optional[int]:
    if not out_wav.is_file():
        return None
    try:
        # Quick sanity: WAV header is 44 bytes; reject empty/truncated files.
        if out_wav.stat().st_size < 44:
            return None
        return _wav_duration_ms(out_wav)
    except Exception:
        return None


def _cue_text_hash(text: str) -> str:
    """Stable hash for cue text (UTF-8, normalized newlines + strip)."""
    norm = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def _load_previous_tts_cue_entries(job_workspace: Path) -> dict[int, dict[str, Any]]:
    """Index -> prior cue record from last tts_manifest.json (if any)."""
    p = job_workspace / "artifacts" / "tts" / "tts_manifest.json"
    if not p.is_file():
        return {}
    try:
        body = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    out: dict[int, dict[str, Any]] = {}
    for c in body.get("cues") or []:
        if not isinstance(c, dict):
            continue
        try:
            idx = int(c.get("index"))
        except Exception:
            continue
        out[idx] = c
    return out


def _tts_params_match(prev: dict[str, Any], *, provider: str, voice: str, rate: str) -> bool:
    return (
        str(prev.get("provider") or "") == str(provider or "")
        and str(prev.get("voice") or "") == str(voice or "")
        and str(prev.get("rate") or "") == str(rate or "")
    )


def _provider_profile_label(cfg: dict[str, Any] | None) -> str:
    if not cfg:
        return "default"
    label = str(cfg.get("label") or "").strip()
    if label:
        return label
    source = str(cfg.get("source") or "config").strip() or "config"
    slot = str(cfg.get("slot") or "primary").strip() or "primary"
    return f"{source}:{slot}"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Synthesize TTS cues from artifacts/translate/final_subtitle.srt."
    )
    p.add_argument("--job-workspace", required=True, help="Job / video workspace root.")
    p.add_argument(
        "--tts-provider",
        default="edge_tts",
        help="TTS adapter name (default: edge_tts).",
    )
    p.add_argument(
        "--voice",
        default="",
        help="Provider voice id (default for edge_tts: vi-VN-HoaiMyNeural).",
    )
    p.add_argument(
        "--rate",
        default="",
        help='Speech rate (e.g. "+10%%" or "-5%%"; default +0%%).',
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


def _blocked_final_subtitle(job_workspace: Path, job_id: str, message: str) -> None:
    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "blocked",
            "current_stage": "final_subtitle_required",
            "last_error": message,
            "tts_provider": None,
            "tts_voice": None,
            "tts_manifest_path": None,
            "tts_output_dir": None,
            "tts_cue_count": None,
        },
    )
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "blocked",
            "current_stage": "final_subtitle_required",
            "last_error": message,
        },
    )


def _fail_tts(job_workspace: Path, job_id: str, message: str) -> None:
    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "failed",
            "current_stage": "tts_failed",
            "last_error": message,
        },
    )
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "failed",
            "current_stage": "tts_failed",
            "last_error": message,
        },
    )


def _rel_posix(path: Path, job_workspace: Path) -> str:
    try:
        return path.resolve().relative_to(job_workspace.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


async def _synthesize_all(
    job_workspace: Path,
    cues: list[SRTCue],
    provider_name: str,
    voice: str,
    rate: str,
    cues_dir: Path,
    *,
    previous_cue_entries: dict[int, dict[str, Any]],
    provider_configs: list[dict[str, Any]] | None = None,
    voice_overrides: dict[int, dict[str, str]] | None = None,
) -> list[dict]:
    provider = get_tts_provider(provider_name)
    pk_norm = (provider_name or "").strip().lower().replace("-", "_")
    manifest_cues: list[dict] = []
    active_provider_idx = 0
    configs = list(provider_configs or [])
    if pk_norm in ("azure_tts", "azure") and not configs:
        configs = resolve_azure_speech_configs()
    overrides = voice_overrides or {}
    # Cache provider instances so per-cue overrides (a different voice/provider on
    # one cue) don't re-create an adapter every cue. The job-default lives here too.
    providers: dict[str, TTSProvider] = {pk_norm: provider}

    def _provider_for(name: str) -> TTSProvider:
        key = (name or "").strip().lower().replace("-", "_")
        if key not in providers:
            providers[key] = get_tts_provider(name)
        return providers[key]

    for cue in cues:
        # Per-cue effective voice/rate/provider: a sidecar override wins over the
        # job default, so one cue can use a different (e.g. cloned) voice. The
        # cache key below uses these effective values, so editing one cue's voice
        # re-synthesizes only that cue.
        ov = overrides.get(int(cue.index)) or {}
        eff_voice = str(ov.get("voice_id") or "").strip() or voice
        eff_rate = str(ov.get("rate") or "").strip() or rate
        eff_provider_name = str(ov.get("provider") or "").strip() or provider_name
        eff_pk_norm = eff_provider_name.strip().lower().replace("-", "_")
        is_override = eff_voice != voice or eff_rate != rate or eff_pk_norm != pk_norm

        preview = cue.text.replace("\n", " ").strip()
        if len(preview) > 120:
            preview = preview[:120] + "..."
        diag_prefix = f"[tts cue={cue.index} voice={eff_voice}]"
        print(f"{diag_prefix} start text={preview!r}", file=sys.stderr)
        wav_name = f"cue_{cue.index:05d}.wav"
        out_wav = cues_dir / wav_name

        text_hash = _cue_text_hash(cue.text)
        existing_ms = _existing_valid_wav_duration_ms(out_wav)
        prev = previous_cue_entries.get(int(cue.index))
        prev_hash = prev.get("text_hash") if isinstance(prev, dict) else None
        prev_hash_ok = isinstance(prev_hash, str) and len(prev_hash) == 64

        skip_ok = (
            existing_ms is not None
            and prev is not None
            and prev_hash_ok
            and prev_hash == text_hash
            and _tts_params_match(prev, provider=eff_provider_name, voice=eff_voice, rate=eff_rate)
        )

        if skip_ok:
            rel_audio = _rel_posix(out_wav, job_workspace)
            manifest_cues.append(
                {
                    "index": cue.index,
                    "start_ms": cue.start_ms,
                    "end_ms": cue.end_ms,
                    "text": cue.text,
                    "text_hash": text_hash,
                    "audio_path": rel_audio,
                    "audio_duration_ms": existing_ms,
                    "provider": eff_provider_name,
                    "voice": eff_voice,
                    "rate": eff_rate,
                }
            )
            print(
                f"{diag_prefix} skip_existing_wav_matched audio_duration_ms={existing_ms} wav={rel_audio}",
                file=sys.stderr,
            )
            continue

        if existing_ms is not None:
            if not prev_hash_ok or prev_hash != text_hash:
                print(f"{diag_prefix} resynth_due_to_text_change", file=sys.stderr)
            else:
                print(f"{diag_prefix} resynth_due_to_voice_change", file=sys.stderr)

        provider_profile_label = ""
        # The Azure multi-profile retry path only applies to the job-default Azure
        # provider; an overridden cue (edge/clone/...) uses the simple path.
        if eff_pk_norm in ("azure_tts", "azure") and not is_override:
            if not configs:
                raise RuntimeError(
                    "Missing Azure Speech config. Save Azure credentials in App Settings "
                    "or set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION."
                )
            audio_duration_ms = 0
            last_exc: Exception | None = None
            candidate_order = [
                (active_provider_idx + offset) % len(configs) for offset in range(len(configs))
            ]
            retries = (0, 2) if len(configs) > 1 else (0, 2, 5, 10)
            for candidate_idx in candidate_order:
                candidate_cfg = configs[candidate_idx]
                provider_profile_label = _provider_profile_label(candidate_cfg)
                candidate_failed = False
                for attempt, backoff in enumerate(retries, start=1):
                    if backoff > 0:
                        await asyncio.sleep(backoff)
                    try:
                        audio_duration_ms = await provider.synthesize_cue_to_wav(
                            cue.text,
                            out_wav,
                            voice=eff_voice,
                            rate=eff_rate,
                            diag_prefix=diag_prefix,
                            provider_config=candidate_cfg,
                        )
                        active_provider_idx = candidate_idx
                        last_exc = None
                        break
                    except Exception as e:
                        last_exc = e
                        is_transient = _is_transient_azure_error(e)
                        print(
                            f"{diag_prefix} profile={provider_profile_label} "
                            f"attempt={attempt}/{len(retries)} failed transient={is_transient} "
                            f"err={_short_err(e)!r}",
                            file=sys.stderr,
                        )
                        candidate_failed = True
                        if (not is_transient) or attempt >= len(retries):
                            break
                if not candidate_failed or last_exc is None:
                    break
                if candidate_idx != candidate_order[-1]:
                    print(
                        f"{diag_prefix} switching_azure_profile from={provider_profile_label!r}",
                        file=sys.stderr,
                    )
            if last_exc is not None:
                raise RuntimeError(
                    f"cue_failed index={cue.index} voice={eff_voice} profile={provider_profile_label or 'azure'} "
                    f"text={preview!r} | {_short_err(last_exc)}"
                ) from last_exc
        else:
            try:
                audio_duration_ms = await _provider_for(eff_provider_name).synthesize_cue_to_wav(
                    cue.text,
                    out_wav,
                    voice=eff_voice,
                    rate=eff_rate,
                    diag_prefix=diag_prefix,
                    provider_config=None,
                )
            except Exception as e:
                raise RuntimeError(
                    f"cue_failed index={cue.index} voice={eff_voice} text={preview!r} | {e}"
                ) from e
        rel_audio = _rel_posix(out_wav, job_workspace)
        manifest_cues.append(
            {
                "index": cue.index,
                "start_ms": cue.start_ms,
                "end_ms": cue.end_ms,
                "text": cue.text,
                "text_hash": text_hash,
                "audio_path": rel_audio,
                "audio_duration_ms": audio_duration_ms,
                "provider": eff_provider_name,
                "voice": eff_voice,
                "rate": eff_rate,
                "provider_profile": provider_profile_label or None,
            }
        )
        extra = f" profile={provider_profile_label}" if provider_profile_label else ""
        print(
            f"{diag_prefix}{extra} ok audio_duration_ms={audio_duration_ms} wav={rel_audio}",
            file=sys.stderr,
        )

    return manifest_cues


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    job_workspace = Path(ns.job_workspace).expanduser().resolve()
    job_id = job_workspace.name

    final_srt = job_workspace / FINAL_SRT_REL
    if not final_srt.is_file():
        msg = f"Missing canonical final subtitle: {final_srt}"
        _blocked_final_subtitle(job_workspace, job_id, msg)
        print(msg, file=sys.stderr)
        return 1

    stale = stale_final_subtitle_message(job_workspace)
    if stale:
        print(stale, file=sys.stderr)
        _fail_tts(job_workspace, job_id, stale)
        return 1

    try:
        sub_res = read_subtitle_file(final_srt)
        log_subtitle_read_issues(
            sub_res,
            stage_tag="tts",
            path_display=str(final_srt.resolve()),
        )
        srt_text = sub_res.text
    except OSError as e:
        msg = f"Could not read final subtitle: {e}"
        _fail_tts(job_workspace, job_id, msg)
        print(msg, file=sys.stderr)
        return 1

    cues = parse_srt_cues(srt_text)
    print(f"[tts] Parsed cue count: {len(cues)}", file=sys.stderr)
    for c in cues[:3]:
        preview = c.text.replace("\n", " ")
        if len(preview) > 120:
            preview = preview[:120] + "..."
        print(
            f"[tts] Cue preview: index={c.index} start_ms={c.start_ms} end_ms={c.end_ms} text={preview!r}",
            file=sys.stderr,
        )
    if len(cues) == 0:
        msg = (
            "No SRT cues parsed from artifacts/translate/final_subtitle.srt. "
            "Ensure the file uses standard SRT timestamps like '00:00:01,000 --> 00:00:02,000' "
            "with blank lines between cues."
        )
        _fail_tts(job_workspace, job_id, msg)
        print(msg, file=sys.stderr)
        return 1
    tts_root = job_workspace / "artifacts" / "tts"
    cues_dir = tts_root / "cues"
    cues_dir.mkdir(parents=True, exist_ok=True)

    provider_key = (ns.tts_provider or "edge_tts").strip()
    pk_norm = provider_key.lower().replace("-", "_")
    azure_configs: list[dict[str, Any]] = []
    if pk_norm in ("edge_tts", "edge"):
        try:
            import edge_tts  # noqa: F401
        except ImportError as e:
            msg = f"edge-tts is not installed ({e}). pip install edge-tts"
            _fail_tts(job_workspace, job_id, msg)
            print(msg, file=sys.stderr)
            return 1
        ff_path, ff_err = resolve_ffmpeg_executable()
        if ff_path is None:
            msg = ff_err or "ffmpeg not found."
            _fail_tts(job_workspace, job_id, msg)
            print(msg, file=sys.stderr)
            return 1
    elif pk_norm in ("azure_tts", "azure"):
        try:
            import azure.cognitiveservices.speech as _speechsdk  # noqa: F401
        except ImportError as e:
            msg = (
                f"azure-cognitiveservices-speech is not installed ({e}). "
                "Install with: pip install azure-cognitiveservices-speech"
            )
            _fail_tts(job_workspace, job_id, msg)
            print(msg, file=sys.stderr)
            return 1
        azure_configs = resolve_azure_speech_configs()
        if not azure_configs:
            msg = (
                "Missing Azure Speech config. Save Azure credentials in App Settings "
                "or set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION. "
                "If Azure is unavailable, you can try --tts-provider edge_tts for testing."
            )
            _fail_tts(job_workspace, job_id, msg)
            print(msg, file=sys.stderr)
            return 1
    voice = (ns.voice or "").strip() or DEFAULT_TTS_VOICE
    rate = (ns.rate or "").strip() or "+0%"
    previous_cue_entries = _load_previous_tts_cue_entries(job_workspace)
    voice_overrides = load_voice_overrides_indexed(job_workspace)
    if voice_overrides:
        print(f"[tts] Per-cue voice overrides: {len(voice_overrides)} cue(s).", file=sys.stderr)

    try:
        manifest_cues = asyncio.run(
            _synthesize_all(
                job_workspace,
                cues,
                provider_key,
                voice,
                rate,
                cues_dir,
                previous_cue_entries=previous_cue_entries,
                provider_configs=azure_configs,
                voice_overrides=voice_overrides,
            )
        )
    except ValueError as e:
        msg = str(e)
        _fail_tts(job_workspace, job_id, msg)
        print(msg, file=sys.stderr)
        return 1
    except Exception as e:
        # The provider should have already printed per-cue diagnostics; here we persist
        # an actionable state in job_state.json.
        msg = f"TTS failed: {e}"
        _fail_tts(job_workspace, job_id, msg)
        print(msg, file=sys.stderr)
        return 1

    manifest_path = tts_root / "tts_manifest.json"
    manifest_body = {
        "version": 2,
        "job_workspace": str(job_workspace),
        "provider": provider_key,
        "voice": voice,
        "rate": rate,
        "provider_profiles_available": [
            _provider_profile_label(cfg) for cfg in azure_configs
        ] if azure_configs else [],
        "final_subtitle_path": _rel_posix(final_srt, job_workspace),
        "tts_output_dir": _rel_posix(tts_root, job_workspace),
        "cue_count": len(manifest_cues),
        "cues": manifest_cues,
        "input_provenance": build_input_provenance_dict(job_workspace),
    }
    try:
        manifest_path.write_text(
            json.dumps(manifest_body, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as e:
        msg = f"Could not write manifest: {e}"
        _fail_tts(job_workspace, job_id, msg)
        print(msg, file=sys.stderr)
        return 1

    manifest_resolved = str(manifest_path.resolve())
    tts_dir_resolved = str(tts_root.resolve())

    _merge_job_state(
        job_workspace,
        {
            "job_id": job_id,
            "job_workspace": str(job_workspace),
            "status": "tts_generated",
            "current_stage": "tts_generated",
            "last_error": None,
            "tts_provider": provider_key,
            "tts_voice": voice,
            "tts_manifest_path": manifest_resolved,
            "tts_output_dir": tts_dir_resolved,
            "tts_cue_count": len(manifest_cues),
        },
    )
    _write_video_state(
        job_workspace,
        {
            "video_id": job_id,
            "status": "tts_generated",
            "current_stage": "tts_generated",
            "last_error": None,
            "tts_provider": provider_key,
            "tts_voice": voice,
            "artifact_paths": {
                "tts_manifest": manifest_resolved,
                "tts_cues_dir": str(cues_dir.resolve()),
            },
        },
    )

    print(
        f"[tts] Wrote {len(manifest_cues)} cue WAV(s) and {manifest_resolved}.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
