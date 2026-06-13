import { readdirSync } from "node:fs";
import { resolve } from "node:path";
import { test, expect } from "@playwright/test";

// End-to-end AUTO run from the migrated Settings screen: transcribe + translate
// (real OpenAI) + seed voice edit, then the voice-edit gate should appear.
// Skips when no OpenAI key is configured.
const BASE = "http://127.0.0.1:8791";
const REPO = resolve(import.meta.dirname, "..", "..");
const TEST_DIR = resolve(REPO, "test");

function findVideo(): string | null {
  try {
    const f = readdirSync(TEST_DIR).find((n) => /\.(mp4|mov|mkv|webm)$/i.test(n));
    return f ? resolve(TEST_DIR, f) : null;
  } catch { return null; }
}

test("run (auto) transcribes + translates the video and opens the voice-edit gate", async ({ page, playwright }) => {
  test.setTimeout(180_000);
  const video = findVideo();
  // Stale for the current linear app: navigates via the removed dashboard
  // ("open job by name") to reach Settings. Needs a rewrite (test seam to set
  // jobWorkspace + jump to the Settings step). Body kept as a template.
  // See docs/14 §A (e2e debt).
  test.skip(true, "needs rework for linear app: no in-browser job-reopen to reach Settings");
  void video;

  const rc = await playwright.request.newContext({ baseURL: BASE });
  const key = await (await rc.post("/api/check-openai-key", { data: {} })).json();
  test.skip(!key?.data?.has_key, "no OpenAI key configured; cannot run auto translate");

  // Fresh job in auto mode (default).
  const init = await (await rc.post("/api/init-job", { data: { video } })).json();
  const workspaceRoot: string = init.data.workspace_root;
  const jobWorkspace: string = init.data.job_workspace;
  const jobName = String(jobWorkspace).split(/[\\/]/).pop() || "";
  await rc.dispose();

  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));

  await page.addInitScript((root) => window.localStorage.setItem("workspace_root", root as string), workspaceRoot);
  await page.goto("/");
  await page.getByText(jobName, { exact: false }).first().click();
  await page.locator(".edit-step-pill").nth(1).click();
  await expect(page.getByTestId("settings-screen")).toBeVisible({ timeout: 20_000 });

  // Run button should be in auto mode for a fresh job.
  await page.getByTestId("run-until-edit").click();

  // After transcribe+translate+seed, the auto path opens the voice-edit gate.
  await expect(page.locator(".voice-edit-gate-backdrop")).toBeVisible({ timeout: 150_000 });

  // Backend produced the translated + seeded voice artifacts.
  const arts = await (await page.request.post("/api/list-artifacts", { data: { job_workspace: jobWorkspace } })).json();
  const rels = (arts?.data?.canonical || []).filter((a: any) => a.exists).map((a: any) => a.rel_path);
  expect(rels).toContain("artifacts/translate/translated_voice.srt");
  expect(rels).toContain("artifacts/edit/edited_voice.srt");
  expect(errors).toEqual([]);
});
