// Types for the desktop server's {ok,data}/{ok,error} JSON contract.
// These mirror desktop/server.py handlers; extend per endpoint as screens move.

export interface ApiErrorShape {
  code: string;
  short_code?: string;
  message: string;
  summary?: string;
  log_tail?: string[];
}

export type JobState =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled";

/** Background job record from /api/job-progress (`data.job`). */
export interface JobRecord {
  job_id: string;
  state: JobState;
  submitted_at: number;
  started_at: number | null;
  finished_at: number | null;
  cancel_requested: boolean;
  error: string | null;
  /** Captured handler payload (the {ok,data} envelope) when succeeded. */
  result: { ok: boolean; data?: unknown; error?: ApiErrorShape } | null;
  result_status: number | null;
}

/** /api/job-progress data payload (progress fields + optional async job). */
export interface JobProgress {
  job: JobRecord | null;
  last_error?: string | null;
  log_tail?: string[];
  [key: string]: unknown;
}

/** Immediate response of an async /api/run-* call. */
export interface AsyncRunAck {
  job_id: string;
  state: "running";
  async: true;
}
