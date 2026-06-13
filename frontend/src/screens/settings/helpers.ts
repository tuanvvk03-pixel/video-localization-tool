// Pure helpers ported from the legacy screens/settings.js (no DOM, no i18n
// state beyond an explicit `lang` arg) so they can be unit-tested.

export const ALIGN_OPTIONS: [string, string][] = [
  ["left", "L"],
  ["center", "C"],
  ["right", "R"],
];
export const VOICE_PREVIEW_TEXT_KEY = "vlt.voicePreviewText";
export const DEFAULT_VOICE_PREVIEW_TEXT = "Xin chào, đây là giọng đọc thử nghiệm.";
export const PREFERRED_VOICE_BY_LOCALE: Record<string, string> = {
  "vi-VN": "vi-VN-HoaiMyNeural",
  "en-US": "en-US-JennyNeural",
  "en-GB": "en-GB-SoniaNeural",
  "zh-CN": "zh-CN-XiaoxiaoNeural",
  "ja-JP": "ja-JP-NanamiNeural",
  "ko-KR": "ko-KR-SunHiNeural",
};
export const ROI_PRESETS: Record<string, Roi> = {
  bottom_band: { x: 0, y: 0.78, w: 1.0, h: 0.22 },
  bottom_wide: { x: 0, y: 0.70, w: 1.0, h: 0.30 },
  full_frame: { x: 0, y: 0, w: 1.0, h: 1.0 },
};

export interface Roi { x: number; y: number; w: number; h: number }
export interface FontItem { family: string; file: string }
export interface VoiceItem {
  provider: string; voice_id: string; label: string; locale: string;
  locale_label: string; locale_label_en: string; gender: string;
  gender_label: string; gender_label_en: string; short_name: string;
  style_tags: string[]; enabled: boolean;
}
export interface Bgm {
  original_path: string; normalized_path: string; original_filename: string;
  duration_ms: number; volume_db: number; loop: boolean;
  fade_in_ms: number; fade_out_ms: number;
}
export interface RenderLayout {
  aspect_ratio: string; background_path: string; background_original_filename: string;
}

export function normalizeFonts(fonts: unknown): FontItem[] {
  const seen = new Set<string>();
  const out: FontItem[] = [];
  for (const item of Array.isArray(fonts) ? fonts : []) {
    if (!item || typeof item.family !== "string" || !item.family.trim()) continue;
    const family = item.family.trim();
    const key = family.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ family, file: String(item.file || "") });
  }
  return out.sort((a, b) => a.family.localeCompare(b.family));
}

export function normalizeVoices(voices: unknown): VoiceItem[] {
  const out: VoiceItem[] = [];
  for (const item of Array.isArray(voices) ? voices : []) {
    if (!item || typeof item.voice_id !== "string" || !item.voice_id.trim()) continue;
    const styleTags = Array.isArray(item.style_tags)
      ? item.style_tags.map((tag: unknown) => String(tag || "").trim()).filter(Boolean)
      : [];
    out.push({
      provider: String(item.provider || "edge_tts"),
      voice_id: item.voice_id.trim(),
      label: String(item.label || item.voice_id).trim(),
      locale: String(item.locale || "").trim(),
      locale_label: String(item.locale_label || "").trim(),
      locale_label_en: String(item.locale_label_en || "").trim(),
      gender: String(item.gender || "").trim().toLowerCase(),
      gender_label: String(item.gender_label || "").trim(),
      gender_label_en: String(item.gender_label_en || "").trim(),
      short_name: String(item.short_name || "").trim(),
      style_tags: styleTags,
      enabled: item.enabled !== false,
    });
  }
  return out;
}

export function voicePoolForProvider(catalog: VoiceItem[], provider: string): VoiceItem[] {
  const enabled = catalog.filter((i) => i.provider === provider && i.enabled !== false);
  return enabled.length ? enabled : catalog.filter((i) => i.provider === provider);
}

export function normalizeTargetLanguage(value: unknown): string {
  const raw = String(value || "").trim();
  if (!raw) return "vi";
  const lower = raw.toLowerCase();
  if (lower.startsWith("english")) return "en";
  if (lower.startsWith("vietnam")) return "vi";
  if (lower.startsWith("chinese")) return "zh";
  if (lower.startsWith("japanese")) return "ja";
  if (lower.startsWith("korean")) return "ko";
  return lower.split(/[-_\s]/, 1)[0] || "vi";
}

