"""Coqui XTTS voice-cloning TTS provider (offline, optional dependency).

Implements the :class:`~engine.tts.base.TTSProvider` interface so a cue can use a
*cloned* voice via the per-cue override
``{"provider": "xtts", "voice_id": "<path to a 6-30s speaker .wav>"}`` — the
``voice`` argument is the speaker reference clip.

Two model paths (chosen by env / provider_config):

* **Base XTTS-v2** (``XTTS_MODEL`` or default) via ``TTS.api`` — supports
  en/es/fr/de/it/pt/pl/tr/ru/nl/cs/ar/zh-cn/hu/ko/ja/hi. **Not Vietnamese.**
* **Fine-tuned local checkpoint** (``XTTS_MODEL_DIR``) via the low-level ``Xtts``
  model — this is how **Vietnamese** works: point it at a downloaded
  `capleaf/viXTTS` checkpoint dir. The provider patches the tokenizer to accept
  ``vi`` (newer coqui-tts rejects it) — verified producing real vi audio.

Optional + heavy: ``TTS`` (coqui) + ``torch`` (GBs) + ideally a CUDA GPU. NOT
bundled; imports are lazy with an actionable error when missing. See
docs/15_voice_cloning.md. Verify with ``scripts/xtts_smoke.py``.
"""
from __future__ import annotations

import os
import re
import wave
from pathlib import Path
from typing import Any

from engine.tts.base import TTSProvider

_DEFAULT_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
_DEFAULT_LANGUAGE = "vi"

# Cache loaded models across cues for the life of the process.
_MODEL_CACHE: dict[str, Any] = {}


def _install_hint(exc: BaseException) -> str:
    return (
        f"Coqui TTS (XTTS) is not available ({exc}). Voice cloning needs the optional "
        "'TTS' package + torch: pip install coqui-tts torch. A CUDA GPU is strongly "
        "recommended (CPU synthesis is very slow). See docs/15_voice_cloning.md."
    )


def _vi_clean(txt: str) -> str:
    """Minimal Vietnamese normalization (the viXTTS BPE vocab does the real work)."""
    return re.sub(r"\s+", " ", str(txt).strip().lower())


def _wav_duration_ms(path: Path) -> int:
    with wave.open(str(path), "rb") as w:
        frames = w.getnframes()
        rate = w.getframerate() or 24000
    if frames <= 0 or rate <= 0:
        raise ValueError("invalid wav written by XTTS: no frames/rate")
    return int(frames / float(rate) * 1000.0)


