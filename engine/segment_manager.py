"""Segment planning + SRT merging for long videos (Phase 4).

Two halves:
1. Pure functions (no external deps) that can be unit-tested without ffmpeg:
     - plan_segments(duration_s)  -> list[SegmentPlan]
     - shift_cues(cues, offset_ms)
     - merge_srts_with_offsets(srt_texts, offsets_ms) -> str

2. ffmpeg wrappers (require ffmpeg/ffprobe on PATH or FFMPEG_BIN/FFPROBE_BIN):
     - probe_video_duration(mp4) -> float
     - split_video(src, plan, out_paths) -> None
     - concat_videos(parts, output) -> None

Segment workspace layout under <parent_workspace>/segments/:
    seg_000/input/source.mp4
    seg_001/input/source.mp4
    ...
    manifest.json          (SegmentManifest)

Each seg_XXX directory is a fully-functional video_workspace — the normal
Phase 1–3 stages (run_job, voice_edit_cli, desktop UI) work on it unchanged.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from engine.ffmpeg_bins import resolve_ffmpeg_executable, resolve_ffprobe_executable
from engine.srt_cues import SRTCue, cues_to_srt, parse_srt_cues
from engine.subtitle_text import read_subtitle_file

SEGMENT_TARGET_S = 4 * 60
SEGMENT_MAX_S = 5 * 60
SEGMENT_MIN_PREFERRED_S = 3 * 60
SINGLE_VIDEO_THRESHOLD_S = 5 * 60


class SegmentError(RuntimeError):
    pass


@dataclass(frozen=True)
class SegmentPlan:
    index: int
    start_s: float
    end_s: float

    @property
    def duration_s(self) -> float:
        return max(0.0, self.end_s - self.start_s)


@dataclass(frozen=True)
class SegmentManifest:
    source_video: str
    source_duration_s: float
    segments: list[dict]
    version: int = 1


def plan_segments(
    duration_s: float,
    *,
    target_s: float = SEGMENT_TARGET_S,
    max_s: float = SEGMENT_MAX_S,
) -> list[SegmentPlan]:
    """
    Decide segment boundaries for a video of ``duration_s`` seconds.

    - Videos at/under SINGLE_VIDEO_THRESHOLD_S (5 min) yield a single segment.
    - Longer videos are split into N equal parts. N is chosen so chunk length <= max_s
      and is as close to target_s as possible.
    - Very short over-threshold videos (5 < d < ~6 min) may produce sub-3min chunks;
      we prefer splitting over silently keeping the 5-min limit violation.
    """
    if duration_s <= 0:
        raise SegmentError("duration_s must be positive")
    if duration_s <= SINGLE_VIDEO_THRESHOLD_S:
        return [SegmentPlan(index=0, start_s=0.0, end_s=float(duration_s))]

    n = max(2, round(duration_s / target_s))
    while duration_s / n > max_s:
        n += 1

    segs: list[SegmentPlan] = []
    step = duration_s / n
    for i in range(n):
        start = i * step
        end = duration_s if i == n - 1 else (i + 1) * step
        segs.append(SegmentPlan(index=i, start_s=start, end_s=end))
    return segs


def shift_cues(cues: list[SRTCue], offset_ms: int) -> list[SRTCue]:
    """Return cues with start/end shifted by ``offset_ms``; indices preserved."""
    out: list[SRTCue] = []
    for c in cues:
        out.append(
            SRTCue(
                index=c.index,
                start_ms=max(0, c.start_ms + offset_ms),
                end_ms=max(0, c.end_ms + offset_ms),
                text=c.text,
            )
        )
    return out


def merge_srts_with_offsets(srt_texts: list[str], offsets_ms: list[int]) -> str:
    """
    Merge per-segment SRT text using the given per-segment offsets.

    - Cues are reindexed sequentially starting at 1.
    - Cues are sorted by final start_ms to produce a coherent timeline.
    """
    if len(srt_texts) != len(offsets_ms):
        raise SegmentError("srt_texts and offsets_ms must have equal length")
    combined: list[SRTCue] = []
    for text, offset in zip(srt_texts, offsets_ms):
        cues = parse_srt_cues(text)
        combined.extend(shift_cues(cues, int(offset)))
    combined.sort(key=lambda c: (c.start_ms, c.end_ms))
    # Reindex after sort.
    reindexed = [
        SRTCue(index=i, start_ms=c.start_ms, end_ms=c.end_ms, text=c.text)
        for i, c in enumerate(combined, start=1)
    ]
    return cues_to_srt(reindexed)


def _require_ffmpeg() -> str:
    ff, err = resolve_ffmpeg_executable()
    if err or not ff:
        raise SegmentError(err or "ffmpeg not available")
    return ff


def _require_ffprobe() -> str:
    fp = resolve_ffprobe_executable()
    if not fp:
        raise SegmentError(
            "ffprobe not found: set FFPROBE_BIN or install ffprobe on PATH."
        )
    return fp


def probe_video_duration(video_path: Path) -> float:
    """Return ``video_path`` duration in seconds via ffprobe."""
    fp = _require_ffprobe()
    proc = subprocess.run(
        [
            fp,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SegmentError(f"ffprobe failed: {proc.stderr.strip()}")
    try:
        return float(proc.stdout.strip())
    except ValueError as e:
        raise SegmentError(f"Could not parse ffprobe duration: {proc.stdout!r}") from e


def split_video(src: Path, plan: list[SegmentPlan], out_paths: list[Path]) -> None:
    """Extract ``plan`` segments from ``src`` into ``out_paths`` using ffmpeg -ss/-to re-encode."""
    if len(plan) != len(out_paths):
        raise SegmentError("plan and out_paths must have equal length")
    ff = _require_ffmpeg()
    for seg, dst in zip(plan, out_paths):
        dst.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [
                ff,
                "-y",
                "-ss",
                f"{seg.start_s:.3f}",
                "-to",
                f"{seg.end_s:.3f}",
                "-i",
                str(src),
                "-map",
                "0",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-c:a",
                "aac",
                str(dst),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise SegmentError(
                f"ffmpeg split failed for segment {seg.index}: {proc.stderr.strip()}"
            )


def concat_videos(parts: list[Path], output: Path) -> None:
    """Concatenate ``parts`` into ``output`` using the ffmpeg concat demuxer."""
    if not parts:
        raise SegmentError("no parts to concat")
    ff = _require_ffmpeg()
    output.parent.mkdir(parents=True, exist_ok=True)
    listfile = output.parent / f"{output.stem}.concat.txt"
    listfile.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in parts) + "\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            ff,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listfile),
            "-c",
            "copy",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    listfile.unlink(missing_ok=True)
    if proc.returncode != 0:
        raise SegmentError(f"ffmpeg concat failed: {proc.stderr.strip()}")


def init_segment_workspaces(
    parent_workspace: Path, source_video: Path, plan: list[SegmentPlan]
) -> list[Path]:
    """
    Create <parent>/segments/seg_NNN/input/source.mp4 for each plan entry and split the
    source video into each. Also writes segments/manifest.json. Requires ffmpeg.
    """
    parent_workspace = parent_workspace.expanduser().resolve()
    segments_root = parent_workspace / "segments"
    segments_root.mkdir(parents=True, exist_ok=True)
    out_paths: list[Path] = []
    seg_dirs: list[Path] = []
    for seg in plan:
        seg_dir = segments_root / f"seg_{seg.index:03d}"
        (seg_dir / "input").mkdir(parents=True, exist_ok=True)
        (seg_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        seg_dirs.append(seg_dir)
        out_paths.append(seg_dir / "input" / "source.mp4")

    split_video(source_video, plan, out_paths)

    duration = plan[-1].end_s if plan else 0.0
    manifest = SegmentManifest(
        source_video=str(source_video.resolve()),
        source_duration_s=float(duration),
        segments=[
            {
                "index": seg.index,
                "start_s": seg.start_s,
                "end_s": seg.end_s,
                "workspace": str(seg_dirs[i].resolve()),
                "video": str(out_paths[i].resolve()),
            }
            for i, seg in enumerate(plan)
        ],
    )
    (segments_root / "manifest.json").write_text(
        json.dumps(asdict(manifest), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return seg_dirs


def load_segment_manifest(parent_workspace: Path) -> SegmentManifest:
    path = parent_workspace / "segments" / "manifest.json"
    if not path.is_file():
        raise SegmentError(f"Missing segment manifest: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return SegmentManifest(
        source_video=str(raw["source_video"]),
        source_duration_s=float(raw["source_duration_s"]),
        segments=list(raw.get("segments") or []),
        version=int(raw.get("version") or 1),
    )


def merge_segment_final_subtitles(
    parent_workspace: Path, output: Path | None = None
) -> Path:
    """
    Merge each segment's artifacts/translate/final_subtitle.srt into one parent SRT.

    Timestamps are shifted by the segment's start_s (from manifest). Output defaults to
    <parent>/artifacts/translate/final_subtitle.srt.
    """
    parent_workspace = parent_workspace.expanduser().resolve()
    manifest = load_segment_manifest(parent_workspace)
    texts: list[str] = []
    offsets: list[int] = []
    for entry in manifest.segments:
        seg_ws = Path(entry["workspace"])
        srt = seg_ws / "artifacts" / "translate" / "final_subtitle.srt"
        if not srt.is_file():
            raise SegmentError(
                f"Segment {entry['index']} missing final_subtitle.srt (expected at {srt})."
            )
        texts.append(read_subtitle_file(srt).text)
        offsets.append(int(float(entry["start_s"]) * 1000))

    merged = merge_srts_with_offsets(texts, offsets)
    out = output or (parent_workspace / "artifacts" / "translate" / "final_subtitle.srt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(merged, encoding="utf-8")
    return out


def seed_segment_edited_voices(
    parent_workspace: Path, *, overwrite: bool = False
) -> list[Path]:
    """Seed artifacts/edit/edited_voice.srt in each segment workspace from its translated_voice.srt."""
    from engine.voice_edit_api import seed_edited_voice  # lazy to avoid cycles

    parent_workspace = parent_workspace.expanduser().resolve()
    manifest = load_segment_manifest(parent_workspace)
    out: list[Path] = []
    for entry in manifest.segments:
        seg_ws = Path(entry["workspace"])
        out.append(seed_edited_voice(seg_ws, overwrite=overwrite))
    return out


def merge_segment_edited_voices(
    parent_workspace: Path,
    *,
    output: Path | None = None,
    fallback_to_translated: bool = True,
) -> Path:
    """Merge each segment's edited_voice.srt (fallback translated_voice.srt) into one parent SRT.

    Timestamps are shifted by the segment's start_s (from manifest). Output defaults to
    <parent>/artifacts/edit/edited_voice.srt.
    """
    parent_workspace = parent_workspace.expanduser().resolve()
    manifest = load_segment_manifest(parent_workspace)
    texts: list[str] = []
    offsets: list[int] = []
    for entry in manifest.segments:
        seg_ws = Path(entry["workspace"])
        edited = seg_ws / "artifacts" / "edit" / "edited_voice.srt"
        translated = seg_ws / "artifacts" / "translate" / "translated_voice.srt"
        if edited.is_file():
            chosen = edited
        elif fallback_to_translated and translated.is_file():
            chosen = translated
        else:
            raise SegmentError(
                f"Segment {entry['index']} missing edited_voice.srt and translated_voice.srt."
            )
        texts.append(read_subtitle_file(chosen).text)
        offsets.append(int(float(entry["start_s"]) * 1000))

    merged = merge_srts_with_offsets(texts, offsets)
    out = output or (parent_workspace / "artifacts" / "edit" / "edited_voice.srt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(merged, encoding="utf-8")
    return out


def distribute_edited_voice_to_segments(
    parent_workspace: Path, *, parent_srt_text: str | None = None
) -> list[Path]:
    """Slice a parent-level edited_voice.srt back into per-segment edited_voice.srt files.

    Each cue is assigned to the segment whose [start_s, end_s) contains its start time.
    Per-segment timestamps are shifted so each file is 0-based relative to its own video;
    cues ending beyond seg.end_s are clamped to seg duration.
    """
    parent_workspace = parent_workspace.expanduser().resolve()
    manifest = load_segment_manifest(parent_workspace)
    if parent_srt_text is None:
        parent_edit = parent_workspace / "artifacts" / "edit" / "edited_voice.srt"
        if not parent_edit.is_file():
            raise SegmentError(f"Missing parent edited_voice.srt at {parent_edit}")
        parent_srt_text = parent_edit.read_text(encoding="utf-8")
    cues = parse_srt_cues(parent_srt_text)

    buckets: dict[int, list[SRTCue]] = {int(e["index"]): [] for e in manifest.segments}
    for cue in cues:
        start_s = cue.start_ms / 1000.0
        assigned: dict | None = None
        for entry in manifest.segments:
            if float(entry["start_s"]) <= start_s < float(entry["end_s"]):
                assigned = entry
                break
        if assigned is None:
            assigned = manifest.segments[-1]
        offset_ms = int(float(assigned["start_s"]) * 1000)
        end_limit_ms = int(float(assigned["end_s"]) * 1000)
        shifted_start = max(0, cue.start_ms - offset_ms)
        shifted_end = min(cue.end_ms, end_limit_ms) - offset_ms
        shifted_end = max(shifted_start, shifted_end)
        buckets[int(assigned["index"])].append(
            SRTCue(
                index=cue.index,
                start_ms=shifted_start,
                end_ms=shifted_end,
                text=cue.text,
            )
        )

    out_paths: list[Path] = []
    for entry in manifest.segments:
        seg_ws = Path(entry["workspace"])
        dst = seg_ws / "artifacts" / "edit" / "edited_voice.srt"
        dst.parent.mkdir(parents=True, exist_ok=True)
        seg_cues = sorted(
            buckets.get(int(entry["index"]), []), key=lambda c: (c.start_ms, c.end_ms)
        )
        reindexed = [
            SRTCue(index=i, start_ms=c.start_ms, end_ms=c.end_ms, text=c.text)
            for i, c in enumerate(seg_cues, start=1)
        ]
        dst.write_text(cues_to_srt(reindexed), encoding="utf-8")
        out_paths.append(dst)
    return out_paths


def merge_segment_renders(
    parent_workspace: Path,
    *,
    render_filename: str = "final.mp4",
    output: Path | None = None,
) -> Path:
    """
    Concat each segment's artifacts/render/<render_filename> into the parent workspace.

    Output defaults to <parent>/artifacts/render/<render_filename>.
    """
    parent_workspace = parent_workspace.expanduser().resolve()
    manifest = load_segment_manifest(parent_workspace)
    parts: list[Path] = []
    for entry in manifest.segments:
        seg_ws = Path(entry["workspace"])
        part = seg_ws / "artifacts" / "render" / render_filename
        if not part.is_file():
            raise SegmentError(
                f"Segment {entry['index']} missing render {render_filename} (expected at {part})."
            )
        parts.append(part)

    out = output or (parent_workspace / "artifacts" / "render" / render_filename)
    concat_videos(parts, out)
    return out
