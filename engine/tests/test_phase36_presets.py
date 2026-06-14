"""Phase F3 — reusable config presets (engine.presets)."""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from engine import presets
from engine import render_settings as rs


class PresetsTest(unittest.TestCase):
    def test_save_list_apply_delete_roundtrip(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            presets_dir = root / "Presets"
            source = root / "proj"
            source.mkdir()
            target = root / "proj2"
            target.mkdir()
            # Author branding (logo + trim + transform) at the source project.
            logo = root / "brand.png"
            logo.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
            rs.import_render_logo_image(source, logo)
            rs.update_render_settings(source, {"aspect_ratio": "9:16", "tail_trim_sec": 2.0, "transform_hflip": True})

            with mock.patch.object(presets, "PRESETS_DIR", presets_dir):
                saved = presets.save_preset("My UA Preset", tts={"tts_voice": "vi-VN-NamMinh", "mix_mode": "keep_music_replace_voice"}, source_root=source)
                self.assertEqual(saved["tts"]["tts_voice"], "vi-VN-NamMinh")

                lst = presets.list_presets()
                self.assertEqual(len(lst), 1)
                pid = lst[0]["id"]
                self.assertIn("logo_path", lst[0]["render"])

                res = presets.apply_preset(pid, target)
                self.assertEqual(res["tts"]["mix_mode"], "keep_music_replace_voice")
                # Branding files + settings landed in the target.
                applied = rs.load_render_settings(target)
                self.assertIn("logo_path", applied)
                self.assertEqual(applied["aspect_ratio"], "9:16")
                self.assertTrue(applied.get("transform_hflip"))
                self.assertTrue((target / applied["logo_path"]).is_file())

                presets.delete_preset(pid)
                self.assertEqual(presets.list_presets(), [])

    def test_apply_unknown_raises(self) -> None:
        with TemporaryDirectory() as d:
            with mock.patch.object(presets, "PRESETS_DIR", Path(d) / "Presets"):
                with self.assertRaises(presets.PresetError):
                    presets.apply_preset("ghost", Path(d))

    def test_save_empty_name_raises(self) -> None:
        with TemporaryDirectory() as d:
            with mock.patch.object(presets, "PRESETS_DIR", Path(d) / "Presets"):
                with self.assertRaises(presets.PresetError):
                    presets.save_preset("  ", tts={}, source_root=Path(d))


if __name__ == "__main__":
    unittest.main()
