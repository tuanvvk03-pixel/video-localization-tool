"""Split a long video into 3-5 minute segment workspaces (Phase 4).

Reads input/source.mp4 under <parent-workspace>, plans 3-5 minute segments,
creates segments/seg_NNN/input/source.mp4 for each, and writes
segments/manifest.json.

Videos at or under 5 minutes still produce a single seg_000 workspace so the
downstream runner can stay uniform.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from engine.segment_manager import (
    SegmentError,
    init_segment_workspaces,
    plan_segments,
    probe_video_duration,
)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Split long video into segment workspaces.")
    p.add_argument("--parent-workspace", required=True, help="Parent workspace (contains input/source.mp4).")
    p.add_argument(
        "--video",
        default="",
        help="Override source video path (default: <parent>/input/source.mp4).",
    )
    p.add_argument(
        "--target-minutes",
        type=float,
        default=4.0,
        help="Target segment length (default 4.0).",
    )
    p.add_argument(
        "--max-minutes",
        type=float,
        default=5.0,
        help="Maximum segment length (default 5.0).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    parent = Path(ns.parent_workspace).expanduser().resolve()
    video = Path(ns.video).expanduser() if ns.video else parent / "input" / "source.mp4"
    if not video.is_file():
        print(f"Missing video: {video}", file=sys.stderr)
        return 1

    try:
        duration = probe_video_duration(video)
    except SegmentError as e:
        print(f"Probe failed: {e}", file=sys.stderr)
        return 1

    try:
        plan = plan_segments(
            duration,
            target_s=float(ns.target_minutes) * 60.0,
            max_s=float(ns.max_minutes) * 60.0,
        )
    except SegmentError as e:
        print(f"Plan failed: {e}", file=sys.stderr)
        return 1

    try:
        seg_dirs = init_segment_workspaces(parent, video, plan)
    except SegmentError as e:
        print(f"Split failed: {e}", file=sys.stderr)
        return 1

    summary = {
        "parent_workspace": str(parent),
        "source_video": str(video.resolve()),
        "duration_s": duration,
        "segment_count": len(seg_dirs),
        "segments": [
            {
                "index": p.index,
                "start_s": p.start_s,
                "end_s": p.end_s,
                "workspace": str(seg_dirs[i].resolve()),
            }
            for i, p in enumerate(plan)
        ],
    }
    json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
