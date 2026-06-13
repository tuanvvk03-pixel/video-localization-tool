var Ji = Object.defineProperty;
var kr = (s) => {
  throw TypeError(s);
};
var Wi = (s, n, d) => n in s ? Ji(s, n, { enumerable: !0, configurable: !0, writable: !0, value: d }) : s[n] = d;
var Sr = (s, n, d) => Wi(s, typeof n != "symbol" ? n + "" : n, d), lt = (s, n, d) => n.has(s) || kr("Cannot " + d);
var Y = (s, n, d) => (lt(s, n, "read from private field"), d ? d.call(s) : n.get(s)), Ee = (s, n, d) => n.has(s) ? kr("Cannot add the same private member more than once") : n instanceof WeakSet ? n.add(s) : n.set(s, d), _t = (s, n, d, r) => (lt(s, n, "write to private field"), r ? r.call(s, d) : n.set(s, d), d), Nr = (s, n, d) => (lt(s, n, "access private method"), d);
import { D as Ki, W as Ui, d as Gi, p as Qi, w as Hi, x as qi, f as ut, i as F, g as i, l as v, a as g, b as Xi, s as Ke, e as W, c as w, h as t, t as h, j as c, u as B, o as q, q as Ce, r as K, P as Ue, z as Yi, K as De, L as Zi, m as V, n as $, A as es, X as ts, V as Ar, k as Mr, Q as rs, R as as } from "./chunks/api-vHpIWCot.js";
import { o as is } from "./chunks/index-client-CjB8cgHo.js";
import { e as ve, i as he } from "./chunks/each-BE197-93.js";
import { b as ss, a as $r } from "./chunks/input-D0G7l_P3.js";
import { b as os } from "./chunks/this-_Wc-LPs7.js";
import { p as ns, B as de } from "./chunks/Button-GpBM5g0S.js";
import { S as vs } from "./chunks/StatusBadge-DT3lodBA.js";
import { P as ds } from "./chunks/ProgressBar-BACn-l7Z.js";
import { s as cs } from "./chunks/screen-DRq5NjFu.js";
var ae, xe, Pe, He, Pr;
const qe = class qe {
  /** @param {ResizeObserverOptions} options */
  constructor(n) {
    Ee(this, He);
    /** */
    Ee(this, ae, /* @__PURE__ */ new WeakMap());
    /** @type {ResizeObserver | undefined} */
    Ee(this, xe);
    /** @type {ResizeObserverOptions} */
    Ee(this, Pe);
    _t(this, Pe, n);
  }
  /**
   * @param {Element} element
   * @param {(entry: ResizeObserverEntry) => any} listener
   */
  observe(n, d) {
    var r = Y(this, ae).get(n) || /* @__PURE__ */ new Set();
    return r.add(d), Y(this, ae).set(n, r), Nr(this, He, Pr).call(this).observe(n, Y(this, Pe)), () => {
      var p = Y(this, ae).get(n);
      p.delete(d), p.size === 0 && (Y(this, ae).delete(n), Y(this, xe).unobserve(n));
    };
  }
};
ae = new WeakMap(), xe = new WeakMap(), Pe = new WeakMap(), He = new WeakSet(), Pr = function() {
  return Y(this, xe) ?? _t(this, xe, new ResizeObserver(
    /** @param {any} entries */
    (n) => {
      for (var d of n) {
        qe.entries.set(d.target, d);
        for (var r of Y(this, ae).get(d.target) || [])
          r(d);
      }
    }
  ));
}, /** @static */
Sr(qe, "entries", /* @__PURE__ */ new WeakMap());
let pt = qe;
var ls = /* @__PURE__ */ new pt({
  box: "border-box"
});
function _s(s, n, d) {
  var r = ls.observe(s, () => d(s[n]));
  Ki(() => (Ui(() => d(s[n])), r));
}
const us = [
  ["#7A1E1E", "#A32626", "#C73535", "#E15757", "#F6B5B5"],
  ["#8A3C10", "#B74B12", "#D96A1D", "#F08D44", "#F8C9A6"],
  ["#8A6B00", "#B58C00", "#D9A700", "#F2C94C", "#FAE7A3"],
  ["#1F6B2D", "#2C8A3D", "#39A84E", "#63C97C", "#B8E6C4"],
  ["#176B6B", "#1C8A8A", "#27A9A9", "#4FCACA", "#AEE8E8"],
  ["#1D4ED8", "#2563EB", "#3B82F6", "#60A5FA", "#BFDBFE"],
  ["#5B3AAE", "#7149D0", "#8A63F0", "#A78BFA", "#D9CCFF"],
  ["#9D2365", "#C0267A", "#E04496", "#F472B6", "#FBC6E3"]
], ps = {
  asr: "🎤",
  ocr: "👁",
  fused_match: "🔀",
  fused_drift: "🔀",
  fused_disagreement: "⚠"
};
function Or() {
  return {
    tts_provider: "edge_tts",
    tts_voice: "vi-VN-HoaiMyNeural",
    speed_multiplier: 1,
    tts_rate: 0,
    tts_pitch: 0,
    mix_mode: "replace_original_speech",
    mix_duck_gain_db: -15
  };
}
function mt(s) {
  return `${Number(s.index) || 0}|${Number(s.start_ms) || 0}|${Number(s.end_ms) || 0}`;
}
function Lr(s) {
  return `${Number(s.start_ms) || 0}|${Number(s.end_ms) || 0}`;
}
function Ge(s) {
  return mt(s);
}
function jr(s) {
  const n = /* @__PURE__ */ new Map(), d = /* @__PURE__ */ new Map(), r = Array.isArray(s) ? s : [];
  for (const p of r)
    n.set(mt(p), p), d.set(Lr(p), p);
  return { byExact: n, byTime: d, list: r };
}
function Br(s, n, d) {
  const r = s.byExact.get(mt(n));
  if (r) return String(r.text || "");
  const p = s.byTime.get(Lr(n));
  if (p) return String(p.text || "");
  const L = s.list[d];
  return L ? String(L.text || "") : "";
}
function ms(s) {
  if (!s || !Array.isArray(s.cues)) return null;
  const n = /* @__PURE__ */ new Map(), d = /* @__PURE__ */ new Map();
  for (const r of s.cues)
    n.set(`${Number(r.start_ms) || 0}|${Number(r.end_ms) || 0}`, r), r.index != null && d.set(Number(r.index), r);
  return { byTime: n, byIndex: d };
}
function bs(s, n, d) {
  return s && (s.byTime.get(`${Number(n.start_ms) || 0}|${Number(n.end_ms) || 0}`) || s.byIndex.get(d + 1)) || null;
}
function gs(s, n, d, r) {
  const p = jr(n), L = jr(d), J = ms(r);
  return (s || []).map((e, E) => {
    const U = bs(J, e, E);
    return {
      index: Number(e.index) || E + 1,
      start_ms: Number(e.start_ms) || 0,
      end_ms: Number(e.end_ms) || 0,
      text: String(e.text || ""),
      source_text: Br(p, e, E),
      reference_text: Br(L, e, E) || String(e.text || ""),
      provenance_source: U?.source || "",
      provenance_needs_review: !!U?.needs_review,
      provenance_asr_text: U?.asr_text || "",
      provenance_ocr_text: U?.ocr_text || "",
      provenance_confidence: Number.isFinite(Number(U?.ocr_confidence)) ? Number(U.ocr_confidence) : null
    };
  });
}
function ye(s) {
  return String(s || "").trim().toLowerCase();
}
function Te(s) {
  return ye(s.text) !== ye(s.reference_text);
}
function fs(s) {
  return String(s || "").split(/\r?\n/).length;
}
function Er(s) {
  const n = Math.max(0, Number(s) || 0), d = Math.floor(n / 36e5), r = Math.floor(n % 36e5 / 6e4), p = Math.floor(n % 6e4 / 1e3), L = Math.floor(n % 1e3);
  return `${String(d).padStart(2, "0")}:${String(r).padStart(2, "0")}:${String(p).padStart(2, "0")}.${String(L).padStart(3, "0")}`;
}
function Qe(s) {
  const n = Math.max(0, Math.floor(Number(s) || 0)), d = Math.floor(n / 3600), r = Math.floor(n % 3600 / 60), p = n % 60;
  return `${String(d).padStart(2, "0")}:${String(r).padStart(2, "0")}:${String(p).padStart(2, "0")}`;
}
function bt(s) {
  const n = String(s || "").trim();
  return /^#(?:[0-9a-f]{6}|[0-9a-f]{8})$/i.test(n) ? n.toUpperCase() : "#000000";
}
function Fe(s) {
  const n = Number(s);
  return Number.isFinite(n) ? Math.max(0.5, Math.min(2, Math.round(n * 100) / 100)) : 1;
}
function we(s) {
  const n = Number(s);
  return Number.isFinite(n) ? Math.max(-30, Math.min(0, Math.round(n * 100) / 100)) : -15;
}
function hs(s) {
  return Math.round((we(s) + 30) / 30 * 100);
}
function ys(s) {
  const n = Math.max(0, Math.min(100, Number(s) || 0));
  return we(-30 + n * 30 / 100);
}
function Cr(s) {
  const n = Or();
  return s && typeof s == "object" && (typeof s.tts_provider == "string" && s.tts_provider && (n.tts_provider = s.tts_provider), typeof s.tts_voice == "string" && s.tts_voice && (n.tts_voice = s.tts_voice), Number.isFinite(Number(s.speed_multiplier)) && (n.speed_multiplier = Fe(Number(s.speed_multiplier))), Number.isFinite(Number(s.tts_rate)) && (n.tts_rate = Number(s.tts_rate)), Number.isFinite(Number(s.tts_pitch)) && (n.tts_pitch = Number(s.tts_pitch)), (s.mix_mode === "duck_original_speech" || s.mix_mode === "replace_original_speech") && (n.mix_mode = s.mix_mode), Number.isFinite(Number(s.mix_duck_gain_db)) && (n.mix_duck_gain_db = we(Number(s.mix_duck_gain_db)))), n;
}
function ws(s) {
  const n = {};
  n.margin_v = Math.max(0, Math.min(500, Math.round(Number(s?.margin_v) || 0)));
  const d = Math.round(Number(s?.font_size) || 0);
  n.font_size = d >= 10 && d <= 120 ? d : null;
  const r = String(s?.subtitle_background_color || "").trim();
  return n.subtitle_background_color = r ? bt(r) : null, n;
}
function Dr(s, n) {
  const d = s || {}, p = Math.max(120, Number(n) || 360) / 1080, L = Math.max(0, Math.min(500, Math.round(Number(d.margin_v) || 0))), J = [`bottom:${Math.round(12 + L * p)}px`], e = Math.round(Number(d.font_size) || 0);
  e >= 10 && e <= 120 && J.push(`font-size:${Math.max(11, Math.round(e * p))}px`);
  const E = String(d.subtitle_background_color || "").trim();
  return E ? J.push(`background-color:${bt(E)}`, "padding:6px 10px", "border-radius:8px") : J.push("background-color:transparent", "padding:0", "border-radius:0"), d.subtitle_font && J.push(`font-family:${d.subtitle_font}, sans-serif`), J.push(`font-weight:${d.bold ? 700 : 800}`), J.push(`font-style:${d.italic ? "italic" : "normal"}`), J.push(`text-align:${d.align === "left" || d.align === "right" ? d.align : "center"}`), J.join(";");
}
function xs(s) {
  return `${Qe(Number(s.start_s) || 0)}–${Qe(Number(s.end_s) || 0)}`;
}
function ks(s) {
  const n = String(s.lifecycle || "").trim();
  return n === "blocked" ? "blocked" : n === "completed" ? "done" : "";
}
var Ss = $('<div class="error-banner"><div class="error-code">UI</div><div class="error-message"> </div></div>'), Ns = $('<div class="card" data-testid="review-empty"><div class="empty-card"><div class="empty-icon">✎</div><h3> </h3><p> </p></div></div>'), As = $('<div class="card" data-testid="review-loading"><div class="empty-card"><div class="empty-icon">…</div><h3> </h3><p> </p></div></div>'), Ms = $('<div class="card review-downstream-progress"><div class="work"><div class="orb"><div class="ring"></div><div class="ring r2"></div><div class="core"></div></div> <h2 class="work-title"> <span class="work-dots"></span></h2> <p class="work-sub"> </p> <div class="work-bar"><!> <div class="work-bar-foot"><span> </span><span> </span></div></div></div></div>'), Tr = $('<div class="info-banner"> </div>'), $s = $('<button type="button"><strong> </strong><span> </span></button>'), js = $('<div class="stack"><div class="segment-rail"></div> <div class="small-muted"> </div></div>'), Bs = $('<button type="button"></button>'), Es = $('<span class="review-clone-chip"><span class="review-clone-chip-name"> <!></span> <button type="button" class="review-clone-chip-x">×</button></span>'), Cs = $('<div class="review-clone-chips"></div>'), Ds = $('<div class="review-upload-row stack"><div class="small-muted"> </div> <div class="small-muted"> </div> <div class="review-upload-controls"><!> <label class="btn secondary"> <input type="file" accept=".srt,text/plain" style="display:none"/></label></div></div>'), Ts = $('<div class="stack" style="gap:12px;padding:16px 0"><div> </div> <!></div>'), Fs = $('<tr><td colspan="6" class="skeleton-row"><!></td></tr>'), Ps = $('<div class="cue-source-wrap"><span> </span><span class="cue-source-text"> </span></div>'), Os = $('<div class="small-muted" style="margin-bottom:6px"> </div>'), Fr = $("<option> </option>"), Ls = $("<optgroup></optgroup>"), Rs = $('<tr><td> </td><td><button type="button" class="review-timecode"> </button></td><td class="cue-source"><!></td><td><!> <textarea class="cue-textarea"></textarea></td><td class="cue-voice-cell"><select class="input cue-voice-select"><option> </option><!><!></select></td><td class="cue-status-cell"><!></td></tr>'), zs = $('<audio controls="" autoplay="" class="review-demo-audio"></audio>'), Is = $('<div class="error-banner"> </div>'), Vs = $('<div class="screen stack" data-testid="review-screen"><!> <!> <div> </div> <!> <div class="review-layout"><div class="stack"><div class="player"><div class="player-screen"><video class="review-video" controls="" preload="metadata"></video> <div class="subtitle-overlay"> </div></div> <div class="controls"><span> </span> <div class="timeline"><div class="bar"></div></div> <span> </span> <span class="tag"> </span></div></div> <div class="card review-burn-card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="small-muted"> </div> <label class="checkbox-row"><input type="checkbox"/> </label> <div class="scroll-region--palette"><div class="tone-grid"></div></div> <div class="field"><label> </label> <input class="input" type="text" placeholder="#000000"/></div> <div class="field"><label> </label> <input class="input" type="number" min="0" max="500" step="2"/> <div class="small-muted"> </div></div> <div class="field"><label> </label> <input class="input" type="number" min="0" max="120" step="1"/> <div class="small-muted"> </div></div> <div class="toolbar"><!></div></div></div></div> <div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body review-editor"><div class="toolbar review-toolbar"><input class="input review-search" type="text"/> <label class="checkbox-row"><input type="checkbox"/> </label> <label class="checkbox-row"><input type="checkbox"/> </label></div> <div class="review-clone-row stack"><div class="review-clone-head"><div class="small-muted"> </div> <!></div> <!></div> <!> <div class="review-table-wrap"><table class="review-table"><thead><tr><th> </th><th> </th><th> </th><th> </th><th> </th><th> </th></tr></thead><tbody><!></tbody></table></div> <div class="sticky-bar"><div><div class="sticky-title"> </div> <div class="small-muted"> </div></div> <div class="actions"><!> <!></div></div></div></div></div> <div class="card" data-review-card="demo"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body review-demo-body"><div class="review-demo-thumb"><div class="review-demo-frame"><video class="review-demo-video" preload="metadata" playsinline=""></video> <div class="review-demo-overlay"> </div></div> <div class="small-muted"> </div></div> <div class="review-demo-controls stack"><div class="toolbar"><!> <!></div> <div class="small-muted"> </div> <div class="stack review-duck-slider"><div class="review-duck-label"><strong> </strong><span class="review-duck-value"> </span></div> <input type="range" min="0" max="100" step="1" class="review-duck-range"/> <div class="small-muted"> </div></div> <!> <!></div></div></div></div>', 2), Js = $("<!> <!>", 1);
function Ws(s, n) {
  Qi(n, !0);
  let d = ns(n, "ctx", 7);
  const r = (a, o) => (d()?.t ?? ((_) => _))(a, o), p = () => String(d()?.jobWorkspace || ""), L = () => String(d()?.parentProjectRoot || "");
  function J() {
    return {
      loadedJobWorkspace: "",
      loading: !1,
      busyAction: "",
      notice: "",
      cues: [],
      segments: [],
      isLongVideo: !1,
      sourceDurationS: 0,
      status: null,
      progress: null,
      searchQuery: "",
      changedOnly: !1,
      pendingOnly: !1,
      ttsSettings: Or(),
      styleSettings: {},
      demoBusy: !1,
      demoNotice: "",
      demoError: "",
      demoAudioRel: "",
      demoAudioBust: 0,
      downstreamLive: null,
      transcriptionEngine: "",
      externalSrtOrigin: "",
      voiceCatalog: [],
      voiceOverrides: {},
      overridesDirty: !1,
      voiceSamples: [],
      sampleBusy: !1
    };
  }
  let e = Hi(d()?.reviewState || J());
  d() && (d().reviewState = e);
  let E = Ke(""), U = Ke(0), gt = Ke(360), R = Ke(void 0), ke = null, ce = null, le = null;
  is(() => {
    ke && clearInterval(ke), ce && clearInterval(ce), le && clearTimeout(le);
  });
  const Xe = () => !!e.busyAction, Ye = () => d()?.importConfig?.use_auto_translate !== !1;
  function Oe(a, o) {
    if (!p()) return "";
    const _ = new URLSearchParams({ workspace: p(), rel: a });
    return o && _.set("v", String(o)), `/media?${_.toString()}`;
  }
  function Se(a) {
    return a instanceof es ? a.summary || a.message : a?.message || r("error.generic");
  }
  async function ft(a = !1) {
    if (p()) {
      if (!a && e.loadedJobWorkspace === p() && e.cues.length) {
        ht();
        return;
      }
      e.loading = !0, e.notice = "", W(E, "");
      try {
        const [
          o,
          _,
          x,
          z,
          Z,
          G,
          oe,
          ee,
          Re,
          ue,
          Ae
        ] = await Promise.all([
          w("/api/status", { job_workspace: p() }),
          w("/api/load", { job_workspace: p() }),
          w("/api/job-progress", { job_workspace: p() }),
          w("/api/list-segments", { job_workspace: p() }),
          w("/api/get-video-tts", { job_workspace: p() }).catch(() => ({ settings: {} })),
          L() ? w("/api/get-project-tts", { project_root: L() }).catch(() => ({ settings: {} })) : Promise.resolve({ settings: {} }),
          w("/api/get-video-style", { job_workspace: p() }).catch(() => ({ style: {} })),
          L() ? w("/api/get-project-style", { project_root: L() }).catch(() => ({ style: {} })) : Promise.resolve({ style: {} }),
          w("/api/list-voices", {}).catch(() => ({ voices: [] })),
          w("/api/get-voice-overrides", { job_workspace: p() }).catch(() => ({ overrides: {} })),
          w("/api/voice-samples/list", { job_workspace: p() }).catch(() => ({ samples: [] }))
        ]), ze = { ...ee.style || {}, ...oe.style || {} }, Me = { ...G.settings || {}, ...Z.settings || {} }, pe = gs(_.cues || [], _.source_cues || [], _.reference_cues || [], _.source_provenance || null).map((te) => ({ ...te, _dirty: !1 }));
        Object.assign(e, {
          loadedJobWorkspace: p(),
          loading: !1,
          cues: pe,
          segments: Array.isArray(z.segments) ? z.segments : [],
          isLongVideo: !!z.is_long_video,
          sourceDurationS: Number(z.source_duration_s) || 0,
          status: o,
          progress: x,
          notice: "",
          ttsSettings: Cr(Me),
          styleSettings: ze,
          demoNotice: "",
          demoError: "",
          demoAudioRel: "",
          demoAudioBust: 0,
          transcriptionEngine: String(o.transcription_engine || ""),
          externalSrtOrigin: o.external_srt_origin != null ? String(o.external_srt_origin) : "",
          voiceCatalog: Array.isArray(Re.voices) ? Re.voices.filter((te) => te && te.voice_id && te.enabled !== !1) : [],
          voiceOverrides: ue && typeof ue.overrides == "object" && ue.overrides || {},
          overridesDirty: !1,
          voiceSamples: Array.isArray(Ae.samples) ? Ae.samples : []
        }), d().applyJobStatusToEditGate?.(d(), o), ht();
      } catch (o) {
        e.loading = !1, W(E, Se(o), !0);
      }
    }
  }
  function ht() {
    ke && clearInterval(ke), ke = setInterval(
      async () => {
        if (!(!d() || e.busyAction))
          try {
            const [a, o] = await Promise.all([
              w("/api/status", { job_workspace: p() }),
              w("/api/job-progress", { job_workspace: p() })
            ]);
            e.status = a, e.progress = o;
          } catch {
          }
      },
      3e3
    );
  }
  async function Le(a, o) {
    if (d()) {
      W(E, ""), e.busyAction = a, e.notice = "";
      try {
        await o();
      } catch (_) {
        W(E, Se(_), !0);
      } finally {
        d() && (e.busyAction = "");
      }
    }
  }
  const ie = B(() => !!(e.status?.voice_edited || e.status?.voice_edit_status === "voice_edited")), se = B(() => {
    const a = Math.floor(i(U) * 1e3);
    return e.cues.find((o) => o.start_ms <= a && a < o.end_ms) || null;
  }), yt = B(() => i(se) ? Ge(i(se)) : ""), zr = B(() => i(se) ? Ye() ? i(se).text || r("review.player.no_active_cue") : (i(se).text || "").trim() ? i(se).text : i(se).source_text || r("review.player.no_active_cue") : r("review.player.no_active_cue")), Ir = B(() => Dr(e.styleSettings, i(gt))), _e = B(() => e.cues.filter((a) => a._dirty).length), Ze = B(() => e.cues.filter((a) => Te(a)).length), wt = B(() => {
    const a = ye(e.searchQuery);
    return e.cues.filter((o) => e.changedOnly && !Te(o) || e.pendingOnly && !o._dirty && !Te(o) ? !1 : a ? ye(o.source_text).includes(a) || ye(o.text).includes(a) || ye(o.reference_text).includes(a) : !0);
  }), et = B(() => Number(i(R)?.duration) || e.sourceDurationS || 0);
  function Vr(a) {
    return a._dirty ? { kind: "blocked", text: r("review.status.unsaved") } : Ge(a) === i(yt) ? { kind: "running", text: r("review.status.current") } : i(ie) ? { kind: "completed", text: r("review.status.approved") } : Te(a) ? { kind: "blocked", text: r("review.status.changed") } : { kind: "queued", text: r("review.status.pending") };
  }
  function Jr(a) {
    i(R) && (i(R).currentTime = Math.max(0, a.start_ms / 1e3), i(R).focus());
  }
  function Wr(a) {
    i(R) && (i(R).currentTime = Math.max(0, Number(a.start_s) || 0), i(R).focus());
  }
  function Kr(a, o) {
    a.text = o, a._dirty = !0;
  }
  function Ur(a) {
    const o = e.voiceOverrides?.[String(a.index)];
    if (!o || typeof o != "object") return "";
    const _ = String(o.voice_id || "");
    return _ ? String(o.provider || "") === "xtts" ? `xtts:${_}` : _ : "";
  }
  function Gr(a, o) {
    const _ = String(a.index), x = { ...e.voiceOverrides || {} }, z = x[_] || {};
    if (!o)
      delete x[_];
    else if (o.startsWith("xtts:"))
      x[_] = { ...z, provider: "xtts", voice_id: o.slice(5) };
    else {
      const { provider: Z, ...G } = z;
      x[_] = { ...G, voice_id: o };
    }
    e.voiceOverrides = x, e.overridesDirty = !0;
  }
  async function Qr() {
    if (!e.sampleBusy) {
      e.sampleBusy = !0, W(E, "");
      try {
        const a = await ts([
          "Audio files (*.wav;*.mp3;*.m4a;*.aac;*.flac;*.ogg)",
          "All files (*.*)"
        ]);
        if (a?.cancelled) return;
        if (!a?.ok || !a.path) throw new Error(a?.error || r("review.sample_pick_unavailable"));
        const o = await w("/api/voice-samples/upload", { job_workspace: p(), sample_path: a.path });
        e.voiceSamples = Array.isArray(o.samples) ? o.samples : e.voiceSamples, e.notice = r("review.sample_uploaded");
      } catch (a) {
        W(E, Se(a), !0);
      } finally {
        e.sampleBusy = !1;
      }
    }
  }
  async function Hr(a) {
    if (!(e.sampleBusy || !window.confirm(r("review.sample_confirm_remove")))) {
      e.sampleBusy = !0, W(E, "");
      try {
        const o = await w("/api/voice-samples/remove", { job_workspace: p(), id: a });
        e.voiceSamples = Array.isArray(o.samples) ? o.samples : [];
      } catch (o) {
        W(E, Se(o), !0);
      } finally {
        e.sampleBusy = !1;
      }
    }
  }
  async function xt() {
    const a = await w("/api/save-voice-overrides", { job_workspace: p(), overrides: e.voiceOverrides || {} });
    e.voiceOverrides = a && a.overrides || {}, e.overridesDirty = !1;
  }
  function qr(a) {
    if (a.key === " " && i(R)) {
      a.preventDefault(), i(R).paused ? i(R).play().catch(() => {
      }) : i(R).pause();
      return;
    }
    a.key === "Escape" && (a.preventDefault(), a.currentTarget.blur());
  }
  function Ne(a) {
    const o = { ...e.styleSettings || {} };
    for (const [_, x] of Object.entries(a))
      x === void 0 ? delete o[_] : o[_] = x;
    e.styleSettings = o;
  }
  const Xr = () => Le("save_burn_style", async () => {
    const a = await w("/api/save-video-style", {
      job_workspace: p(),
      style: ws(e.styleSettings || {})
    });
    e.notice = r("review.burn_saved_notice", { path: a?.path != null ? String(a.path) : "" });
  }), kt = () => e.cues.map((a) => ({
    index: a.index,
    start_ms: a.start_ms,
    end_ms: a.end_ms,
    text: a.text
  })), Yr = () => Le("save_draft", async () => {
    await w("/api/save", {
      job_workspace: p(),
      cues: kt(),
      note: "desktop_review_save"
    }), e.cues.forEach((o) => o._dirty = !1), await xt();
    const a = await w("/api/status", { job_workspace: p() });
    e.status = a, e.notice = r("review.notice_saved"), d().applyJobStatusToEditGate?.(d(), a);
  });
  async function Zr(a) {
    await Le("upload_translation_srt", async () => {
      const o = await a.text(), _ = await w("/api/upload-translation", { job_workspace: p(), srt_text: o });
      e.status = _, d().applyJobStatusToEditGate?.(d(), _), e.notice = r("review.notice_uploaded"), await ft(!0);
    });
  }
  function ea(a) {
    const o = a.target, _ = o.files && o.files[0];
    o.value = "", _ && Zr(_);
  }
  function ta() {
    const a = Oe("artifacts/transcribe/source.srt");
    if (!a) return;
    const o = document.createElement("a");
    o.href = a, o.download = "source.srt", o.rel = "noopener", o.style.display = "none", document.body.appendChild(o), o.click(), o.remove();
  }
  function ra() {
    if (d()?.parentProject) return String(d().parentProject);
    const o = p().replace(/[\\/]+$/, "").split(/[\\/]/);
    return o[o.length - 1] || "job";
  }
  function St(a) {
    const o = e.ttsSettings, _ = d()?.settingsState || {}, x = _.loadedJobWorkspace === p();
    return {
      job_workspace: p(),
      project_name: ra(),
      project_root: L(),
      to_stage: a,
      subtitle_mode: x ? String(_.renderSubtitleMode || "burn") : "burn",
      tts_provider: x && _.tts_provider ? String(_.tts_provider) : o.tts_provider || "edge_tts",
      tts_voice: x && _.tts_voice ? String(_.tts_voice) : o.tts_voice || "",
      tts_rate: x && Number.isFinite(Number(_.tts_rate)) ? Number(_.tts_rate) : Number(o.tts_rate) || 0,
      mix_mode: x && _.mix_mode ? String(_.mix_mode) : o.mix_mode || "replace_original_speech",
      mix_duck_gain_db: x && Number.isFinite(Number(_.mix_duck_gain_db)) ? Number(_.mix_duck_gain_db) : Number.isFinite(Number(o.mix_duck_gain_db)) ? Number(o.mix_duck_gain_db) : -15
    };
  }
  function aa() {
    !d() || e.busyAction !== "approve_downstream" || w("/api/job-progress", { job_workspace: p() }).then((a) => {
      e.busyAction === "approve_downstream" && (e.downstreamLive = {
        ...e.downstreamLive || {},
        overall_percent: Number(a.overall_percent) || 0,
        current_stage_label: String(a.current_stage_label || ""),
        current_stage: String(a.current_stage || ""),
        lifecycle: String(a.lifecycle || "")
      });
    }).catch(() => {
    });
  }
  async function ia() {
    if (e.busyAction) return;
    let a = null;
    if (await Le("approve_save", async () => {
      i(_e) > 0 && (await w("/api/save", {
        job_workspace: p(),
        cues: kt(),
        note: "desktop_review_approve_save"
      }), e.cues.forEach((_) => _._dirty = !1)), await xt(), a = await w("/api/mark-edited", { job_workspace: p() }), e.status = a, e.notice = r("review.notice_approved");
    }), !a) return;
    d().applyJobStatusToEditGate?.(d(), a);
    let o = !1;
    e.busyAction = "approve_downstream", e.downstreamLive = {
      phase: "tts",
      overall_percent: 0,
      current_stage_label: "",
      current_stage: "",
      lifecycle: ""
    }, ce = setInterval(aa, 900);
    try {
      await Ar(p(), await w("/api/run-after-edit", { ...St("tts_generated"), async: !0 })), e.downstreamLive = { ...e.downstreamLive || {}, phase: "render" }, await Ar(p(), await w("/api/run-after-edit", { ...St("rendered"), async: !0 }));
      const _ = await w("/api/status", { job_workspace: p() });
      d().applyJobStatusToEditGate?.(d(), _), e.notice = r("review.notice_downstream_done"), o = !0;
    } catch (_) {
      W(E, Se(_), !0);
    } finally {
      ce && (clearInterval(ce), ce = null), e.busyAction = "", e.downstreamLive = null;
    }
    o && d().navigate("render");
  }
  const Nt = B(() => e.ttsSettings.mix_mode === "duck_original_speech"), At = B(() => hs(e.ttsSettings.mix_duck_gain_db));
  function sa(a) {
    e.ttsSettings.mix_duck_gain_db = ys(a), e.demoNotice = "", e.demoError = "", le && clearTimeout(le), le = setTimeout(
      () => {
        le = null, oa();
      },
      350
    );
  }
  async function oa() {
    const a = e.ttsSettings;
    try {
      const o = await w("/api/save-video-tts", {
        job_workspace: p(),
        settings: {
          tts_provider: a.tts_provider,
          tts_voice: (a.tts_voice || "").trim(),
          speed_multiplier: Fe(a.speed_multiplier),
          tts_rate: Math.max(-50, Math.min(50, Math.round((Fe(a.speed_multiplier) - 1) * 100))),
          tts_pitch: Number(a.tts_pitch) || 0,
          mix_mode: a.mix_mode,
          mix_duck_gain_db: we(a.mix_duck_gain_db)
        }
      });
      e.ttsSettings = Cr(o?.settings || a), e.demoError = "", e.demoNotice = r("review.demo_save_ok", { db: we(e.ttsSettings.mix_duck_gain_db).toFixed(1) });
    } catch (o) {
      e.demoError = o?.message || r("review.demo_save_failed");
    }
  }
  async function na() {
    const a = e.ttsSettings;
    e.demoBusy = !0, e.demoError = "", e.demoNotice = "";
    try {
      const o = await w("/api/tts-preview", {
        job_workspace: p(),
        tts_provider: a.tts_provider,
        tts_voice: (a.tts_voice || "").trim(),
        speed_multiplier: Fe(a.speed_multiplier),
        text: r("review.demo_sample_text")
      });
      e.demoAudioRel = o?.rel_path || "", e.demoAudioBust = Number(o?.cache_bust) || Date.now(), e.demoNotice = r("review.demo_play_ready");
    } catch (o) {
      e.demoError = o?.message || r("review.demo_play_failed");
    } finally {
      e.demoBusy = !1;
    }
  }
  const Mt = B(() => !!String(e.styleSettings?.subtitle_background_color || "").trim());
  qi(() => {
    p(), ft();
  });
  var $t = Js(), jt = ut($t);
  {
    var va = (a) => {
      var o = Ss(), _ = v(t(o)), x = t(_);
      h(() => c(x, i(E))), g(a, o);
    };
    F(jt, (a) => {
      i(E) && a(va);
    });
  }
  var da = v(jt, 2);
  {
    var ca = (a) => {
      var o = Ns(), _ = t(o), x = v(t(_)), z = t(x), Z = v(x), G = t(Z);
      h(
        (oe, ee) => {
          c(z, oe), c(G, ee);
        },
        [() => r("review.empty_title"), () => r("review.empty_body")]
      ), g(a, o);
    }, la = B(() => !p()), _a = (a) => {
      var o = As(), _ = t(o), x = v(t(_)), z = t(x), Z = v(x), G = t(Z);
      h(
        (oe, ee) => {
          c(z, oe), c(G, ee);
        },
        [() => r("review.loading_title"), () => r("common.loading")]
      ), g(a, o);
    }, ua = (a) => {
      var o = Vs(), _ = t(o);
      {
        var x = (l) => {
          const u = B(() => e.downstreamLive), b = B(() => Math.max(0, Math.min(100, Number(i(u).overall_percent) || 0)));
          var f = Ms(), m = t(f), S = v(t(m), 2), y = t(S), N = v(S, 2), T = t(N), D = v(N, 2), C = t(D);
          ds(C, {
            get percent() {
              return i(b);
            },
            wide: !0
          });
          var j = v(C, 2), P = t(j), O = t(P), Q = v(P), $e = t(Q);
          h(
            (me, be, je, Be) => {
              c(y, me), c(T, be), c(O, je), c($e, `${Be ?? ""}%`);
            },
            [
              () => i(u).phase === "render" ? r("review.downstream.phase_render") : r("review.downstream.phase_tts"),
              () => i(u).current_stage_label || (i(u).phase === "render" ? r("review.downstream.render_waiting") : r("review.downstream.tts_waiting")),
              () => r("review.downstream.progress_percent", { percent: Math.round(i(b)) }),
              () => Math.round(i(b))
            ]
          ), g(l, f);
        };
        F(_, (l) => {
          e.busyAction === "approve_downstream" && e.downstreamLive && l(x);
        });
      }
      var z = v(_, 2);
      {
        var Z = (l) => {
          var u = Tr(), b = t(u);
          h(() => c(b, e.notice)), g(l, u);
        };
        F(z, (l) => {
          e.notice && l(Z);
        });
      }
      var G = v(z, 2), oe = t(G), ee = v(G, 2);
      {
        var Re = (l) => {
          var u = js(), b = t(u);
          ve(b, 21, () => e.segments, he, (S, y) => {
            var N = $s(), T = t(N), D = t(T), C = v(T), j = t(C);
            h(
              (P, O, Q) => {
                Ce(N, 1, `segment ${P ?? ""}`), c(D, O), c(j, Q);
              },
              [
                () => ks(i(y)),
                () => r("review.segment.label", { index: i(y).index || 0 }),
                () => xs(i(y))
              ]
            ), V("click", N, () => Wr(i(y))), g(S, N);
          });
          var f = v(b, 2), m = t(f);
          h((S) => c(m, S), [() => r("review.segment.note")]), g(l, u);
        };
        F(ee, (l) => {
          e.isLongVideo && l(Re);
        });
      }
      var ue = v(ee, 2), Ae = t(ue), ze = t(Ae), Me = t(ze), pe = t(Me);
      os(pe, (l) => W(R, l), () => i(R));
      var te = v(pe, 2), pa = t(te), ma = v(Me, 2), Bt = t(ma), ba = t(Bt), Et = v(Bt, 2), ga = t(Et), Ct = v(Et, 2), fa = t(Ct), ha = v(Ct, 2), ya = t(ha), wa = v(ze, 2), Dt = t(wa), xa = t(Dt), Tt = t(xa), ka = t(Tt), Sa = v(Tt), Na = t(Sa), Aa = v(Dt, 2), Ft = t(Aa), Ma = t(Ft), Pt = v(Ft, 2), tt = t(Pt), $a = v(tt), Ot = v(Pt, 2), ja = t(Ot);
      ve(ja, 21, () => us, he, (l, u) => {
        var b = Mr(), f = ut(b);
        ve(f, 17, () => i(u), he, (m, S) => {
          var y = Bs();
          h(
            (N) => {
              Ce(y, 1, `color-swatch ${N ?? ""}`), K(y, "title", i(S)), Ue(y, `background:${i(S)}`), K(y, "aria-label", i(S));
            },
            [
              () => i(Mt) && bt(String(e.styleSettings?.subtitle_background_color || "")) === i(S) ? "active" : ""
            ]
          ), V("click", y, () => Ne({ subtitle_background_color: i(S) })), g(m, y);
        }), g(l, b);
      });
      var Lt = v(Ot, 2), Rt = t(Lt), Ba = t(Rt), zt = v(Rt, 2), It = v(Lt, 2), Vt = t(It), Ea = t(Vt), rt = v(Vt, 2), Ca = v(rt, 2), Da = t(Ca), Jt = v(It, 2), Wt = t(Jt), Ta = t(Wt), at = v(Wt, 2), Fa = v(at, 2), Pa = t(Fa), Oa = v(Jt, 2), La = t(Oa);
      {
        let l = B(Xe);
        de(La, {
          "data-testid": "review-save-burn",
          variant: "primary",
          get disabled() {
            return i(l);
          },
          onclick: Xr,
          children: (u, b) => {
            var f = q();
            h((m) => c(f, m), [() => r("review.burn_save")]), g(u, f);
          },
          $$slots: { default: !0 }
        });
      }
      var Ra = v(Ae, 2), Kt = t(Ra), za = t(Kt), Ut = t(za), Ia = t(Ut), Va = v(Ut), Ja = t(Va), Wa = v(Kt, 2), Gt = t(Wa), it = t(Gt), Qt = v(it, 2), Ht = t(Qt), Ka = v(Ht, 1, !0), Ua = v(Qt, 2), qt = t(Ua), Ga = v(qt, 1, !0), Xt = v(Gt, 2), Yt = t(Xt), Zt = t(Yt), Qa = t(Zt), Ha = v(Zt, 2);
      de(Ha, {
        "data-testid": "review-upload-sample",
        get disabled() {
          return e.sampleBusy;
        },
        onclick: Qr,
        children: (l, u) => {
          var b = q();
          h((f) => c(b, f), [
            () => e.sampleBusy ? r("common.loading") : r("review.btn.upload_sample")
          ]), g(l, b);
        },
        $$slots: { default: !0 }
      });
      var qa = v(Yt, 2);
      {
        var Xa = (l) => {
          var u = Cs();
          ve(u, 21, () => e.voiceSamples, he, (b, f) => {
            var m = Es(), S = t(m), y = t(S), N = v(y);
            {
              var T = (C) => {
                var j = q();
                h((P) => c(j, `· ${P ?? ""}s`), [() => (i(f).duration_ms / 1e3).toFixed(1)]), g(C, j);
              };
              F(N, (C) => {
                i(f).duration_ms && C(T);
              });
            }
            var D = v(S, 2);
            h(
              (C, j) => {
                K(S, "title", i(f).path), c(y, i(f).id), D.disabled = e.sampleBusy, K(D, "title", C), K(D, "aria-label", j);
              },
              [
                () => r("review.btn.remove_sample"),
                () => r("review.btn.remove_sample")
              ]
            ), V("click", D, () => Hr(i(f).id)), g(b, m);
          }), g(l, u);
        };
        F(qa, (l) => {
          e.voiceSamples.length && l(Xa);
        });
      }
      var er = v(Xt, 2);
      {
        var Ya = (l) => {
          var u = Ds(), b = t(u), f = t(b), m = v(b, 2), S = t(m), y = v(m, 2), N = t(y);
          de(N, {
            onclick: ta,
            children: (j, P) => {
              var O = q();
              h((Q) => c(O, Q), [() => r("review.btn.download_source_srt")]), g(j, O);
            },
            $$slots: { default: !0 }
          });
          var T = v(N, 2), D = t(T), C = v(D);
          h(
            (j, P, O) => {
              c(f, j), c(S, P), c(D, O);
            },
            [
              () => r("review.upload_srt_hint"),
              () => r("review.download_source_hint"),
              () => r("review.btn.upload_srt")
            ]
          ), V("change", C, ea), g(l, u);
        };
        F(er, (l) => {
          i(ie) || l(Ya);
        });
      }
      var tr = v(er, 2), Za = t(tr), rr = t(Za), ei = t(rr), ar = t(ei), ti = t(ar), ir = v(ar), ri = t(ir), sr = v(ir), ai = t(sr), or = v(sr), ii = t(or), nr = v(or), si = t(nr), oi = v(nr), ni = t(oi), vi = v(rr), di = t(vi);
      {
        var ci = (l) => {
          var u = Fs(), b = t(u), f = t(b);
          {
            var m = (y) => {
              var N = Ts(), T = t(N), D = t(T), C = v(T, 2);
              de(C, {
                variant: "secondary",
                onclick: () => d().navigate("settings"),
                children: (j, P) => {
                  var O = q();
                  h((Q) => c(O, Q), [() => r("review.goto_settings")]), g(j, O);
                },
                $$slots: { default: !0 }
              }), h((j) => c(D, j), [() => r("review.empty_no_cues")]), g(y, N);
            }, S = (y) => {
              var N = q();
              h((T) => c(N, T), [() => r("review.empty_filtered")]), g(y, N);
            };
            F(f, (y) => {
              e.cues.length === 0 ? y(m) : y(S, -1);
            });
          }
          g(l, u);
        }, li = (l) => {
          var u = Mr(), b = ut(u);
          ve(b, 17, () => i(wt), (f) => Ge(f), (f, m) => {
            const S = B(() => Vr(i(m)));
            var y = Rs(), N = t(y), T = t(N), D = v(N), C = t(D), j = t(C), P = v(D), O = t(P);
            {
              var Q = (k) => {
                var A = Ps(), M = t(A), H = t(M), I = v(M), ne = t(I);
                h(
                  (X) => {
                    Ce(M, 1, `provenance-badge provenance-${i(m).provenance_source ?? ""}`), K(M, "title", X), c(H, ps[i(m).provenance_source] || "?"), c(ne, i(m).source_text || "—");
                  },
                  [() => r(`review.provenance.${i(m).provenance_source}`)]
                ), g(k, A);
              }, $e = (k) => {
                var A = q();
                h(() => c(A, i(m).source_text || "—")), g(k, A);
              };
              F(O, (k) => {
                i(m).provenance_source ? k(Q) : k($e, -1);
              });
            }
            var me = v(P), be = t(me);
            {
              var je = (k) => {
                var A = Os(), M = t(A);
                h(() => c(M, i(m).source_text)), g(k, A);
              }, Be = B(() => !Ye() && (i(m).source_text || "").trim());
              F(be, (k) => {
                i(Be) && k(je);
              });
            }
            var ge = v(be, 2), Ve = v(me), re = t(Ve), fe = t(re), ot = t(fe);
            fe.value = fe.__value = "";
            var Je = v(fe);
            {
              var nt = (k) => {
                var A = Ls();
                ve(A, 21, () => e.voiceSamples, he, (M, H) => {
                  var I = Fr(), ne = t(I), X = {};
                  h(() => {
                    c(ne, i(H).id), X !== (X = `xtts:${i(H).path}`) && (I.value = I.__value = `xtts:${i(H).path}`);
                  }), g(M, I);
                }), h((M) => K(A, "label", M), [() => r("review.cue_voice_clone_group")]), g(k, A);
              };
              F(Je, (k) => {
                e.voiceSamples.length && k(nt);
              });
            }
            var vt = v(Je);
            ve(vt, 17, () => e.voiceCatalog, he, (k, A) => {
              var M = Fr(), H = t(M), I = {};
              h(() => {
                c(H, i(A).short_name || i(A).label || i(A).voice_id), I !== (I = i(A).voice_id) && (M.value = (M.__value = i(A).voice_id) ?? "");
              }), g(k, M);
            });
            var We;
            rs(re);
            var dt = v(Ve), ct = t(dt);
            vs(ct, {
              get kind() {
                return i(S).kind;
              },
              children: (k, A) => {
                var M = q();
                h(() => c(M, i(S).text)), g(k, M);
              },
              $$slots: { default: !0 }
            }), h(
              (k, A, M, H, I, ne, X) => {
                Ce(y, 1, `cue-row ${k ?? ""} ${i(m)._dirty ? "dirty" : ""} ${A ?? ""} ${i(m).provenance_needs_review ? "needs-review" : ""}`), c(T, i(m).index), c(j, `${M ?? ""} → ${H ?? ""}`), K(ge, "rows", I), De(ge, i(m).text), c(ot, ne), We !== (We = X) && (re.value = (re.__value = X) ?? "", as(re, X));
              },
              [
                () => Te(i(m)) ? "changed" : "",
                () => Ge(i(m)) === i(yt) ? "active" : "",
                () => Er(i(m).start_ms),
                () => Er(i(m).end_ms),
                () => Math.max(2, Math.min(5, fs(i(m).text))),
                () => r("review.cue_voice_shared"),
                () => Ur(i(m))
              ]
            ), V("click", C, () => Jr(i(m))), V("input", ge, (k) => Kr(i(m), k.target.value)), V("keydown", ge, qr), V("change", re, (k) => Gr(i(m), k.currentTarget.value)), g(f, y);
          }), g(l, u);
        };
        F(di, (l) => {
          i(wt).length ? l(li, -1) : l(ci);
        });
      }
      var _i = v(tr, 2), vr = t(_i), dr = t(vr), ui = t(dr), pi = v(dr, 2), mi = t(pi), bi = v(vr, 2), cr = t(bi);
      {
        let l = B(() => Xe() || i(_e) === 0 && !e.overridesDirty);
        de(cr, {
          "data-testid": "review-save-draft",
          variant: "secondary",
          get disabled() {
            return i(l);
          },
          onclick: Yr,
          children: (u, b) => {
            var f = q();
            h((m) => c(f, m), [() => r("review.btn.save_draft")]), g(u, f);
          },
          $$slots: { default: !0 }
        });
      }
      var gi = v(cr, 2);
      {
        let l = B(() => Xe() || e.cues.length === 0 || i(ie) && i(_e) === 0);
        de(gi, {
          "data-testid": "review-approve",
          variant: "strong",
          get disabled() {
            return i(l);
          },
          onclick: ia,
          children: (u, b) => {
            var f = q();
            h((m) => c(f, m), [() => r("review.btn.approve_confirm_voice")]), g(u, f);
          },
          $$slots: { default: !0 }
        });
      }
      var fi = v(ue, 2), lr = t(fi), hi = t(lr), _r = t(hi), yi = t(_r), wi = v(_r), xi = t(wi), ki = v(lr, 2), ur = t(ki), pr = t(ur), st = t(pr);
      st.muted = !0;
      var mr = v(st, 2), Si = t(mr), Ni = v(pr, 2), Ai = t(Ni), Mi = v(ur, 2), br = t(Mi), gr = t(br);
      de(gr, {
        "data-testid": "review-demo-play",
        variant: "primary",
        get disabled() {
          return e.demoBusy;
        },
        onclick: na,
        children: (l, u) => {
          var b = q();
          h((f) => c(b, f), [
            () => e.demoBusy ? r("review.demo_playing") : r("review.demo_play_voice")
          ]), g(l, b);
        },
        $$slots: { default: !0 }
      });
      var $i = v(gr, 2);
      {
        var ji = (l) => {
          var u = zs();
          h((b) => K(u, "src", b), [() => Oe(e.demoAudioRel, e.demoAudioBust)]), g(l, u);
        };
        F($i, (l) => {
          e.demoAudioRel && l(ji);
        });
      }
      var fr = v(br, 2), Bi = t(fr), hr = v(fr, 2), yr = t(hr), wr = t(yr), Ei = t(wr), Ci = v(wr), Di = t(Ci), Ie = v(yr, 2), Ti = v(Ie, 2), Fi = t(Ti), xr = v(hr, 2);
      {
        var Pi = (l) => {
          var u = Tr(), b = t(u);
          h(() => c(b, e.demoNotice)), g(l, u);
        };
        F(xr, (l) => {
          e.demoNotice && l(Pi);
        });
      }
      var Oi = v(xr, 2);
      {
        var Li = (l) => {
          var u = Is(), b = t(u);
          h(() => c(b, e.demoError)), g(l, u);
        };
        F(Oi, (l) => {
          e.demoError && l(Li);
        });
      }
      h(
        (l, u, b, f, m, S, y, N, T, D, C, j, P, O, Q, $e, me, be, je, Be, ge, Ve, re, fe, ot, Je, nt, vt, We, dt, ct, k, A, M, H, I, ne, X, Ri, zi, Ii, Vi) => {
          Ce(G, 1, `review-banner ${i(ie) ? "approved" : ""}`), c(oe, l), K(pe, "src", u), Ue(te, i(Ir)), c(pa, i(zr)), c(ba, b), Ue(ga, f), c(fa, m), c(ya, S), c(ka, y), c(Na, N), c(Ma, T), Yi(tt, i(Mt)), c($a, ` ${D ?? ""}`), c(Ba, C), De(zt, j), c(Ea, P), De(rt, O), c(Da, Q), c(Ta, $e), De(at, me), c(Pa, be), c(Ia, je), c(Ja, Be), K(it, "placeholder", ge), c(Ka, Ve), c(Ga, re), c(Qa, fe), c(ti, ot), c(ri, Je), c(ai, nt), c(ii, vt), c(si, We), c(ni, dt), c(ui, ct), c(mi, k), c(yi, A), c(xi, M), K(st, "src", H), Ue(mr, I), c(Si, ne), c(Ai, X), c(Bi, Ri), c(Ei, zi), c(Di, Ii), De(Ie, i(At)), Ie.disabled = !i(Nt), c(Fi, Vi);
        },
        [
          () => i(ie) ? r("review.banner.approved") : r("review.banner.edit_gate"),
          () => Oe("input/source.mp4"),
          () => Qe(i(U)),
          () => `width:${i(et) > 0 ? Math.max(0, Math.min(100, i(U) / i(et) * 100)) : 0}%`,
          () => Qe(i(et)),
          () => r("review.player.subtitle_on"),
          () => r("review.burn_card_title"),
          () => r("review.burn_card_sub"),
          () => r("review.burn_preview_hint"),
          () => r("settings.subtitle.bg_enabled"),
          () => r("settings.subtitle.custom_hex"),
          () => String(e.styleSettings?.subtitle_background_color || "").trim(),
          () => r("settings.subtitle.margin_v_label"),
          () => Math.round(Number(e.styleSettings?.margin_v) || 0),
          () => r("settings.subtitle.margin_v_hint"),
          () => r("settings.subtitle.font_size_label"),
          () => Number(e.styleSettings?.font_size) >= 10 ? Math.round(Number(e.styleSettings.font_size)) : 0,
          () => r("settings.subtitle.font_size_hint"),
          () => r("review.editor_title"),
          () => r("review.editor_sub"),
          () => r("review.search_placeholder"),
          () => r("review.filters.changed_only"),
          () => r("review.filters.pending_only"),
          () => r("review.clone_hint"),
          () => r("review.table.index"),
          () => r("review.table.timecode"),
          () => r("review.table.source"),
          () => r(Ye() ? "review.table.voice_text" : "review.table.voice_text_transcript"),
          () => r("review.table.voice"),
          () => r("review.table.status"),
          () => i(_e) > 0 ? r("review.sticky.unsaved_count", { count: i(_e) }) : i(ie) ? r("review.sticky.approved_title") : i(Ze) > 0 ? r("review.sticky.changed_count", { count: i(Ze) }) : r("review.sticky.clean_title"),
          () => i(_e) > 0 ? r("review.sticky.unsaved_sub") : i(ie) ? r("review.sticky.approved_sub") : i(Ze) > 0 ? r("review.sticky.changed_sub") : r("review.sticky.clean_sub"),
          () => r("review.demo_title"),
          () => r("review.demo_sub"),
          () => Oe("input/source.mp4"),
          () => Dr(e.styleSettings, 220),
          () => r("review.demo_sample_text"),
          () => r("review.demo_unsupported_hint"),
          () => r("review.demo_voice_meta", {
            voice: e.ttsSettings.tts_voice || "—",
            speed: Fe(e.ttsSettings.speed_multiplier).toFixed(2)
          }),
          () => r("review.duck_gain_label"),
          () => r("review.duck_gain_value", {
            percent: i(At),
            db: we(e.ttsSettings.mix_duck_gain_db).toFixed(1)
          }),
          () => i(Nt) ? r("review.duck_gain_hint_active") : r("review.duck_gain_hint_disabled")
        ]
      ), Zi("timeupdate", pe, () => W(U, Number(i(R)?.currentTime) || 0, !0)), _s(Me, "clientHeight", (l) => W(gt, l)), V("change", tt, (l) => Ne({
        subtitle_background_color: l.target.checked ? String(e.styleSettings?.subtitle_background_color || "").trim() || "#000000" : void 0
      })), V("input", zt, (l) => Ne({
        subtitle_background_color: l.target.value.trim() || void 0
      })), V("change", rt, (l) => {
        let u = parseInt(l.target.value, 10);
        Number.isFinite(u) || (u = 0), u = Math.max(0, Math.min(500, u)), Ne({ margin_v: u });
      }), V("change", at, (l) => {
        let u = parseInt(l.target.value, 10);
        Number.isFinite(u) || (u = 0), u = Math.max(0, Math.min(120, u)), Ne({ font_size: u >= 10 ? u : void 0 });
      }), ss(it, () => e.searchQuery, (l) => e.searchQuery = l), $r(Ht, () => e.changedOnly, (l) => e.changedOnly = l), $r(qt, () => e.pendingOnly, (l) => e.pendingOnly = l), V("input", Ie, (l) => sa(Number(l.target.value))), g(a, o);
    };
    F(da, (a) => {
      i(la) ? a(ca) : e.loading ? a(_a, 1) : a(ua, -1);
    });
  }
  g(s, $t), Xi();
}
Gi(["click", "change", "input", "keydown"]);
const Rr = cs(Ws), to = Rr.mount, ro = Rr.unmount;
export {
  to as mount,
  ro as unmount
};
//# sourceMappingURL=review.js.map
