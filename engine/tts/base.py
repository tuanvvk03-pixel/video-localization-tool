"""Abstract TTS provider (async) for engine/run_tts_stage.py."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class TTSProvider(ABC):
    """One WAV file per cue; returns decoded audio duration in milliseconds."""

    @abstractmethod
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
        """Write PCM WAV to out_wav; return audio_duration_ms."""