export function preferredLocaleForTarget(targetLanguage: string): string {
  const code = normalizeTargetLanguage(targetLanguage);
  if (code === "en") return "en-US";
  if (code === "zh") return "zh-CN";
  if (code === "ja") return "ja-JP";
  if (code === "ko") return "ko-KR";
  if (code === "vi") return "vi-VN";
  return code.includes("-") ? code : "";
}

export function localeMatchesTarget(locale: string, targetLanguage: string): boolean {
  const code = normalizeTargetLanguage(targetLanguage);
  return !!locale && !!code && locale.toLowerCase().startsWith(`${code}-`);
}

export function compareVoiceEntries(a: VoiceItem, b: VoiceItem): number {
  const order: Record<string, number> = { female: 0, male: 1 };
  const ag = order[a.gender] ?? 9;
  const bg = order[b.gender] ?? 9;
  if (ag !== bg) return ag - bg;
  return (a.short_name || a.label || a.voice_id).localeCompare(b.short_name || b.label || b.voice_id);
}

export function resolveVoiceForProvider(
  catalog: VoiceItem[], provider: string, currentVoice: string, targetLanguage = "vi",
): string {
  const pool = voicePoolForProvider(catalog, provider);
  if (pool.some((i) => i.voice_id === currentVoice)) return currentVoice;
  const preferredLocale = preferredLocaleForTarget(targetLanguage);
  const preferredVoiceId = PREFERRED_VOICE_BY_LOCALE[preferredLocale];
  const preferredVoice = preferredVoiceId
    ? pool.find((i) => i.voice_id === preferredVoiceId && i.enabled !== false)
    : null;
  if (preferredVoice) return preferredVoice.voice_id;
  const preferred = pool
    .filter((i) => i.locale === preferredLocale || localeMatchesTarget(i.locale, targetLanguage))
    .sort(compareVoiceEntries)[0];
  if (preferred) return preferred.voice_id;
  const female = pool.filter((i) => i.gender === "female").sort(compareVoiceEntries)[0];
  return female?.voice_id || [...pool].sort(compareVoiceEntries)[0]?.voice_id
    || currentVoice || "vi-VN-HoaiMyNeural";
}

export function filterVoicePool(pool: VoiceItem[], locale: string, gender: string): VoiceItem[] {
  return pool.filter((i) => {
    if (locale && i.locale !== locale) return false;
    if (gender && i.gender !== gender) return false;
    return true;
  });
}

export function voiceLocaleLabel(item: VoiceItem, lang: string, unknown: string): string {
  if (lang === "vi") return item.locale_label || item.locale_label_en || item.locale || unknown;
  return item.locale_label_en || item.locale_label || item.locale || unknown;
}

export function voiceGenderLabel(item: VoiceItem, lang: string): string {
  if (lang === "vi") return item.gender_label || item.gender_label_en || item.gender || "";
  return item.gender_label_en || item.gender_label || item.gender || "";
}

export function voiceOptionLabel(item: VoiceItem, lang: string): string {
  const name = item.short_name || item.label || item.voice_id;
  const gender = voiceGenderLabel(item, lang);
  const style = item.style_tags.length ? item.style_tags[0] : "";
  const meta = [gender, style].filter(Boolean).join(", ");
  return meta ? `${name} - ${meta}` : name;
}

export function normalizeRoi(raw: unknown): Roi | null {
  if (!raw || typeof raw !== "object") return null;
  const r = raw as Record<string, unknown>;
  const out = {} as Roi;
  for (const key of ["x", "y", "w", "h"] as const) {
    const n = Number(r[key]);
    if (!Number.isFinite(n) || n < 0 || n > 1) return null;
    out[key] = n;
  }
  if (out.w <= 0 || out.h <= 0) return null;
  if (out.x + out.w > 1.0001 || out.y + out.h > 1.0001) return null;
  return out;
}

