import { requestEditShellRefresh } from "./editShellBridge.js";

/** @param {any} ctx @param {Record<string, unknown>} statusData */
export function applyJobStatusToEditGate(ctx, statusData) {
  if (!ctx?.jobWorkspace || !statusData) return;
  ctx.editGate = {
    job_workspace: ctx.jobWorkspace,
    voice_edit_status: String(statusData.voice_edit_status || ""),
    voice_edited: !!statusData.voice_edited,
  };
  requestEditShellRefresh();
}
