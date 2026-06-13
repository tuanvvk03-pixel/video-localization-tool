import { d as pr, p as ur, w as _r, f as Gt, i as N, g as v, l as c, o as st, t as y, j as h, a as x, q as gt, L as Y, m as B, y as mr, b as fr, s as lt, M as hr, O as gr, c as I, u as E, h as s, r as et, n as F, e as M, A as bt, P as br, Q as xt, R as kt, K as Qt, S as xr, v as Xt } from "./chunks/api-vHpIWCot.js";
import { e as ct, i as dt } from "./chunks/each-BE197-93.js";
import { b as kr } from "./chunks/input-D0G7l_P3.js";
import { b as wr } from "./chunks/this-_Wc-LPs7.js";
import { p as yr, B as vt } from "./chunks/Button-GpBM5g0S.js";
import { s as jr } from "./chunks/screen-DRq5NjFu.js";
const Sr = /[^A-Za-z0-9._-]+/g, $r = [
  "tts_provider",
  "tts_voice",
  "translate_backend",
  "subtitle_extractor",
  "external_srt_path"
];
function zr() {
  return {
    selectedFiles: [],
    activeIndex: 0,
    projectName: "",
    preview: null,
    importProjectBusy: !1,
    useAutoTranslate: !0,
    translateBackend: "block_v2",
    ttsProvider: "edge_tts",
    subtitleExtractor: "audio_only",
    externalSrtPath: ""
  };
}
function U(_) {
  const l = String(_ || "").split(/[\\/]/).filter(Boolean);
  return l[l.length - 1] || "";
}
function wt(_) {
  return String(_ || "").replace(/\.(mp4|mov|mkv|webm|avi)$/i, "");
}
function Fr(_) {
  let l = 5381;
  const n = String(_ || "");
  for (let i = 0; i < n.length; i += 1)
    l = (l << 5) + l ^ n.charCodeAt(i);
  return l >>> 0;
}
function Yt(_) {
  let l = 0;
  const n = String(_ || "");
  for (let i = 0; i < n.length; i += 1) l = l * 31 + n.charCodeAt(i) >>> 0;
  return l.toString(36).slice(0, 5) || "0";
}
function tt(_) {
  const l = String(_ || ""), n = l.replace(Sr, "-").replace(/^-+|-+$/g, "").replace(/^[._-]+|[._-]+$/g, ""), i = /[^\x00-\x7F]/.test(l);
  return n ? i ? `${n}-${Yt(l)}` : n : `video-${Yt(l)}`;
}
function Zt(_, l) {
  const n = String(_.path || "").trim(), i = wt(_.name || U(n) || "video");
  if (!n)
    return tt(`${i}-n${l}`);
  const a = n.replace(/\\/g, "/"), z = Fr(a).toString(36), V = `i${l}`;
  let A = tt(`${i}-${z}-${V}`);
  return A.length > 96 && (A = tt(`${i.slice(0, 32)}-${z}-${V}`)), A || tt(`v-${z}-${V}`);
}
function te(_) {
  const l = String(_ || "").trim();
  return !l || /[\\/]\s*$/.test(l) ? !1 : /\.(mp4|mov|mkv|webm|avi)$/i.test(l);
}
function Pr(_) {
  const l = String(_ || "").trim();
  return l ? /[\\/]\s*$/.test(l) ? !0 : !(/\.(mp4|mov|mkv|webm|avi)$/i.test(l) || /\.[a-z0-9]{1,6}$/i.test(l)) : !1;
}
function Z(_) {
  return String(_).padStart(2, "0");
}
function ee(_) {
  const l = Math.max(0, Math.round(Number(_) || 0)), n = Math.floor(l / 3600), i = Math.floor(l % 3600 / 60), a = l % 60;
  return n > 0 ? `${Z(n)}:${Z(i)}:${Z(a)}` : `${Z(i)}:${Z(a)}`;
}
function re(_) {
  const l = Number(_) || 0;
  if (l <= 0) return "0 B";
  const n = ["B", "KB", "MB", "GB"];
  let i = l, a = 0;
  for (; i >= 1024 && a < n.length - 1; )
    i /= 1024, a += 1;
  const z = i >= 100 || a === 0 ? 0 : 1;
  return `${i.toFixed(z)} ${n[a]}`;
}
function Ir(_) {
  const l = {};
  if (!_) return l;
  for (const n of $r) {
    const i = _[n];
    i != null && String(i).trim() !== "" && (l[n] = i);
  }
  return l;
}
function ie(_) {
  const l = _.subtitleExtractor || "audio_only";
  return {
    translate_backend: _.translateBackend,
    tts_provider: _.ttsProvider,
    use_auto_translate: !!_.useAutoTranslate,
    subtitle_extractor: l,
    external_srt_path: l === "external_srt" ? String(_.externalSrtPath || "").trim() : ""
  };
}
function Nr(_, l) {
  const n = l?.override || {};
  let i = n.subtitle_extractor;
  (i == null || i === "" || i === "__inherit__") && (i = _.subtitle_extractor);
  let a = String(i || "audio_only").toLowerCase();
  (a === "ocr_only" || a === "hybrid") && (a = "audio_only"), a !== "external_srt" && a !== "audio_only" && (a = "audio_only");
  let z = "";
  return n.external_srt_path != null && String(n.external_srt_path).trim() ? z = String(n.external_srt_path).trim() : a === "external_srt" && (z = String(_.external_srt_path || "").trim()), {
    ..._,
    subtitle_extractor: a,
    external_srt_path: a === "external_srt" ? z : ""
  };
}
const ae = (_, l = xr) => {
  var n = Er();
  y(() => {
    et(n, "aria-label", l()), et(n, "data-tooltip", l());
  }), x(_, n);
};
var Er = F('<span class="info-dot has-tooltip" role="img" tabindex="0">i</span>'), Tr = F('<div class="error-banner" data-testid="import-error"><div class="error-code"> </div> <div class="error-message"> </div></div>'), oe = F('<span class="small-muted"> </span>'), Rr = F('<span class="small-muted" style="color:var(--accent, #5b8def)" title="Video này có cấu hình riêng">● riêng</span>'), Br = F('<div role="button" tabindex="0"><strong> </strong> <!> <!> <span style="flex:1"></span> <!> <!></div>'), Ar = F('<div class="stack"><div class="card-sub"> </div> <div class="stack"></div></div>'), Lr = F('<div class="field stack"><label for="import-project-name">Tên dự án (project)</label> <input id="import-project-name" type="text" class="input"/> <div class="small-muted">Nhiều video sẽ được gộp thành một project có thư mục riêng.</div></div>'), Cr = F('<div class="item"><div class="k import-info-label"><span> </span> <!></div> <div class="v"> </div></div>'), Dr = F('<div class="meta-preview"><div class="thumb"></div> <div><div style="font-size:18px;font-weight:800"> </div> <div class="small-muted" style="margin-top:6px"> </div> <div class="kv"></div></div></div>'), Or = F("<option> </option>"), Mr = F('<div><span class="import-option-name"> </span> <!></div>'), Ur = F('<div class="field"><label for="ov-tts-provider">TTS provider (riêng)</label> <select id="ov-tts-provider" class="input"><option>— Dùng chung —</option><option>edge_tts</option><option>azure_tts</option></select></div> <div class="field"><label for="ov-tts-voice">TTS voice (riêng)</label> <input id="ov-tts-voice" type="text" class="input" placeholder="Để trống để dùng chung"/></div> <div class="field"><label for="ov-backend">Translate backend (riêng)</label> <select id="ov-backend" class="input"><option>— Dùng chung —</option><option>block_v2</option><option>legacy</option></select></div> <div class="field"><label for="ov-extractor"> </label> <select id="ov-extractor" class="input"><option> </option><option> </option><option> </option></select></div> <div class="field"><label for="ov-srt"> </label> <input id="ov-srt" type="text" class="input"/></div>', 1), Vr = F('<div class="section-block stack"><div class="card-sub">Cấu hình riêng cho video đang chọn</div> <div class="small-muted"> </div> <!></div>'), Wr = F('<!> <div class="screen video-step" data-testid="import-screen"><div class="card"><h2 class="scr-title"> </h2> <p class="scr-sub"> </p> <div class="stack"><div role="button" tabindex="-1"><input type="file" accept="video/*,.mp4,.mov,.mkv" multiple="" hidden=""/> <div class="dropzone-icon">🎬</div> <div class="big"> </div> <div class="small"> </div> <!></div> <!> <!></div> <div class="video-hint"><span> </span> <button type="button" class="linklike"> </button></div></div> <details class="advanced-block"><summary> </summary> <div class="advanced-body stack"><!> <div class="section-block stack"><div class="stack"><div class="card-sub"> </div> <div class="small-muted"> </div></div> <div class="field"><div class="field-label-row"><label for="import-tts-provider"> </label></div> <select id="import-tts-provider" class="input"></select> <div class="import-option-list"></div></div></div> <!></div></details> <div class="toolbar" style="margin-top:8px"><!> <!></div></div>', 1);
function qr(_, l) {
  ur(l, !0);
  let n = yr(l, "ctx", 7);
  const i = (t, e) => (n()?.t ?? ((r) => r))(t, e);
  let a = _r(n()?.importState || zr());
  n() && (n().importState = a);
  let z = lt(""), V = lt("UI"), A = 0, K = lt(void 0), rt = lt(!1);
  function G() {
    if (!a.selectedFiles.length) return null;
    const t = Math.min(Math.max(a.activeIndex | 0, 0), a.selectedFiles.length - 1);
    return a.selectedFiles[t];
  }
  const se = () => a.selectedFiles.length > 0, Q = () => a.selectedFiles.length >= 2;
  function yt() {
    const t = a.selectedFiles[0];
    return t ? wt(t.name || "project") : "";
  }
  function X() {
    M(z, "");
  }
  function j(t) {
    const e = le(t);
    M(V, e.shortCode || "UI", !0), M(z, e.summary || e.message, !0);
  }
  function le(t) {
    return t instanceof bt ? t : new bt({
      code: "ui_error",
      short_code: "UI",
      message: t && t.message ? t.message : String(t || i("error.generic"))
    });
  }
  function ce(t) {
    const e = String(t || "").trim();
    n().workspaceRoot = e;
    try {
      localStorage.setItem("workspace_root", e);
    } catch {
    }
    const r = document.getElementById("workspaceRootInput");
    r && (r.value = e);
  }
  async function de(t) {
    const e = [
      "Video files (*.mp4;*.mov;*.mkv;*.webm;*.avi)",
      "All files (*.*)"
    ], r = await hr({ filters: e, fallbackInput: t ?? null });
    if (r && r.ok && Array.isArray(r.paths) && r.paths.length) {
      for (const o of r.paths)
        await pt({ name: U(o), path: o, size: 0 });
      return;
    }
    if (!(r && r.ok && (r.cancelled || r.browser_fallback))) {
      if (r && r.unavailable) {
        const o = await gr({ filters: e, fallbackInput: t ?? null });
        if (o && o.ok && o.path) {
          await pt({
            name: U(o.path),
            path: o.path,
            size: 0
          });
          return;
        }
        if (o && o.ok && (o.cancelled || o.browser_fallback)) return;
        o && o.error && j(new Error(o.error));
        return;
      }
      r && r.error && j(new Error(r.error));
    }
  }
  async function ve() {
    const t = v(K)?.files ? Array.from(v(K).files) : [];
    t.length && await jt(t);
  }
  async function jt(t) {
    for (const e of t)
      await pt(e);
  }
  function pe(t) {
    for (const e of a.selectedFiles)
      if (t.path && e.path === t.path || !t.path && e.name === t.name && e.size === t.size) return e;
    return null;
  }
  async function pt(t) {
    const e = ++A, r = String(t?.path || "").trim(), o = String(t?.name || U(r) || "").trim(), m = Number(t?.size) || 0;
    X();
    const f = {
      name: o,
      path: r,
      size: m,
      duration: null,
      override: {},
      _file: t instanceof File ? t : null
    }, u = a.selectedFiles.findIndex((d) => f.path && d.path ? d.path === f.path : d.name === f.name && d.size === f.size);
    if (u >= 0) {
      a.activeIndex = u;
      return;
    }
    a.selectedFiles.push(f), a.activeIndex = a.selectedFiles.length - 1, a.preview = ut({ name: o, path: r, size: m, duration: null });
    try {
      const d = await _e(t);
      if (e !== A) return;
      const p = pe(f);
      if (!p) return;
      const g = String(d?.name || p.name || U(p.path) || "").trim(), k = String(d?.path || p.path).trim(), S = Number(d?.size);
      p.name = g, p.path = k, Number.isFinite(S) && S > 0 && (p.size = S), d?.duration != null && (p.duration = d.duration), G() === p && (a.preview = ut({
        name: p.name,
        path: p.path,
        size: p.size,
        duration: p.duration
      }));
    } catch (d) {
      if (e !== A) return;
      j(d);
    }
  }
  function ue(t) {
    if (t < 0 || t >= a.selectedFiles.length) return;
    a.selectedFiles.splice(t, 1), a.activeIndex >= a.selectedFiles.length && (a.activeIndex = Math.max(0, a.selectedFiles.length - 1));
    const e = G();
    a.preview = e ? ut({
      name: e.name,
      path: e.path,
      size: e.size,
      duration: e.duration
    }) : null;
  }
  async function _e(t) {
    const e = String(t?.path || "").trim();
    if (e) {
      const o = await I("/api/inspect-local-video", { path: e });
      return {
        name: o.name || U(e),
        path: o.path || e,
        size: Number(o.size) || 0,
        duration: Number.isFinite(Number(o.duration_s)) ? Number(o.duration_s) : null
      };
    }
    const r = await me(t);
    return {
      name: String(t?.name || "").trim(),
      path: "",
      size: Number(t?.size) || 0,
      duration: r
    };
  }
  function me(t) {
    return new Promise((e) => {
      if (!t || typeof URL > "u" || typeof document > "u") {
        e(null);
        return;
      }
      const r = URL.createObjectURL(t), o = document.createElement("video");
      o.preload = "metadata";
      const m = (f) => {
        o.removeAttribute("src"), o.load(), URL.revokeObjectURL(r);
        const u = Number(f);
        e(Number.isFinite(u) && u > 0 ? u : null);
      };
      o.onloadedmetadata = () => m(Number(o.duration)), o.onerror = () => m(null), o.src = r;
    });
  }
  function ut(t) {
    return {
      kind: "local_selection",
      sourceType: i("import.source_local"),
      title: t.name || i("import.preview_untitled"),
      sourceName: t.name || "",
      fileSize: t.size || 0,
      duration: t.duration != null ? Number(t.duration) : null,
      workspace: "",
      workspaceRoot: "",
      inputPath: t.path || "",
      jobId: ""
    };
  }
  function fe(t, e) {
    return {
      kind: "local_ready",
      sourceType: i("import.source_local"),
      title: t.source_name || t.job_id || i("import.preview_untitled"),
      sourceName: t.source_name || "",
      fileSize: 0,
      duration: t.source_duration_s,
      workspace: t.job_workspace,
      workspaceRoot: t.workspace_root || "",
      inputPath: t.input_video_path,
      jobId: t.job_id,
      voiceStatus: e && e.voice_edit_status ? e.voice_edit_status : ""
    };
  }
  function he(t) {
    const e = [];
    return t.duration != null && e.push({
      label: i("import.field_duration"),
      value: ee(t.duration),
      hint: i("import.hint_duration")
    }), t.fileSize && e.push({
      label: i("import.field_file_size"),
      value: re(t.fileSize),
      hint: i("import.hint_file_size")
    }), t.jobId && e.push({
      label: i("import.field_job_id"),
      value: t.jobId,
      hint: i("import.hint_job_id")
    }), t.workspace && e.push({
      label: i("import.field_workspace"),
      value: t.workspace,
      hint: i("import.hint_workspace")
    }), t.inputPath && e.push({
      label: i("import.field_input_path"),
      value: t.inputPath,
      hint: i("import.hint_input_path")
    }), t.voiceStatus && e.push({
      label: i("import.field_status"),
      value: i(`stage.${t.voiceStatus}`),
      hint: i("import.hint_status")
    }), e.length === 0 && e.push({
      label: i("import.field_status"),
      value: i("import.status_waiting"),
      hint: i("import.hint_status")
    }), e;
  }
  function L(t) {
    const e = G();
    if (!e) return;
    const r = { ...e.override || {} };
    for (const [o, m] of Object.entries(t || {}))
      m == null || String(m).trim() === "" || m === "__inherit__" ? delete r[o] : r[o] = m;
    e.override = r;
  }
  async function St(t, e) {
    if ((e.subtitle_extractor || "") !== "external_srt") return;
    const r = String(e.external_srt_path || "").trim();
    if (!r)
      throw j(new Error(i("import.external_srt_required"))), new Error("missing_external_srt");
    await I("/api/import-external-srt", { job_workspace: t, srt_path: r });
  }
  async function ge({ navigateOnSuccess: t }) {
    const e = G(), r = String(n().workspaceRoot || "").trim();
    if (r && !Pr(r))
      return j(new Error(i("error.workspace_root_invalid"))), null;
    if (!e || !String(e.path || "").trim())
      return j(new Error(i("import.path_required"))), null;
    const o = String(e.path).trim();
    if (!te(o))
      return j(new Error(i("import.path_invalid_file"))), null;
    X();
    try {
      const m = U(o), f = tt(wt(m || "video")), u = { video: o, job_id: f, force: !1 };
      r && (u.workspace_root = r);
      let d;
      try {
        d = await I("/api/init-job", u);
      } catch (g) {
        if (g instanceof bt && g.code === "workspace_exists")
          d = await I("/api/init-job", { ...u, force: !0 });
        else
          throw g;
      }
      ce(d.workspace_root || r);
      let p = null;
      try {
        p = await I("/api/status", { job_workspace: d.job_workspace });
      } catch {
        p = null;
      }
      return a.preview = fe(d, p), n().jobWorkspace = d.job_workspace, n().parentProject = void 0, n().parentProjectRoot = void 0, d;
    } catch (m) {
      return j(m), null;
    }
  }
  async function be() {
    const t = a.selectedFiles;
    if (t.length < 2) return null;
    for (const r of t) {
      if (!String(r.path || "").trim())
        return j(new Error(i("import.multi_path_required"))), null;
      if (!te(r.path))
        return j(new Error(i("import.multi_invalid_path", { path: r.path }))), null;
    }
    X();
    const e = (a.projectName || yt() || "project").trim();
    try {
      const r = await I("/api/init-project", {
        project_name: e,
        config_overrides: {
          translate_backend: a.translateBackend,
          tts_provider: a.ttsProvider
        }
      }), o = r.project_root, m = [];
      for (let u = 0; u < t.length; u += 1) {
        const d = t[u], p = Ir(d.override), g = {
          project_root: o,
          video: d.path,
          video_id: Zt(d, u),
          force: !1
        };
        Object.keys(p).length && (g.override = p);
        const k = await I("/api/add-video-to-project", g);
        m.push(k);
      }
      const f = ie(a);
      for (let u = 0; u < m.length; u += 1) {
        const d = m[u], p = String(d.workspace || "").trim();
        if (!p) continue;
        const g = String(d.video_id || "");
        let k = t[u];
        for (let w = 0; w < t.length; w += 1)
          if (Zt(t[w], w) === g) {
            k = t[w];
            break;
          }
        const S = Nr(f, k);
        await I("/api/save-import-config", { job_workspace: p, config: S });
        try {
          await St(p, S);
        } catch (w) {
          return j(w instanceof Error ? w : new Error(String(w))), null;
        }
      }
      return n().projectRoot = o, n().projectId = r.project_id, n().projectName = r.project_name, n().projectVideos = m, n().jobWorkspace = "", n().parentProject = r.project_id, n().parentProjectRoot = o, r;
    } catch (r) {
      return j(r), null;
    }
  }
  async function xe() {
    if (a.importProjectBusy) return;
    const t = ie(a);
    X(), a.importProjectBusy = !0;
    try {
      if (Q()) {
        const r = await be();
        if (!r) return;
        n().importConfig = { project_root: r.project_root, ...t }, n().settingsState = null, n().navigate("settings");
        return;
      }
      let e = String(n().jobWorkspace || "").trim();
      if (a.preview && a.preview.kind === "local_ready" && a.preview.workspace)
        e = String(a.preview.workspace).trim();
      else {
        const r = await ge({ navigateOnSuccess: !1 });
        if (!r || !r.job_workspace) return;
        e = String(r.job_workspace).trim();
      }
      if (!e) return;
      try {
        await I("/api/save-video-tts", {
          job_workspace: e,
          settings: { tts_provider: t.tts_provider }
        });
        const r = await I("/api/save-import-config", { job_workspace: e, config: t });
        try {
          await St(e, r.config || t);
        } catch (o) {
          j(o);
          return;
        }
        n().importConfig = { job_workspace: e, ...r.config || t }, n().settingsState = null, n().navigate("settings");
      } catch (r) {
        j(r);
      }
    } finally {
      a.importProjectBusy = !1;
    }
  }
  async function ke() {
    if (!n().workspaceRoot) {
      j(new Error(i("error.workspace_missing")));
      return;
    }
    X();
    try {
      await I("/api/reveal", { path: n().workspaceRoot });
    } catch (t) {
      j(t);
    }
  }
  function we(t) {
    t.preventDefault(), M(rt, !1);
    const e = t.dataTransfer && t.dataTransfer.files ? Array.from(t.dataTransfer.files) : [];
    e.length && jt(e);
  }
  const $t = E(() => [
    ["edge_tts", "edge_tts", i("import.tts_provider_edge_hint")],
    [
      "azure_tts",
      "azure_tts",
      i("import.tts_provider_azure_hint")
    ]
  ]), ye = (t) => !!(t.override?.tts_voice || t.override?.tts_provider || t.override?.translate_backend);
  var zt = Wr(), Ft = Gt(zt);
  {
    var je = (t) => {
      var e = Tr(), r = s(e), o = s(r), m = c(r, 2), f = s(m);
      y(() => {
        h(o, v(V)), h(f, v(z));
      }), x(t, e);
    };
    N(Ft, (t) => {
      v(z) && t(je);
    });
  }
  var Se = c(Ft, 2), Pt = s(Se), It = s(Pt), $e = s(It), Nt = c(It, 2), ze = s(Nt), Et = c(Nt, 2), W = s(Et), _t = s(W);
  wr(_t, (t) => M(K, t), () => v(K));
  var Tt = c(_t, 4), Fe = s(Tt), Rt = c(Tt, 2), Pe = s(Rt), Ie = c(Rt, 2);
  vt(Ie, {
    variant: "primary",
    onclick: () => de(v(K)),
    children: (t, e) => {
      var r = st();
      y((o) => h(r, o), [() => i("import.choose_file")]), x(t, r);
    },
    $$slots: { default: !0 }
  });
  var Bt = c(W, 2);
  {
    var Ne = (t) => {
      var e = Ar(), r = s(e), o = s(r), m = c(r, 2);
      ct(m, 21, () => a.selectedFiles, dt, (f, u, d) => {
        var p = Br(), g = s(p), k = s(g), S = c(g, 2);
        {
          var w = (b) => {
            var P = oe(), R = s(P);
            y((H) => h(R, `(${H ?? ""})`), [() => re(v(u).size)]), x(b, P);
          };
          N(S, (b) => {
            v(u).size > 0 && b(w);
          });
        }
        var C = c(S, 2);
        {
          var q = (b) => {
            var P = oe(), R = s(P);
            y((H) => h(R, H), [() => ee(v(u).duration)]), x(b, P);
          };
          N(C, (b) => {
            v(u).duration != null && b(q);
          });
        }
        var D = c(C, 4);
        {
          var O = (b) => {
            var P = Rr();
            x(b, P);
          }, it = E(() => ye(v(u)));
          N(D, (b) => {
            v(it) && b(O);
          });
        }
        var T = c(D, 2);
        vt(T, {
          variant: "secondary",
          onclick: (b) => {
            b.stopPropagation(), ue(d);
          },
          children: (b, P) => {
            var R = st("Xoá");
            x(b, R);
          },
          $$slots: { default: !0 }
        }), y(() => {
          gt(p, 1, `import-file-info ${a.activeIndex === d ? "active" : ""}`), br(p, `cursor:pointer;padding:8px 10px;border:${a.activeIndex === d ? "2px solid var(--accent, #5b8def)" : "1px solid var(--border, #2b2f3a)"};border-radius:6px;display:flex;align-items:center;gap:10px;`), h(k, v(u).name || `video ${d + 1}`);
        }), B("click", p, (b) => {
          b.target?.tagName !== "BUTTON" && (a.activeIndex = d);
        }), x(f, p);
      }), y((f) => h(o, f), [
        () => Q() ? `${a.selectedFiles.length} video (chế độ multi)` : "1 video (chế độ single)"
      ]), x(t, e);
    };
    N(Bt, (t) => {
      a.selectedFiles.length > 0 && t(Ne);
    });
  }
  var Ee = c(Bt, 2);
  {
    var Te = (t) => {
      var e = Lr(), r = c(s(e), 2);
      y((o) => et(r, "placeholder", o), [() => yt() || "project"]), kr(r, () => a.projectName, (o) => a.projectName = o), x(t, e);
    }, Re = E(() => Q());
    N(Ee, (t) => {
      v(Re) && t(Te);
    });
  }
  var Be = c(Et, 2), At = s(Be), Ae = s(At), Lt = c(At, 2), Le = s(Lt), mt = c(Pt, 2), Ct = s(mt), Ce = s(Ct), De = c(Ct, 2), Dt = s(De);
  {
    var Oe = (t) => {
      var e = Dr(), r = c(s(e), 2), o = s(r), m = s(o), f = c(o, 2), u = s(f), d = c(f, 2);
      ct(d, 21, () => he(a.preview), dt, (p, g) => {
        var k = Cr(), S = s(k), w = s(S), C = s(w), q = c(w, 2);
        ae(q, () => v(g).hint || v(g).label);
        var D = c(S, 2), O = s(D);
        y(() => {
          h(C, v(g).label), h(O, v(g).value);
        }), x(p, k);
      }), y(
        (p, g) => {
          h(m, p), h(u, `${g ?? ""} - ${a.preview?.sourceType ?? ""}`);
        },
        [
          () => a.preview?.title || a.preview?.sourceName || i("import.preview_untitled"),
          () => i("import.source_type")
        ]
      ), x(t, e);
    };
    N(Dt, (t) => {
      a.preview && t(Oe);
    });
  }
  var Ot = c(Dt, 2), Mt = s(Ot), Ut = s(Mt), Me = s(Ut), Ue = c(Ut, 2), Ve = s(Ue), We = c(Mt, 2), Vt = s(We), qe = s(Vt), He = s(qe), ft = c(Vt, 2);
  ct(ft, 21, () => v($t), dt, (t, e) => {
    var r = E(() => Xt(v(e), 2));
    let o = () => v(r)[0], m = () => v(r)[1];
    var f = Or(), u = s(f), d = {};
    y(() => {
      h(u, m()), d !== (d = o()) && (f.value = (f.__value = o()) ?? "");
    }), x(t, f);
  });
  var Je = c(ft, 2);
  ct(Je, 21, () => v($t), dt, (t, e) => {
    var r = E(() => Xt(v(e), 3));
    let o = () => v(r)[0], m = () => v(r)[1], f = () => v(r)[2];
    var u = Mr(), d = s(u), p = s(d), g = c(d, 2);
    ae(g, f), y(() => {
      gt(u, 1, `import-option-item ${a.ttsProvider === o() ? "active" : ""}`), et(u, "data-value", o()), h(p, m());
    }), x(t, u);
  });
  var Ke = c(Ot, 2);
  {
    var Ge = (t) => {
      const e = E(G);
      var r = Vr(), o = c(s(r), 2), m = s(o), f = c(o, 2);
      {
        var u = (d) => {
          var p = Ur(), g = Gt(p), k = c(s(g), 2), S = s(k);
          S.value = S.__value = "__inherit__";
          var w = c(S);
          w.value = w.__value = "edge_tts";
          var C = c(w);
          C.value = C.__value = "azure_tts";
          var q;
          xt(k);
          var D = c(g, 2), O = c(s(D), 2), it = c(D, 2), T = c(s(it), 2), b = s(T);
          b.value = b.__value = "__inherit__";
          var P = c(b);
          P.value = P.__value = "block_v2";
          var R = c(P);
          R.value = R.__value = "legacy";
          var H;
          xt(T);
          var qt = c(it, 2), Ht = s(qt), er = s(Ht), J = c(Ht, 2), at = s(J), rr = s(at);
          at.value = at.__value = "__inherit__";
          var ot = c(at), ir = s(ot);
          ot.value = ot.__value = "audio_only";
          var ht = c(ot), ar = s(ht);
          ht.value = ht.__value = "external_srt";
          var Jt;
          xt(J);
          var or = c(qt, 2), Kt = s(or), nr = s(Kt), nt = c(Kt, 2);
          y(
            ($, sr, lr, cr, dr, vr) => {
              q !== (q = v(e).override.tts_provider || "__inherit__") && (k.value = (k.__value = v(e).override.tts_provider || "__inherit__") ?? "", kt(k, v(e).override.tts_provider || "__inherit__")), Qt(O, v(e).override.tts_voice || ""), H !== (H = v(e).override.translate_backend || "__inherit__") && (T.value = (T.__value = v(e).override.translate_backend || "__inherit__") ?? "", kt(T, v(e).override.translate_backend || "__inherit__")), h(er, $), h(rr, sr), h(ir, lr), h(ar, cr), Jt !== (Jt = v(e).override.subtitle_extractor || "__inherit__") && (J.value = (J.__value = v(e).override.subtitle_extractor || "__inherit__") ?? "", kt(J, v(e).override.subtitle_extractor || "__inherit__")), h(nr, dr), et(nt, "placeholder", vr), Qt(nt, v(e).override.external_srt_path || "");
            },
            [
              () => i("import.per_video_subtitle_mode"),
              () => i("import.per_video_inherit"),
              () => i("settings.extractor.mode.audio_only"),
              () => i("settings.extractor.mode.external_srt"),
              () => i("import.per_video_external_srt"),
              () => i("import.per_video_external_srt_placeholder")
            ]
          ), B("change", k, ($) => L({ tts_provider: $.currentTarget.value })), B("change", O, ($) => L({ tts_voice: $.currentTarget.value })), Y("blur", O, ($) => L({ tts_voice: $.currentTarget.value })), B("change", T, ($) => L({ translate_backend: $.currentTarget.value })), B("change", J, ($) => L({ subtitle_extractor: $.currentTarget.value })), B("change", nt, ($) => L({ external_srt_path: $.currentTarget.value })), Y("blur", nt, ($) => L({ external_srt_path: $.currentTarget.value })), x(d, p);
        };
        N(f, (d) => {
          v(e) && d(u);
        });
      }
      y(() => h(m, v(e) ? `Đang chỉnh: ${v(e).name || `video ${a.activeIndex + 1}`}. Để trống nếu muốn dùng chung cấu hình project.` : "Chọn một video ở danh sách trên để gán cấu hình riêng.")), x(t, r);
    }, Qe = E(() => Q());
    N(Ke, (t) => {
      v(Qe) && t(Ge);
    });
  }
  var Xe = c(mt, 2), Wt = s(Xe);
  {
    let t = E(() => !n().workspaceRoot);
    vt(Wt, {
      get disabled() {
        return v(t);
      },
      onclick: ke,
      children: (e, r) => {
        var o = st();
        y((m) => h(o, m), [() => i("import.open_jobs_folder")]), x(e, o);
      },
      $$slots: { default: !0 }
    });
  }
  var Ye = c(Wt, 2);
  {
    var Ze = (t) => {
      {
        let e = E(() => !!a.importProjectBusy);
        vt(t, {
          variant: "primary",
          get disabled() {
            return v(e);
          },
          onclick: xe,
          children: (r, o) => {
            var m = st();
            y((f) => h(m, f), [
              () => a.importProjectBusy ? i("import.project_creating") : Q() ? i("import.multi_save_continue") : i("import.save_config")
            ]), x(r, m);
          },
          $$slots: { default: !0 }
        });
      }
    }, tr = E(() => se() || a.preview && a.preview.kind === "local_ready");
    N(Ye, (t) => {
      v(tr) && t(Ze);
    });
  }
  y(
    (t, e, r, o, m, f, u, d, p, g) => {
      h($e, t), h(ze, e), gt(W, 1, `dropzone ${v(rt) ? "active" : ""}`), h(Fe, r), h(Pe, o), h(Ae, m), h(Le, `${f ?? ""} →`), mt.open = !!a.preview, h(Ce, u), h(Me, d), h(Ve, p), h(He, g);
    },
    [
      () => i("import.input_title"),
      () => i("import.input_sub"),
      () => i("import.drop_big"),
      () => i("import.drop_small"),
      () => i("import.download_redirect"),
      () => i("rail.download"),
      () => i("import.advanced_summary"),
      () => i("import.config_title"),
      () => i("import.config_sub"),
      () => i("import.tts_provider_label")
    ]
  ), Y("dragover", W, (t) => {
    t.preventDefault(), M(rt, !0);
  }), Y("dragleave", W, () => M(rt, !1)), Y("drop", W, we), B("change", _t, ve), B("click", Lt, () => n().navigate("download")), mr(ft, () => a.ttsProvider, (t) => a.ttsProvider = t), x(_, zt), fr();
}
pr(["change", "click"]);
const ne = jr(qr), Yr = ne.mount, Zr = ne.unmount;
export {
  Yr as mount,
  Zr as unmount
};
//# sourceMappingURL=import.js.map
