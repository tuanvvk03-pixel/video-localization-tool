// Typed client for the desktop server, mirroring desktop/static/api.js so
// migrated Svelte screens get the same {ok,data}/{ok,error} semantics with
// compile-time types. Keep this in sync with api.js until the legacy file is
// retired.

import type { ApiErrorShape, AsyncRunAck, JobProgress } from "./types";

export class ApiError extends Error {
  code: string;
  shortCode: string;
  summary: string;
  logTail: string[];
  status: number;

  constructor(e: Partial<ApiErrorShape> & { status?: number }) {
    super(e.message || e.code || "ApiError");
    this.code = e.code || "unknown";
    this.shortCode = e.short_code || e.code || "unknown";
    this.summary = e.summary || "";
    this.logTail = Array.isArray(e.log_tail) ? e.log_tail : [];
    this.status = e.status || 0;
  }
}

/** POST a JSON body and return the unwrapped `data`, throwing ApiError on !ok. */
export async function post<T = unknown>(path: string, body?: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body ?? {}),
    });
  } catch (e) {
    throw new ApiError({
      code: "network_error",
      short_code: "NET",
      message: (e as Error)?.message || "Network error",
      status: 0,
    });
  }

  let payload: { ok: boolean; data?: T; error?: ApiErrorShape };
  try {
    payload = await res.json();
  } catch {
    throw new ApiError({
      code: "http_error",
      short_code: "HTTP",
      message: `HTTP ${res.status}`,
      status: res.status,
    });
  }

  if (!payload.ok) {
    const err = payload.error || { code: "unknown", message: "Unknown error" };
    throw new ApiError({ ...err, status: res.status });
  }
  return payload.data as T;
}

function isAsyncAck(v: unknown): v is AsyncRunAck {
  return !!v && typeof v === "object" && (v as { async?: unknown }).async === true;
}

/**
 * Resolve a run-until-edit / run-after-edit response to its final data payload.
 * Sync responses pass through; async responses are polled via /api/job-progress
 * until terminal, then the captured handler payload is unwrapped. Mirrors the
 * awaitRunResult helper in the legacy api.js.
 */
export async function awaitRunResult<T = unknown>(
  jobWorkspace: string,
  response: T | AsyncRunAck,
  opts: { intervalMs?: number; onProgress?: (p: JobProgress) => void } = {},
): Promise<T> {
  if (!isAsyncAck(response)) return response as T;
  const intervalMs = opts.intervalMs ?? 800;
  for (;;) {
    await new Promise((r) => setTimeout(r, intervalMs));
    let progress: JobProgress;
    try {
      progress = await post<JobProgress>("/api/job-progress", { job_workspace: jobWorkspace });
    } catch {
      continue; // transient — keep polling for the background job
    }
    opts.onProgress?.(progress);
    const job = progress.job;
    if (!job) continue;
    if (job.state === "succeeded") {
      const payload = job.result;
      if (payload && payload.ok === false) {
        throw new ApiError(payload.error || { code: "run_failed", message: "Run failed" });
      }
      return (payload?.data ?? {}) as T;
    }
    if (job.state === "failed") {
      throw new ApiError({ code: "run_failed", message: job.error || "Run failed" });
    }
    if (job.state === "cancelled") {
      throw new ApiError({ code: "cancelled", message: "Run was cancelled." });
    }
  }
}

/** Request cooperative + hard cancellation of the background job. */
export async function cancelJob(jobWorkspace: string): Promise<unknown> {
  return post("/api/cancel-job", { job_workspace: jobWorkspace });
}

// ---- Native file picking ----------------------------------------------------
// In the pywebview desktop shell, window.pywebview.api.pick_file returns an
// absolute OS path. In a plain browser (dev), fall back to the server-side
// tkinter dialog (/api/pick-file). Mirrors the legacy api.js pickLocalFile for
// the cases the settings screen needs (a real path back).

export interface PickResult {
  ok: boolean;
  path?: string;
  cancelled?: boolean;
  error?: string;
}

export function hasNativeBridge(): boolean {
  const w = window as unknown as { pywebview?: { api?: { pick_file?: unknown } } };
  return !!(w.pywebview && w.pywebview.api && w.pywebview.api.pick_file);
}

/** Pick a single file, returning its absolute path (native bridge or server). */
export async function pickFilePath(filters?: string[]): Promise<PickResult> {
  if (hasNativeBridge()) {
    try {
      const w = window as unknown as {
        pywebview: { api: { pick_file: (f: string[] | null) => Promise<PickResult> } };
      };
      const r = await w.pywebview.api.pick_file(filters ?? null);
      if (r && (r.path || r.cancelled)) return r;
    } catch (e) {
      return { ok: false, error: (e as Error)?.message || String(e) };
    }
  }
  try {
    const data = await post<{ path?: string; cancelled?: boolean }>("/api/pick-file", {
      filters: filters ?? null,
    });
    if (data?.cancelled) return { ok: true, cancelled: true };
    return { ok: true, path: data?.path || "" };
  } catch (e) {
    return { ok: false, error: (e as ApiError)?.message || String(e) };
  }
}

