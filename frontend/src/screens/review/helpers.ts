// Pure helpers ported from the legacy screens/review.js (no DOM / i18n state).

export const BURN_PALETTE_TONES: string[][] = [
  ["#7A1E1E", "#A32626", "#C73535", "#E15757", "#F6B5B5"],
  ["#8A3C10", "#B74B12", "#D96A1D", "#F08D44", "#F8C9A6"],
  ["#8A6B00", "#B58C00", "#D9A700", "#F2C94C", "#FAE7A3"],
  ["#1F6B2D", "#2C8A3D", "#39A84E", "#63C97C", "#B8E6C4"],
  ["#176B6B", "#1C8A8A", "#27A9A9", "#4FCACA", "#AEE8E8"],
  ["#1D4ED8", "#2563EB", "#3B82F6", "#60A5FA", "#BFDBFE"],
  ["#5B3AAE", "#7149D0", "#8A63F0", "#A78BFA", "#D9CCFF"],
  ["#9D2365", "#C0267A", "#E04496", "#F472B6", "#FBC6E3"],
];

export const PROVENANCE_ICON: Record<string, string> = {
  asr: "🎤", ocr: "👁", fused_match: "🔀",
  fused_drift: "🔀", fused_disagreement: "⚠",
};

export interface Cue {
  index: number; start_ms: number; end_ms: number; text: string;
  source_text: string; reference_text: string;
  provenance_source: string; provenance_needs_review: boolean;
  provenance_asr_text: string; provenance_ocr_text: string; provenance_confidence: number | null;
}

export interface TtsSettings {
  tts_provider: string; tts_voice: string; speed_multiplier: number;
  tts_rate: number; tts_pitch: number; mix_mode: string; mix_duck_gain_db: number;
}

export function defaultTtsSettings(): TtsSettings {
  return { tts_provider: "edge_tts", tts_voice: "vi-VN-HoaiMyNeural", speed_multiplier: 1,
    tts_rate: 0, tts_pitch: 0, mix_mode: "replace_original_speech", mix_duck_gain_db: -15 };
}

function cueIndexKey(c: { index?: unknown; start_ms?: unknown; end_ms?: unknown }): string {
  return `${Number(c.index) || 0}|${Number(c.start_ms) || 0}|${Number(c.end_ms) || 0}`;
}
function cueTimeKey(c: { start_ms?: unknown; end_ms?: unknown }): string {
  return `${Number(c.start_ms) || 0}|${Number(c.end_ms) || 0}`;
}
export function cueKey(c: Cue): string { return cueIndexKey(c); }

interface CueMaps { byExact: Map<string, any>; byTime: Map<string, any>; list: any[] }
function buildCueMaps(cues: any[]): CueMaps {
  const byExact = new Map(); const byTime = new Map();
  const list = Array.isArray(cues) ? cues : [];
  for (const cue of list) { byExact.set(cueIndexKey(cue), cue); byTime.set(cueTimeKey(cue), cue); }
  return { byExact, byTime, list };
}
function lookupCueText(maps: CueMaps, cue: any, idx: number): string {
  const exact = maps.byExact.get(cueIndexKey(cue));
  if (exact) return String(exact.text || "");
  const byTime = maps.byTime.get(cueTimeKey(cue));
  if (byTime) return String(byTime.text || "");
  const fallback = maps.list[idx];
  return fallback ? String(fallback.text || "") : "";
}

interface ProvMaps { byTime: Map<string, any>; byIndex: Map<number, any> }
function buildProvenanceMap(provenance: any): ProvMaps | null {
  if (!provenance || !Array.isArray(provenance.cues)) return null;
  const byTime = new Map(); const byIndex = new Map();
  for (const e of provenance.cues) {
    byTime.set(`${Number(e.start_ms) || 0}|${Number(e.end_ms) || 0}`, e);
    if (e.index != null) byIndex.set(Number(e.index), e);
  }
  return { byTime, byIndex };
}
function lookupProvenance(maps: ProvMaps | null, cue: any, idx: number): any {
  if (!maps) return null;
  return maps.byTime.get(`${Number(cue.start_ms) || 0}|${Number(cue.end_ms) || 0}`) || maps.byIndex.get(idx + 1) || null;
}

export function buildCueModels(cues: any[], sourceCues: any[], referenceCues: any[], provenance: any): Cue[] {
  const sourceMaps = buildCueMaps(sourceCues);
  const referenceMaps = buildCueMaps(referenceCues);
  const provMap = buildProvenanceMap(provenance);
  return (cues || []).map((cue, idx) => {
    const prov = lookupProvenance(provMap, cue, idx);
    return {
      index: Number(cue.index) || idx + 1,
      start_ms: Number(cue.start_ms) || 0, end_ms: Number(cue.end_ms) || 0,
      text: String(cue.text || ""),
      source_text: lookupCueText(sourceMaps, cue, idx),
      reference_text: lookupCueText(referenceMaps, cue, idx) || String(cue.text || ""),
      provenance_source: prov?.source || "",
      provenance_needs_review: !!prov?.needs_review,
      provenance_asr_text: prov?.asr_text || "", provenance_ocr_text: prov?.ocr_text || "",
      provenance_confidence: Number.isFinite(Number(prov?.ocr_confidence)) ? Number(prov.ocr_confidence) : null,
    };
  });
}

