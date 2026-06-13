from __future__ import annotations

from engine.json_store import write_json_atomic
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from engine.ffmpeg_bins import resolve_ffmpeg_executable
from engine.input_provenance import fingerprint_file

REPO_ROOT = Path(__file__).resolve().parents[1]
YT_DLP_BUNDLED = REPO_ROOT / "yt" / "yt-dlp.exe"

def default_url_download_workspace_root() -> Path:
    """
    Default parent folder for jobs created via ``init_job_from_url`` (Phase L).

    - Dev: ``<repo>/Downloads``
    - PyInstaller: ``<folder containing the .exe>/Downloads`` (persistent; not ``_MEIPASS``).
    """
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
    else:
        base = REPO_ROOT
    out = (base / "Downloads").resolve()
    out.mkdir(parents=True, exist_ok=True)
    return out
DOWNLOAD_MANIFEST_REL = Path("artifacts") / "download" / "download_manifest.json"
_JOB_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")


class VideoDownloadError(RuntimeError):
    pass


def _slug_job_id(name: str) -> str:
    s = _JOB_ID_RE.sub("-", name).strip("-._")
    return s or "job"


def resolve_yt_dlp_executable() -> tuple[str | None, str | None]:
    raw = (os.environ.get("YT_DLP_BIN") or "").strip()
    if raw:
        candidate = Path(raw).expanduser()
        if not candidate.is_file():
            return None, (
                f"YT_DLP_BIN is set to {raw!r} but that path does not exist. "
                "Fix YT_DLP_BIN, place yt/yt-dlp.exe in the repo, or add yt-dlp to PATH."
            )
        return str(candidate.resolve()), None

    if YT_DLP_BUNDLED.is_file():
        return str(YT_DLP_BUNDLED.resolve()), None

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundled = Path(meipass) / "bin" / "yt-dlp.exe"
            if bundled.is_file():
                return str(bundled.resolve()), None

    found = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")
    if found:
        return found, None
    return None, (
        "yt-dlp not found: set YT_DLP_BIN, place yt/yt-dlp.exe in the repo, "
        "or install yt-dlp and add it to PATH."
    )


def _python_yt_dlp_command() -> list[str] | None:
    if importlib.util.find_spec("yt_dlp") is None:
        return None
    return [sys.executable, "-m", "yt_dlp"]


def _yt_dlp_runtime_env() -> dict[str, str]:
    env = os.environ.copy()
    tmp_root = REPO_ROOT / ".runtime" / "yt-dlp-tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    env["TMP"] = str(tmp_root)
    env["TEMP"] = str(tmp_root)
    # Guard against a common misconfiguration: proxy env vars pointing to a
    # dead local endpoint (e.g. http://127.0.0.1:9) which causes yt-dlp to fail
    # immediately for all network operations.
    toxic = {"http://127.0.0.1:9", "http://localhost:9"}
    removed: dict[str, str] = {}
    for k in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        v = (env.get(k) or "").strip()
        if v in toxic:
            removed[k] = v
            env.pop(k, None)
    if removed:
        # Expose a small diagnostic hint for error messages/manifests.
        env["VIDEO_LOCALIZATION_PROXY_SANITIZED"] = ",".join(sorted(removed.keys()))
    return env


