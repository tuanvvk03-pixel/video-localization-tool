"""Native desktop shell for the video localization tool (Phase N).

Wraps `desktop.server` in an OS-native window via pywebview so the app no
longer depends on the user's default browser. The HTTP server still runs
locally (127.0.0.1 on a free port) and serves the same static SPA and
JSON API.

Run:
    python -m desktop.native

Options:
    --host 127.0.0.1        bind host (default 127.0.0.1)
    --port 0                explicit port, 0 picks a free port (default 0)
    --title "VL Tool"       window title
    --width / --height      initial window size
    --dev                   also open DevTools (pywebview)

The window exposes `window.pywebview.api` with:
    pick_file(filters?)     -> {ok, path | cancelled | error}
    pick_folder()           -> {ok, path | cancelled | error}

Frontend code should prefer these when available and fall back to
`<input type="file">` otherwise — see `desktop/static/api.js`.
"""
from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path


def _suppress_child_consoles() -> None:
    """On Windows GUI builds, prevent child console apps (ffmpeg, yt-dlp, python)
    from flashing a cmd window. Injects CREATE_NO_WINDOW into every
    subprocess.Popen unless the caller already set a console-management flag.
    Also covers asyncio subprocesses (windows_utils.Popen subclasses Popen)."""
    if sys.platform != "win32":
        return
    create_no_window = 0x08000000
    keep_mask = 0x00000010 | 0x00000200 | 0x00000008  # NEW_CONSOLE | NEW_PROCESS_GROUP | DETACHED
    original_init = subprocess.Popen.__init__

    def patched_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        flags = int(kwargs.get("creationflags") or 0)
        if not (flags & keep_mask):
            kwargs["creationflags"] = flags | create_no_window
        return original_init(self, *args, **kwargs)

    subprocess.Popen.__init__ = patched_init  # type: ignore[method-assign]


_suppress_child_consoles()


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from desktop.server import _Handler, _ping_server  # noqa: E402


def _pick_free_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


def _start_server(host: str, port: int) -> tuple[ThreadingHTTPServer, threading.Thread]:
    httpd = ThreadingHTTPServer((host, port), _Handler)
    thread = threading.Thread(
        target=httpd.serve_forever,
        name="vltool-server",
        daemon=True,
    )
    thread.start()
    return httpd, thread


def _wait_for_ready(url: str, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _ping_server(url, timeout=1.0):
            return True
        time.sleep(0.15)
    return False


class NativeApi:
    """Bridge exposed to the renderer as `window.pywebview.api`.

    Each method returns a plain dict so the frontend can distinguish
    "user cancelled" from "error" without relying on exceptions.
    """

    def __init__(self) -> None:
        self._window = None

    def bind(self, window) -> None:
        self._window = window

    def pick_file(self, filters=None):
        try:
            import webview  # type: ignore
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"pywebview_unavailable: {e}"}
        if self._window is None:
            return {"ok": False, "error": "window_not_ready"}
        try:
            file_types = _coerce_file_types(filters)
            result = self._window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=file_types,
            )
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e)}
        if not result:
            return {"ok": True, "cancelled": True}
        path = result[0] if isinstance(result, (list, tuple)) else str(result)
        return {"ok": True, "path": str(path)}

    def pick_files(self, filters=None):
        try:
            import webview  # type: ignore
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"pywebview_unavailable: {e}"}
        if self._window is None:
            return {"ok": False, "error": "window_not_ready"}
        try:
            file_types = _coerce_file_types(filters)
            result = self._window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=True,
                file_types=file_types,
            )
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e)}
        if not result:
            return {"ok": True, "cancelled": True}
        paths = [str(p) for p in result] if isinstance(result, (list, tuple)) else [str(result)]
        return {"ok": True, "paths": paths}

    def pick_folder(self):
        try:
            import webview  # type: ignore
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"pywebview_unavailable: {e}"}
        if self._window is None:
            return {"ok": False, "error": "window_not_ready"}
        try:
            result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e)}
        if not result:
            return {"ok": True, "cancelled": True}
        path = result[0] if isinstance(result, (list, tuple)) else str(result)
        return {"ok": True, "path": str(path)}


def _coerce_file_types(filters):
    if not filters:
        return ("Video files (*.mp4;*.mov;*.mkv;*.webm;*.avi)", "All files (*.*)")
    if isinstance(filters, str):
        return (filters,)
    if isinstance(filters, (list, tuple)):
        return tuple(str(f) for f in filters)
    return ("All files (*.*)",)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Native desktop shell (pywebview).")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=0, help="0 = pick a free port")
    p.add_argument("--title", default="Video Localization Tool")
    p.add_argument("--width", type=int, default=1400)
    p.add_argument("--height", type=int, default=900)
    p.add_argument("--dev", action="store_true", help="open DevTools")
    p.add_argument(
        "--server-only",
        action="store_true",
        help="Run the local HTTP server without opening a native window "
        "(headless / browser mode; also used for packaging smoke tests).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)

    if not ns.server_only:
        try:
            import webview  # type: ignore
        except Exception as e:  # noqa: BLE001
            print(
                "[desktop.native] pywebview is not installed. "
                "Install with: pip install -r engine/requirements-desktop.txt",
                file=sys.stderr,
            )
            print(f"[desktop.native] import error: {e}", file=sys.stderr)
            return 2

    host = ns.host
    port = ns.port or _pick_free_port(host)
    httpd, _thread = _start_server(host, port)
    url = f"http://{host}:{port}"
    print(f"[desktop.native] serving on {url}", file=sys.stderr)

    if not _wait_for_ready(url):
        httpd.shutdown()
        httpd.server_close()
        print("[desktop.native] server failed to respond to /api/ping", file=sys.stderr)
        return 3

    if ns.server_only:
        print(f"[desktop.native] server-only mode; open {url} in a browser. Ctrl+C to stop.", file=sys.stderr)
        try:
            _thread.join()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.shutdown()
            httpd.server_close()
        return 0

    import webview  # type: ignore

    api = NativeApi()
    window = webview.create_window(
        ns.title,
        url=url,
        js_api=api,
        width=ns.width,
        height=ns.height,
        min_size=(960, 600),
    )
    api.bind(window)

    try:
        webview.start(debug=ns.dev)
    finally:
        try:
            httpd.shutdown()
        except Exception:  # noqa: BLE001
            pass
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
