import { d as Dn, p as Gn, w as qn, x as Wn, f as ut, i as T, g as l, l as r, a as m, b as Kn, s as Jn, e as Ht, c as N, A as ye, h as e, t as h, j as s, u as x, n as F, a3 as sr, Q as pt, q as Ze, m as P, r as nt, o as E, R as gt, K as Y, P as nr, z as ta, v as ea, X as xe, V as Hn } from "./chunks/api-vHpIWCot.js";
import { o as Xn } from "./chunks/index-client-CjB8cgHo.js";
import { e as Xt, i as Yt } from "./chunks/each-BE197-93.js";
import { p as Yn, B as A } from "./chunks/Button-GpBM5g0S.js";
import { P as Qn } from "./chunks/ProgressBar-BACn-l7Z.js";
import { s as Zn } from "./chunks/screen-DRq5NjFu.js";
const tl = [
  ["left", "L"],
  ["center", "C"],
  ["right", "R"]
], lr = "vlt.voicePreviewText", Qt = "Xin chào, đây là giọng đọc thử nghiệm.", el = {
  "vi-VN": "vi-VN-HoaiMyNeural",
  "en-US": "en-US-JennyNeural",
  "en-GB": "en-GB-SoniaNeural",
  "zh-CN": "zh-CN-XiaoxiaoNeural",
  "ja-JP": "ja-JP-NanamiNeural",
  "ko-KR": "ko-KR-SunHiNeural"
}, al = {
  bottom_band: { x: 0, y: 0.78, w: 1, h: 0.22 }
};
function _r(_) {
  const n = Number(_);
  return Number.isFinite(n) ? Math.min(600, Math.max(0, Math.round(n * 10) / 10)) : 0;
}
const il = ["top-left", "top-right", "bottom-left", "bottom-right"];
function rl(_) {
  const n = Number(_);
  return Number.isFinite(n) ? Math.min(1, Math.max(0.02, n)) : 0.15;
}
function ol(_) {
  const n = Number(_);
  return Number.isFinite(n) ? Math.min(1, Math.max(0, n)) : 1;
}
function sl(_) {
  const n = Number(_);
  return Number.isFinite(n) ? Math.min(0.5, Math.max(0, n)) : 0.03;
}
function nl(_) {
  const n = /* @__PURE__ */ new Set(), d = [];
  for (const a of Array.isArray(_) ? _ : []) {
    if (!a || typeof a.family != "string" || !a.family.trim()) continue;
    const S = a.family.trim(), b = S.toLowerCase();
    n.has(b) || (n.add(b), d.push({ family: S, file: String(a.file || "") }));
  }
  return d.sort((a, S) => a.family.localeCompare(S.family));
}
function ll(_) {
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
function br(_, n) {
  const d = _.filter((a) => a.provider === n && a.enabled !== !1);
  return d.length ? d : _.filter((a) => a.provider === n);
}
function na(_) {
  const n = String(_ || "").trim();
  if (!n) return "vi";
  const d = n.toLowerCase();
  return d.startsWith("english") ? "en" : d.startsWith("vietnam") ? "vi" : d.startsWith("chinese") ? "zh" : d.startsWith("japanese") ? "ja" : d.startsWith("korean") ? "ko" : d.split(/[-_\s]/, 1)[0] || "vi";
}
function fr(_) {
  const n = na(_);
  return n === "en" ? "en-US" : n === "zh" ? "zh-CN" : n === "ja" ? "ja-JP" : n === "ko" ? "ko-KR" : n === "vi" ? "vi-VN" : n.includes("-") ? n : "";
}
function _l(_, n) {
  const d = na(n);
  return !!_ && !!d && _.toLowerCase().startsWith(`${d}-`);
}
function ke(_, n) {
  const d = { female: 0, male: 1 }, a = d[_.gender] ?? 9, S = d[n.gender] ?? 9;
  return a !== S ? a - S : (_.short_name || _.label || _.voice_id).localeCompare(n.short_name || n.label || n.voice_id);
}
function dl(_, n, d, a = "vi") {
  const S = br(_, n);
  if (S.some((t) => t.voice_id === d)) return d;
  const b = fr(a), Q = el[b], te = Q ? S.find((t) => t.voice_id === Q && t.enabled !== !1) : null;
  if (te) return te.voice_id;
  const Ot = S.filter((t) => t.locale === b || _l(t.locale, a)).sort(ke)[0];
  return Ot ? Ot.voice_id : S.filter((t) => t.gender === "female").sort(ke)[0]?.voice_id || [...S].sort(ke)[0]?.voice_id || d || "vi-VN-HoaiMyNeural";
}
function vl(_, n, d) {
  return _.filter((a) => !(n && a.locale !== n || d && a.gender !== d));
}
function dr(_, n, d) {
  return n === "vi" ? _.locale_label || _.locale_label_en || _.locale || d : _.locale_label_en || _.locale_label || _.locale || d;
}
function cl(_, n) {
  return n === "vi" ? _.gender_label || _.gender_label_en || _.gender || "" : _.gender_label_en || _.gender_label || _.gender || "";
}
function aa(_, n) {
  const d = _.short_name || _.label || _.voice_id, a = cl(_, n), S = _.style_tags.length ? _.style_tags[0] : "", b = [a, S].filter(Boolean).join(", ");
  return b ? `${d} - ${b}` : d;
}
function vr(_) {
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
function cr(_) {
  return Math.max(-50, Math.min(50, Math.round((wt(_) - 1) * 100)));
}
function ul(_) {
  const n = Number(_);
  return Number.isFinite(n) ? wt(1 + n / 100) : 1;
}
function ia(_) {
  const n = Number(_);
  return Number.isFinite(n) ? Math.max(-30, Math.min(0, Math.round(n * 100) / 100)) : -15;
}
function sa(_) {
  const n = Number(_);
  return Number.isFinite(n) ? Math.max(-40, Math.min(0, Math.round(n * 100) / 100)) : -20;
}
function we(_) {
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
    volume_db: sa(n.volume_db),
    loop: n.loop !== !1,
    fade_in_ms: we(n.fade_in_ms ?? 500),
    fade_out_ms: we(n.fade_out_ms ?? 1e3)
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
    logo_position: il.includes(a) ? a : "top-right",
    logo_scale: rl(n.logo_scale ?? 0.15),
    logo_opacity: ol(n.logo_opacity ?? 1),
    logo_margin: sl(n.logo_margin ?? 0.03),
    intro_clip_path: String(n.intro_clip_path || "").trim(),
    intro_original_filename: String(n.intro_original_filename || "").trim(),
    outro_clip_path: String(n.outro_clip_path || "").trim(),
    outro_original_filename: String(n.outro_original_filename || "").trim(),
    head_trim_sec: _r(n.head_trim_sec ?? 0),
    tail_trim_sec: _r(n.tail_trim_sec ?? 0)
  };
}
function ur(_) {
  const n = Number(_), d = Number.isFinite(n) ? Math.round(n * 10) / 10 : 0;
  return `${d > 0 ? "+" : ""}${d} dB`;
}
function pr(_) {
  const n = Number(_) || 0;
  return `${n > 0 ? "+" : ""}${n}%`;
}
function gr(_) {
  return `${wt(_).toFixed(2).replace(/0$/, "").replace(/\.$/, "")}x`;
}
function pl(_) {
  const n = Math.max(0, Math.round((Number(_) || 0) / 1e3)), d = Math.floor(n / 60), a = String(n % 60).padStart(2, "0");
  return `${d}:${a}`;
}
function gl(_) {
  return _ === "left" ? "left" : _ === "right" ? "right" : "center";
}
function ml(_) {
  const n = String(_ || "").trim();
  return n ? `"${n}", "Segoe UI", sans-serif` : '"Segoe UI", sans-serif';
}
function bl(_) {
  const n = String(_ || "").trim();
  return /^#(?:[0-9a-f]{6}|[0-9a-f]{8})$/i.test(n) ? n.toUpperCase() : "#000000";
}
var fl = F('<div class="error-banner"><div class="error-code">UI</div><div class="error-message"> </div></div>'), hl = F('<div class="card" data-testid="settings-empty"><div class="empty-card"><div class="empty-icon">⚙</div> <h3> </h3> <p> </p></div></div>'), yl = F('<div class="small-muted run-until-edit-progress-error"> </div>'), xl = F('<div class="card work-card"><div class="work"><div class="orb"><div class="ring"></div><div class="ring r2"></div><div class="core"></div></div> <h2 class="work-title"> <span class="work-dots"></span></h2> <p class="work-sub"> </p> <div class="work-bar"><!> <div class="work-bar-foot"><span> </span><span> </span></div></div> <!></div></div>'), kl = F('<div class="info-banner"> </div>'), ra = F("<option> </option>"), wl = F('<button type="button"> </button>'), $l = F('<optgroup><option selected=""> </option></optgroup>'), Nl = F("<optgroup></optgroup>"), Sl = F('<div class="small-muted voice-filter-warning"> </div>'), Ll = F('<audio class="audio-preview" controls="" preload="metadata"></audio>'), Zt = F('<div class="meta-empty"> </div>'), Pl = F('<div class="bgm-summary"><div class="row-title"> </div> <div class="small-muted"> </div></div> <audio class="audio-preview" controls="" preload="metadata"></audio> <div class="field-grid"><div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>-40 ... 0 dB</span></div> <input class="range-input" type="range" min="-40" max="0" step="1"/></div> <div class="switch-row"><div><div style="font-weight:700"> </div><div class="small-muted"> </div></div> <label class="checkbox-row"><input type="checkbox"/></label></div></div>', 1), oa = F("<!> <!>", 1), jl = F('<div class="bgm-summary"><div class="row-title"> </div> <div class="small-muted"> </div></div> <img class="render-background-preview" alt=""/>', 1), Ml = F('<div class="bgm-summary"><div class="row-title"> </div> <div class="small-muted"> </div></div> <img class="render-logo-preview" alt=""/> <div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option><option> </option></select></div> <div class="field"><label> </label> <input class="input" type="range" min="2" max="60" step="1"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0" max="100" step="1"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0" max="20" step="1"/></div></div>', 1), mr = F('<div class="small-muted"> </div>'), El = F('<div class="section-block stack inline-action-banner" data-testid="api-key-missing" style="gap:10px"><div class="small-muted"> </div> <div class="toolbar"><!></div></div>'), Al = F('<!> <div class="stack"><div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div><div class="tag"> </div></div> <div class="card-body stack"><div class="section-block stack"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field"><label> </label> <select class="input"></select></div> <div class="field"><label> </label><input class="input" type="text" readonly=""/></div></div> <div class="stack" style="gap:10px"><div class="small-muted"> </div> <div class="toggle-bar"><button type="button" data-testid="style-bold">B</button> <button type="button" data-testid="style-italic">I</button> <!></div></div> <div class="small-muted"> </div> <div class="preview-tile"><div class="card-title"> </div> <div><span class="subtitle-sample"> </span></div></div></div> <div class="section-block stack"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field voice-picker"><label> </label> <div class="voice-filter-row"><select class="input voice-filter-select"><option> </option><!></select> <select class="input voice-filter-select"><option> </option><option> </option><option> </option></select></div> <select class="input"><!><!></select> <!></div> <div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>0.5x ... 2x</span></div> <input class="range-input" type="range" min="0.5" max="2" step="0.05"/></div> <div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option></select></div></div> <details class="advanced-details"><summary> </summary> <div class="field-grid advanced-grid"><div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>-50 ... +50</span></div> <input class="range-input" type="range" min="-50" max="50" step="1"/></div> <div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>-30 ... 0 dB</span></div> <input class="range-input" type="range" min="-30" max="0" step="1"/></div></div></details> <div class="field voice-preview-text-field"><label> </label> <input class="input" type="text"/></div> <div class="preview-tile"><div class="card-title"> </div> <div class="small-muted"><div> </div> <div> </div> <div> </div> <div> </div></div> <!> <div class="small-muted"> </div></div> <div class="toolbar"><!></div></div> <div class="section-block stack bgm-section"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <!> <div class="toolbar"><!> <!></div></div> <div class="section-block stack render-layout-section"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option></select></div></div> <!> <div class="toolbar"><!> <!> <!></div> <div class="stack" style="gap:6px;margin-top:10px"><div class="card-title"> </div><div class="card-sub"> </div></div> <!> <div class="toolbar"><!> <!></div> <div class="stack" style="gap:6px;margin-top:10px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/> <div class="small-muted"> </div></div> <div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/> <div class="small-muted"> </div></div></div> <div class="clip-row"><div class="clip-col"><div class="row-title"> </div> <!> <div class="toolbar"><!> <!></div></div> <div class="clip-col"><div class="row-title"> </div> <!> <div class="toolbar"><!> <!></div></div></div> <div class="toolbar"><!></div></div> <div class="toolbar"><!> <!></div></div></div> <div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option><option> </option><option> </option></select></div></div> <!> <details class="advanced-details"><summary> </summary> <div class="section-block"><div class="switch-row"><div><div style="font-weight:700"> </div><div class="small-muted"> </div></div> <label class="checkbox-row"><input type="checkbox"/></label></div> <div class="switch-row"><div><div style="font-weight:700"> </div><div class="small-muted"> </div></div> <label class="checkbox-row"><input type="checkbox"/></label></div></div></details> <div class="toolbar"><!></div></div></div></div>', 1), Fl = F('<div class="voice-edit-gate-backdrop" role="dialog" aria-modal="true"><div class="voice-edit-gate-card stack"><h3 class="voice-edit-gate-title"> </h3> <p class="voice-edit-gate-body"> </p> <div class="voice-edit-gate-actions"><!> <!></div></div></div>'), Rl = F('<div class="screen stack" data-testid="settings-screen"><!></div> <!>', 1);
function Tl(_, n) {
  Gn(n, !0);
  let d = Yn(n, "ctx", 7);
  const a = (i, c) => (d()?.t ?? ((y) => y))(i, c), S = () => d()?.getLang?.() ?? "vi", b = () => String(d()?.jobWorkspace || ""), Q = () => String(d()?.parentProjectRoot || "");
  function te() {
    try {
      const i = window.localStorage.getItem(lr);
      return i && i.trim() ? i : Qt;
    } catch {
      return Qt;
    }
  }
  function Ot(i) {
    try {
      window.localStorage.setItem(lr, i || Qt);
    } catch {
    }
  }
  function la() {
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
  let t = qn(d()?.settingsState || la());
  d() && (d().settingsState = t);
  let mt = Jn(""), $t = null;
  Xn(() => {
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
  async function _a(i = !1) {
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
      const it = nl(z.fonts || []), D = ll(I.voices || []), tt = M?.tts_provider || R.tts_provider || "edge_tts", Nt = Number.isFinite(Number(R.tts_rate)) ? Number(R.tts_rate) : 0, bt = na(M?.translate_target || M?.target_language || M?.target_locale || "vi");
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
        ocr_roi: vr(M?.ocr_roi) || { x: 0, y: 0.78, w: 1, h: 0.22 },
        tts_provider: tt,
        tts_voice: dl(D, tt, R.tts_voice || "", bt),
        speed_multiplier: Number.isFinite(Number(R.speed_multiplier)) ? wt(Number(R.speed_multiplier)) : ul(Nt),
        tts_rate: Nt,
        tts_pitch: Number.isFinite(Number(R.tts_pitch)) ? Number(R.tts_pitch) : 0,
        mix_mode: R.mix_mode || "replace_original_speech",
        mix_duck_gain_db: Number.isFinite(Number(R.mix_duck_gain_db)) ? ia(Number(R.mix_duck_gain_db)) : -15,
        bgm: lt(Z?.bgm),
        bgmAdvancedOpen: !1,
        renderLayout: O(et?.render),
        previewAudioRel: "",
        previewAudioBust: 0,
        openaiKeyMissing: !1,
        notice: a("settings.notice_loaded")
      });
    } catch (w) {
      t.loading = !1, Ht(mt, $e(w), !0);
    }
  }
  function $e(i) {
    return i instanceof ye ? i.summary || i.message : i?.message || a("error.generic");
  }
  async function U(i, c) {
    if (d()) {
      Ht(mt, ""), t.busyAction = i, t.notice = "";
      try {
        await c();
      } catch (y) {
        Ht(mt, $e(y), !0);
      } finally {
        d() && (t.busyAction = "");
      }
    }
  }
  const yr = () => {
    const i = {};
    return (t.subtitle_font || "").trim() && (i.subtitle_font = t.subtitle_font.trim()), i.bold = !!t.subtitle_bold, i.italic = !!t.subtitle_italic, i.align = t.subtitle_align || "center", i;
  }, xr = () => ({
    tts_provider: t.tts_provider,
    tts_voice: (t.tts_voice || "").trim(),
    speed_multiplier: wt(t.speed_multiplier),
    tts_rate: cr(t.speed_multiplier),
    tts_pitch: Number(t.tts_pitch) || 0,
    mix_mode: t.mix_mode,
    mix_duck_gain_db: ia(t.mix_duck_gain_db)
  }), da = () => {
    const i = lt(t.bgm);
    return i ? {
      original_path: i.original_path,
      normalized_path: i.normalized_path,
      original_filename: i.original_filename,
      duration_ms: i.duration_ms,
      volume_db: sa(i.volume_db),
      loop: !!i.loop,
      fade_in_ms: we(i.fade_in_ms),
      fade_out_ms: we(i.fade_out_ms)
    } : {};
  }, zt = () => {
    const i = O(t.renderLayout), c = {
      aspect_ratio: i.aspect_ratio,
      background_path: i.background_path,
      background_original_filename: i.background_original_filename
    };
    return i.logo_path && (c.logo_path = i.logo_path, c.logo_original_filename = i.logo_original_filename, c.logo_position = i.logo_position, c.logo_scale = i.logo_scale, c.logo_opacity = i.logo_opacity, c.logo_margin = i.logo_margin), i.intro_clip_path && (c.intro_clip_path = i.intro_clip_path, c.intro_original_filename = i.intro_original_filename), i.outro_clip_path && (c.outro_clip_path = i.outro_clip_path, c.outro_original_filename = i.outro_original_filename), c.head_trim_sec = i.head_trim_sec, c.tail_trim_sec = i.tail_trim_sec, c;
  }, kr = () => {
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
    return i === "audio_only" && (c.ocr_roi = vr(t.ocr_roi) || al.bottom_band), c;
  }, wr = () => {
    if (d()?.parentProject) return String(d().parentProject);
    const c = b().replace(/[\\/]+$/, "").split(/[\\/]/);
    return c[c.length - 1] || "job";
  }, $r = () => U("save_text_audio", async () => {
    const i = [
      N("/api/save-video-style", { job_workspace: b(), style: yr() }),
      N("/api/save-video-tts", { job_workspace: b(), settings: xr() })
    ], c = !!t.bgm;
    c && i.push(N("/api/bgm/save", { job_workspace: b(), bgm: da() })), i.push(N("/api/render-settings/save", { job_workspace: b(), render: zt() }));
    const y = await Promise.all(i), w = y[1], j = c ? y[2] : null, _t = c ? y[3] : y[2];
    Number.isFinite(Number(w.settings?.speed_multiplier)) && (t.speed_multiplier = wt(Number(w.settings.speed_multiplier))), Number.isFinite(Number(w.settings?.tts_rate)) && (t.tts_rate = Number(w.settings.tts_rate)), j && (t.bgm = lt(j.bgm)), _t && (t.renderLayout = O(_t.render)), t.notice = a("settings.notice_saved_text_audio", { path: b() });
  }), Nr = () => U("bgm_upload", async () => {
    const i = await xe(["Audio files (*.mp3;*.wav;*.m4a;*.aac)", "All files (*.*)"]);
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
  }), Sr = () => {
    if (t.bgm)
      return U("bgm_save", async () => {
        const i = await N("/api/bgm/save", { job_workspace: b(), bgm: da() });
        t.bgm = lt(i.bgm), t.notice = a("settings.bgm.saved");
      });
  }, Lr = () => {
    if (!(!t.bgm || !window.confirm(a("settings.bgm.confirm_remove"))))
      return U("bgm_remove", async () => {
        await N("/api/bgm/remove", { job_workspace: b() }), t.bgm = null, t.bgmAdvancedOpen = !1, t.notice = a("settings.bgm.removed");
      });
  }, Pr = () => U("render_background_upload", async () => {
    const i = await xe(["Image files (*.jpg;*.jpeg;*.png;*.webp)", "All files (*.*)"]);
    if (i?.cancelled) return;
    if (!i?.ok || !i.path) throw new Error(i?.error || a("settings.render_layout.pick_unavailable"));
    await N("/api/render-settings/save", { job_workspace: b(), render: zt() });
    const c = await N("/api/render-background/upload", { job_workspace: b(), image_path: i.path });
    t.renderLayout = O(c.render), t.notice = a("settings.render_layout.uploaded");
  }), Ne = () => U("render_layout_save", async () => {
    const i = await N("/api/render-settings/save", { job_workspace: b(), render: zt() });
    t.renderLayout = O(i.render), t.notice = a("settings.render_layout.saved");
  }), jr = () => {
    if (!(!O(t.renderLayout).background_path || !window.confirm(a("settings.render_layout.confirm_remove"))))
      return U("render_background_remove", async () => {
        const i = await N("/api/render-background/remove", { job_workspace: b() });
        t.renderLayout = O(i.render), t.notice = a("settings.render_layout.removed");
      });
  };
  function ie(i) {
    t.renderLayout = O({ ...t.renderLayout, ...i });
  }
  const Mr = () => U("render_logo_upload", async () => {
    const i = await xe(["Image files (*.png;*.jpg;*.jpeg;*.webp)", "All files (*.*)"]);
    if (i?.cancelled) return;
    if (!i?.ok || !i.path) throw new Error(i?.error || a("settings.render_layout.pick_unavailable"));
    await N("/api/render-settings/save", { job_workspace: b(), render: zt() });
    const c = await N("/api/render-logo/upload", { job_workspace: b(), image_path: i.path });
    t.renderLayout = O(c.render), t.notice = a("settings.render_layout.logo_uploaded");
  }), Er = () => {
    if (!(!O(t.renderLayout).logo_path || !window.confirm(a("settings.render_layout.logo_confirm_remove"))))
      return U("render_logo_remove", async () => {
        const i = await N("/api/render-logo/remove", { job_workspace: b() });
        t.renderLayout = O(i.render), t.notice = a("settings.render_layout.logo_removed");
      });
  }, va = (i) => U(`render_${i}_upload`, async () => {
    const c = await xe([
      "Video files (*.mp4;*.mov;*.mkv;*.webm;*.m4v)",
      "All files (*.*)"
    ]);
    if (c?.cancelled) return;
    if (!c?.ok || !c.path) throw new Error(c?.error || a("settings.render_layout.pick_unavailable"));
    await N("/api/render-settings/save", { job_workspace: b(), render: zt() });
    const y = await N(`/api/render-${i}/upload`, { job_workspace: b(), clip_path: c.path });
    t.renderLayout = O(y.render), t.notice = a(`settings.render_layout.${i}_uploaded`);
  }), ca = (i) => {
    if (!(!(i === "intro" ? O(t.renderLayout).intro_clip_path : O(t.renderLayout).outro_clip_path) || !window.confirm(a("settings.render_layout.clip_confirm_remove"))))
      return U(`render_${i}_remove`, async () => {
        const y = await N(`/api/render-${i}/remove`, { job_workspace: b() });
        t.renderLayout = O(y.render), t.notice = a(`settings.render_layout.${i}_removed`);
      });
  };
  function ua(i) {
    t.renderLayout = O({ ...t.renderLayout, ...i });
  }
  const Ar = () => U("tts_preview", async () => {
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
  function Se() {
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
  const Fr = () => U("run_until_edit", async () => {
    t.openaiKeyMissing = !1, t.runUntilEditLive = {
      overall_percent: 0,
      current_stage_label: "",
      current_stage: "",
      status_label: "",
      lifecycle: "queued",
      last_error: null
    }, Se();
    try {
      $t = setInterval(Se, 800);
      try {
        const w = await N("/api/save-import-config", { job_workspace: b(), config: kr() });
        d().importConfig = { job_workspace: b(), ...w?.config || {} };
      } catch {
      }
      const i = await N("/api/run-until-edit", {
        job_workspace: b(),
        project_name: wr(),
        use_auto_translate: !0,
        source_language: t.source_language,
        translate_backend: "block_v2",
        enable_source_cleanup: !!t.enable_source_cleanup,
        enable_translation_qa: !!t.enable_translation_qa,
        async: !0,
        subtitle_extractor: "audio_only"
      }), c = await Hn(b(), i);
      d().applyJobStatusToEditGate?.(d(), c), Se();
      const y = c.voice_edit_status || "";
      if (y === "voice_edit_pending") {
        t.voiceEditGateOpen = !0, t.notice = a("settings.notice_run_until_edit", { stage: a(`stage.${y}`) }), t.runUntilEditLive = null;
        return;
      }
      t.voiceEditGateOpen = !1, t.notice = a("settings.notice_run_until_edit", { stage: a(`stage.${y || "voice_edit_pending"}`) }), t.runUntilEditLive = null, d().navigate("review");
    } catch (i) {
      if (i instanceof ye && i.code === "api_key_required") {
        t.openaiKeyMissing = !0, t.runUntilEditLive = null;
        return;
      }
      const c = t.runUntilEditLive?.current_stage_label || t.runUntilEditLive?.current_stage || "", y = i instanceof ye ? i.message || i.code || "" : $e(i), w = i instanceof ye && Array.isArray(i.logTail) && i.logTail.length ? `
— Log:
` + i.logTail.slice(-8).join(`
`) : "";
      Ht(mt, a("settings.run_failed", { stage: c || "—", message: y }) + w), t.runUntilEditLive = null;
      return;
    } finally {
      $t && (clearInterval($t), $t = null), d() && (t.runUntilEditLive = null);
    }
  }), pa = x(() => br(t.voiceCatalog, t.tts_provider)), Rr = x(() => {
    const i = /* @__PURE__ */ new Map();
    for (const c of l(pa))
      !c.locale || i.has(c.locale) || i.set(c.locale, dr(c, S(), a("settings.tts.locale_unknown")));
    return Array.from(i.entries()).sort((c, y) => c[1].localeCompare(y[1]));
  }), ga = x(() => vl(l(pa), t.voiceLocaleFilter, t.voiceGenderFilter)), ma = x(() => !!t.tts_voice && !l(ga).some((i) => i.voice_id === t.tts_voice)), re = x(() => t.voiceCatalog.find((i) => i.provider === t.tts_provider && i.voice_id === t.tts_voice)), Tr = x(() => {
    const i = fr(t.translate_target), c = /* @__PURE__ */ new Map();
    for (const w of [...l(ga)].sort(ke)) {
      const j = w.locale || a("settings.tts.locale_unknown");
      c.has(j) || c.set(j, []), c.get(j).push(w);
    }
    const y = (w, j) => w[0] ? dr(w[0], S(), a("settings.tts.locale_unknown")) : j;
    return Array.from(c.entries()).sort((w, j) => w[0] === i && j[0] !== i ? -1 : j[0] === i && w[0] !== i ? 1 : y(w[1], w[0]).localeCompare(y(j[1], j[0]))).map(([w, j]) => ({ label: y(j, w), items: j }));
  }), Cr = x(() => l(re) ? aa(l(re), S()) : t.tts_voice || a("settings.tts.voice_placeholder")), Br = x(() => t.mix_mode === "duck_original_speech" ? a("settings.tts.mix_duck") : t.mix_mode === "keep_music_replace_voice" ? a("settings.tts.mix_keep_music") : a("settings.tts.mix_replace")), K = x(() => lt(t.bgm)), k = x(() => O(t.renderLayout));
  function Or(i) {
    t.tts_voice = i.target.value, ae();
  }
  function zr(i) {
    t.speed_multiplier = wt(i), t.tts_rate = cr(t.speed_multiplier), ae();
  }
  const Ir = x(() => {
    const i = [];
    t.subtitle_font && !t.fontOptions.some((c) => c.family === t.subtitle_font) && i.push([t.subtitle_font, t.subtitle_font]);
    for (const c of t.fontOptions) i.push([c.family, c.family]);
    return i.length ? i : [[t.subtitle_font || "Arial", t.subtitle_font || "Arial"]];
  });
  Wn(() => {
    b(), Q(), _a();
  });
  var ba = oa(), fa = ut(ba);
  {
    var Vr = (i) => {
      var c = fl(), y = r(e(c)), w = e(y);
      h(() => s(w, l(mt))), m(i, c);
    };
    T(fa, (i) => {
      l(mt) && i(Vr);
    });
  }
  var Ur = r(fa, 2);
  {
    var Dr = (i) => {
      var c = hl(), y = e(c), w = r(e(y), 2), j = e(w), _t = r(w, 2), It = e(_t);
      h(
        (Vt, z) => {
          s(j, Vt), s(It, z);
        },
        [
          () => a("settings.empty_title"),
          () => a("settings.empty_body")
        ]
      ), m(i, c);
    }, Gr = x(() => !b()), qr = (i) => {
      var c = Rl(), y = ut(c), w = e(y);
      {
        var j = (z) => {
          const I = x(() => t.runUntilEditLive), Z = x(() => Math.max(0, Math.min(100, Number(l(I)?.overall_percent) || 0)));
          var et = xl(), G = e(et), R = r(e(G), 2), dt = e(R), M = r(R, 2), q = e(M), at = r(M, 2), V = e(at);
          Qn(V, {
            get percent() {
              return l(Z);
            },
            wide: !0
          });
          var it = r(V, 2), D = e(it), tt = e(D), Nt = r(D), bt = e(Nt), oe = r(at, 2);
          {
            var se = (ft) => {
              var St = yl(), Ut = e(St);
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
          var I = Al(), Z = ut(I);
          {
            var et = (o) => {
              var v = kl(), p = e(v);
              h(() => s(p, t.notice)), m(o, v);
            };
            T(Z, (o) => {
              t.notice && o(et);
            });
          }
          var G = r(Z, 2), R = e(G), dt = e(R), M = e(dt), q = e(M), at = e(q), V = r(q), it = e(V), D = r(M), tt = e(D), Nt = r(dt, 2), bt = e(Nt), oe = e(bt), se = e(oe), ft = e(se), St = r(se), Ut = e(St), ne = r(oe, 2), ha = e(ne), ya = e(ha), Wr = e(ya), Lt = r(ya, 2);
          Xt(Lt, 21, () => l(Ir), Yt, (o, v) => {
            var p = x(() => ea(l(v), 2));
            let u = () => l(p)[0], g = () => l(p)[1];
            var f = ra(), L = e(f), $ = {};
            h(() => {
              sr(f, u() === t.subtitle_font), s(L, g()), $ !== ($ = u()) && (f.value = (f.__value = u()) ?? "");
            }), m(o, f);
          });
          var xa;
          pt(Lt);
          var Kr = r(ha, 2), ka = e(Kr), Jr = e(ka), Hr = r(ka), wa = r(ne, 2), $a = e(wa), Xr = e($a), Yr = r($a, 2), Le = e(Yr), Pe = r(Le, 2), Qr = r(Pe, 2);
          Xt(Qr, 17, () => tl, Yt, (o, v) => {
            var p = x(() => ea(l(v), 2));
            let u = () => l(p)[0], g = () => l(p)[1];
            var f = wl(), L = e(f);
            h(() => {
              Ze(f, 1, `toggle-btn ${t.subtitle_align === u() ? "active" : ""}`), s(L, g());
            }), P("click", f, () => t.subtitle_align = u()), m(o, f);
          });
          var Na = r(wa, 2), Zr = e(Na), to = r(Na, 2), Sa = e(to), eo = e(Sa), La = r(Sa, 2), Pa = e(La), ao = e(Pa), ja = r(bt, 2), Ma = e(ja), Ea = e(Ma), io = e(Ea), ro = r(Ea), oo = e(ro), Aa = r(Ma, 2), Fa = e(Aa), Ra = e(Fa), so = e(Ra), Ta = r(Ra, 2), vt = e(Ta), le = e(vt), no = e(le);
          le.value = le.__value = "";
          var lo = r(le);
          Xt(lo, 17, () => l(Rr), Yt, (o, v) => {
            var p = x(() => ea(l(v), 2));
            let u = () => l(p)[0], g = () => l(p)[1];
            var f = ra(), L = e(f), $ = {};
            h(() => {
              s(L, g()), $ !== ($ = u()) && (f.value = (f.__value = u()) ?? "");
            }), m(o, f);
          });
          var Ca;
          pt(vt);
          var ht = r(vt, 2), _e = e(ht), _o = e(_e);
          _e.value = _e.__value = "";
          var de = r(_e), vo = e(de);
          de.value = de.__value = "female";
          var je = r(de), co = e(je);
          je.value = je.__value = "male";
          var Ba;
          pt(ht);
          var yt = r(Ta, 2), Oa = e(yt);
          {
            var uo = (o) => {
              var v = $l(), p = e(v), u = e(p), g = {};
              h(
                (f, L) => {
                  nt(v, "label", f), s(u, L), g !== (g = t.tts_voice) && (p.value = (p.__value = t.tts_voice) ?? "");
                },
                [
                  () => a("settings.tts.current_voice"),
                  () => l(re) ? aa(l(re), S()) : t.tts_voice
                ]
              ), m(o, v);
            };
            T(Oa, (o) => {
              l(ma) && o(uo);
            });
          }
          var po = r(Oa);
          Xt(po, 17, () => l(Tr), Yt, (o, v) => {
            var p = Nl();
            Xt(p, 21, () => l(v).items, Yt, (u, g) => {
              var f = ra(), L = e(f), $ = {};
              h(
                (B) => {
                  sr(f, l(g).voice_id === t.tts_voice), s(L, B), $ !== ($ = l(g).voice_id) && (f.value = (f.__value = l(g).voice_id) ?? "");
                },
                [() => aa(l(g), S())]
              ), m(u, f);
            }), h(() => nt(p, "label", l(v).label)), m(o, p);
          });
          var za;
          pt(yt);
          var go = r(yt, 2);
          {
            var mo = (o) => {
              var v = Sl(), p = e(v);
              h((u) => s(p, u), [() => a("settings.tts.filter_current_hidden")]), m(o, v);
            };
            T(go, (o) => {
              l(ma) && o(mo);
            });
          }
          var Ia = r(Fa, 2), Va = e(Ia), bo = e(Va), Ua = r(Va, 2), fo = e(Ua), ho = e(fo), Da = r(Ua, 2), yo = r(Ia, 2), Ga = e(yo), xo = e(Ga), Pt = r(Ga, 2), ve = e(Pt), ko = e(ve);
          ve.value = ve.__value = "replace_original_speech";
          var ce = r(ve), wo = e(ce);
          ce.value = ce.__value = "duck_original_speech";
          var Me = r(ce), $o = e(Me);
          Me.value = Me.__value = "keep_music_replace_voice";
          var qa;
          pt(Pt);
          var Wa = r(Aa, 2), Ka = e(Wa), No = e(Ka), So = r(Ka, 2), Ja = e(So), Ha = e(Ja), Lo = e(Ha), Xa = r(Ha, 2), Po = e(Xa), jo = e(Po), Ya = r(Xa, 2), Mo = r(Ja, 2), Qa = e(Mo), Eo = e(Qa), Za = r(Qa, 2), Ao = e(Za), Fo = e(Ao), ti = r(Za, 2), ei = r(Wa, 2), ai = e(ei), Ro = e(ai), Ee = r(ai, 2), ii = r(ei, 2), ri = e(ii), To = e(ri), oi = r(ri, 2), si = e(oi), Co = e(si), ni = r(si, 2), Bo = e(ni), li = r(ni, 2), Oo = e(li), zo = r(li, 2), Io = e(zo), _i = r(oi, 2);
          {
            var Vo = (o) => {
              var v = Ll();
              h((p) => nt(v, "src", p), [() => ee(t.previewAudioRel, t.previewAudioBust)]), m(o, v);
            };
            T(_i, (o) => {
              t.previewAudioRel && o(Vo);
            });
          }
          var Uo = r(_i, 2), Do = e(Uo), Go = r(ii, 2), qo = e(Go);
          {
            let o = x(C);
            A(qo, {
              variant: "strong",
              get disabled() {
                return l(o);
              },
              onclick: Ar,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.tts.test_voice")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var di = r(ja, 2), vi = e(di), ci = e(vi), Wo = e(ci), Ko = r(ci), Jo = e(Ko), ui = r(vi, 2);
          {
            var Ho = (o) => {
              var v = Zt(), p = e(v);
              h((u) => s(p, u), [() => a("settings.bgm.no_bgm")]), m(o, v);
            }, Xo = (o) => {
              var v = Pl(), p = ut(v), u = e(p), g = e(u), f = r(u, 2), L = e(f), $ = r(p, 2), B = r($, 2), W = e(B), J = e(W), Dt = e(J), H = r(J, 2), ct = e(H), Gt = e(ct), rt = r(H, 2), qt = r(W, 2), ot = e(qt), Et = e(ot), xt = e(Et), Wt = r(Et), At = e(Wt), Ft = r(ot, 2), kt = e(Ft);
              h(
                (st, Rt, Tt, Ct, Kt, Bt, Jt) => {
                  s(g, st), s(L, Rt), nt($, "src", Tt), s(Dt, Ct), s(Gt, Kt), Y(rt, l(K).volume_db), s(xt, Bt), s(At, Jt), ta(kt, l(K).loop);
                },
                [
                  () => (l(K).original_filename || l(K).original_path || l(K).normalized_path).split(/[\\/]/).pop(),
                  () => a("settings.bgm.duration", { duration: pl(l(K).duration_ms) }),
                  () => ee(l(K).normalized_path || l(K).original_path, Date.now()),
                  () => a("settings.bgm.volume"),
                  () => ur(l(K).volume_db),
                  () => a("settings.bgm.loop"),
                  () => a("settings.bgm.loop_sub")
                ]
              ), P("input", rt, (st) => t.bgm = lt({ ...t.bgm, volume_db: sa(Number(st.target.value)) })), P("change", kt, (st) => t.bgm = lt({ ...t.bgm, loop: st.target.checked })), m(o, v);
            };
            T(ui, (o) => {
              l(K) ? o(Xo, -1) : o(Ho);
            });
          }
          var Yo = r(ui, 2), pi = e(Yo);
          {
            let o = x(C);
            A(pi, {
              variant: "secondary",
              get disabled() {
                return l(o);
              },
              onclick: Nr,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.bgm.upload")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Qo = r(pi, 2);
          {
            var Zo = (o) => {
              var v = oa(), p = ut(v);
              {
                let g = x(C);
                A(p, {
                  variant: "primary",
                  get disabled() {
                    return l(g);
                  },
                  onclick: Sr,
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
                  onclick: Lr,
                  children: (f, L) => {
                    var $ = E();
                    h((B) => s($, B), [() => a("settings.bgm.remove")]), m(f, $);
                  },
                  $$slots: { default: !0 }
                });
              }
              m(o, v);
            };
            T(Qo, (o) => {
              l(K) && o(Zo);
            });
          }
          var gi = r(di, 2), mi = e(gi), bi = e(mi), ts = e(bi), es = r(bi), as = e(es), fi = r(mi, 2), is = e(fi), hi = e(is), rs = e(hi), jt = r(hi, 2), ue = e(jt), os = e(ue);
          ue.value = ue.__value = "16:9";
          var Ae = r(ue), ss = e(Ae);
          Ae.value = Ae.__value = "9:16";
          var yi;
          pt(jt);
          var xi = r(fi, 2);
          {
            var ns = (o) => {
              var v = jl(), p = ut(v), u = e(p), g = e(u), f = r(u, 2), L = e(f), $ = r(p, 2);
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
            }, ls = (o) => {
              var v = Zt(), p = e(v);
              h((u) => s(p, u), [() => a("settings.render_layout.no_background")]), m(o, v);
            };
            T(xi, (o) => {
              l(k).background_path ? o(ns) : o(ls, -1);
            });
          }
          var ki = r(xi, 2), wi = e(ki);
          {
            let o = x(C);
            A(wi, {
              variant: "secondary",
              get disabled() {
                return l(o);
              },
              onclick: Pr,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.render_layout.upload_background")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var $i = r(wi, 2);
          {
            let o = x(C);
            A($i, {
              variant: "primary",
              get disabled() {
                return l(o);
              },
              onclick: Ne,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.render_layout.save")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var _s = r($i, 2);
          {
            var ds = (o) => {
              {
                let v = x(C);
                A(o, {
                  get disabled() {
                    return l(v);
                  },
                  onclick: jr,
                  children: (p, u) => {
                    var g = E();
                    h((f) => s(g, f), [() => a("settings.render_layout.remove_background")]), m(p, g);
                  },
                  $$slots: { default: !0 }
                });
              }
            };
            T(_s, (o) => {
              l(k).background_path && o(ds);
            });
          }
          var Ni = r(ki, 2), Si = e(Ni), vs = e(Si), cs = r(Si), us = e(cs), Li = r(Ni, 2);
          {
            var ps = (o) => {
              var v = Ml(), p = ut(v), u = e(p), g = e(u), f = r(u, 2), L = e(f), $ = r(p, 2), B = r($, 2), W = e(B), J = e(W), Dt = e(J), H = r(J, 2), ct = e(H), Gt = e(ct);
              ct.value = ct.__value = "top-left";
              var rt = r(ct), qt = e(rt);
              rt.value = rt.__value = "top-right";
              var ot = r(rt), Et = e(ot);
              ot.value = ot.__value = "bottom-left";
              var xt = r(ot), Wt = e(xt);
              xt.value = xt.__value = "bottom-right";
              var At;
              pt(H);
              var Ft = r(W, 2), kt = e(Ft), st = e(kt), Rt = r(kt, 2), Tt = r(Ft, 2), Ct = e(Tt), Kt = e(Ct), Bt = r(Ct, 2), Jt = r(Tt, 2), fe = e(Jt), Ce = e(fe), he = r(fe, 2);
              h(
                (X, Be, Oe, ze, Ie, Ve, Ue, De, Ge, qe, We, Ke, Je, He, Xe, Ye, Qe) => {
                  s(g, X), s(L, Be), nt($, "src", Oe), s(Dt, ze), s(Gt, Ie), s(qt, Ve), s(Et, Ue), s(Wt, De), At !== (At = l(k).logo_position) && (H.value = (H.__value = l(k).logo_position) ?? "", gt(H, l(k).logo_position)), s(st, `${Ge ?? ""} (${qe ?? ""}%)`), Y(Rt, We), s(Kt, `${Ke ?? ""} (${Je ?? ""}%)`), Y(Bt, He), s(Ce, `${Xe ?? ""} (${Ye ?? ""}%)`), Y(he, Qe);
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
              ), P("change", H, (X) => ie({ logo_position: X.target.value })), P("input", Rt, (X) => ie({ logo_scale: Number(X.target.value) / 100 })), P("input", Bt, (X) => ie({ logo_opacity: Number(X.target.value) / 100 })), P("input", he, (X) => ie({ logo_margin: Number(X.target.value) / 100 })), m(o, v);
            }, gs = (o) => {
              var v = Zt(), p = e(v);
              h((u) => s(p, u), [() => a("settings.render_layout.no_logo")]), m(o, v);
            };
            T(Li, (o) => {
              l(k).logo_path ? o(ps) : o(gs, -1);
            });
          }
          var Pi = r(Li, 2), ji = e(Pi);
          {
            let o = x(C);
            A(ji, {
              variant: "secondary",
              get disabled() {
                return l(o);
              },
              onclick: Mr,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.render_layout.upload_logo")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var ms = r(ji, 2);
          {
            var bs = (o) => {
              var v = oa(), p = ut(v);
              {
                let g = x(C);
                A(p, {
                  variant: "primary",
                  get disabled() {
                    return l(g);
                  },
                  onclick: Ne,
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
                  onclick: Er,
                  children: (f, L) => {
                    var $ = E();
                    h((B) => s($, B), [() => a("settings.render_layout.remove_logo")]), m(f, $);
                  },
                  $$slots: { default: !0 }
                });
              }
              m(o, v);
            };
            T(ms, (o) => {
              l(k).logo_path && o(bs);
            });
          }
          var Mi = r(Pi, 2), Ei = e(Mi), fs = e(Ei), hs = r(Ei), ys = e(hs), Ai = r(Mi, 2), Fi = e(Ai), Ri = e(Fi), xs = e(Ri), Fe = r(Ri, 2), ks = r(Fe, 2), ws = e(ks), $s = r(Fi, 2), Ti = e($s), Ns = e(Ti), Re = r(Ti, 2), Ss = r(Re, 2), Ls = e(Ss), Ci = r(Ai, 2), Bi = e(Ci), Oi = e(Bi), Ps = e(Oi), zi = r(Oi, 2);
          {
            var js = (o) => {
              var v = mr(), p = e(v);
              h((u) => s(p, u), [
                () => (l(k).intro_original_filename || l(k).intro_clip_path).split(/[\\/]/).pop()
              ]), m(o, v);
            }, Ms = (o) => {
              var v = Zt(), p = e(v);
              h((u) => s(p, u), [() => a("settings.render_layout.no_clip")]), m(o, v);
            };
            T(zi, (o) => {
              l(k).intro_clip_path ? o(js) : o(Ms, -1);
            });
          }
          var Es = r(zi, 2), Ii = e(Es);
          {
            let o = x(C);
            A(Ii, {
              variant: "secondary",
              get disabled() {
                return l(o);
              },
              onclick: () => va("intro"),
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.render_layout.upload_intro")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var As = r(Ii, 2);
          {
            var Fs = (o) => {
              {
                let v = x(C);
                A(o, {
                  get disabled() {
                    return l(v);
                  },
                  onclick: () => ca("intro"),
                  children: (p, u) => {
                    var g = E();
                    h((f) => s(g, f), [() => a("settings.render_layout.remove_clip")]), m(p, g);
                  },
                  $$slots: { default: !0 }
                });
              }
            };
            T(As, (o) => {
              l(k).intro_clip_path && o(Fs);
            });
          }
          var Rs = r(Bi, 2), Vi = e(Rs), Ts = e(Vi), Ui = r(Vi, 2);
          {
            var Cs = (o) => {
              var v = mr(), p = e(v);
              h((u) => s(p, u), [
                () => (l(k).outro_original_filename || l(k).outro_clip_path).split(/[\\/]/).pop()
              ]), m(o, v);
            }, Bs = (o) => {
              var v = Zt(), p = e(v);
              h((u) => s(p, u), [() => a("settings.render_layout.no_clip")]), m(o, v);
            };
            T(Ui, (o) => {
              l(k).outro_clip_path ? o(Cs) : o(Bs, -1);
            });
          }
          var Os = r(Ui, 2), Di = e(Os);
          {
            let o = x(C);
            A(Di, {
              variant: "secondary",
              get disabled() {
                return l(o);
              },
              onclick: () => va("outro"),
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.render_layout.upload_outro")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var zs = r(Di, 2);
          {
            var Is = (o) => {
              {
                let v = x(C);
                A(o, {
                  get disabled() {
                    return l(v);
                  },
                  onclick: () => ca("outro"),
                  children: (p, u) => {
                    var g = E();
                    h((f) => s(g, f), [() => a("settings.render_layout.remove_clip")]), m(p, g);
                  },
                  $$slots: { default: !0 }
                });
              }
            };
            T(zs, (o) => {
              l(k).outro_clip_path && o(Is);
            });
          }
          var Vs = r(Ci, 2), Us = e(Vs);
          {
            let o = x(C);
            A(Us, {
              variant: "primary",
              get disabled() {
                return l(o);
              },
              onclick: Ne,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.render_layout.save")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Ds = r(gi, 2), Gi = e(Ds);
          {
            let o = x(C);
            A(Gi, {
              variant: "secondary",
              get disabled() {
                return l(o);
              },
              onclick: () => _a(!0),
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.reload")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Gs = r(Gi, 2);
          {
            let o = x(C);
            A(Gs, {
              "data-testid": "save-text-audio",
              variant: "primary",
              get disabled() {
                return l(o);
              },
              onclick: $r,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.text_audio.save")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          var qs = r(R, 2), qi = e(qs), Ws = e(qi), Wi = e(Ws), Ks = e(Wi), Js = r(Wi), Hs = e(Js), Xs = r(qi, 2), Ki = e(Xs), Ys = e(Ki), Ji = e(Ys), Qs = e(Ji), Mt = r(Ji, 2), pe = e(Mt), Zs = e(pe);
          pe.value = pe.__value = "auto";
          var ge = r(pe), tn = e(ge);
          ge.value = ge.__value = "zh";
          var me = r(ge), en = e(me);
          me.value = me.__value = "en";
          var be = r(me), an = e(be);
          be.value = be.__value = "ja";
          var Te = r(be), rn = e(Te);
          Te.value = Te.__value = "ko";
          var Hi;
          pt(Mt);
          var Xi = r(Ki, 2);
          {
            var on = (o) => {
              var v = El(), p = e(v), u = e(p), g = r(p, 2), f = e(g);
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
            T(Xi, (o) => {
              t.openaiKeyMissing && o(on);
            });
          }
          var Yi = r(Xi, 2), Qi = e(Yi), sn = e(Qi), nn = r(Qi, 2), Zi = e(nn), tr = e(Zi), er = e(tr), ln = e(er), _n = r(er), dn = e(_n), vn = r(tr, 2), ar = e(vn), cn = r(Zi, 2), ir = e(cn), rr = e(ir), un = e(rr), pn = r(rr), gn = e(pn), mn = r(ir, 2), or = e(mn), bn = r(Yi, 2), fn = e(bn);
          {
            let o = x(C);
            A(fn, {
              "data-testid": "run-until-edit",
              variant: "strong",
              get disabled() {
                return l(o);
              },
              onclick: Fr,
              children: (v, p) => {
                var u = E();
                h((g) => s(u, g), [() => a("settings.translation.run_until_edit_auto")]), m(v, u);
              },
              $$slots: { default: !0 }
            });
          }
          h(
            (o, v, p, u, g, f, L, $, B, W, J, Dt, H, ct, Gt, rt, qt, ot, Et, xt, Wt, At, Ft, kt, st, Rt, Tt, Ct, Kt, Bt, Jt, fe, Ce, he, X, Be, Oe, ze, Ie, Ve, Ue, De, Ge, qe, We, Ke, Je, He, Xe, Ye, Qe, hn, yn, xn, kn, wn, $n, Nn, Sn, Ln, Pn, jn, Mn, En, An, Fn, Rn, Tn, Cn, Bn, On, zn, In, Vn, Un) => {
              s(at, o), s(it, v), s(tt, p), s(ft, u), s(Ut, g), s(Wr, f), xa !== (xa = t.subtitle_font) && (Lt.value = (Lt.__value = t.subtitle_font) ?? "", gt(Lt, t.subtitle_font)), s(Jr, L), Y(Hr, $), s(Xr, B), Ze(Le, 1, `toggle-btn ${t.subtitle_bold ? "active" : ""}`), Ze(Pe, 1, `toggle-btn ${t.subtitle_italic ? "active" : ""}`), s(Zr, W), s(eo, J), nr(La, Dt), nr(Pa, H), s(ao, ct), s(io, Gt), s(oo, rt), s(so, qt), nt(vt, "aria-label", ot), s(no, `${Et ?? ""}: ${xt ?? ""}`), Ca !== (Ca = t.voiceLocaleFilter) && (vt.value = (vt.__value = t.voiceLocaleFilter) ?? "", gt(vt, t.voiceLocaleFilter)), nt(ht, "aria-label", Wt), s(_o, `${At ?? ""}: ${Ft ?? ""}`), s(vo, kt), s(co, st), Ba !== (Ba = t.voiceGenderFilter) && (ht.value = (ht.__value = t.voiceGenderFilter) ?? "", gt(ht, t.voiceGenderFilter)), za !== (za = t.tts_voice) && (yt.value = (yt.__value = t.tts_voice) ?? "", gt(yt, t.tts_voice)), s(bo, Rt), s(ho, Tt), Y(Da, t.speed_multiplier), s(xo, Ct), s(ko, Kt), s(wo, Bt), s($o, Jt), qa !== (qa = t.mix_mode) && (Pt.value = (Pt.__value = t.mix_mode) ?? "", gt(Pt, t.mix_mode)), s(No, fe), s(Lo, Ce), s(jo, he), Y(Ya, t.tts_pitch), s(Eo, X), s(Fo, Be), Y(ti, t.mix_duck_gain_db), s(Ro, Oe), nt(Ee, "placeholder", Qt), Y(Ee, t.previewText), s(To, ze), s(Co, `${Ie ?? ""}: ${l(Cr) ?? ""}`), s(Bo, `${Ve ?? ""}: ${Ue ?? ""}`), s(Oo, `${De ?? ""}: ${Ge ?? ""}`), s(Io, `${qe ?? ""}: ${l(Br) ?? ""}`), s(Do, We), s(Wo, Ke), s(Jo, Je), s(ts, He), s(as, Xe), s(rs, Ye), s(os, Qe), s(ss, hn), yi !== (yi = l(k).aspect_ratio) && (jt.value = (jt.__value = l(k).aspect_ratio) ?? "", gt(jt, l(k).aspect_ratio)), s(vs, yn), s(us, xn), s(fs, kn), s(ys, wn), s(xs, `${$n ?? ""} (${l(k).head_trim_sec ?? ""}s)`), Y(Fe, l(k).head_trim_sec), s(ws, Nn), s(Ns, `${Sn ?? ""} (${l(k).tail_trim_sec ?? ""}s)`), Y(Re, l(k).tail_trim_sec), s(Ls, Ln), s(Ps, Pn), s(Ts, jn), s(Ks, Mn), s(Hs, En), s(Qs, An), s(Zs, Fn), s(tn, Rn), s(en, Tn), s(an, Cn), s(rn, Bn), Hi !== (Hi = t.source_language) && (Mt.value = (Mt.__value = t.source_language) ?? "", gt(Mt, t.source_language)), s(sn, On), s(ln, zn), s(dn, In), ta(ar, t.enable_source_cleanup), s(un, Vn), s(gn, Un), ta(or, t.enable_translation_qa);
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
              () => `flex:1;display:grid;align-items:end;background:var(--bg-0);border-radius:14px;padding:28px;text-align:${gl(t.subtitle_align)}`,
              () => `font-family:${ml(t.subtitle_font)};background:${t.bg_enabled ? bl(t.subtitle_background_color) : "transparent"};font-weight:${t.subtitle_bold ? 800 : 500};font-style:${t.subtitle_italic ? "italic" : "normal"}`,
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
              () => gr(t.speed_multiplier),
              () => a("settings.tts.mix_mode"),
              () => a("settings.tts.mix_replace"),
              () => a("settings.tts.mix_duck"),
              () => a("settings.tts.mix_keep_music"),
              () => a("settings.tts.advanced"),
              () => a("settings.tts.pitch"),
              () => pr(t.tts_pitch),
              () => a("settings.tts.duck_gain"),
              () => ur(t.mix_duck_gain_db),
              () => a("settings.tts.preview_text_label"),
              () => a("settings.tts.preview_title"),
              () => a("settings.tts.voice"),
              () => a("settings.tts.speed"),
              () => gr(t.speed_multiplier),
              () => a("settings.tts.pitch"),
              () => pr(t.tts_pitch),
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
          ), P("change", Lt, (o) => t.subtitle_font = o.target.value), P("click", Le, () => t.subtitle_bold = !t.subtitle_bold), P("click", Pe, () => t.subtitle_italic = !t.subtitle_italic), P("change", vt, (o) => t.voiceLocaleFilter = o.target.value), P("change", ht, (o) => t.voiceGenderFilter = o.target.value), P("change", yt, Or), P("input", Da, (o) => zr(Number(o.target.value))), P("change", Pt, (o) => t.mix_mode = o.target.value), P("input", Ya, (o) => {
            t.tts_pitch = Number(o.target.value), ae();
          }), P("input", ti, (o) => t.mix_duck_gain_db = ia(Number(o.target.value))), P("input", Ee, (o) => {
            t.previewText = o.target.value, Ot(t.previewText), ae();
          }), P("change", jt, (o) => t.renderLayout = O({ ...t.renderLayout, aspect_ratio: o.target.value })), P("change", Fe, (o) => ua({ head_trim_sec: Number(o.target.value) })), P("change", Re, (o) => ua({ tail_trim_sec: Number(o.target.value) })), P("change", Mt, (o) => t.source_language = o.target.value), P("change", ar, (o) => t.enable_source_cleanup = o.target.checked), P("change", or, (o) => t.enable_translation_qa = o.target.checked), m(z, I);
        };
        T(w, (z) => {
          t.busyAction === "run_until_edit" ? z(j) : z(_t, -1);
        });
      }
      var It = r(y, 2);
      {
        var Vt = (z) => {
          var I = Fl(), Z = e(I), et = e(Z), G = e(et), R = r(et, 2), dt = e(R), M = r(R, 2), q = e(M);
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
    T(Ur, (i) => {
      l(Gr) ? i(Dr) : i(qr, -1);
    });
  }
  m(_, ba), Kn();
}
Dn(["change", "click", "input"]);
const hr = Zn(Tl), Ul = hr.mount, Dl = hr.unmount;
export {
  Ul as mount,
  Dl as unmount
};
//# sourceMappingURL=settings.js.map
