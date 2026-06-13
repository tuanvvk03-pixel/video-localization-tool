"""Phase D — managed-mode bypass for the block_v2 translate preflight.

When the platform backend holds the OpenAI key (managed mode), run_translate_stage
must NOT fail-fast demanding a local key; the actual call is routed through the
cloud by block_translate._call_openai_chat_json. This pins that the preflight in
run_translate_stage.main() honours managed mode (mirroring run_cleanup_source_stage).
"""
from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import run_translate_stage

_SRT = "1\n00:00:00,000 --> 00:00:01,000\n你好\n"


def _make_workspace(d: str) -> Path:
    jw = Path(d)
    src = jw / "artifacts" / "transcribe" / "source.srt"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(_SRT, encoding="utf-8")
    return jw


def _env_without_openai_key() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}


def _argv(jw: Path) -> list[str]:
    return [
        "--job-workspace", str(jw),
        "--project-name", "test_proj",
        "--backend", "block_v2",
        "--source-mode", "raw",
    ]


class ManagedTranslatePreflightTest(unittest.TestCase):
    def test_managed_mode_skips_local_key_requirement(self) -> None:
        with TemporaryDirectory() as d:
            jw = _make_workspace(d)
            translate = mock.MagicMock(side_effect=ValueError("REACHED_TRANSLATE"))
            with (
                mock.patch.dict(os.environ, _env_without_openai_key(), clear=True),
                mock.patch("desktop.cloud_account.managed_enabled", return_value=True),
                mock.patch("engine.block_translate.translate_blocks_two_pass", translate),
            ):
                buf = io.StringIO()
                with redirect_stderr(buf):
                    rc = run_translate_stage.main(_argv(jw))
                err = buf.getvalue()
        # Reached the real translate call (no local key) -> preflight didn't block.
        self.assertTrue(translate.called, "translate was not reached; preflight blocked under managed mode")
        self.assertNotIn("Missing API key", err)
        self.assertEqual(rc, 1)  # our mock raised, but past the key gate

    def test_byok_off_still_requires_local_key(self) -> None:
        with TemporaryDirectory() as d:
            jw = _make_workspace(d)
            translate = mock.MagicMock(side_effect=ValueError("SHOULD_NOT_REACH"))
            with (
                mock.patch.dict(os.environ, _env_without_openai_key(), clear=True),
                mock.patch("desktop.cloud_account.managed_enabled", return_value=False),
                mock.patch("engine.block_translate.translate_blocks_two_pass", translate),
            ):
                buf = io.StringIO()
                with redirect_stderr(buf):
                    rc = run_translate_stage.main(_argv(jw))
                err = buf.getvalue()
        self.assertFalse(translate.called)
        self.assertIn("Missing API key", err)
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
