// Tiny fetch helper wrapping the backend {ok,data} / {ok,error} envelope.
// All POST handlers in desktop/server.py return one of those shapes.

import { t } from "./i18n/i18n.js";

export class ApiError extends Error {
  constructor({ code, shortCode, message, summary, logTail, status }) {
    super(message || code || "ApiError");
    this.code = code;
    this.shortCode = shortCode || code;
    this.summary = summary || "";
    this.logTail = Array.isArray(logTail) ? logTail : [];
    this.status = status || 0;
  }
}

export async function post(path, body) {
  let res;
  try {
    res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
  } catch (e) {
    throw new ApiError({
      code: "network_error",
      shortCode: "NET",
      message: e?.message || "Network error",
      status: 0,
    });
  }

  let payload;
  try {
    payload = await res.json();
  } catch (_) {
    throw new ApiError({
      code: "http_error",
      shortCode: "HTTP",
      message: t("error.http", { status: res.status }),
      status: res.status,
    });
  }

  if (!payload.ok) {
    const err = payload.error || { code: "unknown", message: "Unknown error" };
    throw new ApiError({
      code: err.code,
      shortCode: err.short_code || err.code,
      message: err.message,
      summary: err.summary,
      logTail: err.log_tail,
      status: res.status,
    });
  }

  return payload.data;
}

/**
 * Resolve a run-until-edit / run-after-edit response to its final data payload.
 *
 * Backwards compatible: a synchronous response (no `async` flag) is returned
 * unchanged. An async response (`{async:true, job_id}`) is polled via
 * /api/job-progress until the background job reaches a terminal state, then the
 * captured handler payload is unwrapped to match what the synchronous call used
 * to return. Throws ApiError on a failed/cancelled run, mirroring `post`.
 *
 * @param {string} jobWorkspace
 * @param {any} response value returned by `post("/api/run-*", {async:true})`
 * @param {{intervalMs?:number, onProgress?:(progress:any)=>void}} [opts]
 */
export async function awaitRunResult(jobWorkspace, response, opts = {}) {
  if (!response || !response.async) return response;
  const intervalMs = opts.intervalMs || 800;
  for (;;) {
    await new Promise((r) => setTimeout(r, intervalMs));
    let progress;
    try {
      progress = await post("/api/job-progress", { job_workspace: jobWorkspace });
    } catch (_) {
      continue; // transient polling error — keep waiting for the job
    }
    if (typeof opts.onProgress === "function") {
      try { opts.onProgress(progress); } catch (_) { /* ignore */ }
    }
    const job = progress && progress.job;
    if (!job) continue;
    if (job.state === "succeeded") {
      const payload = job.result;
      if (payload && payload.ok === false) {
        const err = payload.error || { code: "run_failed", message: "Run failed" };
        throw new ApiError({
          code: err.code,
          shortCode: err.short_code || err.code,
          message: err.message,
          summary: err.summary,
          logTail: err.log_tail,
        });
      }
      return payload ? payload.data : {};
    }
    if (job.state === "failed") {
      throw new ApiError({ code: "run_failed", message: job.error || "Run failed" });
    }
    if (job.state === "cancelled") {
      throw new ApiError({ code: "cancelled", message: "Run was cancelled." });
    }
  }
}

/** Request cooperative cancellation of the background job for a workspace. */
export async function cancelJob(jobWorkspace) {
  return post("/api/cancel-job", { job_workspace: jobWorkspace });
}

// Native file/folder picker bridge.
//
// When the app runs inside the pywebview shell (desktop/native.py),
// `window.pywebview.api` is injected by pywebview and exposes
// `pick_file` / `pick_folder` returning an absolute OS path. When the
// app runs in a plain browser (dev mode via `python -m desktop.server`)
// those methods are absent — callers should fall back to an
// `<input type="file">` element or ask the user to paste a path.

export function hasNativeBridge() {
  return !!(typeof window !== "undefined" && window.pywebview && window.pywebview.api);
}

export async function pickNativeFile(filters) {
  if (!hasNativeBridge()) return { ok: false, unavailable: true };
  try {
    const result = await window.pywebview.api.pick_file(filters || null);
    return result || { ok: false, error: "empty_response" };
  } catch (e) {
    return { ok: false, error: e?.message || String(e) };
  }
}

export async function pickNativeFolder() {
  if (!hasNativeBridge()) return { ok: false, unavailable: true };
  try {
    const result = await window.pywebview.api.pick_folder();
    return result || { ok: false, error: "empty_response" };
  } catch (e) {
    return { ok: false, error: e?.message || String(e) };
  }
}

export async function pickServerFile(filters = null) {
  try {
    const data = await post("/api/pick-file", { filters });
    return { ok: true, ...data };
  } catch (e) {
    return { ok: false, error: e?.message || String(e) };
  }
}

function _nativeFilePickResolved(result) {
  if (!result) return false;
  if (result.unavailable === true) return false;
  if (result.ok === true && (Boolean(result.path) || result.cancelled === true)) return true;
  return false;
}

export async function pickLocalFile({ filters = null, fallbackInput = null } = {}) {
  const native = await pickNativeFile(filters);
  if (_nativeFilePickResolved(native)) return native;
  const serverResult = await pickServerFile(filters);
  if (serverResult.ok) return serverResult;
  if (fallbackInput) {
    fallbackInput.click();
    return { ok: true, browser_fallback: true };
  }
  return serverResult.ok === false ? serverResult : native;
}

export async function pickNativeFiles(filters) {
  if (!hasNativeBridge()) return { ok: false, unavailable: true };
  const fn = window.pywebview.api.pick_files;
  if (typeof fn !== "function") return { ok: false, unavailable: true };
  try {
    const result = await fn(filters || null);
    return result || { ok: false, error: "empty_response" };
  } catch (e) {
    return { ok: false, error: e?.message || String(e) };
  }
}

export async function pickServerFiles(filters = null) {
  try {
    const data = await post("/api/pick-files", { filters });
    return { ok: true, ...data };
  } catch (e) {
    return { ok: false, error: e?.message || String(e) };
  }
}

function _nativeFilesPickResolved(result) {
  if (!result) return false;
  if (result.unavailable === true) return false;
  if (result.ok === true && (Array.isArray(result.paths) && result.paths.length > 0)) return true;
  if (result.ok === true && result.cancelled === true) return true;
  return false;
}

export async function pickLocalFiles({ filters = null, fallbackInput = null } = {}) {
  const native = await pickNativeFiles(filters);
  if (_nativeFilesPickResolved(native)) return native;
  const serverResult = await pickServerFiles(filters);
  if (serverResult.ok) return serverResult;
  if (fallbackInput) {
    fallbackInput.click();
    return { ok: true, browser_fallback: true };
  }
  return serverResult.ok === false ? serverResult : native;
}

/** After `pickLocalFile` / `pickLocalFiles` returns `browser_fallback`, wait for `change` (user cancel → null). */
export async function waitForFileInputSelection(input, timeoutMs = 180000) {
  if (!input) return null;
  const immediate = input.files && input.files[0];
  if (immediate) return immediate;
  return new Promise((resolve) => {
    const t = window.setTimeout(() => resolve(null), timeoutMs);
    input.addEventListener(
      "change",
      () => {
        window.clearTimeout(t);
        resolve(input.files && input.files[0] ? input.files[0] : null);
      },
      { once: true },
    );
  });
}
