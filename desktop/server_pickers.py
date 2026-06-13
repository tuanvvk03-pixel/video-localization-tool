"""Native file/folder picker and OS-reveal endpoint handlers.

Desktop-only convenience endpoints backed by tkinter dialogs and the platform
file manager. No job/project state. Extracted from the server monolith with
behaviour identical to the previous inline handlers.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from desktop.server_shared import _err, _ok, _require


def handle_pick_srt_file(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    payload: dict[str, Any] = dict(body) if isinstance(body, dict) else {}
    if not payload.get("filters"):
        payload["filters"] = ["SRT files (*.srt)"]
    return handle_pick_file(payload)


def handle_pick_folder(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Open native folder picker dialog. Works on all platforms."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(title="Chọn thư mục dự án")
        root.destroy()
        if folder:
            return _ok({"path": str(Path(folder).resolve())})
        return _ok({"cancelled": True})
    except Exception as e:
        return _err("pick_folder_failed", f"Could not open folder dialog: {e}")


def handle_pick_file(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Open native file picker dialog and return an absolute path."""
    filters = body.get("filters")
    filetypes: list[tuple[str, str]] = [
        ("Video files", "*.mp4 *.mov *.mkv *.webm *.avi"),
        ("All files", "*.*"),
    ]
    if isinstance(filters, list) and filters:
        parsed: list[tuple[str, str]] = []
        for item in filters:
            text = str(item or "").strip()
            if not text:
                continue
            if "(" in text and ")" in text:
                label, rest = text.split("(", 1)
                pattern = rest.rsplit(")", 1)[0].replace(";", " ").strip()
                parsed.append((label.strip() or "Files", pattern or "*.*"))
            else:
                parsed.append(("Files", text))
        if parsed:
            filetypes = parsed
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askopenfilename(
            title="Chá»n video nguá»“n",
            filetypes=filetypes,
        )
        root.destroy()
        if selected:
            return _ok({"path": str(Path(selected).resolve())})
        return _ok({"cancelled": True})
    except Exception as e:
        return _err("pick_file_failed", f"Could not open file dialog: {e}")


def handle_pick_files(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Open a native multi-file picker and return absolute paths."""
    filters = body.get("filters")
    filetypes: list[tuple[str, str]] = [
        ("Video files", "*.mp4 *.mov *.mkv *.webm *.avi"),
        ("All files", "*.*"),
    ]
    if isinstance(filters, list) and filters:
        parsed: list[tuple[str, str]] = []
        for item in filters:
            text = str(item or "").strip()
            if not text:
                continue
            if "(" in text and ")" in text:
                label, rest = text.split("(", 1)
                pattern = rest.rsplit(")", 1)[0].replace(";", " ").strip()
                parsed.append((label.strip() or "Files", pattern or "*.*"))
            else:
                parsed.append(("Files", text))
        if parsed:
            filetypes = parsed
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askopenfilenames(
            title="Chọn các video nguồn",
            filetypes=filetypes,
        )
        root.destroy()
        if not selected:
            return _ok({"cancelled": True})
        paths = [str(Path(p).resolve()) for p in selected]
        return _ok({"paths": paths})
    except Exception as e:
        return _err("pick_files_failed", f"Could not open file dialog: {e}")


def handle_reveal(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Open the OS file manager at the given path. Desktop-only convenience."""
    missing = _require(body, "path")
    if missing:
        return _err("missing_field", f"Missing required field: {missing}")
    target = Path(str(body["path"])).expanduser()
    try:
        resolved = target.resolve(strict=True)
    except (OSError, FileNotFoundError):
        return _err("path_not_found", f"Path not found: {target}")
    try:
        if sys.platform.startswith("win"):
            if resolved.is_dir():
                subprocess.Popen(["explorer", str(resolved)])  # noqa: S603,S607
            else:
                subprocess.Popen(["explorer", "/select,", str(resolved)])  # noqa: S603,S607
        elif sys.platform == "darwin":
            args = ["open", "-R", str(resolved)] if resolved.is_file() else ["open", str(resolved)]
            subprocess.Popen(args)  # noqa: S603
        else:
            subprocess.Popen(["xdg-open", str(resolved if resolved.is_dir() else resolved.parent)])  # noqa: S603,S607
    except OSError as e:
        return _err("reveal_failed", f"Could not reveal path: {e}")
    return _ok({"path": str(resolved)})
