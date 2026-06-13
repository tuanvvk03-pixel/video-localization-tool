"""Phase 2 acceptance: JSON backend CLI for UI editor.

Covers:
- status / load / seed / save / mark-edited subcommands
- JSON envelope {ok, data|error}
- save via --from-file and via stdin
- load returns parsed cues with ms timestamps
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import voice_edit_cli


SAMPLE_VOICE_SRT = (
    "1\n00:00:00,000 --> 00:00:02,000\nXin chao the gioi\n\n"
    "2\n00:00:02,000 --> 00:00:04,000\nCau hai\n\n"
)


def _run(argv: list[str], *, stdin: str = "") -> tuple[int, dict]:
    buf_out = io.StringIO()
    buf_in = io.StringIO(stdin)
    with contextlib.redirect_stdout(buf_out):
        orig_stdin = sys.stdin
        sys.stdin = buf_in
        try:
            rc = voice_edit_cli.main(argv)
        finally:
            sys.stdin = orig_stdin
    lines = [ln for ln in buf_out.getvalue().splitlines() if ln.strip()]
    payload = json.loads(lines[-1]) if lines else {}
    return rc, payload


class Phase2VoiceEditCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="phase2_voice_edit_cli_"))
        self.jw = self.tmp_root / "job"
        (self.jw / "artifacts" / "translate").mkdir(parents=True)
        (self.jw / "artifacts" / "transcribe").mkdir(parents=True)
        (self.jw / "input").mkdir(parents=True)
        (self.jw / "artifacts" / "translate" / "translated_voice.srt").write_text(
            SAMPLE_VOICE_SRT, encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_status_before_seed_reports_not_started(self) -> None:
        rc, payload = _run(["status", "--job-workspace", str(self.jw)])
        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["voice_edit_status"], "not_started")
        self.assertFalse(payload["data"]["voice_edited"])
        self.assertEqual(payload["data"]["source_mode"], "translated_voice")
        self.assertIsNone(payload["data"]["edited_voice_path"])
        self.assertIsNotNone(payload["data"]["translated_voice_path"])

    def test_load_returns_parsed_cues_from_translated_voice(self) -> None:
        rc, payload = _run(["load", "--job-workspace", str(self.jw)])
        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["source_mode"], "translated_voice")
        cues = payload["data"]["cues"]
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0]["start_ms"], 0)
        self.assertEqual(cues[0]["end_ms"], 2000)
        self.assertEqual(cues[0]["text"], "Xin chao the gioi")

    def test_load_missing_returns_error(self) -> None:
        empty_jw = self.tmp_root / "empty"
        empty_jw.mkdir()
        rc, payload = _run(["load", "--job-workspace", str(empty_jw)])
        self.assertEqual(rc, 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "voice_subtitle_missing")

    def test_seed_then_status_is_pending_and_load_uses_edited(self) -> None:
        rc, payload = _run(["seed", "--job-workspace", str(self.jw)])
        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertTrue(Path(payload["data"]["edited_voice_path"]).is_file())

        rc, payload = _run(["status", "--job-workspace", str(self.jw)])
        self.assertEqual(payload["data"]["voice_edit_status"], "voice_edit_pending")
        self.assertEqual(payload["data"]["source_mode"], "edited_voice")

        rc, payload = _run(["load", "--job-workspace", str(self.jw)])
        self.assertEqual(payload["data"]["source_mode"], "edited_voice")

    def test_save_via_stdin_writes_content(self) -> None:
        _run(["seed", "--job-workspace", str(self.jw)])
        edited_text = SAMPLE_VOICE_SRT.replace("Xin chao the gioi", "Xin chao (da sua)")
        rc, payload = _run(["save", "--job-workspace", str(self.jw)], stdin=edited_text)
        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        path = Path(payload["data"]["edited_voice_path"])
        self.assertIn("(da sua)", path.read_text(encoding="utf-8"))

    def test_save_via_from_file(self) -> None:
        _run(["seed", "--job-workspace", str(self.jw)])
        src = self.tmp_root / "user_edit.srt"
        edited_text = SAMPLE_VOICE_SRT.replace("Cau hai", "Cau hai (sua)")
        src.write_text(edited_text, encoding="utf-8")
        rc, payload = _run(
            ["save", "--job-workspace", str(self.jw), "--from-file", str(src)]
        )
        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        content = Path(payload["data"]["edited_voice_path"]).read_text(encoding="utf-8")
        self.assertIn("(sua)", content)

    def test_save_without_stdin_or_file_errors(self) -> None:
        _run(["seed", "--job-workspace", str(self.jw)])
        rc, payload = _run(["save", "--job-workspace", str(self.jw)], stdin="")
        self.assertEqual(rc, 1)
        self.assertEqual(payload["error"]["code"], "empty_payload")

    def test_mark_edited_flips_state(self) -> None:
        _run(["seed", "--job-workspace", str(self.jw)])
        edited_text = SAMPLE_VOICE_SRT.replace("Xin chao the gioi", "Xin chao (ok)")
        _run(["save", "--job-workspace", str(self.jw)], stdin=edited_text)
        rc, payload = _run(["mark-edited", "--job-workspace", str(self.jw)])
        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["data"]["voice_edited"])
        self.assertEqual(payload["data"]["voice_edit_status"], "voice_edited")

    def test_mark_edited_without_seed_errors(self) -> None:
        rc, payload = _run(["mark-edited", "--job-workspace", str(self.jw)])
        self.assertEqual(rc, 1)
        self.assertEqual(payload["error"]["code"], "mark_failed")


if __name__ == "__main__":
    unittest.main()
