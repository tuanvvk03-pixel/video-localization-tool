from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from engine.srt_cues import SRTCue
from engine.subtitle_text import write_subtitle_file_utf8


class BlockTranslateError(RuntimeError):
    pass


@dataclass(frozen=True)
class TranslationCueResult:
    index: int
    display: str
    voice: str
    confidence: float | None
    notes: str | None


@dataclass(frozen=True)
class TranslationQAItem:
    index: int
    flags: list[str]
    needs_review: bool
    score: float
    details: dict


def _load_glossary(path: Path) -> dict:
    if not path.is_file():
        return {"version": 0, "missing": True}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 0, "invalid": True}


def _chunk_cues(cues: list[SRTCue], *, block_size: int) -> list[list[SRTCue]]:
    n = len(cues)
    if n == 0:
        return []
    bs = max(1, int(block_size))
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


def render_srt(cues: list[SRTCue], text_by_index: dict[int, str]) -> str:
    lines: list[str] = []
    seq = 1
    for c in cues:
        t = (text_by_index.get(int(c.index)) or "").strip()
        if not t:
            t = "…"
        lines.append(str(seq))
        lines.append(f"{_ms_to_ts(c.start_ms)} --> {_ms_to_ts(c.end_ms)}")
        lines.append(t)
        lines.append("")
        seq += 1
    return "\n".join(lines).rstrip() + "\n"


_ZH_RE = re.compile(r"[\u4e00-\u9fff]")


_VI_VOWELS_RE = re.compile(r"[aăâeêioôơuưyáàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]", re.I)
_WORD_RE = re.compile(r"\S+")
_ALLOWED_LATIN_TOKEN_RE = re.compile(
    r"^(Wi-?Fi|USB|TV|HD|SD|DVD|CD|PC|CPU|GPU|API|URL|HTML|HTTP|HTTPS|JSON|"
    r"OpenAI|GPT|MP3|MP4|MV|DJ|MC|OK|VIP|CEO|KOL|AI|ID|IP|IT|UK|USA)$",
    re.I,
)


def _norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _has_vietnamese_diacritics(s: str) -> bool:
    return bool(_VI_VOWELS_RE.search(s or ""))