def _probe_command(
    command: list[str],
    *,
    label: str,
    timeout_s: int,
) -> tuple[bool, str, dict[str, Any]]:
    try:
        proc = subprocess.run(
            [*command, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
            check=False,
            env=_yt_dlp_runtime_env(),
        )
    except OSError as e:
        return False, f"Could not execute {label}: {e}", {"command": command}
    except subprocess.TimeoutExpired:
        return False, f"{label} did not respond to --version within {timeout_s}s.", {"command": command}

    head = (proc.stdout or proc.stderr or "").splitlines()
    version_line = head[0].strip() if head else ""
    details: dict[str, Any] = {"command": command, "returncode": int(proc.returncode)}
    if version_line:
        details["version_line"] = version_line
    if proc.returncode != 0:
        msg = f"{label} failed health probe (--version exit {proc.returncode})."
        if version_line:
            msg = f"{msg} {version_line}"
        return False, msg, details
    return True, f"{label} is healthy: {version_line or 'ok'}", details


def probe_yt_dlp_health(*, timeout_s: int = 15) -> tuple[bool, str, dict[str, Any]]:
    exe_path, exe_err = resolve_yt_dlp_executable()
    errors: list[str] = []
    if exe_path is not None:
        ok, msg, details = _probe_command([exe_path], label="yt-dlp executable", timeout_s=timeout_s)
        details["source"] = "executable"
        details["path"] = exe_path
        if ok:
            return True, msg, details
        errors.append(msg)
    elif exe_err:
        errors.append(exe_err)

    py_cmd = _python_yt_dlp_command()
    if py_cmd is not None:
        ok, msg, details = _probe_command(py_cmd, label="python -m yt_dlp", timeout_s=timeout_s)
        details["source"] = "python_module"
        if ok:
            return True, msg, details
        errors.append(msg)
    else:
        errors.append(
            "Python package yt_dlp is not installed. Install with: python -m pip install yt-dlp"
        )

    return False, " | ".join(err for err in errors if err), {"path": exe_path, "source": "unavailable"}


def _candidate_yt_dlp_commands() -> list[tuple[list[str], str]]:
    out: list[tuple[list[str], str]] = []
    exe_path, _ = resolve_yt_dlp_executable()
    if exe_path is not None:
        out.append(([exe_path], "yt-dlp executable"))
    py_cmd = _python_yt_dlp_command()
    if py_cmd is not None:
        out.append((py_cmd, "python -m yt_dlp"))
    return out


def _run_yt_dlp(
    args: list[str],
    *,
    timeout_s: int,
) -> subprocess.CompletedProcess[str]:
    candidates = _candidate_yt_dlp_commands()
    if not candidates:
        raise VideoDownloadError(
            "yt-dlp is unavailable. Install with: python -m pip install yt-dlp "
            "or provide a working yt-dlp executable."
        )
    errors: list[str] = []
    last_proc: subprocess.CompletedProcess[str] | None = None
    for command, label in candidates:
        try:
            proc = subprocess.run(
                [*command, *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_s,
                check=False,
                env=_yt_dlp_runtime_env(),
            )
        except subprocess.TimeoutExpired:
            errors.append(f"{label} timed out after {timeout_s}s.")
            continue
        except OSError as e:
            errors.append(f"Could not execute {label}: {e}")
            continue
        last_proc = proc
        if proc.returncode == 0:
            return proc
        tail = (proc.stderr or proc.stdout or "").strip()[-1000:]
        errors.append(f"{label} failed (exit {proc.returncode}): {tail}")
    if last_proc is not None:
        return last_proc
    raise VideoDownloadError(" | ".join(errors))


def probe_video_url(url: str, *, timeout_s: int = 120) -> dict[str, Any]:
    source_url = str(url or "").strip()
    if not source_url:
        raise VideoDownloadError("Missing video URL.")

    proc = _run_yt_dlp(
        [
            "--no-playlist",
            "--no-warnings",
            "--dump-single-json",
            source_url,
        ],
        timeout_s=timeout_s,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip()[-4000:]
        sanitized = (_yt_dlp_runtime_env().get("VIDEO_LOCALIZATION_PROXY_SANITIZED") or "").strip()
        hint = f" (proxy env sanitized: {sanitized})" if sanitized else ""
        raise VideoDownloadError(f"yt-dlp probe failed (exit {proc.returncode}): {tail}{hint}")

    text = (proc.stdout or "").strip()
    if not text:
        raise VideoDownloadError("yt-dlp probe returned empty metadata.")
    try:
        info = json.loads(text)
    except json.JSONDecodeError as e:
        raise VideoDownloadError("yt-dlp probe returned invalid JSON.") from e

    return {
        "source_url": source_url,
        "webpage_url": info.get("webpage_url") or source_url,
        "title": info.get("title"),
        "duration": info.get("duration"),
        "uploader": info.get("uploader"),
        "extractor": info.get("extractor"),
        "video_id": info.get("id"),
        "thumbnail": info.get("thumbnail"),
        "raw_info": info,
    }


def _write_download_manifest(job_workspace: Path, body: dict[str, Any]) -> Path:
    path = job_workspace / DOWNLOAD_MANIFEST_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, body)
    return path


def init_job_from_url(
    *,
    url: str,
    workspace_root: str | Path,
    job_id: str = "",
    force: bool = False,
    probe_timeout_s: int = 120,
    download_timeout_s: int = 1800,
) -> dict[str, Any]:
    meta = probe_video_url(url, timeout_s=probe_timeout_s)
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    chosen_job_id = str(job_id or "").strip() or _slug_job_id(
        str(meta.get("title") or meta.get("video_id") or "job")
    )
    job_workspace = resolved_workspace_root / chosen_job_id

    if job_workspace.exists() and any(job_workspace.iterdir()) and not force:
        raise VideoDownloadError(
            f"Workspace already exists and is not empty: {job_workspace}. Pass force=true to reuse."
        )

    input_dir = job_workspace / "input"
    artifacts_dir = job_workspace / "artifacts"
    input_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    outtmpl = input_dir / "source.%(ext)s"
    yt_args = [
        "--no-playlist",
        "--no-warnings",
        "--restrict-filenames",
        "--no-progress",
        "--output",
        str(outtmpl),
        "--format",
        "bv*+ba/b",
        "--merge-output-format",
        "mp4",
        "--print",
        "after_move:filepath",
    ]
    ffmpeg_path, _ = resolve_ffmpeg_executable()
    if ffmpeg_path:
        yt_args.extend(["--ffmpeg-location", ffmpeg_path])
    yt_args.append(str(url).strip())
    proc = _run_yt_dlp(yt_args, timeout_s=download_timeout_s)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip()[-4000:]
        sanitized = (_yt_dlp_runtime_env().get("VIDEO_LOCALIZATION_PROXY_SANITIZED") or "").strip()
        hint = f" (proxy env sanitized: {sanitized})" if sanitized else ""
        raise VideoDownloadError(f"yt-dlp download failed (exit {proc.returncode}): {tail}{hint}")

    lines = [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip()]
    downloaded_path = Path(lines[-1]).expanduser().resolve() if lines else None
    if downloaded_path is None or not downloaded_path.is_file():
        candidates = sorted(input_dir.glob("source.*"))
        candidates = [p for p in candidates if p.is_file()]
        downloaded_path = candidates[-1] if candidates else None
    if downloaded_path is None or not downloaded_path.is_file():
        raise VideoDownloadError("yt-dlp download finished but no output file was found in workspace input/.")

    canonical_input = input_dir / "source.mp4"
    alias_used = downloaded_path.name != canonical_input.name
    if downloaded_path.resolve() != canonical_input.resolve():
        if canonical_input.exists():
            canonical_input.unlink()
        shutil.move(str(downloaded_path), str(canonical_input))

    manifest_path = _write_download_manifest(
        job_workspace,
        {
            "version": 1,
            "downloaded_at_unix": time.time(),
            "source_url": str(url).strip(),
            "webpage_url": meta.get("webpage_url"),
            "extractor": meta.get("extractor"),
            "video_id": meta.get("video_id"),
            "title": meta.get("title"),
            "duration": meta.get("duration"),
            "uploader": meta.get("uploader"),
            "thumbnail": meta.get("thumbnail"),
            "downloaded_original_path": str(downloaded_path),
            "input_video_path": str(canonical_input.resolve()),
            "canonical_name_alias_used": bool(alias_used),
            "input_video_fingerprint": fingerprint_file(canonical_input),
            "proxy_env_sanitized": (_yt_dlp_runtime_env().get("VIDEO_LOCALIZATION_PROXY_SANITIZED") or "").split(",")
            if (_yt_dlp_runtime_env().get("VIDEO_LOCALIZATION_PROXY_SANITIZED") or "").strip()
            else [],
        },
    )
    return {
        "job_id": chosen_job_id,
        "job_workspace": str(job_workspace.resolve()),
        "input_video_path": str(canonical_input.resolve()),
        "input_video_fingerprint": fingerprint_file(canonical_input),
        "download_manifest_path": str(manifest_path.resolve()),
        "download": {
            "source_url": str(url).strip(),
            "webpage_url": meta.get("webpage_url"),
            "title": meta.get("title"),
            "duration": meta.get("duration"),
            "uploader": meta.get("uploader"),
            "extractor": meta.get("extractor"),
            "video_id": meta.get("video_id"),
            "thumbnail": meta.get("thumbnail"),
        },
    }
