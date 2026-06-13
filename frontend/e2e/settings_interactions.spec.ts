import { readdirSync } from "node:fs";
import { resolve } from "node:path";
import { test, expect, type Page, type APIRequestContext } from "@playwright/test";

// Exercises real interactions on the migrated Svelte Settings screen against
// the real server + a real job created from the local test video.
const BASE = "http://127.0.0.1:8791";
const REPO = resolve(import.meta.dirname, "..", "..");
const TEST_DIR = resolve(REPO, "test");

function findVideo(): string | null {
  try {
    const f = readdirSync(TEST_DIR).find((n) => /\.(mp4|mov|mkv|webm)$/i.test(n));
    return f ? resolve(TEST_DIR, f) : null;
  } catch { return null; }
}

let workspaceRoot = "";
let jobWorkspace = "";
let jobName = "";

test.beforeAll(async ({ playwright }) => {
  const video = findVideo();
  // Stale for the current linear app: navigates via the removed dashboard
  // ("open job by name") to reach Settings. Needs a rewrite (test seam to set
  // jobWorkspace + jump to the Settings step). Body kept as a template.
  // See docs/14 §A (e2e debt).
  test.skip(true, "needs rework for linear app: no in-browser job-reopen to reach Settings");
  void video;
  const rc = await playwright.request.newContext({ baseURL: BASE });
  const res = await rc.post("/api/init-job", { data: { video } });
  const j = await res.json();
  workspaceRoot = j.data.workspace_root;
  jobWorkspace = j.data.job_workspace;
  jobName = String(jobWorkspace).split(/[\\/]/).pop() || "";
  await rc.dispose();
});

async function openSettings(page: Page): Promise<string[]> {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.addInitScript((root) => window.localStorage.setItem("workspace_root", root as string), workspaceRoot);
  await page.goto("/");
  await page.getByText(jobName, { exact: false }).first().click();
  await page.locator(".edit-step-pill").nth(1).click();
  await expect(page.getByTestId("settings-screen")).toBeVisible({ timeout: 20_000 });
  return errors;
}

test("style toggle updates preview and persists through save", async ({ page, request }) => {
  const errors = await openSettings(page);
  const bold = page.getByTestId("style-bold");
  if (!(await bold.evaluate((el) => el.classList.contains("active")))) await bold.click();
  await expect(bold).toHaveClass(/active/);
  await expect(page.locator(".subtitle-sample")).toHaveCSS("font-weight", "800");

  await page.getByTestId("save-text-audio").click();
  // No error banner appeared from the save.
  await expect(page.locator(".error-banner")).toHaveCount(0);

  // Backend actually persisted the bold flag.
  await expect.poll(async () => {
    const r = await request.post("/api/get-video-style", { data: { job_workspace: jobWorkspace } });
    return (await r.json())?.data?.style?.bold;
  }, { timeout: 10_000 }).toBe(true);
  expect(errors).toEqual([]);
});

test("extractor toggle swaps audio_only / external_srt panels", async ({ page }) => {
  const errors = await openSettings(page);
  await page.getByTestId("extractor-external_srt").click();
  await expect(page.getByRole("button", { name: /srt/i }).first()).toBeVisible();
  await page.getByTestId("extractor-audio_only").click();
  await expect(page.getByTestId("extractor-audio_only")).toHaveClass(/strong/);
  expect(errors).toEqual([]);
});

test("voice filter narrows the voice list without error", async ({ page }) => {
  const errors = await openSettings(page);
  const mainSelect = page.locator(".voice-picker > select");
  const before = await mainSelect.locator("option").count();
  expect(before).toBeGreaterThan(0);
  // Pick the first concrete locale filter (skip the "all" option).
  const localeFilter = page.locator(".voice-filter-select").first();
  const localeValues = await localeFilter.locator("option").evaluateAll((opts) =>
    (opts as HTMLOptionElement[]).map((o) => o.value).filter(Boolean));
  if (localeValues.length) {
    await localeFilter.selectOption(localeValues[0]);
    await expect(mainSelect.locator("option")).not.toHaveCount(0);
  }
  expect(errors).toEqual([]);
});

test("run (auto, no key) surfaces the API-key-required banner", async ({ page, request }) => {
  // Ensure no OpenAI key is configured for this run.
  const keyState = await (await request.post("/api/check-openai-key", { data: {} })).json();
  test.skip(!!keyState?.data?.has_key, "an OpenAI key is configured; auto run would start");
  const errors = await openSettings(page);
  await page.getByTestId("run-until-edit").click();
  await expect(page.getByTestId("api-key-missing")).toBeVisible({ timeout: 15_000 });
  expect(errors).toEqual([]);
});

test("run (manual) triggers a real transcribe of the video from the new UI", async ({ page, request }) => {
  // Force manual mode so the run needs no API key (transcribe only). Manual mode
  // keeps the user on Settings afterwards (the Review step stays gated until the
  // voice edit is ready) — same as the legacy screen.
  await request.post("/api/save-import-config", {
    data: { job_workspace: jobWorkspace, config: { use_auto_translate: false, subtitle_extractor: "audio_only" } },
  });
  const errors = await openSettings(page);
  await page.getByTestId("run-until-edit").click();

  // The in-flight run shows the live progress card; it clears when finished.
  await expect(page.locator(".run-until-edit-progress-card")).toBeVisible({ timeout: 10_000 });
  await expect(page.locator(".run-until-edit-progress-card")).toHaveCount(0, { timeout: 90_000 });

  // The migrated UI drove a real ASR pass: source.srt now exists for the job.
  const arts = await (await request.post("/api/list-artifacts", { data: { job_workspace: jobWorkspace } })).json();
  const rels = (arts?.data?.canonical || []).filter((a: any) => a.exists).map((a: any) => a.rel_path);
  expect(rels).toContain("artifacts/transcribe/source.srt");
  // Still on Settings (Review gated for manual mode), no crash.
  await expect(page.getByTestId("settings-screen")).toBeVisible();
  expect(errors).toEqual([]);
});
