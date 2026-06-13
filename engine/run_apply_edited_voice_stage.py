"""
Apply externally edited voice SRT into artifacts/edit/edited_voice.srt.

This complements run_seed_voice_edit_stage for workflows where users edit in an external editor
and then re-import the edited file.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from engine.voice_edit_api import VoiceEditError, mark_voice_edited, save_edited_voice


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Apply user-edited voice subtitle file into artifacts/edit/edited_voice.srt."
    )
    p.add_argument("--job-workspace", required=True, help="Job / video workspace root.")
    p.add_argument(
        "--edited-voice-srt-path",
        required=True,
        help="Path to the user's edited .srt file (voice variant).",
    )
    p.add_argument(
        "--mark-voice-edited",
        action="store_true",
        help="Also mark voice edit as completed (voice_edited).",
    )
    p.add_argument("--note", default="", help="Optional note stored into edit_manifest.json.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    jw = Path(ns.job_workspace).expanduser().resolve()
    try:
        out = save_edited_voice(
            jw,
            edited_voice_source_path=Path(ns.edited_voice_srt_path).expanduser(),
            note=(ns.note.strip() or None),
        )
        if ns.mark_voice_edited:
            mark_voice_edited(jw)
    except VoiceEditError as e:
        print(str(e), file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Apply edited voice failed: {e}", file=sys.stderr)
        return 1
    print(str(out.resolve()), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

