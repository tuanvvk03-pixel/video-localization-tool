<script lang="ts">
  // Import step (video selection) — Svelte port of the legacy
  // desktop/static/screens/import_step.js. Behaviour is preserved 1:1: local
  // file/multi-file picking (native bridge → server dialog → browser fallback),
  // per-file inspection, single-video vs multi-video (project) save flows, and
  // the per-video override editor. Only the render()-reachable code paths from
  // the legacy file were ported; its unused render* helpers were dropped.
  import {
    post,
    ApiError,
    pickLocalFile,
    pickLocalFiles,
  } from "../../lib/api";
  import type { ScreenCtx } from "../../lib/screen";
  import Button from "../../lib/ui/Button.svelte";
  import * as H from "./helpers";
  import type { SelectedFile, ImportState } from "./helpers";

  let { ctx }: { ctx: ScreenCtx } = $props();
  const t = (k: string, v?: Record<string, unknown>) => (ctx?.t ?? ((x: string) => x))(k, v);

  // Persist selection/preview across wizard navigation via the shared ctx object,
  // mirroring the legacy ctx.importState. Reuse the live object so an in-flight
  // save keeps its state if the edit shell re-mounts this screen.
  let s = $state<ImportState>((ctx?.importState as ImportState) || H.defaultState());
  if (ctx) ctx.importState = s;

  let errorMsg = $state("");
  let errorCode = $state("UI");

  // Guards stale async inspect results when the active file changes mid-probe.
  let selectionSeq = 0;
  let picker: HTMLInputElement | undefined = $state();
  let dropActive = $state(false);

  // ---- selection helpers ----------------------------------------------------
  function activeFile(): SelectedFile | null {
    if (!s.selectedFiles.length) return null;
    const idx = Math.min(Math.max(s.activeIndex | 0, 0), s.selectedFiles.length - 1);
    return s.selectedFiles[idx];
  }
  const hasSelection = () => s.selectedFiles.length > 0;
  const isMultiMode = () => s.selectedFiles.length >= 2;

  function defaultProjectName(): string {
    const first = s.selectedFiles[0];
    if (first) return H.stripVideoExt(first.name || "project");
    return "";
  }

  // ---- error banner ---------------------------------------------------------
  function clearError() {
    errorMsg = "";
  }
  function showError(err: unknown) {
    const e = asApiError(err);
    errorCode = e.shortCode || "UI";
    errorMsg = e.summary || e.message;
  }
  function asApiError(err: unknown): ApiError {
    if (err instanceof ApiError) return err;
    return new ApiError({
      code: "ui_error",
      short_code: "UI",
      message: err && (err as Error).message ? (err as Error).message : String(err || t("error.generic")),
    });
  }

  // ---- workspace root sync --------------------------------------------------
  function syncWorkspaceRoot(value: string) {
    const next = String(value || "").trim();
    ctx.workspaceRoot = next;
    try {
      localStorage.setItem("workspace_root", next);
    } catch {
      /* ignore */
    }
    const input = document.getElementById("workspaceRootInput") as HTMLInputElement | null;
    if (input) input.value = next;
  }

  // ---- file picking ---------------------------------------------------------
  async function chooseLocalVideos(fallbackInput: HTMLInputElement | undefined) {
    const filters = ["Video files (*.mp4;*.mov;*.mkv;*.webm;*.avi)", "All files (*.*)"];
    const multi = await pickLocalFiles({ filters, fallbackInput: fallbackInput ?? null });
    if (multi && multi.ok && Array.isArray(multi.paths) && multi.paths.length) {
      for (const p of multi.paths) {
        await addFileToSelection({ name: H.basenameFromPath(p), path: p, size: 0 });
      }
      return;
    }
    if (multi && multi.ok && (multi.cancelled || multi.browser_fallback)) return;
    if (multi && multi.unavailable) {
      // Native multi-picker unavailable — fall back to the single-file picker.
      const single = await pickLocalFile({ filters, fallbackInput: fallbackInput ?? null });
      if (single && single.ok && single.path) {
        await addFileToSelection({ name: H.basenameFromPath(single.path), path: single.path, size: 0 });
        return;
      }
      if (single && single.ok && (single.cancelled || single.browser_fallback)) return;
      if (single && single.error) showError(new Error(single.error));
      return;
    }
    if (multi && multi.error) showError(new Error(multi.error));
  }

  async function onPickerChange() {
    const files = picker?.files ? Array.from(picker.files) : [];
    if (!files.length) return;
    await addPickedFiles(files);
  }

  async function addPickedFiles(files: Array<File | { name: string; path: string; size: number }>) {
    for (const file of files) {
      await addFileToSelection(file);
    }
  }

  function findEntryByIdentity(entry: { path: string; name: string; size: number }): SelectedFile | null {
    for (const f of s.selectedFiles) {
      if (entry.path && f.path === entry.path) return f;
      if (!entry.path && f.name === entry.name && f.size === entry.size) return f;
    }
    return null;
  }

  async function addFileToSelection(file: File | { name: string; path: string; size: number }) {
    const seq = ++selectionSeq;
    const path = String((file as any)?.path || "").trim();
    const name = String((file as any)?.name || H.basenameFromPath(path) || "").trim();
    const size = Number((file as any)?.size) || 0;
    clearError();

    const entry: SelectedFile = {
      name,
      path,
      size,
      duration: null,
      override: {},
      _file: file instanceof File ? file : null,
    };
    // Dedupe on path (if known) or name+size.
    const existingIdx = s.selectedFiles.findIndex((f) => {
      if (entry.path && f.path) return f.path === entry.path;
      return f.name === entry.name && f.size === entry.size;
    });
    if (existingIdx >= 0) {
      s.activeIndex = existingIdx;
      return;
    }
    s.selectedFiles.push(entry);
    s.activeIndex = s.selectedFiles.length - 1;
    s.preview = normalizeLocalSelection({ name, path, size, duration: null });

    try {
      const inspected = await inspectLocalSelection(file);
      if (seq !== selectionSeq) return;
      const ref = findEntryByIdentity(entry);
      if (!ref) return;
      const nextName = String(inspected?.name || ref.name || H.basenameFromPath(ref.path) || "").trim();
      const nextPath = String(inspected?.path || ref.path).trim();
      const nextSize = Number(inspected?.size);
      ref.name = nextName;
      ref.path = nextPath;
      if (Number.isFinite(nextSize) && nextSize > 0) ref.size = nextSize;
      if (inspected?.duration != null) ref.duration = inspected.duration;
      if (activeFile() === ref) {
        s.preview = normalizeLocalSelection({
          name: ref.name,
          path: ref.path,
          size: ref.size,
          duration: ref.duration,
        });
      }
    } catch (err) {
      if (seq !== selectionSeq) return;
      showError(err);
    }
  }

  function removeFile(index: number) {
    if (index < 0 || index >= s.selectedFiles.length) return;
    s.selectedFiles.splice(index, 1);
    if (s.activeIndex >= s.selectedFiles.length) {
      s.activeIndex = Math.max(0, s.selectedFiles.length - 1);
    }
    const af = activeFile();
    s.preview = af
      ? normalizeLocalSelection({ name: af.name, path: af.path, size: af.size, duration: af.duration })
      : null;
  }

  async function inspectLocalSelection(file: File | { name: string; path: string; size: number }) {
    const path = String((file as any)?.path || "").trim();
    if (path) {
      const data = await post<any>("/api/inspect-local-video", { path });
      return {
        name: data.name || H.basenameFromPath(path),
        path: data.path || path,
        size: Number(data.size) || 0,
        duration: Number.isFinite(Number(data.duration_s)) ? Number(data.duration_s) : null,
      };
    }
    const duration = await probeBrowserFileDuration(file as File);
    return {
      name: String((file as any)?.name || "").trim(),
      path: "",
      size: Number((file as any)?.size) || 0,
      duration,
    };
  }

  function probeBrowserFileDuration(file: File): Promise<number | null> {
    return new Promise((resolve) => {
      if (!file || typeof URL === "undefined" || typeof document === "undefined") {
        resolve(null);
        return;
      }
      const objectUrl = URL.createObjectURL(file);
      const video = document.createElement("video");
      video.preload = "metadata";
      const done = (duration: number | null) => {
        video.removeAttribute("src");
        video.load();
        URL.revokeObjectURL(objectUrl);
        const d = Number(duration);
        resolve(Number.isFinite(d) && d > 0 ? d : null);
      };
      video.onloadedmetadata = () => done(Number(video.duration));
      video.onerror = () => done(null);
      video.src = objectUrl;
    });
  }

  // ---- preview normalization ------------------------------------------------
  function normalizeLocalSelection(file: { name: string; path: string; size: number; duration: number | null }) {
    return {
      kind: "local_selection",
      sourceType: t("import.source_local"),
      title: file.name || t("import.preview_untitled"),
      sourceName: file.name || "",
      fileSize: file.size || 0,
      duration: file.duration != null ? Number(file.duration) : null,
      workspace: "",
      workspaceRoot: "",
      inputPath: file.path || "",
      jobId: "",
    };
  }

  function normalizeLocalInit(data: any, status: any) {
    return {
      kind: "local_ready",
      sourceType: t("import.source_local"),
      title: data.source_name || data.job_id || t("import.preview_untitled"),
      sourceName: data.source_name || "",
      fileSize: 0,
      duration: data.source_duration_s,
      workspace: data.job_workspace,
      workspaceRoot: data.workspace_root || "",
      inputPath: data.input_video_path,
      jobId: data.job_id,
      voiceStatus: status && status.voice_edit_status ? status.voice_edit_status : "",
    };
  }

  interface MetaItem {
    label: string;
    value: string;
    hint: string;
  }
  function metadataItems(preview: any): MetaItem[] {
    const items: MetaItem[] = [];
    if (preview.duration != null) {
      items.push({ label: t("import.field_duration"), value: H.formatDuration(preview.duration), hint: t("import.hint_duration") });
    }
    if (preview.fileSize) {
      items.push({ label: t("import.field_file_size"), value: H.formatBytes(preview.fileSize), hint: t("import.hint_file_size") });
    }
    if (preview.jobId) {
      items.push({ label: t("import.field_job_id"), value: preview.jobId, hint: t("import.hint_job_id") });
    }
    if (preview.workspace) {
      items.push({ label: t("import.field_workspace"), value: preview.workspace, hint: t("import.hint_workspace") });
    }
    if (preview.inputPath) {
      items.push({ label: t("import.field_input_path"), value: preview.inputPath, hint: t("import.hint_input_path") });
    }
    if (preview.voiceStatus) {
      items.push({ label: t("import.field_status"), value: t(`stage.${preview.voiceStatus}`), hint: t("import.hint_status") });
    }
    if (items.length === 0) {
      items.push({ label: t("import.field_status"), value: t("import.status_waiting"), hint: t("import.hint_status") });
    }
    return items;
  }

  // ---- per-video override ---------------------------------------------------
  function setPerVideoOverride(patch: Record<string, string>) {
    const f = activeFile();
    if (!f) return;
    const next = { ...(f.override || {}) };
    for (const [k, v] of Object.entries(patch || {})) {
      if (v == null || String(v).trim() === "" || v === "__inherit__") {
        delete next[k];
      } else {
        next[k] = v;
      }
    }
    f.override = next;
  }

  // ---- save flows -----------------------------------------------------------
  async function postImportExternalIfNeeded(jobWorkspace: string, cfg: any) {
    if ((cfg.subtitle_extractor || "") !== "external_srt") return;
    const p = String(cfg.external_srt_path || "").trim();
    if (!p) {
      showError(new Error(t("import.external_srt_required")));
      throw new Error("missing_external_srt");
    }
    await post("/api/import-external-srt", { job_workspace: jobWorkspace, srt_path: p });
  }

  async function initSingleLocalJob({ navigateOnSuccess }: { navigateOnSuccess: boolean }): Promise<any> {
    const file = activeFile();
    const customWorkspaceRoot = String(ctx.workspaceRoot || "").trim();
    if (customWorkspaceRoot && !H.looksLikeDirectoryPath(customWorkspaceRoot)) {
      showError(new Error(t("error.workspace_root_invalid")));
      return null;
    }
    if (!file || !String(file.path || "").trim()) {
      showError(new Error(t("import.path_required")));
      return null;
    }
    const candidate = String(file.path).trim();
    if (!H.looksLikeVideoFilePath(candidate)) {
      showError(new Error(t("import.path_invalid_file")));
      return null;
    }
    clearError();
    try {
      const name = H.basenameFromPath(candidate);
      const autoJobId = H.slugForId(H.stripVideoExt(name || "video"));
      const req: any = { video: candidate, job_id: autoJobId, force: false };
      if (customWorkspaceRoot) req.workspace_root = customWorkspaceRoot;
      let data: any;
      try {
        data = await post<any>("/api/init-job", req);
      } catch (e) {
        // The job id is a hash of this exact file, so an existing workspace is
        // the SAME video's job — reuse it (resume) instead of erroring.
        if (e instanceof ApiError && e.code === "workspace_exists") {
          data = await post<any>("/api/init-job", { ...req, force: true });
        } else {
          throw e;
        }
      }
      syncWorkspaceRoot(data.workspace_root || customWorkspaceRoot);
      let status: any = null;
      try {
        status = await post<any>("/api/status", { job_workspace: data.job_workspace });
      } catch {
        status = null;
      }
      s.preview = normalizeLocalInit(data, status);
      ctx.jobWorkspace = data.job_workspace;
      ctx.parentProject = undefined;
      ctx.parentProjectRoot = undefined;
      if (navigateOnSuccess) ctx.navigate("settings");
      return data;
    } catch (err) {
      showError(err);
      return null;
    }
  }

  async function createProjectWithVideos(): Promise<any> {
    const files = s.selectedFiles;
    if (files.length < 2) return null;
    for (const f of files) {
      if (!String(f.path || "").trim()) {
        showError(new Error(t("import.multi_path_required")));
        return null;
      }
      if (!H.looksLikeVideoFilePath(f.path)) {
        showError(new Error(t("import.multi_invalid_path", { path: f.path })));
        return null;
      }
    }
    clearError();
    const projectName = (s.projectName || defaultProjectName() || "project").trim();
    try {
      const projData = await post<any>("/api/init-project", {
        project_name: projectName,
        config_overrides: { translate_backend: s.translateBackend, tts_provider: s.ttsProvider },
      });
      const projectRoot = projData.project_root;
      const added: any[] = [];
      for (let fi = 0; fi < files.length; fi += 1) {
        const f = files[fi];
        const override = H.pickOverrideForProject(f.override);
        const body: any = {
          project_root: projectRoot,
          video: f.path,
          video_id: H.videoWorkspaceIdForFile(f, fi),
          force: false,
        };
        if (Object.keys(override).length) body.override = override;
        const entry = await post<any>("/api/add-video-to-project", body);
        added.push(entry);
      }
      const globalCfg = H.currentImportConfig(s);
      for (let i = 0; i < added.length; i += 1) {
        const entry = added[i];
        const jw = String(entry.workspace || "").trim();
        if (!jw) continue;
        const vid = String(entry.video_id || "");
        let file = files[i];
        for (let fi = 0; fi < files.length; fi += 1) {
          if (H.videoWorkspaceIdForFile(files[fi], fi) === vid) {
            file = files[fi];
            break;
          }
        }
        const cfg = H.mergeImportCfgForVideoFile(globalCfg, file);
        await post("/api/save-import-config", { job_workspace: jw, config: cfg });
        try {
          await postImportExternalIfNeeded(jw, cfg);
        } catch (e) {
          showError(e instanceof Error ? e : new Error(String(e)));
          return null;
        }
      }
      ctx.projectRoot = projectRoot;
      ctx.projectId = projData.project_id;
      ctx.projectName = projData.project_name;
      ctx.projectVideos = added;
      ctx.jobWorkspace = "";
      ctx.parentProject = projData.project_id;
      ctx.parentProjectRoot = projectRoot;
      return projData;
    } catch (err) {
      showError(err);
      return null;
    }
  }

  async function saveImportConfigAndContinue() {
    if (s.importProjectBusy) return;
    const cfg = H.currentImportConfig(s);
    clearError();
    s.importProjectBusy = true;
    try {
      if (isMultiMode()) {
        const projData = await createProjectWithVideos();
        if (!projData) return;
        ctx.importConfig = { project_root: projData.project_root, ...cfg } as any;
        ctx.settingsState = null;
        ctx.navigate("settings");
        return;
      }

      let jobWorkspace = String(ctx.jobWorkspace || "").trim();
      if (s.preview && s.preview.kind === "local_ready" && s.preview.workspace) {
        jobWorkspace = String(s.preview.workspace).trim();
      } else {
        const initData = await initSingleLocalJob({ navigateOnSuccess: false });
        if (!initData || !initData.job_workspace) return;
        jobWorkspace = String(initData.job_workspace).trim();
      }
      if (!jobWorkspace) return;

      try {
        await post("/api/save-video-tts", {
          job_workspace: jobWorkspace,
          settings: { tts_provider: cfg.tts_provider },
        });
        const saved = await post<any>("/api/save-import-config", {
          job_workspace: jobWorkspace,
          config: cfg,
        });

        try {
          await postImportExternalIfNeeded(jobWorkspace, saved.config || cfg);
        } catch (err) {
          showError(err);
          return;
        }

        ctx.importConfig = { job_workspace: jobWorkspace, ...(saved.config || cfg) };
        ctx.settingsState = null;
        ctx.navigate("settings");
      } catch (err) {
        showError(err);
      }
    } finally {
      s.importProjectBusy = false;
    }
  }

  async function revealWorkspaceRoot() {
    if (!ctx.workspaceRoot) {
      showError(new Error(t("error.workspace_missing")));
      return;
    }
    clearError();
    try {
      await post("/api/reveal", { path: ctx.workspaceRoot });
    } catch (err) {
      showError(err);
    }
  }

  // ---- drag & drop ----------------------------------------------------------
  function onDrop(e: DragEvent) {
    e.preventDefault();
    dropActive = false;
    const files = e.dataTransfer && e.dataTransfer.files ? Array.from(e.dataTransfer.files) : [];
    if (files.length) void addPickedFiles(files);
  }

  // The TTS-provider tooltip select preserves the legacy "option list" preview.
  const TTS_OPTIONS: Array<[string, string, string]> = $derived([
    ["edge_tts", "edge_tts", t("import.tts_provider_edge_hint")],
    ["azure_tts", "azure_tts", t("import.tts_provider_azure_hint")],
  ]);

  const overrideHasConfig = (f: SelectedFile) =>
    !!(f.override?.tts_voice || f.override?.tts_provider || f.override?.translate_backend);
