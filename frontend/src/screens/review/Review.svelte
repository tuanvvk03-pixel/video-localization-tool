<script lang="ts">
  import { onDestroy } from "svelte";
  import { post, ApiError, awaitRunResult, pickFilePath } from "../../lib/api";
  import type { ScreenCtx } from "../../lib/screen";
  import Button from "../../lib/ui/Button.svelte";
  import StatusBadge from "../../lib/ui/StatusBadge.svelte";
  import ProgressBar from "../../lib/ui/ProgressBar.svelte";
  import * as H from "./helpers";

  let { ctx }: { ctx: ScreenCtx } = $props();
  const t = (k: string, v?: Record<string, unknown>) => (ctx?.t ?? ((x: string) => x))(k, v);
  const jw = () => String(ctx?.jobWorkspace || "");
  const pr = () => String(ctx?.parentProjectRoot || "");

  function defaultState(): Record<string, any> {
    return {
      loadedJobWorkspace: "", loading: false, busyAction: "", notice: "",
      cues: [], segments: [], isLongVideo: false, sourceDurationS: 0,
      status: null, progress: null, searchQuery: "", changedOnly: false, pendingOnly: false,
      ttsSettings: H.defaultTtsSettings(), styleSettings: {},
      demoBusy: false, demoNotice: "", demoError: "", demoAudioRel: "", demoAudioBust: 0,
      downstreamLive: null, transcriptionEngine: "", externalSrtOrigin: "",
      voiceCatalog: [], voiceOverrides: {}, overridesDirty: false,
      voiceSamples: [], sampleBusy: false,
    };
  }

  // Shared live proxy via ctx.reviewState — survives the re-mounts triggered by
  // applyJobStatusToEditGate -> requestEditShellRefresh (same as Settings).
  let s = $state<Record<string, any>>((ctx?.reviewState as Record<string, any>) || defaultState());
  if (ctx) ctx.reviewState = s;
  let errorMsg = $state("");
  let currentTime = $state(0);
  let playerHeight = $state(360);
  let videoEl: HTMLVideoElement | undefined = $state();
  let pollTimer: ReturnType<typeof setInterval> | null = null;
  let approveTimer: ReturnType<typeof setInterval> | null = null;
  let duckSaveTimer: ReturnType<typeof setTimeout> | null = null;

  onDestroy(() => {
    if (pollTimer) clearInterval(pollTimer);
    if (approveTimer) clearInterval(approveTimer);
    if (duckSaveTimer) clearTimeout(duckSaveTimer);
  });

  const isBusy = () => !!s.busyAction;
  const useAuto = () => ctx?.importConfig?.use_auto_translate !== false;
  function buildMediaUrl(rel: string, bust?: number): string {
    if (!jw()) return "";
    const p = new URLSearchParams({ workspace: jw(), rel });
    if (bust) p.set("v", String(bust));
    return `/media?${p.toString()}`;
  }
  function asMsg(err: unknown): string {
    if (err instanceof ApiError) return err.summary || err.message;
    return (err as Error)?.message || t("error.generic");
  }

  async function load(force = false) {
    if (!jw()) return;
    if (!force && s.loadedJobWorkspace === jw() && s.cues.length) { startPolling(); return; }
    s.loading = true; s.notice = ""; errorMsg = "";
    try {
      const [statusData, loadData, progressData, segmentsData, videoTts, projectTts, videoStyle, projectStyle, voiceData, overridesData, samplesData] =
        await Promise.all([
          post<any>("/api/status", { job_workspace: jw() }),
          post<any>("/api/load", { job_workspace: jw() }),
          post<any>("/api/job-progress", { job_workspace: jw() }),
          post<any>("/api/list-segments", { job_workspace: jw() }),
          post<any>("/api/get-video-tts", { job_workspace: jw() }).catch(() => ({ settings: {} })),
          pr() ? post<any>("/api/get-project-tts", { project_root: pr() }).catch(() => ({ settings: {} })) : Promise.resolve({ settings: {} }),
          post<any>("/api/get-video-style", { job_workspace: jw() }).catch(() => ({ style: {} })),
          pr() ? post<any>("/api/get-project-style", { project_root: pr() }).catch(() => ({ style: {} })) : Promise.resolve({ style: {} }),
          post<any>("/api/list-voices", {}).catch(() => ({ voices: [] })),
          post<any>("/api/get-voice-overrides", { job_workspace: jw() }).catch(() => ({ overrides: {} })),
          post<any>("/api/voice-samples/list", { job_workspace: jw() }).catch(() => ({ samples: [] })),
        ]);
      const mergedStyle = { ...(projectStyle.style || {}), ...(videoStyle.style || {}) };
      const mergedTts = { ...(projectTts.settings || {}), ...(videoTts.settings || {}) };
      const cues = H.buildCueModels(loadData.cues || [], loadData.source_cues || [], loadData.reference_cues || [], loadData.source_provenance || null)
        .map((c) => ({ ...c, _dirty: false }));
      Object.assign(s, {
        loadedJobWorkspace: jw(), loading: false, cues,
        segments: Array.isArray(segmentsData.segments) ? segmentsData.segments : [],
        isLongVideo: !!segmentsData.is_long_video, sourceDurationS: Number(segmentsData.source_duration_s) || 0,
        status: statusData, progress: progressData, notice: "",
        ttsSettings: H.mergeTtsSettings(mergedTts), styleSettings: mergedStyle,
        demoNotice: "", demoError: "", demoAudioRel: "", demoAudioBust: 0,
        transcriptionEngine: String(statusData.transcription_engine || ""),
        externalSrtOrigin: statusData.external_srt_origin != null ? String(statusData.external_srt_origin) : "",
        voiceCatalog: Array.isArray(voiceData.voices) ? voiceData.voices.filter((v: any) => v && v.voice_id && v.enabled !== false) : [],
        voiceOverrides: (overridesData && typeof overridesData.overrides === "object" && overridesData.overrides) || {},
        overridesDirty: false,
        voiceSamples: Array.isArray(samplesData.samples) ? samplesData.samples : [],
      });
      ctx.applyJobStatusToEditGate?.(ctx, statusData);
      startPolling();
    } catch (err) {
      s.loading = false; errorMsg = asMsg(err);
    }
  }

  function startPolling() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(async () => {
      if (!ctx || s.busyAction) return;
      try {
        const [st, pg] = await Promise.all([
          post<any>("/api/status", { job_workspace: jw() }),
          post<any>("/api/job-progress", { job_workspace: jw() }),
        ]);
        s.status = st; s.progress = pg;
      } catch { /* silent */ }
    }, 3000);
  }

  async function runBusy(name: string, fn: () => Promise<void>) {
    if (!ctx) return;
    errorMsg = ""; s.busyAction = name; s.notice = "";
    try { await fn(); }
    catch (err) { errorMsg = asMsg(err); }
    finally { if (ctx) s.busyAction = ""; }
  }

  // ---- derived ----
  const isApproved = $derived(!!(s.status?.voice_edited || s.status?.voice_edit_status === "voice_edited"));
  const activeCue = $derived.by(() => {
    const ms = Math.floor(currentTime * 1000);
    return s.cues.find((c: H.Cue) => c.start_ms <= ms && ms < c.end_ms) || null;
  });
  const activeKey = $derived(activeCue ? H.cueKey(activeCue) : "");
  const overlayText = $derived.by(() => {
    if (!activeCue) return t("review.player.no_active_cue");
    if (useAuto()) return activeCue.text || t("review.player.no_active_cue");
    return (activeCue.text || "").trim() ? activeCue.text : (activeCue.source_text || t("review.player.no_active_cue"));
  });
  const overlayStyle = $derived(H.overlayStyleString(s.styleSettings, playerHeight));
  const dirtyCount = $derived(s.cues.filter((c: any) => c._dirty).length);
  const changedCount = $derived(s.cues.filter((c: H.Cue) => H.isCueChanged(c)).length);
  const visibleCues = $derived.by(() => {
    const q = H.normalizeText(s.searchQuery);
    return s.cues.filter((c: any) => {
      if (s.changedOnly && !H.isCueChanged(c)) return false;
      if (s.pendingOnly && !c._dirty && !H.isCueChanged(c)) return false;
      if (!q) return true;
      return H.normalizeText(c.source_text).includes(q) || H.normalizeText(c.text).includes(q) || H.normalizeText(c.reference_text).includes(q);
    });
  });
  const durationS = $derived(Number(videoEl?.duration) || s.sourceDurationS || 0);

  function cueStatus(cue: any): { kind: string; text: string } {
    if (cue._dirty) return { kind: "blocked", text: t("review.status.unsaved") };
    if (H.cueKey(cue) === activeKey) return { kind: "running", text: t("review.status.current") };
    if (isApproved) return { kind: "completed", text: t("review.status.approved") };
    if (H.isCueChanged(cue)) return { kind: "blocked", text: t("review.status.changed") };
    return { kind: "queued", text: t("review.status.pending") };
  }

  function seekToCue(cue: any) { if (videoEl) { videoEl.currentTime = Math.max(0, cue.start_ms / 1000); videoEl.focus(); } }
  function seekToSegment(seg: any) { if (videoEl) { videoEl.currentTime = Math.max(0, Number(seg.start_s) || 0); videoEl.focus(); } }
  function onCueInput(cue: any, value: string) { cue.text = value; cue._dirty = true; }
  // Per-cue voice override: empty value = "use shared voice" (drops the entry).
  // A cloned voice is encoded as "xtts:<sample abs path>"; catalog voices use
  // their plain voice_id.
  function cueOverrideVoice(cue: any): string {
    const ov = s.voiceOverrides?.[String(cue.index)];
    if (!ov || typeof ov !== "object") return "";
    const vid = String(ov.voice_id || "");
    if (!vid) return "";
    return String(ov.provider || "") === "xtts" ? `xtts:${vid}` : vid;
  }
  function onCueVoiceChange(cue: any, value: string) {
    const key = String(cue.index);
    const next = { ...(s.voiceOverrides || {}) };
    const prev = next[key] || {};
    if (!value) {
      delete next[key];
    } else if (value.startsWith("xtts:")) {
      next[key] = { ...prev, provider: "xtts", voice_id: value.slice(5) };
    } else {
      const { provider, ...rest } = prev;
      next[key] = { ...rest, voice_id: value };
    }
    s.voiceOverrides = next;
    s.overridesDirty = true;
  }
  async function uploadVoiceSample() {
    if (s.sampleBusy) return;
    s.sampleBusy = true; errorMsg = "";
    try {
      const res = await pickFilePath(["Audio files (*.wav;*.mp3;*.m4a;*.aac;*.flac;*.ogg)", "All files (*.*)"]);
      if (res?.cancelled) return;
      if (!res?.ok || !res.path) throw new Error(res?.error || t("review.sample_pick_unavailable"));
      const data = await post<any>("/api/voice-samples/upload", { job_workspace: jw(), sample_path: res.path });
      s.voiceSamples = Array.isArray(data.samples) ? data.samples : s.voiceSamples;
      s.notice = t("review.sample_uploaded");
    } catch (err) { errorMsg = asMsg(err); }
    finally { s.sampleBusy = false; }
  }
  async function removeVoiceSample(id: string) {
    if (s.sampleBusy || !window.confirm(t("review.sample_confirm_remove"))) return;
    s.sampleBusy = true; errorMsg = "";
    try {
      const data = await post<any>("/api/voice-samples/remove", { job_workspace: jw(), id });
      s.voiceSamples = Array.isArray(data.samples) ? data.samples : [];
    } catch (err) { errorMsg = asMsg(err); }
    finally { s.sampleBusy = false; }
  }
  async function persistVoiceOverrides() {
    const data = await post<any>("/api/save-voice-overrides", { job_workspace: jw(), overrides: s.voiceOverrides || {} });
    s.voiceOverrides = (data && data.overrides) || {};
    s.overridesDirty = false;
  }
  function onCueKeydown(e: KeyboardEvent) {
    if (e.key === " " && videoEl) { e.preventDefault(); videoEl.paused ? videoEl.play().catch(() => {}) : videoEl.pause(); return; }
    if (e.key === "Escape") { e.preventDefault(); (e.currentTarget as HTMLElement).blur(); }
  }

  // ---- style/burn ----
  function patchStyle(patch: Record<string, unknown>) {
    const base = { ...(s.styleSettings || {}) };
    for (const [k, v] of Object.entries(patch)) { if (v === undefined) delete base[k]; else base[k] = v; }
    s.styleSettings = base;
  }
  const saveBurn = () => runBusy("save_burn_style", async () => {
    const data = await post<any>("/api/save-video-style", { job_workspace: jw(), style: H.serializeReviewBurnPatchForApi(s.styleSettings || {}) });
    s.notice = t("review.burn_saved_notice", { path: data?.path != null ? String(data.path) : "" });
  });

  // ---- editor actions ----
  const cuesPayload = () => s.cues.map((c: H.Cue) => ({ index: c.index, start_ms: c.start_ms, end_ms: c.end_ms, text: c.text }));
  const saveDraft = () => runBusy("save_draft", async () => {
    await post("/api/save", { job_workspace: jw(), cues: cuesPayload(), note: "desktop_review_save" });
    s.cues.forEach((c: any) => (c._dirty = false));
    await persistVoiceOverrides();
    const st = await post<any>("/api/status", { job_workspace: jw() });
    s.status = st; s.notice = t("review.notice_saved");
    ctx.applyJobStatusToEditGate?.(ctx, st);
  });

  async function uploadSrt(file: File) {
    await runBusy("upload_translation_srt", async () => {
      const text = await file.text();
      const st = await post<any>("/api/upload-translation", { job_workspace: jw(), srt_text: text });
      s.status = st; ctx.applyJobStatusToEditGate?.(ctx, st); s.notice = t("review.notice_uploaded");
      await load(true);
    });
  }
  function onUploadChange(e: Event) {
    const input = e.target as HTMLInputElement;
    const f = input.files && input.files[0];
    input.value = "";
    if (f) void uploadSrt(f);
  }
  function downloadSourceSrt() {
    const url = buildMediaUrl("artifacts/transcribe/source.srt");
    if (!url) return;
    const a = document.createElement("a");
    a.href = url; a.download = "source.srt"; a.rel = "noopener"; a.style.display = "none";
    document.body.appendChild(a); a.click(); a.remove();
  }

  function deriveProjectName() {
    if (ctx?.parentProject) return String(ctx.parentProject);
    const w = jw().replace(/[\\/]+$/, ""); const parts = w.split(/[\\/]/);
    return parts[parts.length - 1] || "job";
  }
  function buildRunAfterEditBody(toStage: string) {
    const ts = s.ttsSettings;
    const stt: any = (ctx?.settingsState as any) || {};
    const m = stt.loadedJobWorkspace === jw();
    return {
      job_workspace: jw(), project_name: deriveProjectName(), project_root: pr(), to_stage: toStage,
      subtitle_mode: m ? String(stt.renderSubtitleMode || "burn") : "burn",
      tts_provider: m && stt.tts_provider ? String(stt.tts_provider) : (ts.tts_provider || "edge_tts"),
      tts_voice: m && stt.tts_voice ? String(stt.tts_voice) : (ts.tts_voice || ""),
      tts_rate: m && Number.isFinite(Number(stt.tts_rate)) ? Number(stt.tts_rate) : (Number(ts.tts_rate) || 0),
      mix_mode: m && stt.mix_mode ? String(stt.mix_mode) : (ts.mix_mode || "replace_original_speech"),
      mix_duck_gain_db: m && Number.isFinite(Number(stt.mix_duck_gain_db)) ? Number(stt.mix_duck_gain_db) : (Number.isFinite(Number(ts.mix_duck_gain_db)) ? Number(ts.mix_duck_gain_db) : -15),
    };
  }

  function pollDownstream() {
    if (!ctx || s.busyAction !== "approve_downstream") return;
    void post<any>("/api/job-progress", { job_workspace: jw() }).then((d) => {
      if (s.busyAction !== "approve_downstream") return;
      s.downstreamLive = { ...(s.downstreamLive || {}), overall_percent: Number(d.overall_percent) || 0,
        current_stage_label: String(d.current_stage_label || ""), current_stage: String(d.current_stage || ""), lifecycle: String(d.lifecycle || "") };
    }).catch(() => {});
  }

  async function approveForVoice() {
    if (s.busyAction) return;
    let markStatus: any = null;
    await runBusy("approve_save", async () => {
      if (dirtyCount > 0) {
        await post("/api/save", { job_workspace: jw(), cues: cuesPayload(), note: "desktop_review_approve_save" });
        s.cues.forEach((c: any) => (c._dirty = false));
      }
      await persistVoiceOverrides();
      markStatus = await post<any>("/api/mark-edited", { job_workspace: jw() });
      s.status = markStatus; s.notice = t("review.notice_approved");
    });
    if (!markStatus) return;
    ctx.applyJobStatusToEditGate?.(ctx, markStatus);

    let ok = false;
    s.busyAction = "approve_downstream";
    s.downstreamLive = { phase: "tts", overall_percent: 0, current_stage_label: "", current_stage: "", lifecycle: "" };
    approveTimer = setInterval(pollDownstream, 900);
    try {
      await awaitRunResult(jw(), await post<any>("/api/run-after-edit", { ...buildRunAfterEditBody("tts_generated"), async: true }));
      s.downstreamLive = { ...(s.downstreamLive || {}), phase: "render" };
      await awaitRunResult(jw(), await post<any>("/api/run-after-edit", { ...buildRunAfterEditBody("rendered"), async: true }));
      const fin = await post<any>("/api/status", { job_workspace: jw() });
      ctx.applyJobStatusToEditGate?.(ctx, fin);
      s.notice = t("review.notice_downstream_done"); ok = true;
    } catch (err) {
      errorMsg = asMsg(err);
    } finally {
      if (approveTimer) { clearInterval(approveTimer); approveTimer = null; }
      s.busyAction = ""; s.downstreamLive = null;
    }
    if (ok) ctx.navigate("render");
  }

  // ---- duck / demo ----
  const isDuck = $derived(s.ttsSettings.mix_mode === "duck_original_speech");
  const duckPct = $derived(H.duckDbToPercent(s.ttsSettings.mix_duck_gain_db));
  function onDuckInput(value: number) {
    s.ttsSettings.mix_duck_gain_db = H.duckPercentToDb(value);
    s.demoNotice = ""; s.demoError = "";
    if (duckSaveTimer) clearTimeout(duckSaveTimer);
    duckSaveTimer = setTimeout(() => { duckSaveTimer = null; void saveTtsOverride(); }, 350);
  }
  async function saveTtsOverride() {
    const ts = s.ttsSettings;
    try {
      const resp = await post<any>("/api/save-video-tts", { job_workspace: jw(), settings: {
        tts_provider: ts.tts_provider, tts_voice: (ts.tts_voice || "").trim(),
        speed_multiplier: H.clampDuckSpeed(ts.speed_multiplier),
        tts_rate: Math.max(-50, Math.min(50, Math.round((H.clampDuckSpeed(ts.speed_multiplier) - 1) * 100))),
        tts_pitch: Number(ts.tts_pitch) || 0, mix_mode: ts.mix_mode, mix_duck_gain_db: H.clampDuckDb(ts.mix_duck_gain_db),
      } });
      s.ttsSettings = H.mergeTtsSettings(resp?.settings || ts); s.demoError = "";
      s.demoNotice = t("review.demo_save_ok", { db: H.clampDuckDb(s.ttsSettings.mix_duck_gain_db).toFixed(1) });
    } catch (err) { s.demoError = (err as Error)?.message || t("review.demo_save_failed"); }
  }
  async function previewDemo() {
    const ts = s.ttsSettings;
    s.demoBusy = true; s.demoError = ""; s.demoNotice = "";
    try {
      const resp = await post<any>("/api/tts-preview", { job_workspace: jw(), tts_provider: ts.tts_provider,
        tts_voice: (ts.tts_voice || "").trim(), speed_multiplier: H.clampDuckSpeed(ts.speed_multiplier), text: t("review.demo_sample_text") });
      s.demoAudioRel = resp?.rel_path || ""; s.demoAudioBust = Number(resp?.cache_bust) || Date.now();
      s.demoNotice = t("review.demo_play_ready");
    } catch (err) { s.demoError = (err as Error)?.message || t("review.demo_play_failed"); }
    finally { s.demoBusy = false; }
  }

  const bgOn = $derived(!!String(s.styleSettings?.subtitle_background_color || "").trim());

  $effect(() => { void jw(); void load(); });
