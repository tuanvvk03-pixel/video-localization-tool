import { readdirSync } from "node:fs";
import { resolve } from "node:path";
import { test, expect } from "@playwright/test";

// Full-screen verification: create a real job from the local test video, open
// it in the app, navigate to the migrated Svelte Settings step, and assert the
// real sections render (voice picker, run button, etc.) with no page errors.
const REPO = resolve(import.meta.dirname, "..", "..");
const TEST_DIR = resolve(REPO, "test");

function findVideo(): string | null {
  try {
    const f = readdirSync(TEST_DIR).find((n) => /\.(mp4|mov|mkv|webm)$/i.test(n));
    return f ? resolve(TEST_DIR, f) : null;
  } catch {
    return null;
  }
}

test("settings: full screen renders for a real job from the test video", async ({ page, request }) => {
  const video = findVideo();
  // Stale for the current linear app: navigates via the removed dashboard
  // ("open job by name") to reach Settings. Needs a rewrite (test seam to set
  // jobWorkspace + jump to the Settings step). Body kept as a template.
  // See docs/14 §A (e2e debt).
  test.skip(true, "needs rework for linear app: no in-browser job-reopen to reach Settings");
  void video;

  // 1) Create a job from the video via the API.
  const initRes = await request.post("/api/init-job", { data: { video } });
  expect(initRes.ok()).toBeTruthy();
  const init = await initRes.json();
  expect(init.ok).toBeTruthy();
  const workspaceRoot: string = init.data.workspace_root;
  const jobWorkspace: string = init.data.job_workspace;

  // 2) Point the dashboard at that workspace root before the app boots.
  await page.addInitScript((root) => {
    window.localStorage.setItem("workspace_root", root as string);
  }, workspaceRoot);

  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(e.message));

  // 3) Dashboard lists the job; open it.
  await page.goto("/");
  const jobName = jobWorkspace.split(/[\\/]/).pop() || "";
  await page.getByText(jobName, { exact: false }).first().click();

  // 4) In the edit wizard, jump to the Settings step (pill index 1).
  await page.locator(".edit-step-pill").nth(1).click();

  // 5) The migrated Settings screen renders its real content.
  await expect(page.getByTestId("settings-screen")).toBeVisible({ timeout: 20_000 });
  await expect(page.locator(".voice-picker > select")).toBeVisible();
  await expect(page.getByRole("button", { name: /run|chạy|dịch/i }).first()).toBeVisible();
  // Extractor mode toggle (audio_only / external_srt) present.
  await expect(page.locator(".extractor-modes .btn").first()).toBeVisible();

  expect(pageErrors, `page errors:\n${pageErrors.join("\n")}`).toEqual([]);
});
