"""Phase 13 — mix_duck_gain_db field on TTS settings.

Validates round-trip persistence and clamping for the duck-gain slider's
backing field introduced in Phase J of the finalization roadmap.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from http import HTTPStatus
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desktop import server as desktop_server  # noqa: E402
from engine.tts_settings import (  # noqa: E402
    TTSSettingsError,
    load_video_tts_override,
    save_video_tts_override,
    validate_settings,
)


class MixDuckGainValidationTest(unittest.TestCase):
    def test_accepts_field_within_range(self) -> None:
        cleaned = validate_settings({"mix_duck_gain_db": -12.5})
        self.assertEqual(cleaned["mix_duck_gain_db"], -12.5)

    def test_accepts_zero_db_upper_bound(self) -> None:
        cleaned = validate_settings({"mix_duck_gain_db": 0.0})
        self.assertEqual(cleaned["mix_duck_gain_db"], 0.0)

    def test_accepts_minus_30_db_lower_bound(self) -> None:
        cleaned = validate_settings({"mix_duck_gain_db": -30.0})
        self.assertEqual(cleaned["mix_duck_gain_db"], -30.0)

    def test_rejects_value_above_zero(self) -> None:
        with self.assertRaises(TTSSettingsError):
            validate_settings({"mix_duck_gain_db": 5.0})

    def test_rejects_value_below_minus_30(self) -> None:
        with self.assertRaises(TTSSettingsError):
            validate_settings({"mix_duck_gain_db": -40.0})

    def test_rejects_non_numeric(self) -> None:
        with self.assertRaises(TTSSettingsError):
            validate_settings({"mix_duck_gain_db": "loud"})

    def test_omits_field_when_absent(self) -> None:
        cleaned = validate_settings({"tts_voice": "vi-VN-HoaiMyNeural"})
        self.assertNotIn("mix_duck_gain_db", cleaned)

    def test_treats_none_as_absent(self) -> None:
        cleaned = validate_settings({"mix_duck_gain_db": None})
        self.assertNotIn("mix_duck_gain_db", cleaned)


class MixDuckGainRoundTripTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="phase13_duck_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_save_then_load_round_trips_field(self) -> None:
        save_video_tts_override(
            self.tmp,
            {
                "tts_provider": "edge_tts",
                "tts_voice": "vi-VN-HoaiMyNeural",
                "mix_mode": "duck_original_speech",
                "mix_duck_gain_db": -7.5,
            },
        )
        settings = load_video_tts_override(self.tmp)
        self.assertEqual(settings["mix_duck_gain_db"], -7.5)
        self.assertEqual(settings["mix_mode"], "duck_original_speech")
        self.assertEqual(settings["tts_voice"], "vi-VN-HoaiMyNeural")


class MixDuckGainEndpointTest(unittest.TestCase):
    """Phase J persists the slider via the existing /api/save-video-tts route."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="phase13_endpoint_"))
        self.jw = self.tmp / "job-duck"
        (self.jw / "input").mkdir(parents=True, exist_ok=True)
        (self.jw / "input" / "source.mp4").write_bytes(b"\x00FAKE")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_save_video_tts_persists_mix_duck_gain_db(self) -> None:
        status, payload = desktop_server.handle_save_video_tts(
            {
                "job_workspace": str(self.jw),
                "settings": {
                    "tts_provider": "edge_tts",
                    "tts_voice": "vi-VN-HoaiMyNeural",
                    "mix_mode": "duck_original_speech",
                    "mix_duck_gain_db": -9.0,
                },
            }
        )
        self.assertEqual(status, HTTPStatus.OK, payload)
        self.assertEqual(
            payload["data"]["settings"]["mix_duck_gain_db"], -9.0
        )

        status, payload = desktop_server.handle_get_video_tts(
            {"job_workspace": str(self.jw)}
        )
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(
            payload["data"]["settings"]["mix_duck_gain_db"], -9.0
        )
        self.assertEqual(
            payload["data"]["settings"]["mix_mode"], "duck_original_speech"
        )

    def test_save_video_tts_rejects_out_of_range_gain(self) -> None:
        status, payload = desktop_server.handle_save_video_tts(
            {
                "job_workspace": str(self.jw),
                "settings": {"mix_duck_gain_db": 12.0},
            }
        )
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(payload["error"]["code"], "invalid_tts_settings")


if __name__ == "__main__":
    unittest.main()
