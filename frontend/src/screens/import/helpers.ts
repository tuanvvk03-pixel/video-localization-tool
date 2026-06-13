// Pure helpers for the Import screen, ported 1:1 from the legacy
// desktop/static/screens/import_step.js so behaviour is identical: job-id
// slugging, per-file workspace ids, path predicates, byte/duration formatting
// and the import-config merge rules.

const JOB_SLUG_RE = /[^A-Za-z0-9._-]+/g;

export const PER_VIDEO_OVERRIDE_KEYS = [
  "tts_provider",
  "tts_voice",
  "translate_backend",
  "subtitle_extractor",
  "external_srt_path",
] as const;

export interface SelectedFile {
  name: string;
  path: string;
  size: number;
  duration: number | null;
  override: Record<string, string>;
  /** Original DOM File when picked through the browser fallback (not reactive). */
  _file: File | null;
}

export interface ImportConfig {
  translate_backend: string;
  tts_provider: string;
  use_auto_translate: boolean;
  subtitle_extractor: string;
  external_srt_path: string;
}

export interface ImportState {
  selectedFiles: SelectedFile[];
  activeIndex: number;
  projectName: string;
  preview: Record<string, any> | null;
  importProjectBusy: boolean;
  useAutoTranslate: boolean;
  translateBackend: string;
  ttsProvider: string;
  subtitleExtractor: string;
  externalSrtPath: string;
}

export function defaultState(): ImportState {
  return {
    selectedFiles: [],
    activeIndex: 0,
    projectName: "",
    preview: null,
    importProjectBusy: false,
    useAutoTranslate: true,
    translateBackend: "block_v2",
    ttsProvider: "edge_tts",
    subtitleExtractor: "audio_only",
    externalSrtPath: "",
  };
}

export function basenameFromPath(value: string): string {
  const parts = String(value || "").split(/[\\/]/).filter(Boolean);
  return parts[parts.length - 1] || "";
}

export function stripVideoExt(value: string): string {
  return String(value || "").replace(/\.(mp4|mov|mkv|webm|avi)$/i, "");
}

/** Stable unsigned 32-bit hash for ASCII-ish strings (paths). */
function pathHash32(str: string): number {
  let h = 5381;
  const s = String(str || "");
  for (let i = 0; i < s.length; i += 1) {
    h = ((h << 5) + h) ^ s.charCodeAt(i);
  }
  return h >>> 0;
}

function shortHash(value: string): string {
  let h = 0;
  const str = String(value || "");
  for (let i = 0; i < str.length; i += 1) h = (h * 31 + str.charCodeAt(i)) >>> 0;
  return h.toString(36).slice(0, 5) || "0";
}

export function slugForId(value: string): string {
  const raw = String(value || "");
  const slug = raw
    .replace(JOB_SLUG_RE, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/^[._-]+|[._-]+$/g, "");
  // Non-ASCII (e.g. Chinese) titles strip to the same leftover ASCII token, so
  // append a short hash of the full name to keep each file's id unique + stable.
  const hadNonAscii = /[^\x00-\x7F]/.test(raw);
  if (!slug) return `video-${shortHash(raw)}`;
  if (hadNonAscii) return `${slug}-${shortHash(raw)}`;
  return slug;
}

/** Unique per absolute file path so multi-import never collides on identical basenames. */
export function videoWorkspaceIdForFile(f: SelectedFile, index: number): string {
  const path = String(f.path || "").trim();
  const stem = stripVideoExt(f.name || basenameFromPath(path) || "video");
  if (!path) {
    return slugForId(`${stem}-n${index}`);
  }
  const norm = path.replace(/\\/g, "/");
  const h = pathHash32(norm).toString(36);
  const disambig = `i${index}`;
  let slug = slugForId(`${stem}-${h}-${disambig}`);
  if (slug.length > 96) {
    slug = slugForId(`${stem.slice(0, 32)}-${h}-${disambig}`);
  }
  return slug || slugForId(`v-${h}-${disambig}`);
}

export function looksLikeVideoFilePath(p: string): boolean {
  const s = String(p || "").trim();
  if (!s) return false;
  if (/[\\/]\s*$/.test(s)) return false;
  return /\.(mp4|mov|mkv|webm|avi)$/i.test(s);
}

export function looksLikeDirectoryPath(p: string): boolean {
  const s = String(p || "").trim();
  if (!s) return false;
  if (/[\\/]\s*$/.test(s)) return true;
  if (/\.(mp4|mov|mkv|webm|avi)$/i.test(s)) return false;
  if (/\.[a-z0-9]{1,6}$/i.test(s)) return false;
  return true;
}

function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

export function formatDuration(seconds: number | null | undefined): string {
  const total = Math.max(0, Math.round(Number(seconds) || 0));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  if (h > 0) return `${pad2(h)}:${pad2(m)}:${pad2(s)}`;
  return `${pad2(m)}:${pad2(s)}`;
}

export function formatBytes(bytes: number | null | undefined): string {
  const value = Number(bytes) || 0;
  if (value <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let size = value;
  let idx = 0;
  while (size >= 1024 && idx < units.length - 1) {
    size /= 1024;
    idx += 1;
  }
  const digits = size >= 100 || idx === 0 ? 0 : 1;
  return `${size.toFixed(digits)} ${units[idx]}`;
}

export function pickOverrideForProject(override: Record<string, string> | undefined): Record<string, string> {
  const clean: Record<string, string> = {};
  if (!override) return clean;
  for (const k of PER_VIDEO_OVERRIDE_KEYS) {
    const v = override[k];
    if (v != null && String(v).trim() !== "") clean[k] = v;
  }
  return clean;
}

export function currentImportConfig(s: ImportState): ImportConfig {
  const ex = s.subtitleExtractor || "audio_only";
  return {
    translate_backend: s.translateBackend,
    tts_provider: s.ttsProvider,
    use_auto_translate: !!s.useAutoTranslate,
    subtitle_extractor: ex,
    external_srt_path: ex === "external_srt" ? String(s.externalSrtPath || "").trim() : "",
  };
}

export function mergeImportCfgForVideoFile(globalCfg: ImportConfig, file: SelectedFile): ImportConfig {
  const o = file?.override || {};
  let rawEx: string | undefined = o.subtitle_extractor;
  if (rawEx == null || rawEx === "" || rawEx === "__inherit__") {
    rawEx = globalCfg.subtitle_extractor;
  }
  let ex = String(rawEx || "audio_only").toLowerCase();
  if (ex === "ocr_only" || ex === "hybrid") ex = "audio_only";
  if (ex !== "external_srt" && ex !== "audio_only") ex = "audio_only";
  let path = "";
  if (o.external_srt_path != null && String(o.external_srt_path).trim()) {
    path = String(o.external_srt_path).trim();
  } else if (ex === "external_srt") {
    path = String(globalCfg.external_srt_path || "").trim();
  }
  return {
    ...globalCfg,
    subtitle_extractor: ex,
    external_srt_path: ex === "external_srt" ? path : "",
  };
}
