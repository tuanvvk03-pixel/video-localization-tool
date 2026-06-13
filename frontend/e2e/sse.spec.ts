import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test, expect } from "@playwright/test";

// Phase C — verifies the live-progress SSE endpoint end to end: a real browser
// EventSource against the real server receives a `progress` frame (carrying the
// /api/job-progress-shaped payload + log_tail) and then a terminal `done` frame,
// after which the server closes the stream. Self-contained: writes a throwaway
// job workspace fixture (job_state.json with a terminal lifecycle), so no real
// pipeline run is needed. This replaces the one-off smoke with regression cover.

function makeWorkspace(state: Record<string, unknown>): string {
  const ws = mkdtempSync(join(tmpdir(), "vl-sse-"));
  writeFileSync(join(ws, "job_state.json"), JSON.stringify(state));
  writeFileSync(join(ws, "video_state.json"), "{}");
  writeFileSync(join(ws, "run.log"), "line one\nline two\n");
  return ws;
}

test("sse: /api/job-events streams progress + done for a terminal job", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(e.message));
  // `failed` is a terminal lifecycle, so the generator emits progress then done.
  const ws = makeWorkspace({ status: "failed", current_stage: "rendered", last_error: "e2e" });
  try {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    const result = await page.evaluate(
      (wsPath) =>
        new Promise<{ events: Array<{ t: string; lifecycle?: string; hasLog?: boolean }>; err?: string }>((resolve) => {
          const events: Array<{ t: string; lifecycle?: string; hasLog?: boolean }> = [];
          const es = new EventSource(`/api/job-events?job_workspace=${encodeURIComponent(wsPath)}`);
          const finish = (r: { events: typeof events; err?: string }) => {
            try { es.close(); } catch { /* noop */ }
            resolve(r);
          };
          es.addEventListener("progress", (e) => {
            try {
              const d = JSON.parse((e as MessageEvent).data);
              events.push({ t: "progress", lifecycle: d.lifecycle, hasLog: Array.isArray(d.log_tail) });
            } catch { events.push({ t: "progress" }); }
          });
          es.addEventListener("done", () => { events.push({ t: "done" }); finish({ events }); });
          es.onerror = () => finish({ events, err: "eventsource error before done" });
          setTimeout(() => finish({ events, err: "timeout" }), 12_000);
        }),
      ws,
    );

    const progress = result.events.find((e) => e.t === "progress");
    expect(progress, `events: ${JSON.stringify(result.events)} err=${result.err ?? ""}`).toBeTruthy();
    expect(progress?.hasLog).toBe(true);
    expect(result.events.some((e) => e.t === "done")).toBe(true);
    expect(pageErrors, `page errors:\n${pageErrors.join("\n")}`).toEqual([]);
  } finally {
    rmSync(ws, { recursive: true, force: true });
  }
});
