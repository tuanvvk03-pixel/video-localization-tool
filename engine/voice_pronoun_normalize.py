"""
Normalize Vietnamese pronoun/register within dialogue blocks in translated_voice.srt.

Blocks are split by long gaps between subtitle cues (scene-ish boundaries).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from engine.srt_cues import SRTCue

# Gap between cues (end -> next start) >= this => new block (ms).
DEFAULT_BLOCK_GAP_MS = 2800

# Register keys: target system for replacements.
REGISTER_TE_TO = "te_to"  # tớ / cậu
REGISTER_TAO_MAY = "tao_may"
REGISTER_MINH_BAN = "minh_ban"  # mình / bạn
REGISTER_TOI_BAN = "toi_ban"  # tôi / bạn (neutral)

_WB = r"(?<!\w)"
_WA = r"(?!\w)"

# Count hits per register (order matters for tie-break: prefer less "rough" systems).
_REGISTER_PRIORITY = (REGISTER_TE_TO, REGISTER_MINH_BAN, REGISTER_TOI_BAN, REGISTER_TAO_MAY)

_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    REGISTER_TE_TO: [
        re.compile(_WB + r"tớ" + _WA, re.I),
        re.compile(_WB + r"cậu" + _WA, re.I),
    ],
    REGISTER_TAO_MAY: [
        re.compile(_WB + r"tao" + _WA, re.I),
        re.compile(_WB + r"mày" + _WA, re.I),
        re.compile(_WB + r"mi" + _WA, re.I),
    ],
    REGISTER_MINH_BAN: [
        re.compile(_WB + r"mình" + _WA, re.I),
        re.compile(_WB + r"bạn" + _WA, re.I),
    ],
    REGISTER_TOI_BAN: [
        re.compile(_WB + r"tôi" + _WA, re.I),
    ],
}

# Whole-word replacements toward a target register (lowercase keys; preserve case heuristically).
_REPL_TOWARD: dict[str, list[tuple[re.Pattern[str], str]]] = {}


def _build_repl_toward() -> dict[str, list[tuple[re.Pattern[str], str]]]:
    def pat(word: str) -> re.Pattern[str]:
        return re.compile(_WB + word + _WA, re.I)

    out: dict[str, list[tuple[re.Pattern[str], str]]] = {
        REGISTER_TE_TO: [
            (pat("tao"), "tớ"),
            (pat("mày"), "cậu"),
            (pat("mi"), "cậu"),
            (pat("mình"), "tớ"),
            (pat("bạn"), "cậu"),
            (pat("tôi"), "tớ"),
        ],
        REGISTER_TAO_MAY: [
            (pat("tớ"), "tao"),
            (pat("cậu"), "mày"),
            (pat("mình"), "tao"),
            (pat("bạn"), "mày"),
            (pat("tôi"), "tao"),
        ],
        REGISTER_MINH_BAN: [
            (pat("tớ"), "mình"),
            (pat("cậu"), "bạn"),
            (pat("tao"), "mình"),
            (pat("mày"), "bạn"),
            (pat("tôi"), "mình"),
        ],
        REGISTER_TOI_BAN: [
            (pat("tớ"), "tôi"),
            (pat("cậu"), "bạn"),
            (pat("tao"), "tôi"),
            (pat("mày"), "bạn"),
            (pat("mình"), "tôi"),
        ],
    }
    return out


_REPL_TOWARD = _build_repl_toward()


def _count_register_hits(text: str) -> dict[str, int]:
    counts: dict[str, int] = {k: 0 for k in _PATTERNS}
    for reg, pats in _PATTERNS.items():
        for p in pats:
            counts[reg] += len(p.findall(text))
    return counts


def _registers_present(counts: dict[str, int]) -> set[str]:
    return {k for k, v in counts.items() if v > 0}


def _choose_target_register(block_counts: dict[str, int]) -> tuple[str | None, bool]:
    """
    Returns (target_register, ambiguous_tie).
    """
    total = sum(block_counts.values())
    if total == 0:
        return None, False
    best = max(block_counts.values())
    candidates = [r for r, v in block_counts.items() if v == best and v > 0]
    if len(candidates) > 1:
        for r in _REGISTER_PRIORITY:
            if r in candidates:
                return r, True
    return candidates[0], False


def _apply_register(text: str, target: str) -> str:
    out = text
    for rx, rep in _REPL_TOWARD.get(target, []):

        def _sub(m: re.Match[str]) -> str:
            g = m.group(0)
            if g.isupper():
                return rep.upper()
            if g[:1].isupper():
                return rep[:1].upper() + rep[1:]
            return rep

        out = rx.sub(_sub, out)
    return out


@dataclass
class PronounBlockReport:
    cue_indices: list[int]
    registers_detected: list[str]
    register_counts: dict[str, int]
    chosen_register: str | None
    ambiguous_tie: bool
    mixed_before: bool
    rewritten: bool


@dataclass
class PronounNormalizeResult:
    text_by_index: dict[int, str]
    blocks: list[PronounBlockReport] = field(default_factory=list)
    cue_flags: dict[int, dict] = field(default_factory=dict)


def segment_blocks(cues: list[SRTCue], *, gap_ms: int) -> list[list[SRTCue]]:
    if not cues:
        return []
    blocks: list[list[SRTCue]] = []
    cur: list[SRTCue] = []
    prev_end: int | None = None
    for c in sorted(cues, key=lambda x: (x.start_ms, x.index)):
        if prev_end is not None and c.start_ms - prev_end >= gap_ms and cur:
            blocks.append(cur)
            cur = []
        cur.append(c)
        prev_end = c.end_ms
    if cur:
        blocks.append(cur)
    return blocks


def pronoun_blocks_to_json(blocks: list[PronounBlockReport]) -> list[dict]:
    return [
        {
            "cue_indices": b.cue_indices,
            "registers_detected": b.registers_detected,
            "register_counts": b.register_counts,
            "chosen_register": b.chosen_register,
            "ambiguous_tie": b.ambiguous_tie,
            "mixed_before": b.mixed_before,
            "rewritten": b.rewritten,
        }
        for b in blocks
    ]


def normalize_voice_pronouns_in_blocks(
    cues: list[SRTCue],
    voice_by_index: dict[int, str],
    *,
    gap_ms: int = DEFAULT_BLOCK_GAP_MS,
) -> PronounNormalizeResult:
    """
    Return updated voice lines and QA hints per cue index.
    """
    blocks = segment_blocks(cues, gap_ms=gap_ms)
    out_text = {int(c.index): (voice_by_index.get(int(c.index)) or "").strip() for c in cues}
    result = PronounNormalizeResult(text_by_index=dict(out_text))

    for blk in blocks:
        indices = [int(c.index) for c in blk]
        combined = " ".join((out_text.get(i) or "").strip() for i in indices)
        per_counts = _count_register_hits(combined)
        present = _registers_present(per_counts)
        mixed_before = len(present) > 1
        target, ambiguous = _choose_target_register(per_counts)
        rewritten = False

        if mixed_before and target is not None and not ambiguous:
            for i in indices:
                t0 = out_text.get(i) or ""
                t1 = _apply_register(t0, target)
                if t1 != t0:
                    rewritten = True
                out_text[i] = t1

        report = PronounBlockReport(
            cue_indices=indices,
            registers_detected=sorted(present),
            register_counts={k: v for k, v in per_counts.items() if v > 0},
            chosen_register=target,
            ambiguous_tie=ambiguous,
            mixed_before=mixed_before,
            rewritten=rewritten,
        )
        result.blocks.append(report)

        if mixed_before:
            for i in indices:
                flags = ["pronoun_inconsistency"]
                if ambiguous or target is None or not rewritten:
                    flags.append("register_shift")
                result.cue_flags[i] = {
                    "flags": flags,
                    "needs_review": True,
                    "pronoun_block_cue_indices": indices,
                    "pronoun_chosen_register": target,
                    "pronoun_normalized": bool(rewritten and target is not None and not ambiguous),
                }

    result.text_by_index = out_text
    return result


def merge_pronoun_qa_into_per_cue_qa(
    qa_list: list[dict],
    cue_flags: dict[int, dict],
) -> list[dict]:
    """Merge pronoun flags into existing translation_qa.json 'qa' entries (by index)."""
    by_idx: dict[int, dict] = {}
    for row in qa_list:
        try:
            idx = int(row.get("index"))
        except Exception:
            continue
        by_idx[idx] = dict(row)

    for idx, extra in cue_flags.items():
        row = by_idx.get(idx)
        if row is None:
            row = {
                "index": idx,
                "flags": [],
                "needs_review": False,
                "score": 0.85,
                "details": {},
            }
            by_idx[idx] = row
        flags = list(row.get("flags") or [])
        for f in extra.get("flags") or []:
            if f not in flags:
                flags.append(f)
        row["flags"] = flags
        row["needs_review"] = bool(row.get("needs_review")) or bool(extra.get("needs_review"))
        det = dict(row.get("details") or {})
        det["pronoun_block_cue_indices"] = extra.get("pronoun_block_cue_indices")
        det["pronoun_chosen_register"] = extra.get("pronoun_chosen_register")
        row["details"] = det
        if extra.get("needs_review"):
            try:
                sc = float(row.get("score") or 1.0)
            except Exception:
                sc = 1.0
            row["score"] = max(0.0, min(1.0, sc - 0.12))

    return sorted(by_idx.values(), key=lambda r: int(r.get("index", 0)))
