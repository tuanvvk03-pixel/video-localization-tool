"""Block-based Chinese ASR subtitle cleanup (no translation)."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

from engine.srt_cues import SRTCue


class CleanupSourceZHError(RuntimeError):
    pass


def _chunk_cues(cues: list[SRTCue], *, block_size: int) -> list[list[SRTCue]]:
    n = len(cues)
    if n == 0:
        return []
    bs = max(1, min(20, int(block_size)))
    out: list[list[SRTCue]] = []
    i = 0
    while i < n:
        out.append(cues[i : i + bs])
        i += bs
    return out


def _ms_to_ts(ms: int) -> str:
    ms = max(0, int(ms))
    h = ms // 3_600_000
    ms -= h * 3_600_000
    m = ms // 60_000
    ms -= m * 60_000
    s = ms // 1000
    ms -= s * 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _build_system_prompt() -> str:
    return (
        "You fix Chinese subtitle text from defective ASR (speech recognition). "
        "The input is Mandarin/subtitle Chinese only.\n"
        "Hard rules:\n"
        "- Do NOT translate. Output Chinese only. Never output Vietnamese or English except proper nouns if clearly present in context.\n"
        "- Preserve meaning and dialogue tone (register, speaker attitude) as closely as possible.\n"
        "- Fix common homophone/ASR errors; remove meaningless filler if it does not carry meaning.\n"
        "- Source may contain broken proper nouns, pop-culture references, idioms, or historical names. If nearby cues make the intended Chinese wording reasonably clear, restore the intended wording instead of keeping the garbled ASR surface form.\n"
        "- Prefer natural colloquial Chinese. Do not invent content not grounded in the ASR line.\n"
        "- Do not lengthen lines unnecessarily; keep similar length when possible.\n"
        "- If ASR is too garbled, output the safest short natural fix and set low_confidence true.\n"
        "- Set suspicious_asr true if the raw line looks like noise or unrelated script.\n"
        "- Set heavy_rewrite true if you change more than light typo-level edits.\n"
        "- Set likely_numeric_fix true if the main fix is numbers/dates/units.\n"
        "- Return STRICT JSON only (no markdown).\n"
    )


def _build_user_payload(
    *,
    block: list[SRTCue],
    context_before: list[SRTCue],
    context_after: list[SRTCue],
) -> str:
    def pack(c: SRTCue) -> dict[str, Any]:
        return {
            "index": int(c.index),
            "ts": f"{_ms_to_ts(c.start_ms)} --> {_ms_to_ts(c.end_ms)}",
            "text": c.text,
        }

    payload = {
        "task": "Clean ASR Chinese subtitle cues; return one entry per cue in block with same index.",
        "context_before": [pack(c) for c in context_before],
        "block": [pack(c) for c in block],
        "context_after": [pack(c) for c in context_after],
        "output_schema": {
            "cues": [
                {
                    "index": 0,
                    "cleaned_text": "Chinese only",
                    "low_confidence": False,
                    "suspicious_asr": False,
                    "heavy_rewrite": False,
                    "likely_numeric_fix": False,
                }
            ]
        },
        "rules": [
            "Return STRICT JSON: object with key 'cues' (array).",
            "Exactly one object per cue in 'block', same index order as block.",
            "Do not change indices.",
            "cleaned_text must be non-empty string (use minimal fix if unsure).",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _call_openai_json(*, api_key: str, model: str, system: str, user: str) -> dict:
    # Managed mode: route through the platform backend (server holds the OpenAI
    # key + meters tokens) so source cleanup works without a local key — same as
    # the translate stage. Falls back to the local BYOK path below if the cloud
    # client isn't available or the user isn't signed in.
    try:
        from desktop.cloud_account import account, managed_enabled  # type: ignore

        if managed_enabled():
            text, _usage = account().translate(
                system, user, model_spec=(f"openai:{model}" if model else "")
            )
            try:
                return json.loads(text)
            except Exception as e:  # noqa: BLE001
                raise CleanupSourceZHError(
                    f"Managed cleanup did not return valid JSON. head={text[:400]!r}"
                ) from e
    except ImportError:
        pass  # desktop client not on path (pure-engine/CLI use) → BYOK below

    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:  # pragma: no cover
        raise CleanupSourceZHError(
            "Missing dependency 'openai'. Install engine/requirements.txt."
        ) from e

    client = OpenAI(api_key=api_key)
    resp = client.responses.create(model=model, instructions=system, input=user)
    text = (getattr(resp, "output_text", None) or "").strip()
    if not text:
        try:
            out_items = getattr(resp, "output", None) or []
            chunks: list[str] = []
            for it in out_items:
                content = getattr(it, "content", None) or []
                for c in content:
                    t = getattr(c, "text", None)
                    if isinstance(t, str) and t:
                        chunks.append(t)
            text = "\n".join(chunks).strip()
        except Exception:
            text = ""
    try:
        return json.loads(text)
    except Exception as e:
        raise CleanupSourceZHError(f"Model did not return valid JSON. head={text[:400]!r}") from e


_ZH_RE = re.compile(r"[\u4e00-\u9fff]")


def _has_chinese(s: str) -> bool:
    return bool(_ZH_RE.search(s or ""))


@dataclass(frozen=True)
class CleanupCueResult:
    index: int
    raw_text: str
    cleaned_text: str
    changed: bool
    low_confidence: bool
    suspicious_asr: bool
    heavy_rewrite: bool
    likely_numeric_fix: bool


def cleanup_zh_cues_in_blocks(
    *,
    cues: list[SRTCue],
    api_key: str,
    model: str,
    block_size: int,
    context_cues: int,
) -> tuple[list[CleanupCueResult], dict[str, Any]]:
    system = _build_system_prompt()
    blocks = _chunk_cues(cues, block_size=block_size)
    n = len(cues)
    idx_to_pos = {int(c.index): i for i, c in enumerate(cues)}
    results: list[CleanupCueResult] = []
    meta_blocks: list[dict[str, Any]] = []
    started = time.time()

    for b in blocks:
        first, last = b[0], b[-1]
        b_start = idx_to_pos.get(int(first.index), 0)
        b_end = idx_to_pos.get(int(last.index), b_start) + 1
        cb = cues[max(0, b_start - int(context_cues)) : b_start]
        ca = cues[b_end : min(n, b_end + int(context_cues))]

        user = _build_user_payload(block=b, context_before=cb, context_after=ca)
        out = _call_openai_json(api_key=api_key, model=model, system=system, user=user)
        items = out.get("cues") or []
        if not isinstance(items, list) or len(items) != len(b):
            raise CleanupSourceZHError(
                f"Invalid cleanup response cues length: got={len(items)} expected={len(b)}"
            )

        seen: set[int] = set()
        for cue, it in zip(b, items):
            if not isinstance(it, dict):
                raise CleanupSourceZHError("Invalid cue entry in model response")
            try:
                idx = int(it.get("index"))
            except Exception as e:
                raise CleanupSourceZHError("Missing or invalid index in model response") from e
            if idx != int(cue.index):
                raise CleanupSourceZHError(
                    f"Index mismatch: block expects {cue.index} model returned {idx}"
                )
            if idx in seen:
                raise CleanupSourceZHError(f"Duplicate index in response: {idx}")
            seen.add(idx)

            raw_t = (cue.text or "").strip()
            cleaned = str(it.get("cleaned_text") or "").strip()
            if not cleaned:
                cleaned = raw_t
            lc = bool(it.get("low_confidence", False))
            sus = bool(it.get("suspicious_asr", False))
            hr = bool(it.get("heavy_rewrite", False))
            numf = bool(it.get("likely_numeric_fix", False))

            if cleaned != raw_t and not _has_chinese(cleaned) and _has_chinese(raw_t):
                cleaned = raw_t
                lc = True

            changed = cleaned != raw_t
            results.append(
                CleanupCueResult(
                    index=idx,
                    raw_text=cue.text,
                    cleaned_text=cleaned,
                    changed=changed,
                    low_confidence=lc,
                    suspicious_asr=sus,
                    heavy_rewrite=hr,
                    likely_numeric_fix=numf,
                )
            )

        meta_blocks.append({"range": [int(first.index), int(last.index)], "cue_count": len(b)})

    finished = time.time()
    meta = {
        "backend": "cleanup_source_zh",
        "model": model,
        "block_size": int(block_size),
        "context_cues": int(context_cues),
        "block_count": len(meta_blocks),
        "blocks": meta_blocks,
        "started_at_unix": started,
        "finished_at_unix": finished,
        "elapsed_sec": float(max(0.0, finished - started)),
    }
    return results, meta
