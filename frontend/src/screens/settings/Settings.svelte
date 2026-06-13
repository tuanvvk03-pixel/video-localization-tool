<script lang="ts">
  import { onDestroy } from "svelte";
  import { post, ApiError, awaitRunResult, pickFilePath } from "../../lib/api";
  import type { ScreenCtx } from "../../lib/screen";
  import Button from "../../lib/ui/Button.svelte";
  import ProgressBar from "../../lib/ui/ProgressBar.svelte";
  import * as H from "./helpers";

  let { ctx }: { ctx: ScreenCtx } = $props();
  const t = (k: string, v?: Record<string, unknown>) => (ctx?.t ?? ((x: string) => x))(k, v);
  const lang = () => ctx?.getLang?.() ?? "vi";
  const jw = () => String(ctx?.jobWorkspace || "");
  const pr = () => String(ctx?.parentProjectRoot || "");

  function loadPreviewText(): string {
    try {
      const v = window.localStorage.getItem(H.VOICE_PREVIEW_TEXT_KEY);
      return v && v.trim() ? v : H.DEFAULT_VOICE_PREVIEW_TEXT;
    } catch { return H.DEFAULT_VOICE_PREVIEW_TEXT; }
  }
  function savePreviewText(value: string) {
    try { window.localStorage.setItem(H.VOICE_PREVIEW_TEXT_KEY, value || H.DEFAULT_VOICE_PREVIEW_TEXT); } catch { /* ignore */ }
  }

  function defaultState(): Record<string, any> {
    return {
      loadedJobWorkspace: "", loadedProjectRoot: "", loading: false, busyAction: "", notice: "",
      fontOptions: [], voiceCatalog: [], voiceLocaleFilter: "", voiceGenderFilter: "",
      subtitle_font: "", subtitle_background_color: "#000000", bg_enabled: false,
      subtitle_bold: false, subtitle_italic: false, subtitle_align: "center",
      subtitle_margin_v: 0, subtitle_font_size: 0,
      enable_source_cleanup: true, enable_translation_qa: false, use_auto_translate: true,
      source_language: "auto", subtitle_extractor: "audio_only", external_srt_path: "",
      legacy_deprecated_extractor: false, ocr_provider: "paddleocr", ocr_language: "ch",
      ocr_device: "auto", ocr_roi: { x: 0, y: 0.78, w: 1.0, h: 0.22 },
      translate_backend: "block_v2", translate_target: "vi",
      tts_provider: "edge_tts", tts_voice: "vi-VN-HoaiMyNeural", speed_multiplier: 1,
      tts_rate: 0, tts_pitch: 0, mix_mode: "replace_original_speech", mix_duck_gain_db: -15,
      bgm: null, bgmAdvancedOpen: false,
      renderLayout: { aspect_ratio: "16:9", background_path: "", background_original_filename: "",
        logo_path: "", logo_original_filename: "", logo_position: "top-right", logo_scale: 0.15, logo_opacity: 1, logo_margin: 0.03,
        intro_clip_path: "", intro_original_filename: "", outro_clip_path: "", outro_original_filename: "", head_trim_sec: 0, tail_trim_sec: 0 },
      previewAudioRel: "", previewAudioBust: 0, previewText: loadPreviewText(),
      voiceEditGateOpen: false, openaiKeyMissing: false, runUntilEditLive: null,
    };
  }

  // Persist edits across navigation by sharing one reactive object via
  // ctx.settingsState. The edit shell can re-mount this screen mid-run (e.g.
  // applyJobStatusToEditGate -> requestEditShellRefresh), so the *live proxy*
  // must be reused — a snapshot copy would disconnect the in-flight run's state
  // updates (busyAction, etc.) from the freshly mounted component.
  let s = $state<Record<string, any>>(
    (ctx?.settingsState as Record<string, any>) || defaultState(),
  );
  if (ctx) ctx.settingsState = s;
  let errorMsg = $state("");
  let runPollTimer: ReturnType<typeof setInterval> | null = null;

  onDestroy(() => {
    if (runPollTimer) clearInterval(runPollTimer);
  });

  const isBusy = () => !!s.loading || !!s.busyAction;

  function buildMediaUrl(rel: string, bust?: number): string {
    if (!jw()) return "";
    const params = new URLSearchParams({ workspace: jw(), rel });
    if (bust) params.set("v", String(bust));
    return `/media?${params.toString()}`;
  }
  function clearPreviewAudio() { s.previewAudioRel = ""; s.previewAudioBust = 0; }

  async function load(force = false) {
    if (!jw()) return;
    if (!force && s.loadedJobWorkspace === jw() && s.loadedProjectRoot === pr()) return;
    s.loading = true; s.notice = ""; errorMsg = "";
    const fontReq = !force && s.fontOptions.length
      ? Promise.resolve({ fonts: s.fontOptions }) : post<any>("/api/list-system-fonts");
    const voiceReq = !force && s.voiceCatalog.length
      ? Promise.resolve({ voices: s.voiceCatalog }) : post<any>("/api/list-voices");
    try {
      const [videoStyle, videoTts, projectStyle, projectTts, importData, fontData, voiceData, bgmData, renderData] =
        await Promise.all([
          post<any>("/api/get-video-style", { job_workspace: jw() }),
          post<any>("/api/get-video-tts", { job_workspace: jw() }),
          pr() ? post<any>("/api/get-project-style", { project_root: pr() }) : Promise.resolve({ style: {} }),
          pr() ? post<any>("/api/get-project-tts", { project_root: pr() }) : Promise.resolve({ settings: {} }),
          post<any>("/api/get-import-config", { job_workspace: jw() }),
          fontReq, voiceReq,
          post<any>("/api/bgm/status", { job_workspace: jw() }),
          post<any>("/api/render-settings/status", { job_workspace: jw() }),
        ]);
      const mergedStyle = { ...(projectStyle.style || {}), ...(videoStyle.style || {}) };
      const mergedTts = { ...(projectTts.settings || {}), ...(videoTts.settings || {}) };
      const ctxCfg = ctx?.importConfig && ctx.importConfig.job_workspace === jw() ? ctx.importConfig : null;
      const importConfig: any = { ...(importData.config || {}), ...(ctxCfg || {}) };
      const rawEx = String(importConfig?.subtitle_extractor || "audio_only").toLowerCase();
      let legacyDeprecated = false;
      let normalizedExtractor = rawEx;
      if (rawEx === "ocr_only" || rawEx === "hybrid") { legacyDeprecated = true; normalizedExtractor = "audio_only"; }
      else if (rawEx !== "external_srt") normalizedExtractor = "audio_only";
      const fontOptions = H.normalizeFonts(fontData.fonts || []);
      const voiceCatalog = H.normalizeVoices(voiceData.voices || []);
      const ttsProvider = importConfig?.tts_provider || mergedTts.tts_provider || "edge_tts";
      const ttsRate = Number.isFinite(Number(mergedTts.tts_rate)) ? Number(mergedTts.tts_rate) : 0;
      const translateTarget = H.normalizeTargetLanguage(
        importConfig?.translate_target || importConfig?.target_language || importConfig?.target_locale || "vi");
      Object.assign(s, {
        loadedJobWorkspace: jw(), loadedProjectRoot: pr(), loading: false, fontOptions, voiceCatalog,
        subtitle_font: mergedStyle.subtitle_font || "",
        subtitle_background_color: mergedStyle.subtitle_background_color || "#000000",
        bg_enabled: Boolean(mergedStyle.subtitle_background_color),
        subtitle_bold: Boolean(mergedStyle.bold), subtitle_italic: Boolean(mergedStyle.italic),
        subtitle_align: mergedStyle.align || "center",
        use_auto_translate: importConfig?.use_auto_translate ?? true,
        source_language: importConfig?.source_language || "auto",
        translate_target: translateTarget, translate_backend: importConfig?.translate_backend || "block_v2",
        subtitle_extractor: normalizedExtractor,
        external_srt_path: String(importConfig?.external_srt_path || "").trim(),
        legacy_deprecated_extractor: legacyDeprecated,
        ocr_provider: importConfig?.ocr_provider || "paddleocr",
        ocr_language: importConfig?.ocr_language || "ch", ocr_device: importConfig?.ocr_device || "auto",
        ocr_roi: H.normalizeRoi(importConfig?.ocr_roi) || { x: 0, y: 0.78, w: 1.0, h: 0.22 },
        tts_provider: ttsProvider,
        tts_voice: H.resolveVoiceForProvider(voiceCatalog, ttsProvider, mergedTts.tts_voice || "", translateTarget),
        speed_multiplier: Number.isFinite(Number(mergedTts.speed_multiplier))
          ? H.clampSpeed(Number(mergedTts.speed_multiplier)) : H.rateToSpeed(ttsRate),
        tts_rate: ttsRate, tts_pitch: Number.isFinite(Number(mergedTts.tts_pitch)) ? Number(mergedTts.tts_pitch) : 0,
        mix_mode: mergedTts.mix_mode || "replace_original_speech",
        mix_duck_gain_db: Number.isFinite(Number(mergedTts.mix_duck_gain_db))
          ? H.clampDuckDb(Number(mergedTts.mix_duck_gain_db)) : -15,
        bgm: H.normalizeBgm(bgmData?.bgm), bgmAdvancedOpen: false,
        renderLayout: H.normalizeRenderLayout(renderData?.render),
        previewAudioRel: "", previewAudioBust: 0, openaiKeyMissing: false,
        notice: t("settings.notice_loaded"),
      });
    } catch (err) {
      s.loading = false;
      errorMsg = asMsg(err);
    }
  }

  function asMsg(err: unknown): string {
    if (err instanceof ApiError) return err.summary || err.message;
    return (err as Error)?.message || t("error.generic");
  }

  async function runBusy(name: string, fn: () => Promise<void>) {
    if (!ctx) return;
    errorMsg = ""; s.busyAction = name; s.notice = "";
    try { await fn(); }
    catch (err) { errorMsg = asMsg(err); }
    finally { if (ctx) s.busyAction = ""; }
  }

  // ---- payload builders ----
  const buildTypographyStylePayload = () => {
    const p: any = {};
    if ((s.subtitle_font || "").trim()) p.subtitle_font = s.subtitle_font.trim();
    p.bold = !!s.subtitle_bold; p.italic = !!s.subtitle_italic; p.align = s.subtitle_align || "center";
    return p;
  };
  const buildTtsPayload = () => ({
    tts_provider: s.tts_provider, tts_voice: (s.tts_voice || "").trim(),
    speed_multiplier: H.clampSpeed(s.speed_multiplier), tts_rate: H.speedToRate(s.speed_multiplier),
    tts_pitch: Number(s.tts_pitch) || 0, mix_mode: s.mix_mode, mix_duck_gain_db: H.clampDuckDb(s.mix_duck_gain_db),
  });
  const buildBgmPayload = () => {
    const b = H.normalizeBgm(s.bgm);
    if (!b) return {};
    return { original_path: b.original_path, normalized_path: b.normalized_path,
      original_filename: b.original_filename, duration_ms: b.duration_ms, volume_db: H.clampBgmDb(b.volume_db),
      loop: !!b.loop, fade_in_ms: H.clampFadeMs(b.fade_in_ms), fade_out_ms: H.clampFadeMs(b.fade_out_ms) };
  };
  const buildRenderLayoutPayload = () => {
    const l = H.normalizeRenderLayout(s.renderLayout);
    const payload: Record<string, unknown> = { aspect_ratio: l.aspect_ratio, background_path: l.background_path,
      background_original_filename: l.background_original_filename };
    if (l.logo_path) {
      payload.logo_path = l.logo_path;
      payload.logo_original_filename = l.logo_original_filename;
      payload.logo_position = l.logo_position;
      payload.logo_scale = l.logo_scale;
      payload.logo_opacity = l.logo_opacity;
      payload.logo_margin = l.logo_margin;
    }
    if (l.intro_clip_path) { payload.intro_clip_path = l.intro_clip_path; payload.intro_original_filename = l.intro_original_filename; }
    if (l.outro_clip_path) { payload.outro_clip_path = l.outro_clip_path; payload.outro_original_filename = l.outro_original_filename; }
    payload.head_trim_sec = l.head_trim_sec;
    payload.tail_trim_sec = l.tail_trim_sec;
    return payload;
  };
  const buildImportConfigPayload = () => {
    const ex = s.subtitle_extractor || "audio_only";
    const base: any = {
      use_auto_translate: !!s.use_auto_translate, translate_backend: s.translate_backend || "block_v2",
      tts_provider: s.tts_provider || "edge_tts", subtitle_extractor: ex,
      external_srt_path: ex === "external_srt" ? String(s.external_srt_path || "").trim() : "",
      ocr_provider: s.ocr_provider || "paddleocr", ocr_language: s.ocr_language || "ch",
      ocr_device: s.ocr_device || "auto",
    };
    if (ex === "audio_only") base.ocr_roi = H.normalizeRoi(s.ocr_roi) || H.ROI_PRESETS.bottom_band;
    return base;
  };
  const deriveProjectName = () => {
    if (ctx?.parentProject) return String(ctx.parentProject);
    const w = jw().replace(/[\\/]+$/, "");
    const parts = w.split(/[\\/]/);
    return parts[parts.length - 1] || "job";
  };

  // ---- actions ----
  const saveTextAudio = () => runBusy("save_text_audio", async () => {
    const reqs: Promise<any>[] = [
      post("/api/save-video-style", { job_workspace: jw(), style: buildTypographyStylePayload() }),
      post("/api/save-video-tts", { job_workspace: jw(), settings: buildTtsPayload() }),
    ];
    const hadBgm = !!s.bgm;
    if (hadBgm) reqs.push(post("/api/bgm/save", { job_workspace: jw(), bgm: buildBgmPayload() }));
    reqs.push(post("/api/render-settings/save", { job_workspace: jw(), render: buildRenderLayoutPayload() }));
    const r = await Promise.all(reqs);
    const ttsData = r[1]; const bgmData = hadBgm ? r[2] : null; const renderData = hadBgm ? r[3] : r[2];
    if (Number.isFinite(Number(ttsData.settings?.speed_multiplier))) s.speed_multiplier = H.clampSpeed(Number(ttsData.settings.speed_multiplier));
    if (Number.isFinite(Number(ttsData.settings?.tts_rate))) s.tts_rate = Number(ttsData.settings.tts_rate);
    if (bgmData) s.bgm = H.normalizeBgm(bgmData.bgm);
    if (renderData) s.renderLayout = H.normalizeRenderLayout(renderData.render);
    s.notice = t("settings.notice_saved_text_audio", { path: jw() });
  });

  const uploadBgm = () => runBusy("bgm_upload", async () => {
    const res = await pickFilePath(["Audio files (*.mp3;*.wav;*.m4a;*.aac)", "All files (*.*)"]);
    if (res?.cancelled) return;
    if (!res?.ok || !res.path) throw new Error(res?.error || t("settings.bgm.pick_unavailable"));
    const cur = H.normalizeBgm(s.bgm) || ({} as any);
    const data = await post<any>("/api/bgm/upload", { job_workspace: jw(), bgm_path: res.path,
      volume_db: cur.volume_db ?? -20, loop: cur.loop ?? true, fade_in_ms: cur.fade_in_ms ?? 500, fade_out_ms: cur.fade_out_ms ?? 1000 });
    s.bgm = H.normalizeBgm(data.bgm); s.notice = t("settings.bgm.uploaded");
  });
  const saveBgm = () => { if (!s.bgm) return; return runBusy("bgm_save", async () => {
    const data = await post<any>("/api/bgm/save", { job_workspace: jw(), bgm: buildBgmPayload() });
    s.bgm = H.normalizeBgm(data.bgm); s.notice = t("settings.bgm.saved"); }); };
  const removeBgm = () => { if (!s.bgm || !window.confirm(t("settings.bgm.confirm_remove"))) return; return runBusy("bgm_remove", async () => {
    await post("/api/bgm/remove", { job_workspace: jw() }); s.bgm = null; s.bgmAdvancedOpen = false; s.notice = t("settings.bgm.removed"); }); };

  const uploadRenderBg = () => runBusy("render_background_upload", async () => {
    const res = await pickFilePath(["Image files (*.jpg;*.jpeg;*.png;*.webp)", "All files (*.*)"]);
    if (res?.cancelled) return;
    if (!res?.ok || !res.path) throw new Error(res?.error || t("settings.render_layout.pick_unavailable"));
    await post("/api/render-settings/save", { job_workspace: jw(), render: buildRenderLayoutPayload() });
    const data = await post<any>("/api/render-background/upload", { job_workspace: jw(), image_path: res.path });
    s.renderLayout = H.normalizeRenderLayout(data.render); s.notice = t("settings.render_layout.uploaded");
  });
  const saveRenderLayout = () => runBusy("render_layout_save", async () => {
    const data = await post<any>("/api/render-settings/save", { job_workspace: jw(), render: buildRenderLayoutPayload() });
    s.renderLayout = H.normalizeRenderLayout(data.render); s.notice = t("settings.render_layout.saved"); });
  const removeRenderBg = () => { if (!H.normalizeRenderLayout(s.renderLayout).background_path || !window.confirm(t("settings.render_layout.confirm_remove"))) return;
    return runBusy("render_background_remove", async () => {
      const data = await post<any>("/api/render-background/remove", { job_workspace: jw() });
      s.renderLayout = H.normalizeRenderLayout(data.render); s.notice = t("settings.render_layout.removed"); }); };

  // ---- E1: brand logo / watermark overlay ----
  function patchLogo(patch: Record<string, unknown>) {
    s.renderLayout = H.normalizeRenderLayout({ ...s.renderLayout, ...patch });
  }
  const uploadRenderLogo = () => runBusy("render_logo_upload", async () => {
    const res = await pickFilePath(["Image files (*.png;*.jpg;*.jpeg;*.webp)", "All files (*.*)"]);
    if (res?.cancelled) return;
    if (!res?.ok || !res.path) throw new Error(res?.error || t("settings.render_layout.pick_unavailable"));
    await post("/api/render-settings/save", { job_workspace: jw(), render: buildRenderLayoutPayload() });
    const data = await post<any>("/api/render-logo/upload", { job_workspace: jw(), image_path: res.path });
    s.renderLayout = H.normalizeRenderLayout(data.render); s.notice = t("settings.render_layout.logo_uploaded");
  });
  const removeRenderLogo = () => { if (!H.normalizeRenderLayout(s.renderLayout).logo_path || !window.confirm(t("settings.render_layout.logo_confirm_remove"))) return;
    return runBusy("render_logo_remove", async () => {
      const data = await post<any>("/api/render-logo/remove", { job_workspace: jw() });
      s.renderLayout = H.normalizeRenderLayout(data.render); s.notice = t("settings.render_layout.logo_removed"); }); };

  // ---- E2: intro/outro clips + head/tail trim ----
  const uploadClip = (kind: "intro" | "outro") => runBusy(`render_${kind}_upload`, async () => {
    const res = await pickFilePath(["Video files (*.mp4;*.mov;*.mkv;*.webm;*.m4v)", "All files (*.*)"]);
    if (res?.cancelled) return;
    if (!res?.ok || !res.path) throw new Error(res?.error || t("settings.render_layout.pick_unavailable"));
    await post("/api/render-settings/save", { job_workspace: jw(), render: buildRenderLayoutPayload() });
    const data = await post<any>(`/api/render-${kind}/upload`, { job_workspace: jw(), clip_path: res.path });
    s.renderLayout = H.normalizeRenderLayout(data.render); s.notice = t(`settings.render_layout.${kind}_uploaded`);
  });
  const removeClip = (kind: "intro" | "outro") => {
    const has = kind === "intro" ? H.normalizeRenderLayout(s.renderLayout).intro_clip_path : H.normalizeRenderLayout(s.renderLayout).outro_clip_path;
    if (!has || !window.confirm(t("settings.render_layout.clip_confirm_remove"))) return;
    return runBusy(`render_${kind}_remove`, async () => {
      const data = await post<any>(`/api/render-${kind}/remove`, { job_workspace: jw() });
      s.renderLayout = H.normalizeRenderLayout(data.render); s.notice = t(`settings.render_layout.${kind}_removed`); });
  };
  function patchTrim(patch: Record<string, unknown>) { s.renderLayout = H.normalizeRenderLayout({ ...s.renderLayout, ...patch }); }

  const previewVoice = () => runBusy("tts_preview", async () => {
    const text = (s.previewText || "").trim() || H.DEFAULT_VOICE_PREVIEW_TEXT; savePreviewText(text);
    const data = await post<any>("/api/tts-preview", { job_workspace: jw(), tts_provider: s.tts_provider,
      tts_voice: s.tts_voice, speed_multiplier: s.speed_multiplier, text });
    s.previewText = text; s.previewAudioRel = data.rel_path || ""; s.previewAudioBust = Number(data.cache_bust) || Date.now();
    s.notice = t("settings.tts.preview_ready");
  });

  function pollRun() {
    void post<any>("/api/job-progress", { job_workspace: jw() }).then((d) => {
      s.runUntilEditLive = {
        overall_percent: Number(d.overall_percent) || 0,
        current_stage_label: String(d.current_stage_label || ""), current_stage: String(d.current_stage || ""),
        status_label: String(d.status_label || ""), lifecycle: String(d.lifecycle || ""),
        last_error: d.last_error != null ? String(d.last_error) : null,
      };
    }).catch(() => {});
  }

  const runUntilEdit = () => runBusy("run_until_edit", async () => {
    // Managed translation is the default — the server picks the key (BYOK or the
    // platform key), so no local OpenAI-key pre-check here. Always block_v2 +
    // audio ASR (external-SRT import was removed).
    s.openaiKeyMissing = false;
    s.runUntilEditLive = { overall_percent: 0, current_stage_label: "", current_stage: "", status_label: "", lifecycle: "queued", last_error: null };
    pollRun();
    try {
      runPollTimer = setInterval(pollRun, 800);
      try {
        const saved = await post<any>("/api/save-import-config", { job_workspace: jw(), config: buildImportConfigPayload() });
        ctx.importConfig = { job_workspace: jw(), ...(saved?.config || {}) };
      } catch { /* non-fatal */ }
      const runResp = await post<any>("/api/run-until-edit", {
        job_workspace: jw(), project_name: deriveProjectName(), use_auto_translate: true,
        source_language: s.source_language, translate_backend: "block_v2",
        enable_source_cleanup: !!s.enable_source_cleanup, enable_translation_qa: !!s.enable_translation_qa,
        async: true, subtitle_extractor: "audio_only",
      });
      const result = await awaitRunResult<any>(jw(), runResp);
      ctx.applyJobStatusToEditGate?.(ctx, result);
      pollRun();
      const st = result.voice_edit_status || "";
      if (st === "voice_edit_pending") {
        s.voiceEditGateOpen = true; s.notice = t("settings.notice_run_until_edit", { stage: t(`stage.${st}`) }); s.runUntilEditLive = null; return;
      }
      s.voiceEditGateOpen = false;
      s.notice = t("settings.notice_run_until_edit", { stage: t(`stage.${st || "voice_edit_pending"}`) });
      s.runUntilEditLive = null;
      ctx.navigate("review");
    } catch (err) {
      if (err instanceof ApiError && err.code === "api_key_required") { s.openaiKeyMissing = true; s.runUntilEditLive = null; return; }
      // Clear, stage-aware error + log pointer instead of a bare message.
      const stageLabel = s.runUntilEditLive?.current_stage_label || s.runUntilEditLive?.current_stage || "";
      const base = err instanceof ApiError ? (err.message || err.code || "") : asMsg(err);
      const tail = (err instanceof ApiError && Array.isArray(err.logTail) && err.logTail.length)
        ? "\n— Log:\n" + err.logTail.slice(-8).join("\n") : "";
      errorMsg = t("settings.run_failed", { stage: stageLabel || "—", message: base }) + tail;
      s.runUntilEditLive = null;
      return;
    } finally {
      if (runPollTimer) { clearInterval(runPollTimer); runPollTimer = null; }
      if (ctx) s.runUntilEditLive = null;
    }
  });

  // ---- derived (voice picker) ----
  const enabledPool = $derived(H.voicePoolForProvider(s.voiceCatalog, s.tts_provider));
  const localeOptions = $derived.by(() => {
    const seen = new Map<string, string>();
    for (const item of enabledPool) {
      if (!item.locale || seen.has(item.locale)) continue;
      seen.set(item.locale, H.voiceLocaleLabel(item, lang(), t("settings.tts.locale_unknown")));
    }
    return Array.from(seen.entries()).sort((a, b) => a[1].localeCompare(b[1]));
  });
  const filteredVoices = $derived(H.filterVoicePool(enabledPool, s.voiceLocaleFilter, s.voiceGenderFilter));
  const currentMissing = $derived(!!s.tts_voice && !filteredVoices.some((i) => i.voice_id === s.tts_voice));
  const currentVoiceItem = $derived(s.voiceCatalog.find((i: H.VoiceItem) => i.provider === s.tts_provider && i.voice_id === s.tts_voice));
  const voiceGroups = $derived.by(() => {
    const preferredLocale = H.preferredLocaleForTarget(s.translate_target);
    const grouped = new Map<string, H.VoiceItem[]>();
    for (const item of [...filteredVoices].sort(H.compareVoiceEntries)) {
      const locale = item.locale || t("settings.tts.locale_unknown");
      if (!grouped.has(locale)) grouped.set(locale, []);
      grouped.get(locale)!.push(item);
    }
    const groupLabel = (items: H.VoiceItem[], loc: string) => items[0] ? H.voiceLocaleLabel(items[0], lang(), t("settings.tts.locale_unknown")) : loc;
    return Array.from(grouped.entries()).sort((a, b) => {
      if (a[0] === preferredLocale && b[0] !== preferredLocale) return -1;
      if (b[0] === preferredLocale && a[0] !== preferredLocale) return 1;
      return groupLabel(a[1], a[0]).localeCompare(groupLabel(b[1], b[0]));
    }).map(([loc, items]) => ({ label: groupLabel(items, loc), items }));
  });
  const resolveVoiceLabel = $derived(currentVoiceItem ? H.voiceOptionLabel(currentVoiceItem, lang()) : (s.tts_voice || t("settings.tts.voice_placeholder")));
  const mixModeLabel = $derived(s.mix_mode === "duck_original_speech" ? t("settings.tts.mix_duck") : t("settings.tts.mix_replace"));
  const bgmView = $derived(H.normalizeBgm(s.bgm));
  const layoutView = $derived(H.normalizeRenderLayout(s.renderLayout));

  function onVoiceChange(e: Event) { s.tts_voice = (e.target as HTMLSelectElement).value; clearPreviewAudio(); }
  function onSpeed(v: number) { s.speed_multiplier = H.clampSpeed(v); s.tts_rate = H.speedToRate(s.speed_multiplier); clearPreviewAudio(); }

  // font options for the select
  const fontSelectOptions = $derived.by(() => {
    const opts: [string, string][] = [];
    if (s.subtitle_font && !s.fontOptions.some((f: H.FontItem) => f.family === s.subtitle_font)) opts.push([s.subtitle_font, s.subtitle_font]);
    for (const f of s.fontOptions) opts.push([f.family, f.family]);
    return opts.length ? opts : [[s.subtitle_font || "Arial", s.subtitle_font || "Arial"]] as [string, string][];
  });

  $effect(() => { void jw(); void pr(); void load(); });