def _qa_score(source: str, display: str, voice: str) -> tuple[float, list[str], dict]:
    flags: list[str] = []
    d: dict = {}

    src = _norm_space(source)
    disp = _norm_space(display)
    voi = _norm_space(voice)

    if not disp or not voi:
        flags.append("low_confidence")
        d["empty_text"] = True

    if _ZH_RE.search(disp) or _ZH_RE.search(voi):
        flags.append("low_confidence")
        d["contains_chinese_chars"] = True

    # TTS comfort: short, clean, easy to read aloud.
    voice_word_count = len(_WORD_RE.findall(voi))
    if voice_word_count >= 20 or len(voi) >= 110:
        flags.append("hard_for_tts")
        d["voice_word_count"] = voice_word_count
        d["voice_len"] = len(voi)

    if sum(1 for ch in voi if ch in "()[]{}<>/\\_|") >= 2:
        flags.append("hard_for_tts")
        d["contains_hard_symbols"] = True

    if voi.count("...") >= 2 or voi.count("…") >= 3:
        flags.append("hard_for_tts")
        d["too_many_ellipses"] = True

    if len(disp) >= 140:
        flags.append("unnatural_vietnamese")
        d["display_len"] = len(disp)

    # Voice style: avoid stiff / abstract / romance-novel phrasing.
    voi_l = voi.lower()
    awkward_phrases = (
        "bất ngờ thôi thúc",
        "khiến mình thèm muốn vô cùng",
        "khiến tôi thèm muốn vô cùng",
        "làm sao để tự chế",
        "tự chế một thứ như vậy",
        "trong lòng họ",
        "coi tôi như một người nguy hiểm",
        "vô cùng",
        "quá đỗi",
        "chẳng lẽ",
        "ắt hẳn",
    )
    if any(p in voi_l for p in awkward_phrases):
        flags.append("awkward_spoken_style")
        d["awkward_phrases_hit"] = True

    # Unnatural Vietnamese: very long, too formal, or lacks Vietnamese diacritics (common in broken outputs).
    if len(voi) >= 120 or (len(voi) >= 55 and not _has_vietnamese_diacritics(voi)):
        flags.append("unnatural_vietnamese")
        d["voice_len"] = len(voi)
        d["voice_has_diacritics"] = _has_vietnamese_diacritics(voi)

    # Literalness: suspicious calques / direct-translation artifacts.
    literal_markers = (
        "một cách",
        "đột nhiên",
        "bỗng nhiên",
        "vì thế",
        "do đó",
        "khiến cho",
        "đối với tôi",
        "đối với hắn",
        "đối với cô ấy",
        "trong lòng",
        "trong tim",
        "tựa như",
        "giống như",
    )
    if any(m in voi_l for m in literal_markers):
        flags.append("too_literal")
        d["literal_markers_hit"] = True

    # Compare with source: if voice keeps many Chinese punctuation/structure cues, treat as literal risk.
    if src and (src.count("，") + src.count("。") + src.count("？") + src.count("！")) >= 2 and ("too_literal" not in flags):
        if any(x in voi for x in ("，", "。", "？", "！")):
            flags.append("too_literal")
            d["chinese_punct_echo"] = True

    # Missing subject/predicate (very heuristic): voice is a fragment or starts with a dependent clause/verb only.
    if voi and len(voi) <= 16:
        fragment_starts = ("để ", "khi ", "vì ", "nên ", "nếu ", "làm ", "khiến ", "bị ", "được ")
        if voi_l.startswith(fragment_starts) and not any(voi_l.startswith(p) for p in ("được rồi", "để xem", "để tôi", "để tao", "để tớ")):
            flags.append("missing_subject_or_predicate")
            d["fragment_start"] = True

    # Awkward spoken style: too bookish address/structure for voice-over.
    if any(x in voi_l for x in ("ngươi", "bổn", "bản tọa", "các hạ")):
        flags.append("awkward_spoken_style")
        d["bookish_pronouns"] = True

    # Generic nonsense/abstract: lots of vague words, little concrete meaning.
    vague_hits = sum(1 for x in ("ý niệm", "khát vọng", "thúc đẩy", "cảm giác", "tâm trạng", "linh hồn") if x in voi_l)
    if vague_hits >= 2:
        flags.append("unnatural_vietnamese")
        d["vague_word_hits"] = vague_hits

    # Suspicious English / Latin tokens (often bad transliteration or hallucinated names).
    latin_tokens = re.findall(r"\b[A-Za-z]{3,}\b", voi)
    latin_sus = [t for t in latin_tokens if not _ALLOWED_LATIN_TOKEN_RE.match(t)]
    if len(latin_sus) >= 2 or (len(latin_sus) == 1 and len(latin_sus[0]) >= 10):
        flags.append("weird_named_entity")
        d["latin_tokens"] = latin_sus[:6]

    nonsense_markers = (
        "là một điều",
        "mang tính",
        "ở một mức độ",
        "theo một nghĩa nào đó",
        "như thể nào đó",
        "một thứ gì đó",
        "cái gì đó mà",
        "không thể nào mà",
    )
    if any(p in voi_l for p in nonsense_markers):
        flags.append("nonsense_phrase")
        d["nonsense_marker_hit"] = True

    # Scoring: start below 1.0 so it's not "almost always perfect".
    score = 0.88
    if "low_confidence" in flags:
        score -= 0.45
    if "hard_for_tts" in flags:
        score -= 0.25
    if "unnatural_vietnamese" in flags:
        score -= 0.22
    if "too_literal" in flags:
        score -= 0.18
    if "awkward_spoken_style" in flags:
        score -= 0.18
    if "missing_subject_or_predicate" in flags:
        score -= 0.15
    if "weird_named_entity" in flags:
        score -= 0.14
    if "nonsense_phrase" in flags:
        score -= 0.12

    # Minor nudges so score spreads even when no big flags.
    if voi and len(voi) <= 6:
        score -= 0.06
        d["very_short_voice"] = True
    if voice_word_count >= 16:
        score -= 0.06
        d["dense_voice"] = True

    score = min(score, 0.98)
    score = max(0.0, min(1.0, score))
    return score, flags, d


