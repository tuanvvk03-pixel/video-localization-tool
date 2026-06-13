"""PaddleOCR provider — recognizes text on a single image (frame).

Lazy-imports paddleocr so the rest of the engine still works without it installed.
Supports `--device auto|cpu|cuda` with silent CPU fallback when CUDA is unavailable.
"""
from __future__ import annotations

import sys
from pathlib import Path

from engine.ocr.base import OcrFrameResult, OcrLine, OcrProvider


def _probe_cuda_available() -> bool:
    """Best-effort probe of paddle CUDA availability without importing PaddleOCR."""
    try:
        import paddle
    except Exception:
        return False
    try:
        if not paddle.device.is_compiled_with_cuda():
            return False
    except Exception:
        return False
    try:
        return int(paddle.device.cuda.device_count()) > 0
    except Exception:
        return False


def _resolve_device(requested: str) -> str:
    req = (requested or "auto").strip().lower()
    if req == "cpu":
        return "cpu"
    if req in ("cuda", "gpu"):
        return "gpu" if _probe_cuda_available() else "cpu"
    return "gpu" if _probe_cuda_available() else "cpu"


_LANG_ALIASES = {
    "zh": "ch",
    "zh-cn": "ch",
    "zh_cn": "ch",
    "chinese": "ch",
    "vi": "vi",
    "vie": "vi",
    "en": "en",
    "english": "en",
    "ja": "japan",
    "ko": "korean",
}


def _normalize_lang(lang: str) -> str:
    key = (lang or "").strip().lower().replace("-", "_")
    return _LANG_ALIASES.get(key, key or "ch")


class PaddleOcrProvider(OcrProvider):
    name = "paddleocr"

    def __init__(self, *, device: str = "auto") -> None:
        self._requested_device = (device or "auto").strip().lower()
        self._resolved_device = _resolve_device(self._requested_device)
        self._engine = None
        self._engine_lang: str | None = None

    def device_used(self) -> str:
        return "cuda" if self._resolved_device == "gpu" else "cpu"

    def _ensure_engine(self, lang: str):
        norm = _normalize_lang(lang)
        if self._engine is not None and self._engine_lang == norm:
            return self._engine
        try:
            from paddleocr import PaddleOCR
        except Exception as exc:
            raise RuntimeError(
                "paddleocr is not installed. Install with: pip install paddleocr paddlepaddle"
            ) from exc

        use_gpu = self._resolved_device == "gpu"

        def _attempts(gpu: bool) -> list[dict]:
            device_str = "gpu" if gpu else "cpu"
            # Modern 3.x first (device= + use_textline_orientation), with
            # enable_mkldnn=False to dodge a known Windows oneDNN bug that
            # raises `NotImplementedError: ConvertPirAttribute2RuntimeAttribute`
            # on paddlepaddle 3.3.x during inference. Then fall back through
            # legacy 2.x args.
            return [
                {"lang": norm, "device": device_str, "use_textline_orientation": True, "enable_mkldnn": False},
                {"lang": norm, "device": device_str, "use_textline_orientation": True},
                {"lang": norm, "device": device_str},
                {"lang": norm, "use_angle_cls": True, "use_gpu": gpu, "show_log": False},
                {"lang": norm, "use_angle_cls": True, "use_gpu": gpu},
                {"lang": norm, "use_gpu": gpu},
                {"lang": norm},
            ]

        def _try_build(attempt_list: list[dict]) -> tuple[object | None, Exception | None]:
            last_exc: Exception | None = None
            for kwargs in attempt_list:
                try:
                    return PaddleOCR(**kwargs), None
                except (TypeError, ValueError) as exc:
                    last_exc = exc
                    continue
                except Exception as exc:
                    return None, exc
            return None, last_exc

        engine, err = _try_build(_attempts(use_gpu))
        if engine is None and use_gpu:
            print(
                f"[ocr] WARNING: PaddleOCR GPU init failed ({err}); falling back to CPU.",
                file=sys.stderr,
            )
            self._resolved_device = "cpu"
            engine, err = _try_build(_attempts(False))
        if engine is None:
            raise RuntimeError(f"PaddleOCR init failed: {err}") from err

        self._engine = engine
        self._engine_lang = norm
        return self._engine

    def recognize_image(self, image_path: Path, *, language: str) -> OcrFrameResult:
        engine = self._ensure_engine(language)
        path_s = str(image_path)
        raw = None
        # PaddleOCR 3.x exposes predict(); 2.x used ocr(..., cls=True). Try
        # them in order and fall through kwarg rejections quietly.
        for call in (
            lambda: engine.predict(path_s) if hasattr(engine, "predict") else None,
            lambda: engine.ocr(path_s, cls=True) if hasattr(engine, "ocr") else None,
            lambda: engine.ocr(path_s) if hasattr(engine, "ocr") else None,
        ):
            try:
                result = call()
            except (TypeError, ValueError):
                continue
            except Exception as exc:
                raise RuntimeError(f"PaddleOCR.ocr failed on {image_path.name}: {exc}") from exc
            if result is not None:
                raw = list(result) if not isinstance(result, (list, dict)) else result
                break

        lines = _parse_paddle_result(raw)
        return OcrFrameResult(lines=lines, device_used=self.device_used())