def _gpu_enabled() -> bool:
    raw = str(os.environ.get("XTTS_GPU") or "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    try:
        import torch  # type: ignore

        return bool(torch.cuda.is_available())
    except Exception:  # noqa: BLE001
        return False


def _load_api_model(model_name: str, *, gpu: bool):
    try:
        from TTS.api import TTS  # type: ignore  # noqa: N811
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(_install_hint(e)) from e
    try:
        return TTS(model_name, gpu=gpu)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(_install_hint(e)) from e


def _load_xtts_dir(model_dir: str, *, gpu: bool):
    """Load a fine-tuned XTTS checkpoint dir (e.g. viXTTS) via the low-level API."""
    try:
        from TTS.tts.configs.xtts_config import XttsConfig  # type: ignore
        from TTS.tts.models.xtts import Xtts  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(_install_hint(e)) from e
    d = Path(model_dir).expanduser()
    if not (d / "config.json").is_file():
        raise RuntimeError(f"XTTS_MODEL_DIR has no config.json: {d}")
    config = XttsConfig()
    config.load_json(str(d / "config.json"))
    model = Xtts.init_from_config(config)
    vocab = d / "vocab.json"
    model.load_checkpoint(
        config,
        checkpoint_dir=str(d),
        vocab_path=str(vocab) if vocab.is_file() else None,
        use_deepspeed=False,
    )
    if gpu:
        model.cuda()
    # Newer coqui-tts tokenizers reject 'vi'; viXTTS targets an older one. Patch
    # char_limits + preprocess_text so vi flows through (BPE vocab tokenizes vi).
    try:
        model.tokenizer.char_limits.setdefault("vi", 250)
    except Exception:  # noqa: BLE001
        pass
    _orig_pp = model.tokenizer.preprocess_text

    def _pp(txt: str, lang: str, _orig=_orig_pp):
        if str(lang).startswith("vi"):
            return _vi_clean(txt)
        return _orig(txt, lang)

    model.tokenizer.preprocess_text = _pp
    return model, config


class XttsProvider(TTSProvider):
    """Clone the voice in a reference clip (``voice`` = path to a speaker .wav)."""

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
        speaker_wav = str(voice or "").strip()
        if not speaker_wav:
            raise RuntimeError(
                "XTTS needs a speaker reference clip: set the cue's voice to the "
                "absolute path of a 6-30s .wav of the target voice."
            )
        speaker_path = Path(speaker_wav).expanduser()
        if not speaker_path.is_file():
            raise RuntimeError(f"XTTS speaker reference not found: {speaker_path}")

        cfg = provider_config or {}
        language = str(cfg.get("language") or os.environ.get("XTTS_LANGUAGE") or _DEFAULT_LANGUAGE)
        gpu = _gpu_enabled()
        model_dir = str(cfg.get("model_dir") or os.environ.get("XTTS_MODEL_DIR") or "").strip()
        out_wav.parent.mkdir(parents=True, exist_ok=True)

        try:
            if model_dir:
                # Fine-tuned local checkpoint (viXTTS for Vietnamese).
                key = f"dir:{model_dir}|gpu={gpu}"
                if key not in _MODEL_CACHE:
                    _MODEL_CACHE[key] = _load_xtts_dir(model_dir, gpu=gpu)
                model, config = _MODEL_CACHE[key]
                import numpy as np  # type: ignore
                import soundfile as sf  # type: ignore

                gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
                    audio_path=[str(speaker_path)],
                    gpt_cond_len=config.gpt_cond_len,
                    max_ref_length=config.max_ref_len,
                    sound_norm_refs=config.sound_norm_refs,
                )
                out = model.inference(
                    text,
                    language,
                    gpt_cond_latent,
                    speaker_embedding,
                    temperature=0.3,
                    length_penalty=config.length_penalty,
                    repetition_penalty=config.repetition_penalty,
                    top_k=config.top_k,
                    top_p=config.top_p,
                    enable_text_splitting=False,
                )
                # XTTS returns float32; write PCM16 (24kHz mono) to match the other
                # providers + stay readable by the wave module / downstream mix.
                sf.write(str(out_wav), np.asarray(out["wav"], dtype="float32"), 24000, subtype="PCM_16")
            else:
                # Base XTTS-v2 via the high-level API (non-Vietnamese languages).
                model_name = str(cfg.get("model") or os.environ.get("XTTS_MODEL") or _DEFAULT_MODEL)
                key = f"api:{model_name}|gpu={gpu}"
                if key not in _MODEL_CACHE:
                    _MODEL_CACHE[key] = _load_api_model(model_name, gpu=gpu)
                _MODEL_CACHE[key].tts_to_file(
                    text=text,
                    speaker_wav=str(speaker_path),
                    language=language,
                    file_path=str(out_wav),
                )
        except RuntimeError:
            raise
        except Exception as e:  # noqa: BLE001
            hint = ""
            if "is not supported" in str(e) and language.startswith("vi"):
                hint = " (Vietnamese needs viXTTS: set XTTS_MODEL_DIR to a capleaf/viXTTS checkpoint — see docs/15_voice_cloning.md)"
            raise RuntimeError(f"XTTS synthesis failed: {e}{hint}") from e
        if not out_wav.is_file() or out_wav.stat().st_size < 44:
            raise RuntimeError("XTTS produced no/empty WAV output.")
        return _wav_duration_ms(out_wav)
