import { readdirSync } from "node:fs";
import { resolve } from "node:path";
import { test, expect } from "@playwright/test";

// Verifies the migrated Svelte Review (subtitle editor) screen. Drives a real
// auto run (transcribe + OpenAI translate + voice-edit seed) so the job has
// cues and the Review step is unlocked, then opens it and edits/saves a cue.
const BASE = "http://127.0.0.1:8791";
const REPO = resolve(import.meta.dirname, "..", "..");
const TEST_DIR = resolve(REPO, "test");

function findVideo(): string | null {
  try {
    const f = readdirSync(TEST_DIR).find((n) => /\.(mp4|mov|mkv|webm)$/i.test(n));
    return f ? resolve(TEST_DIR, f) : null;
  } catch { return null; }
}

test("review: edit + save a cue on the migrated subtitle editor", async ({ page, playwright }) => {
  test.setTimeout(180_000);
  const video = findVideo();
  // Stale for the current linear app: this drives "open an existing job by name"
  // (the removed dashboard) to reach Review. The new app has no in-browser
  // job-reopen path, so this needs a rewrite (e.g. a test seam that sets
  // jobWorkspace + jumps to the Review step). Skipped to avoid false failures.
  // Body kept as the rewrite template. See docs/14 §A (e2e debt).
  test.skip(true, "needs rework for linear app: no in-browser job-reopen to reach Review");
  void video;

  const rc = await playwright.request.newContext({ baseURL: BASE });
  const key = await (await rc.post("/api/check-openai-key", { data: {} })).json();
  test.skip(!key?.data?.has_key, "no OpenAI key; cannot produce cues via auto run");

  // Create a job and run auto to produce translated cues + seed the voice edit.
  const init = await (await rc.post("/api/init-job", { data: { video } })).json();
  const workspaceRoot: string = init.data.workspace_root;
  const jobWorkspace: string = init.data.job_workspace;
  const jobName = String(jobWorkspace).split(/[\\/]/).pop() || "";

  await rc.post("/api/run-until-edit", { data: { job_workspace: jobWorkspace, project_name: "t", use_auto_translate: true, async: true } });
  await expect.poll(async () => {
    const d = (await (await rc.post("/api/job-progress", { data: { job_workspace: jobWorkspace } })).json())?.data;
    return d?.job?.state;
  }, { timeout: 150_000, intervals: [2000] }).toBe("succeeded");
  await rc.dispose();

  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));

  // Open the job (lands on the edit wizard) and go to the Review step.
  await page.addInitScript((root) => window.localStorage.setItem("workspace_root", root as string), workspaceRoot);
  await page.goto("/");
  await page.getByText(jobName, { exact: false }).first().click();
  await page.locator(".edit-step-pill").nth(2).click();

  await expect(page.getByTestId("review-screen")).toBeVisible({ timeout: 20_000 });

  // The video player + cue editor rendered with at least one editable cue.
  await expect(page.locator(".review-video")).toBeVisible();
  const cueArea = page.locator(".cue-textarea").first();
  await expect(cueArea).toBeVisible({ timeout: 10_000 });

  // Edit a cue -> Save draft becomes enabled -> click -> backend persists.
  await cueArea.fill("Bản dịch đã chỉnh sửa");
  const saveBtn = page.getByTestId("review-save-draft");
  await expect(saveBtn).toBeEnabled();
  await saveBtn.click();
  await expect.poll(async () => {
    const r = await page.request.post("/api/load", { data: { job_workspace: jobWorkspace } });
    const cues = (await r.json())?.data?.cues || [];
    return cues.some((c: any) => String(c.text || "").includes("đã chỉnh sửa"));
  }, { timeout: 15_000 }).toBe(true);

  expect(errors).toEqual([]);
});
