import { d as ko, p as wo, w as $o, x as No, f as kt, i as C, g as d, l as r, a as f, b as So, s as Po, e as jt, c as $, A as Qt, h as e, t as y, j as s, u as w, n as E, a3 as vi, Q as ct, q as Se, m as M, r as st, o as B, R as ut, K as wt, P as di, z as Pe, v as je, X as _i, V as jo } from "./chunks/api-vHpIWCot.js";
import { o as Lo } from "./chunks/index-client-CjB8cgHo.js";
import { e as Lt, i as Et } from "./chunks/each-BE197-93.js";
import { p as Eo, B as O } from "./chunks/Button-GpBM5g0S.js";
import { P as Mo } from "./chunks/ProgressBar-BACn-l7Z.js";
import { s as Ao } from "./chunks/screen-DRq5NjFu.js";
const Fo = [
  ["left", "L"],
  ["center", "C"],
  ["right", "R"]
], ci = "vlt.voicePreviewText", Mt = "Xin chào, đây là giọng đọc thử nghiệm.", Ro = {
  "vi-VN": "vi-VN-HoaiMyNeural",
  "en-US": "en-US-JennyNeural",
  "en-GB": "en-GB-SoniaNeural",
  "zh-CN": "zh-CN-XiaoxiaoNeural",
  "ja-JP": "ja-JP-NanamiNeural",
  "ko-KR": "ko-KR-SunHiNeural"
}, Co = {
  bottom_band: { x: 0, y: 0.78, w: 1, h: 0.22 }
};
function To(l) {
  const v = /* @__PURE__ */ new Set(), o = [];
  for (const a of Array.isArray(l) ? l : []) {
    if (!a || typeof a.family != "string" || !a.family.trim()) continue;
    const k = a.family.trim(), b = k.toLowerCase();
    v.has(b) || (v.add(b), o.push({ family: k, file: String(a.file || "") }));
  }
  return o.sort((a, k) => a.family.localeCompare(k.family));
}
function Bo(l) {
  const v = [];
  for (const o of Array.isArray(l) ? l : []) {
    if (!o || typeof o.voice_id != "string" || !o.voice_id.trim()) continue;
    const a = Array.isArray(o.style_tags) ? o.style_tags.map((k) => String(k || "").trim()).filter(Boolean) : [];
    v.push({
      provider: String(o.provider || "edge_tts"),
      voice_id: o.voice_id.trim(),
      label: String(o.label || o.voice_id).trim(),
      locale: String(o.locale || "").trim(),
      locale_label: String(o.locale_label || "").trim(),
      locale_label_en: String(o.locale_label_en || "").trim(),
      gender: String(o.gender || "").trim().toLowerCase(),
      gender_label: String(o.gender_label || "").trim(),
      gender_label_en: String(o.gender_label_en || "").trim(),
      short_name: String(o.short_name || "").trim(),
      style_tags: a,
      enabled: o.enabled !== !1
    });
  }
  return v;
}
function xi(l, v) {
  const o = l.filter((a) => a.provider === v && a.enabled !== !1);
  return o.length ? o : l.filter((a) => a.provider === v);
}
function Fe(l) {
  const v = String(l || "").trim();
  if (!v) return "vi";
  const o = v.toLowerCase();
  return o.startsWith("english") ? "en" : o.startsWith("vietnam") ? "vi" : o.startsWith("chinese") ? "zh" : o.startsWith("japanese") ? "ja" : o.startsWith("korean") ? "ko" : o.split(/[-_\s]/, 1)[0] || "vi";
}
function ki(l) {
  const v = Fe(l);
  return v === "en" ? "en-US" : v === "zh" ? "zh-CN" : v === "ja" ? "ja-JP" : v === "ko" ? "ko-KR" : v === "vi" ? "vi-VN" : v.includes("-") ? v : "";
}
function Oo(l, v) {
  const o = Fe(v);
  return !!l && !!o && l.toLowerCase().startsWith(`${o}-`);
}
function Zt(l, v) {
  const o = { female: 0, male: 1 }, a = o[l.gender] ?? 9, k = o[v.gender] ?? 9;
  return a !== k ? a - k : (l.short_name || l.label || l.voice_id).localeCompare(v.short_name || v.label || v.voice_id);
}
function zo(l, v, o, a = "vi") {
  const k = xi(l, v);
  if (k.some((t) => t.voice_id === o)) return o;
  const b = ki(a), G = Ro[b], At = G ? k.find((t) => t.voice_id === G && t.enabled !== !1) : null;
  if (At) return At.voice_id;
  const $t = k.filter((t) => t.locale === b || Oo(t.locale, a)).sort(Zt)[0];
  return $t ? $t.voice_id : k.filter((t) => t.gender === "female").sort(Zt)[0]?.voice_id || [...k].sort(Zt)[0]?.voice_id || o || "vi-VN-HoaiMyNeural";
}
function Vo(l, v, o) {
  return l.filter((a) => !(v && a.locale !== v || o && a.gender !== o));
}
function ui(l, v, o) {
  return v === "vi" ? l.locale_label || l.locale_label_en || l.locale || o : l.locale_label_en || l.locale_label || l.locale || o;
}
function Uo(l, v) {
  return v === "vi" ? l.gender_label || l.gender_label_en || l.gender || "" : l.gender_label_en || l.gender_label || l.gender || "";
}
function Le(l, v) {
  const o = l.short_name || l.label || l.voice_id, a = Uo(l, v), k = l.style_tags.length ? l.style_tags[0] : "", b = [a, k].filter(Boolean).join(", ");
  return b ? `${o} - ${b}` : o;
}
function gi(l) {
  if (!l || typeof l != "object") return null;
  const v = l, o = {};
  for (const a of ["x", "y", "w", "h"]) {
    const k = Number(v[a]);
    if (!Number.isFinite(k) || k < 0 || k > 1) return null;
    o[a] = k;
  }
  return o.w <= 0 || o.h <= 0 || o.x + o.w > 1.0001 || o.y + o.h > 1.0001 ? null : o;
}
function gt(l) {
  const v = Number(l);
  return Number.isFinite(v) ? Math.max(0.5, Math.min(2, Math.round(v * 20) / 20)) : 1;
}
function pi(l) {
  return Math.max(-50, Math.min(50, Math.round((gt(l) - 1) * 100)));
}
function Io(l) {
  const v = Number(l);
  return Number.isFinite(v) ? gt(1 + v / 100) : 1;
}
function Ee(l) {
  const v = Number(l);
  return Number.isFinite(v) ? Math.max(-30, Math.min(0, Math.round(v * 100) / 100)) : -15;
}
function Ae(l) {
  const v = Number(l);
  return Number.isFinite(v) ? Math.max(-40, Math.min(0, Math.round(v * 100) / 100)) : -20;
}
function te(l) {
  const v = Number(l);
  return Number.isFinite(v) ? Math.max(0, Math.min(1e4, Math.round(v))) : 0;
}
function Q(l) {
  if (!l || typeof l != "object") return null;
  const v = l, o = String(v.normalized_path || "").trim(), a = String(v.original_path || "").trim();
  return !o && !a ? null : {
    original_path: a,
    normalized_path: o,
    original_filename: String(v.original_filename || "").trim(),
    duration_ms: Math.max(0, Math.round(Number(v.duration_ms) || 0)),
    volume_db: Ae(v.volume_db),
    loop: v.loop !== !1,
    fade_in_ms: te(v.fade_in_ms ?? 500),
    fade_out_ms: te(v.fade_out_ms ?? 1e3)
  };
}
function Z(l) {
  const v = l && typeof l == "object" ? l : {};
  return {
    aspect_ratio: String(v.aspect_ratio || "16:9").trim() === "9:16" ? "9:16" : "16:9",
    background_path: String(v.background_path || "").trim(),
    background_original_filename: String(v.background_original_filename || "").trim()
  };
}
function bi(l) {
  const v = Number(l), o = Number.isFinite(v) ? Math.round(v * 10) / 10 : 0;
  return `${o > 0 ? "+" : ""}${o} dB`;
}
function mi(l) {
  const v = Number(l) || 0;
  return `${v > 0 ? "+" : ""}${v}%`;
}
function fi(l) {
  return `${gt(l).toFixed(2).replace(/0$/, "").replace(/\.$/, "")}x`;
}
function Do(l) {
  const v = Math.max(0, Math.round((Number(l) || 0) / 1e3)), o = Math.floor(v / 60), a = String(v % 60).padStart(2, "0");
  return `${o}:${a}`;
}
function Go(l) {
  return l === "left" ? "left" : l === "right" ? "right" : "center";
}
function qo(l) {
  const v = String(l || "").trim();
  return v ? `"${v}", "Segoe UI", sans-serif` : '"Segoe UI", sans-serif';
}
function Wo(l) {
  const v = String(l || "").trim();
  return /^#(?:[0-9a-f]{6}|[0-9a-f]{8})$/i.test(v) ? v.toUpperCase() : "#000000";
}
var Ko = E('<div class="error-banner"><div class="error-code">UI</div><div class="error-message"> </div></div>'), Jo = E('<div class="card" data-testid="settings-empty"><div class="empty-card"><div class="empty-icon">⚙</div> <h3> </h3> <p> </p></div></div>'), Ho = E('<div class="small-muted run-until-edit-progress-error"> </div>'), Xo = E('<div class="card work-card"><div class="work"><div class="orb"><div class="ring"></div><div class="ring r2"></div><div class="core"></div></div> <h2 class="work-title"> <span class="work-dots"></span></h2> <p class="work-sub"> </p> <div class="work-bar"><!> <div class="work-bar-foot"><span> </span><span> </span></div></div> <!></div></div>'), Yo = E('<div class="info-banner"> </div>'), Me = E("<option> </option>"), Qo = E('<button type="button"> </button>'), Zo = E('<optgroup><option selected=""> </option></optgroup>'), tn = E("<optgroup></optgroup>"), en = E('<div class="small-muted voice-filter-warning"> </div>'), an = E('<audio class="audio-preview" controls="" preload="metadata"></audio>'), hi = E('<div class="meta-empty"> </div>'), rn = E('<div class="bgm-summary"><div class="row-title"> </div> <div class="small-muted"> </div></div> <audio class="audio-preview" controls="" preload="metadata"></audio> <div class="field-grid"><div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>-40 ... 0 dB</span></div> <input class="range-input" type="range" min="-40" max="0" step="1"/></div> <div class="switch-row"><div><div style="font-weight:700"> </div><div class="small-muted"> </div></div> <label class="checkbox-row"><input type="checkbox"/></label></div></div>', 1), yi = E("<!> <!>", 1), sn = E('<div class="bgm-summary"><div class="row-title"> </div> <div class="small-muted"> </div></div> <img class="render-background-preview" alt=""/>', 1), on = E('<div class="section-block stack inline-action-banner" data-testid="api-key-missing" style="gap:10px"><div class="small-muted"> </div> <div class="toolbar"><!></div></div>'), nn = E('<!> <div class="stack"><div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div><div class="tag"> </div></div> <div class="card-body stack"><div class="section-block stack"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field"><label> </label> <select class="input"></select></div> <div class="field"><label> </label><input class="input" type="text" readonly=""/></div></div> <div class="stack" style="gap:10px"><div class="small-muted"> </div> <div class="toggle-bar"><button type="button" data-testid="style-bold">B</button> <button type="button" data-testid="style-italic">I</button> <!></div></div> <div class="small-muted"> </div> <div class="preview-tile"><div class="card-title"> </div> <div><span class="subtitle-sample"> </span></div></div></div> <div class="section-block stack"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field voice-picker"><label> </label> <div class="voice-filter-row"><select class="input voice-filter-select"><option> </option><!></select> <select class="input voice-filter-select"><option> </option><option> </option><option> </option></select></div> <select class="input"><!><!></select> <!></div> <div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>0.5x ... 2x</span></div> <input class="range-input" type="range" min="0.5" max="2" step="0.05"/></div> <div class="field"><label> </label> <select class="input"><option> </option><option> </option></select></div></div> <details class="advanced-details"><summary> </summary> <div class="field-grid advanced-grid"><div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>-50 ... +50</span></div> <input class="range-input" type="range" min="-50" max="50" step="1"/></div> <div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>-30 ... 0 dB</span></div> <input class="range-input" type="range" min="-30" max="0" step="1"/></div></div></details> <div class="field voice-preview-text-field"><label> </label> <input class="input" type="text"/></div> <div class="preview-tile"><div class="card-title"> </div> <div class="small-muted"><div> </div> <div> </div> <div> </div> <div> </div></div> <!> <div class="small-muted"> </div></div> <div class="toolbar"><!></div></div> <div class="section-block stack bgm-section"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <!> <div class="toolbar"><!> <!></div></div> <div class="section-block stack render-layout-section"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option></select></div></div> <!> <div class="toolbar"><!> <!> <!></div></div> <div class="toolbar"><!> <!></div></div></div> <div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option><option> </option><option> </option></select></div></div> <!> <details class="advanced-details"><summary> </summary> <div class="section-block"><div class="switch-row"><div><div style="font-weight:700"> </div><div class="small-muted"> </div></div> <label class="checkbox-row"><input type="checkbox"/></label></div> <div class="switch-row"><div><div style="font-weight:700"> </div><div class="small-muted"> </div></div> <label class="checkbox-row"><input type="checkbox"/></label></div></div></details> <div class="toolbar"><!></div></div></div></div>', 1), ln = E('<div class="voice-edit-gate-backdrop" role="dialog" aria-modal="true"><div class="voice-edit-gate-card stack"><h3 class="voice-edit-gate-title"> </h3> <p class="voice-edit-gate-body"> </p> <div class="voice-edit-gate-actions"><!> <!></div></div></div>'), vn = E('<div class="screen stack" data-testid="settings-screen"><!></div> <!>', 1);
function dn(l, v) {
  wo(v, !0);
  let o = Eo(v, "ctx", 7);
  const a = (i, _) => (o()?.t ?? ((h) => h))(i, _), k = () => o()?.getLang?.() ?? "vi", b = () => String(o()?.jobWorkspace || ""), G = () => String(o()?.parentProjectRoot || "");
  function At() {
    try {
      const i = window.localStorage.getItem(ci);
      return i && i.trim() ? i : Mt;
    } catch {
      return Mt;
    }
  }
  function $t(i) {
    try {
      window.localStorage.setItem(ci, i || Mt);
    } catch {
    }
  }
  function Re() {
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
        background_original_filename: ""
      },
      previewAudioRel: "",
      previewAudioBust: 0,
      previewText: At(),
      voiceEditGateOpen: !1,
      openaiKeyMissing: !1,
      runUntilEditLive: null
    };
  }
  let t = $o(o()?.settingsState || Re());
  o() && (o().settingsState = t);
  let ot = Po(""), pt = null;
  Lo(() => {
    pt && clearInterval(pt);
  });
  const I = () => !!t.loading || !!t.busyAction;
  function ee(i, _) {
    if (!b()) return "";
    const h = new URLSearchParams({ workspace: b(), rel: i });
    return _ && h.set("v", String(_)), `/media?${h.toString()}`;
  }
  function Ft() {
    t.previewAudioRel = "", t.previewAudioBust = 0;
  }
  async function Ce(i = !1) {
    if (!b() || !i && t.loadedJobWorkspace === b() && t.loadedProjectRoot === G()) return;
    t.loading = !0, t.notice = "", jt(ot, "");
    const _ = !i && t.fontOptions.length ? Promise.resolve({ fonts: t.fontOptions }) : $("/api/list-system-fonts"), h = !i && t.voiceCatalog.length ? Promise.resolve({ voices: t.voiceCatalog }) : $("/api/list-voices");
    try {
      const [
        x,
        S,
        et,
        Nt,
        St,
        A,
        F,
        q,
        J
      ] = await Promise.all([
        $("/api/get-video-style", { job_workspace: b() }),
        $("/api/get-video-tts", { job_workspace: b() }),
        G() ? $("/api/get-project-style", { project_root: G() }) : Promise.resolve({ style: {} }),
        G() ? $("/api/get-project-tts", { project_root: G() }) : Promise.resolve({ settings: {} }),
        $("/api/get-import-config", { job_workspace: b() }),
        _,
        h,
        $("/api/bgm/status", { job_workspace: b() }),
        $("/api/render-settings/status", { job_workspace: b() })
      ]), z = { ...et.style || {}, ...x.style || {} }, L = { ...Nt.settings || {}, ...S.settings || {} }, at = o()?.importConfig && o().importConfig.job_workspace === b() ? o().importConfig : null, P = { ...St.config || {}, ...at || {} }, V = String(P?.subtitle_extractor || "audio_only").toLowerCase();
      let H = !1, R = V;
      V === "ocr_only" || V === "hybrid" ? (H = !0, R = "audio_only") : V !== "external_srt" && (R = "audio_only");
      const X = To(A.fonts || []), T = Bo(F.voices || []), W = P?.tts_provider || L.tts_provider || "edge_tts", bt = Number.isFinite(Number(L.tts_rate)) ? Number(L.tts_rate) : 0, nt = Fe(P?.translate_target || P?.target_language || P?.target_locale || "vi");
      Object.assign(t, {
        loadedJobWorkspace: b(),
        loadedProjectRoot: G(),
        loading: !1,
        fontOptions: X,
        voiceCatalog: T,
        subtitle_font: z.subtitle_font || "",
        subtitle_background_color: z.subtitle_background_color || "#000000",
        bg_enabled: !!z.subtitle_background_color,
        subtitle_bold: !!z.bold,
        subtitle_italic: !!z.italic,
        subtitle_align: z.align || "center",
        use_auto_translate: P?.use_auto_translate ?? !0,
        source_language: P?.source_language || "auto",
        translate_target: nt,
        translate_backend: P?.translate_backend || "block_v2",
        subtitle_extractor: R,
        external_srt_path: String(P?.external_srt_path || "").trim(),
        legacy_deprecated_extractor: H,
        ocr_provider: P?.ocr_provider || "paddleocr",
        ocr_language: P?.ocr_language || "ch",
        ocr_device: P?.ocr_device || "auto",
        ocr_roi: gi(P?.ocr_roi) || { x: 0, y: 0.78, w: 1, h: 0.22 },
        tts_provider: W,
        tts_voice: zo(T, W, L.tts_voice || "", nt),
        speed_multiplier: Number.isFinite(Number(L.speed_multiplier)) ? gt(Number(L.speed_multiplier)) : Io(bt),
        tts_rate: bt,
        tts_pitch: Number.isFinite(Number(L.tts_pitch)) ? Number(L.tts_pitch) : 0,
        mix_mode: L.mix_mode || "replace_original_speech",
        mix_duck_gain_db: Number.isFinite(Number(L.mix_duck_gain_db)) ? Ee(Number(L.mix_duck_gain_db)) : -15,
        bgm: Q(q?.bgm),
        bgmAdvancedOpen: !1,
        renderLayout: Z(J?.render),
        previewAudioRel: "",
        previewAudioBust: 0,
        openaiKeyMissing: !1,
        notice: a("settings.notice_loaded")
      });
    } catch (x) {
      t.loading = !1, jt(ot, ae(x), !0);
    }
  }
  function ae(i) {
    return i instanceof Qt ? i.summary || i.message : i?.message || a("error.generic");
  }
  async function K(i, _) {
    if (o()) {
      jt(ot, ""), t.busyAction = i, t.notice = "";
      try {
        await _();
      } catch (h) {
        jt(ot, ae(h), !0);
      } finally {
        o() && (t.busyAction = "");
      }
    }
  }
  const $i = () => {
    const i = {};
    return (t.subtitle_font || "").trim() && (i.subtitle_font = t.subtitle_font.trim()), i.bold = !!t.subtitle_bold, i.italic = !!t.subtitle_italic, i.align = t.subtitle_align || "center", i;
  }, Ni = () => ({
    tts_provider: t.tts_provider,
    tts_voice: (t.tts_voice || "").trim(),
    speed_multiplier: gt(t.speed_multiplier),
    tts_rate: pi(t.speed_multiplier),
    tts_pitch: Number(t.tts_pitch) || 0,
    mix_mode: t.mix_mode,
    mix_duck_gain_db: Ee(t.mix_duck_gain_db)
  }), Te = () => {
    const i = Q(t.bgm);
    return i ? {
      original_path: i.original_path,
      normalized_path: i.normalized_path,
      original_filename: i.original_filename,
      duration_ms: i.duration_ms,
      volume_db: Ae(i.volume_db),
      loop: !!i.loop,
      fade_in_ms: te(i.fade_in_ms),
      fade_out_ms: te(i.fade_out_ms)
    } : {};
  }, ie = () => {
    const i = Z(t.renderLayout);
    return {
      aspect_ratio: i.aspect_ratio,
      background_path: i.background_path,
      background_original_filename: i.background_original_filename
    };
  }, Si = () => {
    const i = t.subtitle_extractor || "audio_only", _ = {
      use_auto_translate: !!t.use_auto_translate,
      translate_backend: t.translate_backend || "block_v2",
      tts_provider: t.tts_provider || "edge_tts",
      subtitle_extractor: i,
      external_srt_path: i === "external_srt" ? String(t.external_srt_path || "").trim() : "",
      ocr_provider: t.ocr_provider || "paddleocr",
      ocr_language: t.ocr_language || "ch",
      ocr_device: t.ocr_device || "auto"
    };
    return i === "audio_only" && (_.ocr_roi = gi(t.ocr_roi) || Co.bottom_band), _;
  }, Pi = () => {
    if (o()?.parentProject) return String(o().parentProject);
    const _ = b().replace(/[\\/]+$/, "").split(/[\\/]/);
    return _[_.length - 1] || "job";
  }, ji = () => K("save_text_audio", async () => {
    const i = [
      $("/api/save-video-style", { job_workspace: b(), style: $i() }),
      $("/api/save-video-tts", { job_workspace: b(), settings: Ni() })
    ], _ = !!t.bgm;
    _ && i.push($("/api/bgm/save", { job_workspace: b(), bgm: Te() })), i.push($("/api/render-settings/save", { job_workspace: b(), render: ie() }));
    const h = await Promise.all(i), x = h[1], S = _ ? h[2] : null, et = _ ? h[3] : h[2];
    Number.isFinite(Number(x.settings?.speed_multiplier)) && (t.speed_multiplier = gt(Number(x.settings.speed_multiplier))), Number.isFinite(Number(x.settings?.tts_rate)) && (t.tts_rate = Number(x.settings.tts_rate)), S && (t.bgm = Q(S.bgm)), et && (t.renderLayout = Z(et.render)), t.notice = a("settings.notice_saved_text_audio", { path: b() });
  }), Li = () => K("bgm_upload", async () => {
    const i = await _i(["Audio files (*.mp3;*.wav;*.m4a;*.aac)", "All files (*.*)"]);
    if (i?.cancelled) return;
    if (!i?.ok || !i.path) throw new Error(i?.error || a("settings.bgm.pick_unavailable"));
    const _ = Q(t.bgm) || {}, h = await $("/api/bgm/upload", {
      job_workspace: b(),
      bgm_path: i.path,
      volume_db: _.volume_db ?? -20,
      loop: _.loop ?? !0,
      fade_in_ms: _.fade_in_ms ?? 500,
      fade_out_ms: _.fade_out_ms ?? 1e3
    });
    t.bgm = Q(h.bgm), t.notice = a("settings.bgm.uploaded");
  }), Ei = () => {
    if (t.bgm)
      return K("bgm_save", async () => {
        const i = await $("/api/bgm/save", { job_workspace: b(), bgm: Te() });
        t.bgm = Q(i.bgm), t.notice = a("settings.bgm.saved");
      });
  }, Mi = () => {
    if (!(!t.bgm || !window.confirm(a("settings.bgm.confirm_remove"))))
      return K("bgm_remove", async () => {
        await $("/api/bgm/remove", { job_workspace: b() }), t.bgm = null, t.bgmAdvancedOpen = !1, t.notice = a("settings.bgm.removed");
      });
  }, Ai = () => K("render_background_upload", async () => {
    const i = await _i(["Image files (*.jpg;*.jpeg;*.png;*.webp)", "All files (*.*)"]);
    if (i?.cancelled) return;
    if (!i?.ok || !i.path) throw new Error(i?.error || a("settings.render_layout.pick_unavailable"));
    await $("/api/render-settings/save", { job_workspace: b(), render: ie() });
    const _ = await $("/api/render-background/upload", { job_workspace: b(), image_path: i.path });
    t.renderLayout = Z(_.render), t.notice = a("settings.render_layout.uploaded");
  }), Fi = () => K("render_layout_save", async () => {
    const i = await $("/api/render-settings/save", { job_workspace: b(), render: ie() });
    t.renderLayout = Z(i.render), t.notice = a("settings.render_layout.saved");
  }), Ri = () => {
    if (!(!Z(t.renderLayout).background_path || !window.confirm(a("settings.render_layout.confirm_remove"))))
      return K("render_background_remove", async () => {
        const i = await $("/api/render-background/remove", { job_workspace: b() });
        t.renderLayout = Z(i.render), t.notice = a("settings.render_layout.removed");
      });
  }, Ci = () => K("tts_preview", async () => {
    const i = (t.previewText || "").trim() || Mt;
    $t(i);
    const _ = await $("/api/tts-preview", {
      job_workspace: b(),
      tts_provider: t.tts_provider,
      tts_voice: t.tts_voice,
      speed_multiplier: t.speed_multiplier,
      text: i
    });
    t.previewText = i, t.previewAudioRel = _.rel_path || "", t.previewAudioBust = Number(_.cache_bust) || Date.now(), t.notice = a("settings.tts.preview_ready");
  });
  function re() {
    $("/api/job-progress", { job_workspace: b() }).then((i) => {
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
  const Ti = () => K("run_until_edit", async () => {
    t.openaiKeyMissing = !1, t.runUntilEditLive = {
      overall_percent: 0,
      current_stage_label: "",
      current_stage: "",
      status_label: "",
      lifecycle: "queued",
      last_error: null
    }, re();
    try {
      pt = setInterval(re, 800);
      try {
        const x = await $("/api/save-import-config", { job_workspace: b(), config: Si() });
        o().importConfig = { job_workspace: b(), ...x?.config || {} };
      } catch {
      }
      const i = await $("/api/run-until-edit", {
        job_workspace: b(),
        project_name: Pi(),
        use_auto_translate: !0,
        source_language: t.source_language,
        translate_backend: "block_v2",
        enable_source_cleanup: !!t.enable_source_cleanup,
        enable_translation_qa: !!t.enable_translation_qa,
        async: !0,
        subtitle_extractor: "audio_only"
      }), _ = await jo(b(), i);
      o().applyJobStatusToEditGate?.(o(), _), re();
      const h = _.voice_edit_status || "";
      if (h === "voice_edit_pending") {
        t.voiceEditGateOpen = !0, t.notice = a("settings.notice_run_until_edit", { stage: a(`stage.${h}`) }), t.runUntilEditLive = null;
        return;
      }
      t.voiceEditGateOpen = !1, t.notice = a("settings.notice_run_until_edit", { stage: a(`stage.${h || "voice_edit_pending"}`) }), t.runUntilEditLive = null, o().navigate("review");
    } catch (i) {
      if (i instanceof Qt && i.code === "api_key_required") {
        t.openaiKeyMissing = !0, t.runUntilEditLive = null;
        return;
      }
      const _ = t.runUntilEditLive?.current_stage_label || t.runUntilEditLive?.current_stage || "", h = i instanceof Qt ? i.message || i.code || "" : ae(i), x = i instanceof Qt && Array.isArray(i.logTail) && i.logTail.length ? `
— Log:
` + i.logTail.slice(-8).join(`
`) : "";
      jt(ot, a("settings.run_failed", { stage: _ || "—", message: h }) + x), t.runUntilEditLive = null;
      return;
    } finally {
      pt && (clearInterval(pt), pt = null), o() && (t.runUntilEditLive = null);
    }
  }), Be = w(() => xi(t.voiceCatalog, t.tts_provider)), Bi = w(() => {
    const i = /* @__PURE__ */ new Map();
    for (const _ of d(Be))
      !_.locale || i.has(_.locale) || i.set(_.locale, ui(_, k(), a("settings.tts.locale_unknown")));
    return Array.from(i.entries()).sort((_, h) => _[1].localeCompare(h[1]));
  }), Oe = w(() => Vo(d(Be), t.voiceLocaleFilter, t.voiceGenderFilter)), ze = w(() => !!t.tts_voice && !d(Oe).some((i) => i.voice_id === t.tts_voice)), Rt = w(() => t.voiceCatalog.find((i) => i.provider === t.tts_provider && i.voice_id === t.tts_voice)), Oi = w(() => {
    const i = ki(t.translate_target), _ = /* @__PURE__ */ new Map();
    for (const x of [...d(Oe)].sort(Zt)) {
      const S = x.locale || a("settings.tts.locale_unknown");
      _.has(S) || _.set(S, []), _.get(S).push(x);
    }
    const h = (x, S) => x[0] ? ui(x[0], k(), a("settings.tts.locale_unknown")) : S;
    return Array.from(_.entries()).sort((x, S) => x[0] === i && S[0] !== i ? -1 : S[0] === i && x[0] !== i ? 1 : h(x[1], x[0]).localeCompare(h(S[1], S[0]))).map(([x, S]) => ({ label: h(S, x), items: S }));
  }), zi = w(() => d(Rt) ? Le(d(Rt), k()) : t.tts_voice || a("settings.tts.voice_placeholder")), Vi = w(() => t.mix_mode === "duck_original_speech" ? a("settings.tts.mix_duck") : a("settings.tts.mix_replace")), D = w(() => Q(t.bgm)), tt = w(() => Z(t.renderLayout));
  function Ui(i) {
    t.tts_voice = i.target.value, Ft();
  }
  function Ii(i) {
    t.speed_multiplier = gt(i), t.tts_rate = pi(t.speed_multiplier), Ft();
  }
  const Di = w(() => {
    const i = [];
    t.subtitle_font && !t.fontOptions.some((_) => _.family === t.subtitle_font) && i.push([t.subtitle_font, t.subtitle_font]);
    for (const _ of t.fontOptions) i.push([_.family, _.family]);
    return i.length ? i : [[t.subtitle_font || "Arial", t.subtitle_font || "Arial"]];
  });
  No(() => {
    b(), G(), Ce();
  });
  var Ve = yi(), Ue = kt(Ve);
  {
    var Gi = (i) => {
      var _ = Ko(), h = r(e(_)), x = e(h);
      y(() => s(x, d(ot))), f(i, _);
    };
    C(Ue, (i) => {
      d(ot) && i(Gi);
    });
  }
  var qi = r(Ue, 2);
  {
    var Wi = (i) => {
      var _ = Jo(), h = e(_), x = r(e(h), 2), S = e(x), et = r(x, 2), Nt = e(et);
      y(
        (St, A) => {
          s(S, St), s(Nt, A);
        },
        [
          () => a("settings.empty_title"),
          () => a("settings.empty_body")
        ]
      ), f(i, _);
    }, Ki = w(() => !b()), Ji = (i) => {
      var _ = vn(), h = kt(_), x = e(h);
      {
        var S = (A) => {
          const F = w(() => t.runUntilEditLive), q = w(() => Math.max(0, Math.min(100, Number(d(F)?.overall_percent) || 0)));
          var J = Xo(), z = e(J), L = r(e(z), 2), at = e(L), P = r(L, 2), V = e(P), H = r(P, 2), R = e(H);
          Mo(R, {
            get percent() {
              return d(q);
            },
            wide: !0
          });
          var X = r(R, 2), T = e(X), W = e(T), bt = r(T), nt = e(bt), Ct = r(H, 2);
          {
            var Tt = (lt) => {
              var mt = Ho(), Pt = e(mt);
              y(() => s(Pt, d(F).last_error)), f(lt, mt);
            };
            C(Ct, (lt) => {
              d(F)?.last_error && lt(Tt);
            });
          }
          y(
            (lt, mt, Pt, Bt) => {
              s(at, lt), s(V, `${mt ?? ""}${d(F)?.status_label ? ` · ${d(F).status_label}` : ""}`), s(W, Pt), s(nt, `${Bt ?? ""}%`);
            },
            [
              () => a("settings.run_until_edit_progress_title"),
              () => d(F)?.current_stage_label || a("settings.run_until_edit_progress_waiting"),
              () => a("settings.translation.progress_percent", { percent: Math.round(d(q)) }),
              () => Math.round(d(q))
            ]
          ), f(A, J);
        }, et = (A) => {
          var F = nn(), q = kt(F);
          {
            var J = (n) => {
              var c = Yo(), g = e(c);
              y(() => s(g, t.notice)), f(n, c);
            };
            C(q, (n) => {
              t.notice && n(J);
            });
          }
          var z = r(q, 2), L = e(z), at = e(L), P = e(at), V = e(P), H = e(V), R = r(V), X = e(R), T = r(P), W = e(T), bt = r(at, 2), nt = e(bt), Ct = e(nt), Tt = e(Ct), lt = e(Tt), mt = r(Tt), Pt = e(mt), Bt = r(Ct, 2), Ie = e(Bt), De = e(Ie), Hi = e(De), ft = r(De, 2);
          Lt(ft, 21, () => d(Di), Et, (n, c) => {
            var g = w(() => je(d(c), 2));
            let u = () => d(g)[0], p = () => d(g)[1];
            var m = Me(), j = e(m), N = {};
            y(() => {
              vi(m, u() === t.subtitle_font), s(j, p()), N !== (N = u()) && (m.value = (m.__value = u()) ?? "");
            }), f(n, m);
          });
          var Ge;
          ct(ft);
          var Xi = r(Ie, 2), qe = e(Xi), Yi = e(qe), Qi = r(qe), We = r(Bt, 2), Ke = e(We), Zi = e(Ke), tr = r(Ke, 2), se = e(tr), oe = r(se, 2), er = r(oe, 2);
          Lt(er, 17, () => Fo, Et, (n, c) => {
            var g = w(() => je(d(c), 2));
            let u = () => d(g)[0], p = () => d(g)[1];
            var m = Qo(), j = e(m);
            y(() => {
              Se(m, 1, `toggle-btn ${t.subtitle_align === u() ? "active" : ""}`), s(j, p());
            }), M("click", m, () => t.subtitle_align = u()), f(n, m);
          });
          var Je = r(We, 2), ar = e(Je), ir = r(Je, 2), He = e(ir), rr = e(He), Xe = r(He, 2), Ye = e(Xe), sr = e(Ye), Qe = r(nt, 2), Ze = e(Qe), ta = e(Ze), or = e(ta), nr = r(ta), lr = e(nr), ea = r(Ze, 2), aa = e(ea), ia = e(aa), vr = e(ia), ra = r(ia, 2), it = e(ra), Ot = e(it), dr = e(Ot);
          Ot.value = Ot.__value = "";
          var _r = r(Ot);
          Lt(_r, 17, () => d(Bi), Et, (n, c) => {
            var g = w(() => je(d(c), 2));
            let u = () => d(g)[0], p = () => d(g)[1];
            var m = Me(), j = e(m), N = {};
            y(() => {
              s(j, p()), N !== (N = u()) && (m.value = (m.__value = u()) ?? "");
            }), f(n, m);
          });
          var sa;
          ct(it);
          var vt = r(it, 2), zt = e(vt), cr = e(zt);
          zt.value = zt.__value = "";
          var Vt = r(zt), ur = e(Vt);
          Vt.value = Vt.__value = "female";
          var ne = r(Vt), gr = e(ne);
          ne.value = ne.__value = "male";
          var oa;
          ct(vt);
          var dt = r(ra, 2), na = e(dt);
          {
            var pr = (n) => {
              var c = Zo(), g = e(c), u = e(g), p = {};
              y(
                (m, j) => {
                  st(c, "label", m), s(u, j), p !== (p = t.tts_voice) && (g.value = (g.__value = t.tts_voice) ?? "");
                },
                [
                  () => a("settings.tts.current_voice"),
                  () => d(Rt) ? Le(d(Rt), k()) : t.tts_voice
                ]
              ), f(n, c);
            };
            C(na, (n) => {
              d(ze) && n(pr);
            });
          }
          var br = r(na);
          Lt(br, 17, () => d(Oi), Et, (n, c) => {
            var g = tn();
            Lt(g, 21, () => d(c).items, Et, (u, p) => {
              var m = Me(), j = e(m), N = {};
              y(
                (U) => {
                  vi(m, d(p).voice_id === t.tts_voice), s(j, U), N !== (N = d(p).voice_id) && (m.value = (m.__value = d(p).voice_id) ?? "");
                },
                [() => Le(d(p), k())]
              ), f(u, m);
            }), y(() => st(g, "label", d(c).label)), f(n, g);
          });
          var la;
          ct(dt);
          var mr = r(dt, 2);
          {
            var fr = (n) => {
              var c = en(), g = e(c);
              y((u) => s(g, u), [() => a("settings.tts.filter_current_hidden")]), f(n, c);
            };
            C(mr, (n) => {
              d(ze) && n(fr);
            });
          }
          var va = r(aa, 2), da = e(va), hr = e(da), _a = r(da, 2), yr = e(_a), xr = e(yr), ca = r(_a, 2), kr = r(va, 2), ua = e(kr), wr = e(ua), ht = r(ua, 2), Ut = e(ht), $r = e(Ut);
          Ut.value = Ut.__value = "replace_original_speech";
          var le = r(Ut), Nr = e(le);
          le.value = le.__value = "duck_original_speech";
          var ga;
          ct(ht);
          var pa = r(ea, 2), ba = e(pa), Sr = e(ba), Pr = r(ba, 2), ma = e(Pr), fa = e(ma), jr = e(fa), ha = r(fa, 2), Lr = e(ha), Er = e(Lr), ya = r(ha, 2), Mr = r(ma, 2), xa = e(Mr), Ar = e(xa), ka = r(xa, 2), Fr = e(ka), Rr = e(Fr), wa = r(ka, 2), $a = r(pa, 2), Na = e($a), Cr = e(Na), ve = r(Na, 2), Sa = r($a, 2), Pa = e(Sa), Tr = e(Pa), ja = r(Pa, 2), La = e(ja), Br = e(La), Ea = r(La, 2), Or = e(Ea), Ma = r(Ea, 2), zr = e(Ma), Vr = r(Ma, 2), Ur = e(Vr), Aa = r(ja, 2);
          {
            var Ir = (n) => {
              var c = an();
              y((g) => st(c, "src", g), [() => ee(t.previewAudioRel, t.previewAudioBust)]), f(n, c);
            };
            C(Aa, (n) => {
              t.previewAudioRel && n(Ir);
            });
          }
          var Dr = r(Aa, 2), Gr = e(Dr), qr = r(Sa, 2), Wr = e(qr);
          {
            let n = w(I);
            O(Wr, {
              variant: "strong",
              get disabled() {
                return d(n);
              },
              onclick: Ci,
              children: (c, g) => {
                var u = B();
                y((p) => s(u, p), [() => a("settings.tts.test_voice")]), f(c, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Fa = r(Qe, 2), Ra = e(Fa), Ca = e(Ra), Kr = e(Ca), Jr = r(Ca), Hr = e(Jr), Ta = r(Ra, 2);
          {
            var Xr = (n) => {
              var c = hi(), g = e(c);
              y((u) => s(g, u), [() => a("settings.bgm.no_bgm")]), f(n, c);
            }, Yr = (n) => {
              var c = rn(), g = kt(c), u = e(g), p = e(u), m = r(u, 2), j = e(m), N = r(g, 2), U = r(N, 2), Y = e(U), rt = e(Y), ce = e(rt), Kt = r(rt, 2), ue = e(Kt), ge = e(ue), Jt = r(Kt, 2), pe = r(Y, 2), Ht = e(pe), Xt = e(Ht), be = e(Xt), me = r(Xt), fe = e(me), he = r(Ht, 2), Yt = e(he);
              y(
                (_t, ye, xe, ke, we, $e, Ne) => {
                  s(p, _t), s(j, ye), st(N, "src", xe), s(ce, ke), s(ge, we), wt(Jt, d(D).volume_db), s(be, $e), s(fe, Ne), Pe(Yt, d(D).loop);
                },
                [
                  () => (d(D).original_filename || d(D).original_path || d(D).normalized_path).split(/[\\/]/).pop(),
                  () => a("settings.bgm.duration", { duration: Do(d(D).duration_ms) }),
                  () => ee(d(D).normalized_path || d(D).original_path, Date.now()),
                  () => a("settings.bgm.volume"),
                  () => bi(d(D).volume_db),
                  () => a("settings.bgm.loop"),
                  () => a("settings.bgm.loop_sub")
                ]
              ), M("input", Jt, (_t) => t.bgm = Q({ ...t.bgm, volume_db: Ae(Number(_t.target.value)) })), M("change", Yt, (_t) => t.bgm = Q({ ...t.bgm, loop: _t.target.checked })), f(n, c);
            };
            C(Ta, (n) => {
              d(D) ? n(Yr, -1) : n(Xr);
            });
          }
          var Qr = r(Ta, 2), Ba = e(Qr);
          {
            let n = w(I);
            O(Ba, {
              variant: "secondary",
              get disabled() {
                return d(n);
              },
              onclick: Li,
              children: (c, g) => {
                var u = B();
                y((p) => s(u, p), [() => a("settings.bgm.upload")]), f(c, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Zr = r(Ba, 2);
          {
            var ts = (n) => {
              var c = yi(), g = kt(c);
              {
                let p = w(I);
                O(g, {
                  variant: "primary",
                  get disabled() {
                    return d(p);
                  },
                  onclick: Ei,
                  children: (m, j) => {
                    var N = B();
                    y((U) => s(N, U), [() => a("settings.bgm.save")]), f(m, N);
                  },
                  $$slots: { default: !0 }
                });
              }
              var u = r(g, 2);
              {
                let p = w(I);
                O(u, {
                  get disabled() {
                    return d(p);
                  },
                  onclick: Mi,
                  children: (m, j) => {
                    var N = B();
                    y((U) => s(N, U), [() => a("settings.bgm.remove")]), f(m, N);
                  },
                  $$slots: { default: !0 }
                });
              }
              f(n, c);
            };
            C(Zr, (n) => {
              d(D) && n(ts);
            });
          }
          var Oa = r(Fa, 2), za = e(Oa), Va = e(za), es = e(Va), as = r(Va), is = e(as), Ua = r(za, 2), rs = e(Ua), Ia = e(rs), ss = e(Ia), yt = r(Ia, 2), It = e(yt), os = e(It);
          It.value = It.__value = "16:9";
          var de = r(It), ns = e(de);
          de.value = de.__value = "9:16";
          var Da;
          ct(yt);
          var Ga = r(Ua, 2);
          {
            var ls = (n) => {
              var c = sn(), g = kt(c), u = e(g), p = e(u), m = r(u, 2), j = e(m), N = r(g, 2);
              y(
                (U, Y, rt) => {
                  s(p, U), s(j, Y), st(N, "src", rt);
                },
                [
                  () => (d(tt).background_original_filename || d(tt).background_path).split(/[\\/]/).pop(),
                  () => a("settings.render_layout.background_ready"),
                  () => ee(d(tt).background_path, Date.now())
                ]
              ), f(n, c);
            }, vs = (n) => {
              var c = hi(), g = e(c);
              y((u) => s(g, u), [() => a("settings.render_layout.no_background")]), f(n, c);
            };
            C(Ga, (n) => {
              d(tt).background_path ? n(ls) : n(vs, -1);
            });
          }
          var ds = r(Ga, 2), qa = e(ds);
          {
            let n = w(I);
            O(qa, {
              variant: "secondary",
              get disabled() {
                return d(n);
              },
              onclick: Ai,
              children: (c, g) => {
                var u = B();
                y((p) => s(u, p), [() => a("settings.render_layout.upload_background")]), f(c, u);
              },
              $$slots: { default: !0 }
            });
          }
          var Wa = r(qa, 2);
          {
            let n = w(I);
            O(Wa, {
              variant: "primary",
              get disabled() {
                return d(n);
              },
              onclick: Fi,
              children: (c, g) => {
                var u = B();
                y((p) => s(u, p), [() => a("settings.render_layout.save")]), f(c, u);
              },
              $$slots: { default: !0 }
            });
          }
          var _s = r(Wa, 2);
          {
            var cs = (n) => {
              {
                let c = w(I);
                O(n, {
                  get disabled() {
                    return d(c);
                  },
                  onclick: Ri,
                  children: (g, u) => {
                    var p = B();
                    y((m) => s(p, m), [() => a("settings.render_layout.remove_background")]), f(g, p);
                  },
                  $$slots: { default: !0 }
                });
              }
            };
            C(_s, (n) => {
              d(tt).background_path && n(cs);
            });
          }
          var us = r(Oa, 2), Ka = e(us);
          {
            let n = w(I);
            O(Ka, {
              variant: "secondary",
              get disabled() {
                return d(n);
              },
              onclick: () => Ce(!0),
              children: (c, g) => {
                var u = B();
                y((p) => s(u, p), [() => a("settings.reload")]), f(c, u);
              },
              $$slots: { default: !0 }
            });
          }
          var gs = r(Ka, 2);
          {
            let n = w(I);
            O(gs, {
              "data-testid": "save-text-audio",
              variant: "primary",
              get disabled() {
                return d(n);
              },
              onclick: ji,
              children: (c, g) => {
                var u = B();
                y((p) => s(u, p), [() => a("settings.text_audio.save")]), f(c, u);
              },
              $$slots: { default: !0 }
            });
          }
          var ps = r(L, 2), Ja = e(ps), bs = e(Ja), Ha = e(bs), ms = e(Ha), fs = r(Ha), hs = e(fs), ys = r(Ja, 2), Xa = e(ys), xs = e(Xa), Ya = e(xs), ks = e(Ya), xt = r(Ya, 2), Dt = e(xt), ws = e(Dt);
          Dt.value = Dt.__value = "auto";
          var Gt = r(Dt), $s = e(Gt);
          Gt.value = Gt.__value = "zh";
          var qt = r(Gt), Ns = e(qt);
          qt.value = qt.__value = "en";
          var Wt = r(qt), Ss = e(Wt);
          Wt.value = Wt.__value = "ja";
          var _e = r(Wt), Ps = e(_e);
          _e.value = _e.__value = "ko";
          var Qa;
          ct(xt);
          var Za = r(Xa, 2);
          {
            var js = (n) => {
              var c = on(), g = e(c), u = e(g), p = r(g, 2), m = e(p);
              {
                let j = w(I);
                O(m, {
                  variant: "secondary",
                  get disabled() {
                    return d(j);
                  },
                  onclick: () => o().navigate("app_settings"),
                  children: (N, U) => {
                    var Y = B();
                    y((rt) => s(Y, rt), [() => a("settings.translation.go_to_app_settings")]), f(N, Y);
                  },
                  $$slots: { default: !0 }
                });
              }
              y((j) => s(u, j), [() => a("settings.translation.api_key_required")]), f(n, c);
            };
            C(Za, (n) => {
              t.openaiKeyMissing && n(js);
            });
          }
          var ti = r(Za, 2), ei = e(ti), Ls = e(ei), Es = r(ei, 2), ai = e(Es), ii = e(ai), ri = e(ii), Ms = e(ri), As = r(ri), Fs = e(As), Rs = r(ii, 2), si = e(Rs), Cs = r(ai, 2), oi = e(Cs), ni = e(oi), Ts = e(ni), Bs = r(ni), Os = e(Bs), zs = r(oi, 2), li = e(zs), Vs = r(ti, 2), Us = e(Vs);
          {
            let n = w(I);
            O(Us, {
              "data-testid": "run-until-edit",
              variant: "strong",
              get disabled() {
                return d(n);
              },
              onclick: Ti,
              children: (c, g) => {
                var u = B();
                y((p) => s(u, p), [() => a("settings.translation.run_until_edit_auto")]), f(c, u);
              },
              $$slots: { default: !0 }
            });
          }
          y(
            (n, c, g, u, p, m, j, N, U, Y, rt, ce, Kt, ue, ge, Jt, pe, Ht, Xt, be, me, fe, he, Yt, _t, ye, xe, ke, we, $e, Ne, Is, Ds, Gs, qs, Ws, Ks, Js, Hs, Xs, Ys, Qs, Zs, to, eo, ao, io, ro, so, oo, no, lo, vo, _o, co, uo, go, po, bo, mo, fo, ho, yo, xo) => {
              s(H, n), s(X, c), s(W, g), s(lt, u), s(Pt, p), s(Hi, m), Ge !== (Ge = t.subtitle_font) && (ft.value = (ft.__value = t.subtitle_font) ?? "", ut(ft, t.subtitle_font)), s(Yi, j), wt(Qi, N), s(Zi, U), Se(se, 1, `toggle-btn ${t.subtitle_bold ? "active" : ""}`), Se(oe, 1, `toggle-btn ${t.subtitle_italic ? "active" : ""}`), s(ar, Y), s(rr, rt), di(Xe, ce), di(Ye, Kt), s(sr, ue), s(or, ge), s(lr, Jt), s(vr, pe), st(it, "aria-label", Ht), s(dr, `${Xt ?? ""}: ${be ?? ""}`), sa !== (sa = t.voiceLocaleFilter) && (it.value = (it.__value = t.voiceLocaleFilter) ?? "", ut(it, t.voiceLocaleFilter)), st(vt, "aria-label", me), s(cr, `${fe ?? ""}: ${he ?? ""}`), s(ur, Yt), s(gr, _t), oa !== (oa = t.voiceGenderFilter) && (vt.value = (vt.__value = t.voiceGenderFilter) ?? "", ut(vt, t.voiceGenderFilter)), la !== (la = t.tts_voice) && (dt.value = (dt.__value = t.tts_voice) ?? "", ut(dt, t.tts_voice)), s(hr, ye), s(xr, xe), wt(ca, t.speed_multiplier), s(wr, ke), s($r, we), s(Nr, $e), ga !== (ga = t.mix_mode) && (ht.value = (ht.__value = t.mix_mode) ?? "", ut(ht, t.mix_mode)), s(Sr, Ne), s(jr, Is), s(Er, Ds), wt(ya, t.tts_pitch), s(Ar, Gs), s(Rr, qs), wt(wa, t.mix_duck_gain_db), s(Cr, Ws), st(ve, "placeholder", Mt), wt(ve, t.previewText), s(Tr, Ks), s(Br, `${Js ?? ""}: ${d(zi) ?? ""}`), s(Or, `${Hs ?? ""}: ${Xs ?? ""}`), s(zr, `${Ys ?? ""}: ${Qs ?? ""}`), s(Ur, `${Zs ?? ""}: ${d(Vi) ?? ""}`), s(Gr, to), s(Kr, eo), s(Hr, ao), s(es, io), s(is, ro), s(ss, so), s(os, oo), s(ns, no), Da !== (Da = d(tt).aspect_ratio) && (yt.value = (yt.__value = d(tt).aspect_ratio) ?? "", ut(yt, d(tt).aspect_ratio)), s(ms, lo), s(hs, vo), s(ks, _o), s(ws, co), s($s, uo), s(Ns, go), s(Ss, po), s(Ps, bo), Qa !== (Qa = t.source_language) && (xt.value = (xt.__value = t.source_language) ?? "", ut(xt, t.source_language)), s(Ls, mo), s(Ms, fo), s(Fs, ho), Pe(si, t.enable_source_cleanup), s(Ts, yo), s(Os, xo), Pe(li, t.enable_translation_qa);
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
              () => `flex:1;display:grid;align-items:end;background:var(--bg-0);border-radius:14px;padding:28px;text-align:${Go(t.subtitle_align)}`,
              () => `font-family:${qo(t.subtitle_font)};background:${t.bg_enabled ? Wo(t.subtitle_background_color) : "transparent"};font-weight:${t.subtitle_bold ? 800 : 500};font-style:${t.subtitle_italic ? "italic" : "normal"}`,
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
              () => fi(t.speed_multiplier),
              () => a("settings.tts.mix_mode"),
              () => a("settings.tts.mix_replace"),
              () => a("settings.tts.mix_duck"),
              () => a("settings.tts.advanced"),
              () => a("settings.tts.pitch"),
              () => mi(t.tts_pitch),
              () => a("settings.tts.duck_gain"),
              () => bi(t.mix_duck_gain_db),
              () => a("settings.tts.preview_text_label"),
              () => a("settings.tts.preview_title"),
              () => a("settings.tts.voice"),
              () => a("settings.tts.speed"),
              () => fi(t.speed_multiplier),
              () => a("settings.tts.pitch"),
              () => mi(t.tts_pitch),
              () => a("settings.tts.mix_mode"),
              () => a("settings.tts.preview_sub"),
              () => a("settings.bgm.title"),
              () => a("settings.bgm.sub"),
              () => a("settings.render_layout.title"),
              () => a("settings.render_layout.sub"),
              () => a("settings.render_layout.aspect_ratio"),
              () => a("settings.render_layout.aspect_16_9"),
              () => a("settings.render_layout.aspect_9_16"),
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
          ), M("change", ft, (n) => t.subtitle_font = n.target.value), M("click", se, () => t.subtitle_bold = !t.subtitle_bold), M("click", oe, () => t.subtitle_italic = !t.subtitle_italic), M("change", it, (n) => t.voiceLocaleFilter = n.target.value), M("change", vt, (n) => t.voiceGenderFilter = n.target.value), M("change", dt, Ui), M("input", ca, (n) => Ii(Number(n.target.value))), M("change", ht, (n) => t.mix_mode = n.target.value), M("input", ya, (n) => {
            t.tts_pitch = Number(n.target.value), Ft();
          }), M("input", wa, (n) => t.mix_duck_gain_db = Ee(Number(n.target.value))), M("input", ve, (n) => {
            t.previewText = n.target.value, $t(t.previewText), Ft();
          }), M("change", yt, (n) => t.renderLayout = Z({ ...t.renderLayout, aspect_ratio: n.target.value })), M("change", xt, (n) => t.source_language = n.target.value), M("change", si, (n) => t.enable_source_cleanup = n.target.checked), M("change", li, (n) => t.enable_translation_qa = n.target.checked), f(A, F);
        };
        C(x, (A) => {
          t.busyAction === "run_until_edit" ? A(S) : A(et, -1);
        });
      }
      var Nt = r(h, 2);
      {
        var St = (A) => {
          var F = ln(), q = e(F), J = e(q), z = e(J), L = r(J, 2), at = e(L), P = r(L, 2), V = e(P);
          O(V, {
            variant: "secondary",
            onclick: () => {
              t.voiceEditGateOpen = !1, o().navigate("review");
            },
            children: (R, X) => {
              var T = B();
              y((W) => s(T, W), [() => a("settings.voice_edit_gate.pause")]), f(R, T);
            },
            $$slots: { default: !0 }
          });
          var H = r(V, 2);
          O(H, {
            variant: "strong",
            onclick: () => {
              t.voiceEditGateOpen = !1, o().pendingVoiceEditContinue = !0, o().navigate("render");
            },
            children: (R, X) => {
              var T = B();
              y((W) => s(T, W), [() => a("settings.voice_edit_gate.continue")]), f(R, T);
            },
            $$slots: { default: !0 }
          }), y(
            (R, X) => {
              s(z, R), s(at, X);
            },
            [
              () => a("settings.voice_edit_gate.title"),
              () => a("settings.voice_edit_gate.body")
            ]
          ), f(A, F);
        };
        C(Nt, (A) => {
          t.voiceEditGateOpen && A(St);
        });
      }
      f(i, _);
    };
    C(qi, (i) => {
      d(Ki) ? i(Wi) : i(Ji, -1);
    });
  }
  f(l, Ve), So();
}
ko(["change", "click", "input"]);
const wi = Ao(dn), mn = wi.mount, fn = wi.unmount;
export {
  mn as mount,
  fn as unmount
};
//# sourceMappingURL=settings.js.map
