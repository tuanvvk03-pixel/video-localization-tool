<script lang="ts">
  import { onDestroy } from "svelte";
  import { post, ApiError } from "../lib/api";
  import { subscribeJobEvents } from "../lib/events";
  import type { ScreenCtx } from "../lib/screen";
  import Button from "../lib/ui/Button.svelte";
  import StatusBadge from "../lib/ui/StatusBadge.svelte";

  let { ctx }: { ctx: ScreenCtx } = $props();
  const t = (key: string, vars?: Record<string, unknown>) =>
    (ctx?.t ?? ((k: string) => k))(key, vars);
  const jw = () => String(ctx?.jobWorkspace || "");

  const TABS = ["logs", "artifacts", "state"] as const;
  type Tab = (typeof TABS)[number];

  const ARTIFACT_LABEL_KEYS: Record<string, string> = {
    "artifacts/download/download_manifest.json": "artifact.download_manifest",
    "artifacts/transcribe/source.srt": "artifact.source_srt",
    "artifacts/transcribe/source_cleaned_zh.srt": "artifact.source_cleaned_zh_srt",
    "artifacts/translate/translated_auto.srt": "artifact.translated_auto_srt",
    "artifacts/translate/translated_voice.srt": "artifact.translated_voice_srt",
    "artifacts/translate/translated_manual.srt": "artifact.translated_manual_srt",
    "artifacts/translate/final_subtitle.srt": "artifact.final_subtitle_srt",
    "artifacts/translate/final_subtitle_manifest.json": "artifact.final_subtitle_manifest",
    "artifacts/edit/edited_voice.srt": "artifact.edited_voice_srt",
    "artifacts/edit/edit_manifest.json": "artifact.edit_manifest",
    "artifacts/tts/tts_manifest.json": "artifact.tts_manifest",
    "artifacts/aligned/alignment_manifest.json": "artifact.alignment_manifest",
    "artifacts/mixed/mix_manifest.json": "artifact.mix_manifest",
    "artifacts/render/final.mp4": "artifact.final_mp4",
    "artifacts/render/render_manifest.json": "artifact.render_manifest",
    "job_state.json": "artifact.job_state",
    "video_state.json": "artifact.video_state",
    "style_override.json": "artifact.style_override",
    "tts_override.json": "artifact.tts_override",
  };

  interface Artifact {
    rel_path?: string;
    label?: string;
    path?: string;
    exists?: boolean;
    size_bytes?: number;
    modified_unix?: number;
    count?: number;
  }

  let loading = $state(true);
  let busyAction = $state("");
  let activeTab = $state<Tab>("logs");
  let autoScroll = $state(true);
  let progress = $state<Record<string, any> | null>(null);
  let status = $state<Record<string, any> | null>(null);
  let artifacts = $state<Artifact[]>([]);
  let extras = $state<Artifact[]>([]);
  let errorMsg = $state("");

  let unsubEvents: (() => void) | null = null;
  let lastEventStage = "";
  let logbox: HTMLDivElement | undefined = $state();

  async function refreshRuntime() {
    const [p, s, a] = await Promise.all([
      post<Record<string, any>>("/api/job-progress", { job_workspace: jw() }),
      post<Record<string, any>>("/api/status", { job_workspace: jw() }),
      post<{ canonical?: Artifact[]; extras?: Artifact[] }>("/api/list-artifacts", { job_workspace: jw() }),
    ]);
    progress = p;
    status = s;
    artifacts = Array.isArray(a.canonical) ? a.canonical : [];
    extras = Array.isArray(a.extras) ? a.extras : [];
  }

  async function load() {
    if (!jw()) {
      loading = false;
      return;
    }
    errorMsg = "";
    loading = true;
    try {
      await refreshRuntime();
      loading = false;
      startEvents();
    } catch (err) {
      loading = false;
      errorMsg = asMessage(err);
    }
  }

  // Live progress + log tail via SSE (replaces the 2.5s poll). The pushed payload
  // carries progress fields + log_tail, so we update instantly and only re-fetch
  // status+artifacts on a stage change / terminal. Falls back to polling.
  function startEvents() {
    stopEvents();
    if (!jw()) return;
    lastEventStage = String((progress as Record<string, any>)?.current_stage || "");
    unsubEvents = subscribeJobEvents(jw(), {
      onProgress: (data) => {
        progress = data;
        if (logbox && activeTab === "logs" && autoScroll) {
          logbox.scrollTop = logbox.scrollHeight;
        }
        const stage = String(data?.current_stage || "");
        if (stage !== lastEventStage) {
          lastEventStage = stage;
          void refreshRuntime().catch(() => {});
        }
      },
      onDone: () => { void refreshRuntime().catch(() => {}); },
    });
  }

  function stopEvents() {
    if (unsubEvents) { unsubEvents(); unsubEvents = null; }
  }

  async function runBusy(name: string, fn: () => Promise<void>) {
    errorMsg = "";
    busyAction = name;
    try {
      await fn();
    } catch (err) {
      errorMsg = asMessage(err);
    } finally {
      busyAction = "";
    }
  }

  const forceRefresh = () => runBusy("refresh", refreshRuntime);
  const revealPath = (path?: string) =>
    runBusy("reveal", async () => {
      await post("/api/reveal", { path });
    });

  function openArtifact(entry: Artifact) {
    if (!entry?.rel_path) return;
    const params = new URLSearchParams({ workspace: jw(), rel: entry.rel_path });
    window.open(`/media?${params.toString()}`, "_blank", "noopener");
  }

  async function copyText(text?: string) {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(String(text));
    } catch {
      /* clipboard unavailable */
    }
  }

  function asMessage(err: unknown): string {
    if (err instanceof ApiError) return err.summary || err.message;
    return (err as Error)?.message || t("error.generic");
  }

  function artifactLabel(entry: Artifact): string {
    const key = entry.rel_path ? ARTIFACT_LABEL_KEYS[entry.rel_path] : undefined;
    return key ? t(key) : entry.label || entry.rel_path || "";
  }

  function formatBytes(bytes?: number): string {
    const v = Number(bytes) || 0;
    if (v >= 1024 * 1024) return `${(v / (1024 * 1024)).toFixed(1)} MB`;
    if (v >= 1024) return `${(v / 1024).toFixed(1)} KB`;
    return `${v} B`;
  }

  function formatDate(unix?: number): string {
    const v = Number(unix) || 0;
    if (!v) return "—";
    return new Date(v * 1000).toLocaleString();
  }

  function escapeHtml(value: string): string {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  // Escapes first, then adds highlight spans — safe to use with {@html}.
  function highlightLog(line: string): string {
    let html = escapeHtml(line);
    html = html.replace(/\b(INFO|OK)\b/g, '<span class="ok">$1</span>');
    html = html.replace(/\b(RUN|RUNNING)\b/g, '<span class="run">$1</span>');
    html = html.replace(/\b(WARN|WAIT|BLOCKED|ERROR|FAILED)\b/g, '<span class="warn">$1</span>');
    html = html.replace(
      /([A-Za-z]:\\[^ <>\n]+|artifacts\/[^ <>\n]+|input\/[^ <>\n]+)/g,
      '<span class="path">$1</span>',
    );
    return html;
  }

  const logTail = $derived(Array.isArray(progress?.log_tail) ? (progress!.log_tail as string[]) : []);
  const canonicalRows = $derived(artifacts.filter((e) => e.exists));
  const statePayload = $derived({
    workspace: jw(),
    lifecycle: progress?.lifecycle || "idle",
    status: progress?.status || "",
    current_stage: progress?.current_stage || "",
    current_stage_label: progress?.current_stage_label || "",
    overall_percent: progress?.overall_percent || 0,
    voice_edit_status: status?.voice_edit_status || "",
    voice_edited: !!status?.voice_edited,
    required_action: status?.required_action || null,
    last_error: progress?.last_error || null,
    log_tail: progress?.log_tail || [],
  });
  const overallPct = $derived(Math.max(0, Math.min(100, Number(progress?.overall_percent) || 0)));

  // Load on mount; reload when the workspace changes.
  $effect(() => {
    void jw();
    void load();
  });
  onDestroy(stopEvents);
</script>

{#if errorMsg}
  <div class="error-banner" data-testid="diag-error">
    <div class="error-code">UI</div>
    <div class="error-message">{errorMsg}</div>
  </div>
{/if}

{#if !jw()}
  <div class="card" data-testid="diag-empty">
    <div class="empty-card">
      <div class="empty-icon">⌘</div>
      <h3>{t("diag.empty_title")}</h3>
      <p>{t("diag.empty_body")}</p>
    </div>
  </div>
{:else if loading}
  <div class="card" data-testid="diag-loading">
    <div class="empty-card">
      <div class="empty-icon">…</div>
      <h3>{t("diag.loading_title")}</h3>
      <p>{t("common.loading")}</p>
    </div>
  </div>
{:else}
  <div class="screen stack" data-testid="diag-screen">
    <div class="pipeline">
      <div class="stage"><span class="dot running"></span><span>{t("diag.pipeline_logs")}</span></div>
      <div class="stage"><span class="dot done"></span><span>{t("diag.pipeline_artifacts")}</span></div>
      <div class="stage"><span class="dot queued"></span><span>{t("diag.pipeline_state")}</span></div>
    </div>

    <div class="tabs">
      {#each TABS as tab}
        <button
          type="button"
          class="tab {activeTab === tab ? 'active' : ''}"
          onclick={() => (activeTab = tab)}
        >{t(`diag.tab.${tab}`)}</button>
      {/each}
    </div>

    <div class="state-grid">
      <!-- main panel -->
      {#if activeTab === "logs"}
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">{t("diag.logs.title")}</div>
              <div class="card-sub">{t("diag.logs.sub")}</div>
            </div>
            <label class="checkbox-row">
              <input type="checkbox" bind:checked={autoScroll} />
              {t("diag.auto_scroll")}
            </label>
          </div>
          <div class="card-body">
            <div class="logbox" bind:this={logbox}>
              {#if !logTail.length}
                <div class="small-muted">{t("diag.logs.empty")}</div>
              {:else}
                {#each logTail as line}
                  <div class="logline">{@html highlightLog(String(line || ""))}</div>
                {/each}
              {/if}
            </div>
          </div>
        </div>
      {:else if activeTab === "artifacts"}
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">{t("diag.artifacts.title")}</div>
              <div class="card-sub">{t("diag.artifacts.sub")}</div>
            </div>
          </div>
          <div class="card-body card-body--scroll">
            <div class="artifact-list">
              {#if !canonicalRows.length && !extras.length}
                <div class="meta-empty">{t("diag.artifacts.empty")}</div>
              {:else}
                {#each canonicalRows as entry}
                  <div class="artifact">
                    <div>
                      <div class="artifact-name">{artifactLabel(entry)}</div>
                      <small>{formatBytes(entry.size_bytes)} • {formatDate(entry.modified_unix)}</small>
                    </div>
                    <StatusBadge kind="completed">{t("status.completed")}</StatusBadge>
                    <div class="toolbar">
                      <Button disabled={!entry.rel_path} onclick={() => openArtifact(entry)}>{t("common.open")}</Button>
                      <Button disabled={!entry.path} onclick={() => revealPath(entry.path)}>{t("common.reveal")}</Button>
                      <Button disabled={!entry.path} onclick={() => copyText(entry.path)}>{t("diag.copy_path")}</Button>
                    </div>
                  </div>
                {/each}
                {#each extras as entry}
                  <div class="artifact">
                    <div>
                      <div class="artifact-name">{String(entry.label || t("diag.artifacts.extra"))}</div>
                      <small>{t("diag.artifacts.extra_count", { count: String(entry.count || 0) })}</small>
                    </div>
                    <StatusBadge kind="completed">{t("status.completed")}</StatusBadge>
                    <div class="toolbar">
                      <Button disabled={!entry.path} onclick={() => revealPath(entry.path)}>{t("common.reveal")}</Button>
                      <Button disabled={!entry.path} onclick={() => copyText(entry.path)}>{t("diag.copy_path")}</Button>
                    </div>
                  </div>
                {/each}
              {/if}
            </div>
          </div>
        </div>
      {:else}
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">{t("diag.state.title")}</div>
              <div class="card-sub">{t("diag.state.sub")}</div>
            </div>
          </div>
          <div class="card-body">
            <pre class="mini-json">{JSON.stringify(statePayload, null, 2)}</pre>
          </div>
        </div>
      {/if}

      <!-- side panel -->
      <div class="stack">
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">{t("diag.summary.title")}</div>
              <div class="card-sub">{t("diag.summary.sub")}</div>
            </div>
          </div>
          <div class="card-body stack">
            <div class="section-block">
              <div style="font-weight:800">{progress?.current_stage_label || t("diag.summary.idle")}</div>
              <div class="small-muted" style="margin-top:6px">
                {progress?.status_label || t("status.waiting")} • {overallPct}%
              </div>
            </div>
            <div class="toolbar">
              <Button variant="primary" disabled={!!busyAction} onclick={forceRefresh}>{t("common.refresh")}</Button>
              <Button onclick={() => copyText(jw())}>{t("diag.copy_path")}</Button>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">{t("diag.quick_state.title")}</div>
              <div class="card-sub">{t("diag.quick_state.sub")}</div>
            </div>
          </div>
          <div class="card-body">
            <div class="settings-context">
              <div class="context-pill"><strong>{t("diag.quick_state.workspace")}:</strong> {jw() || "—"}</div>
              <div class="context-pill"><strong>{t("diag.quick_state.lifecycle")}:</strong> {progress?.lifecycle || "idle"}</div>
              <div class="context-pill"><strong>{t("diag.quick_state.voice_status")}:</strong> {status?.voice_edit_status || "not_started"}</div>
              <div class="context-pill"><strong>{t("diag.quick_state.required_action")}:</strong> {status?.required_action || "—"}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}
