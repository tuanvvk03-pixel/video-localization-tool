<script lang="ts">
  // Download screen — Svelte port of the legacy desktop/static/screens/download.js.
  // Paste URLs → analyze (probe) → download each → open the created job in the
  // edit wizard. Behaviour preserved 1:1; state persists across nav via
  // ctx.downloadState (the legacy used a module-level object).
  import { post, ApiError } from "../../lib/api";
  import type { ScreenCtx } from "../../lib/screen";
  import Button from "../../lib/ui/Button.svelte";

  let { ctx }: { ctx: ScreenCtx } = $props();
  const t = (k: string, v?: Record<string, unknown>) => (ctx?.t ?? ((x: string) => x))(k, v);

  interface QueueLine {
    url: string;
    phase: string;
    message: string;
    probe: Record<string, any> | null;
    jobWorkspace: string;
  }
  interface DownloadState {
    urlsText: string;
    outputRoot: string;
    outputTouched: boolean;
    forceReuse: boolean;
    lines: QueueLine[];
    busy: string;
    lastJobWorkspace: string;
  }
  function defaultState(): DownloadState {
    return { urlsText: "", outputRoot: "", outputTouched: false, forceReuse: false, lines: [], busy: "", lastJobWorkspace: "" };
  }

  let s = $state<DownloadState>((ctx?.downloadState as DownloadState) || defaultState());
  if (ctx) ctx.downloadState = s;
  let errorMsg = $state("");
  let errorCode = $state("UI");

  const workspaceRoot = () => String(ctx?.workspaceRoot || "").trim();

  function clearErrors() { errorMsg = ""; }
  function showError(err: unknown) {
    const e = err instanceof ApiError ? err : null;
    errorCode = e?.shortCode || "UI";
    errorMsg = e ? (e.summary || e.message) : ((err as Error)?.message || t("error.generic"));
  }

  function parseUrls(text: string): string[] {
    return String(text || "").split(/\r?\n/).map((x) => x.trim()).filter(Boolean);
  }

  async function bootstrapOutputRoot() {
    if (s.outputTouched && s.outputRoot.trim()) return;
    const fromTopbar = workspaceRoot();
    if (fromTopbar) { s.outputRoot = fromTopbar; s.outputTouched = false; return; }
    try {
      const data = await post<any>("/api/default-download-root", {});
      const next = String(data.workspace_root || "").trim();
      if (next) { s.outputRoot = next; s.outputTouched = false; }
    } catch { /* keep empty; user can type */ }
  }

  async function applyDefaultFolder() {
    clearErrors();
    try {
      const data = await post<any>("/api/default-download-root", {});
      const next = String(data.workspace_root || "").trim();
      if (!next) throw new Error(t("download.default_folder_failed"));
      s.outputRoot = next; s.outputTouched = true;
    } catch (err) { showError(err); }
  }

  async function runAnalyze() {
    clearErrors();
    const root = s.outputRoot.trim();
    if (!root) { showError(new Error(t("download.output_required"))); return; }
    const urls = parseUrls(s.urlsText);
    if (!urls.length) { showError(new Error(t("download.urls_required"))); return; }
    s.busy = "analyze";
    s.lines = urls.map((url) => ({ url, phase: "pending", message: t("download.phase_pending"), probe: null, jobWorkspace: "" }));
    for (let i = 0; i < urls.length; i += 1) {
      const url = urls[i];
      s.lines[i] = { ...s.lines[i], phase: "probing", message: t("download.phase_probing") };
      try {
        const probe = await post<any>("/api/probe-video-url", { url });
        s.lines[i] = { url, phase: "ready", message: t("download.phase_ready"), probe, jobWorkspace: "" };
      } catch (err) {
        const msg = err instanceof ApiError ? err.message : String(err || "");
        s.lines[i] = { url, phase: "error", message: msg, probe: null, jobWorkspace: "" };
      }
    }
    s.busy = "";
  }

  async function runDownloadRow(index: number) {
    clearErrors();
    const root = s.outputRoot.trim();
    if (!root) { showError(new Error(t("download.output_required"))); return; }
    const prev = s.lines[index];
    if (!prev || prev.phase !== "ready") return;
    s.busy = `download:${index}`;
    s.lines[index] = { ...prev, phase: "downloading", message: t("download.phase_downloading") };
    try {
      const data = await post<any>("/api/init-job-from-url", { url: prev.url, workspace_root: root, force: !!s.forceReuse });
      const jw = String(data.job_workspace || "").trim();
      s.lines[index] = { ...prev, phase: "done", message: t("download.phase_done"), jobWorkspace: jw };
      s.lastJobWorkspace = jw; s.busy = "";
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : String(err || "");
      s.lines[index] = { ...prev, phase: "error", message: msg, jobWorkspace: prev.jobWorkspace };
      s.busy = "";
    }
  }

  function openLastInEdit() {
    const jw = s.lastJobWorkspace.trim();
    if (jw) openJobInEdit(jw);
  }

  function openJobInEdit(jobWorkspace: string) {
    const jw = String(jobWorkspace || "").trim();
    if (!jw || !ctx?.navigate) return;
    ctx.jobWorkspace = jw;
    const root = s.outputRoot.trim();
    if (root) {
      ctx.workspaceRoot = root;
      try { localStorage.setItem("workspace_root", root); } catch { /* ignore */ }
      const input = document.getElementById("workspaceRootInput") as HTMLInputElement | null;
      if (input) input.value = root;
    }
    ctx.preflightAfterOpenJob = true;
    ctx.navigate("edit", { stepIndex: 0 });
  }

  async function revealWorkspace() {
    clearErrors();
    const path = (workspaceRoot() || s.outputRoot.trim());
    if (!path) { showError(new Error(t("download.workspace_missing"))); return; }
    try { await post("/api/reveal", { path }); } catch (err) { showError(err); }
  }

  function formatDuration(seconds: any): string {
    const total = Math.max(0, Math.round(Number(seconds) || 0));
    if (!total) return "—";
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    const sec = total % 60;
    if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
    return `${m}:${String(sec).padStart(2, "0")}`;
  }

  const canOpenFolder = $derived(!!(workspaceRoot() || s.outputRoot.trim()));

  $effect(() => { void bootstrapOutputRoot(); });
