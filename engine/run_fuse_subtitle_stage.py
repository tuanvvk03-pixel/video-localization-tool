"""
CLI wrapper around engine/fuse_subtitle.py — merges source_audio.srt + source_ocr.srt
into source.srt + source_provenance.json inside a job workspace.

Typical usage (from hybrid mode in run_transcribe_stage.py):

    python -m engine.run_fuse_subtitle_stage --job-workspace <jw>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from engine.fuse_subtitle import fuse_files


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fuse ASR + OCR SRTs into source.srt + provenance.")
    p.add_argument("--job-workspace", required=True, help="Job / video workspace root.")
    p.add_argument(
        "--match-threshold",
        type=float,
        default=0.15,
        help="Levenshtein threshold for fused_match (default 0.15).",
    )
    p.add_argument(
        "--drift-threshold",
        type=float,
        default=0.40,
        help="Levenshtein threshold for fused_drift (default 0.40); above -> fused_disagreement.",
    )
    p.add_argument(
        "--extractor-label",
        default="hybrid",
        help="String stamped into source_provenance.json (default hybrid).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    jw = Path(ns.job_workspace).expanduser().resolve()
    transcribe_dir = jw / "artifacts" / "transcribe"
    asr_srt = transcribe_dir / "source_audio.srt"
    ocr_srt = transcribe_dir / "source_ocr.srt"
    out_srt = transcribe_dir / "source.srt"
    out_prov = transcribe_dir / "source_provenance.json"

    if not asr_srt.is_file() and not ocr_srt.is_file():
        print(
            f"[fuse] neither {asr_srt.name} nor {ocr_srt.name} exists under {transcribe_dir}",
            file=sys.stderr,
        )
        return 1

    try:
        prov = fuse_files(
            asr_srt,
            ocr_srt,
            out_srt=out_srt,
            out_provenance=out_prov,
            match_threshold=float(ns.match_threshold),
            drift_threshold=float(ns.drift_threshold),
            extractor_label=ns.extractor_label,
        )
    except Exception as exc:
        print(f"[fuse] failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"[fuse] wrote {out_srt} ({prov['final_cue_count']} cues; "
        f"asr={prov['asr_cue_count']} ocr={prov['ocr_cue_count']}).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
