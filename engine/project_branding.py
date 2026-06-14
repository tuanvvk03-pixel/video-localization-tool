"""F1.1 — distribute shared branding from a project to each of its videos.

Branding (logo / intro / outro / background + aspect + trim) is authored once at
the *project* level. We reuse engine.render_settings by treating the project root
as a pseudo-workspace: the template lives in ``<project_root>/video_state.json``
("render" block) with files under ``<project_root>/assets/render_*``. At batch
run time we copy those files into each video workspace (same relative paths) and
write the same render settings there, so every video renders with the shared
logo/outro/intro/trim without the user touching each one.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from engine.render_settings import load_render_settings, save_render_settings

# Settings keys that point at a workspace-relative file to copy across.
_FILE_KEYS = ("logo_path", "intro_clip_path", "outro_clip_path", "background_path")


def has_project_branding(project_root: str | Path) -> bool:
    settings = load_render_settings(project_root)
    return bool(settings)


def apply_branding_to_video(project_root: str | Path, video_workspace: str | Path) -> dict[str, Any] | None:
    """Copy the project's branding files + settings into one video workspace.

    Returns the applied render settings, or None when the project has no branding.
    """
    pr = Path(project_root)
    vw = Path(video_workspace)
    template = load_render_settings(pr)
    if not template:
        return None

    for key in _FILE_KEYS:
        rel = str(template.get(key) or "").strip()
        if not rel:
            continue
        src = pr / rel
        if not src.is_file():
            # File referenced but missing at project level → drop it for this video.
            template.pop(key, None)
            continue
        dst = vw / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    return save_render_settings(vw, template)
