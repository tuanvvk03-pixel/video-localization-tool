"""TTS provider adapters (edge-tts MVP; room for Azure etc.)."""
from __future__ import annotations

from engine.tts.base import TTSProvider
from engine.tts.azure_tts_provider import AzureTtsProvider
from engine.tts.edge_tts_provider import EdgeTtsProvider
from engine.tts.xtts_provider import XttsProvider

_DEFAULT_REGISTRY: dict[str, type[TTSProvider]] = {
    "edge_tts": EdgeTtsProvider,
    "azure_tts": AzureTtsProvider,
    # Optional voice-cloning provider (coqui XTTS). Lazy-imports torch/TTS only
    # when a cue actually synthesizes, so registering it costs nothing here.
    "xtts": XttsProvider,
}


def get_tts_provider(name: str) -> TTSProvider:
    key = (name or "").strip().lower().replace("-", "_")
    if key == "edge":
        key = "edge_tts"
    if key == "azure":
        key = "azure_tts"
    if key in ("coqui", "xtts_v2", "xttsv2"):
        key = "xtts"
    cls = _DEFAULT_REGISTRY.get(key)
    if cls is None:
        raise ValueError(
            f"Unknown TTS provider {name!r}. Supported: {', '.join(sorted(_DEFAULT_REGISTRY))}."
        )
    return cls()