export function normalizeText(v: unknown): string { return String(v || "").trim().toLowerCase(); }
export function isCueChanged(cue: Cue): boolean { return normalizeText(cue.text) !== normalizeText(cue.reference_text); }
export function lineCount(text: unknown): number { return String(text || "").split(/\r?\n/).length; }

export function formatMs(ms: unknown): string {
  const total = Math.max(0, Number(ms) || 0);
  const hh = Math.floor(total / 3600000), mm = Math.floor((total % 3600000) / 60000),
    ss = Math.floor((total % 60000) / 1000), frac = Math.floor(total % 1000);
  return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}.${String(frac).padStart(3, "0")}`;
}
export function formatClock(seconds: unknown): string {
  const total = Math.max(0, Math.floor(Number(seconds) || 0));
  const hh = Math.floor(total / 3600), mm = Math.floor((total % 3600) / 60), ss = total % 60;
  return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`;
}

export function normalizeHexReview(value: unknown): string {
  const raw = String(value || "").trim();
  if (/^#(?:[0-9a-f]{6}|[0-9a-f]{8})$/i.test(raw)) return raw.toUpperCase();
  return "#000000";
}

export function clampDuckSpeed(v: unknown): number {
  const n = Number(v); if (!Number.isFinite(n)) return 1;
  return Math.max(0.5, Math.min(2, Math.round(n * 100) / 100));
}
export function clampDuckDb(v: unknown): number {
  const n = Number(v); if (!Number.isFinite(n)) return -15;
  return Math.max(-30, Math.min(0, Math.round(n * 100) / 100));
}
export function duckDbToPercent(db: unknown): number { return Math.round(((clampDuckDb(db) + 30) / 30) * 100); }
export function duckPercentToDb(percent: unknown): number {
  const p = Math.max(0, Math.min(100, Number(percent) || 0));
  return clampDuckDb(-30 + (p * 30) / 100);
}

export function mergeTtsSettings(raw: any): TtsSettings {
  const out = defaultTtsSettings();
  if (raw && typeof raw === "object") {
    if (typeof raw.tts_provider === "string" && raw.tts_provider) out.tts_provider = raw.tts_provider;
    if (typeof raw.tts_voice === "string" && raw.tts_voice) out.tts_voice = raw.tts_voice;
    if (Number.isFinite(Number(raw.speed_multiplier))) out.speed_multiplier = clampDuckSpeed(Number(raw.speed_multiplier));
    if (Number.isFinite(Number(raw.tts_rate))) out.tts_rate = Number(raw.tts_rate);
    if (Number.isFinite(Number(raw.tts_pitch))) out.tts_pitch = Number(raw.tts_pitch);
    if (raw.mix_mode === "duck_original_speech" || raw.mix_mode === "replace_original_speech") out.mix_mode = raw.mix_mode;
    if (Number.isFinite(Number(raw.mix_duck_gain_db))) out.mix_duck_gain_db = clampDuckDb(Number(raw.mix_duck_gain_db));
  }
  return out;
}

/** Only burn layout fields — server merges into style_override.json. */
export function serializeReviewBurnPatchForApi(raw: any): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  payload.margin_v = Math.max(0, Math.min(500, Math.round(Number(raw?.margin_v) || 0)));
  const fs = Math.round(Number(raw?.font_size) || 0);
  payload.font_size = fs >= 10 && fs <= 120 ? fs : null;
  const bg = String(raw?.subtitle_background_color || "").trim();
  payload.subtitle_background_color = bg ? normalizeHexReview(bg) : null;
  return payload;
}

/** Inline CSS string approximating ASS MarginV + Fontsize on the HTML overlay. */
export function overlayStyleString(style: any, refHeightPx: number): string {
  const st = style || {};
  const h = Math.max(120, Number(refHeightPx) || 360);
  const scale = h / 1080;
  const marginV = Math.max(0, Math.min(500, Math.round(Number(st.margin_v) || 0)));
  const parts: string[] = [`bottom:${Math.round(12 + marginV * scale)}px`];
  const fs = Math.round(Number(st.font_size) || 0);
  if (fs >= 10 && fs <= 120) parts.push(`font-size:${Math.max(11, Math.round(fs * scale))}px`);
  const bg = String(st.subtitle_background_color || "").trim();
  if (bg) parts.push(`background-color:${normalizeHexReview(bg)}`, "padding:6px 10px", "border-radius:8px");
  else parts.push("background-color:transparent", "padding:0", "border-radius:0");
  if (st.subtitle_font) parts.push(`font-family:${st.subtitle_font}, sans-serif`);
  parts.push(`font-weight:${st.bold ? 700 : 800}`);
  parts.push(`font-style:${st.italic ? "italic" : "normal"}`);
  parts.push(`text-align:${st.align === "left" || st.align === "right" ? st.align : "center"}`);
  return parts.join(";");
}

export function segmentRange(segment: any): string {
  return `${formatClock(Number(segment.start_s) || 0)}–${formatClock(Number(segment.end_s) || 0)}`;
}
export function segmentClass(segment: any): string {
  const lc = String(segment.lifecycle || "").trim();
  if (lc === "blocked") return "blocked";
  if (lc === "completed") return "done";
  return "";
}
