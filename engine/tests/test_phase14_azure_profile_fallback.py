from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.run_tts_stage import _synthesize_all  # noqa: E402
from engine.srt_cues import SRTCue  # noqa: E402


class AzureProfileFallbackTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="phase14_azure_profiles_"))
        self.cues_dir = self.tmp / "artifacts" / "tts" / "cues"
        self.cues_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    async def test_switches_to_backup_profile_and_keeps_using_it(self) -> None:
        calls: list[str] = []

        class FakeProvider:
            async def synthesize_cue_to_wav(
                self,
                text,
                out_wav,
                *,
                voice,
                rate,
                diag_prefix="",
                provider_config=None,
            ):
                del text, voice, rate, diag_prefix
                label = str((provider_config or {}).get("label") or "default")
                calls.append(label)
                if label == "app:primary":
                    raise RuntimeError("server busy")
                out_wav.write_bytes(b"RIFFFAKE")
                return 777

        configs = [
            {"label": "app:primary", "key": "k1", "region": "southeastasia"},
            {"label": "app:secondary", "key": "k2", "region": "eastasia"},
        ]
        cues = [
            SRTCue(index=1, start_ms=0, end_ms=1000, text="Xin chao"),
            SRTCue(index=2, start_ms=1000, end_ms=2000, text="The gioi"),
        ]

        with mock.patch("engine.run_tts_stage.get_tts_provider", return_value=FakeProvider()):
            manifest = await _synthesize_all(
                self.tmp,
                cues,
                "azure_tts",
                "vi-VN-HoaiMyNeural",
                "+0%",
                self.cues_dir,
                previous_cue_entries={},
                provider_configs=configs,
            )

        self.assertEqual(
            calls,
            ["app:primary", "app:primary", "app:secondary", "app:secondary"],
        )
        self.assertEqual(
            [cue["provider_profile"] for cue in manifest],
            ["app:secondary", "app:secondary"],
        )


if __name__ == "__main__":
    unittest.main()
