"""Abstract OCR provider for engine/run_ocr_stage.py."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OcrLine:
    """One recognized text line on a frame."""

    text: str
    confidence: float
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)


@dataclass
class OcrFrameResult:
    """All recognized lines on one frame plus the device used."""

    lines: list[OcrLine] = field(default_factory=list)
    device_used: str = "cpu"

    @property
    def joined_text(self) -> str:
        parts = [ln.text.strip() for ln in self.lines if (ln.text or "").strip()]
        return "\n".join(parts)

    @property
    def mean_confidence(self) -> float:
        vals = [float(ln.confidence) for ln in self.lines if ln.text]
        if not vals:
            return 0.0
        return sum(vals) / len(vals)


class OcrProvider(ABC):
    """Synchronous OCR over a single image file (one extracted frame)."""

    name: str = "base"

    @abstractmethod
    def recognize_image(
        self,
        image_path: Path,
        *,
        language: str,
    ) -> OcrFrameResult:
        """Return all detected lines for one image."""

    def device_used(self) -> str:
        """Best-effort label for the device actually used (filled in after first recognize call)."""
        return "cpu"