export function roiPresetName(raw: unknown): string {
  const roi = normalizeRoi(raw);
  if (!roi) return "bottom_band";
  for (const [name, preset] of Object.entries(ROI_PRESETS)) {
    if (Math.abs(roi.x - preset.x) < 1e-3 && Math.abs(roi.y - preset.y) < 1e-3
      && Math.abs(roi.w - preset.w) < 1e-3 && Math.abs(roi.h - preset.h) < 1e-3) return name;
  }
  return "custom";
}

export function clampSpeed(value: unknown): number {
  const n = Number(value);
  if (!Number.isFinite(n)) return 1;
  return Math.max(0.5, Math.min(2, Math.round(n * 20) / 20));
}
export function speedToRate(value: unknown): number {
  return Math.max(-50, Math.min(50, Math.round((clampSpeed(value) - 1) * 100)));
}
export function rateToSpeed(value: unknown): number {
  const n = Number(value);
  if (!Number.isFinite(n)) return 1;
  return clampSpeed(1 + n / 100);
}
export function clampDuckDb(value: unknown): number {
  const n = Number(value);
  if (!Number.isFinite(n)) return -15;
  return Math.max(-30, Math.min(0, Math.round(n * 100) / 100));
}
export function clampBgmDb(value: unknown): number {
  const n = Number(value);
  if (!Number.isFinite(n)) return -20;
  return Math.max(-40, Math.min(0, Math.round(n * 100) / 100));
}
export function clampFadeMs(value: unknown): number {
  const n = Number(value);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(10000, Math.round(n)));
}

export function normalizeBgm(raw: unknown): Bgm | null {
  if (!raw || typeof raw !== "object") return null;
  const r = raw as Record<string, unknown>;
  const normalizedPath = String(r.normalized_path || "").trim();
  const originalPath = String(r.original_path || "").trim();
  if (!normalizedPath && !originalPath) return null;
  return {
    original_path: originalPath,
    normalized_path: normalizedPath,
    original_filename: String(r.original_filename || "").trim(),
    duration_ms: Math.max(0, Math.round(Number(r.duration_ms) || 0)),
    volume_db: clampBgmDb(r.volume_db),
    loop: r.loop !== false,
    fade_in_ms: clampFadeMs(r.fade_in_ms ?? 500),
    fade_out_ms: clampFadeMs(r.fade_out_ms ?? 1000),
  };
}

export function normalizeRenderLayout(raw: unknown): RenderLayout {
  const data = (raw && typeof raw === "object" ? raw : {}) as Record<string, unknown>;
  const aspect = String(data.aspect_ratio || "16:9").trim();
  return {
    aspect_ratio: aspect === "9:16" ? "9:16" : "16:9",
    background_path: String(data.background_path || "").trim(),
    background_original_filename: String(data.background_original_filename || "").trim(),
  };
}

export function formatDb(value: unknown): string {
  const n = Number(value);
  const rounded = Number.isFinite(n) ? Math.round(n * 10) / 10 : 0;
  return `${rounded > 0 ? "+" : ""}${rounded} dB`;
}
export function formatMs(value: unknown): string { return `${clampFadeMs(value)} ms`; }
export function formatPct(n: unknown): string {
  const value = Number(n) || 0;
  return `${value > 0 ? "+" : ""}${value}%`;
}
export function formatSpeed(n: unknown): string {
  return `${clampSpeed(n).toFixed(2).replace(/0$/, "").replace(/\.$/, "")}x`;
}
export function formatBgmDuration(ms: unknown): string {
  const total = Math.max(0, Math.round((Number(ms) || 0) / 1000));
  const minutes = Math.floor(total / 60);
  const seconds = String(total % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export function alignToCss(value: string): "left" | "right" | "center" {
  if (value === "left") return "left";
  if (value === "right") return "right";
  return "center";
}
export function buildPreviewFontFamily(value: unknown): string {
  const trimmed = String(value || "").trim();
  return trimmed ? `"${trimmed}", "Segoe UI", sans-serif` : '"Segoe UI", sans-serif';
}
export function normalizeHex(value: unknown): string {
  const raw = String(value || "").trim();
  if (/^#(?:[0-9a-f]{6}|[0-9a-f]{8})$/i.test(raw)) return raw.toUpperCase();
  return "#000000";
}
export function basenameOnly(p: unknown): string {
  const s = String(p || "").replace(/[/\\]+$/, "");
  const parts = s.split(/[/\\]/);
  return parts[parts.length - 1] || s;
}
