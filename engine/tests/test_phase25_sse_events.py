"""Phase C — SSE job-event stream (desktop/server_events.py).

Tests the frame generator deterministically by injecting sleep/monotonic, so no
real timing or server boot is needed. The HTTP endpoint (_serve_job_events) is
exercised live in the manual/Playwright smoke; here we pin the core logic.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from desktop.server_events import iter_job_event_frames


def _clock(values):
    """Return a monotonic() stub yielding the given values, then repeating the last."""
    seq = list(values)
    state = {"i": 0}

    def _next() -> float:
        i = state["i"]
        if i < len(seq):
            state["i"] = i + 1
            return float(seq[i])
        return float(seq[-1])

    return _next


def _parse_frames(frames):
    """Split SSE byte frames into (event, data_or_None) tuples."""
    out = []
    for raw in frames:
        text = raw.decode("utf-8")
        if text.startswith(":"):
            out.append(("ping", None))
            continue
        event = ""
        data = None
        for line in text.strip().splitlines():
            if line.startswith("event: "):
                event = line[len("event: "):]
            elif line.startswith("data: "):
                data = json.loads(line[len("data: "):])
        out.append((event, data))
    return out


class SseEventFrameTest(unittest.TestCase):
    def _write_state(self, jw: Path, state: dict) -> None:
        (jw / "job_state.json").write_text(json.dumps(state), encoding="utf-8")

    def test_completed_job_emits_progress_then_done(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            self._write_state(jw, {"status": "rendered", "current_stage": "rendered", "runner": {"to_stage": "rendered"}})
            frames = list(
                iter_job_event_frames(jw, sleep=lambda _s: None, monotonic=_clock([0, 0]))
            )
        parsed = _parse_frames(frames)
        events = [e for e, _ in parsed]
        self.assertEqual(events, ["progress", "done"])
        # The done payload carries the terminal lifecycle.
        self.assertEqual(parsed[-1][1]["lifecycle"], "completed")
        self.assertEqual(parsed[0][1]["lifecycle"], "completed")

    def test_running_job_heartbeats_then_caps_at_max_runtime(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            self._write_state(
                jw,
                {"status": "running", "current_stage": "transcribed", "runner": {"to_stage": "rendered"}},
            )
            frames = list(
                iter_job_event_frames(
                    jw,
                    max_runtime_s=20.0,
                    heartbeat_s=15.0,
                    sleep=lambda _s: None,
                    monotonic=_clock([0, 0, 16, 25]),
                )
            )
        events = [e for e, _ in _parse_frames(frames)]
        # First a live progress frame, a heartbeat while unchanged, then a final done.
        self.assertEqual(events[0], "progress")
        self.assertIn("ping", events)
        self.assertEqual(events[-1], "done")

    def test_progress_payload_includes_log_tail(self) -> None:
        with TemporaryDirectory() as d:
            jw = Path(d)
            self._write_state(jw, {"status": "rendered", "current_stage": "rendered", "runner": {"to_stage": "rendered"}})
            (jw / "run.log").write_text("line one\nline two\n", encoding="utf-8")
            frames = list(
                iter_job_event_frames(jw, sleep=lambda _s: None, monotonic=_clock([0, 0]))
            )
        first = _parse_frames(frames)[0][1]
        self.assertIn("log_tail", first)
        self.assertEqual(first["log_tail"], ["line one", "line two"])
        self.assertIn("overall_percent", first)


if __name__ == "__main__":
    unittest.main()
