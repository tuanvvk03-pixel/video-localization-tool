"""
Subtitle text I/O helpers (UTF-8 first).

Pipeline note: source audio is often Chinese; subtitles are translated to Vietnamese;
TTS defaults to a Vietnamese neural voice (see run_tts_stage DEFAULT_TTS_VOICE).

Canonical workspace artifacts (translated_auto.srt, translated_manual.srt, edited.srt,
final_subtitle.srt) should be stored as UTF-8 (no BOM). Use write_subtitle_file_utf8 /
copy_subtitle_reencode_utf8 after any import or legacy pipeline output.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path
import shutil


@dataclass(frozen=True)
class SubtitleTextResult:
    """Result of reading a subtitle file for re-encoding."""

    text: str
    mojibake_repaired: bool
    """True if Latin-1 mojibake (UTF-8 misread) was detected and corrected."""
    fallback_encoding: str | None
    """If not None, bytes were not valid UTF-8 and this codec (or replace) was used."""


def read_subtitle_file(path: Path) -> SubtitleTextResult:
    """
    Read subtitle file: decode safely, optional mojibake repair, NFC-normalize.
    """
    raw = path.read_bytes()
    base, fallback = _decode_subtitle_bytes_primary(raw)
    repaired, did_repair = _repair_mojibake_utf8_as_latin1_with_flag(base)
    final = unicodedata.normalize("NFC", repaired)
    return SubtitleTextResult(
        text=final,
        mojibake_repaired=did_repair,
        fallback_encoding=fallback,
    )


def read_subtitle_file_unicode(path: Path) -> str:
    """Backward-compatible: return Unicode text only (same rules as read_subtitle_file)."""
    return read_subtitle_file(path).text


def write_subtitle_file_utf8(path: Path, text: str) -> None:
    """Write subtitle content as UTF-8 (no BOM), Unix newlines, NFC."""
    normalized = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(normalized.encode("utf-8"))


def copy_subtitle_reencode_utf8(src: Path, dst: Path) -> SubtitleTextResult:
    """Read src with safe decoding, write dst as canonical UTF-8."""
    result = read_subtitle_file(src)
    write_subtitle_file_utf8(dst, result.text)
    return result


def normalize_subtitle_file_utf8(path: Path, stage_tag: str) -> SubtitleTextResult | None:
    """Re-read path and rewrite as UTF-8 NFC in place; log repairs. Returns None if missing."""
    if not path.is_file():
        return None
    result = read_subtitle_file(path)
    write_subtitle_file_utf8(path, result.text)
    log_subtitle_read_issues(
        result,
        stage_tag=stage_tag,
        path_display=str(path.resolve()),
    )
    return result


def log_subtitle_read_issues(
    result: SubtitleTextResult,
    *,
    stage_tag: str,
    path_display: str,
) -> None:
    """Emit clear stderr lines when repair or fallback decoding was used."""
    import sys

    if result.mojibake_repaired:
        print(
            f"[{stage_tag}] Subtitle mojibake repaired (UTF-8 bytes misread as Latin-1): {path_display}",
            file=sys.stderr,
        )
    if result.fallback_encoding is not None:
        print(
            f"[{stage_tag}] Subtitle decoded with fallback encoding "
            f"{result.fallback_encoding!r} then normalized to UTF-8: {path_display}",
            file=sys.stderr,
        )


@dataclass(frozen=True)
class SubtitleCopyResult:
    """Result of copying a subtitle artifact into the workspace."""

    used_binary_copy: bool
    read: SubtitleTextResult | None


def copy_subtitle_artifact(
    src: Path,
    dst: Path,
    *,
    stage_tag: str,
) -> SubtitleCopyResult:
    """
    Copy subtitle artifact with minimal structure changes.

    - Prefer binary-safe copy (shutil.copy2) when src looks like valid UTF-8 and no repair is needed.
    - If mojibake repair or fallback decoding is needed, rewrite dst as canonical UTF-8 (no BOM) and log.
    """
    # First pass: inspect text issues without modifying dst.
    res = read_subtitle_file(src)
    needs_transform = bool(res.mojibake_repaired) or (res.fallback_encoding is not None)

    dst.parent.mkdir(parents=True, exist_ok=True)
    if not needs_transform:
        shutil.copy2(src, dst)
        return SubtitleCopyResult(used_binary_copy=True, read=None)

    write_subtitle_file_utf8(dst, res.text)
    log_subtitle_read_issues(res, stage_tag=stage_tag, path_display=str(dst.resolve()))
    return SubtitleCopyResult(used_binary_copy=False, read=res)


def _decode_subtitle_bytes_primary(raw: bytes) -> tuple[str, str | None]:
    """
    Decode bytes without Latin-1 mojibake repair.
    Returns (text, fallback_label or None if plain UTF-8).
    """
    if not raw:
        return "", None

    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), None

    try:
        return raw.decode("utf-8"), None
    except UnicodeDecodeError:
        pass

    for enc in ("cp1258", "cp1252"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue

    return raw.decode("utf-8", errors="replace"), "utf-8-replace"


def _repair_mojibake_utf8_as_latin1_with_flag(s: str) -> tuple[str, bool]:
    """
    If UTF-8 was misinterpreted as Latin-1, recover intended Unicode.
    Returns (text, True) if repair changed content.
    """
    if len(s) < 2:
        return s, False
    if not any(ch in s for ch in ("Ã", "Ä", "Â", "Å")):
        return s, False
    try:
        repaired = s.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return s, False
    if not repaired or repaired == s or len(repaired) > len(s) * 3:
        return s, False
    return repaired, True


def _decode_subtitle_bytes(raw: bytes) -> str:
    """Decode + repair (legacy helper); prefer read_subtitle_file."""
    base, _ = _decode_subtitle_bytes_primary(raw)
    t, _ = _repair_mojibake_utf8_as_latin1_with_flag(base)
    return t
