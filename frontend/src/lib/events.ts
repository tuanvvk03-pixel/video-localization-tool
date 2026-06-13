// Live job-event subscription (Phase C). Opens an SSE stream to
// /api/job-events and pushes the same payload the UI used to poll from
// /api/job-progress (progress fields + last_error + log_tail), so screens can
// drop their setInterval. Falls back to polling /api/job-progress when
// EventSource is unavailable or fails before any message arrives.
import { post } from "./api";

export interface JobEventHandlers {
  /** Live progress frame (same shape as /api/job-progress data, minus `job`). */
  onProgress?: (data: Record<string, unknown>) => void;
  /** Terminal frame (lifecycle completed/failed); the stream then closes. */
  onDone?: (data: Record<string, unknown>) => void;
  onError?: (err: unknown) => void;
}

/**
 * Subscribe to live job events. Returns a `close()` to stop the stream/poll.
 * Prefers SSE; transparently falls back to polling when SSE can't be used.
 */
export function subscribeJobEvents(
  jobWorkspace: string,
  handlers: JobEventHandlers,
  opts: { pollIntervalMs?: number } = {},
): () => void {
  let closed = false;
  let es: EventSource | null = null;
  let pollTimer: ReturnType<typeof setInterval> | null = null;
  let gotMessage = false;

  function stop(): void {
    closed = true;
    if (es) { es.close(); es = null; }
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
  }

  function startPolling(): void {
    if (closed || pollTimer) return;
    const interval = opts.pollIntervalMs ?? 2000;
    const tick = () => {
      if (closed) return;
      post<Record<string, unknown>>("/api/job-progress", { job_workspace: jobWorkspace })
        .then((data) => {
          if (closed) return;
          handlers.onProgress?.(data);
          const lc = String(data?.lifecycle || "");
          if (lc === "completed" || lc === "failed") { handlers.onDone?.(data); stop(); }
        })
        .catch((e) => { if (!closed) handlers.onError?.(e); });
    };
    pollTimer = setInterval(tick, interval);
    tick();
  }

  if (typeof EventSource === "undefined" || !jobWorkspace) {
    startPolling();
    return stop;
  }

  try {
    const params = new URLSearchParams({ job_workspace: jobWorkspace });
    es = new EventSource(`/api/job-events?${params.toString()}`);
    es.addEventListener("progress", (e) => {
      gotMessage = true;
      try { handlers.onProgress?.(JSON.parse((e as MessageEvent).data)); } catch { /* ignore */ }
    });
    es.addEventListener("done", (e) => {
      gotMessage = true;
      try { handlers.onDone?.(JSON.parse((e as MessageEvent).data)); } catch { /* ignore */ }
      stop();
    });
    es.onerror = () => {
      if (closed) return;
      // EventSource auto-reconnects on transient drops; only fall back to polling
      // if it fails before any frame (SSE blocked / unsupported).
      if (!gotMessage) { es?.close(); es = null; startPolling(); }
    };
  } catch (e) {
    handlers.onError?.(e);
    startPolling();
  }

  return stop;
}
