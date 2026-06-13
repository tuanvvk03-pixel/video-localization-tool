"""
Seed artifacts/edit/edited_voice.srt from artifacts/translate/translated_voice.srt.

This is the official entrypoint to start the voice-edit flow for the app:
- Creates artifacts/edit/edited_voice.srt (without overwriting by default)
- Writes artifacts/edit/edit_manifest.json
- Marks job/video state as voice_edit_pending
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from engine.voice_edit_api import VoiceEditError, seed_edited_voice


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Seed edited_voice.srt for voice edit flow.")
    p.add_argument("--job-workspace", required=True, help="Job / video workspace root.")
    p.add_argument("--overwrite", action="store_true", help="Overwrite artifacts/edit/edited_voice.srt if it exists.")
    p.add_argument("--note", default="", help="Optional note stored into edit_manifest.json.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    jw = Path(ns.job_workspace).expanduser().resolve()
    try:
        out = seed_edited_voice(
            jw,
            overwrite=bool(ns.overwrite),
            note=(ns.note.strip() or None),
        )
    except VoiceEditError as e:
        print(str(e), file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Seed voice edit failed: {e}", file=sys.stderr)
        return 1
    print(str(out.resolve()), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

