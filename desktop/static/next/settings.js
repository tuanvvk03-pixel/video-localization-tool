import { d as Ml, p as Ol, w as Dl, x as Vl, f as vt, i as S, g as l, l as r, a as u, b as Il, s as zl, e as Gt, c as k, A as ge, h as t, t as g, j as o, u as f, n as N, a3 as Zi, Q as _t, q as We, m as $, r as it, o as E, R as dt, K as J, P as tr, z as Je, v as Xe, X as me, V as Ul } from "./chunks/api-vHpIWCot.js";
import { o as ql } from "./chunks/index-client-CjB8cgHo.js";
import { e as Kt, i as Wt } from "./chunks/each-BE197-93.js";
import { p as Gl, B as A } from "./chunks/Button-GpBM5g0S.js";
import { P as Kl } from "./chunks/ProgressBar-BACn-l7Z.js";
import { a as Wl, b as Jl, c as Xl, n as B, d as rt, e as He, f as be, r as Hl, g as Ql, h as er, V as ar, D as Jt, A as Yl, v as Qe, i as Zl, j as tn, k as en, l as ir, m as rr, o as sr, p as or, q as an, s as rn, t as lr, u as sn, w as on, x as ln, y as nr, z as vr, R as nn } from "./chunks/helpers-BtNcAVZn.js";
import { s as vn } from "./chunks/screen-DRq5NjFu.js";
var _n = N('<div class="error-banner"><div class="error-code">UI</div><div class="error-message"> </div></div>'), dn = N('<div class="card" data-testid="settings-empty"><div class="empty-card"><div class="empty-icon">⚙</div> <h3> </h3> <p> </p></div></div>'), cn = N('<div class="small-muted run-until-edit-progress-error"> </div>'), un = N('<div class="card work-card"><div class="work"><div class="orb"><div class="ring"></div><div class="ring r2"></div><div class="core"></div></div> <h2 class="work-title"> <span class="work-dots"></span></h2> <p class="work-sub"> </p> <div class="work-bar"><!> <div class="work-bar-foot"><span> </span><span> </span></div></div> <!></div></div>'), pn = N('<div class="info-banner"> </div>'), Ye = N("<option> </option>"), gn = N('<button type="button"> </button>'), mn = N('<optgroup><option selected=""> </option></optgroup>'), bn = N("<optgroup></optgroup>"), fn = N('<div class="small-muted voice-filter-warning"> </div>'), yn = N('<audio class="audio-preview" controls="" preload="metadata"></audio>'), Xt = N('<div class="meta-empty"> </div>'), xn = N('<div class="bgm-summary"><div class="row-title"> </div> <div class="small-muted"> </div></div> <audio class="audio-preview" controls="" preload="metadata"></audio> <div class="field-grid"><div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>-40 ... 0 dB</span></div> <input class="range-input" type="range" min="-40" max="0" step="1"/></div> <div class="switch-row"><div><div style="font-weight:700"> </div><div class="small-muted"> </div></div> <label class="checkbox-row"><input type="checkbox"/></label></div></div>', 1), Ze = N("<!> <!>", 1), hn = N('<div class="bgm-summary"><div class="row-title"> </div> <div class="small-muted"> </div></div> <img class="render-background-preview" alt=""/>', 1), kn = N('<div class="bgm-summary"><div class="row-title"> </div> <div class="small-muted"> </div></div> <img class="render-logo-preview" alt=""/> <div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option><option> </option></select></div> <div class="field"><label> </label> <input class="input" type="range" min="2" max="60" step="1"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0" max="100" step="1"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0" max="20" step="1"/></div></div>', 1), _r = N('<div class="small-muted"> </div>'), wn = N('<div class="section-block stack inline-action-banner" data-testid="api-key-missing" style="gap:10px"><div class="small-muted"> </div> <div class="toolbar"><!></div></div>'), $n = N('<!> <div class="stack"><div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div><div class="tag"> </div></div> <div class="card-body stack"><div class="section-block stack"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field"><label> </label> <select class="input"></select></div> <div class="field"><label> </label><input class="input" type="text" readonly=""/></div></div> <div class="stack" style="gap:10px"><div class="small-muted"> </div> <div class="toggle-bar"><button type="button" data-testid="style-bold">B</button> <button type="button" data-testid="style-italic">I</button> <!></div></div> <div class="small-muted"> </div> <div class="preview-tile"><div class="card-title"> </div> <div><span class="subtitle-sample"> </span></div></div></div> <div class="section-block stack"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field voice-picker"><label> </label> <div class="voice-filter-row"><select class="input voice-filter-select"><option> </option><!></select> <select class="input voice-filter-select"><option> </option><option> </option><option> </option></select></div> <select class="input"><!><!></select> <!></div> <div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>0.5x ... 2x</span></div> <input class="range-input" type="range" min="0.5" max="2" step="0.05"/></div> <div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option></select></div></div> <details class="advanced-details"><summary> </summary> <div class="field-grid advanced-grid"><div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>-50 ... +50</span></div> <input class="range-input" type="range" min="-50" max="50" step="1"/></div> <div class="field slider-row"><label> </label> <div class="slider-meta"><span> </span><span>-30 ... 0 dB</span></div> <input class="range-input" type="range" min="-30" max="0" step="1"/></div></div></details> <div class="field voice-preview-text-field"><label> </label> <input class="input" type="text"/></div> <div class="preview-tile"><div class="card-title"> </div> <div class="small-muted"><div> </div> <div> </div> <div> </div> <div> </div></div> <!> <div class="small-muted"> </div></div> <div class="toolbar"><!></div></div> <div class="section-block stack bgm-section"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <!> <div class="toolbar"><!> <!></div></div> <div class="section-block stack render-layout-section"><div class="stack" style="gap:6px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option></select></div></div> <!> <div class="toolbar"><!> <!> <!></div> <div class="stack" style="gap:6px;margin-top:10px"><div class="card-title"> </div><div class="card-sub"> </div></div> <!> <div class="toolbar"><!> <!></div> <div class="stack" style="gap:6px;margin-top:10px"><div class="card-title"> </div><div class="card-sub"> </div></div> <div class="field-grid"><div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/> <div class="small-muted"> </div></div> <div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/> <div class="small-muted"> </div></div></div> <div class="clip-row"><div class="clip-col"><div class="row-title"> </div> <!> <div class="toolbar"><!> <!></div></div> <div class="clip-col"><div class="row-title"> </div> <!> <div class="toolbar"><!> <!></div></div></div> <div class="toolbar"><!></div></div> <div class="toolbar"><!> <!></div></div></div> <div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option><option> </option><option> </option></select></div></div> <!> <details class="advanced-details"><summary> </summary> <div class="section-block"><div class="switch-row"><div><div style="font-weight:700"> </div><div class="small-muted"> </div></div> <label class="checkbox-row"><input type="checkbox"/></label></div> <div class="switch-row"><div><div style="font-weight:700"> </div><div class="small-muted"> </div></div> <label class="checkbox-row"><input type="checkbox"/></label></div></div></details> <div class="toolbar"><!></div></div></div></div>', 1), Ln = N('<div class="voice-edit-gate-backdrop" role="dialog" aria-modal="true"><div class="voice-edit-gate-card stack"><h3 class="voice-edit-gate-title"> </h3> <p class="voice-edit-gate-body"> </p> <div class="voice-edit-gate-actions"><!> <!></div></div></div>'), Pn = N('<div class="screen stack" data-testid="settings-screen"><!></div> <!>', 1);
function jn(cr, ta) {
  Ol(ta, !0);
  let L = Gl(ta, "ctx", 7);
  const i = (a, v) => (L()?.t ?? ((b) => b))(a, v), Ft = () => L()?.getLang?.() ?? "vi", m = () => String(L()?.jobWorkspace || ""), ct = () => String(L()?.parentProjectRoot || "");
  function ur() {
    try {
      const a = window.localStorage.getItem(ar);
      return a && a.trim() ? a : Jt;
    } catch {
      return Jt;
    }
  }
  function ea(a) {
    try {
      window.localStorage.setItem(ar, a || Jt);
    } catch {
    }
  }
  function pr() {
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
      previewText: ur(),
      voiceEditGateOpen: !1,
      openaiKeyMissing: !1,
      runUntilEditLive: null
    };
  }
  let e = Dl(L()?.settingsState || pr());
  L() && (L().settingsState = e);
  let ut = zl(""), xt = null;
  ql(() => {
    xt && clearInterval(xt);
  });
  const T = () => !!e.loading || !!e.busyAction;
  function Ht(a, v) {
    if (!m()) return "";
    const b = new URLSearchParams({ workspace: m(), rel: a });
    return v && b.set("v", String(v)), `/media?${b.toString()}`;
  }
  function Qt() {
    e.previewAudioRel = "", e.previewAudioBust = 0;
  }
  async function aa(a = !1) {
    if (!m() || !a && e.loadedJobWorkspace === m() && e.loadedProjectRoot === ct()) return;
    e.loading = !0, e.notice = "", Gt(ut, "");
    const v = !a && e.fontOptions.length ? Promise.resolve({ fonts: e.fontOptions }) : k("/api/list-system-fonts"), b = !a && e.voiceCatalog.length ? Promise.resolve({ voices: e.voiceCatalog }) : k("/api/list-voices");
    try {
      const [
        x,
        P,
        st,
        Ct,
        Mt,
        C,
        M,
        X,
        Q
      ] = await Promise.all([
        k("/api/get-video-style", { job_workspace: m() }),
        k("/api/get-video-tts", { job_workspace: m() }),
        ct() ? k("/api/get-project-style", { project_root: ct() }) : Promise.resolve({ style: {} }),
        ct() ? k("/api/get-project-tts", { project_root: ct() }) : Promise.resolve({ settings: {} }),
        k("/api/get-import-config", { job_workspace: m() }),
        v,
        b,
        k("/api/bgm/status", { job_workspace: m() }),
        k("/api/render-settings/status", { job_workspace: m() })
      ]), I = { ...st.style || {}, ...x.style || {} }, R = { ...Ct.settings || {}, ...P.settings || {} }, ot = L()?.importConfig && L().importConfig.job_workspace === m() ? L().importConfig : null, j = { ...Mt.config || {}, ...ot || {} }, z = String(j?.subtitle_extractor || "audio_only").toLowerCase();
      let Y = !1, O = z;
      z === "ocr_only" || z === "hybrid" ? (Y = !0, O = "audio_only") : z !== "external_srt" && (O = "audio_only");
      const Z = Wl(C.fonts || []), V = Jl(M.voices || []), H = j?.tts_provider || R.tts_provider || "edge_tts", ht = Number.isFinite(Number(R.tts_rate)) ? Number(R.tts_rate) : 0, pt = Xl(j?.translate_target || j?.target_language || j?.target_locale || "vi");
      Object.assign(e, {
        loadedJobWorkspace: m(),
        loadedProjectRoot: ct(),
        loading: !1,
        fontOptions: Z,
        voiceCatalog: V,
        subtitle_font: I.subtitle_font || "",
        subtitle_background_color: I.subtitle_background_color || "#000000",
        bg_enabled: !!I.subtitle_background_color,
        subtitle_bold: !!I.bold,
        subtitle_italic: !!I.italic,
        subtitle_align: I.align || "center",
        use_auto_translate: j?.use_auto_translate ?? !0,
        source_language: j?.source_language || "auto",
        translate_target: pt,
        translate_backend: j?.translate_backend || "block_v2",
        subtitle_extractor: O,
        external_srt_path: String(j?.external_srt_path || "").trim(),
        legacy_deprecated_extractor: Y,
        ocr_provider: j?.ocr_provider || "paddleocr",
        ocr_language: j?.ocr_language || "ch",
        ocr_device: j?.ocr_device || "auto",
        ocr_roi: er(j?.ocr_roi) || { x: 0, y: 0.78, w: 1, h: 0.22 },
        tts_provider: H,
        tts_voice: Ql(V, H, R.tts_voice || "", pt),
        speed_multiplier: Number.isFinite(Number(R.speed_multiplier)) ? be(Number(R.speed_multiplier)) : Hl(ht),
        tts_rate: ht,
        tts_pitch: Number.isFinite(Number(R.tts_pitch)) ? Number(R.tts_pitch) : 0,
        mix_mode: R.mix_mode || "replace_original_speech",
        mix_duck_gain_db: Number.isFinite(Number(R.mix_duck_gain_db)) ? He(Number(R.mix_duck_gain_db)) : -15,
        bgm: rt(X?.bgm),
        bgmAdvancedOpen: !1,
        renderLayout: B(Q?.render),
        previewAudioRel: "",
        previewAudioBust: 0,
        openaiKeyMissing: !1,
        notice: i("settings.notice_loaded")
      });
    } catch (x) {
      e.loading = !1, Gt(ut, fe(x), !0);
    }
  }
  function fe(a) {
    return a instanceof ge ? a.summary || a.message : a?.message || i("error.generic");
  }
  async function D(a, v) {
    if (L()) {
      Gt(ut, ""), e.busyAction = a, e.notice = "";
      try {
        await v();
      } catch (b) {
        Gt(ut, fe(b), !0);
      } finally {
        L() && (e.busyAction = "");
      }
    }
  }
  const gr = () => {
    const a = {};
    return (e.subtitle_font || "").trim() && (a.subtitle_font = e.subtitle_font.trim()), a.bold = !!e.subtitle_bold, a.italic = !!e.subtitle_italic, a.align = e.subtitle_align || "center", a;
  }, mr = () => ({
    tts_provider: e.tts_provider,
    tts_voice: (e.tts_voice || "").trim(),
    speed_multiplier: be(e.speed_multiplier),
    tts_rate: lr(e.speed_multiplier),
    tts_pitch: Number(e.tts_pitch) || 0,
    mix_mode: e.mix_mode,
    mix_duck_gain_db: He(e.mix_duck_gain_db)
  }), ia = () => {
    const a = rt(e.bgm);
    return a ? {
      original_path: a.original_path,
      normalized_path: a.normalized_path,
      original_filename: a.original_filename,
      duration_ms: a.duration_ms,
      volume_db: nr(a.volume_db),
      loop: !!a.loop,
      fade_in_ms: vr(a.fade_in_ms),
      fade_out_ms: vr(a.fade_out_ms)
    } : {};
  }, Bt = () => {
    const a = B(e.renderLayout), v = {
      aspect_ratio: a.aspect_ratio,
      background_path: a.background_path,
      background_original_filename: a.background_original_filename
    };
    return a.logo_path && (v.logo_path = a.logo_path, v.logo_original_filename = a.logo_original_filename, v.logo_position = a.logo_position, v.logo_scale = a.logo_scale, v.logo_opacity = a.logo_opacity, v.logo_margin = a.logo_margin), a.intro_clip_path && (v.intro_clip_path = a.intro_clip_path, v.intro_original_filename = a.intro_original_filename), a.outro_clip_path && (v.outro_clip_path = a.outro_clip_path, v.outro_original_filename = a.outro_original_filename), v.head_trim_sec = a.head_trim_sec, v.tail_trim_sec = a.tail_trim_sec, v;
  }, br = () => {
    const a = e.subtitle_extractor || "audio_only", v = {
      use_auto_translate: !!e.use_auto_translate,
      translate_backend: e.translate_backend || "block_v2",
      tts_provider: e.tts_provider || "edge_tts",
      subtitle_extractor: a,
      external_srt_path: a === "external_srt" ? String(e.external_srt_path || "").trim() : "",
      ocr_provider: e.ocr_provider || "paddleocr",
      ocr_language: e.ocr_language || "ch",
      ocr_device: e.ocr_device || "auto"
    };
    return a === "audio_only" && (v.ocr_roi = er(e.ocr_roi) || nn.bottom_band), v;
  }, fr = () => {
    if (L()?.parentProject) return String(L().parentProject);
    const v = m().replace(/[\\/]+$/, "").split(/[\\/]/);
    return v[v.length - 1] || "job";
  }, yr = () => D("save_text_audio", async () => {
    const a = [
      k("/api/save-video-style", { job_workspace: m(), style: gr() }),
      k("/api/save-video-tts", { job_workspace: m(), settings: mr() })
    ], v = !!e.bgm;
    v && a.push(k("/api/bgm/save", { job_workspace: m(), bgm: ia() })), a.push(k("/api/render-settings/save", { job_workspace: m(), render: Bt() }));
    const b = await Promise.all(a), x = b[1], P = v ? b[2] : null, st = v ? b[3] : b[2];
    Number.isFinite(Number(x.settings?.speed_multiplier)) && (e.speed_multiplier = be(Number(x.settings.speed_multiplier))), Number.isFinite(Number(x.settings?.tts_rate)) && (e.tts_rate = Number(x.settings.tts_rate)), P && (e.bgm = rt(P.bgm)), st && (e.renderLayout = B(st.render)), e.notice = i("settings.notice_saved_text_audio", { path: m() });
  }), xr = () => D("bgm_upload", async () => {
    const a = await me(["Audio files (*.mp3;*.wav;*.m4a;*.aac)", "All files (*.*)"]);
    if (a?.cancelled) return;
    if (!a?.ok || !a.path) throw new Error(a?.error || i("settings.bgm.pick_unavailable"));
    const v = rt(e.bgm) || {}, b = await k("/api/bgm/upload", {
      job_workspace: m(),
      bgm_path: a.path,
      volume_db: v.volume_db ?? -20,
      loop: v.loop ?? !0,
      fade_in_ms: v.fade_in_ms ?? 500,
      fade_out_ms: v.fade_out_ms ?? 1e3
    });
    e.bgm = rt(b.bgm), e.notice = i("settings.bgm.uploaded");
  }), hr = () => {
    if (e.bgm)
      return D("bgm_save", async () => {
        const a = await k("/api/bgm/save", { job_workspace: m(), bgm: ia() });
        e.bgm = rt(a.bgm), e.notice = i("settings.bgm.saved");
      });
  }, kr = () => {
    if (!(!e.bgm || !window.confirm(i("settings.bgm.confirm_remove"))))
      return D("bgm_remove", async () => {
        await k("/api/bgm/remove", { job_workspace: m() }), e.bgm = null, e.bgmAdvancedOpen = !1, e.notice = i("settings.bgm.removed");
      });
  }, wr = () => D("render_background_upload", async () => {
    const a = await me(["Image files (*.jpg;*.jpeg;*.png;*.webp)", "All files (*.*)"]);
    if (a?.cancelled) return;
    if (!a?.ok || !a.path) throw new Error(a?.error || i("settings.render_layout.pick_unavailable"));
    await k("/api/render-settings/save", { job_workspace: m(), render: Bt() });
    const v = await k("/api/render-background/upload", { job_workspace: m(), image_path: a.path });
    e.renderLayout = B(v.render), e.notice = i("settings.render_layout.uploaded");
  }), ye = () => D("render_layout_save", async () => {
    const a = await k("/api/render-settings/save", { job_workspace: m(), render: Bt() });
    e.renderLayout = B(a.render), e.notice = i("settings.render_layout.saved");
  }), $r = () => {
    if (!(!B(e.renderLayout).background_path || !window.confirm(i("settings.render_layout.confirm_remove"))))
      return D("render_background_remove", async () => {
        const a = await k("/api/render-background/remove", { job_workspace: m() });
        e.renderLayout = B(a.render), e.notice = i("settings.render_layout.removed");
      });
  };
  function Yt(a) {
    e.renderLayout = B({ ...e.renderLayout, ...a });
  }
  const Lr = () => D("render_logo_upload", async () => {
    const a = await me(["Image files (*.png;*.jpg;*.jpeg;*.webp)", "All files (*.*)"]);
    if (a?.cancelled) return;
    if (!a?.ok || !a.path) throw new Error(a?.error || i("settings.render_layout.pick_unavailable"));
    await k("/api/render-settings/save", { job_workspace: m(), render: Bt() });
    const v = await k("/api/render-logo/upload", { job_workspace: m(), image_path: a.path });
    e.renderLayout = B(v.render), e.notice = i("settings.render_layout.logo_uploaded");
  }), Pr = () => {
    if (!(!B(e.renderLayout).logo_path || !window.confirm(i("settings.render_layout.logo_confirm_remove"))))
      return D("render_logo_remove", async () => {
        const a = await k("/api/render-logo/remove", { job_workspace: m() });
        e.renderLayout = B(a.render), e.notice = i("settings.render_layout.logo_removed");
      });
  }, ra = (a) => D(`render_${a}_upload`, async () => {
    const v = await me([
      "Video files (*.mp4;*.mov;*.mkv;*.webm;*.m4v)",
      "All files (*.*)"
    ]);
    if (v?.cancelled) return;
    if (!v?.ok || !v.path) throw new Error(v?.error || i("settings.render_layout.pick_unavailable"));
    await k("/api/render-settings/save", { job_workspace: m(), render: Bt() });
    const b = await k(`/api/render-${a}/upload`, { job_workspace: m(), clip_path: v.path });
    e.renderLayout = B(b.render), e.notice = i(`settings.render_layout.${a}_uploaded`);
  }), sa = (a) => {
    if (!(!(a === "intro" ? B(e.renderLayout).intro_clip_path : B(e.renderLayout).outro_clip_path) || !window.confirm(i("settings.render_layout.clip_confirm_remove"))))
      return D(`render_${a}_remove`, async () => {
        const b = await k(`/api/render-${a}/remove`, { job_workspace: m() });
        e.renderLayout = B(b.render), e.notice = i(`settings.render_layout.${a}_removed`);
      });
  };
  function oa(a) {
    e.renderLayout = B({ ...e.renderLayout, ...a });
  }
  const jr = () => D("tts_preview", async () => {
    const a = (e.previewText || "").trim() || Jt;
    ea(a);
    const v = await k("/api/tts-preview", {
      job_workspace: m(),
      tts_provider: e.tts_provider,
      tts_voice: e.tts_voice,
      speed_multiplier: e.speed_multiplier,
      text: a
    });
    e.previewText = a, e.previewAudioRel = v.rel_path || "", e.previewAudioBust = Number(v.cache_bust) || Date.now(), e.notice = i("settings.tts.preview_ready");
  });
  function xe() {
    k("/api/job-progress", { job_workspace: m() }).then((a) => {
      e.runUntilEditLive = {
        overall_percent: Number(a.overall_percent) || 0,
        current_stage_label: String(a.current_stage_label || ""),
        current_stage: String(a.current_stage || ""),
        status_label: String(a.status_label || ""),
        lifecycle: String(a.lifecycle || ""),
        last_error: a.last_error != null ? String(a.last_error) : null
      };
    }).catch(() => {
    });
  }
  const Er = () => D("run_until_edit", async () => {
    e.openaiKeyMissing = !1, e.runUntilEditLive = {
      overall_percent: 0,
      current_stage_label: "",
      current_stage: "",
      status_label: "",
      lifecycle: "queued",
      last_error: null
    }, xe();
    try {
      xt = setInterval(xe, 800);
      try {
        const x = await k("/api/save-import-config", { job_workspace: m(), config: br() });
        L().importConfig = { job_workspace: m(), ...x?.config || {} };
      } catch {
      }
      const a = await k("/api/run-until-edit", {
        job_workspace: m(),
        project_name: fr(),
        use_auto_translate: !0,
        source_language: e.source_language,
        translate_backend: "block_v2",
        enable_source_cleanup: !!e.enable_source_cleanup,
        enable_translation_qa: !!e.enable_translation_qa,
        async: !0,
        subtitle_extractor: "audio_only"
      }), v = await Ul(m(), a);
      L().applyJobStatusToEditGate?.(L(), v), xe();
      const b = v.voice_edit_status || "";
      if (b === "voice_edit_pending") {
        e.voiceEditGateOpen = !0, e.notice = i("settings.notice_run_until_edit", { stage: i(`stage.${b}`) }), e.runUntilEditLive = null;
        return;
      }
      e.voiceEditGateOpen = !1, e.notice = i("settings.notice_run_until_edit", { stage: i(`stage.${b || "voice_edit_pending"}`) }), e.runUntilEditLive = null, L().navigate("review");
    } catch (a) {
      if (a instanceof ge && a.code === "api_key_required") {
        e.openaiKeyMissing = !0, e.runUntilEditLive = null;
        return;
      }
      const v = e.runUntilEditLive?.current_stage_label || e.runUntilEditLive?.current_stage || "", b = a instanceof ge ? a.message || a.code || "" : fe(a), x = a instanceof ge && Array.isArray(a.logTail) && a.logTail.length ? `
— Log:
` + a.logTail.slice(-8).join(`
`) : "";
      Gt(ut, i("settings.run_failed", { stage: v || "—", message: b }) + x), e.runUntilEditLive = null;
      return;
    } finally {
      xt && (clearInterval(xt), xt = null), L() && (e.runUntilEditLive = null);
    }
  }), la = f(() => sn(e.voiceCatalog, e.tts_provider)), Ar = f(() => {
    const a = /* @__PURE__ */ new Map();
    for (const v of l(la))
      !v.locale || a.has(v.locale) || a.set(v.locale, or(v, Ft(), i("settings.tts.locale_unknown")));
    return Array.from(a.entries()).sort((v, b) => v[1].localeCompare(b[1]));
  }), na = f(() => on(l(la), e.voiceLocaleFilter, e.voiceGenderFilter)), va = f(() => !!e.tts_voice && !l(na).some((a) => a.voice_id === e.tts_voice)), Zt = f(() => e.voiceCatalog.find((a) => a.provider === e.tts_provider && a.voice_id === e.tts_voice)), Nr = f(() => {
    const a = an(e.translate_target), v = /* @__PURE__ */ new Map();
    for (const x of [...l(na)].sort(rn)) {
      const P = x.locale || i("settings.tts.locale_unknown");
      v.has(P) || v.set(P, []), v.get(P).push(x);
    }
    const b = (x, P) => x[0] ? or(x[0], Ft(), i("settings.tts.locale_unknown")) : P;
    return Array.from(v.entries()).sort((x, P) => x[0] === a && P[0] !== a ? -1 : P[0] === a && x[0] !== a ? 1 : b(x[1], x[0]).localeCompare(b(P[1], P[0]))).map(([x, P]) => ({ label: b(P, x), items: P }));
  }), Rr = f(() => l(Zt) ? Qe(l(Zt), Ft()) : e.tts_voice || i("settings.tts.voice_placeholder")), Sr = f(() => e.mix_mode === "duck_original_speech" ? i("settings.tts.mix_duck") : e.mix_mode === "keep_music_replace_voice" ? i("settings.tts.mix_keep_music") : i("settings.tts.mix_replace")), q = f(() => rt(e.bgm)), y = f(() => B(e.renderLayout));
  function Tr(a) {
    e.tts_voice = a.target.value, Qt();
  }
  function Fr(a) {
    e.speed_multiplier = be(a), e.tts_rate = lr(e.speed_multiplier), Qt();
  }
  const Br = f(() => {
    const a = [];
    e.subtitle_font && !e.fontOptions.some((v) => v.family === e.subtitle_font) && a.push([e.subtitle_font, e.subtitle_font]);
    for (const v of e.fontOptions) a.push([v.family, v.family]);
    return a.length ? a : [[e.subtitle_font || "Arial", e.subtitle_font || "Arial"]];
  });
  Vl(() => {
    m(), ct(), aa();
  });
  var _a = Ze(), da = vt(_a);
  {
    var Cr = (a) => {
      var v = _n(), b = r(t(v)), x = t(b);
      g(() => o(x, l(ut))), u(a, v);
    };
    S(da, (a) => {
      l(ut) && a(Cr);
    });
  }
  var Mr = r(da, 2);
  {
    var Or = (a) => {
      var v = dn(), b = t(v), x = r(t(b), 2), P = t(x), st = r(x, 2), Ct = t(st);
      g(
        (Mt, C) => {
          o(P, Mt), o(Ct, C);
        },
        [
          () => i("settings.empty_title"),
          () => i("settings.empty_body")
        ]
      ), u(a, v);
    }, Dr = f(() => !m()), Vr = (a) => {
      var v = Pn(), b = vt(v), x = t(b);
      {
        var P = (C) => {
          const M = f(() => e.runUntilEditLive), X = f(() => Math.max(0, Math.min(100, Number(l(M)?.overall_percent) || 0)));
          var Q = un(), I = t(Q), R = r(t(I), 2), ot = t(R), j = r(R, 2), z = t(j), Y = r(j, 2), O = t(Y);
          Kl(O, {
            get percent() {
              return l(X);
            },
            wide: !0
          });
          var Z = r(O, 2), V = t(Z), H = t(V), ht = r(V), pt = t(ht), te = r(Y, 2);
          {
            var ee = (gt) => {
              var kt = cn(), Ot = t(kt);
              g(() => o(Ot, l(M).last_error)), u(gt, kt);
            };
            S(te, (gt) => {
              l(M)?.last_error && gt(ee);
            });
          }
          g(
            (gt, kt, Ot, ae) => {
              o(ot, gt), o(z, `${kt ?? ""}${l(M)?.status_label ? ` · ${l(M).status_label}` : ""}`), o(H, Ot), o(pt, `${ae ?? ""}%`);
            },
            [
              () => i("settings.run_until_edit_progress_title"),
              () => l(M)?.current_stage_label || i("settings.run_until_edit_progress_waiting"),
              () => i("settings.translation.progress_percent", { percent: Math.round(l(X)) }),
              () => Math.round(l(X))
            ]
          ), u(C, Q);
        }, st = (C) => {
          var M = $n(), X = vt(M);
          {
            var Q = (s) => {
              var n = pn(), d = t(n);
              g(() => o(d, e.notice)), u(s, n);
            };
            S(X, (s) => {
              e.notice && s(Q);
            });
          }
          var I = r(X, 2), R = t(I), ot = t(R), j = t(ot), z = t(j), Y = t(z), O = r(z), Z = t(O), V = r(j), H = t(V), ht = r(ot, 2), pt = t(ht), te = t(pt), ee = t(te), gt = t(ee), kt = r(ee), Ot = t(kt), ae = r(te, 2), ca = t(ae), ua = t(ca), Ir = t(ua), wt = r(ua, 2);
          Kt(wt, 21, () => l(Br), Wt, (s, n) => {
            var d = f(() => Xe(l(n), 2));
            let _ = () => l(d)[0], c = () => l(d)[1];
            var p = Ye(), w = t(p), h = {};
            g(() => {
              Zi(p, _() === e.subtitle_font), o(w, c()), h !== (h = _()) && (p.value = (p.__value = _()) ?? "");
            }), u(s, p);
          });
          var pa;
          _t(wt);
          var zr = r(ca, 2), ga = t(zr), Ur = t(ga), qr = r(ga), ma = r(ae, 2), ba = t(ma), Gr = t(ba), Kr = r(ba, 2), he = t(Kr), ke = r(he, 2), Wr = r(ke, 2);
          Kt(Wr, 17, () => Yl, Wt, (s, n) => {
            var d = f(() => Xe(l(n), 2));
            let _ = () => l(d)[0], c = () => l(d)[1];
            var p = gn(), w = t(p);
            g(() => {
              We(p, 1, `toggle-btn ${e.subtitle_align === _() ? "active" : ""}`), o(w, c());
            }), $("click", p, () => e.subtitle_align = _()), u(s, p);
          });
          var fa = r(ma, 2), Jr = t(fa), Xr = r(fa, 2), ya = t(Xr), Hr = t(ya), xa = r(ya, 2), ha = t(xa), Qr = t(ha), ka = r(pt, 2), wa = t(ka), $a = t(wa), Yr = t($a), Zr = r($a), ts = t(Zr), La = r(wa, 2), Pa = t(La), ja = t(Pa), es = t(ja), Ea = r(ja, 2), lt = t(Ea), ie = t(lt), as = t(ie);
          ie.value = ie.__value = "";
          var is = r(ie);
          Kt(is, 17, () => l(Ar), Wt, (s, n) => {
            var d = f(() => Xe(l(n), 2));
            let _ = () => l(d)[0], c = () => l(d)[1];
            var p = Ye(), w = t(p), h = {};
            g(() => {
              o(w, c()), h !== (h = _()) && (p.value = (p.__value = _()) ?? "");
            }), u(s, p);
          });
          var Aa;
          _t(lt);
          var mt = r(lt, 2), re = t(mt), rs = t(re);
          re.value = re.__value = "";
          var se = r(re), ss = t(se);
          se.value = se.__value = "female";
          var we = r(se), os = t(we);
          we.value = we.__value = "male";
          var Na;
          _t(mt);
          var bt = r(Ea, 2), Ra = t(bt);
          {
            var ls = (s) => {
              var n = mn(), d = t(n), _ = t(d), c = {};
              g(
                (p, w) => {
                  it(n, "label", p), o(_, w), c !== (c = e.tts_voice) && (d.value = (d.__value = e.tts_voice) ?? "");
                },
                [
                  () => i("settings.tts.current_voice"),
                  () => l(Zt) ? Qe(l(Zt), Ft()) : e.tts_voice
                ]
              ), u(s, n);
            };
            S(Ra, (s) => {
              l(va) && s(ls);
            });
          }
          var ns = r(Ra);
          Kt(ns, 17, () => l(Nr), Wt, (s, n) => {
            var d = bn();
            Kt(d, 21, () => l(n).items, Wt, (_, c) => {
              var p = Ye(), w = t(p), h = {};
              g(
                (F) => {
                  Zi(p, l(c).voice_id === e.tts_voice), o(w, F), h !== (h = l(c).voice_id) && (p.value = (p.__value = l(c).voice_id) ?? "");
                },
                [() => Qe(l(c), Ft())]
              ), u(_, p);
            }), g(() => it(d, "label", l(n).label)), u(s, d);
          });
          var Sa;
          _t(bt);
          var vs = r(bt, 2);
          {
            var _s = (s) => {
              var n = fn(), d = t(n);
              g((_) => o(d, _), [() => i("settings.tts.filter_current_hidden")]), u(s, n);
            };
            S(vs, (s) => {
              l(va) && s(_s);
            });
          }
          var Ta = r(Pa, 2), Fa = t(Ta), ds = t(Fa), Ba = r(Fa, 2), cs = t(Ba), us = t(cs), Ca = r(Ba, 2), ps = r(Ta, 2), Ma = t(ps), gs = t(Ma), $t = r(Ma, 2), oe = t($t), ms = t(oe);
          oe.value = oe.__value = "replace_original_speech";
          var le = r(oe), bs = t(le);
          le.value = le.__value = "duck_original_speech";
          var $e = r(le), fs = t($e);
          $e.value = $e.__value = "keep_music_replace_voice";
          var Oa;
          _t($t);
          var Da = r(La, 2), Va = t(Da), ys = t(Va), xs = r(Va, 2), Ia = t(xs), za = t(Ia), hs = t(za), Ua = r(za, 2), ks = t(Ua), ws = t(ks), qa = r(Ua, 2), $s = r(Ia, 2), Ga = t($s), Ls = t(Ga), Ka = r(Ga, 2), Ps = t(Ka), js = t(Ps), Wa = r(Ka, 2), Ja = r(Da, 2), Xa = t(Ja), Es = t(Xa), Le = r(Xa, 2), Ha = r(Ja, 2), Qa = t(Ha), As = t(Qa), Ya = r(Qa, 2), Za = t(Ya), Ns = t(Za), ti = r(Za, 2), Rs = t(ti), ei = r(ti, 2), Ss = t(ei), Ts = r(ei, 2), Fs = t(Ts), ai = r(Ya, 2);
          {
            var Bs = (s) => {
              var n = yn();
              g((d) => it(n, "src", d), [() => Ht(e.previewAudioRel, e.previewAudioBust)]), u(s, n);
            };
            S(ai, (s) => {
              e.previewAudioRel && s(Bs);
            });
          }
          var Cs = r(ai, 2), Ms = t(Cs), Os = r(Ha, 2), Ds = t(Os);
          {
            let s = f(T);
            A(Ds, {
              variant: "strong",
              get disabled() {
                return l(s);
              },
              onclick: jr,
              children: (n, d) => {
                var _ = E();
                g((c) => o(_, c), [() => i("settings.tts.test_voice")]), u(n, _);
              },
              $$slots: { default: !0 }
            });
          }
          var ii = r(ka, 2), ri = t(ii), si = t(ri), Vs = t(si), Is = r(si), zs = t(Is), oi = r(ri, 2);
          {
            var Us = (s) => {
              var n = Xt(), d = t(n);
              g((_) => o(d, _), [() => i("settings.bgm.no_bgm")]), u(s, n);
            }, qs = (s) => {
              var n = xn(), d = vt(n), _ = t(d), c = t(_), p = r(_, 2), w = t(p), h = r(d, 2), F = r(h, 2), U = t(F), G = t(U), Dt = t(G), K = r(G, 2), nt = t(K), Vt = t(nt), tt = r(K, 2), It = r(U, 2), et = t(It), jt = t(et), ft = t(jt), zt = r(jt), Et = t(zt), At = r(et, 2), yt = t(At);
              g(
                (at, Nt, Rt, St, Ut, Tt, qt) => {
                  o(c, at), o(w, Nt), it(h, "src", Rt), o(Dt, St), o(Vt, Ut), J(tt, l(q).volume_db), o(ft, Tt), o(Et, qt), Je(yt, l(q).loop);
                },
                [
                  () => (l(q).original_filename || l(q).original_path || l(q).normalized_path).split(/[\\/]/).pop(),
                  () => i("settings.bgm.duration", { duration: ln(l(q).duration_ms) }),
                  () => Ht(l(q).normalized_path || l(q).original_path, Date.now()),
                  () => i("settings.bgm.volume"),
                  () => sr(l(q).volume_db),
                  () => i("settings.bgm.loop"),
                  () => i("settings.bgm.loop_sub")
                ]
              ), $("input", tt, (at) => e.bgm = rt({ ...e.bgm, volume_db: nr(Number(at.target.value)) })), $("change", yt, (at) => e.bgm = rt({ ...e.bgm, loop: at.target.checked })), u(s, n);
            };
            S(oi, (s) => {
              l(q) ? s(qs, -1) : s(Us);
            });
          }
          var Gs = r(oi, 2), li = t(Gs);
          {
            let s = f(T);
            A(li, {
              variant: "secondary",
              get disabled() {
                return l(s);
              },
              onclick: xr,
              children: (n, d) => {
                var _ = E();
                g((c) => o(_, c), [() => i("settings.bgm.upload")]), u(n, _);
              },
              $$slots: { default: !0 }
            });
          }
          var Ks = r(li, 2);
          {
            var Ws = (s) => {
              var n = Ze(), d = vt(n);
              {
                let c = f(T);
                A(d, {
                  variant: "primary",
                  get disabled() {
                    return l(c);
                  },
                  onclick: hr,
                  children: (p, w) => {
                    var h = E();
                    g((F) => o(h, F), [() => i("settings.bgm.save")]), u(p, h);
                  },
                  $$slots: { default: !0 }
                });
              }
              var _ = r(d, 2);
              {
                let c = f(T);
                A(_, {
                  get disabled() {
                    return l(c);
                  },
                  onclick: kr,
                  children: (p, w) => {
                    var h = E();
                    g((F) => o(h, F), [() => i("settings.bgm.remove")]), u(p, h);
                  },
                  $$slots: { default: !0 }
                });
              }
              u(s, n);
            };
            S(Ks, (s) => {
              l(q) && s(Ws);
            });
          }
          var ni = r(ii, 2), vi = t(ni), _i = t(vi), Js = t(_i), Xs = r(_i), Hs = t(Xs), di = r(vi, 2), Qs = t(di), ci = t(Qs), Ys = t(ci), Lt = r(ci, 2), ne = t(Lt), Zs = t(ne);
          ne.value = ne.__value = "16:9";
          var Pe = r(ne), to = t(Pe);
          Pe.value = Pe.__value = "9:16";
          var ui;
          _t(Lt);
          var pi = r(di, 2);
          {
            var eo = (s) => {
              var n = hn(), d = vt(n), _ = t(d), c = t(_), p = r(_, 2), w = t(p), h = r(d, 2);
              g(
                (F, U, G) => {
                  o(c, F), o(w, U), it(h, "src", G);
                },
                [
                  () => (l(y).background_original_filename || l(y).background_path).split(/[\\/]/).pop(),
                  () => i("settings.render_layout.background_ready"),
                  () => Ht(l(y).background_path, Date.now())
                ]
              ), u(s, n);
            }, ao = (s) => {
              var n = Xt(), d = t(n);
              g((_) => o(d, _), [() => i("settings.render_layout.no_background")]), u(s, n);
            };
            S(pi, (s) => {
              l(y).background_path ? s(eo) : s(ao, -1);
            });
          }
          var gi = r(pi, 2), mi = t(gi);
          {
            let s = f(T);
            A(mi, {
              variant: "secondary",
              get disabled() {
                return l(s);
              },
              onclick: wr,
              children: (n, d) => {
                var _ = E();
                g((c) => o(_, c), [() => i("settings.render_layout.upload_background")]), u(n, _);
              },
              $$slots: { default: !0 }
            });
          }
          var bi = r(mi, 2);
          {
            let s = f(T);
            A(bi, {
              variant: "primary",
              get disabled() {
                return l(s);
              },
              onclick: ye,
              children: (n, d) => {
                var _ = E();
                g((c) => o(_, c), [() => i("settings.render_layout.save")]), u(n, _);
              },
              $$slots: { default: !0 }
            });
          }
          var io = r(bi, 2);
          {
            var ro = (s) => {
              {
                let n = f(T);
                A(s, {
                  get disabled() {
                    return l(n);
                  },
                  onclick: $r,
                  children: (d, _) => {
                    var c = E();
                    g((p) => o(c, p), [() => i("settings.render_layout.remove_background")]), u(d, c);
                  },
                  $$slots: { default: !0 }
                });
              }
            };
            S(io, (s) => {
              l(y).background_path && s(ro);
            });
          }
          var fi = r(gi, 2), yi = t(fi), so = t(yi), oo = r(yi), lo = t(oo), xi = r(fi, 2);
          {
            var no = (s) => {
              var n = kn(), d = vt(n), _ = t(d), c = t(_), p = r(_, 2), w = t(p), h = r(d, 2), F = r(h, 2), U = t(F), G = t(U), Dt = t(G), K = r(G, 2), nt = t(K), Vt = t(nt);
              nt.value = nt.__value = "top-left";
              var tt = r(nt), It = t(tt);
              tt.value = tt.__value = "top-right";
              var et = r(tt), jt = t(et);
              et.value = et.__value = "bottom-left";
              var ft = r(et), zt = t(ft);
              ft.value = ft.__value = "bottom-right";
              var Et;
              _t(K);
              var At = r(U, 2), yt = t(At), at = t(yt), Nt = r(yt, 2), Rt = r(At, 2), St = t(Rt), Ut = t(St), Tt = r(St, 2), qt = r(Rt, 2), ue = t(qt), Ne = t(ue), pe = r(ue, 2);
              g(
                (W, Re, Se, Te, Fe, Be, Ce, Me, Oe, De, Ve, Ie, ze, Ue, qe, Ge, Ke) => {
                  o(c, W), o(w, Re), it(h, "src", Se), o(Dt, Te), o(Vt, Fe), o(It, Be), o(jt, Ce), o(zt, Me), Et !== (Et = l(y).logo_position) && (K.value = (K.__value = l(y).logo_position) ?? "", dt(K, l(y).logo_position)), o(at, `${Oe ?? ""} (${De ?? ""}%)`), J(Nt, Ve), o(Ut, `${Ie ?? ""} (${ze ?? ""}%)`), J(Tt, Ue), o(Ne, `${qe ?? ""} (${Ge ?? ""}%)`), J(pe, Ke);
                },
                [
                  () => (l(y).logo_original_filename || l(y).logo_path).split(/[\\/]/).pop(),
                  () => i("settings.render_layout.logo_ready"),
                  () => Ht(l(y).logo_path, Date.now()),
                  () => i("settings.render_layout.logo_position"),
                  () => i("settings.render_layout.pos_top_left"),
                  () => i("settings.render_layout.pos_top_right"),
                  () => i("settings.render_layout.pos_bottom_left"),
                  () => i("settings.render_layout.pos_bottom_right"),
                  () => i("settings.render_layout.logo_scale"),
                  () => Math.round(l(y).logo_scale * 100),
                  () => Math.round(l(y).logo_scale * 100),
                  () => i("settings.render_layout.logo_opacity"),
                  () => Math.round(l(y).logo_opacity * 100),
                  () => Math.round(l(y).logo_opacity * 100),
                  () => i("settings.render_layout.logo_margin"),
                  () => Math.round(l(y).logo_margin * 100),
                  () => Math.round(l(y).logo_margin * 100)
                ]
              ), $("change", K, (W) => Yt({ logo_position: W.target.value })), $("input", Nt, (W) => Yt({ logo_scale: Number(W.target.value) / 100 })), $("input", Tt, (W) => Yt({ logo_opacity: Number(W.target.value) / 100 })), $("input", pe, (W) => Yt({ logo_margin: Number(W.target.value) / 100 })), u(s, n);
            }, vo = (s) => {
              var n = Xt(), d = t(n);
              g((_) => o(d, _), [() => i("settings.render_layout.no_logo")]), u(s, n);
            };
            S(xi, (s) => {
              l(y).logo_path ? s(no) : s(vo, -1);
            });
          }
          var hi = r(xi, 2), ki = t(hi);
          {
            let s = f(T);
            A(ki, {
              variant: "secondary",
              get disabled() {
                return l(s);
              },
              onclick: Lr,
              children: (n, d) => {
                var _ = E();
                g((c) => o(_, c), [() => i("settings.render_layout.upload_logo")]), u(n, _);
              },
              $$slots: { default: !0 }
            });
          }
          var _o = r(ki, 2);
          {
            var co = (s) => {
              var n = Ze(), d = vt(n);
              {
                let c = f(T);
                A(d, {
                  variant: "primary",
                  get disabled() {
                    return l(c);
                  },
                  onclick: ye,
                  children: (p, w) => {
                    var h = E();
                    g((F) => o(h, F), [() => i("settings.render_layout.save")]), u(p, h);
                  },
                  $$slots: { default: !0 }
                });
              }
              var _ = r(d, 2);
              {
                let c = f(T);
                A(_, {
                  get disabled() {
                    return l(c);
                  },
                  onclick: Pr,
                  children: (p, w) => {
                    var h = E();
                    g((F) => o(h, F), [() => i("settings.render_layout.remove_logo")]), u(p, h);
                  },
                  $$slots: { default: !0 }
                });
              }
              u(s, n);
            };
            S(_o, (s) => {
              l(y).logo_path && s(co);
            });
          }
          var wi = r(hi, 2), $i = t(wi), uo = t($i), po = r($i), go = t(po), Li = r(wi, 2), Pi = t(Li), ji = t(Pi), mo = t(ji), je = r(ji, 2), bo = r(je, 2), fo = t(bo), yo = r(Pi, 2), Ei = t(yo), xo = t(Ei), Ee = r(Ei, 2), ho = r(Ee, 2), ko = t(ho), Ai = r(Li, 2), Ni = t(Ai), Ri = t(Ni), wo = t(Ri), Si = r(Ri, 2);
          {
            var $o = (s) => {
              var n = _r(), d = t(n);
              g((_) => o(d, _), [
                () => (l(y).intro_original_filename || l(y).intro_clip_path).split(/[\\/]/).pop()
              ]), u(s, n);
            }, Lo = (s) => {
              var n = Xt(), d = t(n);
              g((_) => o(d, _), [() => i("settings.render_layout.no_clip")]), u(s, n);
            };
            S(Si, (s) => {
              l(y).intro_clip_path ? s($o) : s(Lo, -1);
            });
          }
          var Po = r(Si, 2), Ti = t(Po);
          {
            let s = f(T);
            A(Ti, {
              variant: "secondary",
              get disabled() {
                return l(s);
              },
              onclick: () => ra("intro"),
              children: (n, d) => {
                var _ = E();
                g((c) => o(_, c), [() => i("settings.render_layout.upload_intro")]), u(n, _);
              },
              $$slots: { default: !0 }
            });
          }
          var jo = r(Ti, 2);
          {
            var Eo = (s) => {
              {
                let n = f(T);
                A(s, {
                  get disabled() {
                    return l(n);
                  },
                  onclick: () => sa("intro"),
                  children: (d, _) => {
                    var c = E();
                    g((p) => o(c, p), [() => i("settings.render_layout.remove_clip")]), u(d, c);
                  },
                  $$slots: { default: !0 }
                });
              }
            };
            S(jo, (s) => {
              l(y).intro_clip_path && s(Eo);
            });
          }
          var Ao = r(Ni, 2), Fi = t(Ao), No = t(Fi), Bi = r(Fi, 2);
          {
            var Ro = (s) => {
              var n = _r(), d = t(n);
              g((_) => o(d, _), [
                () => (l(y).outro_original_filename || l(y).outro_clip_path).split(/[\\/]/).pop()
              ]), u(s, n);
            }, So = (s) => {
              var n = Xt(), d = t(n);
              g((_) => o(d, _), [() => i("settings.render_layout.no_clip")]), u(s, n);
            };
            S(Bi, (s) => {
              l(y).outro_clip_path ? s(Ro) : s(So, -1);
            });
          }
          var To = r(Bi, 2), Ci = t(To);
          {
            let s = f(T);
            A(Ci, {
              variant: "secondary",
              get disabled() {
                return l(s);
              },
              onclick: () => ra("outro"),
              children: (n, d) => {
                var _ = E();
                g((c) => o(_, c), [() => i("settings.render_layout.upload_outro")]), u(n, _);
              },
              $$slots: { default: !0 }
            });
          }
          var Fo = r(Ci, 2);
          {
            var Bo = (s) => {
              {
                let n = f(T);
                A(s, {
                  get disabled() {
                    return l(n);
                  },
                  onclick: () => sa("outro"),
                  children: (d, _) => {
                    var c = E();
                    g((p) => o(c, p), [() => i("settings.render_layout.remove_clip")]), u(d, c);
                  },
                  $$slots: { default: !0 }
                });
              }
            };
            S(Fo, (s) => {
              l(y).outro_clip_path && s(Bo);
            });
          }
          var Co = r(Ai, 2), Mo = t(Co);
          {
            let s = f(T);
            A(Mo, {
              variant: "primary",
              get disabled() {
                return l(s);
              },
              onclick: ye,
              children: (n, d) => {
                var _ = E();
                g((c) => o(_, c), [() => i("settings.render_layout.save")]), u(n, _);
              },
              $$slots: { default: !0 }
            });
          }
          var Oo = r(ni, 2), Mi = t(Oo);
          {
            let s = f(T);
            A(Mi, {
              variant: "secondary",
              get disabled() {
                return l(s);
              },
              onclick: () => aa(!0),
              children: (n, d) => {
                var _ = E();
                g((c) => o(_, c), [() => i("settings.reload")]), u(n, _);
              },
              $$slots: { default: !0 }
            });
          }
          var Do = r(Mi, 2);
          {
            let s = f(T);
            A(Do, {
              "data-testid": "save-text-audio",
              variant: "primary",
              get disabled() {
                return l(s);
              },
              onclick: yr,
              children: (n, d) => {
                var _ = E();
                g((c) => o(_, c), [() => i("settings.text_audio.save")]), u(n, _);
              },
              $$slots: { default: !0 }
            });
          }
          var Vo = r(R, 2), Oi = t(Vo), Io = t(Oi), Di = t(Io), zo = t(Di), Uo = r(Di), qo = t(Uo), Go = r(Oi, 2), Vi = t(Go), Ko = t(Vi), Ii = t(Ko), Wo = t(Ii), Pt = r(Ii, 2), ve = t(Pt), Jo = t(ve);
          ve.value = ve.__value = "auto";
          var _e = r(ve), Xo = t(_e);
          _e.value = _e.__value = "zh";
          var de = r(_e), Ho = t(de);
          de.value = de.__value = "en";
          var ce = r(de), Qo = t(ce);
          ce.value = ce.__value = "ja";
          var Ae = r(ce), Yo = t(Ae);
          Ae.value = Ae.__value = "ko";
          var zi;
          _t(Pt);
          var Ui = r(Vi, 2);
          {
            var Zo = (s) => {
              var n = wn(), d = t(n), _ = t(d), c = r(d, 2), p = t(c);
              {
                let w = f(T);
                A(p, {
                  variant: "secondary",
                  get disabled() {
                    return l(w);
                  },
                  onclick: () => L().navigate("app_settings"),
                  children: (h, F) => {
                    var U = E();
                    g((G) => o(U, G), [() => i("settings.translation.go_to_app_settings")]), u(h, U);
                  },
                  $$slots: { default: !0 }
                });
              }
              g((w) => o(_, w), [() => i("settings.translation.api_key_required")]), u(s, n);
            };
            S(Ui, (s) => {
              e.openaiKeyMissing && s(Zo);
            });
          }
          var qi = r(Ui, 2), Gi = t(qi), tl = t(Gi), el = r(Gi, 2), Ki = t(el), Wi = t(Ki), Ji = t(Wi), al = t(Ji), il = r(Ji), rl = t(il), sl = r(Wi, 2), Xi = t(sl), ol = r(Ki, 2), Hi = t(ol), Qi = t(Hi), ll = t(Qi), nl = r(Qi), vl = t(nl), _l = r(Hi, 2), Yi = t(_l), dl = r(qi, 2), cl = t(dl);
          {
            let s = f(T);
            A(cl, {
              "data-testid": "run-until-edit",
              variant: "strong",
              get disabled() {
                return l(s);
              },
              onclick: Er,
              children: (n, d) => {
                var _ = E();
                g((c) => o(_, c), [() => i("settings.translation.run_until_edit_auto")]), u(n, _);
              },
              $$slots: { default: !0 }
            });
          }
          g(
            (s, n, d, _, c, p, w, h, F, U, G, Dt, K, nt, Vt, tt, It, et, jt, ft, zt, Et, At, yt, at, Nt, Rt, St, Ut, Tt, qt, ue, Ne, pe, W, Re, Se, Te, Fe, Be, Ce, Me, Oe, De, Ve, Ie, ze, Ue, qe, Ge, Ke, ul, pl, gl, ml, bl, fl, yl, xl, hl, kl, wl, $l, Ll, Pl, jl, El, Al, Nl, Rl, Sl, Tl, Fl, Bl, Cl) => {
              o(Y, s), o(Z, n), o(H, d), o(gt, _), o(Ot, c), o(Ir, p), pa !== (pa = e.subtitle_font) && (wt.value = (wt.__value = e.subtitle_font) ?? "", dt(wt, e.subtitle_font)), o(Ur, w), J(qr, h), o(Gr, F), We(he, 1, `toggle-btn ${e.subtitle_bold ? "active" : ""}`), We(ke, 1, `toggle-btn ${e.subtitle_italic ? "active" : ""}`), o(Jr, U), o(Hr, G), tr(xa, Dt), tr(ha, K), o(Qr, nt), o(Yr, Vt), o(ts, tt), o(es, It), it(lt, "aria-label", et), o(as, `${jt ?? ""}: ${ft ?? ""}`), Aa !== (Aa = e.voiceLocaleFilter) && (lt.value = (lt.__value = e.voiceLocaleFilter) ?? "", dt(lt, e.voiceLocaleFilter)), it(mt, "aria-label", zt), o(rs, `${Et ?? ""}: ${At ?? ""}`), o(ss, yt), o(os, at), Na !== (Na = e.voiceGenderFilter) && (mt.value = (mt.__value = e.voiceGenderFilter) ?? "", dt(mt, e.voiceGenderFilter)), Sa !== (Sa = e.tts_voice) && (bt.value = (bt.__value = e.tts_voice) ?? "", dt(bt, e.tts_voice)), o(ds, Nt), o(us, Rt), J(Ca, e.speed_multiplier), o(gs, St), o(ms, Ut), o(bs, Tt), o(fs, qt), Oa !== (Oa = e.mix_mode) && ($t.value = ($t.__value = e.mix_mode) ?? "", dt($t, e.mix_mode)), o(ys, ue), o(hs, Ne), o(ws, pe), J(qa, e.tts_pitch), o(Ls, W), o(js, Re), J(Wa, e.mix_duck_gain_db), o(Es, Se), it(Le, "placeholder", Jt), J(Le, e.previewText), o(As, Te), o(Ns, `${Fe ?? ""}: ${l(Rr) ?? ""}`), o(Rs, `${Be ?? ""}: ${Ce ?? ""}`), o(Ss, `${Me ?? ""}: ${Oe ?? ""}`), o(Fs, `${De ?? ""}: ${l(Sr) ?? ""}`), o(Ms, Ve), o(Vs, Ie), o(zs, ze), o(Js, Ue), o(Hs, qe), o(Ys, Ge), o(Zs, Ke), o(to, ul), ui !== (ui = l(y).aspect_ratio) && (Lt.value = (Lt.__value = l(y).aspect_ratio) ?? "", dt(Lt, l(y).aspect_ratio)), o(so, pl), o(lo, gl), o(uo, ml), o(go, bl), o(mo, `${fl ?? ""} (${l(y).head_trim_sec ?? ""}s)`), J(je, l(y).head_trim_sec), o(fo, yl), o(xo, `${xl ?? ""} (${l(y).tail_trim_sec ?? ""}s)`), J(Ee, l(y).tail_trim_sec), o(ko, hl), o(wo, kl), o(No, wl), o(zo, $l), o(qo, Ll), o(Wo, Pl), o(Jo, jl), o(Xo, El), o(Ho, Al), o(Qo, Nl), o(Yo, Rl), zi !== (zi = e.source_language) && (Pt.value = (Pt.__value = e.source_language) ?? "", dt(Pt, e.source_language)), o(tl, Sl), o(al, Tl), o(rl, Fl), Je(Xi, e.enable_source_cleanup), o(ll, Bl), o(vl, Cl), Je(Yi, e.enable_translation_qa);
            },
            [
              () => i("settings.text_audio.title"),
              () => i("settings.text_audio.sub"),
              () => i("settings.scope_video"),
              () => i("settings.subtitle.title"),
              () => i("settings.subtitle.sub"),
              () => i("settings.subtitle.font"),
              () => i("settings.subtitle.mode"),
              () => i("settings.subtitle.mode_value"),
              () => i("settings.subtitle.style_tools"),
              () => i("settings.subtitle.burn_moved_hint"),
              () => i("settings.subtitle.preview_title"),
              () => `flex:1;display:grid;align-items:end;background:var(--bg-0);border-radius:14px;padding:28px;text-align:${Zl(e.subtitle_align)}`,
              () => `font-family:${tn(e.subtitle_font)};background:${e.bg_enabled ? en(e.subtitle_background_color) : "transparent"};font-weight:${e.subtitle_bold ? 800 : 500};font-style:${e.subtitle_italic ? "italic" : "normal"}`,
              () => i("settings.subtitle.preview_sample"),
              () => i("settings.tts.title"),
              () => i("settings.tts.sub"),
              () => i("settings.tts.voice"),
              () => i("settings.tts.filter_locale"),
              () => i("settings.tts.filter_locale"),
              () => i("settings.tts.filter_all"),
              () => i("settings.tts.filter_gender"),
              () => i("settings.tts.filter_gender"),
              () => i("settings.tts.filter_all"),
              () => i("settings.tts.filter_female"),
              () => i("settings.tts.filter_male"),
              () => i("settings.tts.speed"),
              () => ir(e.speed_multiplier),
              () => i("settings.tts.mix_mode"),
              () => i("settings.tts.mix_replace"),
              () => i("settings.tts.mix_duck"),
              () => i("settings.tts.mix_keep_music"),
              () => i("settings.tts.advanced"),
              () => i("settings.tts.pitch"),
              () => rr(e.tts_pitch),
              () => i("settings.tts.duck_gain"),
              () => sr(e.mix_duck_gain_db),
              () => i("settings.tts.preview_text_label"),
              () => i("settings.tts.preview_title"),
              () => i("settings.tts.voice"),
              () => i("settings.tts.speed"),
              () => ir(e.speed_multiplier),
              () => i("settings.tts.pitch"),
              () => rr(e.tts_pitch),
              () => i("settings.tts.mix_mode"),
              () => i("settings.tts.preview_sub"),
              () => i("settings.bgm.title"),
              () => i("settings.bgm.sub"),
              () => i("settings.render_layout.title"),
              () => i("settings.render_layout.sub"),
              () => i("settings.render_layout.aspect_ratio"),
              () => i("settings.render_layout.aspect_16_9"),
              () => i("settings.render_layout.aspect_9_16"),
              () => i("settings.render_layout.logo_title"),
              () => i("settings.render_layout.logo_sub"),
              () => i("settings.render_layout.clips_title"),
              () => i("settings.render_layout.clips_sub"),
              () => i("settings.render_layout.head_trim"),
              () => i("settings.render_layout.head_trim_hint"),
              () => i("settings.render_layout.tail_trim"),
              () => i("settings.render_layout.tail_trim_hint"),
              () => i("settings.render_layout.intro_clip"),
              () => i("settings.render_layout.outro_clip"),
              () => i("settings.translation.title"),
              () => i("settings.translation.sub"),
              () => i("settings.translation.source_language"),
              () => i("settings.translation.source_language_auto"),
              () => i("settings.translation.source_language_zh"),
              () => i("settings.translation.source_language_en"),
              () => i("settings.translation.source_language_ja"),
              () => i("settings.translation.source_language_ko"),
              () => i("settings.tts.advanced"),
              () => i("settings.translation.cleanup_title"),
              () => i("settings.translation.cleanup_sub"),
              () => i("settings.translation.qa_title"),
              () => i("settings.translation.qa_sub")
            ]
          ), $("change", wt, (s) => e.subtitle_font = s.target.value), $("click", he, () => e.subtitle_bold = !e.subtitle_bold), $("click", ke, () => e.subtitle_italic = !e.subtitle_italic), $("change", lt, (s) => e.voiceLocaleFilter = s.target.value), $("change", mt, (s) => e.voiceGenderFilter = s.target.value), $("change", bt, Tr), $("input", Ca, (s) => Fr(Number(s.target.value))), $("change", $t, (s) => e.mix_mode = s.target.value), $("input", qa, (s) => {
            e.tts_pitch = Number(s.target.value), Qt();
          }), $("input", Wa, (s) => e.mix_duck_gain_db = He(Number(s.target.value))), $("input", Le, (s) => {
            e.previewText = s.target.value, ea(e.previewText), Qt();
          }), $("change", Lt, (s) => e.renderLayout = B({ ...e.renderLayout, aspect_ratio: s.target.value })), $("change", je, (s) => oa({ head_trim_sec: Number(s.target.value) })), $("change", Ee, (s) => oa({ tail_trim_sec: Number(s.target.value) })), $("change", Pt, (s) => e.source_language = s.target.value), $("change", Xi, (s) => e.enable_source_cleanup = s.target.checked), $("change", Yi, (s) => e.enable_translation_qa = s.target.checked), u(C, M);
        };
        S(x, (C) => {
          e.busyAction === "run_until_edit" ? C(P) : C(st, -1);
        });
      }
      var Ct = r(b, 2);
      {
        var Mt = (C) => {
          var M = Ln(), X = t(M), Q = t(X), I = t(Q), R = r(Q, 2), ot = t(R), j = r(R, 2), z = t(j);
          A(z, {
            variant: "secondary",
            onclick: () => {
              e.voiceEditGateOpen = !1, L().navigate("review");
            },
            children: (O, Z) => {
              var V = E();
              g((H) => o(V, H), [() => i("settings.voice_edit_gate.pause")]), u(O, V);
            },
            $$slots: { default: !0 }
          });
          var Y = r(z, 2);
          A(Y, {
            variant: "strong",
            onclick: () => {
              e.voiceEditGateOpen = !1, L().pendingVoiceEditContinue = !0, L().navigate("render");
            },
            children: (O, Z) => {
              var V = E();
              g((H) => o(V, H), [() => i("settings.voice_edit_gate.continue")]), u(O, V);
            },
            $$slots: { default: !0 }
          }), g(
            (O, Z) => {
              o(I, O), o(ot, Z);
            },
            [
              () => i("settings.voice_edit_gate.title"),
              () => i("settings.voice_edit_gate.body")
            ]
          ), u(C, M);
        };
        S(Ct, (C) => {
          e.voiceEditGateOpen && C(Mt);
        });
      }
      u(a, v);
    };
    S(Mr, (a) => {
      l(Dr) ? a(Or) : a(Vr, -1);
    });
  }
  u(cr, _a), Il();
}
Ml(["change", "click", "input"]);
const dr = vn(jn), Bn = dr.mount, Cn = dr.unmount;
export {
  Bn as mount,
  Cn as unmount
};
//# sourceMappingURL=settings.js.map
