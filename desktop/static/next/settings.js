import { d as In, p as Vn, w as Un, x as Dn, f as ut, i as T, g as l, l as r, a as m, b as Gn, s as qn, e as Ht, c as N, A as he, h as e, t as h, j as s, u as x, n as F, a3 as or, Q as pt, q as Qe, m as P, r as nt, o as E, R as gt, K as Y, P as sr, z as Ze, v as ta, X as ye, V as Wn } from "./chunks/api-vHpIWCot.js";
import { o as Kn } from "./chunks/index-client-CjB8cgHo.js";
import { e as Xt, i as Yt } from "./chunks/each-BE197-93.js";
import { p as Jn, B as A } from "./chunks/Button-GpBM5g0S.js";
import { P as Hn } from "./chunks/ProgressBar-BACn-l7Z.js";
import { s as Xn } from "./chunks/screen-DRq5NjFu.js";
const Yn = [
  ["left", "L"],
  ["center", "C"],
  ["right", "R"]
], nr = "vlt.voicePreviewText", Qt = "Xin chào, đây là giọng đọc thử nghiệm.", Qn = {
  "vi-VN": "vi-VN-HoaiMyNeural",
  "en-US": "en-US-JennyNeural",
  "en-GB": "en-GB-SoniaNeural",
  "zh-CN": "zh-CN-XiaoxiaoNeural",
  "ja-JP": "ja-JP-NanamiNeural",
  "ko-KR": "ko-KR-SunHiNeural"
}, Zn = {
  bottom_band: { x: 0, y: 0.78, w: 1, h: 0.22 }
};
function lr(_) {
  const n = Number(_);
  return Number.isFinite(n) ? Math.min(600, Math.max(0, Math.round(n * 10) / 10)) : 0;
}
const tl = ["top-left", "top-right", "bottom-left", "bottom-right"];
function el(_) {
  const n = Number(_);
  return Number.isFinite(n) ? Math.min(1, Math.max(0.02, n)) : 0.15;
}
function al(_) {
  const n = Number(_);
  return Number.isFinite(n) ? Math.min(1, Math.max(0, n)) : 1;
}
function il(_) {
  const n = Number(_);
  return Number.isFinite(n) ? Math.min(0.5, Math.max(0, n)) : 0.03;
}
function rl(_) {
  const n = /* @__PURE__ */ new Set(), d = [];
  for (const a of Array.isArray(_) ? _ : []) {
    if (!a || typeof a.family != "string" || !a.family.trim()) continue;
    const S = a.family.trim(), b = S.toLowerCase();
    n.has(b) || (n.add(b), d.push({ family: S, file: String(a.file || "") }));
  }
  return d.sort((a, S) => a.family.localeCompare(S.family));
}
function ol(_) {
  const n = [];
  for (const d of Array.isArray(_) ? _ : []) {
    if (!d || typeof d.voice_id != "string" || !d.voice_id.trim()) continue;
    const a = Array.isArray(d.style_tags) ? d.style_tags.map((S) => String(S || "").trim()).filter(Boolean) : [];
    n.push({
      provider: String(d.provider || "edge_tts"),
      voice_id: d.voice_id.trim(),
      label: String(d.label || d.voice_id).trim(),
      locale: String(d.locale || "").trim(),
      locale_label: String(d.locale_label || "").trim(),
      locale_label_en: String(d.locale_label_en || "").trim(),
      gender: String(d.gender || "").trim().toLowerCase(),
      gender_label: String(d.gender_label || "").trim(),
      gender_label_en: String(d.gender_label_en || "").trim(),
      short_name: String(d.short_name || "").trim(),
      style_tags: a,
      enabled: d.enabled !== !1
    });
  }
  return n;
}
function mr(_, n) {
  const d = _.filter((a) => a.provider === n && a.enabled !== !1);
  return d.length ? d : _.filter((a) => a.provider === n);
}
function sa(_) {
  const n = String(_ || "").trim();
  if (!n) return "vi";
  const d = n.toLowerCase();
  return d.startsWith("english") ? "en" : d.startsWith("vietnam") ? "vi" : d.startsWith("chinese") ? "zh" : d.startsWith("japanese") ? "ja" : d.startsWith("korean") ? "ko" : d.split(/[-_\s]/, 1)[0] || "vi";
}
function br(_) {
  const n = sa(_);
  return n === "en" ? "en-US" : n === "zh" ? "zh-CN" : n === "ja" ? "ja-JP" : n === "ko" ? "ko-KR" : n === "vi" ? "vi-VN" : n.includes("-") ? n : "";
}
function sl(_, n) {
  const d = sa(n);
  return !!_ && !!d && _.toLowerCase().startsWith(`${d}-`);
}
function xe(_, n) {
  const d = { female: 0, male: 1 }, a = d[_.gender] ?? 9, S = d[n.gender] ?? 9;
  return a !== S ? a - S : (_.short_name || _.label || _.voice_id).localeCompare(n.short_name || n.label || n.voice_id);
}
function nl(_, n, d, a = "vi") {
  const S = mr(_, n);
  if (S.some((t) => t.voice_id === d)) return d;
  const b = br(a), Q = Qn[b], te = Q ? S.find((t) => t.voice_id === Q && t.enabled !== !1) : null;
  if (te) return te.voice_id;
  const Ot = S.filter((t) => t.locale === b || sl(t.locale, a)).sort(xe)[0];
  return Ot ? Ot.voice_id : S.filter((t) => t.gender === "female").sort(xe)[0]?.voice_id || [...S].sort(xe)[0]?.voice_id || d || "vi-VN-HoaiMyNeural";
}
function ll(_, n, d) {
  return _.filter((a) => !(n && a.locale !== n || d && a.gender !== d));
}
function _r(_, n, d) {
  return n === "vi" ? _.locale_label || _.locale_label_en || _.locale || d : _.locale_label_en || _.locale_label || _.locale || d;
}
function _l(_, n) {
  return n === "vi" ? _.gender_label || _.gender_label_en || _.gender || "" : _.gender_label_en || _.gender_label || _.gender || "";
}
function ea(_, n) {
  const d = _.short_name || _.label || _.voice_id, a = _l(_, n), S = _.style_tags.length ? _.style_tags[0] : "", b = [a, S].filter(Boolean).join(", ");
  return b ? `${d} - ${b}` : d;
}
function dr(_) {
  if (!_ || typeof _ != "object") return null;
  const n = _, d = {};
  for (const a of ["x", "y", "w", "h"]) {
    const S = Number(n[a]);
    if (!Number.isFinite(S) || S < 0 || S > 1) return null;
    d[a] = S;
  }
  return d.w <= 0 || d.h <= 0 || d.x + d.w > 1.0001 || d.y + d.h > 1.0001 ? null : d;
}
function wt(_) {
  const n = Number(_);
  return Number.isFinite(n) ? Math.max(0.5, Math.min(2, Math.round(n * 20) / 20)) : 1;
}
function vr(_) {
  return Math.max(-50, Math.min(50, Math.round((wt(_) - 1) * 100)));
}
function dl(_) {
  const n = Number(_);
  return Number.isFinite(n) ? wt(1 + n / 100) : 1;
}
function aa(_) {
  const n = Number(_);
  return Number.isFinite(n) ? Math.max(-30, Math.min(0, Math.round(n * 100) / 100)) : -15;
}
function oa(_) {
  const n = Number(_);
  return Number.isFinite(n) ? Math.max(-40, Math.min(0, Math.round(n * 100) / 100)) : -20;
}
function ke(_) {
  const n = Number(_);
  return Number.isFinite(n) ? Math.max(0, Math.min(1e4, Math.round(n))) : 0;
}
function lt(_) {
  if (!_ || typeof _ != "object") return null;
  const n = _, d = String(n.normalized_path || "").trim(), a = String(n.original_path || "").trim();
  return !d && !a ? null : {
    original_path: a,
    normalized_path: d,
    original_filename: String(n.original_filename || "").trim(),
    duration_ms: Math.max(0, Math.round(Number(n.duration_ms) || 0)),
    volume_db: oa(n.volume_db),
    loop: n.loop !== !1,
    fade_in_ms: ke(n.fade_in_ms ?? 500),
    fade_out_ms: ke(n.fade_out_ms ?? 1e3)
  };
}
function O(_) {
  const n = _ && typeof _ == "object" ? _ : {}, d = String(n.aspect_ratio || "16:9").trim(), a = String(n.logo_position || "top-right").trim();
  return {
    aspect_ratio: d === "9:16" ? "9:16" : "16:9",
    background_path: String(n.background_path || "").trim(),
    background_original_filename: String(n.background_original_filename || "").trim(),
    logo_path: String(n.logo_path || "").trim(),
    logo_original_filename: String(n.logo_original_filename || "").trim(),
    logo_position: tl.includes(a) ? a : "top-right",
    logo_scale: el(n.logo_scale ?? 0.15),
    logo_opacity: al(n.logo_opacity ?? 1),
    logo_margin: il(n.logo_margin ?? 0.03),
    intro_clip_path: String(n.intro_clip_path || "").trim(),
    intro_original_filename: String(n.intro_original_filename || "").trim(),
    outro_clip_path: String(n.outro_clip_path || "").trim(),
    outro_original_filename: String(n.outro_original_filename || "").trim(),
    head_trim_sec: lr(n.head_trim_sec ?? 0),
    tail_trim_sec: lr(n.tail_trim_sec ?? 0)
  };
}
function cr(_) {
  const n = Number(_), d = Number.isFinite(n) ? Math.round(n * 10) / 10 : 0;
  return `${d > 0 ? "+" : ""}${d} dB`;
}
function ur(_) {
  const n = Number(_) || 0;
  return `${n > 0 ? "+" : ""}${n}%`;
}
function pr(_) {
  return `${wt(_).toFixed(2).replace(/0$/, "").replace(/\.$/, "")}x`;
}
function vl(_) {
  const n = Math.max(0, Math.round((Number(_) || 0) / 1e3)), d = Math.floor(n / 60), a = String(n % 60).padStart(2, "0");
  return `${d}:${a}`;
}
function cl(_) {
  return _ === "left" ? "left" : _ === "right" ? "right" : "center";
}
function ul(_) {
  const n = String(_ || "").trim();
  return n ? `"${n}", "Segoe UI", sans-serif` : '"Segoe UI", sans-serif';
}
function pl(_) {
  const n = String(_ || "").trim();
  return /^#(?:[0-9a-f]{6}|[0-9a-f]{8})$/i.test(n) ? n.toUpperCase() : "#000000";
}
var gl = F('<div class="error-banner"><div class="error-code">UI</div><div class="error-message"> </div></div>'), ml = F('<div class="card" data-testid="settings-empty"><div class="empty-card"><div class="empty-icon">⚙</div> <h3> </h3> <p> </p></div></div>'), bl = F('<div class="small-muted run-until-edit-progress-error"> </div>'), fl = F('<div class="card work-card"><div class="work"><div class="orb"><div class="ring"></div><div class="ring r2"></div><div class="core"></div></div> <h2 class="work-title"> <span class="work-dots"></span></h2> <p class="work-sub"> </p> <div class="work-bar"><!> <div class="work-bar-foot"><span> </span><span> </span></div></div> <!></div></div>'), hl = F('<div class="info-banner"> </div>'), ia = F("<option> </option>"), yl = F('<button type="button"> </button>'), xl = F('<optgroup><option selected=""> </option></optgroup>'), kl = F("<optgroup></optgroup>"), wl = F('<div class="small-muted voice-filter-warning"> </div>'), $l = F('<audio class="audio-preview" controls="" preload="metadata"></audio>'), Zt = F('<div class="meta-empty"> </div>'), Nl = F('<div class="bgm-summary"><div class="row-title"> </div> <div class="small-muted"> </div></div> <audio class="audio-preview" controls="" preload="metadata"></audio> <div class="field-grid"><div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>-40 ... 0 dB</span></div> <input class="range-input" type="range" min="-40" max="0" step="1"/></div> <div class="switch-row"><div><div style="font-weight:700"> </div><div class="small-muted"> </div></div> <label class="checkbox-row"><input type="checkbox"/></label></div></div>', 1), ra = F("<!> <!>", 1), Sl = F('<div class="bgm-summary"><div class="row-title"> </div> <div class="small-muted"> </div></div> <img class="render-background-preview" alt=""/>', 1), Ll = F('<div class="bgm-summary"><div class="row-title"> </div> <div class="small-muted"> </div></div> <img class="render-logo-preview" alt=""/> <div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option><option> </option></select></div> <div class="field"><label> </label> <input class="input" type="range" min="2" max="60" step="1"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0" max="100" step="1"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0" max="20" step="1"/></div></div>', 1), gr = F('<div class="small-muted"> </div>'), Pl = F('<div class="section-block stack inline-action-banner" data-testid="api-key-missing" style="gap:10px"><div class="small-muted"> </div> <div class="toolbar"><!></div></div>'), jl = F('<!> <div class="stack"><div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div><div class="tag"> </div></div> <div class="card-body stack"><div class="section-block stack"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field"><label> </label> <select class="input"></select></div> <div class="field"><label> </label><input class="input" type="text" readonly=""/></div></div> <div class="stack" style="gap:10px"><div class="small-muted"> </div> <div class="toggle-bar"><button type="button" data-testid="style-bold">B</button> <button type="button" data-testid="style-italic">I</button> <!></div></div> <div class="small-muted"> </div> <div class="preview-tile"><div class="card-title"> </div> <div><span class="subtitle-sample"> </span></div></div></div> <div class="section-block stack"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field voice-picker"><label> </label> <div class="voice-filter-row"><select class="input voice-filter-select"><option> </option><!></select> <select class="input voice-filter-select"><option> </option><option> </option><option> </option></select></div> <select class="input"><!><!></select> <!></div> <div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>0.5x ... 2x</span></div> <input class="range-input" type="range" min="0.5" max="2" step="0.05"/></div> <div class="field"><label> </label> <select class="input"><option> </option><option> </option></select></div></div> <details class="advanced-details"><summary> </summary> <div class="field-grid advanced-grid"><div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>-50 ... +50</span></div> <input class="range-input" type="range" min="-50" max="50" step="1"/></div> <div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>-30 ... 0 dB</span></div> <input class="range-input" type="range" min="-30" max="0" step="1"/></div></div></details> <div class="field voice-preview-text-field"><label> </label> <input class="input" type="text"/></div> <div class="preview-tile"><div class="card-title"> </div> <div class="small-muted"><div> </div> <div> </div> <div> </div> <div> </div></div> <!> <div class="small-muted"> </div></div> <div class="toolbar"><!></div></div> <div class="section-block stack bgm-section"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <!> <div class="toolbar"><!> <!></div></div> <div class="section-block stack render-layout-section"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option></select></div></div> <!> <div class="toolbar"><!> <!> <!></div> <div class="stack" style="gap:6px;margin-top:10px"><div class="card-title"> </div><div class="card-sub"> </div></div> <!> <div class="toolbar"><!> <!></div> <div class="stack" style="gap:6px;margin-top:10px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/> <div class="small-muted"> </div></div> <div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/> <div class="small-muted"> </div></div></div> <div class="clip-row"><div class="clip-col"><div class="row-title"> </div> <!> <div class="toolbar"><!> <!></div></div> <div class="clip-col"><div class="row-title"> </div> <!> <div class="toolbar"><!> <!></div></div></div> <div class="toolbar"><!></div></div> <div class="toolbar"><!> <!></div></div></div> <div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option><option> </option><option> </option></select></div></div> <!> <details class="advanced-details"><summary> </summary> <div class="section-block"><div class="switch-row"><div><div style="font-weight:700"> </div><div class="small-muted"> </div></div> <label class="checkbox-row"><input type="checkbox"/></label></div> <div class="switch-row"><div><div style="font-weight:700"> </div><div class="small-muted"> </div></div> <label class="checkbox-row"><input type="checkbox"/></label></div></div></details> <div class="toolbar"><!></div></div></div></div>', 1), Ml = F('<div class="voice-edit-gate-backdrop" role="dialog" aria-modal="true"><div class="voice-edit-gate-card stack"><h3 class="voice-edit-gate-title"> </h3> <p class="voice-edit-gate-body"> </p> <div class="voice-edit-gate-actions"><!> <!></div></div></div>'), El = F('<div class="screen stack" data-testid="settings-screen"><!></div> <!>', 1);
function Al(_, n) {
  Vn(n, !0);
  let d = Jn(n, "ctx", 7);
  const a = (i, c) => (d()?.t ?? ((y) => y))(i, c), S = () => d()?.getLang?.() ?? "vi", b = () => String(d()?.jobWorkspace || ""), Q = () => String(d()?.parentProjectRoot || "");
  function te() {
    try {
      const i = window.localStorage.getItem(nr);
      return i && i.trim() ? i : Qt;
    } catch {
      return Qt;
    }
  }
  function Ot(i) {
    try {
      window.localStorage.setItem(nr, i || Qt);
    } catch {
    }
  }
  function na() {
    return {
      loadedJobWorkspace: "",
      loadedProjectRoot: "",
      loading: !1,
      busyAction: "",
      notice: "",
      fontOptions: [],
      voiceCatalog: [],
      voiceLocaleFilter: "",
      voiceGenderFilter: "",
      subtitle_font: "",
      subtitle_background_color: "#000000",
      bg_enabled: !1,
      subtitle_bold: !1,
      subtitle_italic: !1,
      subtitle_align: "center",
      subtitle_margin_v: 0,
      subtitle_font_size: 0,
      enable_source_cleanup: !0,
      enable_translation_qa: !1,
      use_auto_translate: !0,
      source_language: "auto",
      subtitle_extractor: "audio_only",
      external_srt_path: "",
      legacy_deprecated_extractor: !1,
      ocr_provider: "paddleocr",
      ocr_language: "ch",
      ocr_device: "auto",
      ocr_roi: { x: 0, y: 0.78, w: 1, h: 0.22 },
      translate_backend: "block_v2",
      translate_target: "vi",
      tts_provider: "edge_tts",
      tts_voice: "vi-VN-HoaiMyNeural",
      speed_multiplier: 1,
      tts_rate: 0,
      tts_pitch: 0,
      mix_mode: "replace_original_speech",
      mix_duck_gain_db: -15,
      bgm: null,
      bgmAdvancedOpen: !1,
      renderLayout: {
        aspect_ratio: "16:9",
        background_path: "",
        background_original_filename: "",
        logo_path: "",
        logo_original_filename: "",
        logo_position: "top-right",
        logo_scale: 0.15,
        logo_opacity: 1,
        logo_margin: 0.03,
        intro_clip_path: "",
        intro_original_filename: "",
        outro_clip_path: "",
        outro_original_filename: "",
        head_trim_sec: 0,
        tail_trim_sec: 0
      },
      previewAudioRel: "",
      previewAudioBust: 0,
      previewText: te(),
      voiceEditGateOpen: !1,
      openaiKeyMissing: !1,
      runUntilEditLive: null
    };
  }
  let t = Un(d()?.settingsState || na());
  d() && (d().settingsState = t);
  let mt = qn(""), $t = null;
  Kn(() => {
    $t && clearInterval($t);
  });
  const C = () => !!t.loading || !!t.busyAction;
  function ee(i, c) {
    if (!b()) return "";
    const y = new URLSearchParams({ workspace: b(), rel: i });
    return c && y.set("v", String(c)), `/media?${y.toString()}`;
  }
  function ae() {
    t.previewAudioRel = "", t.previewAudioBust = 0;
  }
  async function la(i = !1) {
    if (!b() || !i && t.loadedJobWorkspace === b() && t.loadedProjectRoot === Q()) return;
    t.loading = !0, t.notice = "", Ht(mt, "");
    const c = !i && t.fontOptions.length ? Promise.resolve({ fonts: t.fontOptions }) : N("/api/list-system-fonts"), y = !i && t.voiceCatalog.length ? Promise.resolve({ voices: t.voiceCatalog }) : N("/api/list-voices");
    try {
      const [
        w,
        j,
        _t,
        It,
        Vt,
        z,
        I,
        Z,
        et
      ] = await Promise.all([
        N("/api/get-video-style", { job_workspace: b() }),
        N("/api/get-video-tts", { job_workspace: b() }),
        Q() ? N("/api/get-project-style", { project_root: Q() }) : Promise.resolve({ style: {} }),
        Q() ? N("/api/get-project-tts", { project_root: Q() }) : Promise.resolve({ settings: {} }),
        N("/api/get-import-config", { job_workspace: b() }),
        c,
        y,
        N("/api/bgm/status", { job_workspace: b() }),
        N("/api/render-settings/status", { job_workspace: b() })
      ]), G = { ..._t.style || {}, ...w.style || {} }, R = { ...It.settings || {}, ...j.settings || {} }, dt = d()?.importConfig && d().importConfig.job_workspace === b() ? d().importConfig : null, M = { ...Vt.config || {}, ...dt || {} }, q = String(M?.subtitle_extractor || "audio_only").toLowerCase();
      let at = !1, V = q;
      q === "ocr_only" || q === "hybrid" ? (at = !0, V = "audio_only") : q !== "external_srt" && (V = "audio_only");
      const it = rl(z.fonts || []), D = ol(I.voices || []), tt = M?.tts_provider || R.tts_provider || "edge_tts", Nt = Number.isFinite(Number(R.tts_rate)) ? Number(R.tts_rate) : 0, bt = sa(M?.translate_target || M?.target_language || M?.target_locale || "vi");
      Object.assign(t, {
        loadedJobWorkspace: b(),
        loadedProjectRoot: Q(),
        loading: !1,
        fontOptions: it,
        voiceCatalog: D,
        subtitle_font: G.subtitle_font || "",
        subtitle_background_color: G.subtitle_background_color || "#000000",
        bg_enabled: !!G.subtitle_background_color,
        subtitle_bold: !!G.bold,
        subtitle_italic: !!G.italic,
        subtitle_align: G.align || "center",
        use_auto_translate: M?.use_auto_translate ?? !0,
        source_language: M?.source_language || "auto",
        translate_target: bt,
        translate_backend: M?.translate_backend || "block_v2",
        subtitle_extractor: V,
        external_srt_path: String(M?.external_srt_path || "").trim(),
        legacy_deprecated_extractor: at,
        ocr_provider: M?.ocr_provider || "paddleocr",
        ocr_language: M?.ocr_language || "ch",
        ocr_device: M?.ocr_device || "auto",
        ocr_roi: dr(M?.ocr_roi) || { x: 0, y: 0.78, w: 1, h: 0.22 },
        tts_provider: tt,
        tts_voice: nl(D, tt, R.tts_voice || "", bt),
        speed_multiplier: Number.isFinite(Number(R.speed_multiplier)) ? wt(Number(R.speed_multiplier)) : dl(Nt),
        tts_rate: Nt,
        tts_pitch: Number.isFinite(Number(R.tts_pitch)) ? Number(R.tts_pitch) : 0,
        mix_mode: R.mix_mode || "replace_original_speech",
        mix_duck_gain_db: Number.isFinite(Number(R.mix_duck_gain_db)) ? aa(Number(R.mix_duck_gain_db)) : -15,
        bgm: lt(Z?.bgm),
        bgmAdvancedOpen: !1,
        renderLayout: O(et?.render),
        previewAudioRel: "",
        previewAudioBust: 0,
        openaiKeyMissing: !1,
        notice: a("settings.notice_loaded")
      });
    } catch (w) {
      t.loading = !1, Ht(mt, we(w), !0);
    }
  }
  function we(i) {
    return i instanceof he ? i.summary || i.message : i?.message || a("error.generic");
  }
  async function U(i, c) {
    if (d()) {
      Ht(mt, ""), t.busyAction = i, t.notice = "";
      try {
        await c();
      } catch (y) {
        Ht(mt, we(y), !0);
      } finally {
        d() && (t.busyAction = "");
      }
    }
  }
  const hr = () => {
    const i = {};
    return (t.subtitle_font || "").trim() && (i.subtitle_font = t.subtitle_font.trim()), i.bold = !!t.subtitle_bold, i.italic = !!t.subtitle_italic, i.align = t.subtitle_align || "center", i;
  }, yr = () => ({
    tts_provider: t.tts_provider,
    tts_voice: (t.tts_voice || "").trim(),
    speed_multiplier: wt(t.speed_multiplier),
    tts_rate: vr(t.speed_multiplier),
    tts_pitch: Number(t.tts_pitch) || 0,
    mix_mode: t.mix_mode,
    mix_duck_gain_db: aa(t.mix_duck_gain_db)
  }), _a = () => {
    const i = lt(t.bgm);
    return i ? {
      original_path: i.original_path,
      normalized_path: i.normalized_path,
      original_filename: i.original_filename,
      duration_ms: i.duration_ms,
      volume_db: oa(i.volume_db),
      loop: !!i.loop,
      fade_in_ms: ke(i.fade_in_ms),
      fade_out_ms: ke(i.fade_out_ms)
    } : {};
  }, zt = () => {
    const i = O(t.renderLayout), c = {
      aspect_ratio: i.aspect_ratio,
      background_path: i.background_path,
      background_original_filename: i.background_original_filename
    };
    return i.logo_path && (c.logo_path = i.logo_path, c.logo_original_filename = i.logo_original_filename, c.logo_position = i.logo_position, c.logo_scale = i.logo_scale, c.logo_opacity = i.logo_opacity, c.logo_margin = i.logo_margin), i.intro_clip_path && (c.intro_clip_path = i.intro_clip_path, c.intro_original_filename = i.intro_original_filename), i.outro_clip_path && (c.outro_clip_path = i.outro_clip_path, c.outro_original_filename = i.outro_original_filename), c.head_trim_sec = i.head_trim_sec, c.tail_trim_sec = i.tail_trim_sec, c;
  }, xr = () => {
    const i = t.subtitle_extractor || "audio_only", c = {
      use_auto_translate: !!t.use_auto_translate,
      translate_backend: t.translate_backend || "block_v2",
      tts_provider: t.tts_provider || "edge_tts",
      subtitle_extractor: i,
      external_srt_path: i === "external_srt" ? String(t.external_srt_path || "").trim() : "",
      ocr_provider: t.ocr_provider || "paddleocr",
      ocr_language: t.ocr_language || "ch",
      ocr_device: t.ocr_device || "auto"
    };
    return i === "audio_only" && (c.ocr_roi = dr(t.ocr_roi) || Zn.bottom_band), c;
  }, kr = () => {
    if (d()?.parentProject) return String(d().parentProject);
    const c = b().replace(/[\\/]+$/, "").split(/[\\/]/);
    return c[c.length - 1] || "job";
  }, wr = () => U("save_text_audio", async () => {
    const i = [
      N("/api/save-video-style", { job_workspace: b(), style: hr() }),
      N("/api/save-video-tts", { job_workspace: b(), settings: yr() })
    ], c = !!t.bgm;
    c && i.push(N("/api/bgm/save", { job_workspace: b(), bgm: _a() })), i.push(N("/api/render-settings/save", { job_workspace: b(), render: zt() }));
    const y = await Promise.all(i), w = y[1], j = c ? y[2] : null, _t = c ? y[3] : y[2];
    Number.isFinite(Number(w.settings?.speed_multiplier)) && (t.speed_multiplier = wt(Number(w.settings.speed_multiplier))), Number.isFinite(Number(w.settings?.tts_rate)) && (t.tts_rate = Number(w.settings.tts_rate)), j && (t.bgm = lt(j.bgm)), _t && (t.renderLayout = O(_t.render)), t.notice = a("settings.notice_saved_text_audio", { path: b() });
  }), $r = () => U("bgm_upload", async () => {
    const i = await ye(["Audio files (*.mp3;*.wav;*.m4a;*.aac)", "All files (*.*)"]);
    if (i?.cancelled) return;
    if (!i?.ok || !i.path) throw new Error(i?.error || a("settings.bgm.pick_unavailable"));
    const c = lt(t.bgm) || {}, y = await N("/api/bgm/upload", {
      job_workspace: b(),
      bgm_path: i.path,
      volume_db: c.volume_db ?? -20,
      loop: c.loop ?? !0,
      fade_in_ms: c.fade_in_ms ?? 500,
      fade_out_ms: c.fade_out_ms ?? 1e3
    });
    t.bgm = lt(y.bgm), t.notice = a("settings.bgm.uploaded");
  }), Nr = () => {
    if (t.bgm)
      return U("bgm_save", async () => {
        const i = await N("/api/bgm/save", { job_workspace: b(), bgm: _a() });
        t.bgm = lt(i.bgm), t.notice = a("settings.bgm.saved");
      });
  }, Sr = () => {
    if (!(!t.bgm || !window.confirm(a("settings.bgm.confirm_remove"))))
      return U("bgm_remove", async () => {
        await N("/api/bgm/remove", { job_workspace: b() }), t.bgm = null, t.bgmAdvancedOpen = !1, t.notice = a("settings.bgm.removed");
      });
  }, Lr = () => U("render_background_upload", async () => {
    const i = await ye(["Image files (*.jpg;*.jpeg;*.png;*.webp)", "All files (*.*)"]);
    if (i?.cancelled) return;
    if (!i?.ok || !i.path) throw new Error(i?.error || a("settings.render_layout.pick_unavailable"));
    await N("/api/render-settings/save", { job_workspace: b(), render: zt() });
    const c = await N("/api/render-background/upload", { job_workspace: b(), image_path: i.path });
    t.renderLayout = O(c.render), t.notice = a("settings.render_layout.uploaded");
  }), $e = () => U("render_layout_save", async () => {
    const i = await N("/api/render-settings/save", { job_workspace: b(), render: zt() });
    t.renderLayout = O(i.render), t.notice = a("settings.render_layout.saved");
  }), Pr = () => {
    if (!(!O(t.renderLayout).background_path || !window.confirm(a("settings.render_layout.confirm_remove"))))
      return U("render_background_remove", async () => {
        const i = await N("/api/render-background/remove", { job_workspace: b() });
        t.renderLayout = O(i.render), t.notice = a("settings.render_layout.removed");
      });
  };
  function ie(i) {
    t.renderLayout = O({ ...t.renderLayout, ...i });
  }
  const jr = () => U("render_logo_upload", async () => {
    const i = await ye(["Image files (*.png;*.jpg;*.jpeg;*.webp)", "All files (*.*)"]);
    if (i?.cancelled) return;
    if (!i?.ok || !i.path) throw new Error(i?.error || a("settings.render_layout.pick_unavailable"));
    await N("/api/render-settings/save", { job_workspace: b(), render: zt() });
    const c = await N("/api/render-logo/upload", { job_workspace: b(), image_path: i.path });
    t.renderLayout = O(c.render), t.notice = a("settings.render_layout.logo_uploaded");
  }), Mr = () => {
    if (!(!O(t.renderLayout).logo_path || !window.confirm(a("settings.render_layout.logo_confirm_remove"))))
      return U("render_logo_remove", async () => {
        const i = await N("/api/render-logo/remove", { job_workspace: b() });
        t.renderLayout = O(i.render), t.notice = a("settings.render_layout.logo_removed");
      });
  }, da = (i) => U(`render_${i}_upload`, async () => {
    const c = await ye([
      "Video files (*.mp4;*.mov;*.mkv;*.webm;*.m4v)",
      "All files (*.*)"
    ]);
    if (c?.cancelled) return;
    if (!c?.ok || !c.path) throw new Error(c?.error || a("settings.render_layout.pick_unavailable"));
    await N("/api/render-settings/save", { job_workspace: b(), render: zt() });
    const y = await N(`/api/render-${i}/upload`, { job_workspace: b(), clip_path: c.path });
    t.renderLayout = O(y.render), t.notice = a(`settings.render_layout.${i}_uploaded`);
  }), va = (i) => {
    if (!(!(i === "intro" ? O(t.renderLayout).intro_clip_path : O(t.renderLayout).outro_clip_path) || !window.confirm(a("settings.render_layout.clip_confirm_remove"))))
      return U(`render_${i}_remove`, async () => {
        const y = await N(`/api/render-${i}/remove`, { job_workspace: b() });
        t.renderLayout = O(y.render), t.notice = a(`settings.render_layout.${i}_removed`);
      });
  };
  function ca(i) {
    t.renderLayout = O({ ...t.renderLayout, ...i });
  }
  const Er = () => U("tts_preview", async () => {
    const i = (t.previewText || "").trim() || Qt;
    Ot(i);
    const c = await N("/api/tts-preview", {
      job_workspace: b(),
      tts_provider: t.tts_provider,
      tts_voice: t.tts_voice,
      speed_multiplier: t.speed_multiplier,
      text: i
    });
    t.previewText = i, t.previewAudioRel = c.rel_path || "", t.previewAudioBust = Number(c.cache_bust) || Date.now(), t.notice = a("settings.tts.preview_ready");
  });
  function Ne() {
    N("/api/job-progress", { job_workspace: b() }).then((i) => {
      t.runUntilEditLive = {
        overall_percent: Number(i.overall_percent) || 0,
        current_stage_label: String(i.current_stage_label || ""),
        current_stage: String(i.current_stage || ""),
        status_label: String(i.status_label || ""),
        lifecycle: String(i.lifecycle || ""),
        last_error: i.last_error != null ? String(i.last_error) : null
      };
    }).catch(() => {
    });
  }
  const Ar = () => U("run_until_edit", async () => {
    t.openaiKeyMissing = !1, t.runUntilEditLive = {
      overall_percent: 0,
      current_stage_label: "",
      current_stage: "",
      status_label: "",
      lifecycle: "queued",
      last_error: null
    }, Ne();
    try {
      $t = setInterval(Ne, 800);
      try {
        const w = await N("/api/save-import-config", { job_workspace: b(), config: xr() });
        d().importConfig = { job_workspace: b(), ...w?.config || {} };
      } catch {
      }
      const i = await N("/api/run-until-edit", {
        job_workspace: b(),
        project_name: kr(),
        use_auto_translate: !0,
        source_language: t.source_language,
        translate_backend: "block_v2",
        enable_source_cleanup: !!t.enable_source_cleanup,
        enable_translation_qa: !!t.enable_translation_qa,
        async: !0,
        subtitle_extractor: "audio_only"
      }), c = await Wn(b(), i);
      d().applyJobStatusToEditGate?.(d(), c), Ne();
      const y = c.voice_edit_status || "";
      if (y === "voice_edit_pending") {
        t.voiceEditGateOpen = !0, t.notice = a("settings.notice_run_until_edit", { stage: a(`stage.${y}`) }), t.runUntilEditLive = null;
        return;
      }
      t.voiceEditGateOpen = !1, t.notice = a("settings.notice_run_until_edit", { stage: a(`stage.${y || "voice_edit_pending"}`) }), t.runUntilEditLive = null, d().navigate("review");
    } catch (i) {
      if (i instanceof he && i.code === "api_key_required") {
        t.openaiKeyMissing = !0, t.runUntilEditLive = null;
        return;
      }
      const c = t.runUntilEditLive?.current_stage_label || t.runUntilEditLive?.current_stage || "", y = i instanceof he ? i.message || i.code || "" : we(i), w = i instanceof he && Array.isArray(i.logTail) && i.logTail.length ? `
— Log:
` + i.logTail.slice(-8).join(`
`) : "";
      Ht(mt, a("settings.run_failed", { stage: c || "—", message: y }) + w), t.runUntilEditLive = null;
      return;
    } finally {
      $t && (clearInterval($t), $t = null), d() && (t.runUntilEditLive = null);
    }
  }), ua = x(() => mr(t.voiceCatalog, t.tts_provider)), Fr = x(() => {
    const i = /* @__PURE__ */ new Map();
    for (const c of l(ua))
      !c.locale || i.has(c.locale) || i.set(c.locale, _r(c, S(), a("settings.tts.locale_unknown")));
    return Array.from(i.entries()).sort((c, y) => c[1].localeCompare(y[1]));
  }), pa = x(() => ll(l(ua), t.voiceLocaleFilter, t.voiceGenderFilter)), ga = x(() => !!t.tts_voice && !l(pa).some((i) => i.voice_id === t.tts_voice)), re = x(() => t.voiceCatalog.find((i) => i.provider === t.tts_provider && i.voice_id === t.tts_voice)), Rr = x(() => {
    const i = br(t.translate_target), c = /* @__PURE__ */ new Map();
    for (const w of [...l(pa)].sort(xe)) {
      const j = w.locale || a("settings.tts.locale_unknown");
      c.has(j) || c.set(j, []), c.get(j).push(w);
    }
    const y = (w, j) => w[0] ? _r(w[0], S(), a("settings.tts.locale_unknown")) : j;
    return Array.from(c.entries()).sort((w, j) => w[0] === i && j[0] !== i ? -1 : j[0] === i && w[0] !== i ? 1 : y(w[1], w[0]).localeCompare(y(j[1], j[0]))).map(([w, j]) => ({ label: y(j, w), items: j }));
  }), Tr = x(() => l(re) ? ea(l(re), S()) : t.tts_voice || a("settings.tts.voice_placeholder")), Cr = x(() => t.mix_mode === "duck_original_speech" ? a("settings.tts.mix_duck") : a("settings.tts.mix_replace")), K = x(() => lt(t.bgm)), k = x(() => O(t.renderLayout));
  function Br(i) {
    t.tts_voice = i.target.value, ae();
  }
  function Or(i) {
    t.speed_multiplier = wt(i), t.tts_rate = vr(t.speed_multiplier), ae();
  }
  const zr = x(() => {
    const i = [];
    t.subtitle_font && !t.fontOptions.some((c) => c.family === t.subtitle_font) && i.push([t.subtitle_font, t.subtitle_font]);
    for (const c of t.fontOptions) i.push([c.family, c.family]);
    return i.length ? i : [[t.subtitle_font || "Arial", t.subtitle_font || "Arial"]];
  });
  Dn(() => {
    b(), Q(), la();
  });
  var ma = ra(), ba = ut(ma);
  {
    var Ir = (i) => {
      var c = gl(), y = r(e(c)), w = e(y);
      h(() => s(w, l(mt))), m(i, c);
    };
    T(ba, (i) => {
      l(mt) && i(Ir);
    });
  }
  var Vr = r(ba, 2);
  {
    var Ur = (i) => {
      var c = ml(), y = e(c), w = r(e(y), 2), j = e(w), _t = r(w, 2), It = e(_t);
      h(
        (Vt, z) => {
          s(j, Vt), s(It, z);
        },
        [
          () => a("settings.empty_title"),
          () => a("settings.empty_body")
        ]
      ), m(i, c);
    }, Dr = x(() => !b()), Gr = (i) => {
      var c = El(), y = ut(c), w = e(y);
      {
        var j = (z) => {
          const I = x(() => t.runUntilEditLive), Z = x(() => Math.max(0, Math.min(100, Number(l(I)?.overall_percent) || 0)));
          var et = fl(), G = e(et), R = r(e(G), 2), dt = e(R), M = r(R, 2), q = e(M), at = r(M, 2), V = e(at);
          Hn(V, {
            get percent() {
              return l(Z);
            },
            wide: !0
          });
          var it = r(V, 2), D = e(it), tt = e(D), Nt = r(D), bt = e(Nt), oe = r(at, 2);
          {
            var se = (ft) => {
              var St = bl(), Ut = e(St);
              h(() => s(Ut, l(I).last_error)), m(ft, St);
            };
            T(oe, (ft) => {
              l(I)?.last_error && ft(se);
            });
          }
          h(
            (ft, St, Ut, ne) => {
              s(dt, ft), s(q, `${St ?? ""}${l(I)?.status_label ? ` · ${l(I).status_label}` : ""}`), s(tt, Ut), s(bt, `${ne ?? ""}%`);
            },
            [
              () => a("settings.run_until_edit_progress_title"),
              () => l(I)?.current_stage_label || a("settings.run_until_edit_progress_waiting"),
              () => a("settings.translation.progress_percent", { percent: Math.round(l(Z)) }),
              () => Math.round(l(Z))
            ]
          ), m(z, et);
        }, _t = (z) => {
          var I = jl(), Z = ut(I);
          {
            var et = (o) => {
              var v = hl(), p = e(v);
              h(() => s(p, t.notice)), m(o, v);
            };
            T(Z, (o) => {
              t.notice && o(et);
            });
          }
          var G = r(Z, 2), R = e(G), dt = e(R), M = e(dt), q = e(M), at = e(q), V = r(q), it = e(V), D = r(M), tt = e(D), Nt = r(dt, 2), bt = e(Nt), oe = e(bt), se = e(oe), ft = e(se), St = r(se), Ut = e(St), ne = r(oe, 2), fa = e(ne), ha = e(fa), qr = e(ha), Lt = r(ha, 2);
          Xt(Lt, 21, () => l(zr), Yt, (o, v) => {
            var p = x(() => ta(l(v), 2));
            let u = () => l(p)[0], g = () => l(p)[1];
            var f = ia(), L = e(f), $ = {};
            h(() => {
              or(f, u() === t.subtitle_font), s(L, g()), $ !== ($ = u()) && (f.value = (f.__value = u()) ?? "");
            }), m(o, f);
          });
          var ya;
          pt(Lt);
          var Wr = r(fa, 2), xa = e(Wr), Kr = e(xa), Jr = r(xa), ka = r(ne, 2), wa = e(ka), Hr = e(wa), Xr = r(wa, 2), Se = e(Xr), Le = r(Se, 2), Yr = r(Le, 2);
          Xt(Yr, 17, () => Yn, Yt, (o, v) => {
            var p = x(() => ta(l(v), 2));
            let u = () => l(p)[0], g = () => l(p)[1];
            var f = yl(), L = e(f);
            h(() => {
              Qe(f, 1, `toggle-btn ${t.subtitle_align === u() ? "active" : ""}`), s(L, g());
            }), P("click", f, () => t.subtitle_align = u()), m(o, f);
          });
          var $a = r(ka, 2), Qr = e($a), Zr = r($a, 2), Na = e(Zr), to = e(Na), Sa = r(Na, 2), La = e(Sa), eo = e(La), Pa = r(bt, 2), ja = e(Pa), Ma = e(ja), ao = e(Ma), io = r(Ma), ro = e(io), Ea = r(ja, 2), Aa = e(Ea), Fa = e(Aa), oo = e(Fa), Ra = r(Fa, 2), vt = e(Ra), le = e(vt), so = e(le);
          le.value = le.__value = "";
          var no = r(le);
          Xt(no, 17, () => l(Fr), Yt, (o, v) => {
            var p = x(() => ta(l(v), 2));
            let u = () => l(p)[0], g = () => l(p)[1];
            var f = ia(), L = e(f), $ = {};
            h(() => {
              s(L, g()), $ !== ($ = u()) && (f.value = (f.__value = u()) ?? "");
            }), m(o, f);
          });
          var Ta;
          pt(vt);
          var ht = r(vt, 2), _e = e(ht), lo = e(_e);
          _e.value = _e.__value = "";
          var de = r(_e), _o = e(de);
          de.value = de.__value = "female";
          var Pe = r(de), vo = e(Pe);
          Pe.value = Pe.__value = "male";
          var Ca;
          pt(ht);
          var yt = r(Ra, 2), Ba = e(yt);
          {
            var co = (o) => {
              var v = xl(), p = e(v), u = e(p), g = {};
              h(
                (f, L) => {
                  nt(v, "label", f), s(u, L), g !== (g = t.tts_voice) && (p.value = (p.__value = t.tts_voice) ?? "");
                },
                [
                  () => a("settings.tts.current_voice"),
                  () => l(re) ? ea(l(re), S()) : t.tts_voice
                ]
              ), m(o, v);
            };
            T(Ba, (o) => {
              l(ga) && o(co);
            });
          }
          var uo = r(Ba);
          Xt(uo, 17, () => l(Rr), Yt, (o, v) => {
            var p = kl();
            Xt(p, 21, () => l(v).items, Yt, (u, g) => {
              var f = ia(), L = e(f), $ = {};
              h(
                (B) => {
                  or(f, l(g).voice_id === t.tts_voice), s(L, B), $ !== ($ = l(g).voice_id) && (f.value = (f.__value = l(g).voice_id) ?? "");
                },
                [() => ea(l(g), S())]
              ), m(u, f);
            }), h(() => nt(p, "label", l(v).label)), m(o, p);
          });
          var Oa;
          pt(yt);
          var po = r(yt, 2);
          {
            var go = (o) => {
              var v = wl(), p = e(v);
              h((u) => s(p, u), [() => a("settings.tts.filter_current_hidden")]), m(o, v);
            };
            T(po, (o) => {
              l(ga) && o(go);
            });
          }
          var za = r(Aa, 2), Ia = e(za), mo = e(Ia), Va = r(Ia, 2), bo = e(Va), fo = e(bo), Ua = r(Va, 2), ho = r(za, 2), Da = e(ho), yo = e(Da), Pt = r(Da, 2), ve = e(Pt), xo = e(ve);
          ve.value = ve.__value = "replace_original_speech";
          var je = r(ve), ko = e(je);
          je.value = je.__value = "duck_original_speech";
          var Ga;
          pt(Pt);
          var qa = r(Ea, 2), Wa = e(qa), wo = e(Wa), $o = r(Wa, 2), Ka = e($o), Ja = e(Ka), No = e(Ja), Ha = r(Ja, 2), So = e(Ha), Lo = e(So), Xa = r(Ha, 2), Po = r(Ka, 2), Ya = e(Po), jo = e(Ya), Qa = r(Ya, 2), Mo = e(Qa), Eo = e(Mo), Za = r(Qa, 2), ti = r(qa, 2), ei = e(ti), Ao = e(ei), Me = r(ei, 2), ai = r(ti, 2), ii = e(ai), Fo = e(ii), ri = r(ii, 2), oi = e(ri), Ro = e(oi), si = r(oi, 2), To = e(si), ni = r(si, 2), Co = e(ni), Bo = r(ni, 2), Oo = e(Bo), li = r(ri, 2);
          {
            var zo = (o) => {
              var v = $l();
              h((p) => nt(v, "src", p), [() => ee(t.previewAudioRel, t.previewAudioBust)]), m(o, v);
            };
            T(li, (o) => {
              t.previewAudioRel && o(zo);
            });
          }
          var Io = r(li, 2), Vo = e(Io), Uo = r(ai, 2), Do = e(Uo);
          {
            let o = x(C);
            A(Do, {
              variant: "strong",
              get disabled() {
                return l(o);
              },
              onclick: Er,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.tts.test_voice")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var _i = r(Pa, 2), di = e(_i), vi = e(di), Go = e(vi), qo = r(vi), Wo = e(qo), ci = r(di, 2);
          {
            var Ko = (o) => {
              var v = Zt(), p = e(v);
              h((u) => s(p, u), [() => a("settings.bgm.no_bgm")]), m(o, v);
            }, Jo = (o) => {
              var v = Nl(), p = ut(v), u = e(p), g = e(u), f = r(u, 2), L = e(f), $ = r(p, 2), B = r($, 2), W = e(B), J = e(W), Dt = e(J), H = r(J, 2), ct = e(H), Gt = e(ct), rt = r(H, 2), qt = r(W, 2), ot = e(qt), Et = e(ot), xt = e(Et), Wt = r(Et), At = e(Wt), Ft = r(ot, 2), kt = e(Ft);
              h(
                (st, Rt, Tt, Ct, Kt, Bt, Jt) => {
                  s(g, st), s(L, Rt), nt($, "src", Tt), s(Dt, Ct), s(Gt, Kt), Y(rt, l(K).volume_db), s(xt, Bt), s(At, Jt), Ze(kt, l(K).loop);
                },
                [
                  () => (l(K).original_filename || l(K).original_path || l(K).normalized_path).split(/[\\/]/).pop(),
                  () => a("settings.bgm.duration", { duration: vl(l(K).duration_ms) }),
                  () => ee(l(K).normalized_path || l(K).original_path, Date.now()),
                  () => a("settings.bgm.volume"),
                  () => cr(l(K).volume_db),
                  () => a("settings.bgm.loop"),
                  () => a("settings.bgm.loop_sub")
                ]
              ), P("input", rt, (st) => t.bgm = lt({ ...t.bgm, volume_db: oa(Number(st.target.value)) })), P("change", kt, (st) => t.bgm = lt({ ...t.bgm, loop: st.target.checked })), m(o, v);
            };
            T(ci, (o) => {
              l(K) ? o(Jo, -1) : o(Ko);
            });
          }
          var Ho = r(ci, 2), ui = e(Ho);
          {
            let o = x(C);
            A(ui, {
              variant: "secondary",
              get disabled() {
                return l(o);
              },
              onclick: $r,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.bgm.upload")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Xo = r(ui, 2);
          {
            var Yo = (o) => {
              var v = ra(), p = ut(v);
              {
                let g = x(C);
                A(p, {
                  variant: "primary",
                  get disabled() {
                    return l(g);
                  },
                  onclick: Nr,
                  children: (f, L) => {
                    var $ = E();
                    h((B) => s($, B), [() => a("settings.bgm.save")]), m(f, $);
                  },
                  $$slots: { default: !0 }
                });
              }
              var u = r(p, 2);
              {
                let g = x(C);
                A(u, {
                  get disabled() {
                    return l(g);
                  },
                  onclick: Sr,
                  children: (f, L) => {
                    var $ = E();
                    h((B) => s($, B), [() => a("settings.bgm.remove")]), m(f, $);
                  },
                  $$slots: { default: !0 }
                });
              }
              m(o, v);
            };
            T(Xo, (o) => {
              l(K) && o(Yo);
            });
          }
          var pi = r(_i, 2), gi = e(pi), mi = e(gi), Qo = e(mi), Zo = r(mi), ts = e(Zo), bi = r(gi, 2), es = e(bi), fi = e(es), as = e(fi), jt = r(fi, 2), ce = e(jt), is = e(ce);
          ce.value = ce.__value = "16:9";
          var Ee = r(ce), rs = e(Ee);
          Ee.value = Ee.__value = "9:16";
          var hi;
          pt(jt);
          var yi = r(bi, 2);
          {
            var os = (o) => {
              var v = Sl(), p = ut(v), u = e(p), g = e(u), f = r(u, 2), L = e(f), $ = r(p, 2);
              h(
                (B, W, J) => {
                  s(g, B), s(L, W), nt($, "src", J);
                },
                [
                  () => (l(k).background_original_filename || l(k).background_path).split(/[\\/]/).pop(),
                  () => a("settings.render_layout.background_ready"),
                  () => ee(l(k).background_path, Date.now())
                ]
              ), m(o, v);
            }, ss = (o) => {
              var v = Zt(), p = e(v);
              h((u) => s(p, u), [() => a("settings.render_layout.no_background")]), m(o, v);
            };
            T(yi, (o) => {
              l(k).background_path ? o(os) : o(ss, -1);
            });
          }
          var xi = r(yi, 2), ki = e(xi);
          {
            let o = x(C);
            A(ki, {
              variant: "secondary",
              get disabled() {
                return l(o);
              },
              onclick: Lr,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.render_layout.upload_background")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var wi = r(ki, 2);
          {
            let o = x(C);
            A(wi, {
              variant: "primary",
              get disabled() {
                return l(o);
              },
              onclick: $e,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.render_layout.save")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var ns = r(wi, 2);
          {
            var ls = (o) => {
              {
                let v = x(C);
                A(o, {
                  get disabled() {
                    return l(v);
                  },
                  onclick: Pr,
                  children: (p, u) => {
                    var g = E();
                    h((f) => s(g, f), [() => a("settings.render_layout.remove_background")]), m(p, g);
                  },
                  $$slots: { default: !0 }
                });
              }
            };
            T(ns, (o) => {
              l(k).background_path && o(ls);
            });
          }
          var $i = r(xi, 2), Ni = e($i), _s = e(Ni), ds = r(Ni), vs = e(ds), Si = r($i, 2);
          {
            var cs = (o) => {
              var v = Ll(), p = ut(v), u = e(p), g = e(u), f = r(u, 2), L = e(f), $ = r(p, 2), B = r($, 2), W = e(B), J = e(W), Dt = e(J), H = r(J, 2), ct = e(H), Gt = e(ct);
              ct.value = ct.__value = "top-left";
              var rt = r(ct), qt = e(rt);
              rt.value = rt.__value = "top-right";
              var ot = r(rt), Et = e(ot);
              ot.value = ot.__value = "bottom-left";
              var xt = r(ot), Wt = e(xt);
              xt.value = xt.__value = "bottom-right";
              var At;
              pt(H);
              var Ft = r(W, 2), kt = e(Ft), st = e(kt), Rt = r(kt, 2), Tt = r(Ft, 2), Ct = e(Tt), Kt = e(Ct), Bt = r(Ct, 2), Jt = r(Tt, 2), be = e(Jt), Te = e(be), fe = r(be, 2);
              h(
                (X, Ce, Be, Oe, ze, Ie, Ve, Ue, De, Ge, qe, We, Ke, Je, He, Xe, Ye) => {
                  s(g, X), s(L, Ce), nt($, "src", Be), s(Dt, Oe), s(Gt, ze), s(qt, Ie), s(Et, Ve), s(Wt, Ue), At !== (At = l(k).logo_position) && (H.value = (H.__value = l(k).logo_position) ?? "", gt(H, l(k).logo_position)), s(st, `${De ?? ""} (${Ge ?? ""}%)`), Y(Rt, qe), s(Kt, `${We ?? ""} (${Ke ?? ""}%)`), Y(Bt, Je), s(Te, `${He ?? ""} (${Xe ?? ""}%)`), Y(fe, Ye);
                },
                [
                  () => (l(k).logo_original_filename || l(k).logo_path).split(/[\\/]/).pop(),
                  () => a("settings.render_layout.logo_ready"),
                  () => ee(l(k).logo_path, Date.now()),
                  () => a("settings.render_layout.logo_position"),
                  () => a("settings.render_layout.pos_top_left"),
                  () => a("settings.render_layout.pos_top_right"),
                  () => a("settings.render_layout.pos_bottom_left"),
                  () => a("settings.render_layout.pos_bottom_right"),
                  () => a("settings.render_layout.logo_scale"),
                  () => Math.round(l(k).logo_scale * 100),
                  () => Math.round(l(k).logo_scale * 100),
                  () => a("settings.render_layout.logo_opacity"),
                  () => Math.round(l(k).logo_opacity * 100),
                  () => Math.round(l(k).logo_opacity * 100),
                  () => a("settings.render_layout.logo_margin"),
                  () => Math.round(l(k).logo_margin * 100),
                  () => Math.round(l(k).logo_margin * 100)
                ]
              ), P("change", H, (X) => ie({ logo_position: X.target.value })), P("input", Rt, (X) => ie({ logo_scale: Number(X.target.value) / 100 })), P("input", Bt, (X) => ie({ logo_opacity: Number(X.target.value) / 100 })), P("input", fe, (X) => ie({ logo_margin: Number(X.target.value) / 100 })), m(o, v);
            }, us = (o) => {
              var v = Zt(), p = e(v);
              h((u) => s(p, u), [() => a("settings.render_layout.no_logo")]), m(o, v);
            };
            T(Si, (o) => {
              l(k).logo_path ? o(cs) : o(us, -1);
            });
          }
          var Li = r(Si, 2), Pi = e(Li);
          {
            let o = x(C);
            A(Pi, {
              variant: "secondary",
              get disabled() {
                return l(o);
              },
              onclick: jr,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.render_layout.upload_logo")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var ps = r(Pi, 2);
          {
            var gs = (o) => {
              var v = ra(), p = ut(v);
              {
                let g = x(C);
                A(p, {
                  variant: "primary",
                  get disabled() {
                    return l(g);
                  },
                  onclick: $e,
                  children: (f, L) => {
                    var $ = E();
                    h((B) => s($, B), [() => a("settings.render_layout.save")]), m(f, $);
                  },
                  $$slots: { default: !0 }
                });
              }
              var u = r(p, 2);
              {
                let g = x(C);
                A(u, {
                  get disabled() {
                    return l(g);
                  },
                  onclick: Mr,
                  children: (f, L) => {
                    var $ = E();
                    h((B) => s($, B), [() => a("settings.render_layout.remove_logo")]), m(f, $);
                  },
                  $$slots: { default: !0 }
                });
              }
              m(o, v);
            };
            T(ps, (o) => {
              l(k).logo_path && o(gs);
            });
          }
          var ji = r(Li, 2), Mi = e(ji), ms = e(Mi), bs = r(Mi), fs = e(bs), Ei = r(ji, 2), Ai = e(Ei), Fi = e(Ai), hs = e(Fi), Ae = r(Fi, 2), ys = r(Ae, 2), xs = e(ys), ks = r(Ai, 2), Ri = e(ks), ws = e(Ri), Fe = r(Ri, 2), $s = r(Fe, 2), Ns = e($s), Ti = r(Ei, 2), Ci = e(Ti), Bi = e(Ci), Ss = e(Bi), Oi = r(Bi, 2);
          {
            var Ls = (o) => {
              var v = gr(), p = e(v);
              h((u) => s(p, u), [
                () => (l(k).intro_original_filename || l(k).intro_clip_path).split(/[\\/]/).pop()
              ]), m(o, v);
            }, Ps = (o) => {
              var v = Zt(), p = e(v);
              h((u) => s(p, u), [() => a("settings.render_layout.no_clip")]), m(o, v);
            };
            T(Oi, (o) => {
              l(k).intro_clip_path ? o(Ls) : o(Ps, -1);
            });
          }
          var js = r(Oi, 2), zi = e(js);
          {
            let o = x(C);
            A(zi, {
              variant: "secondary",
              get disabled() {
                return l(o);
              },
              onclick: () => da("intro"),
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.render_layout.upload_intro")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Ms = r(zi, 2);
          {
            var Es = (o) => {
              {
                let v = x(C);
                A(o, {
                  get disabled() {
                    return l(v);
                  },
                  onclick: () => va("intro"),
                  children: (p, u) => {
                    var g = E();
                    h((f) => s(g, f), [() => a("settings.render_layout.remove_clip")]), m(p, g);
                  },
                  $$slots: { default: !0 }
                });
              }
            };
            T(Ms, (o) => {
              l(k).intro_clip_path && o(Es);
            });
          }
          var As = r(Ci, 2), Ii = e(As), Fs = e(Ii), Vi = r(Ii, 2);
          {
            var Rs = (o) => {
              var v = gr(), p = e(v);
              h((u) => s(p, u), [
                () => (l(k).outro_original_filename || l(k).outro_clip_path).split(/[\\/]/).pop()
              ]), m(o, v);
            }, Ts = (o) => {
              var v = Zt(), p = e(v);
              h((u) => s(p, u), [() => a("settings.render_layout.no_clip")]), m(o, v);
            };
            T(Vi, (o) => {
              l(k).outro_clip_path ? o(Rs) : o(Ts, -1);
            });
          }
          var Cs = r(Vi, 2), Ui = e(Cs);
          {
            let o = x(C);
            A(Ui, {
              variant: "secondary",
              get disabled() {
                return l(o);
              },
              onclick: () => da("outro"),
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.render_layout.upload_outro")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Bs = r(Ui, 2);
          {
            var Os = (o) => {
              {
                let v = x(C);
                A(o, {
                  get disabled() {
                    return l(v);
                  },
                  onclick: () => va("outro"),
                  children: (p, u) => {
                    var g = E();
                    h((f) => s(g, f), [() => a("settings.render_layout.remove_clip")]), m(p, g);
                  },
                  $$slots: { default: !0 }
                });
              }
            };
            T(Bs, (o) => {
              l(k).outro_clip_path && o(Os);
            });
          }
          var zs = r(Ti, 2), Is = e(zs);
          {
            let o = x(C);
            A(Is, {
              variant: "primary",
              get disabled() {
                return l(o);
              },
              onclick: $e,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.render_layout.save")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Vs = r(pi, 2), Di = e(Vs);
          {
            let o = x(C);
            A(Di, {
              variant: "secondary",
              get disabled() {
                return l(o);
              },
              onclick: () => la(!0),
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.reload")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Us = r(Di, 2);
          {
            let o = x(C);
            A(Us, {
              "data-testid": "save-text-audio",
              variant: "primary",
              get disabled() {
                return l(o);
              },
              onclick: wr,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.text_audio.save")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Ds = r(R, 2), Gi = e(Ds), Gs = e(Gi), qi = e(Gs), qs = e(qi), Ws = r(qi), Ks = e(Ws), Js = r(Gi, 2), Wi = e(Js), Hs = e(Wi), Ki = e(Hs), Xs = e(Ki), Mt = r(Ki, 2), ue = e(Mt), Ys = e(ue);
          ue.value = ue.__value = "auto";
          var pe = r(ue), Qs = e(pe);
          pe.value = pe.__value = "zh";
          var ge = r(pe), Zs = e(ge);
          ge.value = ge.__value = "en";
          var me = r(ge), tn = e(me);
          me.value = me.__value = "ja";
          var Re = r(me), en = e(Re);
          Re.value = Re.__value = "ko";
          var Ji;
          pt(Mt);
          var Hi = r(Wi, 2);
          {
            var an = (o) => {
              var v = Pl(), p = e(v), u = e(p), g = r(p, 2), f = e(g);
              {
                let L = x(C);
                A(f, {
                  variant: "secondary",
                  get disabled() {
                    return l(L);
                  },
                  onclick: () => d().navigate("app_settings"),
                  children: ($, B) => {
                    var W = E();
                    h((J) => s(W, J), [() => a("settings.translation.go_to_app_settings")]), m($, W);
                  },
                  $$slots: { default: !0 }
                });
              }
              h((L) => s(u, L), [() => a("settings.translation.api_key_required")]), m(o, v);
            };
            T(Hi, (o) => {
              t.openaiKeyMissing && o(an);
            });
          }
          var Xi = r(Hi, 2), Yi = e(Xi), rn = e(Yi), on = r(Yi, 2), Qi = e(on), Zi = e(Qi), tr = e(Zi), sn = e(tr), nn = r(tr), ln = e(nn), _n = r(Zi, 2), er = e(_n), dn = r(Qi, 2), ar = e(dn), ir = e(ar), vn = e(ir), cn = r(ir), un = e(cn), pn = r(ar, 2), rr = e(pn), gn = r(Xi, 2), mn = e(gn);
          {
            let o = x(C);
            A(mn, {
              "data-testid": "run-until-edit",
              variant: "strong",
              get disabled() {
                return l(o);
              },
              onclick: Ar,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.translation.run_until_edit_auto")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          h(
            (o, v, p, u, g, f, L, $, B, W, J, Dt, H, ct, Gt, rt, qt, ot, Et, xt, Wt, At, Ft, kt, st, Rt, Tt, Ct, Kt, Bt, Jt, be, Te, fe, X, Ce, Be, Oe, ze, Ie, Ve, Ue, De, Ge, qe, We, Ke, Je, He, Xe, Ye, bn, fn, hn, yn, xn, kn, wn, $n, Nn, Sn, Ln, Pn, jn, Mn, En, An, Fn, Rn, Tn, Cn, Bn, On, zn) => {
              s(at, o), s(it, v), s(tt, p), s(ft, u), s(Ut, g), s(qr, f), ya !== (ya = t.subtitle_font) && (Lt.value = (Lt.__value = t.subtitle_font) ?? "", gt(Lt, t.subtitle_font)), s(Kr, L), Y(Jr, $), s(Hr, B), Qe(Se, 1, `toggle-btn ${t.subtitle_bold ? "active" : ""}`), Qe(Le, 1, `toggle-btn ${t.subtitle_italic ? "active" : ""}`), s(Qr, W), s(to, J), sr(Sa, Dt), sr(La, H), s(eo, ct), s(ao, Gt), s(ro, rt), s(oo, qt), nt(vt, "aria-label", ot), s(so, `${Et ?? ""}: ${xt ?? ""}`), Ta !== (Ta = t.voiceLocaleFilter) && (vt.value = (vt.__value = t.voiceLocaleFilter) ?? "", gt(vt, t.voiceLocaleFilter)), nt(ht, "aria-label", Wt), s(lo, `${At ?? ""}: ${Ft ?? ""}`), s(_o, kt), s(vo, st), Ca !== (Ca = t.voiceGenderFilter) && (ht.value = (ht.__value = t.voiceGenderFilter) ?? "", gt(ht, t.voiceGenderFilter)), Oa !== (Oa = t.tts_voice) && (yt.value = (yt.__value = t.tts_voice) ?? "", gt(yt, t.tts_voice)), s(mo, Rt), s(fo, Tt), Y(Ua, t.speed_multiplier), s(yo, Ct), s(xo, Kt), s(ko, Bt), Ga !== (Ga = t.mix_mode) && (Pt.value = (Pt.__value = t.mix_mode) ?? "", gt(Pt, t.mix_mode)), s(wo, Jt), s(No, be), s(Lo, Te), Y(Xa, t.tts_pitch), s(jo, fe), s(Eo, X), Y(Za, t.mix_duck_gain_db), s(Ao, Ce), nt(Me, "placeholder", Qt), Y(Me, t.previewText), s(Fo, Be), s(Ro, `${Oe ?? ""}: ${l(Tr) ?? ""}`), s(To, `${ze ?? ""}: ${Ie ?? ""}`), s(Co, `${Ve ?? ""}: ${Ue ?? ""}`), s(Oo, `${De ?? ""}: ${l(Cr) ?? ""}`), s(Vo, Ge), s(Go, qe), s(Wo, We), s(Qo, Ke), s(ts, Je), s(as, He), s(is, Xe), s(rs, Ye), hi !== (hi = l(k).aspect_ratio) && (jt.value = (jt.__value = l(k).aspect_ratio) ?? "", gt(jt, l(k).aspect_ratio)), s(_s, bn), s(vs, fn), s(ms, hn), s(fs, yn), s(hs, `${xn ?? ""} (${l(k).head_trim_sec ?? ""}s)`), Y(Ae, l(k).head_trim_sec), s(xs, kn), s(ws, `${wn ?? ""} (${l(k).tail_trim_sec ?? ""}s)`), Y(Fe, l(k).tail_trim_sec), s(Ns, $n), s(Ss, Nn), s(Fs, Sn), s(qs, Ln), s(Ks, Pn), s(Xs, jn), s(Ys, Mn), s(Qs, En), s(Zs, An), s(tn, Fn), s(en, Rn), Ji !== (Ji = t.source_language) && (Mt.value = (Mt.__value = t.source_language) ?? "", gt(Mt, t.source_language)), s(rn, Tn), s(sn, Cn), s(ln, Bn), Ze(er, t.enable_source_cleanup), s(vn, On), s(un, zn), Ze(rr, t.enable_translation_qa);
            },
            [
              () => a("settings.text_audio.title"),
              () => a("settings.text_audio.sub"),
              () => a("settings.scope_video"),
              () => a("settings.subtitle.title"),
              () => a("settings.subtitle.sub"),
              () => a("settings.subtitle.font"),
              () => a("settings.subtitle.mode"),
              () => a("settings.subtitle.mode_value"),
              () => a("settings.subtitle.style_tools"),
              () => a("settings.subtitle.burn_moved_hint"),
              () => a("settings.subtitle.preview_title"),
              () => `flex:1;display:grid;align-items:end;background:var(--bg-0);border-radius:14px;padding:28px;text-align:${cl(t.subtitle_align)}`,
              () => `font-family:${ul(t.subtitle_font)};background:${t.bg_enabled ? pl(t.subtitle_background_color) : "transparent"};font-weight:${t.subtitle_bold ? 800 : 500};font-style:${t.subtitle_italic ? "italic" : "normal"}`,
              () => a("settings.subtitle.preview_sample"),
              () => a("settings.tts.title"),
              () => a("settings.tts.sub"),
              () => a("settings.tts.voice"),
              () => a("settings.tts.filter_locale"),
              () => a("settings.tts.filter_locale"),
              () => a("settings.tts.filter_all"),
              () => a("settings.tts.filter_gender"),
              () => a("settings.tts.filter_gender"),
              () => a("settings.tts.filter_all"),
              () => a("settings.tts.filter_female"),
              () => a("settings.tts.filter_male"),
              () => a("settings.tts.speed"),
              () => pr(t.speed_multiplier),
              () => a("settings.tts.mix_mode"),
              () => a("settings.tts.mix_replace"),
              () => a("settings.tts.mix_duck"),
              () => a("settings.tts.advanced"),
              () => a("settings.tts.pitch"),
              () => ur(t.tts_pitch),
              () => a("settings.tts.duck_gain"),
              () => cr(t.mix_duck_gain_db),
              () => a("settings.tts.preview_text_label"),
              () => a("settings.tts.preview_title"),
              () => a("settings.tts.voice"),
              () => a("settings.tts.speed"),
              () => pr(t.speed_multiplier),
              () => a("settings.tts.pitch"),
              () => ur(t.tts_pitch),
              () => a("settings.tts.mix_mode"),
              () => a("settings.tts.preview_sub"),
              () => a("settings.bgm.title"),
              () => a("settings.bgm.sub"),
              () => a("settings.render_layout.title"),
              () => a("settings.render_layout.sub"),
              () => a("settings.render_layout.aspect_ratio"),
              () => a("settings.render_layout.aspect_16_9"),
              () => a("settings.render_layout.aspect_9_16"),
              () => a("settings.render_layout.logo_title"),
              () => a("settings.render_layout.logo_sub"),
              () => a("settings.render_layout.clips_title"),
              () => a("settings.render_layout.clips_sub"),
              () => a("settings.render_layout.head_trim"),
              () => a("settings.render_layout.head_trim_hint"),
              () => a("settings.render_layout.tail_trim"),
              () => a("settings.render_layout.tail_trim_hint"),
              () => a("settings.render_layout.intro_clip"),
              () => a("settings.render_layout.outro_clip"),
              () => a("settings.translation.title"),
              () => a("settings.translation.sub"),
              () => a("settings.translation.source_language"),
              () => a("settings.translation.source_language_auto"),
              () => a("settings.translation.source_language_zh"),
              () => a("settings.translation.source_language_en"),
              () => a("settings.translation.source_language_ja"),
              () => a("settings.translation.source_language_ko"),
              () => a("settings.tts.advanced"),
              () => a("settings.translation.cleanup_title"),
              () => a("settings.translation.cleanup_sub"),
              () => a("settings.translation.qa_title"),
              () => a("settings.translation.qa_sub")
            ]
          ), P("change", Lt, (o) => t.subtitle_font = o.target.value), P("click", Se, () => t.subtitle_bold = !t.subtitle_bold), P("click", Le, () => t.subtitle_italic = !t.subtitle_italic), P("change", vt, (o) => t.voiceLocaleFilter = o.target.value), P("change", ht, (o) => t.voiceGenderFilter = o.target.value), P("change", yt, Br), P("input", Ua, (o) => Or(Number(o.target.value))), P("change", Pt, (o) => t.mix_mode = o.target.value), P("input", Xa, (o) => {
            t.tts_pitch = Number(o.target.value), ae();
          }), P("input", Za, (o) => t.mix_duck_gain_db = aa(Number(o.target.value))), P("input", Me, (o) => {
            t.previewText = o.target.value, Ot(t.previewText), ae();
          }), P("change", jt, (o) => t.renderLayout = O({ ...t.renderLayout, aspect_ratio: o.target.value })), P("change", Ae, (o) => ca({ head_trim_sec: Number(o.target.value) })), P("change", Fe, (o) => ca({ tail_trim_sec: Number(o.target.value) })), P("change", Mt, (o) => t.source_language = o.target.value), P("change", er, (o) => t.enable_source_cleanup = o.target.checked), P("change", rr, (o) => t.enable_translation_qa = o.target.checked), m(z, I);
        };
        T(w, (z) => {
          t.busyAction === "run_until_edit" ? z(j) : z(_t, -1);
        });
      }
      var It = r(y, 2);
      {
        var Vt = (z) => {
          var I = Ml(), Z = e(I), et = e(Z), G = e(et), R = r(et, 2), dt = e(R), M = r(R, 2), q = e(M);
          A(q, {
            variant: "secondary",
            onclick: () => {
              t.voiceEditGateOpen = !1, d().navigate("review");
            },
            children: (V, it) => {
              var D = E();
              h((tt) => s(D, tt), [() => a("settings.voice_edit_gate.pause")]), m(V, D);
            },
            $$slots: { default: !0 }
          });
          var at = r(q, 2);
          A(at, {
            variant: "strong",
            onclick: () => {
              t.voiceEditGateOpen = !1, d().pendingVoiceEditContinue = !0, d().navigate("render");
            },
            children: (V, it) => {
              var D = E();
              h((tt) => s(D, tt), [() => a("settings.voice_edit_gate.continue")]), m(V, D);
            },
            $$slots: { default: !0 }
          }), h(
            (V, it) => {
              s(G, V), s(dt, it);
            },
            [
              () => a("settings.voice_edit_gate.title"),
              () => a("settings.voice_edit_gate.body")
            ]
          ), m(z, I);
        };
        T(It, (z) => {
          t.voiceEditGateOpen && z(Vt);
        });
      }
      m(i, c);
    };
    T(Vr, (i) => {
      l(Dr) ? i(Ur) : i(Gr, -1);
    });
  }
  m(_, ma), Gn();
}
In(["change", "click", "input"]);
const fr = Xn(Al), zl = fr.mount, Il = fr.unmount;
export {
  zl as mount,
  Il as unmount
};
//# sourceMappingURL=settings.js.map