def _parse_paddle_result(raw) -> list[OcrLine]:
    """PaddleOCR result parser covering both 2.x and 3.x output shapes.

    - 2.x ocr(): nested lists of ``[bbox_pts, (text, confidence)]`` entries.
    - 3.x predict(): list of dict-like objects exposing ``rec_texts``,
      ``rec_scores``, and ``rec_polys``/``dt_polys``.
    """
    out: list[OcrLine] = []
    if raw is None:
        return out

    pages = raw if isinstance(raw, list) else [raw]
    for page in pages:
        if page is None:
            continue
        # 3.x predict() result: a dict-like with rec_texts/rec_scores/rec_polys.
        if _looks_like_paddle3_result(page):
            out.extend(_parse_paddle3_page(page))
            continue
        if not isinstance(page, list):
            continue
        for entry in page:
            if not entry:
                continue
            bbox_pts = None
            text_conf = None
            if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                bbox_pts, text_conf = entry[0], entry[1]
            elif isinstance(entry, dict):
                bbox_pts = entry.get("bbox") or entry.get("points")
                text_conf = (entry.get("text"), entry.get("confidence"))
            else:
                continue

            text = ""
            conf = 0.0
            if isinstance(text_conf, (list, tuple)) and len(text_conf) >= 2:
                text = str(text_conf[0] or "").strip()
                try:
                    conf = float(text_conf[1])
                except (TypeError, ValueError):
                    conf = 0.0
            elif isinstance(text_conf, str):
                text = text_conf.strip()

            if not text:
                continue

            x0 = y0 = x1 = y1 = 0.0
            if isinstance(bbox_pts, (list, tuple)) and bbox_pts:
                xs = []
                ys = []
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

            out.append(OcrLine(text=text, confidence=conf, bbox=(x0, y0, x1, y1)))
    return out


def _looks_like_paddle3_result(page) -> bool:
    if isinstance(page, dict):
        getter = page.get
    elif hasattr(page, "get") and callable(page.get):
        getter = page.get
    else:
        return False
    try:
        return getter("rec_texts") is not None or getter("rec_polys") is not None or getter("dt_polys") is not None
    except Exception:
        return False


def _parse_paddle3_page(page) -> list[OcrLine]:
    getter = page.get
    texts = list(getter("rec_texts") or [])
    scores = list(getter("rec_scores") or [])
    polys = list(getter("rec_polys") or getter("dt_polys") or [])
    lines: list[OcrLine] = []
    for i, raw_text in enumerate(texts):
        text = str(raw_text or "").strip()
        if not text:
            continue
        try:
            conf = float(scores[i]) if i < len(scores) else 0.0
        except (TypeError, ValueError):
            conf = 0.0
        x0 = y0 = x1 = y1 = 0.0
        if i < len(polys):
            xs: list[float] = []
            ys: list[float] = []
            for pt in polys[i]:
                try:
                    xs.append(float(pt[0]))
                    ys.append(float(pt[1]))
                except (TypeError, ValueError, IndexError):
                    pass
            if xs and ys:
                x0, x1 = min(xs), max(xs)
                y0, y1 = min(ys), max(ys)
        lines.append(OcrLine(text=text, confidence=conf, bbox=(x0, y0, x1, y1)))
    return lines
