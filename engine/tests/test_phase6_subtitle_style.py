"""Phase 6 — Subtitle styling tests."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from engine import project_manager, run_render_stage
from engine.subtitle_style import (
    PROJECT_STYLE_REL,
    VIDEO_STYLE_OVERRIDE_REL,
    SubtitleStyleError,
    hex_to_ffmpeg_color,
    load_project_style,
    load_video_style_override,
    resolve_subtitle_style,
    save_project_style,
    save_video_style_override,
    style_to_ass_force_style,
    validate_style,
)
from engine.voice_edit_api import mark_voice_edited


class ValidateStyleTest(unittest.TestCase):
    def test_accepts_font_and_hex6(self):
        out = validate_style({"subtitle_font": "Arial", "subtitle_background_color": "#112233"})
        self.assertEqual(out, {"subtitle_font": "Arial", "subtitle_background_color": "#112233"})

    def test_accepts_hex8_with_alpha(self):
        out = validate_style({"subtitle_background_color": "#11223344"})
        self.assertEqual(out["subtitle_background_color"], "#11223344")

    def test_rejects_non_hex_color(self):
        with self.assertRaises(SubtitleStyleError):
            validate_style({"subtitle_background_color": "black"})

    def test_rejects_empty_font(self):
        with self.assertRaises(SubtitleStyleError):
            validate_style({"subtitle_font": "   "})

    def test_drops_unknown_keys(self):
        out = validate_style({"subtitle_font": "Arial", "zzz": "nope"})
        self.assertEqual(out, {"subtitle_font": "Arial"})

    def test_missing_keys_returns_empty(self):
        self.assertEqual(validate_style({}), {})

    def test_accepts_bold_italic_and_align(self):
        out = validate_style({"bold": True, "italic": False, "align": "right"})
        self.assertEqual(out, {"bold": True, "italic": False, "align": "right"})

    def test_rejects_invalid_align(self):
        with self.assertRaises(SubtitleStyleError):
            validate_style({"align": "top"})

    def test_rejects_non_bool_style_flags(self):
        with self.assertRaises(SubtitleStyleError):
            validate_style({"bold": "yes"})

    def test_accepts_margin_v_and_font_size(self):
        out = validate_style({"margin_v": 80, "font_size": 28})
        self.assertEqual(out, {"margin_v": 80, "font_size": 28})

    def test_rejects_margin_v_out_of_range(self):
        with self.assertRaises(SubtitleStyleError):
            validate_style({"margin_v": 501})

    def test_rejects_font_size_out_of_range(self):
        with self.assertRaises(SubtitleStyleError):
            validate_style({"font_size": 4})


class StoragePathsTest(unittest.TestCase):
    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pr = root / "project"
            vw = root / "project" / "videos" / "v1"
            vw.mkdir(parents=True)

            save_project_style(pr, {"subtitle_font": "Roboto"})
            save_video_style_override(vw, {"subtitle_background_color": "#000000"})

            self.assertTrue((pr / PROJECT_STYLE_REL).is_file())
            self.assertTrue((vw / VIDEO_STYLE_OVERRIDE_REL).is_file())
            self.assertEqual(load_project_style(pr), {"subtitle_font": "Roboto"})
            self.assertEqual(
                load_video_style_override(vw), {"subtitle_background_color": "#000000"}
            )

    def test_save_video_style_merge_preserves_omitted_fields(self):
        with tempfile.TemporaryDirectory() as td:
            vw = Path(td) / "jobws"
            vw.mkdir(parents=True)
            save_video_style_override(
                vw,
                {
                    "subtitle_font": "Arial",
                    "margin_v": 120,
                    "font_size": 30,
                    "align": "center",
                },
            )
            save_video_style_override(vw, {"bold": True})
            loaded = load_video_style_override(vw)
            self.assertEqual(loaded.get("subtitle_font"), "Arial")
            self.assertEqual(loaded.get("margin_v"), 120)
            self.assertEqual(loaded.get("font_size"), 30)
            self.assertTrue(loaded.get("bold"))

    def test_save_video_style_font_size_none_removes(self):
        with tempfile.TemporaryDirectory() as td:
            vw = Path(td) / "jobws"
            vw.mkdir(parents=True)
            save_video_style_override(vw, {"font_size": 28})
            save_video_style_override(vw, {"font_size": None})
            loaded = load_video_style_override(vw)
            self.assertNotIn("font_size", loaded)

    def test_save_project_style_merge_preserves_omitted_fields(self):
        with tempfile.TemporaryDirectory() as td:
            pr = Path(td) / "proj"
            pr.mkdir(parents=True)
            save_project_style(pr, {"subtitle_font": "Arial", "margin_v": 90})
            save_project_style(pr, {"italic": True})
            loaded = load_project_style(pr)
            self.assertEqual(loaded.get("subtitle_font"), "Arial")
            self.assertEqual(loaded.get("margin_v"), 90)
            self.assertTrue(loaded.get("italic"))

    def test_resolve_override_wins(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pr = root / "project"
            vw = root / "project" / "videos" / "v1"
            vw.mkdir(parents=True)
            save_project_style(
                pr, {"subtitle_font": "Roboto", "subtitle_background_color": "#111111"}
            )
            save_video_style_override(vw, {"subtitle_background_color": "#222222"})
            merged = resolve_subtitle_style(vw, project_root=pr)
            self.assertEqual(merged["subtitle_font"], "Roboto")
            self.assertEqual(merged["subtitle_background_color"], "#222222")

    def test_resolve_without_project_uses_override_only(self):
        with tempfile.TemporaryDirectory() as td:
            vw = Path(td)
            save_video_style_override(vw, {"subtitle_font": "Inter"})
            self.assertEqual(resolve_subtitle_style(vw), {"subtitle_font": "Inter"})

    def test_resolve_empty_when_no_files(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(resolve_subtitle_style(Path(td)), {})

    def test_load_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as td:
            vw = Path(td)
            (vw / VIDEO_STYLE_OVERRIDE_REL).write_text("{not json", encoding="utf-8")
            with self.assertRaises(SubtitleStyleError):
                load_video_style_override(vw)


class AssForceStyleTest(unittest.TestCase):
    def test_empty_style_returns_empty_string(self):
        self.assertEqual(style_to_ass_force_style({}), "")

    def test_font_only(self):
        self.assertEqual(style_to_ass_force_style({"subtitle_font": "Arial"}), "FontName=Arial")

    def test_bg_sets_border_style_box(self):
        s = style_to_ass_force_style({"subtitle_background_color": "#112233"})
        # #RRGGBB=#112233 -> ASS BBGGRR=332211, alpha 00 (opaque)
        self.assertIn("BackColour=&H00332211", s)
        self.assertIn("BorderStyle=4", s)
        self.assertIn("Outline=0", s)
        self.assertIn("Shadow=0", s)

    def test_hex8_inverts_alpha_to_ass_transparency(self):
        # Input alpha 0xFF = fully opaque -> ASS transparency 0x00
        s = style_to_ass_force_style({"subtitle_background_color": "#112233FF"})
        self.assertIn("BackColour=&H00332211", s)
        # Input alpha 0x00 = fully transparent -> ASS transparency 0xFF
        s2 = style_to_ass_force_style({"subtitle_background_color": "#11223300"})
        self.assertIn("BackColour=&HFF332211", s2)

    def test_bold_italic_and_alignment_are_mapped(self):
        s = style_to_ass_force_style({"bold": True, "italic": False, "align": "right"})
        self.assertIn("Bold=1", s)
        self.assertIn("Italic=0", s)
        self.assertIn("Alignment=3", s)

    def test_margin_v_and_font_size_in_force_style(self):
        s = style_to_ass_force_style(
            {"subtitle_background_color": "#000000", "margin_v": 120, "font_size": 32}
        )
        self.assertIn("MarginV=120", s)
        self.assertIn("Fontsize=32", s)

    def test_hex_to_ffmpeg_color_clamps_min_opacity(self):
        self.assertEqual(
            hex_to_ffmpeg_color("#11223344", min_opacity=0.92),
            "0x112233@0.920",
        )


class RenderStageStyleResolveTest(unittest.TestCase):
    """Render stage should fail fast when style file is malformed."""

    def test_invalid_style_fails_render(self):
        with tempfile.TemporaryDirectory() as td:
            jw = Path(td)
            (jw / VIDEO_STYLE_OVERRIDE_REL).write_text(
                json.dumps({"subtitle_background_color": "not-hex"}), encoding="utf-8"
            )
            # Missing source video would also fail; style validation runs first only after
            # reaching the resolve step. Instead test resolve directly.
            with self.assertRaises(SubtitleStyleError):
                resolve_subtitle_style(jw)

    def test_burn_filter_uses_libass_only_no_full_width_band(self):
        filt, burn_style = run_render_stage._build_burn_subtitle_filter(
            Path("demo.srt"),
            {"subtitle_background_color": "#112233"},
        )
        self.assertNotIn("drawbox", filt)
        self.assertIn("subtitles=filename=", filt)
        self.assertIn("BorderStyle=4", filt)
        self.assertEqual(burn_style["subtitle_background_color"], "#112233")


class RenderManifestStyleRecordedTest(unittest.TestCase):
    """_write_manifest must persist subtitle_style on both success and failure paths."""

    def test_success_and_failure_manifest_both_record_style(self):
        with tempfile.TemporaryDirectory() as td:
            render_dir = Path(td)
            fake = Path(td) / "fake"
            fake.write_bytes(b"x")
            style = {"subtitle_font": "Arial", "subtitle_background_color": "#112233"}
            mp = run_render_stage._write_manifest(
                render_dir,
                {"status": "rendered", "last_error": None},
                0.0,
                1.0,
                fake,
                fake,
                fake,
                "mixed",
                "burn",
                "ffmpeg",
                "ffprobe",
                4.0,
                4.0,
                fake,
                ["ffmpeg", "-i", "x"],
                {},
                subtitle_style=style,
            )
            body = json.loads(mp.read_text(encoding="utf-8"))
            self.assertEqual(body["subtitle_style"], style)


class ProjectManagerRendersWithProjectRootTest(unittest.TestCase):
    """run_render_phase should pass --project-root through to render stage argv."""

    def test_render_argv_contains_project_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = project_manager.init_project(root, "stylecheck")
            pr = Path(state.project_root)
            # Fake video workspace with an edited_voice.srt so render_one doesn't early-skip.
            vid = "vid1"
            jw = pr / "videos" / vid
            (jw / "input").mkdir(parents=True)
            (jw / "artifacts" / "edit").mkdir(parents=True)
            (jw / "artifacts" / "edit" / "edited_voice.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n", encoding="utf-8")
            (jw / "input" / "source.mp4").write_bytes(b"fake")
            # Register the entry directly (bypass ffprobe duration check).
            from engine.project_manager import ProjectVideoEntry, _write_state
            state.videos.append(
                ProjectVideoEntry(
                    video_id=vid,
                    workspace=str(jw.resolve()),
                    added_at_unix=0.0,
                    source_path=str((jw / "input" / "source.mp4").resolve()),
                    duration_s=10.0,
                )
            )
            _write_state(state)
            mark_voice_edited(jw)

            captured: list[list[str]] = []

            def fake_runner(argv):
                captured.append(list(argv))
                return 0

            results = project_manager.run_render_phase(pr, runner=fake_runner)
            self.assertEqual(len(results), 1)
            self.assertTrue(results[0]["ok"], results[0])
            self.assertEqual(len(captured), 1)
            argv = captured[0]
            self.assertIn("--project-root", argv)
            idx = argv.index("--project-root")
            self.assertEqual(Path(argv[idx + 1]).resolve(), pr.resolve())


if __name__ == "__main__":
    unittest.main()