</script>

{#if errorMsg}
  <div class="error-banner"><div class="error-code">UI</div><div class="error-message">{errorMsg}</div></div>
{/if}

{#if !jw()}
  <div class="card" data-testid="review-empty"><div class="empty-card">
    <div class="empty-icon">✎</div><h3>{t("review.empty_title")}</h3><p>{t("review.empty_body")}</p>
  </div></div>
{:else if s.loading}
  <div class="card" data-testid="review-loading"><div class="empty-card">
    <div class="empty-icon">…</div><h3>{t("review.loading_title")}</h3><p>{t("common.loading")}</p>
  </div></div>
{:else}
  <div class="screen stack" data-testid="review-screen">
    {#if s.busyAction === "approve_downstream" && s.downstreamLive}
      {@const live = s.downstreamLive}
      {@const pct = Math.max(0, Math.min(100, Number(live.overall_percent) || 0))}
      <div class="card review-downstream-progress">
        <div class="work">
          <div class="orb"><div class="ring"></div><div class="ring r2"></div><div class="core"></div></div>
          <h2 class="work-title">{live.phase === "render" ? t("review.downstream.phase_render") : t("review.downstream.phase_tts")}<span class="work-dots"></span></h2>
          <p class="work-sub">{live.current_stage_label || (live.phase === "render" ? t("review.downstream.render_waiting") : t("review.downstream.tts_waiting"))}</p>
          <div class="work-bar">
            <ProgressBar percent={pct} wide />
            <div class="work-bar-foot"><span>{t("review.downstream.progress_percent", { percent: Math.round(pct) })}</span><span>{Math.round(pct)}%</span></div>
          </div>
        </div>
      </div>
    {/if}

    {#if s.notice}<div class="info-banner">{s.notice}</div>{/if}
    <div class="review-banner {isApproved ? 'approved' : ''}">{isApproved ? t("review.banner.approved") : t("review.banner.edit_gate")}</div>

    {#if s.isLongVideo}
      <div class="stack">
        <div class="segment-rail">
          {#each s.segments as seg}
            <button type="button" class="segment {H.segmentClass(seg)}" onclick={() => seekToSegment(seg)}>
              <strong>{t("review.segment.label", { index: seg.index || 0 })}</strong><span>{H.segmentRange(seg)}</span>
            </button>
          {/each}
        </div>
        <div class="small-muted">{t("review.segment.note")}</div>
      </div>
    {/if}

    <div class="review-layout">
      <!-- player column -->
      <div class="stack">
        <div class="player">
          <div class="player-screen" bind:clientHeight={playerHeight}>
            <!-- svelte-ignore a11y_media_has_caption -->
            <video class="review-video" controls preload="metadata" bind:this={videoEl}
              src={buildMediaUrl("input/source.mp4")}
              ontimeupdate={() => (currentTime = Number(videoEl?.currentTime) || 0)}></video>
            <div class="subtitle-overlay" style={overlayStyle}>{overlayText}</div>
          </div>
          <div class="controls">
            <span>{H.formatClock(currentTime)}</span>
            <div class="timeline"><div class="bar" style={`width:${durationS > 0 ? Math.max(0, Math.min(100, (currentTime / durationS) * 100)) : 0}%`}></div></div>
            <span>{H.formatClock(durationS)}</span>
            <span class="tag">{t("review.player.subtitle_on")}</span>
          </div>
        </div>

        <!-- burn layout card -->
        <div class="card review-burn-card">
          <div class="card-header"><div><div class="card-title">{t("review.burn_card_title")}</div><div class="card-sub">{t("review.burn_card_sub")}</div></div></div>
          <div class="card-body stack">
            <div class="small-muted">{t("review.burn_preview_hint")}</div>
            <label class="checkbox-row">
              <input type="checkbox" checked={bgOn} onchange={(e) => patchStyle({ subtitle_background_color: (e.target as HTMLInputElement).checked ? (String(s.styleSettings?.subtitle_background_color || "").trim() || "#000000") : undefined })} />
              {t("settings.subtitle.bg_enabled")}
            </label>
            <div class="scroll-region--palette"><div class="tone-grid">
              {#each H.BURN_PALETTE_TONES as tone}{#each tone as color}
                <button type="button" class="color-swatch {bgOn && H.normalizeHexReview(String(s.styleSettings?.subtitle_background_color || '')) === color ? 'active' : ''}" title={color} style={`background:${color}`} onclick={() => patchStyle({ subtitle_background_color: color })} aria-label={color}></button>
              {/each}{/each}
            </div></div>
            <div class="field"><label>{t("settings.subtitle.custom_hex")}</label>
              <input class="input" type="text" placeholder="#000000" value={String(s.styleSettings?.subtitle_background_color || "").trim()}
                oninput={(e) => patchStyle({ subtitle_background_color: (e.target as HTMLInputElement).value.trim() || undefined })} /></div>
            <div class="field"><label>{t("settings.subtitle.margin_v_label")}</label>
              <input class="input" type="number" min="0" max="500" step="2" value={Math.round(Number(s.styleSettings?.margin_v) || 0)}
                onchange={(e) => { let v = parseInt((e.target as HTMLInputElement).value, 10); if (!Number.isFinite(v)) v = 0; v = Math.max(0, Math.min(500, v)); patchStyle({ margin_v: v }); }} />
              <div class="small-muted">{t("settings.subtitle.margin_v_hint")}</div></div>
            <div class="field"><label>{t("settings.subtitle.font_size_label")}</label>
              <input class="input" type="number" min="0" max="120" step="1" value={Number(s.styleSettings?.font_size) >= 10 ? Math.round(Number(s.styleSettings.font_size)) : 0}
                onchange={(e) => { let fs = parseInt((e.target as HTMLInputElement).value, 10); if (!Number.isFinite(fs)) fs = 0; fs = Math.max(0, Math.min(120, fs)); patchStyle({ font_size: fs >= 10 ? fs : undefined }); }} />
              <div class="small-muted">{t("settings.subtitle.font_size_hint")}</div></div>
            <div class="toolbar"><Button data-testid="review-save-burn" variant="primary" disabled={isBusy()} onclick={saveBurn}>{t("review.burn_save")}</Button></div>
          </div>
        </div>
      </div>

      <!-- editor column -->
      <div class="card">
        <div class="card-header"><div><div class="card-title">{t("review.editor_title")}</div><div class="card-sub">{t("review.editor_sub")}</div></div></div>
        <div class="card-body review-editor">
          <div class="toolbar review-toolbar">
            <input class="input review-search" type="text" placeholder={t("review.search_placeholder")} bind:value={s.searchQuery} />
            <label class="checkbox-row"><input type="checkbox" bind:checked={s.changedOnly} />{t("review.filters.changed_only")}</label>
            <label class="checkbox-row"><input type="checkbox" bind:checked={s.pendingOnly} />{t("review.filters.pending_only")}</label>
          </div>

          <div class="review-clone-row stack">
            <div class="review-clone-head">
              <div class="small-muted">{t("review.clone_hint")}</div>
              <Button data-testid="review-upload-sample" disabled={s.sampleBusy} onclick={uploadVoiceSample}>{s.sampleBusy ? t("common.loading") : t("review.btn.upload_sample")}</Button>
            </div>
            {#if s.voiceSamples.length}
              <div class="review-clone-chips">
                {#each s.voiceSamples as sm}
                  <span class="review-clone-chip">
                    <span class="review-clone-chip-name" title={sm.path}>{sm.id}{#if sm.duration_ms} · {(sm.duration_ms / 1000).toFixed(1)}s{/if}</span>
                    <button type="button" class="review-clone-chip-x" disabled={s.sampleBusy} title={t("review.btn.remove_sample")} aria-label={t("review.btn.remove_sample")} onclick={() => removeVoiceSample(sm.id)}>×</button>
                  </span>
                {/each}
              </div>
            {/if}
          </div>

          {#if !isApproved}
            <div class="review-upload-row stack">
              <div class="small-muted">{t("review.upload_srt_hint")}</div>
              <div class="small-muted">{t("review.download_source_hint")}</div>
              <div class="review-upload-controls">
                <Button onclick={downloadSourceSrt}>{t("review.btn.download_source_srt")}</Button>
                <label class="btn secondary">{t("review.btn.upload_srt")}<input type="file" accept=".srt,text/plain" style="display:none" onchange={onUploadChange} /></label>
              </div>
            </div>
          {/if}

          <div class="review-table-wrap">
            <table class="review-table">
              <thead><tr>
                <th>{t("review.table.index")}</th><th>{t("review.table.timecode")}</th>
                <th>{t("review.table.source")}</th>
                <th>{t(useAuto() ? "review.table.voice_text" : "review.table.voice_text_transcript")}</th>
                <th>{t("review.table.voice")}</th>
                <th>{t("review.table.status")}</th>
              </tr></thead>
              <tbody>
                {#if !visibleCues.length}
                  <tr><td colspan="6" class="skeleton-row">
                    {#if s.cues.length === 0}
                      <div class="stack" style="gap:12px;padding:16px 0">
                        <div>{t("review.empty_no_cues")}</div>
                        <Button variant="secondary" onclick={() => ctx.navigate("settings")}>{t("review.goto_settings")}</Button>
                      </div>
                    {:else}{t("review.empty_filtered")}{/if}
                  </td></tr>
                {:else}
                  {#each visibleCues as cue (H.cueKey(cue))}
                    {@const st = cueStatus(cue)}
                    <tr class="cue-row {H.isCueChanged(cue) ? 'changed' : ''} {cue._dirty ? 'dirty' : ''} {H.cueKey(cue) === activeKey ? 'active' : ''} {cue.provenance_needs_review ? 'needs-review' : ''}">
                      <td>{cue.index}</td>
                      <td><button type="button" class="review-timecode" onclick={() => seekToCue(cue)}>{H.formatMs(cue.start_ms)} → {H.formatMs(cue.end_ms)}</button></td>
                      <td class="cue-source">
                        {#if cue.provenance_source}
                          <div class="cue-source-wrap"><span class="provenance-badge provenance-{cue.provenance_source}" title={t(`review.provenance.${cue.provenance_source}`)}>{H.PROVENANCE_ICON[cue.provenance_source] || "?"}</span><span class="cue-source-text">{cue.source_text || "—"}</span></div>
                        {:else}{cue.source_text || "—"}{/if}
                      </td>
                      <td>
                        {#if !useAuto() && (cue.source_text || "").trim()}<div class="small-muted" style="margin-bottom:6px">{cue.source_text}</div>{/if}
                        <textarea class="cue-textarea" rows={Math.max(2, Math.min(5, H.lineCount(cue.text)))} value={cue.text}
                          oninput={(e) => onCueInput(cue, (e.target as HTMLTextAreaElement).value)} onkeydown={onCueKeydown}></textarea>
                      </td>
                      <td class="cue-voice-cell">
                        <select class="input cue-voice-select" value={cueOverrideVoice(cue)}
                          onchange={(e) => onCueVoiceChange(cue, (e.currentTarget as HTMLSelectElement).value)}>
                          <option value="">{t("review.cue_voice_shared")}</option>
                          {#if s.voiceSamples.length}
                            <optgroup label={t("review.cue_voice_clone_group")}>
                              {#each s.voiceSamples as sm}
                                <option value={`xtts:${sm.path}`}>{sm.id}</option>
                              {/each}
                            </optgroup>
                          {/if}
                          {#each s.voiceCatalog as v}
                            <option value={v.voice_id}>{v.short_name || v.label || v.voice_id}</option>
                          {/each}
                        </select>
                      </td>
                      <td class="cue-status-cell"><StatusBadge kind={st.kind}>{st.text}</StatusBadge></td>
                    </tr>
                  {/each}
                {/if}
              </tbody>
            </table>
          </div>

          <div class="sticky-bar">
            <div>
              <div class="sticky-title">{dirtyCount > 0 ? t("review.sticky.unsaved_count", { count: dirtyCount }) : isApproved ? t("review.sticky.approved_title") : changedCount > 0 ? t("review.sticky.changed_count", { count: changedCount }) : t("review.sticky.clean_title")}</div>
              <div class="small-muted">{dirtyCount > 0 ? t("review.sticky.unsaved_sub") : isApproved ? t("review.sticky.approved_sub") : changedCount > 0 ? t("review.sticky.changed_sub") : t("review.sticky.clean_sub")}</div>
            </div>
            <div class="actions">
              <Button data-testid="review-save-draft" variant="secondary" disabled={isBusy() || (dirtyCount === 0 && !s.overridesDirty)} onclick={saveDraft}>{t("review.btn.save_draft")}</Button>
              <Button data-testid="review-approve" variant="strong" disabled={isBusy() || s.cues.length === 0 || (isApproved && dirtyCount === 0)} onclick={approveForVoice}>{t("review.btn.approve_confirm_voice")}</Button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- demo preview card -->
    <div class="card" data-review-card="demo">
      <div class="card-header"><div><div class="card-title">{t("review.demo_title")}</div><div class="card-sub">{t("review.demo_sub")}</div></div></div>
      <div class="card-body review-demo-body">
        <div class="review-demo-thumb">
          <div class="review-demo-frame">
            <!-- svelte-ignore a11y_media_has_caption -->
            <video class="review-demo-video" muted preload="metadata" playsinline src={buildMediaUrl("input/source.mp4")}></video>
            <div class="review-demo-overlay" style={H.overlayStyleString(s.styleSettings, 220)}>{t("review.demo_sample_text")}</div>
          </div>
          <div class="small-muted">{t("review.demo_unsupported_hint")}</div>
        </div>
        <div class="review-demo-controls stack">
          <div class="toolbar">
            <Button data-testid="review-demo-play" variant="primary" disabled={s.demoBusy} onclick={previewDemo}>{s.demoBusy ? t("review.demo_playing") : t("review.demo_play_voice")}</Button>
            {#if s.demoAudioRel}<audio controls autoplay class="review-demo-audio" src={buildMediaUrl(s.demoAudioRel, s.demoAudioBust)}></audio>{/if}
          </div>
          <div class="small-muted">{t("review.demo_voice_meta", { voice: s.ttsSettings.tts_voice || "—", speed: H.clampDuckSpeed(s.ttsSettings.speed_multiplier).toFixed(2) })}</div>
          <div class="stack review-duck-slider">
            <div class="review-duck-label"><strong>{t("review.duck_gain_label")}</strong><span class="review-duck-value">{t("review.duck_gain_value", { percent: duckPct, db: H.clampDuckDb(s.ttsSettings.mix_duck_gain_db).toFixed(1) })}</span></div>
            <input type="range" min="0" max="100" step="1" class="review-duck-range" value={duckPct} disabled={!isDuck} oninput={(e) => onDuckInput(Number((e.target as HTMLInputElement).value))} />
            <div class="small-muted">{isDuck ? t("review.duck_gain_hint_active") : t("review.duck_gain_hint_disabled")}</div>
          </div>
          {#if s.demoNotice}<div class="info-banner">{s.demoNotice}</div>{/if}
          {#if s.demoError}<div class="error-banner">{s.demoError}</div>{/if}
        </div>
      </div>
    </div>
  </div>
{/if}