def _build_system_prompt(*, glossary: dict) -> str:
    g = json.dumps(glossary, ensure_ascii=False, indent=2)
    return (
        "You are a professional Chinese→Vietnamese subtitle translator for voice-over dubbing.\n"
        "Hard requirements:\n"
        "- Do NOT translate line-by-line literally; produce natural Vietnamese.\n"
        "- Keep meaning correct (actions, relationships, intent).\n"
        "- Keep character names and address terms consistent across cues.\n"
        "- Output TWO variants per cue:\n"
        "  - display: good for on-screen subtitle.\n"
        "  - voice: rewritten for TTS voice-over in everyday Vietnamese: natural, short, easy to read aloud.\n"
        "- Do not add new content. Do not drop meaning.\n"
        "- Avoid nonsense Vietnamese.\n"
        "- For voice: prefer conversational storytelling tone; avoid stiff/abstract/bookish phrasing.\n"
        "- For voice: do NOT cling to Chinese structure; rewrite freely while preserving meaning.\n"
        "- For voice: avoid phrases like: 'bất ngờ thôi thúc', 'khiến mình thèm muốn vô cùng', 'làm sao để tự chế một thứ như vậy'.\n"
        "- For voice: do not invent random English names or gibberish tokens; keep proper nouns consistent with glossary/source.\n"
        "- Respect glossary constraints.\n\n"
        f"Glossary JSON:\n{g}\n"
    )


def _build_voice_rewrite_system_prompt(*, glossary: dict) -> str:
    g = json.dumps(glossary, ensure_ascii=False, indent=2)
    return (
        "You are a Vietnamese dialogue writer rewriting subtitle lines for TTS voice-over.\n"
        "Goal: make the Vietnamese sound natural and spoken, like everyday narration/dialogue.\n"
        "Hard requirements:\n"
        "- Only rewrite the 'voice' variant. Keep meaning consistent with the original Chinese + display Vietnamese.\n"
        "- Be concise. Prefer short sentences. Remove stiffness and literal calques.\n"
        "- Prefer everyday Vietnamese (đời thường). Avoid abstract/romance-novel/bookish language.\n"
        "- Avoid nonsense, vague lines, or empty-sounding sentences.\n"
        "- Avoid phrases like: 'bất ngờ thôi thúc', 'khiến mình thèm muốn vô cùng', 'làm sao để tự chế một thứ như vậy'.\n"
        "- Remove empty filler ('mang tính', 'ở một mức độ', vague double-talk) and weird English gibberish.\n"
        "- Make it easy for TTS: avoid weird symbols, nested parentheses, excessive ellipses.\n"
        "- Do not add new facts. Do not change who does what to whom.\n"
        "- Respect glossary constraints.\n"
        "- Output STRICT JSON only.\n\n"
        f"Glossary JSON:\n{g}\n"
    )


