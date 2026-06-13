import { d as zs, p as Is, w as Vs, x as Us, f as ut, i as R, g as v, l as r, a as f, b as Ds, s as Gs, e as Jt, c as N, A as fe, h as e, t as y, j as o, u as w, n as A, a3 as zi, Q as gt, q as Ke, m as j, r as st, o as T, R as pt, K as nt, P as Ii, z as Je, v as He, X as Xe, V as qs } from "./chunks/api-vHpIWCot.js";
import { o as Ws } from "./chunks/index-client-CjB8cgHo.js";
import { e as Ht, i as Xt } from "./chunks/each-BE197-93.js";
import { p as Ks, B as C } from "./chunks/Button-GpBM5g0S.js";
import { P as Js } from "./chunks/ProgressBar-BACn-l7Z.js";
import { s as Hs } from "./chunks/screen-DRq5NjFu.js";
const Xs = [
  ["left", "L"],
  ["center", "C"],
  ["right", "R"]
], Vi = "vlt.voicePreviewText", Yt = "Xin chào, đây là giọng đọc thử nghiệm.", Ys = {
  "vi-VN": "vi-VN-HoaiMyNeural",
  "en-US": "en-US-JennyNeural",
  "en-GB": "en-GB-SoniaNeural",
  "zh-CN": "zh-CN-XiaoxiaoNeural",
  "ja-JP": "ja-JP-NanamiNeural",
  "ko-KR": "ko-KR-SunHiNeural"
}, Qs = {
  bottom_band: { x: 0, y: 0.78, w: 1, h: 0.22 }
}, Zs = ["top-left", "top-right", "bottom-left", "bottom-right"];
function tn(l) {
  const n = Number(l);
  return Number.isFinite(n) ? Math.min(1, Math.max(0.02, n)) : 0.15;
}
function en(l) {
  const n = Number(l);
  return Number.isFinite(n) ? Math.min(1, Math.max(0, n)) : 1;
}
function an(l) {
  const n = Number(l);
  return Number.isFinite(n) ? Math.min(0.5, Math.max(0, n)) : 0.03;
}
function rn(l) {
  const n = /* @__PURE__ */ new Set(), _ = [];
  for (const a of Array.isArray(l) ? l : []) {
    if (!a || typeof a.family != "string" || !a.family.trim()) continue;
    const $ = a.family.trim(), m = $.toLowerCase();
    n.has(m) || (n.add(m), _.push({ family: $, file: String(a.file || "") }));
  }
  return _.sort((a, $) => a.family.localeCompare($.family));
}
function on(l) {
  const n = [];
  for (const _ of Array.isArray(l) ? l : []) {
    if (!_ || typeof _.voice_id != "string" || !_.voice_id.trim()) continue;
    const a = Array.isArray(_.style_tags) ? _.style_tags.map(($) => String($ || "").trim()).filter(Boolean) : [];
    n.push({
      provider: String(_.provider || "edge_tts"),
      voice_id: _.voice_id.trim(),
      label: String(_.label || _.voice_id).trim(),
      locale: String(_.locale || "").trim(),
      locale_label: String(_.locale_label || "").trim(),
      locale_label_en: String(_.locale_label_en || "").trim(),
      gender: String(_.gender || "").trim().toLowerCase(),
      gender_label: String(_.gender_label || "").trim(),
      gender_label_en: String(_.gender_label_en || "").trim(),
      short_name: String(_.short_name || "").trim(),
      style_tags: a,
      enabled: _.enabled !== !1
    });
  }
  return n;
}
function Ji(l, n) {
  const _ = l.filter((a) => a.provider === n && a.enabled !== !1);
  return _.length ? _ : l.filter((a) => a.provider === n);
}
function ia(l) {
  const n = String(l || "").trim();
  if (!n) return "vi";
  const _ = n.toLowerCase();
  return _.startsWith("english") ? "en" : _.startsWith("vietnam") ? "vi" : _.startsWith("chinese") ? "zh" : _.startsWith("japanese") ? "ja" : _.startsWith("korean") ? "ko" : _.split(/[-_\s]/, 1)[0] || "vi";
}
function Hi(l) {
  const n = ia(l);
  return n === "en" ? "en-US" : n === "zh" ? "zh-CN" : n === "ja" ? "ja-JP" : n === "ko" ? "ko-KR" : n === "vi" ? "vi-VN" : n.includes("-") ? n : "";
}
function sn(l, n) {
  const _ = ia(n);
  return !!l && !!_ && l.toLowerCase().startsWith(`${_}-`);
}
function ye(l, n) {
  const _ = { female: 0, male: 1 }, a = _[l.gender] ?? 9, $ = _[n.gender] ?? 9;
  return a !== $ ? a - $ : (l.short_name || l.label || l.voice_id).localeCompare(n.short_name || n.label || n.voice_id);
}
function nn(l, n, _, a = "vi") {
  const $ = Ji(l, n);
  if ($.some((t) => t.voice_id === _)) return _;
  const m = Hi(a), Y = Ys[m], Qt = Y ? $.find((t) => t.voice_id === Y && t.enabled !== !1) : null;
  if (Qt) return Qt.voice_id;
  const Ot = $.filter((t) => t.locale === m || sn(t.locale, a)).sort(ye)[0];
  return Ot ? Ot.voice_id : $.filter((t) => t.gender === "female").sort(ye)[0]?.voice_id || [...$].sort(ye)[0]?.voice_id || _ || "vi-VN-HoaiMyNeural";
}
function ln(l, n, _) {
  return l.filter((a) => !(n && a.locale !== n || _ && a.gender !== _));
}
function Ui(l, n, _) {
  return n === "vi" ? l.locale_label || l.locale_label_en || l.locale || _ : l.locale_label_en || l.locale_label || l.locale || _;
}
function _n(l, n) {
  return n === "vi" ? l.gender_label || l.gender_label_en || l.gender || "" : l.gender_label_en || l.gender_label || l.gender || "";
}
function Ye(l, n) {
  const _ = l.short_name || l.label || l.voice_id, a = _n(l, n), $ = l.style_tags.length ? l.style_tags[0] : "", m = [a, $].filter(Boolean).join(", ");
  return m ? `${_} - ${m}` : _;
}
function Di(l) {
  if (!l || typeof l != "object") return null;
  const n = l, _ = {};
  for (const a of ["x", "y", "w", "h"]) {
    const $ = Number(n[a]);
    if (!Number.isFinite($) || $ < 0 || $ > 1) return null;
    _[a] = $;
  }
  return _.w <= 0 || _.h <= 0 || _.x + _.w > 1.0001 || _.y + _.h > 1.0001 ? null : _;
}
function wt(l) {
  const n = Number(l);
  return Number.isFinite(n) ? Math.max(0.5, Math.min(2, Math.round(n * 20) / 20)) : 1;
}
function Gi(l) {
  return Math.max(-50, Math.min(50, Math.round((wt(l) - 1) * 100)));
}
function vn(l) {
  const n = Number(l);
  return Number.isFinite(n) ? wt(1 + n / 100) : 1;
}
function Qe(l) {
  const n = Number(l);
  return Number.isFinite(n) ? Math.max(-30, Math.min(0, Math.round(n * 100) / 100)) : -15;
}
function aa(l) {
  const n = Number(l);
  return Number.isFinite(n) ? Math.max(-40, Math.min(0, Math.round(n * 100) / 100)) : -20;
}
function he(l) {
  const n = Number(l);
  return Number.isFinite(n) ? Math.max(0, Math.min(1e4, Math.round(n))) : 0;
}
function lt(l) {
  if (!l || typeof l != "object") return null;
  const n = l, _ = String(n.normalized_path || "").trim(), a = String(n.original_path || "").trim();
  return !_ && !a ? null : {
    original_path: a,
    normalized_path: _,
    original_filename: String(n.original_filename || "").trim(),
    duration_ms: Math.max(0, Math.round(Number(n.duration_ms) || 0)),
    volume_db: aa(n.volume_db),
    loop: n.loop !== !1,
    fade_in_ms: he(n.fade_in_ms ?? 500),
    fade_out_ms: he(n.fade_out_ms ?? 1e3)
  };
}
function U(l) {
  const n = l && typeof l == "object" ? l : {}, _ = String(n.aspect_ratio || "16:9").trim(), a = String(n.logo_position || "top-right").trim();
  return {
    aspect_ratio: _ === "9:16" ? "9:16" : "16:9",
    background_path: String(n.background_path || "").trim(),
    background_original_filename: String(n.background_original_filename || "").trim(),
    logo_path: String(n.logo_path || "").trim(),
    logo_original_filename: String(n.logo_original_filename || "").trim(),
    logo_position: Zs.includes(a) ? a : "top-right",
    logo_scale: tn(n.logo_scale ?? 0.15),
    logo_opacity: en(n.logo_opacity ?? 1),
    logo_margin: an(n.logo_margin ?? 0.03)
  };
}
function qi(l) {
  const n = Number(l), _ = Number.isFinite(n) ? Math.round(n * 10) / 10 : 0;
  return `${_ > 0 ? "+" : ""}${_} dB`;
}
function Wi(l) {
  const n = Number(l) || 0;
  return `${n > 0 ? "+" : ""}${n}%`;
}
function Ki(l) {
  return `${wt(l).toFixed(2).replace(/0$/, "").replace(/\.$/, "")}x`;
}
function dn(l) {
  const n = Math.max(0, Math.round((Number(l) || 0) / 1e3)), _ = Math.floor(n / 60), a = String(n % 60).padStart(2, "0");
  return `${_}:${a}`;
}
function cn(l) {
  return l === "left" ? "left" : l === "right" ? "right" : "center";
}
function un(l) {
  const n = String(l || "").trim();
  return n ? `"${n}", "Segoe UI", sans-serif` : '"Segoe UI", sans-serif';
}
function gn(l) {
  const n = String(l || "").trim();
  return /^#(?:[0-9a-f]{6}|[0-9a-f]{8})$/i.test(n) ? n.toUpperCase() : "#000000";
}
var pn = A('<div class="error-banner"><div class="error-code">UI</div><div class="error-message"> </div></div>'), mn = A('<div class="card" data-testid="settings-empty"><div class="empty-card"><div class="empty-icon">⚙</div> <h3> </h3> <p> </p></div></div>'), bn = A('<div class="small-muted run-until-edit-progress-error"> </div>'), fn = A('<div class="card work-card"><div class="work"><div class="orb"><div class="ring"></div><div class="ring r2"></div><div class="core"></div></div> <h2 class="work-title"> <span class="work-dots"></span></h2> <p class="work-sub"> </p> <div class="work-bar"><!> <div class="work-bar-foot"><span> </span><span> </span></div></div> <!></div></div>'), yn = A('<div class="info-banner"> </div>'), Ze = A("<option> </option>"), hn = A('<button type="button"> </button>'), xn = A('<optgroup><option selected=""> </option></optgroup>'), kn = A("<optgroup></optgroup>"), wn = A('<div class="small-muted voice-filter-warning"> </div>'), $n = A('<audio class="audio-preview" controls="" preload="metadata"></audio>'), ta = A('<div class="meta-empty"> </div>'), Nn = A('<div class="bgm-summary"><div class="row-title"> </div> <div class="small-muted"> </div></div> <audio class="audio-preview" controls="" preload="metadata"></audio> <div class="field-grid"><div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>-40 ... 0 dB</span></div> <input class="range-input" type="range" min="-40" max="0" step="1"/></div> <div class="switch-row"><div><div style="font-weight:700"> </div><div class="small-muted"> </div></div> <label class="checkbox-row"><input type="checkbox"/></label></div></div>', 1), ea = A("<!> <!>", 1), Sn = A('<div class="bgm-summary"><div class="row-title"> </div> <div class="small-muted"> </div></div> <img class="render-background-preview" alt=""/>', 1), Ln = A('<div class="bgm-summary"><div class="row-title"> </div> <div class="small-muted"> </div></div> <img class="render-logo-preview" alt=""/> <div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option><option> </option></select></div> <div class="field"><label> </label> <input class="input" type="range" min="2" max="60" step="1"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0" max="100" step="1"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0" max="20" step="1"/></div></div>', 1), Pn = A('<div class="section-block stack inline-action-banner" data-testid="api-key-missing" style="gap:10px"><div class="small-muted"> </div> <div class="toolbar"><!></div></div>'), jn = A('<!> <div class="stack"><div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div><div class="tag"> </div></div> <div class="card-body stack"><div class="section-block stack"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field"><label> </label> <select class="input"></select></div> <div class="field"><label> </label><input class="input" type="text" readonly=""/></div></div> <div class="stack" style="gap:10px"><div class="small-muted"> </div> <div class="toggle-bar"><button type="button" data-testid="style-bold">B</button> <button type="button" data-testid="style-italic">I</button> <!></div></div> <div class="small-muted"> </div> <div class="preview-tile"><div class="card-title"> </div> <div><span class="subtitle-sample"> </span></div></div></div> <div class="section-block stack"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field voice-picker"><label> </label> <div class="voice-filter-row"><select class="input voice-filter-select"><option> </option><!></select> <select class="input voice-filter-select"><option> </option><option> </option><option> </option></select></div> <select class="input"><!><!></select> <!></div> <div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>0.5x ... 2x</span></div> <input class="range-input" type="range" min="0.5" max="2" step="0.05"/></div> <div class="field"><label> </label> <select class="input"><option> </option><option> </option></select></div></div> <details class="advanced-details"><summary> </summary> <div class="field-grid advanced-grid"><div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>-50 ... +50</span></div> <input class="range-input" type="range" min="-50" max="50" step="1"/></div> <div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>-30 ... 0 dB</span></div> <input class="range-input" type="range" min="-30" max="0" step="1"/></div></div></details> <div class="field voice-preview-text-field"><label> </label> <input class="input" type="text"/></div> <div class="preview-tile"><div class="card-title"> </div> <div class="small-muted"><div> </div> <div> </div> <div> </div> <div> </div></div> <!> <div class="small-muted"> </div></div> <div class="toolbar"><!></div></div> <div class="section-block stack bgm-section"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <!> <div class="toolbar"><!> <!></div></div> <div class="section-block stack render-layout-section"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option></select></div></div> <!> <div class="toolbar"><!> <!> <!></div> <div class="stack" style="gap:6px;margin-top:10px"><div class="card-title"> </div><div class="card-sub"> </div></div> <!> <div class="toolbar"><!> <!></div></div> <div class="toolbar"><!> <!></div></div></div> <div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option><option> </option><option> </option></select></div></div> <!> <details class="advanced-details"><summary> </summary> <div class="section-block"><div class="switch-row"><div><div style="font-weight:700"> </div><div class="small-muted"> </div></div> <label class="checkbox-row"><input type="checkbox"/></label></div> <div class="switch-row"><div><div style="font-weight:700"> </div><div class="small-muted"> </div></div> <label class="checkbox-row"><input type="checkbox"/></label></div></div></details> <div class="toolbar"><!></div></div></div></div>', 1), Mn = A('<div class="voice-edit-gate-backdrop" role="dialog" aria-modal="true"><div class="voice-edit-gate-card stack"><h3 class="voice-edit-gate-title"> </h3> <p class="voice-edit-gate-body"> </p> <div class="voice-edit-gate-actions"><!> <!></div></div></div>'), En = A('<div class="screen stack" data-testid="settings-screen"><!></div> <!>', 1);
function An(l, n) {
  Is(n, !0);
  let _ = Ks(n, "ctx", 7);
  const a = (i, d) => (_()?.t ?? ((h) => h))(i, d), $ = () => _()?.getLang?.() ?? "vi", m = () => String(_()?.jobWorkspace || ""), Y = () => String(_()?.parentProjectRoot || "");
  function Qt() {
    try {
      const i = window.localStorage.getItem(Vi);
      return i && i.trim() ? i : Yt;
    } catch {
      return Yt;
    }
  }
  function Ot(i) {
    try {
      window.localStorage.setItem(Vi, i || Yt);
    } catch {
    }
  }
  function ra() {
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
        logo_margin: 0.03
      },
      previewAudioRel: "",
      previewAudioBust: 0,
      previewText: Qt(),
      voiceEditGateOpen: !1,
      openaiKeyMissing: !1,
      runUntilEditLive: null
    };
  }
  let t = Vs(_()?.settingsState || ra());
  _() && (_().settingsState = t);
  let mt = Gs(""), $t = null;
  Ws(() => {
    $t && clearInterval($t);
  });
  const B = () => !!t.loading || !!t.busyAction;
  function Zt(i, d) {
    if (!m()) return "";
    const h = new URLSearchParams({ workspace: m(), rel: i });
    return d && h.set("v", String(d)), `/media?${h.toString()}`;
  }
  function te() {
    t.previewAudioRel = "", t.previewAudioBust = 0;
  }
  async function oa(i = !1) {
    if (!m() || !i && t.loadedJobWorkspace === m() && t.loadedProjectRoot === Y()) return;
    t.loading = !0, t.notice = "", Jt(mt, "");
    const d = !i && t.fontOptions.length ? Promise.resolve({ fonts: t.fontOptions }) : N("/api/list-system-fonts"), h = !i && t.voiceCatalog.length ? Promise.resolve({ voices: t.voiceCatalog }) : N("/api/list-voices");
    try {
      const [
        x,
        P,
        _t,
        zt,
        It,
        O,
        z,
        Q,
        tt
      ] = await Promise.all([
        N("/api/get-video-style", { job_workspace: m() }),
        N("/api/get-video-tts", { job_workspace: m() }),
        Y() ? N("/api/get-project-style", { project_root: Y() }) : Promise.resolve({ style: {} }),
        Y() ? N("/api/get-project-tts", { project_root: Y() }) : Promise.resolve({ settings: {} }),
        N("/api/get-import-config", { job_workspace: m() }),
        d,
        h,
        N("/api/bgm/status", { job_workspace: m() }),
        N("/api/render-settings/status", { job_workspace: m() })
      ]), D = { ..._t.style || {}, ...x.style || {} }, E = { ...zt.settings || {}, ...P.settings || {} }, vt = _()?.importConfig && _().importConfig.job_workspace === m() ? _().importConfig : null, M = { ...It.config || {}, ...vt || {} }, G = String(M?.subtitle_extractor || "audio_only").toLowerCase();
      let et = !1, I = G;
      G === "ocr_only" || G === "hybrid" ? (et = !0, I = "audio_only") : G !== "external_srt" && (I = "audio_only");
      const at = rn(O.fonts || []), V = on(z.voices || []), Z = M?.tts_provider || E.tts_provider || "edge_tts", Nt = Number.isFinite(Number(E.tts_rate)) ? Number(E.tts_rate) : 0, bt = ia(M?.translate_target || M?.target_language || M?.target_locale || "vi");
      Object.assign(t, {
        loadedJobWorkspace: m(),
        loadedProjectRoot: Y(),
        loading: !1,
        fontOptions: at,
        voiceCatalog: V,
        subtitle_font: D.subtitle_font || "",
        subtitle_background_color: D.subtitle_background_color || "#000000",
        bg_enabled: !!D.subtitle_background_color,
        subtitle_bold: !!D.bold,
        subtitle_italic: !!D.italic,
        subtitle_align: D.align || "center",
        use_auto_translate: M?.use_auto_translate ?? !0,
        source_language: M?.source_language || "auto",
        translate_target: bt,
        translate_backend: M?.translate_backend || "block_v2",
        subtitle_extractor: I,
        external_srt_path: String(M?.external_srt_path || "").trim(),
        legacy_deprecated_extractor: et,
        ocr_provider: M?.ocr_provider || "paddleocr",
        ocr_language: M?.ocr_language || "ch",
        ocr_device: M?.ocr_device || "auto",
        ocr_roi: Di(M?.ocr_roi) || { x: 0, y: 0.78, w: 1, h: 0.22 },
        tts_provider: Z,
        tts_voice: nn(V, Z, E.tts_voice || "", bt),
        speed_multiplier: Number.isFinite(Number(E.speed_multiplier)) ? wt(Number(E.speed_multiplier)) : vn(Nt),
        tts_rate: Nt,
        tts_pitch: Number.isFinite(Number(E.tts_pitch)) ? Number(E.tts_pitch) : 0,
        mix_mode: E.mix_mode || "replace_original_speech",
        mix_duck_gain_db: Number.isFinite(Number(E.mix_duck_gain_db)) ? Qe(Number(E.mix_duck_gain_db)) : -15,
        bgm: lt(Q?.bgm),
        bgmAdvancedOpen: !1,
        renderLayout: U(tt?.render),
        previewAudioRel: "",
        previewAudioBust: 0,
        openaiKeyMissing: !1,
        notice: a("settings.notice_loaded")
      });
    } catch (x) {
      t.loading = !1, Jt(mt, xe(x), !0);
    }
  }
  function xe(i) {
    return i instanceof fe ? i.summary || i.message : i?.message || a("error.generic");
  }
  async function W(i, d) {
    if (_()) {
      Jt(mt, ""), t.busyAction = i, t.notice = "";
      try {
        await d();
      } catch (h) {
        Jt(mt, xe(h), !0);
      } finally {
        _() && (t.busyAction = "");
      }
    }
  }
  const Yi = () => {
    const i = {};
    return (t.subtitle_font || "").trim() && (i.subtitle_font = t.subtitle_font.trim()), i.bold = !!t.subtitle_bold, i.italic = !!t.subtitle_italic, i.align = t.subtitle_align || "center", i;
  }, Qi = () => ({
    tts_provider: t.tts_provider,
    tts_voice: (t.tts_voice || "").trim(),
    speed_multiplier: wt(t.speed_multiplier),
    tts_rate: Gi(t.speed_multiplier),
    tts_pitch: Number(t.tts_pitch) || 0,
    mix_mode: t.mix_mode,
    mix_duck_gain_db: Qe(t.mix_duck_gain_db)
  }), sa = () => {
    const i = lt(t.bgm);
    return i ? {
      original_path: i.original_path,
      normalized_path: i.normalized_path,
      original_filename: i.original_filename,
      duration_ms: i.duration_ms,
      volume_db: aa(i.volume_db),
      loop: !!i.loop,
      fade_in_ms: he(i.fade_in_ms),
      fade_out_ms: he(i.fade_out_ms)
    } : {};
  }, ee = () => {
    const i = U(t.renderLayout), d = {
      aspect_ratio: i.aspect_ratio,
      background_path: i.background_path,
      background_original_filename: i.background_original_filename
    };
    return i.logo_path && (d.logo_path = i.logo_path, d.logo_original_filename = i.logo_original_filename, d.logo_position = i.logo_position, d.logo_scale = i.logo_scale, d.logo_opacity = i.logo_opacity, d.logo_margin = i.logo_margin), d;
  }, Zi = () => {
    const i = t.subtitle_extractor || "audio_only", d = {
      use_auto_translate: !!t.use_auto_translate,
      translate_backend: t.translate_backend || "block_v2",
      tts_provider: t.tts_provider || "edge_tts",
      subtitle_extractor: i,
      external_srt_path: i === "external_srt" ? String(t.external_srt_path || "").trim() : "",
      ocr_provider: t.ocr_provider || "paddleocr",
      ocr_language: t.ocr_language || "ch",
      ocr_device: t.ocr_device || "auto"
    };
    return i === "audio_only" && (d.ocr_roi = Di(t.ocr_roi) || Qs.bottom_band), d;
  }, tr = () => {
    if (_()?.parentProject) return String(_().parentProject);
    const d = m().replace(/[\\/]+$/, "").split(/[\\/]/);
    return d[d.length - 1] || "job";
  }, er = () => W("save_text_audio", async () => {
    const i = [
      N("/api/save-video-style", { job_workspace: m(), style: Yi() }),
      N("/api/save-video-tts", { job_workspace: m(), settings: Qi() })
    ], d = !!t.bgm;
    d && i.push(N("/api/bgm/save", { job_workspace: m(), bgm: sa() })), i.push(N("/api/render-settings/save", { job_workspace: m(), render: ee() }));
    const h = await Promise.all(i), x = h[1], P = d ? h[2] : null, _t = d ? h[3] : h[2];
    Number.isFinite(Number(x.settings?.speed_multiplier)) && (t.speed_multiplier = wt(Number(x.settings.speed_multiplier))), Number.isFinite(Number(x.settings?.tts_rate)) && (t.tts_rate = Number(x.settings.tts_rate)), P && (t.bgm = lt(P.bgm)), _t && (t.renderLayout = U(_t.render)), t.notice = a("settings.notice_saved_text_audio", { path: m() });
  }), ar = () => W("bgm_upload", async () => {
    const i = await Xe(["Audio files (*.mp3;*.wav;*.m4a;*.aac)", "All files (*.*)"]);
    if (i?.cancelled) return;
    if (!i?.ok || !i.path) throw new Error(i?.error || a("settings.bgm.pick_unavailable"));
    const d = lt(t.bgm) || {}, h = await N("/api/bgm/upload", {
      job_workspace: m(),
      bgm_path: i.path,
      volume_db: d.volume_db ?? -20,
      loop: d.loop ?? !0,
      fade_in_ms: d.fade_in_ms ?? 500,
      fade_out_ms: d.fade_out_ms ?? 1e3
    });
    t.bgm = lt(h.bgm), t.notice = a("settings.bgm.uploaded");
  }), ir = () => {
    if (t.bgm)
      return W("bgm_save", async () => {
        const i = await N("/api/bgm/save", { job_workspace: m(), bgm: sa() });
        t.bgm = lt(i.bgm), t.notice = a("settings.bgm.saved");
      });
  }, rr = () => {
    if (!(!t.bgm || !window.confirm(a("settings.bgm.confirm_remove"))))
      return W("bgm_remove", async () => {
        await N("/api/bgm/remove", { job_workspace: m() }), t.bgm = null, t.bgmAdvancedOpen = !1, t.notice = a("settings.bgm.removed");
      });
  }, or = () => W("render_background_upload", async () => {
    const i = await Xe(["Image files (*.jpg;*.jpeg;*.png;*.webp)", "All files (*.*)"]);
    if (i?.cancelled) return;
    if (!i?.ok || !i.path) throw new Error(i?.error || a("settings.render_layout.pick_unavailable"));
    await N("/api/render-settings/save", { job_workspace: m(), render: ee() });
    const d = await N("/api/render-background/upload", { job_workspace: m(), image_path: i.path });
    t.renderLayout = U(d.render), t.notice = a("settings.render_layout.uploaded");
  }), na = () => W("render_layout_save", async () => {
    const i = await N("/api/render-settings/save", { job_workspace: m(), render: ee() });
    t.renderLayout = U(i.render), t.notice = a("settings.render_layout.saved");
  }), sr = () => {
    if (!(!U(t.renderLayout).background_path || !window.confirm(a("settings.render_layout.confirm_remove"))))
      return W("render_background_remove", async () => {
        const i = await N("/api/render-background/remove", { job_workspace: m() });
        t.renderLayout = U(i.render), t.notice = a("settings.render_layout.removed");
      });
  };
  function ae(i) {
    t.renderLayout = U({ ...t.renderLayout, ...i });
  }
  const nr = () => W("render_logo_upload", async () => {
    const i = await Xe(["Image files (*.png;*.jpg;*.jpeg;*.webp)", "All files (*.*)"]);
    if (i?.cancelled) return;
    if (!i?.ok || !i.path) throw new Error(i?.error || a("settings.render_layout.pick_unavailable"));
    await N("/api/render-settings/save", { job_workspace: m(), render: ee() });
    const d = await N("/api/render-logo/upload", { job_workspace: m(), image_path: i.path });
    t.renderLayout = U(d.render), t.notice = a("settings.render_layout.logo_uploaded");
  }), lr = () => {
    if (!(!U(t.renderLayout).logo_path || !window.confirm(a("settings.render_layout.logo_confirm_remove"))))
      return W("render_logo_remove", async () => {
        const i = await N("/api/render-logo/remove", { job_workspace: m() });
        t.renderLayout = U(i.render), t.notice = a("settings.render_layout.logo_removed");
      });
  }, _r = () => W("tts_preview", async () => {
    const i = (t.previewText || "").trim() || Yt;
    Ot(i);
    const d = await N("/api/tts-preview", {
      job_workspace: m(),
      tts_provider: t.tts_provider,
      tts_voice: t.tts_voice,
      speed_multiplier: t.speed_multiplier,
      text: i
    });
    t.previewText = i, t.previewAudioRel = d.rel_path || "", t.previewAudioBust = Number(d.cache_bust) || Date.now(), t.notice = a("settings.tts.preview_ready");
  });
  function ke() {
    N("/api/job-progress", { job_workspace: m() }).then((i) => {
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
  const vr = () => W("run_until_edit", async () => {
    t.openaiKeyMissing = !1, t.runUntilEditLive = {
      overall_percent: 0,
      current_stage_label: "",
      current_stage: "",
      status_label: "",
      lifecycle: "queued",
      last_error: null
    }, ke();
    try {
      $t = setInterval(ke, 800);
      try {
        const x = await N("/api/save-import-config", { job_workspace: m(), config: Zi() });
        _().importConfig = { job_workspace: m(), ...x?.config || {} };
      } catch {
      }
      const i = await N("/api/run-until-edit", {
        job_workspace: m(),
        project_name: tr(),
        use_auto_translate: !0,
        source_language: t.source_language,
        translate_backend: "block_v2",
        enable_source_cleanup: !!t.enable_source_cleanup,
        enable_translation_qa: !!t.enable_translation_qa,
        async: !0,
        subtitle_extractor: "audio_only"
      }), d = await qs(m(), i);
      _().applyJobStatusToEditGate?.(_(), d), ke();
      const h = d.voice_edit_status || "";
      if (h === "voice_edit_pending") {
        t.voiceEditGateOpen = !0, t.notice = a("settings.notice_run_until_edit", { stage: a(`stage.${h}`) }), t.runUntilEditLive = null;
        return;
      }
      t.voiceEditGateOpen = !1, t.notice = a("settings.notice_run_until_edit", { stage: a(`stage.${h || "voice_edit_pending"}`) }), t.runUntilEditLive = null, _().navigate("review");
    } catch (i) {
      if (i instanceof fe && i.code === "api_key_required") {
        t.openaiKeyMissing = !0, t.runUntilEditLive = null;
        return;
      }
      const d = t.runUntilEditLive?.current_stage_label || t.runUntilEditLive?.current_stage || "", h = i instanceof fe ? i.message || i.code || "" : xe(i), x = i instanceof fe && Array.isArray(i.logTail) && i.logTail.length ? `
— Log:
` + i.logTail.slice(-8).join(`
`) : "";
      Jt(mt, a("settings.run_failed", { stage: d || "—", message: h }) + x), t.runUntilEditLive = null;
      return;
    } finally {
      $t && (clearInterval($t), $t = null), _() && (t.runUntilEditLive = null);
    }
  }), la = w(() => Ji(t.voiceCatalog, t.tts_provider)), dr = w(() => {
    const i = /* @__PURE__ */ new Map();
    for (const d of v(la))
      !d.locale || i.has(d.locale) || i.set(d.locale, Ui(d, $(), a("settings.tts.locale_unknown")));
    return Array.from(i.entries()).sort((d, h) => d[1].localeCompare(h[1]));
  }), _a = w(() => ln(v(la), t.voiceLocaleFilter, t.voiceGenderFilter)), va = w(() => !!t.tts_voice && !v(_a).some((i) => i.voice_id === t.tts_voice)), ie = w(() => t.voiceCatalog.find((i) => i.provider === t.tts_provider && i.voice_id === t.tts_voice)), cr = w(() => {
    const i = Hi(t.translate_target), d = /* @__PURE__ */ new Map();
    for (const x of [...v(_a)].sort(ye)) {
      const P = x.locale || a("settings.tts.locale_unknown");
      d.has(P) || d.set(P, []), d.get(P).push(x);
    }
    const h = (x, P) => x[0] ? Ui(x[0], $(), a("settings.tts.locale_unknown")) : P;
    return Array.from(d.entries()).sort((x, P) => x[0] === i && P[0] !== i ? -1 : P[0] === i && x[0] !== i ? 1 : h(x[1], x[0]).localeCompare(h(P[1], P[0]))).map(([x, P]) => ({ label: h(P, x), items: P }));
  }), ur = w(() => v(ie) ? Ye(v(ie), $()) : t.tts_voice || a("settings.tts.voice_placeholder")), gr = w(() => t.mix_mode === "duck_original_speech" ? a("settings.tts.mix_duck") : a("settings.tts.mix_replace")), K = w(() => lt(t.bgm)), L = w(() => U(t.renderLayout));
  function pr(i) {
    t.tts_voice = i.target.value, te();
  }
  function mr(i) {
    t.speed_multiplier = wt(i), t.tts_rate = Gi(t.speed_multiplier), te();
  }
  const br = w(() => {
    const i = [];
    t.subtitle_font && !t.fontOptions.some((d) => d.family === t.subtitle_font) && i.push([t.subtitle_font, t.subtitle_font]);
    for (const d of t.fontOptions) i.push([d.family, d.family]);
    return i.length ? i : [[t.subtitle_font || "Arial", t.subtitle_font || "Arial"]];
  });
  Us(() => {
    m(), Y(), oa();
  });
  var da = ea(), ca = ut(da);
  {
    var fr = (i) => {
      var d = pn(), h = r(e(d)), x = e(h);
      y(() => o(x, v(mt))), f(i, d);
    };
    R(ca, (i) => {
      v(mt) && i(fr);
    });
  }
  var yr = r(ca, 2);
  {
    var hr = (i) => {
      var d = mn(), h = e(d), x = r(e(h), 2), P = e(x), _t = r(x, 2), zt = e(_t);
      y(
        (It, O) => {
          o(P, It), o(zt, O);
        },
        [
          () => a("settings.empty_title"),
          () => a("settings.empty_body")
        ]
      ), f(i, d);
    }, xr = w(() => !m()), kr = (i) => {
      var d = En(), h = ut(d), x = e(h);
      {
        var P = (O) => {
          const z = w(() => t.runUntilEditLive), Q = w(() => Math.max(0, Math.min(100, Number(v(z)?.overall_percent) || 0)));
          var tt = fn(), D = e(tt), E = r(e(D), 2), vt = e(E), M = r(E, 2), G = e(M), et = r(M, 2), I = e(et);
          Js(I, {
            get percent() {
              return v(Q);
            },
            wide: !0
          });
          var at = r(I, 2), V = e(at), Z = e(V), Nt = r(V), bt = e(Nt), re = r(et, 2);
          {
            var oe = (ft) => {
              var St = bn(), Vt = e(St);
              y(() => o(Vt, v(z).last_error)), f(ft, St);
            };
            R(re, (ft) => {
              v(z)?.last_error && ft(oe);
            });
          }
          y(
            (ft, St, Vt, se) => {
              o(vt, ft), o(G, `${St ?? ""}${v(z)?.status_label ? ` · ${v(z).status_label}` : ""}`), o(Z, Vt), o(bt, `${se ?? ""}%`);
            },
            [
              () => a("settings.run_until_edit_progress_title"),
              () => v(z)?.current_stage_label || a("settings.run_until_edit_progress_waiting"),
              () => a("settings.translation.progress_percent", { percent: Math.round(v(Q)) }),
              () => Math.round(v(Q))
            ]
          ), f(O, tt);
        }, _t = (O) => {
          var z = jn(), Q = ut(z);
          {
            var tt = (s) => {
              var c = yn(), g = e(c);
              y(() => o(g, t.notice)), f(s, c);
            };
            R(Q, (s) => {
              t.notice && s(tt);
            });
          }
          var D = r(Q, 2), E = e(D), vt = e(E), M = e(vt), G = e(M), et = e(G), I = r(G), at = e(I), V = r(M), Z = e(V), Nt = r(vt, 2), bt = e(Nt), re = e(bt), oe = e(re), ft = e(oe), St = r(oe), Vt = e(St), se = r(re, 2), ua = e(se), ga = e(ua), wr = e(ga), Lt = r(ga, 2);
          Ht(Lt, 21, () => v(br), Xt, (s, c) => {
            var g = w(() => He(v(c), 2));
            let u = () => v(g)[0], p = () => v(g)[1];
            var b = Ze(), S = e(b), k = {};
            y(() => {
              zi(b, u() === t.subtitle_font), o(S, p()), k !== (k = u()) && (b.value = (b.__value = u()) ?? "");
            }), f(s, b);
          });
          var pa;
          gt(Lt);
          var $r = r(ua, 2), ma = e($r), Nr = e(ma), Sr = r(ma), ba = r(se, 2), fa = e(ba), Lr = e(fa), Pr = r(fa, 2), we = e(Pr), $e = r(we, 2), jr = r($e, 2);
          Ht(jr, 17, () => Xs, Xt, (s, c) => {
            var g = w(() => He(v(c), 2));
            let u = () => v(g)[0], p = () => v(g)[1];
            var b = hn(), S = e(b);
            y(() => {
              Ke(b, 1, `toggle-btn ${t.subtitle_align === u() ? "active" : ""}`), o(S, p());
            }), j("click", b, () => t.subtitle_align = u()), f(s, b);
          });
          var ya = r(ba, 2), Mr = e(ya), Er = r(ya, 2), ha = e(Er), Ar = e(ha), xa = r(ha, 2), ka = e(xa), Fr = e(ka), wa = r(bt, 2), $a = e(wa), Na = e($a), Rr = e(Na), Tr = r(Na), Cr = e(Tr), Sa = r($a, 2), La = e(Sa), Pa = e(La), Br = e(Pa), ja = r(Pa, 2), dt = e(ja), ne = e(dt), Or = e(ne);
          ne.value = ne.__value = "";
          var zr = r(ne);
          Ht(zr, 17, () => v(dr), Xt, (s, c) => {
            var g = w(() => He(v(c), 2));
            let u = () => v(g)[0], p = () => v(g)[1];
            var b = Ze(), S = e(b), k = {};
            y(() => {
              o(S, p()), k !== (k = u()) && (b.value = (b.__value = u()) ?? "");
            }), f(s, b);
          });
          var Ma;
          gt(dt);
          var yt = r(dt, 2), le = e(yt), Ir = e(le);
          le.value = le.__value = "";
          var _e = r(le), Vr = e(_e);
          _e.value = _e.__value = "female";
          var Ne = r(_e), Ur = e(Ne);
          Ne.value = Ne.__value = "male";
          var Ea;
          gt(yt);
          var ht = r(ja, 2), Aa = e(ht);
          {
            var Dr = (s) => {
              var c = xn(), g = e(c), u = e(g), p = {};
              y(
                (b, S) => {
                  st(c, "label", b), o(u, S), p !== (p = t.tts_voice) && (g.value = (g.__value = t.tts_voice) ?? "");
                },
                [
                  () => a("settings.tts.current_voice"),
                  () => v(ie) ? Ye(v(ie), $()) : t.tts_voice
                ]
              ), f(s, c);
            };
            R(Aa, (s) => {
              v(va) && s(Dr);
            });
          }
          var Gr = r(Aa);
          Ht(Gr, 17, () => v(cr), Xt, (s, c) => {
            var g = kn();
            Ht(g, 21, () => v(c).items, Xt, (u, p) => {
              var b = Ze(), S = e(b), k = {};
              y(
                (F) => {
                  zi(b, v(p).voice_id === t.tts_voice), o(S, F), k !== (k = v(p).voice_id) && (b.value = (b.__value = v(p).voice_id) ?? "");
                },
                [() => Ye(v(p), $())]
              ), f(u, b);
            }), y(() => st(g, "label", v(c).label)), f(s, g);
          });
          var Fa;
          gt(ht);
          var qr = r(ht, 2);
          {
            var Wr = (s) => {
              var c = wn(), g = e(c);
              y((u) => o(g, u), [() => a("settings.tts.filter_current_hidden")]), f(s, c);
            };
            R(qr, (s) => {
              v(va) && s(Wr);
            });
          }
          var Ra = r(La, 2), Ta = e(Ra), Kr = e(Ta), Ca = r(Ta, 2), Jr = e(Ca), Hr = e(Jr), Ba = r(Ca, 2), Xr = r(Ra, 2), Oa = e(Xr), Yr = e(Oa), Pt = r(Oa, 2), ve = e(Pt), Qr = e(ve);
          ve.value = ve.__value = "replace_original_speech";
          var Se = r(ve), Zr = e(Se);
          Se.value = Se.__value = "duck_original_speech";
          var za;
          gt(Pt);
          var Ia = r(Sa, 2), Va = e(Ia), to = e(Va), eo = r(Va, 2), Ua = e(eo), Da = e(Ua), ao = e(Da), Ga = r(Da, 2), io = e(Ga), ro = e(io), qa = r(Ga, 2), oo = r(Ua, 2), Wa = e(oo), so = e(Wa), Ka = r(Wa, 2), no = e(Ka), lo = e(no), Ja = r(Ka, 2), Ha = r(Ia, 2), Xa = e(Ha), _o = e(Xa), Le = r(Xa, 2), Ya = r(Ha, 2), Qa = e(Ya), vo = e(Qa), Za = r(Qa, 2), ti = e(Za), co = e(ti), ei = r(ti, 2), uo = e(ei), ai = r(ei, 2), go = e(ai), po = r(ai, 2), mo = e(po), ii = r(Za, 2);
          {
            var bo = (s) => {
              var c = $n();
              y((g) => st(c, "src", g), [() => Zt(t.previewAudioRel, t.previewAudioBust)]), f(s, c);
            };
            R(ii, (s) => {
              t.previewAudioRel && s(bo);
            });
          }
          var fo = r(ii, 2), yo = e(fo), ho = r(Ya, 2), xo = e(ho);
          {
            let s = w(B);
            C(xo, {
              variant: "strong",
              get disabled() {
                return v(s);
              },
              onclick: _r,
              children: (c, g) => {
                var u = T();
                y((p) => o(u, p), [() => a("settings.tts.test_voice")]), f(c, u);
              },
              $$slots: { default: !0 }
            });
          }
          var ri = r(wa, 2), oi = e(ri), si = e(oi), ko = e(si), wo = r(si), $o = e(wo), ni = r(oi, 2);
          {
            var No = (s) => {
              var c = ta(), g = e(c);
              y((u) => o(g, u), [() => a("settings.bgm.no_bgm")]), f(s, c);
            }, So = (s) => {
              var c = Nn(), g = ut(c), u = e(g), p = e(u), b = r(u, 2), S = e(b), k = r(g, 2), F = r(k, 2), q = e(F), J = e(q), Ut = e(J), H = r(J, 2), ct = e(H), Dt = e(ct), it = r(H, 2), Gt = r(q, 2), rt = e(Gt), Et = e(rt), xt = e(Et), qt = r(Et), At = e(qt), Ft = r(rt, 2), kt = e(Ft);
              y(
                (ot, Rt, Tt, Ct, Wt, Bt, Kt) => {
                  o(p, ot), o(S, Rt), st(k, "src", Tt), o(Ut, Ct), o(Dt, Wt), nt(it, v(K).volume_db), o(xt, Bt), o(At, Kt), Je(kt, v(K).loop);
                },
                [
                  () => (v(K).original_filename || v(K).original_path || v(K).normalized_path).split(/[\\/]/).pop(),
                  () => a("settings.bgm.duration", { duration: dn(v(K).duration_ms) }),
                  () => Zt(v(K).normalized_path || v(K).original_path, Date.now()),
                  () => a("settings.bgm.volume"),
                  () => qi(v(K).volume_db),
                  () => a("settings.bgm.loop"),
                  () => a("settings.bgm.loop_sub")
                ]
              ), j("input", it, (ot) => t.bgm = lt({ ...t.bgm, volume_db: aa(Number(ot.target.value)) })), j("change", kt, (ot) => t.bgm = lt({ ...t.bgm, loop: ot.target.checked })), f(s, c);
            };
            R(ni, (s) => {
              v(K) ? s(So, -1) : s(No);
            });
          }
          var Lo = r(ni, 2), li = e(Lo);
          {
            let s = w(B);
            C(li, {
              variant: "secondary",
              get disabled() {
                return v(s);
              },
              onclick: ar,
              children: (c, g) => {
                var u = T();
                y((p) => o(u, p), [() => a("settings.bgm.upload")]), f(c, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Po = r(li, 2);
          {
            var jo = (s) => {
              var c = ea(), g = ut(c);
              {
                let p = w(B);
                C(g, {
                  variant: "primary",
                  get disabled() {
                    return v(p);
                  },
                  onclick: ir,
                  children: (b, S) => {
                    var k = T();
                    y((F) => o(k, F), [() => a("settings.bgm.save")]), f(b, k);
                  },
                  $$slots: { default: !0 }
                });
              }
              var u = r(g, 2);
              {
                let p = w(B);
                C(u, {
                  get disabled() {
                    return v(p);
                  },
                  onclick: rr,
                  children: (b, S) => {
                    var k = T();
                    y((F) => o(k, F), [() => a("settings.bgm.remove")]), f(b, k);
                  },
                  $$slots: { default: !0 }
                });
              }
              f(s, c);
            };
            R(Po, (s) => {
              v(K) && s(jo);
            });
          }
          var _i = r(ri, 2), vi = e(_i), di = e(vi), Mo = e(di), Eo = r(di), Ao = e(Eo), ci = r(vi, 2), Fo = e(ci), ui = e(Fo), Ro = e(ui), jt = r(ui, 2), de = e(jt), To = e(de);
          de.value = de.__value = "16:9";
          var Pe = r(de), Co = e(Pe);
          Pe.value = Pe.__value = "9:16";
          var gi;
          gt(jt);
          var pi = r(ci, 2);
          {
            var Bo = (s) => {
              var c = Sn(), g = ut(c), u = e(g), p = e(u), b = r(u, 2), S = e(b), k = r(g, 2);
              y(
                (F, q, J) => {
                  o(p, F), o(S, q), st(k, "src", J);
                },
                [
                  () => (v(L).background_original_filename || v(L).background_path).split(/[\\/]/).pop(),
                  () => a("settings.render_layout.background_ready"),
                  () => Zt(v(L).background_path, Date.now())
                ]
              ), f(s, c);
            }, Oo = (s) => {
              var c = ta(), g = e(c);
              y((u) => o(g, u), [() => a("settings.render_layout.no_background")]), f(s, c);
            };
            R(pi, (s) => {
              v(L).background_path ? s(Bo) : s(Oo, -1);
            });
          }
          var mi = r(pi, 2), bi = e(mi);
          {
            let s = w(B);
            C(bi, {
              variant: "secondary",
              get disabled() {
                return v(s);
              },
              onclick: or,
              children: (c, g) => {
                var u = T();
                y((p) => o(u, p), [() => a("settings.render_layout.upload_background")]), f(c, u);
              },
              $$slots: { default: !0 }
            });
          }
          var fi = r(bi, 2);
          {
            let s = w(B);
            C(fi, {
              variant: "primary",
              get disabled() {
                return v(s);
              },
              onclick: na,
              children: (c, g) => {
                var u = T();
                y((p) => o(u, p), [() => a("settings.render_layout.save")]), f(c, u);
              },
              $$slots: { default: !0 }
            });
          }
          var zo = r(fi, 2);
          {
            var Io = (s) => {
              {
                let c = w(B);
                C(s, {
                  get disabled() {
                    return v(c);
                  },
                  onclick: sr,
                  children: (g, u) => {
                    var p = T();
                    y((b) => o(p, b), [() => a("settings.render_layout.remove_background")]), f(g, p);
                  },
                  $$slots: { default: !0 }
                });
              }
            };
            R(zo, (s) => {
              v(L).background_path && s(Io);
            });
          }
          var yi = r(mi, 2), hi = e(yi), Vo = e(hi), Uo = r(hi), Do = e(Uo), xi = r(yi, 2);
          {
            var Go = (s) => {
              var c = Ln(), g = ut(c), u = e(g), p = e(u), b = r(u, 2), S = e(b), k = r(g, 2), F = r(k, 2), q = e(F), J = e(q), Ut = e(J), H = r(J, 2), ct = e(H), Dt = e(ct);
              ct.value = ct.__value = "top-left";
              var it = r(ct), Gt = e(it);
              it.value = it.__value = "top-right";
              var rt = r(it), Et = e(rt);
              rt.value = rt.__value = "bottom-left";
              var xt = r(rt), qt = e(xt);
              xt.value = xt.__value = "bottom-right";
              var At;
              gt(H);
              var Ft = r(q, 2), kt = e(Ft), ot = e(kt), Rt = r(kt, 2), Tt = r(Ft, 2), Ct = e(Tt), Wt = e(Ct), Bt = r(Ct, 2), Kt = r(Tt, 2), me = e(Kt), Me = e(me), be = r(me, 2);
              y(
                (X, Ee, Ae, Fe, Re, Te, Ce, Be, Oe, ze, Ie, Ve, Ue, De, Ge, qe, We) => {
                  o(p, X), o(S, Ee), st(k, "src", Ae), o(Ut, Fe), o(Dt, Re), o(Gt, Te), o(Et, Ce), o(qt, Be), At !== (At = v(L).logo_position) && (H.value = (H.__value = v(L).logo_position) ?? "", pt(H, v(L).logo_position)), o(ot, `${Oe ?? ""} (${ze ?? ""}%)`), nt(Rt, Ie), o(Wt, `${Ve ?? ""} (${Ue ?? ""}%)`), nt(Bt, De), o(Me, `${Ge ?? ""} (${qe ?? ""}%)`), nt(be, We);
                },
                [
                  () => (v(L).logo_original_filename || v(L).logo_path).split(/[\\/]/).pop(),
                  () => a("settings.render_layout.logo_ready"),
                  () => Zt(v(L).logo_path, Date.now()),
                  () => a("settings.render_layout.logo_position"),
                  () => a("settings.render_layout.pos_top_left"),
                  () => a("settings.render_layout.pos_top_right"),
                  () => a("settings.render_layout.pos_bottom_left"),
                  () => a("settings.render_layout.pos_bottom_right"),
                  () => a("settings.render_layout.logo_scale"),
                  () => Math.round(v(L).logo_scale * 100),
                  () => Math.round(v(L).logo_scale * 100),
                  () => a("settings.render_layout.logo_opacity"),
                  () => Math.round(v(L).logo_opacity * 100),
                  () => Math.round(v(L).logo_opacity * 100),
                  () => a("settings.render_layout.logo_margin"),
                  () => Math.round(v(L).logo_margin * 100),
                  () => Math.round(v(L).logo_margin * 100)
                ]
              ), j("change", H, (X) => ae({ logo_position: X.target.value })), j("input", Rt, (X) => ae({ logo_scale: Number(X.target.value) / 100 })), j("input", Bt, (X) => ae({ logo_opacity: Number(X.target.value) / 100 })), j("input", be, (X) => ae({ logo_margin: Number(X.target.value) / 100 })), f(s, c);
            }, qo = (s) => {
              var c = ta(), g = e(c);
              y((u) => o(g, u), [() => a("settings.render_layout.no_logo")]), f(s, c);
            };
            R(xi, (s) => {
              v(L).logo_path ? s(Go) : s(qo, -1);
            });
          }
          var Wo = r(xi, 2), ki = e(Wo);
          {
            let s = w(B);
            C(ki, {
              variant: "secondary",
              get disabled() {
                return v(s);
              },
              onclick: nr,
              children: (c, g) => {
                var u = T();
                y((p) => o(u, p), [() => a("settings.render_layout.upload_logo")]), f(c, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Ko = r(ki, 2);
          {
            var Jo = (s) => {
              var c = ea(), g = ut(c);
              {
                let p = w(B);
                C(g, {
                  variant: "primary",
                  get disabled() {
                    return v(p);
                  },
                  onclick: na,
                  children: (b, S) => {
                    var k = T();
                    y((F) => o(k, F), [() => a("settings.render_layout.save")]), f(b, k);
                  },
                  $$slots: { default: !0 }
                });
              }
              var u = r(g, 2);
              {
                let p = w(B);
                C(u, {
                  get disabled() {
                    return v(p);
                  },
                  onclick: lr,
                  children: (b, S) => {
                    var k = T();
                    y((F) => o(k, F), [() => a("settings.render_layout.remove_logo")]), f(b, k);
                  },
                  $$slots: { default: !0 }
                });
              }
              f(s, c);
            };
            R(Ko, (s) => {
              v(L).logo_path && s(Jo);
            });
          }
          var Ho = r(_i, 2), wi = e(Ho);
          {
            let s = w(B);
            C(wi, {
              variant: "secondary",
              get disabled() {
                return v(s);
              },
              onclick: () => oa(!0),
              children: (c, g) => {
                var u = T();
                y((p) => o(u, p), [() => a("settings.reload")]), f(c, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Xo = r(wi, 2);
          {
            let s = w(B);
            C(Xo, {
              "data-testid": "save-text-audio",
              variant: "primary",
              get disabled() {
                return v(s);
              },
              onclick: er,
              children: (c, g) => {
                var u = T();
                y((p) => o(u, p), [() => a("settings.text_audio.save")]), f(c, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Yo = r(E, 2), $i = e(Yo), Qo = e($i), Ni = e(Qo), Zo = e(Ni), ts = r(Ni), es = e(ts), as = r($i, 2), Si = e(as), is = e(Si), Li = e(is), rs = e(Li), Mt = r(Li, 2), ce = e(Mt), os = e(ce);
          ce.value = ce.__value = "auto";
          var ue = r(ce), ss = e(ue);
          ue.value = ue.__value = "zh";
          var ge = r(ue), ns = e(ge);
          ge.value = ge.__value = "en";
          var pe = r(ge), ls = e(pe);
          pe.value = pe.__value = "ja";
          var je = r(pe), _s = e(je);
          je.value = je.__value = "ko";
          var Pi;
          gt(Mt);
          var ji = r(Si, 2);
          {
            var vs = (s) => {
              var c = Pn(), g = e(c), u = e(g), p = r(g, 2), b = e(p);
              {
                let S = w(B);
                C(b, {
                  variant: "secondary",
                  get disabled() {
                    return v(S);
                  },
                  onclick: () => _().navigate("app_settings"),
                  children: (k, F) => {
                    var q = T();
                    y((J) => o(q, J), [() => a("settings.translation.go_to_app_settings")]), f(k, q);
                  },
                  $$slots: { default: !0 }
                });
              }
              y((S) => o(u, S), [() => a("settings.translation.api_key_required")]), f(s, c);
            };
            R(ji, (s) => {
              t.openaiKeyMissing && s(vs);
            });
          }
          var Mi = r(ji, 2), Ei = e(Mi), ds = e(Ei), cs = r(Ei, 2), Ai = e(cs), Fi = e(Ai), Ri = e(Fi), us = e(Ri), gs = r(Ri), ps = e(gs), ms = r(Fi, 2), Ti = e(ms), bs = r(Ai, 2), Ci = e(bs), Bi = e(Ci), fs = e(Bi), ys = r(Bi), hs = e(ys), xs = r(Ci, 2), Oi = e(xs), ks = r(Mi, 2), ws = e(ks);
          {
            let s = w(B);
            C(ws, {
              "data-testid": "run-until-edit",
              variant: "strong",
              get disabled() {
                return v(s);
              },
              onclick: vr,
              children: (c, g) => {
                var u = T();
                y((p) => o(u, p), [() => a("settings.translation.run_until_edit_auto")]), f(c, u);
              },
              $$slots: { default: !0 }
            });
          }
          y(
            (s, c, g, u, p, b, S, k, F, q, J, Ut, H, ct, Dt, it, Gt, rt, Et, xt, qt, At, Ft, kt, ot, Rt, Tt, Ct, Wt, Bt, Kt, me, Me, be, X, Ee, Ae, Fe, Re, Te, Ce, Be, Oe, ze, Ie, Ve, Ue, De, Ge, qe, We, $s, Ns, Ss, Ls, Ps, js, Ms, Es, As, Fs, Rs, Ts, Cs, Bs, Os) => {
              o(et, s), o(at, c), o(Z, g), o(ft, u), o(Vt, p), o(wr, b), pa !== (pa = t.subtitle_font) && (Lt.value = (Lt.__value = t.subtitle_font) ?? "", pt(Lt, t.subtitle_font)), o(Nr, S), nt(Sr, k), o(Lr, F), Ke(we, 1, `toggle-btn ${t.subtitle_bold ? "active" : ""}`), Ke($e, 1, `toggle-btn ${t.subtitle_italic ? "active" : ""}`), o(Mr, q), o(Ar, J), Ii(xa, Ut), Ii(ka, H), o(Fr, ct), o(Rr, Dt), o(Cr, it), o(Br, Gt), st(dt, "aria-label", rt), o(Or, `${Et ?? ""}: ${xt ?? ""}`), Ma !== (Ma = t.voiceLocaleFilter) && (dt.value = (dt.__value = t.voiceLocaleFilter) ?? "", pt(dt, t.voiceLocaleFilter)), st(yt, "aria-label", qt), o(Ir, `${At ?? ""}: ${Ft ?? ""}`), o(Vr, kt), o(Ur, ot), Ea !== (Ea = t.voiceGenderFilter) && (yt.value = (yt.__value = t.voiceGenderFilter) ?? "", pt(yt, t.voiceGenderFilter)), Fa !== (Fa = t.tts_voice) && (ht.value = (ht.__value = t.tts_voice) ?? "", pt(ht, t.tts_voice)), o(Kr, Rt), o(Hr, Tt), nt(Ba, t.speed_multiplier), o(Yr, Ct), o(Qr, Wt), o(Zr, Bt), za !== (za = t.mix_mode) && (Pt.value = (Pt.__value = t.mix_mode) ?? "", pt(Pt, t.mix_mode)), o(to, Kt), o(ao, me), o(ro, Me), nt(qa, t.tts_pitch), o(so, be), o(lo, X), nt(Ja, t.mix_duck_gain_db), o(_o, Ee), st(Le, "placeholder", Yt), nt(Le, t.previewText), o(vo, Ae), o(co, `${Fe ?? ""}: ${v(ur) ?? ""}`), o(uo, `${Re ?? ""}: ${Te ?? ""}`), o(go, `${Ce ?? ""}: ${Be ?? ""}`), o(mo, `${Oe ?? ""}: ${v(gr) ?? ""}`), o(yo, ze), o(ko, Ie), o($o, Ve), o(Mo, Ue), o(Ao, De), o(Ro, Ge), o(To, qe), o(Co, We), gi !== (gi = v(L).aspect_ratio) && (jt.value = (jt.__value = v(L).aspect_ratio) ?? "", pt(jt, v(L).aspect_ratio)), o(Vo, $s), o(Do, Ns), o(Zo, Ss), o(es, Ls), o(rs, Ps), o(os, js), o(ss, Ms), o(ns, Es), o(ls, As), o(_s, Fs), Pi !== (Pi = t.source_language) && (Mt.value = (Mt.__value = t.source_language) ?? "", pt(Mt, t.source_language)), o(ds, Rs), o(us, Ts), o(ps, Cs), Je(Ti, t.enable_source_cleanup), o(fs, Bs), o(hs, Os), Je(Oi, t.enable_translation_qa);
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
              () => `flex:1;display:grid;align-items:end;background:var(--bg-0);border-radius:14px;padding:28px;text-align:${cn(t.subtitle_align)}`,
              () => `font-family:${un(t.subtitle_font)};background:${t.bg_enabled ? gn(t.subtitle_background_color) : "transparent"};font-weight:${t.subtitle_bold ? 800 : 500};font-style:${t.subtitle_italic ? "italic" : "normal"}`,
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
              () => Ki(t.speed_multiplier),
              () => a("settings.tts.mix_mode"),
              () => a("settings.tts.mix_replace"),
              () => a("settings.tts.mix_duck"),
              () => a("settings.tts.advanced"),
              () => a("settings.tts.pitch"),
              () => Wi(t.tts_pitch),
              () => a("settings.tts.duck_gain"),
              () => qi(t.mix_duck_gain_db),
              () => a("settings.tts.preview_text_label"),
              () => a("settings.tts.preview_title"),
              () => a("settings.tts.voice"),
              () => a("settings.tts.speed"),
              () => Ki(t.speed_multiplier),
              () => a("settings.tts.pitch"),
              () => Wi(t.tts_pitch),
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
          ), j("change", Lt, (s) => t.subtitle_font = s.target.value), j("click", we, () => t.subtitle_bold = !t.subtitle_bold), j("click", $e, () => t.subtitle_italic = !t.subtitle_italic), j("change", dt, (s) => t.voiceLocaleFilter = s.target.value), j("change", yt, (s) => t.voiceGenderFilter = s.target.value), j("change", ht, pr), j("input", Ba, (s) => mr(Number(s.target.value))), j("change", Pt, (s) => t.mix_mode = s.target.value), j("input", qa, (s) => {
            t.tts_pitch = Number(s.target.value), te();
          }), j("input", Ja, (s) => t.mix_duck_gain_db = Qe(Number(s.target.value))), j("input", Le, (s) => {
            t.previewText = s.target.value, Ot(t.previewText), te();
          }), j("change", jt, (s) => t.renderLayout = U({ ...t.renderLayout, aspect_ratio: s.target.value })), j("change", Mt, (s) => t.source_language = s.target.value), j("change", Ti, (s) => t.enable_source_cleanup = s.target.checked), j("change", Oi, (s) => t.enable_translation_qa = s.target.checked), f(O, z);
        };
        R(x, (O) => {
          t.busyAction === "run_until_edit" ? O(P) : O(_t, -1);
        });
      }
      var zt = r(h, 2);
      {
        var It = (O) => {
          var z = Mn(), Q = e(z), tt = e(Q), D = e(tt), E = r(tt, 2), vt = e(E), M = r(E, 2), G = e(M);
          C(G, {
            variant: "secondary",
            onclick: () => {
              t.voiceEditGateOpen = !1, _().navigate("review");
            },
            children: (I, at) => {
              var V = T();
              y((Z) => o(V, Z), [() => a("settings.voice_edit_gate.pause")]), f(I, V);
            },
            $$slots: { default: !0 }
          });
          var et = r(G, 2);
          C(et, {
            variant: "strong",
            onclick: () => {
              t.voiceEditGateOpen = !1, _().pendingVoiceEditContinue = !0, _().navigate("render");
            },
            children: (I, at) => {
              var V = T();
              y((Z) => o(V, Z), [() => a("settings.voice_edit_gate.continue")]), f(I, V);
            },
            $$slots: { default: !0 }
          }), y(
            (I, at) => {
              o(D, I), o(vt, at);
            },
            [
              () => a("settings.voice_edit_gate.title"),
              () => a("settings.voice_edit_gate.body")
            ]
          ), f(O, z);
        };
        R(zt, (O) => {
          t.voiceEditGateOpen && O(It);
        });
      }
      f(i, d);
    };
    R(yr, (i) => {
      v(xr) ? i(hr) : i(kr, -1);
    });
  }
  f(l, da), Ds();
}
zs(["change", "click", "input"]);
const Xi = Hs(An), zn = Xi.mount, In = Xi.unmount;
export {
  zn as mount,
  In as unmount
};
//# sourceMappingURL=settings.js.map
