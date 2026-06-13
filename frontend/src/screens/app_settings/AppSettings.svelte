<script lang="ts">
  // App Settings — Svelte port of the legacy desktop/static/screens/app_settings.js.
  // Language, OpenAI key + translation model, Azure Speech profiles (under an
  // "advanced" toggle) and the voice-catalog manager (search / refresh / toggle /
  // preview). Behaviour preserved 1:1; state persists via ctx.appSettingsState.
  // Changing language on save goes through ctx.changeLang (app.js re-mounts the
  // screen so labels re-translate), mirroring the legacy setLang+loadLang+render.
  import { post } from "../../lib/api";
  import type { ScreenCtx } from "../../lib/screen";
  import Button from "../../lib/ui/Button.svelte";
  import StatusBadge from "../../lib/ui/StatusBadge.svelte";

  let { ctx }: { ctx: ScreenCtx } = $props();
  const t = (k: string, v?: Record<string, unknown>) => (ctx?.t ?? ((x: string) => x))(k, v);
  const lang = () => ctx?.getLang?.() ?? "vi";
  const jw = () => String(ctx?.jobWorkspace || "");

  interface Voice {
    provider: string; voice_id: string; label: string; locale: string;
    locale_label: string; locale_label_en: string; gender: string;
    gender_label: string; gender_label_en: string; short_name: string;
    style_tags: string[]; enabled: boolean;
  }

  function defaultState(): Record<string, any> {
    return {
      loading: false, language: lang(), hasKey: false, maskedKey: "", keyInput: "",
      translationModel: "", resolvedTranslationModel: "",
      azureFallbackEnabled: false,
      azurePrimaryHasKey: false, azurePrimaryMaskedKey: "", azurePrimaryKeyInput: "", azurePrimaryRegion: "",
      azureSecondaryHasKey: false, azureSecondaryMaskedKey: "", azureSecondaryKeyInput: "", azureSecondaryRegion: "",
      azureResolvedProfiles: [], voiceCatalog: [], voiceQuery: "", voiceBusy: "",
      voicePreviewRel: "", voicePreviewBust: 0, advancedOpen: false, notice: "",
    };
  }

  let s = $state<Record<string, any>>((ctx?.appSettingsState as Record<string, any>) || defaultState());
  if (ctx) ctx.appSettingsState = s;
  let errorMsg = $state("");

  function showError(err: unknown) { errorMsg = (err instanceof Error ? err.message : String(err)) || ""; }
  function clearError() { errorMsg = ""; }

  function applySettings(data: any) {
    s.hasKey = !!data.has_openai_key;
    s.maskedKey = data.openai_key_masked || "";
    s.keyInput = "";
    s.translationModel = data.openai_translation_model || "";
    s.resolvedTranslationModel = data.resolved_openai_translation_model || "";
    s.azureFallbackEnabled = !!data.azure_speech?.fallback_enabled;
    s.azurePrimaryHasKey = !!data.azure_speech?.primary?.has_key;
    s.azurePrimaryMaskedKey = data.azure_speech?.primary?.key_masked || "";
    s.azurePrimaryKeyInput = "";
    s.azurePrimaryRegion = data.azure_speech?.primary?.region || "";
    s.azureSecondaryHasKey = !!data.azure_speech?.secondary?.has_key;
    s.azureSecondaryMaskedKey = data.azure_speech?.secondary?.key_masked || "";
    s.azureSecondaryKeyInput = "";
    s.azureSecondaryRegion = data.azure_speech?.secondary?.region || "";
    s.azureResolvedProfiles = Array.isArray(data.azure_speech?.resolved_profiles) ? data.azure_speech.resolved_profiles : [];
  }

  async function loadSettings() {
    s.loading = true; s.notice = ""; clearError();
    try {
      const [data, voiceData] = await Promise.all([
        post<any>("/api/get-app-settings", {}),
        post<any>("/api/list-voices", {}),
      ]);
      s.loading = false;
      s.language = data.language || lang();
      applySettings(data);
      s.voiceCatalog = normalizeVoices(voiceData.voices || []);
    } catch (err) {
      s.loading = false;
      showError(err);
    }
  }

  async function saveSettings() {
    clearError();
    const payload: any = {
      language: s.language,
      openai_translation_model: (s.translationModel || "").trim(),
      azure_speech: {
        fallback_enabled: !!s.azureFallbackEnabled,
        primary: { region: (s.azurePrimaryRegion || "").trim() },
        secondary: { region: (s.azureSecondaryRegion || "").trim() },
      },
    };
    if (s.keyInput.trim()) payload.openai_api_key = s.keyInput.trim();
    if (s.azurePrimaryKeyInput.trim()) payload.azure_speech.primary.key = s.azurePrimaryKeyInput.trim();
    if (s.azureSecondaryKeyInput.trim()) payload.azure_speech.secondary.key = s.azureSecondaryKeyInput.trim();
    try {
      const data = await post<any>("/api/save-app-settings", payload);
      applySettings(data);
      s.notice = t("app_settings.notice_saved");
      const changeLang = ctx?.changeLang as ((l: string) => Promise<void>) | undefined;
      if (data.language && data.language !== lang() && typeof changeLang === "function") {
        await changeLang(data.language);
      }
    } catch (err) {
      showError(err);
    }
  }

  async function refreshVoices() {
    s.voiceBusy = "refresh"; s.notice = "";
    try {
      const data = await post<any>("/api/voices/refresh", {});
      s.voiceBusy = ""; s.voiceCatalog = normalizeVoices(data.voices || []); s.notice = t("app_settings.voices_refresh_done");
    } catch (err) { s.voiceBusy = ""; showError(err); }
  }

  async function toggleVoice(voice: Voice, enabled: boolean) {
    s.voiceBusy = `toggle:${voice.provider}:${voice.voice_id}`; s.notice = "";
    try {
      const data = await post<any>("/api/voices/toggle", { provider: voice.provider, voice_id: voice.voice_id, enabled });
      s.voiceBusy = ""; s.voiceCatalog = normalizeVoices(data.voices || []); s.notice = t("app_settings.voices_toggle_done");
    } catch (err) { s.voiceBusy = ""; showError(err); }
  }

  async function previewVoice(voice: Voice) {
    if (!jw()) return;
    s.voiceBusy = `preview:${voice.provider}:${voice.voice_id}`; s.notice = "";
    try {
      const data = await post<any>("/api/tts-preview", {
        job_workspace: jw(), tts_provider: voice.provider, tts_voice: voice.voice_id,
        text: lang() === "vi" ? "Xin chào, đây là giọng đọc thử nghiệm." : "Hello, this is a voice preview.",
      });
      s.voiceBusy = ""; s.voicePreviewRel = data.rel_path || ""; s.voicePreviewBust = Number(data.cache_bust) || Date.now();
      s.notice = t("app_settings.voices_preview_done");
    } catch (err) { s.voiceBusy = ""; showError(err); }
  }

  function normalizeVoices(voices: any[]): Voice[] {
    const out: Voice[] = [];
    for (const item of Array.isArray(voices) ? voices : []) {
      if (!item || !String(item.voice_id || "").trim()) continue;
      out.push({
        provider: String(item.provider || "edge_tts"), voice_id: String(item.voice_id || "").trim(),
        label: String(item.label || item.voice_id).trim(), locale: String(item.locale || "").trim(),
        locale_label: String(item.locale_label || "").trim(), locale_label_en: String(item.locale_label_en || "").trim(),
        gender: String(item.gender || "").trim().toLowerCase(), gender_label: String(item.gender_label || "").trim(),
        gender_label_en: String(item.gender_label_en || "").trim(), short_name: String(item.short_name || "").trim(),
        style_tags: Array.isArray(item.style_tags) ? item.style_tags.map((x: any) => String(x || "").trim()).filter(Boolean) : [],
        enabled: item.enabled !== false,
      });
    }
    return out;
  }

  function voiceLocaleLabel(v: Voice): string {
    return lang() === "vi" ? (v.locale_label || v.locale_label_en || v.locale || "") : (v.locale_label_en || v.locale_label || v.locale || "");
  }
  function voiceGenderLabel(v: Voice): string {
    return lang() === "vi" ? (v.gender_label || v.gender_label_en || v.gender || "") : (v.gender_label_en || v.gender_label || v.gender || "");
  }
  function voiceStyleLabel(v: Voice): string {
    return v.style_tags.length ? v.style_tags.slice(0, 2).join(", ") : "neutral";
  }
  function filteredVoices(voices: Voice[], query: string): Voice[] {
    const q = String(query || "").trim().toLowerCase();
    const sorted = [...voices].sort((a, b) =>
      `${a.locale}:${a.gender}:${a.voice_id}`.localeCompare(`${b.locale}:${b.gender}:${b.voice_id}`));
    if (!q) return sorted;
    return sorted.filter((v) =>
      [v.provider, v.voice_id, v.label, v.locale, voiceLocaleLabel(v), voiceGenderLabel(v), voiceStyleLabel(v)].join(" ").toLowerCase().includes(q));
  }
  function buildVoicePreviewUrl(rel: string, bust: number): string {
    if (!jw()) return "";
    const params = new URLSearchParams({ workspace: jw(), rel });
    if (bust) params.set("v", String(bust));
    return `/media?${params.toString()}`;
  }

  const voiceRows = $derived(filteredVoices(s.voiceCatalog as Voice[], s.voiceQuery));
  const enabledCount = $derived((s.voiceCatalog as Voice[]).filter((v) => v.enabled !== false).length);
  const azureProfilesHint = $derived((() => {
    const profiles = (s.azureResolvedProfiles || []).filter(Boolean).join(", ");
    return profiles ? t("app_settings.azure_hint_profiles", { profiles }) : t("app_settings.azure_hint_env");
  })());

  $effect(() => { void loadSettings(); });
