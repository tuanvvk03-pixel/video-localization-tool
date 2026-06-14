"""G — collect a project's rendered videos into one export folder.

After a batch run each video's output lives at
``<video_workspace>/artifacts/render/final.mp4``. This gathers them into a single
folder with clean, descriptive names so the user can upload the whole batch.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from engine.project_manager import load_project


def _safe(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", str(name).strip()).strip("-._")
    return (s or "video")[:80]


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
        if final.is_file():
            out = export_dir / f"{proj}_{_safe(v.video_id)}.mp4"
            shutil.copy2(final, out)
            exported.append({"video_id": v.video_id, "path": str(out)})
        else:
            skipped.append(v.video_id)
    return {"export_dir": str(export_dir), "exported": exported, "skipped": skipped}
