from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import runtime_app_settings  # noqa: E402
from engine.block_translate import translate_blocks_two_pass  # noqa: E402
from engine.srt_cues import SRTCue  # noqa: E402


class TranslationPolishPassTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="phase15_translation_"))
        self.glossary = self.tmp / "glossary.json"
        self.glossary.write_text(json.dumps({"version": 1}), encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_block_polish_pass_replaces_literal_draft(self) -> None:
        cues = [
            SRTCue(index=1, start_ms=0, end_ms=1000, text="你不是普通的废物"),
            SRTCue(index=2, start_ms=1000, end_ms=2000, text="是从小看动漫长大的废物"),
        ]
        raw = {
            "cues": [
                {
                    "index": 1,
                    "display": "Em khong phai nguoi vo dung binh thuong",
                    "voice": "Em khong phai nguoi vo dung binh thuong",
                    "confidence": 0.51,
                },
                {
                    "index": 2,
                    "display": "La dua tre me anime tu nho",
                    "voice": "La dua tre me anime tu nho",
                    "confidence": 0.51,
                },
            ]
        }
        polished = {
            "cues": [
                {
                    "index": 1,
                    "display": "Em dau phai loai vo dung binh thuong",
                    "voice": "Em dau phai loai vo dung binh thuong",
                    "confidence": 0.9,
                },
                {
                    "index": 2,
                    "display": "ma la kieu me anime tu be den gio",
                    "voice": "ma la kieu me anime tu be den gio",
                    "confidence": 0.9,
                },
            ]
        }

        with mock.patch(
            "engine.block_translate._call_openai_chat_json",
            side_effect=[raw, polished],
        ):
            results, qa, meta = translate_blocks_two_pass(
                cues=cues,
                api_key="sk-test",
                model="gpt-test",
                glossary_path=self.glossary,
                block_size=8,
                context_cues=1,
                qa_enabled=False,
            )

        self.assertEqual(results[1].display, "Em dau phai loai vo dung binh thuong")
        self.assertEqual(results[2].voice, "ma la kieu me anime tu be den gio")
        self.assertEqual(qa, [])
        self.assertTrue(meta["blocks"][0]["polish_applied"])

    def test_block_polish_failure_falls_back_to_initial_draft(self) -> None:
        cues = [SRTCue(index=1, start_ms=0, end_ms=1000, text="店长")]
        raw = {
            "cues": [
                {
                    "index": 1,
                    "display": "Quan ly",
                    "voice": "Quan ly oi",
                    "confidence": 0.6,
                }
            ]
        }

        with mock.patch(
            "engine.block_translate._call_openai_chat_json",
            side_effect=[
                raw,
                {"cues": []},
            ],
        ):
            results, qa, meta = translate_blocks_two_pass(
                cues=cues,
                api_key="sk-test",
                model="gpt-test",
                glossary_path=self.glossary,
                block_size=8,
                context_cues=1,
                qa_enabled=False,
            )

        self.assertEqual(results[1].display, "Quan ly")
        self.assertEqual(results[1].voice, "Quan ly oi")
        self.assertEqual(qa, [])
        self.assertFalse(meta["blocks"][0]["polish_applied"])


class TranslationModelResolutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="phase15_model_"))
        self.settings_path = self.tmp / "app_settings.json"
        self.orig_path = runtime_app_settings.app_settings_path
        runtime_app_settings.app_settings_path = lambda: self.settings_path  # type: ignore[assignment]

    def tearDown(self) -> None:
        runtime_app_settings.app_settings_path = self.orig_path  # type: ignore[assignment]
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_saved_model_overrides_default(self) -> None:
        self.settings_path.write_text(
            json.dumps({"openai_translation_model": "gpt-4.1-mini"}, ensure_ascii=False),
            encoding="utf-8",
        )
        with mock.patch.dict(os.environ, {}, clear=False):
            self.assertEqual(
                runtime_app_settings.resolve_openai_translation_model(),
                "gpt-4.1-mini",
            )

    def test_env_model_used_when_setting_missing(self) -> None:
        with mock.patch.dict(os.environ, {"OPENAI_TRANSLATION_MODEL": "gpt-env"}, clear=False):
            self.assertEqual(
                runtime_app_settings.resolve_openai_translation_model(),
                "gpt-env",
            )

    def test_default_model_is_gpt_5_4(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                runtime_app_settings.resolve_openai_translation_model(),
                "gpt-5.4",
            )


if __name__ == "__main__":
    unittest.main()
