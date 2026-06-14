<script lang="ts">
  import { onDestroy } from "svelte";
  import { post, pickLocalFile, pickLocalFiles, ApiError } from "../../lib/api";
  import type { ScreenCtx } from "../../lib/screen";
  import { normalizeRenderLayout, addTransformPayload, type RenderLayout } from "../settings/helpers";
  import Button from "../../lib/ui/Button.svelte";
  import StatusBadge from "../../lib/ui/StatusBadge.svelte";

  let { ctx }: { ctx: ScreenCtx } = $props();
  const t = (k: string, v?: Record<string, unknown>) => (ctx?.t ?? ((x: string) => x))(k, v);

  let projectName = $state("");
  let projectRoot = $state("");
  let videos = $state<any[]>([]);
  let statuses = $state<Record<string, any>>({});
  let voiceCatalog = $state<any[]>([]);
  let cfg = $state({ tts_provider: "edge_tts", tts_voice: "", mix_mode: "replace_original_speech" });
  let busy = $state("");
  let running = $state(false);
  let notice = $state("");
  let errorMsg = $state("");
  let branding = $state<RenderLayout | null>(null);
  let pollTimer: ReturnType<typeof setInterval> | null = null;

  onDestroy(() => { if (pollTimer) clearInterval(pollTimer); });

  $effect(() => { void loadVoices(); });
  async function loadVoices() {
    try {
      const d = await post<any>("/api/list-voices", {});
      voiceCatalog = Array.isArray(d.voices) ? d.voices.filter((v: any) => v && v.voice_id && v.enabled !== false) : [];
    } catch { /* non-fatal */ }
  }

  async function run(name: string, fn: () => Promise<void>) {
    errorMsg = ""; busy = name; notice = "";
    try { await fn(); }
    catch (e) { errorMsg = e instanceof ApiError ? (e.summary || e.message) : ((e as Error)?.message || "error"); }
    finally { busy = ""; }
  }
  const isBusy = () => !!busy || running;

  const createProject = () => run("create", async () => {
    const nm = projectName.trim();
    if (!nm) throw new Error(t("projects.name_required"));
    const d = await post<any>("/api/init-project", {
      project_name: nm,
      config_overrides: {
        tts_provider: cfg.tts_provider,
        tts_voice: cfg.tts_voice.trim(),
        mix_mode: cfg.mix_mode,
        translate_backend: "block_v2",
      },
    });
    projectRoot = String(d.project_root || "");
    notice = t("projects.created");
    await refresh();
  });

  const addVideos = () => run("add", async () => {
    if (!projectRoot) throw new Error(t("projects.create_first"));
    const res = await pickLocalFiles({ filters: ["Video files (*.mp4;*.mov;*.mkv;*.webm)", "All files (*.*)"] });
    if (res?.cancelled) return;
    const paths = res?.paths || [];
    if (!paths.length) throw new Error(res?.error || t("projects.pick_unavailable"));
    let added = 0;
    const failed: string[] = [];
    for (const p of paths) {
      try { await post("/api/add-video-to-project", { project_root: projectRoot, video: p }); added++; }
      catch { failed.push(p.split(/[\\/]/).pop() || p); }
    }
    notice = t("projects.added", { count: added }) + (failed.length ? ` (${t("projects.add_failed", { count: failed.length })})` : "");
    await refresh();
  });

  async function refresh() {
    if (!projectRoot) return;
    const d = await post<any>("/api/get-project", { project_root: projectRoot });
    videos = Array.isArray(d.videos) ? d.videos : [];
    const map: Record<string, any> = {};
    for (const s of (d.statuses || [])) map[String(s.video_id)] = s;
    statuses = map;
    await loadBranding();
  }

  // ---- F1.1: shared branding (reuses the per-video render endpoints, targeting
  // the project root as the template workspace) ----
  async function loadBranding() {
    if (!projectRoot) return;
    try {
      const d = await post<any>("/api/render-settings/status", { job_workspace: projectRoot });
      branding = normalizeRenderLayout(d.render || {});
    } catch { /* non-fatal */ }
  }
  function brandPayload(): Record<string, unknown> {
    const l = branding || normalizeRenderLayout({});
    const p: Record<string, unknown> = {
      aspect_ratio: l.aspect_ratio, background_path: l.background_path,
      background_original_filename: l.background_original_filename,
      head_trim_sec: l.head_trim_sec, tail_trim_sec: l.tail_trim_sec,
    };
    if (l.logo_path) Object.assign(p, { logo_path: l.logo_path, logo_original_filename: l.logo_original_filename,
      logo_position: l.logo_position, logo_scale: l.logo_scale, logo_opacity: l.logo_opacity, logo_margin: l.logo_margin });
    if (l.intro_clip_path) Object.assign(p, { intro_clip_path: l.intro_clip_path, intro_original_filename: l.intro_original_filename });
    if (l.outro_clip_path) Object.assign(p, { outro_clip_path: l.outro_clip_path, outro_original_filename: l.outro_original_filename });
    addTransformPayload(p, l);
    return p;
  }
  function patchBrand(patch: Record<string, unknown>) { branding = normalizeRenderLayout({ ...(branding || {}), ...patch }); }
  const saveBranding = () => run("brand_save", async () => {
    const d = await post<any>("/api/render-settings/save", { job_workspace: projectRoot, render: brandPayload() });
    branding = normalizeRenderLayout(d.render); notice = t("projects.brand_saved");
  });
  const uploadBrandLogo = () => run("brand_logo", async () => {
    const res = await pickLocalFile({ filters: ["Image files (*.png;*.jpg;*.jpeg;*.webp)", "All files (*.*)"] });
    if (res?.cancelled) return;
    if (!res?.ok || !res.path) throw new Error(res?.error || t("projects.pick_unavailable"));
    await post("/api/render-settings/save", { job_workspace: projectRoot, render: brandPayload() });
    const d = await post<any>("/api/render-logo/upload", { job_workspace: projectRoot, image_path: res.path });
    branding = normalizeRenderLayout(d.render);
  });
  const removeBrandLogo = () => run("brand_logo_rm", async () => {
    const d = await post<any>("/api/render-logo/remove", { job_workspace: projectRoot }); branding = normalizeRenderLayout(d.render);
  });
  const uploadBrandClip = (kind: "intro" | "outro") => run(`brand_${kind}`, async () => {
    const res = await pickLocalFile({ filters: ["Video files (*.mp4;*.mov;*.mkv;*.webm)", "All files (*.*)"] });
    if (res?.cancelled) return;
    if (!res?.ok || !res.path) throw new Error(res?.error || t("projects.pick_unavailable"));
    await post("/api/render-settings/save", { job_workspace: projectRoot, render: brandPayload() });
    const d = await post<any>(`/api/render-${kind}/upload`, { job_workspace: projectRoot, clip_path: res.path });
    branding = normalizeRenderLayout(d.render);
  });
  const removeBrandClip = (kind: "intro" | "outro") => run(`brand_${kind}_rm`, async () => {
    const d = await post<any>(`/api/render-${kind}/remove`, { job_workspace: projectRoot }); branding = normalizeRenderLayout(d.render);
  });

  const runAll = () => run("run", async () => {
    if (!projectRoot || !videos.length) throw new Error(t("projects.no_videos"));
    running = true;
    try {
      await post("/api/run-project", { project_root: projectRoot, async: true });
      startPolling();
    } catch (e) { running = false; throw e; }
  });

  function startPolling() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(async () => {
      try {
        await refresh();
        if (videos.length && videos.every((v) => isDone(statuses[v.video_id]))) {
          running = false;
          if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
          notice = t("projects.done");
        }
      } catch { /* keep polling */ }
    }, 3000);
  }

  function stageOf(s: any): string { return String(s?.current_stage || s?.status || "queued"); }
  function isDone(s: any): boolean { const st = stageOf(s); return st.includes("rendered") || st.includes("failed"); }
  function statusKind(s: any): string {
    const st = stageOf(s);
    if (st.includes("failed")) return "blocked";
    if (st.includes("rendered")) return "completed";
    if (running) return "running";
    return "queued";
  }
  function outputUrl(v: any): string {
    const ws = String(v?.workspace || "");
    if (!ws) return "";
    const p = new URLSearchParams({ workspace: ws, rel: "artifacts/render/final.mp4", v: String(Date.now()) });
    return `/media?${p.toString()}`;
  }
  const doneCount = $derived(videos.filter((v) => stageOf(statuses[v.video_id]).includes("rendered")).length);
  const failedCount = $derived(videos.filter((v) => stageOf(statuses[v.video_id]).includes("failed")).length);
  const bv = $derived(branding || normalizeRenderLayout({}));
  const clipName = (p: string) => (p || "").split(/[\\/]/).pop();
