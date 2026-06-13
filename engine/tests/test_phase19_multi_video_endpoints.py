"""Phase 19: multi-video project HTTP endpoints (desktop/server.py).

Covers:
    /api/init-project
    /api/add-video-to-project
    /api/save-video-override
    /api/get-project
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from http import HTTPStatus
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desktop import server as desktop_server
from engine import segment_manager


class MultiVideoEndpointsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase19_projects_"))
        self.projects_root = self.tmp_root / "projects"
        self.projects_root.mkdir()
        self.video_a = self.tmp_root / "clip_a.mp4"
        self.video_a.write_bytes(b"\x00A")
        self.video_b = self.tmp_root / "clip_b.mp4"
        self.video_b.write_bytes(b"\x00B")
        self._orig_probe = segment_manager.probe_video_duration
        segment_manager.probe_video_duration = lambda _p: 90.0  # type: ignore[assignment]

    def tearDown(self) -> None:
        segment_manager.probe_video_duration = self._orig_probe  # type: ignore[assignment]
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    # --- /api/init-project -------------------------------------------------

    def test_init_project_missing_name(self) -> None:
        status, payload = desktop_server.handle_init_project({})
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "missing_field")

    def test_init_project_creates_state_file(self) -> None:
        status, payload = desktop_server.handle_init_project(
            {
                "project_name": "demo",
                "projects_root": str(self.projects_root),
            }
        )
        self.assertEqual(status, HTTPStatus.OK)
        data = payload["data"]
        root = Path(data["project_root"])
        self.assertTrue((root / "project_state.json").is_file())
        self.assertFalse(data["used_default_projects_root"])
        self.assertEqual(data["project_name"], "demo")

    def test_init_project_rejects_existing_without_force(self) -> None:
        desktop_server.handle_init_project(
            {"project_name": "demo", "projects_root": str(self.projects_root)}
        )
        # seed a file so the project_root is "not empty"
        project_root = self.projects_root / "demo"
        (project_root / "sentinel.txt").write_text("x", encoding="utf-8")
        status, payload = desktop_server.handle_init_project(
            {"project_name": "demo", "projects_root": str(self.projects_root)}
        )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "init_project_failed")

    def test_init_project_applies_config_overrides(self) -> None:
        status, payload = desktop_server.handle_init_project(
            {
                "project_name": "demo",
                "projects_root": str(self.projects_root),
                "config_overrides": {
                    "tts_voice": "vi-VN-HoaiMyNeural",
                    "translate_backend": "block_v2",
                },
            }
        )
        self.assertEqual(status, HTTPStatus.OK)
        state = json.loads(
            (Path(payload["data"]["project_root"]) / "project_state.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(state["config"]["tts_voice"], "vi-VN-HoaiMyNeural")

    # --- /api/add-video-to-project ----------------------------------------

    def _make_project(self) -> Path:
        status, payload = desktop_server.handle_init_project(
            {"project_name": "demo", "projects_root": str(self.projects_root)}
        )
        self.assertEqual(status, HTTPStatus.OK)
        return Path(payload["data"]["project_root"])

    def test_add_video_copies_and_returns_entry(self) -> None:
        project_root = self._make_project()
        status, payload = desktop_server.handle_add_video_to_project(
            {
                "project_root": str(project_root),
                "video": str(self.video_a),
                "video_id": "clipA",
            }
        )
        self.assertEqual(status, HTTPStatus.OK)
        entry = payload["data"]
        self.assertEqual(entry["video_id"], "clipA")
        self.assertEqual(entry["duration_s"], 90.0)
        self.assertTrue((Path(entry["workspace"]) / "input" / "source.mp4").is_file())

    def test_add_video_duplicate_without_force(self) -> None:
        project_root = self._make_project()
        desktop_server.handle_add_video_to_project(
            {"project_root": str(project_root), "video": str(self.video_a), "video_id": "clipA"}
        )
        status, payload = desktop_server.handle_add_video_to_project(
            {"project_root": str(project_root), "video": str(self.video_a), "video_id": "clipA"}
        )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "add_video_failed")

    def test_add_video_with_override_persists_config(self) -> None:
        project_root = self._make_project()
        status, payload = desktop_server.handle_add_video_to_project(
            {
                "project_root": str(project_root),
                "video": str(self.video_a),
                "video_id": "clipA",
                "override": {"tts_voice": "vi-VN-NamMinhNeural"},
            }
        )
        self.assertEqual(status, HTTPStatus.OK)
        state = json.loads((project_root / "project_state.json").read_text(encoding="utf-8"))
        self.assertEqual(
            state["config"]["per_video_overrides"]["clipA"]["tts_voice"],
            "vi-VN-NamMinhNeural",
        )

    # --- /api/save-video-override -----------------------------------------

    def test_save_video_override_merges_and_clears(self) -> None:
        project_root = self._make_project()
        desktop_server.handle_add_video_to_project(
            {"project_root": str(project_root), "video": str(self.video_a), "video_id": "clipA"}
        )
        status, payload = desktop_server.handle_save_video_override(
            {
                "project_root": str(project_root),
                "video_id": "clipA",
                "override": {"tts_voice": "voice1", "tts_provider": "edge_tts"},
            }
        )
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["override"]["tts_voice"], "voice1")

        # Shallow merge: setting only tts_voice keeps tts_provider
        status, payload = desktop_server.handle_save_video_override(
            {
                "project_root": str(project_root),
                "video_id": "clipA",
                "override": {"tts_voice": "voice2"},
            }
        )
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["data"]["override"]["tts_voice"], "voice2")
        self.assertEqual(payload["data"]["override"]["tts_provider"], "edge_tts")

        # None clears a key
        status, payload = desktop_server.handle_save_video_override(
            {
                "project_root": str(project_root),
                "video_id": "clipA",
                "override": {"tts_provider": None},
            }
        )
        self.assertEqual(status, HTTPStatus.OK)
        self.assertNotIn("tts_provider", payload["data"]["override"])

    def test_save_video_override_rejects_unknown_keys(self) -> None:
        project_root = self._make_project()
        desktop_server.handle_add_video_to_project(
            {"project_root": str(project_root), "video": str(self.video_a), "video_id": "clipA"}
        )
        status, payload = desktop_server.handle_save_video_override(
            {
                "project_root": str(project_root),
                "video_id": "clipA",
                "override": {"not_a_real_key": "x"},
            }
        )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "unknown_override_keys")

    def test_save_video_override_unknown_video(self) -> None:
        project_root = self._make_project()
        status, payload = desktop_server.handle_save_video_override(
            {
                "project_root": str(project_root),
                "video_id": "ghost",
                "override": {"tts_voice": "x"},
            }
        )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "video_not_in_project")

    # --- /api/get-project -------------------------------------------------

    def test_get_project_returns_videos_and_statuses(self) -> None:
        project_root = self._make_project()
        desktop_server.handle_add_video_to_project(
            {
                "project_root": str(project_root),
                "video": str(self.video_a),
                "video_id": "clipA",
                "override": {"tts_voice": "voiceA"},
            }
        )
        desktop_server.handle_add_video_to_project(
            {"project_root": str(project_root), "video": str(self.video_b), "video_id": "clipB"}
        )
        status, payload = desktop_server.handle_get_project(
            {"project_root": str(project_root)}
        )
        self.assertEqual(status, HTTPStatus.OK)
        data = payload["data"]
        self.assertEqual(len(data["videos"]), 2)
        ids = sorted(v["video_id"] for v in data["videos"])
        self.assertEqual(ids, ["clipA", "clipB"])
        clipA = next(v for v in data["videos"] if v["video_id"] == "clipA")
        self.assertEqual(clipA["override"]["tts_voice"], "voiceA")
        self.assertEqual(clipA["resolved"]["tts_voice"], "voiceA")
        self.assertEqual(len(data["statuses"]), 2)

    def test_get_project_missing_root(self) -> None:
        status, payload = desktop_server.handle_get_project(
            {"project_root": str(self.tmp_root / "nope")}
        )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "project_not_found")


if __name__ == "__main__":
    unittest.main()