</script>

{#if errorMsg}
  <div class="error-banner" data-testid="app-settings-error"><div class="error-code">UI</div><div class="error-message">{errorMsg}</div></div>
{/if}

<div class="screen stack" data-testid="app-settings-screen">
  <div class="card"><div class="card-body">
    <div class="card-title">{t("app_settings.title")}</div>
    <div class="card-sub">{t("app_settings.sub")}</div>
  </div></div>

  {#if s.notice}<div class="info-banner">{s.notice}</div>{/if}

  {#if s.loading}
    <div class="card"><div class="empty-card"><h3>{t("common.loading")}</h3></div></div>
  {:else}
    <!-- Language -->
    <div class="card"><div class="card-body stack">
      <div class="card-title">{t("app_settings.language_title")}</div>
      <div class="field">
        <label for="as-lang">{t("app_settings.language_label")}</label>
        <select id="as-lang" class="input" bind:value={s.language}>
          <option value="vi">Tiếng Việt</option>
          <option value="en">English</option>
        </select>
      </div>
    </div></div>

    <!-- API key -->
    <div class="card"><div class="card-body stack">
      <div class="card-title">{t("app_settings.api_key_title")}</div>
      <div class="card-sub">{t("app_settings.api_key_sub")}</div>
      {#if s.hasKey}
        <div class="app-settings-key-display">
          <code class="app-settings-key-masked">{s.maskedKey || "****"}</code>
          <StatusBadge kind="completed">{t("app_settings.key_active")}</StatusBadge>
        </div>
      {/if}
      <div class="field">
        <label for="as-key">{t("app_settings.key_label")}</label>
        <input id="as-key" class="input" type="password" placeholder={s.maskedKey || t("app_settings.key_placeholder")} bind:value={s.keyInput} />
      </div>
      <div class="field">
        <label for="as-model">{t("app_settings.translation_model_label")}</label>
        <input id="as-model" class="input" type="text" placeholder={s.resolvedTranslationModel || t("app_settings.translation_model_placeholder")} bind:value={s.translationModel} />
      </div>
      <div class="small-muted">{s.hasKey ? t("app_settings.key_edit_hint") : t("app_settings.key_hint")}</div>
      <div class="small-muted">{t("app_settings.translation_model_hint", { model: s.resolvedTranslationModel || t("app_settings.translation_model_placeholder") })}</div>
    </div></div>

    <!-- Advanced toggle -->
    <div class="card"><div class="card-body stack">
      <div class="card-title">{t("app_settings.advanced_title")}</div>
      <div class="card-sub">{t("app_settings.advanced_sub")}</div>
      <div class="toolbar">
        <Button variant="secondary" onclick={() => (s.advancedOpen = !s.advancedOpen)}>
          {s.advancedOpen ? t("app_settings.advanced_hide") : t("app_settings.advanced_show")}
        </Button>
      </div>
    </div></div>

    {#if s.advancedOpen}
      <div class="card"><div class="card-body stack">
        <div class="card-title">{t("app_settings.azure_title")}</div>
        <div class="card-sub">{t("app_settings.azure_sub")}</div>
        <label class="checkbox-row">
          <input type="checkbox" bind:checked={s.azureFallbackEnabled} />
          <span>{t("app_settings.azure_fallback")}</span>
        </label>

        {#each [{ key: "Primary", titleKey: "app_settings.azure_primary_title" }, { key: "Secondary", titleKey: "app_settings.azure_secondary_title" }] as prof}
          <div class="stack" style="gap:8px">
            <div class="small-muted">{t(prof.titleKey)}</div>
            {#if s[`azure${prof.key}HasKey`]}
              <div class="app-settings-key-display">
                <code class="app-settings-key-masked">{s[`azure${prof.key}MaskedKey`] || "****"}</code>
                <StatusBadge kind="completed">{t("app_settings.key_active")}</StatusBadge>
              </div>
            {/if}
            <div class="field-grid">
              <div class="field">
                <label for="as-az-{prof.key}-key">{t("app_settings.azure_key_label")}</label>
                <input id="as-az-{prof.key}-key" class="input" type="password" placeholder={s[`azure${prof.key}MaskedKey`] || t("app_settings.azure_key_placeholder")} bind:value={s[`azure${prof.key}KeyInput`]} />
              </div>
              <div class="field">
                <label for="as-az-{prof.key}-region">{t("app_settings.azure_region_label")}</label>
                <input id="as-az-{prof.key}-region" class="input" type="text" placeholder={t("app_settings.azure_region_placeholder")} bind:value={s[`azure${prof.key}Region`]} />
              </div>
            </div>
          </div>
        {/each}

        <div class="small-muted">{azureProfilesHint}</div>
      </div></div>
    {/if}

    <!-- Voice catalog -->
    <div class="card"><div class="card-body stack">
      <div class="card-title">{t("app_settings.voices_title")}</div>
      <div class="card-sub">{t("app_settings.voices_sub")}</div>
      <div class="toolbar">
        <input class="input voice-catalog-search" type="search" placeholder={t("app_settings.voices_search")} bind:value={s.voiceQuery} />
        <Button variant="secondary" disabled={!!s.voiceBusy} onclick={refreshVoices}>
          {s.voiceBusy === "refresh" ? t("app_settings.voices_refreshing") : t("app_settings.voices_refresh")}
        </Button>
      </div>
      <div class="small-muted">{t("app_settings.voices_count", { count: voiceRows.length, enabled: enabledCount })}</div>
      <div class="table-wrap voice-catalog-table-wrap">
        <table>
          <thead><tr>
            {#each ["voices_col_locale", "voices_col_voice", "voices_col_gender", "voices_col_style", "voices_col_enabled", "voices_col_preview"] as col}
              <th>{t(`app_settings.${col}`)}</th>
            {/each}
          </tr></thead>
          <tbody>
            {#each voiceRows.slice(0, 160) as voice}
              <tr>
                <td style="white-space:pre-line">{voiceLocaleLabel(voice)}</td>
                <td style="white-space:pre-line">{voice.short_name || voice.label || voice.voice_id}{"\n"}{voice.voice_id}</td>
                <td style="white-space:pre-line">{voiceGenderLabel(voice)}</td>
                <td style="white-space:pre-line">{voiceStyleLabel(voice)}</td>
                <td>
                  <input type="checkbox" checked={voice.enabled !== false} disabled={!!s.voiceBusy}
                    onchange={(e) => toggleVoice(voice, (e.currentTarget as HTMLInputElement).checked)} />
                </td>
                <td>
                  <Button variant="secondary" class="voice-preview-btn" disabled={!!s.voiceBusy || !jw()} onclick={() => previewVoice(voice)}>
                    {s.voiceBusy === `preview:${voice.provider}:${voice.voice_id}` ? t("app_settings.voices_previewing") : t("app_settings.voices_preview")}
                  </Button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      {#if voiceRows.length > 160}<div class="small-muted">{t("app_settings.voices_limited")}</div>{/if}
      {#if s.voicePreviewRel && jw()}
        <!-- svelte-ignore a11y_media_has_caption -->
        <audio class="audio-preview" controls preload="metadata" src={buildVoicePreviewUrl(s.voicePreviewRel, s.voicePreviewBust)}></audio>
      {/if}
    </div></div>

    <div class="toolbar" style="margin-top:8px">
      <Button variant="primary" onclick={saveSettings}>{t("app_settings.save")}</Button>
    </div>
  {/if}
</div>
