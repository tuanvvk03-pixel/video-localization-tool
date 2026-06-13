"""RapidOCR provider — ONNX-based alternative to PaddleOCR.

RapidOCR (rapidocr_onnxruntime) ships as a ~50 MB ONNX bundle and runs on
CPU out of the box; GPU requires the `rapidocr-onnxruntime-gpu` wheel +
CUDA onnxruntime. This provider lazy-imports the package so the rest of
the engine still works without it installed.
"""
from __future__ import annotations

import sys
from pathlib import Path

from engine.ocr.base import OcrFrameResult, OcrLine, OcrProvider


def _probe_onnx_cuda() -> bool:
    """Best-effort probe for onnxruntime CUDAExecutionProvider availability."""
    try:
        import onnxruntime as ort  # type: ignore
    except Exception:
        return False
    try:
        providers = list(ort.get_available_providers())
    except Exception:
        return False
    return "CUDAExecutionProvider" in providers


def _resolve_device(requested: str) -> str:
    req = (requested or "auto").strip().lower()
    if req == "cpu":
        return "cpu"
    if req in ("cuda", "gpu"):
        return "cuda" if _probe_onnx_cuda() else "cpu"
    # auto
    return "cuda" if _probe_onnx_cuda() else "cpu"


_LANG_ALIASES = {
    "zh": "ch",
    "zh-cn": "ch",
    "zh_cn": "ch",
    "chinese": "ch",
    "japan": "japan",
    "ja": "japan",
    "ko": "korean",
    "en": "en",
    "english": "en",
    "vi": "en",
    "vie": "en",
}


def _normalize_lang(lang: str) -> str:
    key = (lang or "").strip().lower().replace("-", "_")
    return _LANG_ALIASES.get(key, key or "ch")


class RapidOcrProvider(OcrProvider):
    name = "rapidocr"

    def __init__(self, *, device: str = "auto") -> None:
        self._requested_device = (device or "auto").strip().lower()
        self._resolved_device = _resolve_device(self._requested_device)
        self._engine = None
        self._engine_lang: str | None = None

    def device_used(self) -> str:
        return "cuda" if self._resolved_device == "cuda" else "cpu"

    def _load_engine(self, use_cuda: bool):
        try:
            from rapidocr_onnxruntime import RapidOCR  # type: ignore
        except Exception as exc:
            raise RuntimeError(
                "rapidocr_onnxruntime is not installed. Install with: pip install rapidocr_onnxruntime"
            ) from exc
        kwargs: dict = {}
        if use_cuda:
            # rapidocr-onnxruntime >= 1.3 exposes providers via det_use_cuda / rec_use_cuda kwargs.
            kwargs["det_use_cuda"] = True
            kwargs["rec_use_cuda"] = True
            kwargs["cls_use_cuda"] = True
        try:
            return RapidOCR(**kwargs)
        except TypeError:
            return RapidOCR()

    def _ensure_engine(self, lang: str):
        norm = _normalize_lang(lang)
        if self._engine is not None and self._engine_lang == norm:
            return self._engine
        use_cuda = self._resolved_device == "cuda"
        try:
            self._engine = self._load_engine(use_cuda=use_cuda)
        except Exception as exc:
            if use_cuda:
                print(
                    f"[ocr] WARNING: RapidOCR CUDA init failed ({exc}); falling back to CPU.",
                    file=sys.stderr,
                )
                self._resolved_device = "cpu"
                self._engine = self._load_engine(use_cuda=False)
            else:
                raise
        self._engine_lang = norm
        return self._engine

    def recognize_image(self, image_path: Path, *, language: str) -> OcrFrameResult:
        engine = self._ensure_engine(language)
        try:
            result, _elapsed = engine(str(image_path))
        except Exception as exc:
            raise RuntimeError(f"RapidOCR failed on {image_path.name}: {exc}") from exc
        lines = _parse_rapid_result(result)
        return OcrFrameResult(lines=lines, device_used=self.device_used())


def _parse_rapid_result(raw) -> list[OcrLine]:
    """RapidOCR returns [[bbox_pts, text, confidence], ...] or None.

    bbox_pts is a list of 4 (x, y) points.
    """
    out: list[OcrLine] = []
    if not raw:
        return out
    for entry in raw:
        if not entry:
            continue
        bbox_pts = text = conf = None
        if isinstance(entry, (list, tuple)):
            if len(entry) >= 3:
                bbox_pts, text, conf = entry[0], entry[1], entry[2]
            elif len(entry) == 2:
                bbox_pts, text = entry[0], entry[1]
        elif isinstance(entry, dict):
            bbox_pts = entry.get("bbox") or entry.get("points")
            text = entry.get("text")
            conf = entry.get("confidence") or entry.get("score")
        else:
            continue
        text_s = str(text or "").strip()
        if not text_s:
            continue
        try:
            conf_f = float(conf) if conf is not None else 0.0
        except (TypeError, ValueError):
            conf_f = 0.0
        x0 = y0 = x1 = y1 = 0.0
        if isinstance(bbox_pts, (list, tuple)) and bbox_pts:
            xs: list[float] = []
            ys: list[float] = []
            for pt in bbox_pts:
                if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                    try:
                        xs.append(float(pt[0]))
                        ys.append(float(pt[1]))
                    except (TypeError, ValueError):
                        pass
            if xs and ys:
                x0, x1 = min(xs), max(xs)
                y0, y1 = min(ys), max(ys)
        out.append(OcrLine(text=text_s, confidence=conf_f, bbox=(x0, y0, x1, y1)))
    return out