// ---- Multi-file / fallback picking (mirrors legacy api.js) -------------------
// Same resolution order as pickFilePath but supports multiple files and an
// <input type="file"> fallback when neither the native bridge nor the server
// tkinter dialog can return an absolute path (plain browser dev mode).

/** Outcome of pickLocalFile/pickLocalFiles. `browser_fallback` means the caller
 * must read the provided <input type="file"> after it fires `change`. */
export interface PickLocalResult {
  ok: boolean;
  path?: string;
  paths?: string[];
  cancelled?: boolean;
  unavailable?: boolean;
  browser_fallback?: boolean;
  error?: string;
}

interface PickerWindow {
  pywebview?: {
    api?: {
      pick_file?: (f: string[] | null) => Promise<PickLocalResult>;
      pick_files?: (f: string[] | null) => Promise<PickLocalResult>;
    };
  };
}

async function pickNativeFile(filters: string[] | null): Promise<PickLocalResult> {
  const api = (window as unknown as PickerWindow).pywebview?.api;
  if (!api?.pick_file) return { ok: false, unavailable: true };
  try {
    return (await api.pick_file(filters || null)) || { ok: false, error: "empty_response" };
  } catch (e) {
    return { ok: false, error: (e as Error)?.message || String(e) };
  }
}

async function pickNativeFiles(filters: string[] | null): Promise<PickLocalResult> {
  const api = (window as unknown as PickerWindow).pywebview?.api;
  if (typeof api?.pick_files !== "function") return { ok: false, unavailable: true };
  try {
    return (await api.pick_files(filters || null)) || { ok: false, error: "empty_response" };
  } catch (e) {
    return { ok: false, error: (e as Error)?.message || String(e) };
  }
}

async function pickServerFile(filters: string[] | null): Promise<PickLocalResult> {
  try {
    const data = await post<{ path?: string; cancelled?: boolean }>("/api/pick-file", { filters });
    return { ok: true, ...data };
  } catch (e) {
    return { ok: false, error: (e as Error)?.message || String(e) };
  }
}

async function pickServerFiles(filters: string[] | null): Promise<PickLocalResult> {
  try {
    const data = await post<{ paths?: string[]; cancelled?: boolean }>("/api/pick-files", { filters });
    return { ok: true, ...data };
  } catch (e) {
    return { ok: false, error: (e as Error)?.message || String(e) };
  }
}

function nativeFileResolved(r: PickLocalResult): boolean {
  if (!r || r.unavailable === true) return false;
  return r.ok === true && (Boolean(r.path) || r.cancelled === true);
}

function nativeFilesResolved(r: PickLocalResult): boolean {
  if (!r || r.unavailable === true) return false;
  if (r.ok === true && Array.isArray(r.paths) && r.paths.length > 0) return true;
  return r.ok === true && r.cancelled === true;
}

export async function pickLocalFile(
  opts: { filters?: string[] | null; fallbackInput?: HTMLInputElement | null } = {},
): Promise<PickLocalResult> {
  const { filters = null, fallbackInput = null } = opts;
  const native = await pickNativeFile(filters);
  if (nativeFileResolved(native)) return native;
  const server = await pickServerFile(filters);
  if (server.ok) return server;
  if (fallbackInput) {
    fallbackInput.click();
    return { ok: true, browser_fallback: true };
  }
  return server.ok === false ? server : native;
}

export async function pickLocalFiles(
  opts: { filters?: string[] | null; fallbackInput?: HTMLInputElement | null } = {},
): Promise<PickLocalResult> {
  const { filters = null, fallbackInput = null } = opts;
  const native = await pickNativeFiles(filters);
  if (nativeFilesResolved(native)) return native;
  const server = await pickServerFiles(filters);
  if (server.ok) return server;
  if (fallbackInput) {
    fallbackInput.click();
    return { ok: true, browser_fallback: true };
  }
  return server.ok === false ? server : native;
}

/** After a `browser_fallback` result, resolve to the user's chosen File (or null on cancel/timeout). */
export function waitForFileInputSelection(
  input: HTMLInputElement | null,
  timeoutMs = 180000,
): Promise<File | null> {
  if (!input) return Promise.resolve(null);
  const immediate = input.files && input.files[0];
  if (immediate) return Promise.resolve(immediate);
  return new Promise((resolve) => {
    const timer = window.setTimeout(() => resolve(null), timeoutMs);
    input.addEventListener(
      "change",
      () => {
        window.clearTimeout(timer);
        resolve(input.files && input.files[0] ? input.files[0] : null);
      },
      { once: true },
    );
  });
}
