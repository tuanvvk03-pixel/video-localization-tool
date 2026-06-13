import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { defineConfig } from "@playwright/test";

// E2E against the real Python server serving desktop/static (incl. the built
// Svelte screen modules under /next/). Playwright boots the server, runs the
// browser tests, then tears it down.
const PORT = 8791;
const REPO = resolve(import.meta.dirname, "..");
const VENV =
  process.platform === "win32"
    ? resolve(REPO, ".venv/Scripts/python.exe")
    : resolve(REPO, ".venv/bin/python");
// Pick the interpreter: an explicit override wins (e.g. a machine with no repo
// venv), then the repo venv if present, then the system "python" on PATH.
const PYTHON = process.env.VLTOOL_PYTHON || process.env.PYTHON || (existsSync(VENV) ? VENV : "python");

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  fullyParallel: false,
  // One worker: specs share a single server and some drive the real pipeline,
  // so serialize to avoid concurrent runs contending on the same backend.
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [["list"]],
  webServer: {
    command: `"${PYTHON}" -m desktop.server --no-browser --port ${PORT}`,
    cwd: REPO,
    url: `http://127.0.0.1:${PORT}/`,
    timeout: 60_000,
    reuseExistingServer: false,
    stdout: "pipe",
    stderr: "pipe",
  },
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    browserName: "chromium",
    trace: "retain-on-failure",
  },
});