</script>

{#snippet infoDot(text: string)}
  <span class="info-dot has-tooltip" role="img" tabindex="0" aria-label={text} data-tooltip={text}>i</span>
{/snippet}

{#if errorMsg}
  <div class="error-banner" data-testid="import-error">
    <div class="error-code">{errorCode}</div>
    <div class="error-message">{errorMsg}</div>
  </div>
{/if}

<div class="screen video-step" data-testid="import-screen">
  <!-- Primary card: choose a video -->
  <div class="card">
    <h2 class="scr-title">{t("import.input_title")}</h2>
    <p class="scr-sub">{t("import.input_sub")}</p>

    <div class="stack">
      <div
        class="dropzone {dropActive ? 'active' : ''}"
        role="button"
        tabindex="-1"
        ondragover={(e) => { e.preventDefault(); dropActive = true; }}
        ondragleave={() => (dropActive = false)}
        ondrop={onDrop}
      >
        <input
          type="file"
          accept="video/*,.mp4,.mov,.mkv"
          multiple
          hidden
          bind:this={picker}
          onchange={onPickerChange}
        />
        <div class="dropzone-icon">🎬</div>
        <div class="big">{t("import.drop_big")}</div>
        <div class="small">{t("import.drop_small")}</div>
        <Button variant="primary" onclick={() => chooseLocalVideos(picker)}>
          {t("import.choose_file")}
        </Button>
      </div>

      {#if s.selectedFiles.length > 0}
        <div class="stack">
          <div class="card-sub">
            {isMultiMode()
              ? `${s.selectedFiles.length} video (chế độ multi)`
              : "1 video (chế độ single)"}
          </div>
          <div class="stack">
            {#each s.selectedFiles as file, i}
              <div
                class="import-file-info {s.activeIndex === i ? 'active' : ''}"
                role="button"
                tabindex="0"
                style="cursor:pointer;padding:8px 10px;border:{s.activeIndex === i
                  ? '2px solid var(--accent, #5b8def)'
                  : '1px solid var(--border, #2b2f3a)'};border-radius:6px;display:flex;align-items:center;gap:10px;"
                onclick={(e) => {
                  if ((e.target as HTMLElement)?.tagName === "BUTTON") return;
                  s.activeIndex = i;
                }}
              >
                <strong>{file.name || `video ${i + 1}`}</strong>
                {#if file.size > 0}<span class="small-muted">({H.formatBytes(file.size)})</span>{/if}
                {#if file.duration != null}<span class="small-muted">{H.formatDuration(file.duration)}</span>{/if}
                <span style="flex:1"></span>
                {#if overrideHasConfig(file)}
                  <span class="small-muted" style="color:var(--accent, #5b8def)" title="Video này có cấu hình riêng">● riêng</span>
                {/if}
                <Button variant="secondary" onclick={(e: MouseEvent) => { e.stopPropagation(); removeFile(i); }}>Xoá</Button>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      {#if isMultiMode()}
        <div class="field stack">
          <label for="import-project-name">Tên dự án (project)</label>
          <input
            id="import-project-name"
            type="text"
            class="input"
            placeholder={defaultProjectName() || "project"}
            bind:value={s.projectName}
          />
          <div class="small-muted">Nhiều video sẽ được gộp thành một project có thư mục riêng.</div>
        </div>
      {/if}
    </div>

    <!-- Hint → standalone downloader -->
    <div class="video-hint">
      <span>{t("import.download_redirect")}</span>
      <button type="button" class="linklike" onclick={() => ctx.navigate("download")}>{t("rail.download")} →</button>
    </div>
  </div>

  <!-- Advanced options: collapsed by default, auto-open once analyzed -->
  <details class="advanced-block" open={!!s.preview}>
    <summary>{t("import.advanced_summary")}</summary>
    <div class="advanced-body stack">
      {#if s.preview}
        <div class="meta-preview">
          <div class="thumb"></div>
          <div>
            <div style="font-size:18px;font-weight:800">{s.preview?.title || s.preview?.sourceName || t("import.preview_untitled")}</div>
            <div class="small-muted" style="margin-top:6px">{t("import.source_type")} - {s.preview?.sourceType}</div>
            <div class="kv">
              {#each metadataItems(s.preview) as item}
                <div class="item">
                  <div class="k import-info-label">
                    <span>{item.label}</span>
                    {@render infoDot(item.hint || item.label)}
                  </div>
                  <div class="v">{item.value}</div>
                </div>
              {/each}
            </div>
          </div>
        </div>
      {/if}

      <!-- Config: translation is always managed now; only the default TTS provider remains here. -->
      <div class="section-block stack">
        <div class="stack">
          <div class="card-sub">{t("import.config_title")}</div>
          <div class="small-muted">{t("import.config_sub")}</div>
        </div>

        <div class="field">
          <div class="field-label-row">
            <label for="import-tts-provider">{t("import.tts_provider_label")}</label>
          </div>
          <select id="import-tts-provider" class="input" bind:value={s.ttsProvider}>
            {#each TTS_OPTIONS as [value, label]}
              <option {value}>{label}</option>
            {/each}
          </select>
          <div class="import-option-list">
            {#each TTS_OPTIONS as [value, label, hint]}
              <div class="import-option-item {s.ttsProvider === value ? 'active' : ''}" data-value={value}>
                <span class="import-option-name">{label}</span>
                {@render infoDot(hint)}
              </div>
            {/each}
          </div>
        </div>
      </div>

      {#if isMultiMode()}
        {@const active = activeFile()}
        <div class="section-block stack">
          <div class="card-sub">Cấu hình riêng cho video đang chọn</div>
          <div class="small-muted">
            {active
              ? `Đang chỉnh: ${active.name || `video ${s.activeIndex + 1}`}. Để trống nếu muốn dùng chung cấu hình project.`
              : "Chọn một video ở danh sách trên để gán cấu hình riêng."}
          </div>

          {#if active}
            <div class="field">
              <label for="ov-tts-provider">TTS provider (riêng)</label>
              <select
                id="ov-tts-provider"
                class="input"
                value={active.override.tts_provider || "__inherit__"}
                onchange={(e) => setPerVideoOverride({ tts_provider: (e.currentTarget as HTMLSelectElement).value })}
              >
                <option value="__inherit__">— Dùng chung —</option>
                <option value="edge_tts">edge_tts</option>
                <option value="azure_tts">azure_tts</option>
              </select>
            </div>

            <div class="field">
              <label for="ov-tts-voice">TTS voice (riêng)</label>
              <input
                id="ov-tts-voice"
                type="text"
                class="input"
                placeholder="Để trống để dùng chung"
                value={active.override.tts_voice || ""}
                onchange={(e) => setPerVideoOverride({ tts_voice: (e.currentTarget as HTMLInputElement).value })}
                onblur={(e) => setPerVideoOverride({ tts_voice: (e.currentTarget as HTMLInputElement).value })}
              />
            </div>

            <div class="field">
              <label for="ov-backend">Translate backend (riêng)</label>
              <select
                id="ov-backend"
                class="input"
                value={active.override.translate_backend || "__inherit__"}
                onchange={(e) => setPerVideoOverride({ translate_backend: (e.currentTarget as HTMLSelectElement).value })}
              >
                <option value="__inherit__">— Dùng chung —</option>
                <option value="block_v2">block_v2</option>
                <option value="legacy">legacy</option>
              </select>
            </div>

            <div class="field">
              <label for="ov-extractor">{t("import.per_video_subtitle_mode")}</label>
              <select
                id="ov-extractor"
                class="input"
                value={active.override.subtitle_extractor || "__inherit__"}
                onchange={(e) => setPerVideoOverride({ subtitle_extractor: (e.currentTarget as HTMLSelectElement).value })}
              >
                <option value="__inherit__">{t("import.per_video_inherit")}</option>
                <option value="audio_only">{t("settings.extractor.mode.audio_only")}</option>
                <option value="external_srt">{t("settings.extractor.mode.external_srt")}</option>
              </select>
            </div>

            <div class="field">
              <label for="ov-srt">{t("import.per_video_external_srt")}</label>
              <input
                id="ov-srt"
                type="text"
                class="input"
                placeholder={t("import.per_video_external_srt_placeholder")}
                value={active.override.external_srt_path || ""}
                onchange={(e) => setPerVideoOverride({ external_srt_path: (e.currentTarget as HTMLInputElement).value })}
                onblur={(e) => setPerVideoOverride({ external_srt_path: (e.currentTarget as HTMLInputElement).value })}
              />
            </div>
          {/if}
        </div>
      {/if}
    </div>
  </details>

  <!-- Primary actions -->
  <div class="toolbar" style="margin-top:8px">
    <Button disabled={!ctx.workspaceRoot} onclick={revealWorkspaceRoot}>
      {t("import.open_jobs_folder")}
    </Button>
    {#if hasSelection() || (s.preview && s.preview.kind === "local_ready")}
      <Button variant="primary" disabled={!!s.importProjectBusy} onclick={saveImportConfigAndContinue}>
        {s.importProjectBusy
          ? t("import.project_creating")
          : isMultiMode()
            ? t("import.multi_save_continue")
            : t("import.save_config")}
      </Button>
    {/if}
  </div>
</div>