</script>

{#if errorMsg}
  <div class="error-banner"><div class="error-code">UI</div><div class="error-message">{errorMsg}</div></div>
{/if}

{#if !jw()}
  <div class="card" data-testid="settings-empty">
    <div class="empty-card">
      <div class="empty-icon">⚙</div>
      <h3>{t("settings.empty_title")}</h3>
      <p>{t("settings.empty_body")}</p>
    </div>
  </div>
{:else}
  <div class="screen stack" data-testid="settings-screen">
    {#if s.busyAction === "run_until_edit"}
      {@const live = s.runUntilEditLive}
      {@const pct = Math.max(0, Math.min(100, Number(live?.overall_percent) || 0))}
      <div class="card work-card">
        <div class="work">
          <div class="orb"><div class="ring"></div><div class="ring r2"></div><div class="core"></div></div>
          <h2 class="work-title">{t("settings.run_until_edit_progress_title")}<span class="work-dots"></span></h2>
          <p class="work-sub">{live?.current_stage_label || t("settings.run_until_edit_progress_waiting")}{live?.status_label ? ` · ${live.status_label}` : ""}</p>
          <div class="work-bar">
            <ProgressBar percent={pct} wide />
            <div class="work-bar-foot"><span>{t("settings.translation.progress_percent", { percent: Math.round(pct) })}</span><span>{Math.round(pct)}%</span></div>
          </div>
          {#if live?.last_error}<div class="small-muted run-until-edit-progress-error">{live.last_error}</div>{/if}
        </div>
      </div>
    {:else}
    {#if s.notice}<div class="info-banner">{s.notice}</div>{/if}

    <div class="stack">
      <!-- Text & Audio -->
      <div class="card">
        <div class="card-header"><div><div class="card-title">{t("settings.text_audio.title")}</div><div class="card-sub">{t("settings.text_audio.sub")}</div></div><div class="tag">{t("settings.scope_video")}</div></div>
        <div class="card-body stack">
          <!-- subtitle -->
          <div class="section-block stack">
            <div class="stack" style="gap:6px"><div class="card-title">{t("settings.subtitle.title")}</div><div class="card-sub">{t("settings.subtitle.sub")}</div></div>
            <div class="field-grid">
              <div class="field"><label>{t("settings.subtitle.font")}</label>
                <select class="input" value={s.subtitle_font} onchange={(e) => (s.subtitle_font = (e.target as HTMLSelectElement).value)}>
                  {#each fontSelectOptions as [val, lab]}<option value={val} selected={val === s.subtitle_font}>{lab}</option>{/each}
                </select>
              </div>
              <div class="field"><label>{t("settings.subtitle.mode")}</label><input class="input" type="text" readonly value={t("settings.subtitle.mode_value")} /></div>
            </div>
            <div class="stack" style="gap:10px">
              <div class="small-muted">{t("settings.subtitle.style_tools")}</div>
              <div class="toggle-bar">
                <button type="button" data-testid="style-bold" class="toggle-btn {s.subtitle_bold ? 'active' : ''}" onclick={() => (s.subtitle_bold = !s.subtitle_bold)}>B</button>
                <button type="button" data-testid="style-italic" class="toggle-btn {s.subtitle_italic ? 'active' : ''}" onclick={() => (s.subtitle_italic = !s.subtitle_italic)}>I</button>
                {#each H.ALIGN_OPTIONS as [al, lab]}
                  <button type="button" class="toggle-btn {s.subtitle_align === al ? 'active' : ''}" onclick={() => (s.subtitle_align = al)}>{lab}</button>
                {/each}
              </div>
            </div>
            <div class="small-muted">{t("settings.subtitle.burn_moved_hint")}</div>
            <div class="preview-tile">
              <div class="card-title">{t("settings.subtitle.preview_title")}</div>
              <div style={`flex:1;display:grid;align-items:end;background:var(--bg-0);border-radius:14px;padding:28px;text-align:${H.alignToCss(s.subtitle_align)}`}>
                <span class="subtitle-sample" style={`font-family:${H.buildPreviewFontFamily(s.subtitle_font)};background:${s.bg_enabled ? H.normalizeHex(s.subtitle_background_color) : "transparent"};font-weight:${s.subtitle_bold ? 800 : 500};font-style:${s.subtitle_italic ? "italic" : "normal"}`}>{t("settings.subtitle.preview_sample")}</span>
              </div>
            </div>
          </div>

          <!-- tts -->
          <div class="section-block stack">
            <div class="stack" style="gap:6px"><div class="card-title">{t("settings.tts.title")}</div><div class="card-sub">{t("settings.tts.sub")}</div></div>
            <div class="field-grid">
              <div class="field voice-picker">
                <label>{t("settings.tts.voice")}</label>
                <div class="voice-filter-row">
                  <select class="input voice-filter-select" aria-label={t("settings.tts.filter_locale")} value={s.voiceLocaleFilter} onchange={(e) => (s.voiceLocaleFilter = (e.target as HTMLSelectElement).value)}>
                    <option value="">{t("settings.tts.filter_locale")}: {t("settings.tts.filter_all")}</option>
                    {#each localeOptions as [val, lab]}<option value={val}>{lab}</option>{/each}
                  </select>
                  <select class="input voice-filter-select" aria-label={t("settings.tts.filter_gender")} value={s.voiceGenderFilter} onchange={(e) => (s.voiceGenderFilter = (e.target as HTMLSelectElement).value)}>
                    <option value="">{t("settings.tts.filter_gender")}: {t("settings.tts.filter_all")}</option>
                    <option value="female">{t("settings.tts.filter_female")}</option>
                    <option value="male">{t("settings.tts.filter_male")}</option>
                  </select>
                </div>
                <select class="input" value={s.tts_voice} onchange={onVoiceChange}>
                  {#if currentMissing}
                    <optgroup label={t("settings.tts.current_voice")}>
                      <option value={s.tts_voice} selected>{currentVoiceItem ? H.voiceOptionLabel(currentVoiceItem, lang()) : s.tts_voice}</option>
                    </optgroup>
                  {/if}
                  {#each voiceGroups as group}
                    <optgroup label={group.label}>
                      {#each group.items as item}<option value={item.voice_id} selected={item.voice_id === s.tts_voice}>{H.voiceOptionLabel(item, lang())}</option>{/each}
                    </optgroup>
                  {/each}
                </select>
                {#if currentMissing}<div class="small-muted voice-filter-warning">{t("settings.tts.filter_current_hidden")}</div>{/if}
              </div>
              <div class="field slider-row">
                <label>{t("settings.tts.speed")}</label>
                <div class="slider-meta"><span>{H.formatSpeed(s.speed_multiplier)}</span><span>0.5x ... 2x</span></div>
                <input class="range-input" type="range" min="0.5" max="2" step="0.05" value={s.speed_multiplier} oninput={(e) => onSpeed(Number((e.target as HTMLInputElement).value))} />
              </div>
              <div class="field"><label>{t("settings.tts.mix_mode")}</label>
                <select class="input" value={s.mix_mode} onchange={(e) => (s.mix_mode = (e.target as HTMLSelectElement).value)}>
                  <option value="replace_original_speech">{t("settings.tts.mix_replace")}</option>
                  <option value="duck_original_speech">{t("settings.tts.mix_duck")}</option>
                </select>
              </div>
            </div>
            <details class="advanced-details">
              <summary>{t("settings.tts.advanced")}</summary>
              <div class="field-grid advanced-grid">
                <div class="field slider-row"><label>{t("settings.tts.pitch")}</label>
                  <div class="slider-meta"><span>{H.formatPct(s.tts_pitch)}</span><span>-50 ... +50</span></div>
                  <input class="range-input" type="range" min="-50" max="50" step="1" value={s.tts_pitch} oninput={(e) => { s.tts_pitch = Number((e.target as HTMLInputElement).value); clearPreviewAudio(); }} />
                </div>
                <div class="field slider-row"><label>{t("settings.tts.duck_gain")}</label>
                  <div class="slider-meta"><span>{H.formatDb(s.mix_duck_gain_db)}</span><span>-30 ... 0 dB</span></div>
                  <input class="range-input" type="range" min="-30" max="0" step="1" value={s.mix_duck_gain_db} oninput={(e) => (s.mix_duck_gain_db = H.clampDuckDb(Number((e.target as HTMLInputElement).value)))} />
                </div>
              </div>
            </details>
            <div class="field voice-preview-text-field"><label>{t("settings.tts.preview_text_label")}</label>
              <input class="input" type="text" placeholder={H.DEFAULT_VOICE_PREVIEW_TEXT} value={s.previewText}
                oninput={(e) => { s.previewText = (e.target as HTMLInputElement).value; savePreviewText(s.previewText); clearPreviewAudio(); }} />
            </div>
            <div class="preview-tile">
              <div class="card-title">{t("settings.tts.preview_title")}</div>
              <div class="small-muted">
                <div>{t("settings.tts.voice")}: {resolveVoiceLabel}</div>
                <div>{t("settings.tts.speed")}: {H.formatSpeed(s.speed_multiplier)}</div>
                <div>{t("settings.tts.pitch")}: {H.formatPct(s.tts_pitch)}</div>
                <div>{t("settings.tts.mix_mode")}: {mixModeLabel}</div>
              </div>
              {#if s.previewAudioRel}<audio class="audio-preview" controls preload="metadata" src={buildMediaUrl(s.previewAudioRel, s.previewAudioBust)}></audio>{/if}
              <div class="small-muted">{t("settings.tts.preview_sub")}</div>
            </div>
            <div class="toolbar"><Button variant="strong" disabled={isBusy()} onclick={previewVoice}>{t("settings.tts.test_voice")}</Button></div>
          </div>

          <!-- bgm -->
          <div class="section-block stack bgm-section">
            <div class="stack" style="gap:6px"><div class="card-title">{t("settings.bgm.title")}</div><div class="card-sub">{t("settings.bgm.sub")}</div></div>
            {#if !bgmView}
              <div class="meta-empty">{t("settings.bgm.no_bgm")}</div>
            {:else}
              <div class="bgm-summary"><div class="row-title">{(bgmView.original_filename || bgmView.original_path || bgmView.normalized_path).split(/[\\/]/).pop()}</div>
                <div class="small-muted">{t("settings.bgm.duration", { duration: H.formatBgmDuration(bgmView.duration_ms) })}</div></div>
              <audio class="audio-preview" controls preload="metadata" src={buildMediaUrl(bgmView.normalized_path || bgmView.original_path, Date.now())}></audio>
              <div class="field-grid">
                <div class="field slider-row"><label>{t("settings.bgm.volume")}</label>
                  <div class="slider-meta"><span>{H.formatDb(bgmView.volume_db)}</span><span>-40 ... 0 dB</span></div>
                  <input class="range-input" type="range" min="-40" max="0" step="1" value={bgmView.volume_db} oninput={(e) => (s.bgm = H.normalizeBgm({ ...s.bgm, volume_db: H.clampBgmDb(Number((e.target as HTMLInputElement).value)) }))} />
                </div>
                <div class="switch-row"><div><div style="font-weight:700">{t("settings.bgm.loop")}</div><div class="small-muted">{t("settings.bgm.loop_sub")}</div></div>
                  <label class="checkbox-row"><input type="checkbox" checked={bgmView.loop} onchange={(e) => (s.bgm = H.normalizeBgm({ ...s.bgm, loop: (e.target as HTMLInputElement).checked }))} /></label></div>
              </div>
            {/if}
            <div class="toolbar">
              <Button variant="secondary" disabled={isBusy()} onclick={uploadBgm}>{t("settings.bgm.upload")}</Button>
              {#if bgmView}
                <Button variant="primary" disabled={isBusy()} onclick={saveBgm}>{t("settings.bgm.save")}</Button>
                <Button disabled={isBusy()} onclick={removeBgm}>{t("settings.bgm.remove")}</Button>
              {/if}
            </div>
          </div>

          <!-- render layout -->
          <div class="section-block stack render-layout-section">
            <div class="stack" style="gap:6px"><div class="card-title">{t("settings.render_layout.title")}</div><div class="card-sub">{t("settings.render_layout.sub")}</div></div>
            <div class="field-grid">
              <div class="field"><label>{t("settings.render_layout.aspect_ratio")}</label>
                <select class="input" value={layoutView.aspect_ratio} onchange={(e) => (s.renderLayout = H.normalizeRenderLayout({ ...s.renderLayout, aspect_ratio: (e.target as HTMLSelectElement).value }))}>
                  <option value="16:9">{t("settings.render_layout.aspect_16_9")}</option>
                  <option value="9:16">{t("settings.render_layout.aspect_9_16")}</option>
                </select>
              </div>
            </div>
            {#if layoutView.background_path}
              <div class="bgm-summary"><div class="row-title">{(layoutView.background_original_filename || layoutView.background_path).split(/[\\/]/).pop()}</div>
                <div class="small-muted">{t("settings.render_layout.background_ready")}</div></div>
              <img class="render-background-preview" alt="" src={buildMediaUrl(layoutView.background_path, Date.now())} />
            {:else}
              <div class="meta-empty">{t("settings.render_layout.no_background")}</div>
            {/if}
            <div class="toolbar">
              <Button variant="secondary" disabled={isBusy()} onclick={uploadRenderBg}>{t("settings.render_layout.upload_background")}</Button>
              <Button variant="primary" disabled={isBusy()} onclick={saveRenderLayout}>{t("settings.render_layout.save")}</Button>
              {#if layoutView.background_path}<Button disabled={isBusy()} onclick={removeRenderBg}>{t("settings.render_layout.remove_background")}</Button>{/if}
            </div>

            <!-- E1: brand logo / watermark overlay -->
            <div class="stack" style="gap:6px;margin-top:10px"><div class="card-title">{t("settings.render_layout.logo_title")}</div><div class="card-sub">{t("settings.render_layout.logo_sub")}</div></div>
            {#if layoutView.logo_path}
              <div class="bgm-summary"><div class="row-title">{(layoutView.logo_original_filename || layoutView.logo_path).split(/[\\/]/).pop()}</div>
                <div class="small-muted">{t("settings.render_layout.logo_ready")}</div></div>
              <img class="render-logo-preview" alt="" src={buildMediaUrl(layoutView.logo_path, Date.now())} />
              <div class="field-grid">
                <div class="field"><label>{t("settings.render_layout.logo_position")}</label>
                  <select class="input" value={layoutView.logo_position} onchange={(e) => patchLogo({ logo_position: (e.target as HTMLSelectElement).value })}>
                    <option value="top-left">{t("settings.render_layout.pos_top_left")}</option>
                    <option value="top-right">{t("settings.render_layout.pos_top_right")}</option>
                    <option value="bottom-left">{t("settings.render_layout.pos_bottom_left")}</option>
                    <option value="bottom-right">{t("settings.render_layout.pos_bottom_right")}</option>
                  </select>
                </div>
                <div class="field"><label>{t("settings.render_layout.logo_scale")} ({Math.round(layoutView.logo_scale * 100)}%)</label>
                  <input class="input" type="range" min="2" max="60" step="1" value={Math.round(layoutView.logo_scale * 100)} oninput={(e) => patchLogo({ logo_scale: Number((e.target as HTMLInputElement).value) / 100 })} /></div>
                <div class="field"><label>{t("settings.render_layout.logo_opacity")} ({Math.round(layoutView.logo_opacity * 100)}%)</label>
                  <input class="input" type="range" min="0" max="100" step="1" value={Math.round(layoutView.logo_opacity * 100)} oninput={(e) => patchLogo({ logo_opacity: Number((e.target as HTMLInputElement).value) / 100 })} /></div>
                <div class="field"><label>{t("settings.render_layout.logo_margin")} ({Math.round(layoutView.logo_margin * 100)}%)</label>
                  <input class="input" type="range" min="0" max="20" step="1" value={Math.round(layoutView.logo_margin * 100)} oninput={(e) => patchLogo({ logo_margin: Number((e.target as HTMLInputElement).value) / 100 })} /></div>
              </div>
            {:else}
              <div class="meta-empty">{t("settings.render_layout.no_logo")}</div>
            {/if}
            <div class="toolbar">
              <Button variant="secondary" disabled={isBusy()} onclick={uploadRenderLogo}>{t("settings.render_layout.upload_logo")}</Button>
              {#if layoutView.logo_path}
                <Button variant="primary" disabled={isBusy()} onclick={saveRenderLayout}>{t("settings.render_layout.save")}</Button>
                <Button disabled={isBusy()} onclick={removeRenderLogo}>{t("settings.render_layout.remove_logo")}</Button>
              {/if}
            </div>

            <!-- E2: intro/outro clips + head/tail trim -->
            <div class="stack" style="gap:6px;margin-top:10px"><div class="card-title">{t("settings.render_layout.clips_title")}</div><div class="card-sub">{t("settings.render_layout.clips_sub")}</div></div>
            <div class="field-grid">
              <div class="field"><label>{t("settings.render_layout.head_trim")} ({layoutView.head_trim_sec}s)</label>
                <input class="input" type="number" min="0" max="600" step="0.5" value={layoutView.head_trim_sec}
                  onchange={(e) => patchTrim({ head_trim_sec: Number((e.target as HTMLInputElement).value) })} />
                <div class="small-muted">{t("settings.render_layout.head_trim_hint")}</div></div>
              <div class="field"><label>{t("settings.render_layout.tail_trim")} ({layoutView.tail_trim_sec}s)</label>
                <input class="input" type="number" min="0" max="600" step="0.5" value={layoutView.tail_trim_sec}
                  onchange={(e) => patchTrim({ tail_trim_sec: Number((e.target as HTMLInputElement).value) })} />
                <div class="small-muted">{t("settings.render_layout.tail_trim_hint")}</div></div>
            </div>
            <div class="clip-row">
              <div class="clip-col">
                <div class="row-title">{t("settings.render_layout.intro_clip")}</div>
                {#if layoutView.intro_clip_path}
                  <div class="small-muted">{(layoutView.intro_original_filename || layoutView.intro_clip_path).split(/[\\/]/).pop()}</div>
                {:else}<div class="meta-empty">{t("settings.render_layout.no_clip")}</div>{/if}
                <div class="toolbar">
                  <Button variant="secondary" disabled={isBusy()} onclick={() => uploadClip("intro")}>{t("settings.render_layout.upload_intro")}</Button>
                  {#if layoutView.intro_clip_path}<Button disabled={isBusy()} onclick={() => removeClip("intro")}>{t("settings.render_layout.remove_clip")}</Button>{/if}
                </div>
              </div>
              <div class="clip-col">
                <div class="row-title">{t("settings.render_layout.outro_clip")}</div>
                {#if layoutView.outro_clip_path}
                  <div class="small-muted">{(layoutView.outro_original_filename || layoutView.outro_clip_path).split(/[\\/]/).pop()}</div>
                {:else}<div class="meta-empty">{t("settings.render_layout.no_clip")}</div>{/if}
                <div class="toolbar">
                  <Button variant="secondary" disabled={isBusy()} onclick={() => uploadClip("outro")}>{t("settings.render_layout.upload_outro")}</Button>
                  {#if layoutView.outro_clip_path}<Button disabled={isBusy()} onclick={() => removeClip("outro")}>{t("settings.render_layout.remove_clip")}</Button>{/if}
                </div>
              </div>
            </div>
            <div class="toolbar"><Button variant="primary" disabled={isBusy()} onclick={saveRenderLayout}>{t("settings.render_layout.save")}</Button></div>
          </div>

          <div class="toolbar">
            <Button variant="secondary" disabled={isBusy()} onclick={() => load(true)}>{t("settings.reload")}</Button>
            <Button data-testid="save-text-audio" variant="primary" disabled={isBusy()} onclick={saveTextAudio}>{t("settings.text_audio.save")}</Button>
          </div>
        </div>
      </div>

      <!-- Dịch (run) -->
      <div class="card">
        <div class="card-header"><div><div class="card-title">{t("settings.translation.title")}</div><div class="card-sub">{t("settings.translation.sub")}</div></div></div>
        <div class="card-body stack">
          <div class="field-grid">
            <div class="field"><label>{t("settings.translation.source_language")}</label>
              <select class="input" value={s.source_language} onchange={(e) => (s.source_language = (e.target as HTMLSelectElement).value)}>
                <option value="auto">{t("settings.translation.source_language_auto")}</option>
                <option value="zh">{t("settings.translation.source_language_zh")}</option>
                <option value="en">{t("settings.translation.source_language_en")}</option>
                <option value="ja">{t("settings.translation.source_language_ja")}</option>
                <option value="ko">{t("settings.translation.source_language_ko")}</option>
              </select>
            </div>
          </div>
          {#if s.openaiKeyMissing}
            <div class="section-block stack inline-action-banner" data-testid="api-key-missing" style="gap:10px">
              <div class="small-muted">{t("settings.translation.api_key_required")}</div>
              <div class="toolbar"><Button variant="secondary" disabled={isBusy()} onclick={() => ctx.navigate("app_settings")}>{t("settings.translation.go_to_app_settings")}</Button></div>
            </div>
          {/if}
          <details class="advanced-details">
            <summary>{t("settings.tts.advanced")}</summary>
            <div class="section-block">
              <div class="switch-row"><div><div style="font-weight:700">{t("settings.translation.cleanup_title")}</div><div class="small-muted">{t("settings.translation.cleanup_sub")}</div></div>
                <label class="checkbox-row"><input type="checkbox" checked={s.enable_source_cleanup} onchange={(e) => (s.enable_source_cleanup = (e.target as HTMLInputElement).checked)} /></label></div>
              <div class="switch-row"><div><div style="font-weight:700">{t("settings.translation.qa_title")}</div><div class="small-muted">{t("settings.translation.qa_sub")}</div></div>
                <label class="checkbox-row"><input type="checkbox" checked={s.enable_translation_qa} onchange={(e) => (s.enable_translation_qa = (e.target as HTMLInputElement).checked)} /></label></div>
            </div>
          </details>
          <div class="toolbar">
            <Button data-testid="run-until-edit" variant="strong" disabled={isBusy()} onclick={runUntilEdit}>
              {t("settings.translation.run_until_edit_auto")}
            </Button>
          </div>
        </div>
      </div>
    </div>
    {/if}
  </div>

  {#if s.voiceEditGateOpen}
    <div class="voice-edit-gate-backdrop" role="dialog" aria-modal="true">
      <div class="voice-edit-gate-card stack">
        <h3 class="voice-edit-gate-title">{t("settings.voice_edit_gate.title")}</h3>
        <p class="voice-edit-gate-body">{t("settings.voice_edit_gate.body")}</p>
        <div class="voice-edit-gate-actions">
          <Button variant="secondary" onclick={() => { s.voiceEditGateOpen = false; ctx.navigate("review"); }}>{t("settings.voice_edit_gate.pause")}</Button>
          <Button variant="strong" onclick={() => { s.voiceEditGateOpen = false; ctx.pendingVoiceEditContinue = true; ctx.navigate("render"); }}>{t("settings.voice_edit_gate.continue")}</Button>
        </div>
      </div>
    </div>
  {/if}
{/if}