def _build_voice_rewrite_user_prompt(
    *,
    cue: SRTCue,
    display: str,
    voice: str,
    context_before: list[SRTCue],
    context_after: list[SRTCue],
    reason_flags: list[str],
) -> str:
    def pack(c: SRTCue) -> dict:
        return {
            "index": int(c.index),
            "ts": f"{_ms_to_ts(c.start_ms)} --> {_ms_to_ts(c.end_ms)}",
            "text": c.text,
        }

    payload = {
        "task": "Rewrite a single cue 'voice' line for TTS Vietnamese.",
        "cue": pack(cue),
        "display_vietnamese": display,
        "current_voice_vietnamese": voice,
        "rewrite_reasons": reason_flags,
        "context_before": [pack(c) for c in context_before],
        "context_after": [pack(c) for c in context_after],
        "output_schema": {
            "type": "object",
            "required": ["index", "voice"],
            "example": {"index": int(cue.index), "voice": "Rewrite here", "notes": "optional"},
        },
        "rules": [
            "Return STRICT JSON only (no markdown).",
            "Keep index unchanged.",
            "Return a single best rewrite (no alternatives).",
            "Keep it short and spoken; don't be literal.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _build_user_prompt(
    *,
    block: list[SRTCue],
    context_before: list[SRTCue],
    context_after: list[SRTCue],
) -> str:
    def pack(c: SRTCue) -> dict:
        return {
            "index": int(c.index),
            "ts": f"{_ms_to_ts(c.start_ms)} --> {_ms_to_ts(c.end_ms)}",
            "text": c.text,
        }

    payload = {
        "task": "Translate a block of subtitle cues with context; return per-cue mapping by index.",
        "context_before": [pack(c) for c in context_before],
        "block": [pack(c) for c in block],
        "context_after": [pack(c) for c in context_after],
        "output_schema": {
            "type": "object",
            "required": ["cues"],
            "cues": [
                {
                    "index": 123,
                    "display": "Vietnamese for subtitle display",
                    "voice": "Vietnamese rewritten for TTS speech",
                    "confidence": 0.0,
                    "notes": "optional",
                }
            ],
        },
        "rules": [
            "Return STRICT JSON only (no markdown).",
            "Return one entry per cue in 'block'.",
            "Do not change indices.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _build_translation_system_prompt_v2(*, glossary: dict) -> str:
    g = json.dumps(glossary, ensure_ascii=False, indent=2)
    return (
        "You are the lead subtitle adapter for Chinese-to-Vietnamese localization.\n"
        "Your output should read like a strong human-edited Vietnamese subtitle script, not a literal machine translation.\n"
        "Priority order:\n"
        "1. Recover the intended meaning from noisy ASR using nearby cues.\n"
        "2. Preserve scene logic, humor, insults, relationships, and speaker attitude.\n"
        "3. Write idiomatic spoken Vietnamese.\n"
        "4. Keep names and address terms consistent across cues.\n"
        "5. Keep each cue compact enough for subtitles and TTS.\n"
        "Hard requirements:\n"
        "- Source may contain ASR mistakes, homophones, broken names, or garbled references. If the intended meaning is reasonably clear from context, repair it silently instead of translating the error literally.\n"
        "- Do NOT translate word-by-word or keep Chinese sentence structure.\n"
        "- Output TWO variants per cue:\n"
        "  - display: natural subtitle Vietnamese, concise and readable.\n"
        "  - voice: same meaning, optimized for TTS; even more conversational and easy to say aloud.\n"
        "- If display already sounds natural, voice may stay close. Do not force artificial differences.\n"
        "- For jokes, banter, teasing, and insults, keep the comedic force rather than the exact wording.\n"
        "- Prefer bold, idiomatic, punchy Vietnamese over bland safe wording when both preserve the same meaning.\n"
        "- If the source sounds like a roast, comeback, complaint, or emotional outburst, make it land naturally in Vietnamese.\n"
        "- If a reference/name is obviously damaged by ASR and cannot be safely restored, replace the broken literal wording with a natural paraphrase instead of preserving nonsense.\n"
        "- Avoid stiff, bookish, or abstract Vietnamese.\n"
        "- Avoid fabricated names, transliterated garbage, and random English tokens.\n"
        "- Do not add facts that are unsupported by source/context.\n"
        "- If uncertain, choose the most plausible natural line, not a broken literal line.\n"
        "- Respect glossary constraints.\n\n"
        f"Glossary JSON:\n{g}\n"
    )


def _build_translation_user_prompt_v2(
    *,
    block: list[SRTCue],
    context_before: list[SRTCue],
    context_after: list[SRTCue],
) -> str:
    def pack(c: SRTCue) -> dict:
        return {
            "index": int(c.index),
            "ts": f"{_ms_to_ts(c.start_ms)} --> {_ms_to_ts(c.end_ms)}",
            "text": c.text,
        }

    payload = {
        "task": "Translate one continuous subtitle block with context; treat the block like a short scene, not isolated lines.",
        "context_before": [pack(c) for c in context_before],
        "block": [pack(c) for c in block],
        "context_after": [pack(c) for c in context_after],
        "output_schema": {
            "type": "object",
            "required": ["cues"],
            "cues": [
                {
                    "index": 123,
                    "display": "Vietnamese for subtitle display",
                    "voice": "Vietnamese rewritten for TTS speech",
                    "confidence": 0.0,
                    "notes": "optional",
                }
            ],
        },
        "rules": [
            "Return STRICT JSON only (no markdown).",
            "Return one entry per cue in 'block'.",
            "Do not change indices.",
            "Prefer natural Vietnamese that preserves the scene's intent over literal Chinese phrasing.",
            "Aim for the quality bar of a polished human subtitle editor, not a cautious machine draft.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _build_block_polish_system_prompt(*, glossary: dict) -> str:
    g = json.dumps(glossary, ensure_ascii=False, indent=2)
    return (
        "You are a Vietnamese subtitle editor doing a second-pass polish on a translated scene.\n"
        "You will receive source cues plus draft Vietnamese lines.\n"
        "Your job is to aggressively upgrade the draft to fluent, native, context-aware Vietnamese.\n"
        "Hard requirements:\n"
        "- Improve both display and voice for every cue in the block.\n"
        "- Fix literal wording, broken named entities, and ASR-induced mistranslations when context makes the intended meaning clear.\n"
        "- Keep cue-to-cue continuity: setup/payoff, sarcasm, teasing, and callbacks must still work across the block.\n"
        "- Prefer what a skilled Vietnamese subtitle editor would actually write, even if that means rewriting the sentence structure strongly.\n"
        "- You may rewrite aggressively for naturalness, rhythm, punch, and emotional force as long as the scene meaning stays intact.\n"
        "- Upgrade bland, flat, or overly safe lines into livelier Vietnamese when the draft undershoots the scene tone.\n"
        "- For banter, jokes, mockery, and heated dialogue, prioritize a line that lands naturally in Vietnamese over literal lexical matching.\n"
        "- Keep display concise for reading on screen.\n"
        "- Keep voice easy for TTS: spoken, compact, and smooth.\n"
        "- Avoid translationese, explanatory phrasing, and dead-sounding filler.\n"
        "- If a draft line contains garbage proper nouns caused by ASR, replace them with a sensible paraphrase unless the name can be restored confidently.\n"
        "- Do not add unsupported facts or over-explain.\n"
        "- Keep names/address terms consistent with the glossary and surrounding cues.\n"
        "- Output STRICT JSON only.\n\n"
        f"Glossary JSON:\n{g}\n"
    )


def _build_block_polish_user_prompt(
    *,
    block: list[SRTCue],
    context_before: list[SRTCue],
    context_after: list[SRTCue],
    draft_items: list[dict],
) -> str:
    def pack(c: SRTCue) -> dict:
        return {
            "index": int(c.index),
            "ts": f"{_ms_to_ts(c.start_ms)} --> {_ms_to_ts(c.end_ms)}",
            "text": c.text,
        }

    draft_by_index: dict[int, dict[str, object]] = {}
    for item in draft_items:
        try:
            idx = int(item.get("index"))
        except Exception:
            continue
        draft_by_index[idx] = {
            "display": str(item.get("display") or "").strip(),
            "voice": str(item.get("voice") or "").strip(),
            "confidence": item.get("confidence"),
            "notes": str(item.get("notes") or "").strip(),
        }

    payload = {
        "task": "Polish the Vietnamese subtitle draft for the whole block and return final per-cue lines.",
        "context_before": [pack(c) for c in context_before],
        "block": [
            {
                **pack(c),
                "draft_display": (draft_by_index.get(int(c.index)) or {}).get("display", ""),
                "draft_voice": (draft_by_index.get(int(c.index)) or {}).get("voice", ""),
            }
            for c in block
        ],
        "context_after": [pack(c) for c in context_after],
        "output_schema": {
            "type": "object",
            "required": ["cues"],
            "cues": [
                {
                    "index": 123,
                    "display": "Polished subtitle Vietnamese",
                    "voice": "Polished TTS Vietnamese",
                    "confidence": 0.0,
                    "notes": "optional",
                }
            ],
        },
        "rules": [
            "Return STRICT JSON only (no markdown).",
            "Return one entry per cue in 'block'.",
            "Do not change indices.",
            "Preserve scene coherence across neighboring cues.",
            "Do not stay close to the draft if the draft sounds literal, weak, or awkward.",
            "Choose the strongest natural Vietnamese line that still matches the source scene.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _call_openai_chat_json(*, api_key: str, model: str, system: str, user: str) -> dict:
    # Managed mode: route the call through the platform backend (server holds the
    # OpenAI key + meters tokens). Falls back to the local BYOK path below if the
    # cloud client isn't available or the user isn't signed in.
    try:
        from desktop.cloud_account import account, managed_enabled  # type: ignore

        if managed_enabled():
            text, _usage = account().translate(
                system, user, model_spec=(f"openai:{model}" if model else "")
            )
            try:
                return json.loads(text)
            except Exception as e:  # noqa: BLE001
                raise BlockTranslateError(
                    f"Managed translate did not return valid JSON. head={text[:400]!r}"
                ) from e
    except ImportError:
        pass  # desktop client not on path (pure-engine/CLI use) → BYOK below

    # Lazy import so engine can still run without openai installed unless this path is used.
    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:  # pragma: no cover
        raise BlockTranslateError(
            "Missing dependency 'openai'. Install engine/requirements.txt (or use the repo .venv) to enable block_v2."
        ) from e

    client = OpenAI(api_key=api_key)
    # Use Responses API (official SDK). Provide plain text input; do not JSON-encode request bodies.
    resp = client.responses.create(
        model=model,
        instructions=system,
        input=user,
    )
    # SDK convenience: aggregated text across output items.
    text = (getattr(resp, "output_text", None) or "").strip()
    if not text:
        # Fallback extraction for older SDK shapes
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
        raise BlockTranslateError(f"Model did not return valid JSON. head={text[:400]!r}") from e


def translate_blocks_two_pass(
    *,
    cues: list[SRTCue],
    api_key: str,
    model: str,
    glossary_path: Path,
    block_size: int,
    context_cues: int,
    qa_enabled: bool,
) -> tuple[dict[int, TranslationCueResult], list[TranslationQAItem], dict]:
    glossary = _load_glossary(glossary_path)
    system = _build_translation_system_prompt_v2(glossary=glossary)
    polish_system = _build_block_polish_system_prompt(glossary=glossary)
    rewrite_system = _build_voice_rewrite_system_prompt(glossary=glossary)
    blocks = _chunk_cues(cues, block_size=block_size)

    by_index: dict[int, TranslationCueResult] = {}
    qa: list[TranslationQAItem] = []
    meta_blocks: list[dict] = []

    n = len(cues)
    idx_to_pos = {int(c.index): i for i, c in enumerate(cues)}
    idx_to_cue = {int(c.index): c for c in cues}

    started = time.time()
    total_blocks = len(blocks)
    for bi, b in enumerate(blocks, start=1):
        first = b[0]
        last = b[-1]
        b_start = idx_to_pos.get(int(first.index), 0)
        b_end = idx_to_pos.get(int(last.index), b_start) + 1
        cb = cues[max(0, b_start - int(context_cues)) : b_start]
        ca = cues[b_end : min(n, b_end + int(context_cues))]

        elapsed = time.time() - started
        print(
            f"[block_translate] block {bi}/{total_blocks} "
            f"cue_index {int(first.index)}..{int(last.index)} (n={len(b)}) "
            f"elapsed={elapsed:.1f}s",
            file=sys.stderr,
            flush=True,
        )

        user = _build_translation_user_prompt_v2(block=b, context_before=cb, context_after=ca)
        out = _call_openai_chat_json(api_key=api_key, model=model, system=system, user=user)

        items = out.get("cues") or []
        if not isinstance(items, list) or len(items) != len(b):
            raise BlockTranslateError(
                f"Invalid model response cues length: got={len(items)} expected={len(b)}"
            )

        polish_applied = False
        try:
            polish_user = _build_block_polish_user_prompt(
                block=b,
                context_before=cb,
                context_after=ca,
                draft_items=items,
            )
            polish_out = _call_openai_chat_json(
                api_key=api_key,
                model=model,
                system=polish_system,
                user=polish_user,
            )
            polish_items = polish_out.get("cues") or []
            if isinstance(polish_items, list) and len(polish_items) == len(b):
                items = polish_items
                polish_applied = True
        except BlockTranslateError:
            polish_applied = False

        block_meta = {
            "range": [int(first.index), int(last.index)],
            "cue_count": len(b),
            "polish_applied": bool(polish_applied),
        }
        meta_blocks.append(block_meta)

        draft_by_index: dict[int, dict[str, object]] = {}
        for draft in out.get("cues") or []:
            try:
                draft_idx = int(draft.get("index"))
            except Exception:
                continue
            draft_by_index[draft_idx] = {
                "display": str(draft.get("display") or "").strip(),
                "voice": str(draft.get("voice") or "").strip(),
                "confidence": draft.get("confidence"),
                "notes": str(draft.get("notes") or "").strip() or None,
            }

        seen: set[int] = set()
        for it in items:
            try:
                idx = int(it.get("index"))
            except Exception:
                continue
            if idx in seen:
                continue
            seen.add(idx)
            fallback = draft_by_index.get(idx) or {}
            display = str(it.get("display") or fallback.get("display") or "").strip()
            voice = str(it.get("voice") or fallback.get("voice") or display).strip()
            conf = it.get("confidence", None)
            try:
                if conf is None and fallback.get("confidence") is not None:
                    conf = fallback.get("confidence")
                conf_f = float(conf) if conf is not None else None
            except Exception:
                conf_f = None
            notes = str(it.get("notes") or fallback.get("notes") or "").strip() or None
            by_index[idx] = TranslationCueResult(
                index=idx, display=display, voice=voice, confidence=conf_f, notes=notes
            )

            if qa_enabled:
                src = (idx_to_cue.get(idx).text if idx_to_cue.get(idx) else "") or ""
                score, flags, details = _qa_score(src, display, voice)
                needs_review = (score < 0.68) or ("low_confidence" in flags)

                # If QA manifest is enabled, try one extra rewrite pass for cues that look bad.
                # Limit rewrite attempts to avoid infinite loops / runaway costs.
                if needs_review:
                    max_rewrite_passes = 2
                    for _pass in range(max_rewrite_passes):
                        cue_obj = idx_to_cue.get(idx)
                        if cue_obj is None:
                            break

                        pos = idx_to_pos.get(idx, 0)
                        cb2 = cues[max(0, pos - int(context_cues)) : pos]
                        ca2 = cues[pos + 1 : min(n, pos + 1 + int(context_cues))]
                        user_rewrite = _build_voice_rewrite_user_prompt(
                            cue=cue_obj,
                            display=display,
                            voice=voice,
                            context_before=cb2,
                            context_after=ca2,
                            reason_flags=flags,
                        )
                        out2 = _call_openai_chat_json(
                            api_key=api_key, model=model, system=rewrite_system, user=user_rewrite
                        )
                        new_voice = str(out2.get("voice") or "").strip()
                        if new_voice:
                            voice = new_voice
                            by_index[idx] = TranslationCueResult(
                                index=idx,
                                display=display,
                                voice=voice,
                                confidence=conf_f,
                                notes=notes,
                            )

                        score, flags, details = _qa_score(src, display, voice)
                        needs_review = (score < 0.68) or ("low_confidence" in flags)
                        if not needs_review:
                            break

                qa.append(
                    TranslationQAItem(
                        index=idx,
                        flags=flags,
                        needs_review=bool(needs_review),
                        score=float(score),
                        details=details,
                    )
                )

    finished = time.time()
    print(
        f"[block_translate] done cues={n} blocks={total_blocks} "
        f"elapsed={finished - started:.1f}s",
        file=sys.stderr,
        flush=True,
    )
    meta = {
        "backend": "block_v2",
        "model": model,
        "block_size": int(block_size),
        "context_cues": int(context_cues),
        "block_count": len(meta_blocks),
        "blocks": meta_blocks,
        "glossary_path": str(glossary_path).replace("\\", "/"),
        "started_at_unix": started,
        "finished_at_unix": finished,
        "elapsed_sec": float(max(0.0, finished - started)),
    }
    return by_index, qa, meta


def write_translation_outputs(
    *,
    out_display_srt: Path,
    out_voice_srt: Path,
    cues: list[SRTCue],
    results: dict[int, TranslationCueResult],
) -> None:
    display_map = {idx: res.display for idx, res in results.items()}
    voice_map = {idx: res.voice for idx, res in results.items()}
    write_subtitle_file_utf8(out_display_srt, render_srt(cues, display_map))
    write_subtitle_file_utf8(out_voice_srt, render_srt(cues, voice_map))