</script>

{#if errorMsg}
  <div class="error-banner" data-testid="download-error">
    <div class="error-code">{errorCode}</div>
    <div class="error-message">{errorMsg}</div>
  </div>
{/if}

<div class="screen download-screen" data-testid="download-screen">
  <div class="dlhero">
    <h2>{t("rail.download")}</h2>
    <p>{t("download.sub")}</p>
  </div>

  <div class="card dlbox">
    <div class="card-body stack">
      <div class="field">
        <label for="dl-urls">{t("download.urls_label")}</label>
        <textarea id="dl-urls" class="input download-url-textarea" rows="8" placeholder={t("download.urls_placeholder")} bind:value={s.urlsText}></textarea>
      </div>

      <div class="toolbar download-toolbar">
        <Button variant="strong" disabled={!!s.busy} onclick={runAnalyze}>{t("download.analyze")}</Button>
        <Button variant="secondary" disabled={!!s.busy} onclick={() => { s.lines = []; s.busy = ""; }}>{t("download.clear_queue")}</Button>
        <Button disabled={!!s.busy} onclick={applyDefaultFolder}>{t("download.use_default_folder")}</Button>
      </div>

      <div class="warning-banner">{t("download.ytdlp_warning")}</div>

      <div class="field">
        <label for="dl-output">{t("download.output_root_label")}</label>
        <input id="dl-output" class="input" type="text" placeholder={t("download.output_root_placeholder")}
          value={s.outputRoot}
          oninput={(e) => { s.outputRoot = (e.currentTarget as HTMLInputElement).value; s.outputTouched = true; }} />
      </div>

      <div class="toolbar download-footer-actions">
        <Button variant="primary" disabled={!s.lastJobWorkspace || !!s.busy} onclick={openLastInEdit}>{t("download.open_edit")}</Button>
        <Button variant="secondary" disabled={!canOpenFolder} onclick={revealWorkspace}>{t("download.open_workspace")}</Button>
      </div>
    </div>
  </div>

  {#if s.lines.length}
    <div class="card">
      <div class="card-body stack">
        <div class="card-title">{t("download.queue_title")}</div>
        <label class="checkbox-row">
          <input type="checkbox" bind:checked={s.forceReuse} />
          <span>{t("download.force_reuse")}</span>
        </label>
        <div class="download-queue-list">
          {#each s.lines as row, idx}
            <div class="download-queue-row stack">
              <div class="download-queue-head">
                <div class="download-queue-url">{row.url}</div>
                <div class="download-queue-status download-queue-status--{row.phase}">
                  {row.phase === "error" ? t("download.status_error") : row.message || row.phase}
                </div>
              </div>

              {#if row.probe && row.phase === "ready"}
                <div class="download-queue-meta small-muted">
                  {t("download.probe_summary", { title: row.probe.title || row.probe.video_id || "—", duration: formatDuration(row.probe.duration), extractor: row.probe.extractor || "—" })}
                </div>
                {#if row.probe.thumbnail}
                  <img class="download-queue-thumb" alt="" loading="lazy" src={String(row.probe.thumbnail)} />
                {/if}
              {/if}

              {#if row.phase === "error" && row.message}
                <div class="small-muted">{row.message}</div>
              {/if}

              {#if row.phase === "ready"}
                <Button variant="primary" disabled={!!s.busy} onclick={() => runDownloadRow(idx)}>{t("download.confirm_download")}</Button>
              {/if}

              {#if row.phase === "done" && row.jobWorkspace}
                <div class="info-banner">{t("download.done_notice", { path: row.jobWorkspace })}</div>
                <Button variant="secondary" onclick={() => openJobInEdit(row.jobWorkspace)}>{t("download.open_this_edit")}</Button>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}
</div>
