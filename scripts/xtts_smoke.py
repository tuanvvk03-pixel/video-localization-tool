"""Manual smoke for the XTTS voice-cloning provider (Phase D2).

Requires the optional heavy deps + ideally a CUDA GPU:
    pip install TTS torch

Usage (from repo root):
    python scripts/xtts_smoke.py --speaker path/to/speaker.wav
    python scripts/xtts_smoke.py --speaker s.wav --text "..." --language vi --out out.wav

Synthesizes one cue by cloning the voice in --speaker and prints the output
duration. Not part of CI (no model/GPU there) — run this to validate XTTS on a
machine that has the deps installed.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Allow running as `python scripts/xtts_smoke.py` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.tts.xtts_provider import XttsProvider  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Smoke-test the XTTS clone provider.")
    ap.add_argument("--speaker", required=True, help="6-30s reference .wav of the target voice.")
    ap.add_argument("--text", default="Xin chào, đây là giọng nói được nhân bản thử nghiệm.")
    ap.add_argument("--language", default="vi", help="XTTS language code (vi/en/zh/ja/ko/...).")
    ap.add_argument("--out", default="xtts_smoke_out.wav")
    ns = ap.parse_args(argv)

    os.environ.setdefault("XTTS_LANGUAGE", ns.language)
    out = Path(ns.out).resolve()
    try:
        dur = asyncio.run(
            XttsProvider().synthesize_cue_to_wav(ns.text, out, voice=ns.speaker, rate="")
        )
    except RuntimeError as e:
        print(f"FAILED: {e}", file=sys.stderr)
        return 1
    print(f"OK: wrote {out} ({dur} ms) by cloning {ns.speaker!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
