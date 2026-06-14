<script lang="ts">
  import { onDestroy } from "svelte";
  import { post, pickLocalFiles, ApiError } from "../../lib/api";
  import type { ScreenCtx } from "../../lib/screen";
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
  }

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
