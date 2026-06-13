"""Merge segment outputs into parent workspace (Phase 4).

Two sub-operations (both run by default):
    subtitle   merge each segment's artifacts/translate/final_subtitle.srt with time offsets
    render     concat each segment's artifacts/render/<render-filename> via ffmpeg concat

Safe to re-run; overwrites the parent outputs.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from engine.segment_manager import (
    SegmentError,
    merge_segment_final_subtitles,
    merge_segment_renders,
)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Merge per-segment outputs into parent workspace.")
    p.add_argument("--parent-workspace", required=True)
    p.add_argument(
        "--skip-subtitle",
        action="store_true",
        help="Skip merging final_subtitle.srt.",
    )
    p.add_argument(
        "--skip-render",
        action="store_true",
        help="Skip ffmpeg concat of per-segment render outputs.",
    )
    p.add_argument(
        "--render-filename",
        default="final.mp4",
        help="File name to concat from each segment's artifacts/render/ (default final.mp4).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    parent = Path(ns.parent_workspace).expanduser().resolve()

    if not ns.skip_subtitle:
        try:
            out = merge_segment_final_subtitles(parent)
        except SegmentError as e:
            print(f"Merge subtitle failed: {e}", file=sys.stderr)
            return 1
        print(f"[merge] subtitle -> {out}", file=sys.stderr)

    if not ns.skip_render:
        try:
            out = merge_segment_renders(parent, render_filename=ns.render_filename)
        except SegmentError as e:
            print(f"Merge render failed: {e}", file=sys.stderr)
            return 1
        print(f"[merge] render -> {out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