</script>

<div class="screen stack" data-testid="projects-screen">
  {#if errorMsg}<div class="error-banner"><div class="error-code">UI</div><div class="error-message">{errorMsg}</div></div>{/if}
  {#if notice}<div class="info-banner">{notice}</div>{/if}

  <div class="card">
    <div class="card-header"><div><div class="card-title">{t("projects.title")}</div><div class="card-sub">{t("projects.sub")}</div></div></div>
    <div class="card-body stack">
      <!-- shared config -->
      <div class="field-grid">
        <div class="field"><label>{t("projects.cfg_provider")}</label>
          <select class="input" value={cfg.tts_provider} onchange={(e) => (cfg.tts_provider = (e.target as HTMLSelectElement).value)} disabled={!!projectRoot}>
            <option value="edge_tts">edge_tts</option>
            <option value="azure_tts">azure_tts</option>
          </select>
        </div>
        <div class="field"><label>{t("projects.cfg_voice")}</label>
          <select class="input" value={cfg.tts_voice} onchange={(e) => (cfg.tts_voice = (e.target as HTMLSelectElement).value)} disabled={!!projectRoot}>
            <option value="">{t("projects.cfg_voice_default")}</option>
            {#each voiceCatalog as v}<option value={v.voice_id}>{v.short_name || v.label || v.voice_id}</option>{/each}
          </select>
        </div>
        <div class="field"><label>{t("projects.cfg_mix")}</label>
          <select class="input" value={cfg.mix_mode} onchange={(e) => (cfg.mix_mode = (e.target as HTMLSelectElement).value)} disabled={!!projectRoot}>
            <option value="replace_original_speech">{t("settings.tts.mix_replace")}</option>
            <option value="duck_original_speech">{t("settings.tts.mix_duck")}</option>
            <option value="keep_music_replace_voice">{t("settings.tts.mix_keep_music")}</option>
          </select>
        </div>
      </div>

      {#if !projectRoot}
        <div class="toolbar">
          <input class="input" style="max-width:320px" type="text" placeholder={t("projects.name_placeholder")} bind:value={projectName} />
          <Button variant="primary" disabled={isBusy()} onclick={createProject}>{t("projects.create")}</Button>
        </div>
        <div class="small-muted">{t("projects.create_hint")}</div>
      {:else}
        <div class="small-muted">{t("projects.open_label")}: {projectRoot}</div>
        <div class="toolbar">
          <Button variant="secondary" disabled={isBusy()} onclick={addVideos}>{t("projects.add_videos")}</Button>
          <Button variant="strong" disabled={isBusy() || !videos.length} onclick={runAll}>{running ? t("projects.running") : t("projects.run_all")}</Button>
          <Button disabled={isBusy()} onclick={() => run("refresh", refresh)}>{t("projects.refresh")}</Button>
        </div>
        <div class="small-muted">{t("projects.cfg_locked_hint")}</div>
      {/if}
    </div>
  </div>

  {#if projectRoot}
    <!-- F1.1: shared branding applied to every video at run time -->
    <div class="card">
      <div class="card-header"><div><div class="card-title">{t("projects.brand_title")}</div><div class="card-sub">{t("projects.brand_sub")}</div></div></div>
      <div class="card-body stack">
        <div class="field-grid">
          <div class="field"><label>{t("settings.render_layout.aspect_ratio")}</label>
            <select class="input" value={bv.aspect_ratio} onchange={(e) => patchBrand({ aspect_ratio: (e.target as HTMLSelectElement).value })}>
              <option value="16:9">{t("settings.render_layout.aspect_16_9")}</option>
              <option value="9:16">{t("settings.render_layout.aspect_9_16")}</option>
            </select></div>
          <div class="field"><label>{t("settings.render_layout.head_trim")} ({bv.head_trim_sec}s)</label>
            <input class="input" type="number" min="0" max="600" step="0.5" value={bv.head_trim_sec} onchange={(e) => patchBrand({ head_trim_sec: Number((e.target as HTMLInputElement).value) })} /></div>
          <div class="field"><label>{t("settings.render_layout.tail_trim")} ({bv.tail_trim_sec}s)</label>
            <input class="input" type="number" min="0" max="600" step="0.5" value={bv.tail_trim_sec} onchange={(e) => patchBrand({ tail_trim_sec: Number((e.target as HTMLInputElement).value) })} /></div>
          {#if bv.logo_path}
            <div class="field"><label>{t("settings.render_layout.logo_position")}</label>
              <select class="input" value={bv.logo_position} onchange={(e) => patchBrand({ logo_position: (e.target as HTMLSelectElement).value })}>
                <option value="top-left">{t("settings.render_layout.pos_top_left")}</option>
                <option value="top-right">{t("settings.render_layout.pos_top_right")}</option>
                <option value="bottom-left">{t("settings.render_layout.pos_bottom_left")}</option>
                <option value="bottom-right">{t("settings.render_layout.pos_bottom_right")}</option>
              </select></div>
          {/if}
        </div>
        <div class="clip-row">
          <div class="clip-col"><div class="row-title">{t("settings.render_layout.logo_title")}</div>
            <div class="small-muted">{bv.logo_path ? clipName(bv.logo_original_filename || bv.logo_path) : t("settings.render_layout.no_logo")}</div>
            <div class="toolbar"><Button variant="secondary" disabled={isBusy()} onclick={uploadBrandLogo}>{t("settings.render_layout.upload_logo")}</Button>
              {#if bv.logo_path}<Button disabled={isBusy()} onclick={removeBrandLogo}>{t("settings.render_layout.remove_logo")}</Button>{/if}</div></div>
          <div class="clip-col"><div class="row-title">{t("settings.render_layout.intro_clip")}</div>
            <div class="small-muted">{bv.intro_clip_path ? clipName(bv.intro_original_filename || bv.intro_clip_path) : t("settings.render_layout.no_clip")}</div>
            <div class="toolbar"><Button variant="secondary" disabled={isBusy()} onclick={() => uploadBrandClip("intro")}>{t("settings.render_layout.upload_intro")}</Button>
              {#if bv.intro_clip_path}<Button disabled={isBusy()} onclick={() => removeBrandClip("intro")}>{t("settings.render_layout.remove_clip")}</Button>{/if}</div></div>
          <div class="clip-col"><div class="row-title">{t("settings.render_layout.outro_clip")}</div>
            <div class="small-muted">{bv.outro_clip_path ? clipName(bv.outro_original_filename || bv.outro_clip_path) : t("settings.render_layout.no_clip")}</div>
            <div class="toolbar"><Button variant="secondary" disabled={isBusy()} onclick={() => uploadBrandClip("outro")}>{t("settings.render_layout.upload_outro")}</Button>
              {#if bv.outro_clip_path}<Button disabled={isBusy()} onclick={() => removeBrandClip("outro")}>{t("settings.render_layout.remove_clip")}</Button>{/if}</div></div>
        </div>

        <div class="stack" style="gap:6px;margin-top:8px"><div class="card-title">{t("settings.render_layout.tx_title")}</div><div class="card-sub">{t("settings.render_layout.tx_sub")}</div></div>
        <label class="checkbox-row"><input type="checkbox" checked={bv.transform_hflip} onchange={(e) => patchBrand({ transform_hflip: (e.target as HTMLInputElement).checked })} />{t("settings.render_layout.tx_hflip")}</label>
        <div class="field-grid">
          <div class="field"><label>{t("settings.render_layout.tx_speed")} ({bv.transform_speed.toFixed(2)}x)</label>
            <input class="input" type="range" min="0.8" max="1.2" step="0.01" value={bv.transform_speed} oninput={(e) => patchBrand({ transform_speed: Number((e.target as HTMLInputElement).value) })} /></div>
          <div class="field"><label>{t("settings.render_layout.tx_zoom")} ({Math.round((bv.transform_zoom - 1) * 100)}%)</label>
            <input class="input" type="range" min="1" max="1.3" step="0.01" value={bv.transform_zoom} oninput={(e) => patchBrand({ transform_zoom: Number((e.target as HTMLInputElement).value) })} /></div>
          <div class="field"><label>{t("settings.render_layout.tx_brightness")} ({bv.transform_brightness.toFixed(2)})</label>
            <input class="input" type="range" min="-0.2" max="0.2" step="0.01" value={bv.transform_brightness} oninput={(e) => patchBrand({ transform_brightness: Number((e.target as HTMLInputElement).value) })} /></div>
          <div class="field"><label>{t("settings.render_layout.tx_contrast")} ({bv.transform_contrast.toFixed(2)})</label>
            <input class="input" type="range" min="0.7" max="1.3" step="0.01" value={bv.transform_contrast} oninput={(e) => patchBrand({ transform_contrast: Number((e.target as HTMLInputElement).value) })} /></div>
          <div class="field"><label>{t("settings.render_layout.tx_saturation")} ({bv.transform_saturation.toFixed(2)})</label>
            <input class="input" type="range" min="0.5" max="1.5" step="0.01" value={bv.transform_saturation} oninput={(e) => patchBrand({ transform_saturation: Number((e.target as HTMLInputElement).value) })} /></div>
        </div>
        <div class="toolbar"><Button variant="primary" disabled={isBusy()} onclick={saveBranding}>{t("settings.render_layout.save")}</Button></div>
      </div>
    </div>

    <div class="card">
      <div class="card-header"><div>
        <div class="card-title">{t("projects.videos_title", { count: videos.length })}</div>
        <div class="card-sub">{t("projects.progress_summary", { done: doneCount, failed: failedCount, total: videos.length })}</div>
      </div></div>
      <div class="card-body">
        {#if !videos.length}
          <div class="empty-card"><div class="empty-icon">＋</div><h3>{t("projects.empty_title")}</h3><p>{t("projects.empty_body")}</p></div>
        {:else}
          <table class="review-table">
            <thead><tr><th>{t("projects.col_video")}</th><th>{t("projects.col_status")}</th><th>{t("projects.col_output")}</th></tr></thead>
            <tbody>
              {#each videos as v (v.video_id)}
                {@const s = statuses[v.video_id]}
                <tr>
                  <td><div class="row-title">{v.video_id}</div><div class="small-muted">{(v.source_path || "").split(/[\\/]/).pop()}{v.is_long ? " · long" : ""}</div></td>
                  <td><StatusBadge kind={statusKind(s)}>{stageOf(s)}</StatusBadge></td>
                  <td>{#if stageOf(s).includes("rendered")}<a href={outputUrl(v)} target="_blank" rel="noopener">{t("projects.open_output")}</a>{:else}—{/if}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        {/if}
      </div>
    </div>
  {/if}
</div>
