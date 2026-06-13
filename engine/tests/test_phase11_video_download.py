from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.video_download import (
    VideoDownloadError,
    default_url_download_workspace_root,
    init_job_from_url,
    probe_video_url,
)


class VideoDownloadTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="phase11_download_"))
        self.workspace_root = self.root / "workspaces"
        self.workspace_root.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_default_url_download_workspace_root_creates_downloads_dir(self) -> None:
        path = default_url_download_workspace_root()
        self.assertTrue(path.is_dir())
        self.assertEqual(path.name, "Downloads")

    def test_probe_video_url_returns_normalized_metadata(self) -> None:
        payload = {
            "id": "abc123",
            "title": "Demo Video",
            "duration": 42,
            "uploader": "Uploader",
            "extractor": "youtube",
            "webpage_url": "https://example.com/watch?v=abc123",
        }
        with mock.patch(
            "engine.video_download._run_yt_dlp",
            return_value=SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr=""),
        ):
            info = probe_video_url("https://example.com/watch?v=abc123")
        self.assertEqual(info["video_id"], "abc123")
        self.assertEqual(info["title"], "Demo Video")
        self.assertEqual(info["webpage_url"], "https://example.com/watch?v=abc123")

    def test_init_job_from_url_downloads_into_workspace_and_writes_manifest(self) -> None:
        download_path_holder: dict[str, Path] = {}

        def fake_run(args: list[str], *, timeout_s: int):
            if "--dump-single-json" in args:
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps(
                        {
                            "id": "abc123",
                            "title": "Demo Video",
                            "duration": 42,
                            "uploader": "Uploader",
                            "extractor": "youtube",
                            "webpage_url": "https://example.com/watch?v=abc123",
                        }
                    ),
                    stderr="",
                )
            out_idx = args.index("--output") + 1
            outtmpl = Path(args[out_idx])
            downloaded = outtmpl.parent / "source.webm"
            downloaded.write_bytes(b"video")
            download_path_holder["path"] = downloaded
            return SimpleNamespace(returncode=0, stdout=str(downloaded) + "\n", stderr="")

        with mock.patch("engine.video_download._run_yt_dlp", side_effect=fake_run):
            payload = init_job_from_url(
                url="https://example.com/watch?v=abc123",
                workspace_root=self.workspace_root,
            )

        jw = Path(payload["job_workspace"])
        canonical = jw / "input" / "source.mp4"
        manifest = jw / "artifacts" / "download" / "download_manifest.json"
        self.assertTrue(canonical.is_file())
        self.assertTrue(manifest.is_file())
        self.assertFalse(download_path_holder["path"].exists())
        body = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(body["video_id"], "abc123")
        self.assertTrue(body["canonical_name_alias_used"])
        self.assertEqual(body["input_video_path"], str(canonical.resolve()))

    def test_init_job_from_url_errors_when_workspace_exists_without_force(self) -> None:
        existing = self.workspace_root / "demo-video"
        existing.mkdir()
        (existing / "keep.txt").write_text("x", encoding="utf-8")
        with mock.patch(
            "engine.video_download._run_yt_dlp",
            return_value=SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"id": "abc123", "title": "Demo Video"}),
                stderr="",
            ),
        ):
            with self.assertRaises(VideoDownloadError):
                init_job_from_url(
                    url="https://example.com/watch?v=abc123",
                    workspace_root=self.workspace_root,
                )

    def test_probe_health_falls_back_to_python_module_when_exe_is_broken(self) -> None:
        from engine import video_download

        calls: list[list[str]] = []

        def fake_run(cmd: list[str], **_kwargs):
            calls.append(list(cmd))
            if cmd[0].endswith("yt-dlp.exe"):
                return SimpleNamespace(returncode=1, stdout="", stderr="broken exe")
            return SimpleNamespace(returncode=0, stdout="2026.04.15\n", stderr="")

        with mock.patch("engine.video_download.resolve_yt_dlp_executable", return_value=("D:/repo/yt/yt-dlp.exe", None)), \
                mock.patch("engine.video_download.importlib.util.find_spec", return_value=object()), \
                mock.patch("engine.video_download.subprocess.run", side_effect=fake_run):
            ok, message, details = video_download.probe_yt_dlp_health()
        self.assertTrue(ok)
        self.assertEqual(details["source"], "python_module")
        self.assertIn("python -m yt_dlp", message)
        self.assertEqual(calls[0][0], "D:/repo/yt/yt-dlp.exe")
        self.assertEqual(calls[1][:3], [sys.executable, "-m", "yt_dlp"])


if __name__ == "__main__":
    unittest.main()
