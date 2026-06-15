"""G — collect a project's rendered videos into one export folder.

After a batch run each video's output lives at
``<video_workspace>/artifacts/render/final.mp4``. This gathers them into a single
folder with clean, descriptive names so the user can upload the whole batch.
"""
from __future__ import annotations

import re
import shutil
import time
from pathlib import Path
from typing import Any

from engine.project_manager import load_project


def _safe(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", str(name).strip()).strip("-._")
    return (s or "video")[:80]


def _mp4_has_moov(path: Path) -> bool:
    """Scan top-level MP4 boxes for 'moov' — present only on a fully written file.
    A render still being flushed (Windows) lacks it, so we avoid copying a
    truncated 'moov atom not found' file."""
    try:
        size = path.stat().st_size
        if size < 16:
            return False
        with open(path, "rb") as f:
            pos = 0
            while pos < size:
                f.seek(pos)
                header = f.read(8)
                if len(header) < 8:
                    return False
                box_size = int.from_bytes(header[:4], "big")
                box_type = header[4:8]
                if box_type == b"moov":
                    return True
                if box_size == 1:  # 64-bit extended size
                    ext = f.read(8)
                    if len(ext) < 8:
                        return False
                    box_size = int.from_bytes(ext, "big")
                if box_size < 8:
                    return False
                pos += box_size
    except OSError:
        return False
    return False


def _wait_ready(path: Path, timeout: float = 8.0) -> bool:
    """Wait until the file size is stable and the MP4 has a moov atom (fully
    written), so export never copies a render that's mid-flush."""
    deadline = time.time() + max(0.0, timeout)
    last_size = -1
    while time.time() < deadline:
        try:
            sz = path.stat().st_size
        except OSError:
            sz = -1
        if sz > 0 and sz == last_size and _mp4_has_moov(path):
            return True
        last_size = sz
        time.sleep(0.4)
    return _mp4_has_moov(path)


def export_project_renders(project_root: str | Path, dest: str | Path | None = None) -> dict[str, Any]:
    """Copy every rendered final.mp4 in the project into ``dest`` (default
    ``<project_root>/export``) named ``<project>_<video_id>.mp4``."""
    pr = Path(project_root).expanduser().resolve()
    state = load_project(pr)
    export_dir = Path(dest).expanduser().resolve() if dest else (pr / "export")
    export_dir.mkdir(parents=True, exist_ok=True)
    proj = _safe(state.config.project_name or pr.name)

    exported: list[dict[str, str]] = []
    skipped: list[str] = []
    for v in state.videos:
        final = Path(v.workspace) / "artifacts" / "render" / "final.mp4"
        if not final.is_file():
            skipped.append(v.video_id)
            continue
        # Guard against copying a render that is still being flushed to disk
        # (Windows) — wait for a stable, moov-complete MP4 before copying.
        if not _wait_ready(final):
            skipped.append(v.video_id)
            continue
        out = export_dir / f"{proj}_{_safe(v.video_id)}.mp4"
        shutil.copy2(final, out)
        exported.append({"video_id": v.video_id, "path": str(out)})
    return {"export_dir": str(export_dir), "exported": exported, "skipped": skipped}
