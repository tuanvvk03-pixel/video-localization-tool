"""OCR provider adapters (PaddleOCR + RapidOCR)."""
from __future__ import annotations

from engine.ocr.base import OcrFrameResult, OcrLine, OcrProvider


SUPPORTED_PROVIDERS: tuple[str, ...] = ("paddleocr", "rapidocr")


def canonical_provider_name(name: str) -> str:
    """Return the canonical internal key for a provider name, or '' if unknown."""
    key = (name or "").strip().lower().replace("-", "_")
    if key in ("", "paddle", "paddleocr", "paddle_ocr"):
        return "paddleocr"
    if key in ("rapid", "rapidocr", "rapid_ocr", "rapidocr_onnxruntime"):
        return "rapidocr"
    return ""


def get_ocr_provider(name: str, *, device: str = "auto") -> OcrProvider:
    canonical = canonical_provider_name(name)
    if canonical == "paddleocr":
        from engine.ocr.paddle_provider import PaddleOcrProvider

        return PaddleOcrProvider(device=device)
    if canonical == "rapidocr":
        from engine.ocr.rapid_provider import RapidOcrProvider

        return RapidOcrProvider(device=device)
    raise ValueError(
        f"Unknown OCR provider {name!r}. Supported: {', '.join(SUPPORTED_PROVIDERS)}."
    )


__all__ = [
    "OcrProvider",
    "OcrFrameResult",
    "OcrLine",
    "get_ocr_provider",
    "canonical_provider_name",
    "SUPPORTED_PROVIDERS",
]
