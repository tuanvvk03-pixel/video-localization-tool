import { test, expect } from "@playwright/test";

// Verifies the migrated Svelte Import screen mounts through the legacy app.js
// router (strangler-fig) in a real browser against the real server — i.e. the
// build → serve → mount pipeline works end to end for the edit wizard's first
// step. The current app is linear (no rail): a signed-in boot lands directly on
// "work" → step 0 = Import. If the boot shows the login gate instead (no local
// session), the screen can't be reached, so the test skips rather than failing.
test("import: migrated Svelte screen mounts via the legacy router", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(e.message));

  await page.goto("/", { waitUntil: "networkidle" });

  const gate = page.locator("#loginGate");
  if (await gate.isVisible().catch(() => false)) {
    test.skip(true, "login gate shown — no local session to reach the edit wizard");
  }

  // The Svelte component renders this testid once mounted.
  const screen = page.getByTestId("import-screen");
  await expect(screen).toBeVisible({ timeout: 20_000 });

  // i18n came through ctx.t (translated text, not a raw "import.*" key).
  const chooseBtn = page.locator(".dropzone .btn.primary").first();
  await expect(chooseBtn).toBeVisible();
  const label = (await chooseBtn.textContent())?.trim() || "";
  expect(label.length).toBeGreaterThan(0);
  expect(label.startsWith("import.")).toBe(false);

  // Full mount: dropzone + the default-TTS-provider config select both rendered.
  await expect(page.locator(".dropzone")).toHaveCount(1);
  await expect(page.locator("#import-tts-provider")).toHaveCount(1);

  expect(pageErrors, `page errors:\n${pageErrors.join("\n")}`).toEqual([]);
});
