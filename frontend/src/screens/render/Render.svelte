<script lang="ts">
  // Render step — Svelte port of the legacy desktop/static/screens/render.js.
  // Behaviour preserved 1:1: loads status/progress/artifacts + effective
  // TTS/style snapshot, lists downstream artifacts with live status, runs
  // run-after-edit (export), polls runtime every 4s until idle, and previews
  // final.mp4. Only render()-reachable code paths were ported (the unused
  // renderPipelineStrip + RENDER_PIPELINE_ORDER from the legacy file were dropped).
  import { onDestroy } from "svelte";
  import { post, ApiError, awaitRunResult } from "../../lib/api";
  import { subscribeJobEvents } from "../../lib/events";
  import type { ScreenCtx } from "../../lib/screen";
  import Card from "../../lib/ui/Card.svelte";
  import Button from "../../lib/ui/Button.svelte";
  import StatusBadge from "../../lib/ui/StatusBadge.svelte";
  import ProgressBar from "../../lib/ui/ProgressBar.svelte";

  let { ctx }: { ctx: ScreenCtx } = $props();
  const t = (k: string, v?: Record<string, unknown>) => (ctx?.t ?? ((x: string) => x))(k, v);
  const jw = () => String(ctx?.jobWorkspace || "");
  const pr = () => String(ctx?.parentProjectRoot || "");

  const DOWNSTREAM_ARTIFACTS = [
    "artifacts/translate/final_subtitle.srt",
    "artifacts/translate/final_subtitle_manifest.json",
    "artifacts/tts/tts_manifest.json",
    "artifacts/aligned/alignment_manifest.json",
    "artifacts/mixed/mix_manifest.json",
    "artifacts/render/final.mp4",
    "artifacts/render/render_manifest.json",
  ];

  const ARTIFACT_STAGE: Record<string, string> = {
    "artifacts/translate/final_subtitle.srt": "voice_edited",
    "artifacts/translate/final_subtitle_manifest.json": "voice_edited",
    "artifacts/tts/tts_manifest.json": "tts_generated",
    "artifacts/aligned/alignment_manifest.json": "aligned",
    "artifacts/mixed/mix_manifest.json": "mixed",
    "artifacts/render/final.mp4": "rendered",
    "artifacts/render/render_manifest.json": "rendered",
  };

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

  function defaultState(): Record<string, any> {
    return {
      loadedJobWorkspace: "", loading: false, busyAction: "", notice: "",
      status: null, progress: null, artifacts: [], extras: [],
      effectiveTts: {
        tts_provider: "edge_tts", tts_voice: "vi-VN-HoaiMyNeural",
        tts_rate: 0, tts_pitch: 0, mix_mode: "replace_original_speech",
      },
      effectiveStyle: {}, renderSubtitleMode: "burn", importSummary: null,
    };
  }

  // Persist across wizard navigation via the shared ctx, like the legacy
  // ctx.renderState. Reuse the live object so an in-flight export keeps its state.
  let s = $state<Record<string, any>>((ctx?.renderState as Record<string, any>) || defaultState());
  if (ctx) ctx.renderState = s;
  let errorMsg = $state("");
  let errorCode = $state("UI");

  let unsubEvents: (() => void) | null = null;
  let lastEventStage = "";

  onDestroy(() => stopEvents());

  // ---- snapshot helpers -----------------------------------------------------
  function pickOverride(): Record<string, any> | null {
    const ss = ctx?.settingsState as Record<string, any> | undefined;
    return ss && ss.loadedJobWorkspace === jw() ? ss : null;
  }

  function mergeEffectiveTts(projectTts: any, videoTts: any, override: Record<string, any> | null) {
    return {
      ...(projectTts?.settings || {}),
      ...(videoTts?.settings || {}),
      ...(override
        ? {
            tts_provider: override.tts_provider, tts_voice: override.tts_voice,
            speed_multiplier: override.speed_multiplier, tts_rate: override.tts_rate,
            tts_pitch: override.tts_pitch, mix_mode: override.mix_mode,
            mix_duck_gain_db: override.mix_duck_gain_db,
          }
        : {}),
    };
  }

  // ---- load + runtime -------------------------------------------------------
  async function maybeLoadRender(force = false) {
    if (!jw()) return;
    if (!force && s.loadedJobWorkspace === jw() && s.progress) {
      void refreshTtsStyleSnapshot().catch(() => {});
      startEvents();
      return;
    }
    clearError();
    s.loading = true; s.notice = ""; s.loadedJobWorkspace = jw();
    try {
      const [statusData, progressData, artifactData, videoTts, videoStyle, projectTts, projectStyle, importCfg] =
        await Promise.all([
          post<any>("/api/status", { job_workspace: jw() }),
          post<any>("/api/job-progress", { job_workspace: jw() }),
          post<any>("/api/list-artifacts", { job_workspace: jw() }),
          post<any>("/api/get-video-tts", { job_workspace: jw() }),
          post<any>("/api/get-video-style", { job_workspace: jw() }),
          pr() ? post<any>("/api/get-project-tts", { project_root: pr() }) : Promise.resolve({ settings: {} }),
          pr() ? post<any>("/api/get-project-style", { project_root: pr() }) : Promise.resolve({ style: {} }),
          post<any>("/api/get-import-config", { job_workspace: jw() }).catch(() => ({ config: {} })),
        ]);
      const override = pickOverride();
      const effectiveTts = mergeEffectiveTts(projectTts, videoTts, override);
      const effectiveStyle = { ...(projectStyle.style || {}), ...(videoStyle.style || {}) };
      const icfg = importCfg && typeof importCfg.config === "object" ? importCfg.config : {};
      Object.assign(s, {
        loadedJobWorkspace: jw(), loading: false, status: statusData, progress: progressData,
        artifacts: normalizeArtifacts(artifactData.canonical || []),
        extras: Array.isArray(artifactData.extras) ? artifactData.extras : [],
        effectiveTts, effectiveStyle,
        renderSubtitleMode: String(override?.renderSubtitleMode || "burn"),
        importSummary: {
          use_auto_translate: icfg.use_auto_translate !== false,
          source_language: String(icfg.source_language || "auto"),
          translate_backend: String(icfg.translate_backend || "block_v2"),
        },
        notice: "",
      });
      startEvents();
      if (ctx?.pendingVoiceEditContinue) {
        ctx.pendingVoiceEditContinue = false;
        void runAfterApproval();
      }
    } catch (err) {
      if (ctx) ctx.pendingVoiceEditContinue = false;
      s.loading = false;
      showError(err);
    }
  }

  async function refreshTtsStyleSnapshot() {
    if (!jw()) return;
    const [videoTts, projectTts, videoStyle, projectStyle] = await Promise.all([
      post<any>("/api/get-video-tts", { job_workspace: jw() }).catch(() => ({ settings: {} })),
      pr() ? post<any>("/api/get-project-tts", { project_root: pr() }).catch(() => ({ settings: {} })) : Promise.resolve({ settings: {} }),
      post<any>("/api/get-video-style", { job_workspace: jw() }).catch(() => ({ style: {} })),
      pr() ? post<any>("/api/get-project-style", { project_root: pr() }).catch(() => ({ style: {} })) : Promise.resolve({ style: {} }),
    ]);
    const override = pickOverride();
    s.effectiveTts = mergeEffectiveTts(projectTts, videoTts, override);
    s.effectiveStyle = { ...(projectStyle.style || {}), ...(videoStyle.style || {}) };
    if (override && typeof override.renderSubtitleMode === "string") {
      s.renderSubtitleMode = override.renderSubtitleMode;
    }
  }

  async function refreshRuntime(refreshArtifacts = false) {
    if (!jw()) return;
    const jobs: Promise<any>[] = [
      post<any>("/api/status", { job_workspace: jw() }),
      post<any>("/api/job-progress", { job_workspace: jw() }),
    ];
    if (refreshArtifacts) jobs.push(post<any>("/api/list-artifacts", { job_workspace: jw() }));
    const [statusData, progressData, artifactData] = await Promise.all(jobs);
    s.status = statusData; s.progress = progressData;
    if (artifactData) {
      s.artifacts = normalizeArtifacts(artifactData.canonical || []);
      s.extras = Array.isArray(artifactData.extras) ? artifactData.extras : [];
    }
  }

  // ---- actions --------------------------------------------------------------
  async function runAfterApproval() {
    // Re-open the live event stream: the previous one closed on the last `done`.
    startEvents();
    await runBusy("run_after_approval", async () => {
      await refreshTtsStyleSnapshot();
      const eff = s.effectiveTts || {};
      const runResponse = await post<any>("/api/run-after-edit", {
        job_workspace: jw(), project_name: deriveProjectName(), project_root: pr(),
        to_stage: "rendered", subtitle_mode: s.renderSubtitleMode,
        tts_provider: eff.tts_provider || "edge_tts", tts_voice: eff.tts_voice || "",
        tts_rate: Number(eff.tts_rate) || 0, mix_mode: eff.mix_mode || "replace_original_speech",
        mix_duck_gain_db: Number.isFinite(Number(eff.mix_duck_gain_db)) ? Number(eff.mix_duck_gain_db) : -15,
        async: true,
      });
      const result = await awaitRunResult<any>(jw(), runResponse);
      s.notice = result?.render_dir
        ? t("render.notice_run_finished", { path: result.render_dir })
        : t("render.notice_run_started");
      await refreshRuntime(true);
    });
  }

  async function revealOutputFolder() {
    await revealPath(`${jw()}\\artifacts\\render`);
  }
  async function revealPath(path?: string) {
    await runBusy("reveal", async () => {
      const data = await post<any>("/api/reveal", { path });
      s.notice = t("render.notice_revealed", { path: data.path });
    });
  }
  function openArtifact(entry: Artifact) {
    if (!entry?.exists || !entry.rel_path) return;
    window.open(buildMediaUrl(entry.rel_path, Number(entry.modified_unix) || 0), "_blank", "noopener");
  }

  // ---- polling --------------------------------------------------------------
  // Live progress via SSE (replaces the 4s poll). The pushed payload is the
  // /api/job-progress shape, so s.progress updates instantly for the bar/label;
  // we only re-fetch status+artifacts on a stage change or terminal (to pick up
  // intermediate manifests + the final mp4). Falls back to polling internally.
  function startEvents() {
    stopEvents();
    if (!jw()) return;
    lastEventStage = String(s.progress?.current_stage || "");
    unsubEvents = subscribeJobEvents(jw(), {
      onProgress: (data) => {
        s.progress = data;
        const stage = String(data?.current_stage || "");
        if (stage !== lastEventStage) {
          lastEventStage = stage;
          void refreshRuntime(true).catch(() => {});
        }
      },
      onDone: (data) => {
        s.progress = data;
        void refreshRuntime(true).catch(() => {});
      },
    });
  }
  function stopEvents() {
    if (unsubEvents) { unsubEvents(); unsubEvents = null; }
  }

  async function runBusy(name: string, fn: () => Promise<void>) {
    clearError();
    s.busyAction = name;
    try {
      await fn();
    } catch (err) {
      showError(err);
    } finally {
      s.busyAction = "";
    }
  }

  // ---- error banner ---------------------------------------------------------
  function clearError() { errorMsg = ""; }
  function showError(err: unknown) {
    const e = err instanceof ApiError ? err : null;
    errorCode = e?.shortCode || "UI";
    errorMsg = e ? (e.summary || e.message) : ((err as Error)?.message || t("error.generic"));
  }

  // ---- pure helpers ---------------------------------------------------------
  function normalizeArtifacts(canonical: any[]): Artifact[] {
    return Array.isArray(canonical) ? canonical.map((e) => ({ ...e })) : [];
  }
  function deriveProjectName(): string {
    if (ctx?.parentProject) return String(ctx.parentProject);
    const j = jw().replace(/[\\/]+$/, "");
    const parts = j.split(/[\\/]/);
    return parts[parts.length - 1] || "job";
  }
  function buildMediaUrl(rel: string, cacheBust = 0): string {
    if (!jw()) return "";
    const params = new URLSearchParams({ workspace: jw(), rel });
    if (cacheBust) params.set("v", String(cacheBust));
    return `/media?${params.toString()}`;
  }
  function artifactLabel(entry: Artifact): string {
    const key = entry.rel_path ? ARTIFACT_LABEL_KEYS[entry.rel_path] : undefined;
    return key ? t(key) : entry.label || entry.rel_path || "";
  }
  function artifactSubtext(entry: Artifact): string {
    if (entry.exists) {
      return t("render.artifact_ready_meta", {
        size: formatBytes(entry.size_bytes || 0), updated: formatDate(entry.modified_unix || 0),
      });
    }
    return t("render.artifact_pending_meta", {
      stage: t(`stage.${(entry.rel_path && ARTIFACT_STAGE[entry.rel_path]) || "rendered"}`),
    });
  }
  function mixModeLabel(value: string): string {
    return value === "duck_original_speech" ? t("settings.tts.mix_duck") : t("settings.tts.mix_replace");
  }
  function subtitleModeLabel(value: string): string {
    return value === "burn" || value === "hard" ? t("render.subtitle_mode_hard") : t("render.subtitle_mode_soft");
  }
  function sourceLanguageSummaryLabel(code: string): string {
    const c = String(code || "auto");
    const key = `settings.translation.source_language_${c}`;
    const label = t(key);
    return label === key ? c : label;
  }
  function currentStageSummary(): string {
    const tts = s.effectiveTts || {};
    return t("render.current_voice_summary", {
      voice: tts.tts_voice || "—", rate: formatPct(tts.tts_rate), pitch: formatPct(tts.tts_pitch),
      status: s.progress?.status_label || t("status.waiting"),
    });
  }
  function formatPct(n: any): string {
    const value = Number(n) || 0;
    return `${value > 0 ? "+" : ""}${value}%`;
  }
  function formatBytes(bytes: number): string {
    const value = Number(bytes) || 0;
    if (value >= 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB`;
    if (value >= 1024) return `${(value / 1024).toFixed(1)} KB`;
    return `${value} B`;
  }
  function formatDate(unix: number): string {
    const value = Number(unix) || 0;
    if (!value) return "—";
    return new Date(value * 1000).toLocaleString();
  }

  // ---- status pills ---------------------------------------------------------
  type Pill = { kind: string; text: string };
  function artifactStatus(entry: Artifact): Pill {
    const currentStage = s.progress?.current_stage || "";
    const lifecycle = s.progress?.lifecycle || "";
    const targetStage = (entry.rel_path && ARTIFACT_STAGE[entry.rel_path]) || "rendered";
    if (entry.exists) return { kind: "completed", text: t("status.completed") };
    if (currentStage === targetStage && lifecycle === "running") return { kind: "running", text: t("status.running") };
    if (!s.status?.voice_edited) return { kind: "blocked", text: t("status.needs_review") };
    return { kind: "queued", text: t("status.waiting") };
  }
  function lifecycleTag(): Pill {
    const lifecycle = s.status?.voice_edited ? (s.progress?.lifecycle || "queued") : "blocked";
    const text = lifecycle === "blocked" ? t("status.needs_review") : (t(`status.${lifecycle}`) || lifecycle);
    return { kind: lifecycle === "idle" ? "queued" : lifecycle, text };
  }

  // ---- derived for template -------------------------------------------------
  const approved = $derived(!!s.status?.voice_edited);
  const downstreamRows = $derived(
    (s.artifacts as Artifact[]).filter((e) => e.rel_path && DOWNSTREAM_ARTIFACTS.includes(e.rel_path)),
  );
  const finalVideo = $derived(
    (s.artifacts as Artifact[]).find((e) => e.rel_path === "artifacts/render/final.mp4" && e.exists) || null,
  );
  const finalVideoSrc = $derived(
    finalVideo ? buildMediaUrl(finalVideo.rel_path!, Number(finalVideo.modified_unix) || 0) : "",
  );
  const overallPct = $derived(Math.max(0, Math.min(100, Number(s.progress?.overall_percent) || 0)));
  const lt = $derived(lifecycleTag());

  // Load on mount; the edit shell re-mounts this screen when navigated to.
  $effect(() => {
    void jw();
    void maybeLoadRender();
  });
</script>

{#if errorMsg}
  <div class="error-banner" data-testid="render-error">
    <div class="error-code">{errorCode}</div>
    <div class="error-message">{errorMsg}</div>
  </div>
{/if}

{#if !jw()}
  <div class="card" data-testid="render-empty">
    <div class="empty-card">
      <div class="empty-icon">▶</div>
      <h3>{t("render.empty_title")}</h3>
      <p>{t("render.empty_body")}</p>
    </div>
  </div>
{:else if s.loading}
  <div class="card" data-testid="render-loading">
    <div class="empty-card">
      <div class="empty-icon">…</div>
      <h3>{t("render.loading_title")}</h3>
      <p>{t("common.loading")}</p>
    </div>
  </div>
{:else}
  <div class="screen stack" data-testid="render-screen">
    {#if s.importSummary}
      {@const sum = s.importSummary}
      <Card title={t("render.config_summary_title")} sub={t("render.config_summary_sub")} bodyClass="stack">
        <div class="kv">
          <div class="item"><div class="k">{t("render.summary_source_language")}</div><div class="v">{sourceLanguageSummaryLabel(sum.source_language)}</div></div>
          <div class="item"><div class="k">{t("render.summary_translate_mode")}</div><div class="v">{sum.use_auto_translate ? t("render.summary_translate_on") : t("render.summary_translate_off")}</div></div>
          <div class="item"><div class="k">{t("render.summary_translate_backend")}</div><div class="v">{String(sum.translate_backend || "—")}</div></div>
          <div class="item"><div class="k">{t("render.summary_tts_provider")}</div><div class="v">{String(s.effectiveTts?.tts_provider || "—")}</div></div>
          <div class="item"><div class="k">{t("render.summary_subtitle_mode")}</div><div class="v">{subtitleModeLabel(s.renderSubtitleMode)}</div></div>
        </div>
      </Card>
    {/if}

    {#if s.notice}
      <div class="info-banner">{s.notice}</div>
    {/if}

    <div class="grid-2">
      <!-- Execution column -->
      <div class="stack">
        <Card title={t("render.execution_title")} sub={t("render.execution_sub")} bodyClass="stack">
          {#snippet headerRight()}<StatusBadge kind={lt.kind}>{lt.text}</StatusBadge>{/snippet}
          <div class="artifact-list">
            {#if !downstreamRows.length && !s.extras.length}
              <div class="meta-empty">{t("render.artifacts_empty")}</div>
            {:else}
              {#each downstreamRows as entry}
                {@const st = artifactStatus(entry)}
                <div class="artifact">
                  <div>
                    <div class="artifact-name">{artifactLabel(entry)}</div>
                    <small>{artifactSubtext(entry)}</small>
                  </div>
                  <StatusBadge kind={st.kind}>{st.text}</StatusBadge>
                  <div class="toolbar">
                    <Button disabled={!entry.exists || !entry.rel_path} onclick={() => openArtifact(entry)}>{t("common.open")}</Button>
                    <Button disabled={!entry.exists || !entry.path} onclick={() => revealPath(entry.path)}>{t("common.reveal")}</Button>
                  </div>
                </div>
              {/each}
              {#each s.extras as extra}
                <div class="artifact">
                  <div>
                    <div class="artifact-name">{String(extra.label || t("render.extra_artifacts"))}</div>
                    <small>{t("render.extra_count", { count: String(extra.count || 0) })}</small>
                  </div>
                  <StatusBadge kind="completed">{t("render.extra_ready")}</StatusBadge>
                  <div class="toolbar">
                    <Button disabled={!extra.path} onclick={() => revealPath(extra.path)}>{t("common.reveal")}</Button>
                  </div>
                </div>
              {/each}
            {/if}
          </div>

          <div class="toolbar">
            <Button variant="strong" disabled={!!s.busyAction || !approved} onclick={runAfterApproval}>{t("render.export_video")}</Button>
            <Button onclick={() => ctx.navigate("diagnostics")}>{t("render.open_diagnostics")}</Button>
            <Button onclick={revealOutputFolder}>{t("render.reveal_output")}</Button>
          </div>

          {#if !approved}
            <div class="small-muted">{t("render.locked_hint_export")}</div>
          {/if}
        </Card>
      </div>

      <!-- Output column -->
      <div class="stack">
        <Card title={t("render.preview_title")} sub={t("render.preview_sub")}>
          {#if finalVideo}
            <!-- svelte-ignore a11y_media_has_caption -->
            <video class="render-preview-video" controls preload="metadata" src={finalVideoSrc}></video>
          {:else}
            <div class="thumb render-thumb"></div>
          {/if}
          <div class="kv">
            <div class="item"><div class="k">{t("render.summary_preset")}</div><div class="v">{t("render.summary_preset_value")}</div></div>
            <div class="item"><div class="k">{t("render.summary_audio_mix")}</div><div class="v">{mixModeLabel(s.effectiveTts.mix_mode)}</div></div>
            <div class="item"><div class="k">{t("render.summary_subtitle_mode")}</div><div class="v">{subtitleModeLabel(s.renderSubtitleMode)}</div></div>
            <div class="item"><div class="k">{t("render.summary_output_folder")}</div><div class="v">{jw()}\artifacts\render</div></div>
          </div>
          <div class="toolbar" style="margin-top:16px">
            <Button variant="primary" onclick={revealOutputFolder}>{t("render.reveal")}</Button>
          </div>
        </Card>

        <Card title={t("render.current_title")} sub={t("render.current_sub")}>
          <div class="section-block">
            <div style="font-weight:800">{s.progress?.current_stage_label || t("render.current_idle")}</div>
            <div class="small-muted" style="margin-top:6px">{currentStageSummary()}</div>
            <ProgressBar percent={overallPct} style="margin-top:14px" />
            <div class="small-muted" style="margin-top:8px">{t("render.progress_value", { percent: String(overallPct) })}</div>
          </div>
        </Card>
      </div>
    </div>
  </div>
{/if}
