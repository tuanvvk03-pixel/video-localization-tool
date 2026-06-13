"""
Azure Speech TTS provider (production path).

Requires environment:
- AZURE_SPEECH_KEY
- AZURE_SPEECH_REGION
"""
from __future__ import annotations

import html
from pathlib import Path

from engine.runtime_app_settings import resolve_azure_speech_configs
from engine.tts.base import TTSProvider


class AzureTtsProvider(TTSProvider):
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
        try:
            import azure.cognitiveservices.speech as speechsdk
        except ImportError as e:
            raise RuntimeError(
                f"azure-cognitiveservices-speech is not installed ({e}). "
                "Install with: pip install azure-cognitiveservices-speech"
            ) from e

        cfg = provider_config or _default_azure_config()
        key = str(cfg.get("key") or "").strip()
        region = str(cfg.get("region") or "").strip()
        config_label = str(cfg.get("label") or "azure")
        if not key or not region:
            raise RuntimeError(
                "Missing Azure Speech config. Save Azure credentials in App Settings "
                "or set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION."
            )

        out_wav.parent.mkdir(parents=True, exist_ok=True)

        speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        speech_config.speech_synthesis_voice_name = voice
        # Match our current pipeline convention (24kHz mono PCM WAV)
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
        )

        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(out_wav))
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config
        )

        ssml = _build_ssml(text=text, voice=voice, rate=rate)

        if diag_prefix:
            import sys

            print(
                f"{diag_prefix} azure-tts: profile={config_label!r} region={region!r} "
                f"voice={voice!r} writing_wav={out_wav}",
                file=sys.stderr,
            )

        # SDK future is not awaitable; run in a thread.
        import asyncio

        result = await asyncio.to_thread(lambda: synthesizer.speak_ssml_async(ssml).get())

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return _wav_duration_ms(out_wav)

        if result.reason == speechsdk.ResultReason.Canceled:
            details = _get_synthesis_cancellation_details(speechsdk, result)
            reason = getattr(details, "reason", None)
            error_details = getattr(details, "error_details", None)
            raise RuntimeError(
                f"azure-tts canceled: reason={reason!r} error_details={error_details!r}"
            )

        raise RuntimeError(f"azure-tts failed: reason={result.reason}")


def _default_azure_config() -> dict[str, str]:
    configs = resolve_azure_speech_configs()
    if not configs:
        return {}
    return configs[0]


def _get_synthesis_cancellation_details(speechsdk, result):
    """
    Python Speech SDK pattern uses constructor-style cancellation details, not from_result.
    Keep this helper version-tolerant.
    """
    cls = getattr(speechsdk, "SpeechSynthesisCancellationDetails", None)
    if cls is None:
        return None
    try:
        return cls(result)  # type: ignore[misc]
    except TypeError:
        return cls(result=result)  # type: ignore[call-arg]


def _build_ssml(*, text: str, voice: str, rate: str) -> str:
    safe_text = html.escape((text or "").strip())
    safe_voice = html.escape(voice)
    r = (rate or "").strip() or "+0%"
    ssml_rate = _rate_to_ssml(r)
    # Keep minimal SSML; Azure expects prosody rate like "+10%" or "-5%".
    return (
        "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
        "<speak version=\"1.0\" xmlns=\"http://www.w3.org/2001/10/synthesis\" xml:lang=\"vi-VN\">"
        f"<voice name=\"{safe_voice}\">"
        f"<prosody rate=\"{html.escape(ssml_rate)}\">{safe_text}</prosody>"
        "</voice></speak>"
    )


def _rate_to_ssml(rate: str) -> str:
    r = rate.strip()
    if not r:
        return "+0%"
    # Accept "+10%" / "-5%" / "10%" / "-5"
    if r.endswith("%"):
        return r if r.startswith(("+", "-")) else f"+{r}"
    if r[0].isdigit():
        return f"+{r}%"
    if r.startswith(("+", "-")) and r[1:].isdigit():
        return f"{r}%"
    return r


def _wav_duration_ms(path: Path) -> int:
    import wave

    with wave.open(str(path), "rb") as w:
        frames = w.getnframes()
        rate = w.getframerate() or 24000
        return int(frames / float(rate) * 1000.0)

