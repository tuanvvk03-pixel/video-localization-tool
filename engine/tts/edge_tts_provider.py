"""
Microsoft Edge online TTS via edge-tts; outputs WAV via ffmpeg.

Project flow: translated subtitles (often Vietnamese) are synthesized with a matching
neural voice; default voice is set in run_tts_stage (vi-VN-HoaiMyNeural).
"""
from __future__ import annotations

import asyncio
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

from engine.ffmpeg_bins import resolve_ffmpeg_executable
from engine.tts.base import TTSProvider


_EDGE_TTS_PUNCT_RE = re.compile(r"""[\.,;:!?…，。！？；："“”'‘’`\(\)\[\]\{\}<>/\\|]+""")
_EDGE_TTS_SPACE_RE = re.compile(r"\s+")


def _is_retryable_no_audio_error(exc: BaseException) -> bool:
    msg = (str(exc) or "").lower()
    cls = exc.__class__.__name__.lower()
    return (
        cls == "noaudioreceived"
        or "no audio was received" in msg
        or "empty mp3" in msg
    )


def _soften_edge_tts_text(text: str) -> str:
    softened = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    softened = softened.replace("\ufeff", "").replace("\u200b", "")
    softened = _EDGE_TTS_PUNCT_RE.sub(" ", softened)
    softened = _EDGE_TTS_SPACE_RE.sub(" ", softened).strip()
    return softened


def _edge_tts_text_candidates(text: str) -> list[tuple[str, str]]:
    base = (text or "").strip()
    seen: set[str] = set()
    out: list[tuple[str, str]] = []

    def _add(label: str, candidate: str) -> None:
        normalized = candidate.strip()
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        out.append((label, normalized))

    # Edge's online TTS sporadically rejects some Vietnamese cues that mix
    # punctuation with composed diacritics. Keep the original text first, then
    # progressively fall back to less fragile Unicode / punctuation forms.
    _add("original", base)
    _add("nfkd", unicodedata.normalize("NFKD", base))
    _add("soft_punct", _soften_edge_tts_text(base))
    _add("nfkd_soft_punct", _soften_edge_tts_text(unicodedata.normalize("NFKD", base)))
    return out


class EdgeTtsProvider(TTSProvider):
    async def synthesize_cue_to_wav(
        self,
        text: str,
        out_wav: Path,
        *,
        voice: str,
        rate: str,
        diag_prefix: str = "",
        provider_config: dict | None = None,
    ) -> int:
        import edge_tts

        del provider_config

        rate_arg = rate.strip() if rate else "+0%"

        ffmpeg, ff_err = resolve_ffmpeg_executable()
        if ffmpeg is None:
            raise RuntimeError(ff_err or "ffmpeg not found.")

        out_wav.parent.mkdir(parents=True, exist_ok=True)
        text_candidates = _edge_tts_text_candidates(text)
        for attempt_idx, (variant_label, candidate_text) in enumerate(text_candidates, start=1):
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                mp3_path = Path(tmp.name)
            try:
                if diag_prefix:
                    prefix = "edge-tts: saving" if variant_label == "original" else (
                        f"edge-tts: retry transform={variant_label} saving"
                    )
                    print(f"{diag_prefix} {prefix} temp mp3 -> {mp3_path}", file=sys.stderr)
                communicate = edge_tts.Communicate(candidate_text, voice, rate=rate_arg)
                await communicate.save(str(mp3_path))
                if diag_prefix:
                    exists = mp3_path.is_file()
                    size = mp3_path.stat().st_size if exists else -1
                    print(
                        f"{diag_prefix} edge-tts: temp mp3 exists={exists} size_bytes={size}",
                        file=sys.stderr,
                    )
                if not mp3_path.is_file():
                    raise RuntimeError("edge-tts did not create the temp mp3 file.")
                if mp3_path.stat().st_size <= 0:
                    raise RuntimeError("No audio was received (edge-tts returned empty mp3).")
                if diag_prefix:
                    print(f"{diag_prefix} ffmpeg: starting mp3->wav conversion...", file=sys.stderr)
                proc = await asyncio.create_subprocess_exec(
                    ffmpeg,
                    "-y",
                    "-i",
                    str(mp3_path),
                    "-acodec",
                    "pcm_s16le",
                    "-ar",
                    "24000",
                    "-ac",
                    "1",
                    str(out_wav),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    err = (stderr or b"").decode("utf-8", errors="replace")[-2000:]
                    raise RuntimeError(f"ffmpeg failed (exit {proc.returncode}): {err}")
                if diag_prefix and variant_label != "original":
                    print(
                        f"{diag_prefix} edge-tts: recovered with transform={variant_label}",
                        file=sys.stderr,
                    )
                return _wav_duration_ms(out_wav)
            except Exception as exc:
                retryable = _is_retryable_no_audio_error(exc)
                if diag_prefix and variant_label != "original":
                    print(
                        f"{diag_prefix} edge-tts: transform={variant_label} failed "
                        f"retryable={retryable} err={exc}",
                        file=sys.stderr,
                    )
                if not retryable or attempt_idx >= len(text_candidates):
                    raise
            finally:
                mp3_path.unlink(missing_ok=True)

        raise RuntimeError("edge-tts failed without producing audio.")


def _wav_duration_ms(path: Path) -> int:
    import wave

    with wave.open(str(path), "rb") as w:
        frames = w.getnframes()
        rate = w.getframerate() or 24000
        return int(frames / float(rate) * 1000.0)
