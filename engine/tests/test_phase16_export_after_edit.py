from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import run_job, run_tts_stage


SAMPLE_SOURCE_SRT = "1\n00:00:00,000 --> 00:00:01,000\nni hao\n\n"
SAMPLE_VOICE_SRT = "1\n00:00:00,000 --> 00:00:01,000\nxin chao\n\n"


class ExportAfterEditRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="phase16_export_after_edit_"))
        self.jw = self.tmp / "job"
        (self.jw / "input").mkdir(parents=True)
        (self.jw / "artifacts" / "transcribe").mkdir(parents=True)
        (self.jw / "artifacts" / "translate").mkdir(parents=True)
        (self.jw / "artifacts" / "edit").mkdir(parents=True)
        (self.jw / "input" / "source.mp4").write_bytes(b"video")
        (self.jw / "artifacts" / "transcribe" / "source.srt").write_text(
            SAMPLE_SOURCE_SRT, encoding="utf-8"
        )
        (self.jw / "artifacts" / "translate" / "translated_voice.srt").write_text(
            SAMPLE_VOICE_SRT, encoding="utf-8"
        )
        (self.jw / "artifacts" / "edit" / "edited_voice.srt").write_text(
            SAMPLE_VOICE_SRT.replace("xin chao", "xin chao da duyet"),
            encoding="utf-8",
        )
        self._write_voice_approved_state()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_voice_approved_state(self) -> None:
        job_state = {
            "status": "voice_edited",
            "current_stage": "voice_edited",
            "voice_edit_status": "voice_edited",
            "voice_edited": True,
        }
        video_state = {
            "status": "voice_edited",
            "current_stage": "voice_edited",
            "voice_edit_status": "voice_edited",
            "voice_edited": True,
        }
        (self.jw / "job_state.json").write_text(
            json.dumps(job_state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (self.jw / "video_state.json").write_text(
            json.dumps(video_state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_run_job_reuses_approved_edited_voice_without_rerunning_translate(self) -> None:
        calls: list[str] = []

        def _stub(name: str):
            def _inner(argv: list[str]) -> int:
                calls.append(name)
                if name == "finalize":
                    final_srt = self.jw / "artifacts" / "translate" / "final_subtitle.srt"
                    final_srt.write_text(
                        SAMPLE_VOICE_SRT.replace("xin chao", "xin chao da duyet"),
                        encoding="utf-8",
                    )
                return 0

            return _inner

        with (
            mock.patch.object(
                run_job.run_translate_stage,
                "main",
                side_effect=AssertionError("translate should not run after voice approval"),
            ),
            mock.patch.object(run_job.run_finalize_subtitle_stage, "main", side_effect=_stub("finalize")),
            mock.patch.object(run_job.run_tts_stage, "main", side_effect=_stub("tts")),
            mock.patch.object(run_job.run_compact_tts_stage, "main", side_effect=_stub("compact")),
            mock.patch.object(run_job.run_align_stage, "main", side_effect=_stub("align")),
            mock.patch.object(run_job.run_mix_stage, "main", side_effect=_stub("mix")),
            mock.patch.object(run_job.run_render_stage, "main", side_effect=_stub("render")),
        ):
            rc = run_job.main(
                [
                    "--job-workspace",
                    str(self.jw),
                    "--project-name",
                    "demo",
                    "--to-stage",
                    "rendered",
                    "--finalize-mode",
                    "voice",
                ]
            )

        self.assertEqual(rc, 0)
        self.assertEqual(calls, ["finalize", "tts", "compact", "align", "mix", "render"])

    def test_edge_tts_main_passes_empty_provider_configs(self) -> None:
        final_srt = self.jw / "artifacts" / "translate" / "final_subtitle.srt"
        final_srt.write_text(SAMPLE_VOICE_SRT, encoding="utf-8")
        captured: dict[str, object] = {}

        async def _fake_synthesize_all(
            job_workspace,
            cues,
            provider_key,
            voice,
            rate,
            cues_dir,
            *,
            previous_cue_entries,
            provider_configs,
            voice_overrides=None,
        ):
            del job_workspace, cues, provider_key, voice, rate, cues_dir, previous_cue_entries, voice_overrides
            captured["provider_configs"] = list(provider_configs)
            return [{"index": 1, "provider_profile": "default"}]

        with (
            mock.patch.dict(sys.modules, {"edge_tts": mock.Mock()}),
            mock.patch.object(run_tts_stage, "resolve_ffmpeg_executable", return_value=("ffmpeg", "")),
            mock.patch.object(run_tts_stage, "stale_final_subtitle_message", return_value=None),
            mock.patch.object(run_tts_stage, "_synthesize_all", side_effect=_fake_synthesize_all),
        ):
            rc = run_tts_stage.main(
                [
                    "--job-workspace",
                    str(self.jw),
                    "--tts-provider",
                    "edge_tts",
                ]
            )

        self.assertEqual(rc, 0)
        self.assertEqual(captured.get("provider_configs"), [])
        manifest = json.loads(
            (self.jw / "artifacts" / "tts" / "tts_manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest.get("provider_profiles_available"), [])


if __name__ == "__main__":
    unittest.main()
