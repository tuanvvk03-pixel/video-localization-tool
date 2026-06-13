"""E4 — vocal separation (Demucs) so the original music/SFX bed survives.

The default mix either drops the whole original track (loses the music) or ducks
it (the competitor's voice bleeds through). Demucs splits the original audio into
``vocals`` + ``no_vocals`` (instrumental); we keep the instrumental and lay the
new translated voice over it → a clean dub that preserves the original music.

Demucs is an optional, heavy dependency (torch). It is invoked as a subprocess of
the *same* Python that runs this stage (so it shares the app venv's torch/cuda).
If it isn't installed we raise VocalSeparationError with an install hint rather
than crashing the pipeline.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


class VocalSeparationError(RuntimeError):
    pass


DEFAULT_MODEL = "htdemucs"


def demucs_available(python_exe: str | None = None) -> bool:
    exe = python_exe or sys.executable
    proc = subprocess.run([exe, "-c", "import demucs"], capture_output=True, text=True)
    return proc.returncode == 0


def separate_instrumental(
    audio_input: str | Path,
    out_instrumental_wav: str | Path,
    *,
    device: str = "auto",
    model: str = DEFAULT_MODEL,
    python_exe: str | None = None,
    work_dir: str | Path | None = None,
) -> dict:
    """Run Demucs two-stem separation and copy the instrumental to out_instrumental_wav.

    ``device`` is one of "auto" | "cpu" | "cuda". "auto" lets Demucs pick (CUDA
    when available). Returns a small manifest dict. Raises VocalSeparationError.
    """
    exe = python_exe or sys.executable
    src = Path(audio_input).expanduser().resolve()
    out_wav = Path(out_instrumental_wav).expanduser().resolve()
    if not src.is_file():
        raise VocalSeparationError(f"Audio input not found: {src}")
    if not demucs_available(exe):
        raise VocalSeparationError(
            "Demucs is not installed. Install it into the app environment: pip install demucs"
        )

    out_dir = Path(work_dir).expanduser().resolve() if work_dir else (out_wav.parent / "_demucs")
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [exe, "-m", "demucs", "--two-stems", "vocals", "-n", model, "-o", str(out_dir)]
    dev = (device or "auto").strip().lower()
    if dev in ("cpu", "cuda"):
        cmd.extend(["-d", dev])
    cmd.append(str(src))

    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        tail = ((proc.stderr or "") + "\n" + (proc.stdout or ""))[-4000:]
        raise VocalSeparationError(f"Demucs failed (exit {proc.returncode}):\n{tail}")

    # Demucs writes <out_dir>/<model>/<input_stem>/no_vocals.wav
    produced = out_dir / model / src.stem / "no_vocals.wav"
    if not produced.is_file():
        # Be tolerant of model-name subfolder differences; search for it.
        matches = list(out_dir.rglob("no_vocals.wav"))
        if not matches:
            raise VocalSeparationError(
                f"Demucs ran but no_vocals.wav was not found under {out_dir}."
            )
        produced = matches[0]

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(produced, out_wav)
    shutil.rmtree(out_dir, ignore_errors=True)
    return {
        "model": model,
        "device": dev,
        "instrumental_path": str(out_wav),
        "source_audio": str(src),
    }
