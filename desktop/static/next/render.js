import { T as we, i as N, l as o, S as Pe, t as l, q as Ae, U as Te, a as v, h as e, n as g, j as n, k as Re, f as yt, p as Me, w as Ce, x as Ee, g as i, b as Ne, s as Zt, c as w, e as Bt, u as f, o as J, r as De, V as Le, A as Be } from "./chunks/api-vHpIWCot.js";
import { o as Fe } from "./chunks/index-client-CjB8cgHo.js";
import { e as te, i as ee } from "./chunks/each-BE197-93.js";
import { p as Rt, s as re, r as Ve, B as ft } from "./chunks/Button-GpBM5g0S.js";
import { s as We } from "./chunks/events-OW5kxpYF.js";
import { S as Ft } from "./chunks/StatusBadge-DT3lodBA.js";
import { P as Je } from "./chunks/ProgressBar-BACn-l7Z.js";
import { s as ze } from "./chunks/screen-DRq5NjFu.js";
var Ie = /* @__PURE__ */ new Set([
  "$$slots",
  "$$events",
  "$$legacy",
  "title",
  "sub",
  "bodyClass",
  "headerRight",
  "children"
]), Ue = g('<div class="card-title"> </div>'), qe = g('<div class="card-sub"> </div>'), Oe = g('<div class="card-header"><div><!> <!></div> <!></div>'), Ke = g("<div><!> <div><!></div></div>");
function Tt(Mt, M) {
  let b = Rt(M, "title", 3, ""), a = Rt(M, "sub", 3, ""), c = Rt(M, "bodyClass", 3, ""), C = Ve(M, Ie);
  var gt = Ke();
  we(gt, () => ({ class: "card", ...C }));
  var bt = e(gt);
  {
    var Ct = (et) => {
      var xt = Oe(), ot = e(xt), mt = e(ot);
      {
        var $t = (A) => {
          var E = Ue(), z = e(E);
          l(() => n(z, b())), v(A, E);
        };
        N(mt, (A) => {
          b() && A($t);
        });
      }
      var jt = o(mt, 2);
      {
        var Et = (A) => {
          var E = qe(), z = e(E);
          l(() => n(z, a())), v(A, E);
        };
        N(jt, (A) => {
          a() && A(Et);
        });
      }
      var St = o(ot, 2);
      {
        var ht = (A) => {
          var E = Re(), z = yt(E);
          re(z, () => M.headerRight), v(A, E);
        };
        N(St, (A) => {
          M.headerRight && A(ht);
        });
      }
      v(et, xt);
    };
    N(bt, (et) => {
      (b() || a() || M.headerRight) && et(Ct);
    });
  }
  var kt = o(bt, 2), s = e(kt);
  re(s, () => M.children ?? Pe), l(() => Ae(kt, 1, Te(c() ? `card-body ${c()}` : "card-body"))), v(Mt, gt);
}
var Ge = g('<div class="error-banner" data-testid="render-error"><div class="error-code"> </div> <div class="error-message"> </div></div>'), He = g('<div class="card" data-testid="render-empty"><div class="empty-card"><div class="empty-icon">▶</div> <h3> </h3> <p> </p></div></div>'), Ye = g('<div class="card" data-testid="render-loading"><div class="empty-card"><div class="empty-icon">…</div> <h3> </h3> <p> </p></div></div>'), Qe = g('<div class="kv"><div class="item"><div class="k"> </div><div class="v"> </div></div> <div class="item"><div class="k"> </div><div class="v"> </div></div> <div class="item"><div class="k"> </div><div class="v"> </div></div> <div class="item"><div class="k"> </div><div class="v"> </div></div> <div class="item"><div class="k"> </div><div class="v"> </div></div></div>'), Xe = g('<div class="info-banner"> </div>'), Ze = g('<div class="meta-empty"> </div>'), tr = g('<div class="artifact"><div><div class="artifact-name"> </div> <small> </small></div> <!> <div class="toolbar"><!> <!></div></div>'), er = g('<div class="artifact"><div><div class="artifact-name"> </div> <small> </small></div> <!> <div class="toolbar"><!></div></div>'), ae = g("<!> <!>", 1), rr = g('<div class="small-muted"> </div>'), ar = g('<div class="artifact-list"><!></div> <div class="toolbar"><!> <!> <!></div> <!>', 1), sr = g('<video class="render-preview-video" controls="" preload="metadata"></video>', 2), ir = g('<div class="thumb render-thumb"></div>'), nr = g('<!> <div class="kv"><div class="item"><div class="k"> </div><div class="v"> </div></div> <div class="item"><div class="k"> </div><div class="v"> </div></div> <div class="item"><div class="k"> </div><div class="v"> </div></div> <div class="item"><div class="k"> </div><div class="v"> </div></div></div> <div class="toolbar" style="margin-top:16px"><!></div>', 1), or = g('<div class="section-block"><div style="font-weight:800"> </div> <div class="small-muted" style="margin-top:6px"> </div> <!> <div class="small-muted" style="margin-top:8px"> </div></div>'), dr = g('<div class="screen stack" data-testid="render-screen"><!> <!> <div class="grid-2"><div class="stack"><!></div> <div class="stack"><!> <!></div></div></div>');
function cr(Mt, M) {
  Me(M, !0);
  let b = Rt(M, "ctx", 7);
  const a = (t, r) => (b()?.t ?? ((d) => d))(t, r), c = () => String(b()?.jobWorkspace || ""), C = () => String(b()?.parentProjectRoot || ""), gt = [
    "artifacts/translate/final_subtitle.srt",
    "artifacts/translate/final_subtitle_manifest.json",
    "artifacts/tts/tts_manifest.json",
    "artifacts/aligned/alignment_manifest.json",
    "artifacts/mixed/mix_manifest.json",
    "artifacts/render/final.mp4",
    "artifacts/render/render_manifest.json"
  ], bt = {
    "artifacts/translate/final_subtitle.srt": "voice_edited",
    "artifacts/translate/final_subtitle_manifest.json": "voice_edited",
    "artifacts/tts/tts_manifest.json": "tts_generated",
    "artifacts/aligned/alignment_manifest.json": "aligned",
    "artifacts/mixed/mix_manifest.json": "mixed",
    "artifacts/render/final.mp4": "rendered",
    "artifacts/render/render_manifest.json": "rendered"
  }, Ct = {
    "artifacts/download/download_manifest.json": "artifact.download_manifest",
    "artifacts/transcribe/source.srt": "artifact.source_srt",
    "artifacts/transcribe/source_cleaned_zh.srt": "artifact.source_cleaned_zh_srt",
    "artifacts/translate/translated_auto.srt": "artifact.translated_auto_srt",
    "artifacts/translate/translated_voice.srt": "artifact.translated_voice_srt",
    "artifacts/translate/translated_manual.srt": "artifact.translated_manual_srt",
    "artifacts/translate/final_subtitle.srt": "artifact.final_subtitle_srt",
    "artifacts/translate/final_subtitle_manifest.json": "artifact.final_subtitle_manifest",
    "artifacts/edit/edited_voice.srt": "artifact.edited_voice_srt",
    "artifacts/edit/edit_manifest.json": "artifact.edit_manifest",
    "artifacts/tts/tts_manifest.json": "artifact.tts_manifest",
    "artifacts/aligned/alignment_manifest.json": "artifact.alignment_manifest",
    "artifacts/mixed/mix_manifest.json": "artifact.mix_manifest",
    "artifacts/render/final.mp4": "artifact.final_mp4",
    "artifacts/render/render_manifest.json": "artifact.render_manifest",
    "job_state.json": "artifact.job_state",
    "video_state.json": "artifact.video_state",
    "style_override.json": "artifact.style_override",
    "tts_override.json": "artifact.tts_override"
  };
  function kt() {
    return {
      loadedJobWorkspace: "",
      loading: !1,
      busyAction: "",
      notice: "",
      status: null,
      progress: null,
      artifacts: [],
      extras: [],
      effectiveTts: {
        tts_provider: "edge_tts",
        tts_voice: "vi-VN-HoaiMyNeural",
        tts_rate: 0,
        tts_pitch: 0,
        mix_mode: "replace_original_speech"
      },
      effectiveStyle: {},
      renderSubtitleMode: "burn",
      importSummary: null
    };
  }
  let s = Ce(b()?.renderState || kt());
  b() && (b().renderState = s);
  let et = Zt(""), xt = Zt("UI"), ot = null, mt = "";
  Fe(() => Vt());
  function $t() {
    const t = b()?.settingsState;
    return t && t.loadedJobWorkspace === c() ? t : null;
  }
  function jt(t, r, d) {
    return {
      ...t?.settings || {},
      ...r?.settings || {},
      ...d ? {
        tts_provider: d.tts_provider,
        tts_voice: d.tts_voice,
        speed_multiplier: d.speed_multiplier,
        tts_rate: d.tts_rate,
        tts_pitch: d.tts_pitch,
        mix_mode: d.mix_mode,
        mix_duck_gain_db: d.mix_duck_gain_db
      } : {}
    };
  }
  async function Et(t = !1) {
    if (c()) {
      if (!t && s.loadedJobWorkspace === c() && s.progress) {
        St().catch(() => {
        }), Nt();
        return;
      }
      Jt(), s.loading = !0, s.notice = "", s.loadedJobWorkspace = c();
      try {
        const [
          r,
          d,
          _,
          m,
          I,
          dt,
          rt,
          U
        ] = await Promise.all([
          w("/api/status", { job_workspace: c() }),
          w("/api/job-progress", { job_workspace: c() }),
          w("/api/list-artifacts", { job_workspace: c() }),
          w("/api/get-video-tts", { job_workspace: c() }),
          w("/api/get-video-style", { job_workspace: c() }),
          C() ? w("/api/get-project-tts", { project_root: C() }) : Promise.resolve({ settings: {} }),
          C() ? w("/api/get-project-style", { project_root: C() }) : Promise.resolve({ style: {} }),
          w("/api/get-import-config", { job_workspace: c() }).catch(() => ({ config: {} }))
        ]), Pt = $t(), At = jt(dt, m, Pt), Dt = { ...rt.style || {}, ...I.style || {} }, k = U && typeof U.config == "object" ? U.config : {};
        Object.assign(s, {
          loadedJobWorkspace: c(),
          loading: !1,
          status: r,
          progress: d,
          artifacts: It(_.canonical || []),
          extras: Array.isArray(_.extras) ? _.extras : [],
          effectiveTts: At,
          effectiveStyle: Dt,
          renderSubtitleMode: String(Pt?.renderSubtitleMode || "burn"),
          importSummary: {
            use_auto_translate: k.use_auto_translate !== !1,
            source_language: String(k.source_language || "auto"),
            translate_backend: String(k.translate_backend || "block_v2")
          },
          notice: ""
        }), Nt(), b()?.pendingVoiceEditContinue && (b().pendingVoiceEditContinue = !1, A());
      } catch (r) {
        b() && (b().pendingVoiceEditContinue = !1), s.loading = !1, zt(r);
      }
    }
  }
  async function St() {
    if (!c()) return;
    const [t, r, d, _] = await Promise.all([
      w("/api/get-video-tts", { job_workspace: c() }).catch(() => ({ settings: {} })),
      C() ? w("/api/get-project-tts", { project_root: C() }).catch(() => ({ settings: {} })) : Promise.resolve({ settings: {} }),
      w("/api/get-video-style", { job_workspace: c() }).catch(() => ({ style: {} })),
      C() ? w("/api/get-project-style", { project_root: C() }).catch(() => ({ style: {} })) : Promise.resolve({ style: {} })
    ]), m = $t();
    s.effectiveTts = jt(r, t, m), s.effectiveStyle = { ..._.style || {}, ...d.style || {} }, m && typeof m.renderSubtitleMode == "string" && (s.renderSubtitleMode = m.renderSubtitleMode);
  }
  async function ht(t = !1) {
    if (!c()) return;
    const r = [
      w("/api/status", { job_workspace: c() }),
      w("/api/job-progress", { job_workspace: c() })
    ];
    t && r.push(w("/api/list-artifacts", { job_workspace: c() }));
    const [d, _, m] = await Promise.all(r);
    s.status = d, s.progress = _, m && (s.artifacts = It(m.canonical || []), s.extras = Array.isArray(m.extras) ? m.extras : []);
  }
  async function A() {
    Nt(), await Wt("run_after_approval", async () => {
      await St();
      const t = s.effectiveTts || {}, r = await w("/api/run-after-edit", {
        job_workspace: c(),
        project_name: ne(),
        project_root: C(),
        to_stage: "rendered",
        subtitle_mode: s.renderSubtitleMode,
        tts_provider: t.tts_provider || "edge_tts",
        tts_voice: t.tts_voice || "",
        tts_rate: Number(t.tts_rate) || 0,
        mix_mode: t.mix_mode || "replace_original_speech",
        mix_duck_gain_db: Number.isFinite(Number(t.mix_duck_gain_db)) ? Number(t.mix_duck_gain_db) : -15,
        async: !0
      }), d = await Le(c(), r);
      s.notice = d?.render_dir ? a("render.notice_run_finished", { path: d.render_dir }) : a("render.notice_run_started"), await ht(!0);
    });
  }
  async function E() {
    await z(`${c()}\\artifacts\\render`);
  }
  async function z(t) {
    await Wt("reveal", async () => {
      const r = await w("/api/reveal", { path: t });
      s.notice = a("render.notice_revealed", { path: r.path });
    });
  }
  function ie(t) {
    !t?.exists || !t.rel_path || window.open(Ut(t.rel_path, Number(t.modified_unix) || 0), "_blank", "noopener");
  }
  function Nt() {
    Vt(), c() && (mt = String(s.progress?.current_stage || ""), ot = We(c(), {
      onProgress: (t) => {
        s.progress = t;
        const r = String(t?.current_stage || "");
        r !== mt && (mt = r, ht(!0).catch(() => {
        }));
      },
      onDone: (t) => {
        s.progress = t, ht(!0).catch(() => {
        });
      }
    }));
  }
  function Vt() {
    ot && (ot(), ot = null);
  }
  async function Wt(t, r) {
    Jt(), s.busyAction = t;
    try {
      await r();
    } catch (d) {
      zt(d);
    } finally {
      s.busyAction = "";
    }
  }
  function Jt() {
    Bt(et, "");
  }
  function zt(t) {
    const r = t instanceof Be ? t : null;
    Bt(xt, r?.shortCode || "UI", !0), Bt(
      et,
      r ? r.summary || r.message : t?.message || a("error.generic"),
      !0
    );
  }
  function It(t) {
    return Array.isArray(t) ? t.map((r) => ({ ...r })) : [];
  }
  function ne() {
    if (b()?.parentProject) return String(b().parentProject);
    const r = c().replace(/[\\/]+$/, "").split(/[\\/]/);
    return r[r.length - 1] || "job";
  }
  function Ut(t, r = 0) {
    if (!c()) return "";
    const d = new URLSearchParams({ workspace: c(), rel: t });
    return r && d.set("v", String(r)), `/media?${d.toString()}`;
  }
  function oe(t) {
    const r = t.rel_path ? Ct[t.rel_path] : void 0;
    return r ? a(r) : t.label || t.rel_path || "";
  }
  function de(t) {
    return t.exists ? a("render.artifact_ready_meta", {
      size: _e(t.size_bytes || 0),
      updated: ue(t.modified_unix || 0)
    }) : a("render.artifact_pending_meta", {
      stage: a(`stage.${t.rel_path && bt[t.rel_path] || "rendered"}`)
    });
  }
  function ce(t) {
    return a(t === "duck_original_speech" ? "settings.tts.mix_duck" : "settings.tts.mix_replace");
  }
  function qt(t) {
    return a(t === "burn" || t === "hard" ? "render.subtitle_mode_hard" : "render.subtitle_mode_soft");
  }
  function ve(t) {
    const r = String(t || "auto"), d = `settings.translation.source_language_${r}`, _ = a(d);
    return _ === d ? r : _;
  }
  function le() {
    const t = s.effectiveTts || {};
    return a("render.current_voice_summary", {
      voice: t.tts_voice || "—",
      rate: Ot(t.tts_rate),
      pitch: Ot(t.tts_pitch),
      status: s.progress?.status_label || a("status.waiting")
    });
  }
  function Ot(t) {
    const r = Number(t) || 0;
    return `${r > 0 ? "+" : ""}${r}%`;
  }
  function _e(t) {
    const r = Number(t) || 0;
    return r >= 1024 * 1024 ? `${(r / (1024 * 1024)).toFixed(1)} MB` : r >= 1024 ? `${(r / 1024).toFixed(1)} KB` : `${r} B`;
  }
  function ue(t) {
    const r = Number(t) || 0;
    return r ? new Date(r * 1e3).toLocaleString() : "—";
  }
  function fe(t) {
    const r = s.progress?.current_stage || "", d = s.progress?.lifecycle || "", _ = t.rel_path && bt[t.rel_path] || "rendered";
    return t.exists ? { kind: "completed", text: a("status.completed") } : r === _ && d === "running" ? { kind: "running", text: a("status.running") } : s.status?.voice_edited ? { kind: "queued", text: a("status.waiting") } : { kind: "blocked", text: a("status.needs_review") };
  }
  function me() {
    const t = s.status?.voice_edited ? s.progress?.lifecycle || "queued" : "blocked", r = t === "blocked" ? a("status.needs_review") : a(`status.${t}`) || t;
    return { kind: t === "idle" ? "queued" : t, text: r };
  }
  const Kt = f(() => !!s.status?.voice_edited), Gt = f(() => s.artifacts.filter((t) => t.rel_path && gt.includes(t.rel_path))), wt = f(() => s.artifacts.find((t) => t.rel_path === "artifacts/render/final.mp4" && t.exists) || null), pe = f(() => i(wt) ? Ut(i(wt).rel_path, Number(i(wt).modified_unix) || 0) : ""), Ht = f(() => Math.max(0, Math.min(100, Number(s.progress?.overall_percent) || 0))), Yt = f(me);
  Ee(() => {
    c(), Et();
  });
  var Qt = ae(), Xt = yt(Qt);
  {
    var ge = (t) => {
      var r = Ge(), d = e(r), _ = e(d), m = o(d, 2), I = e(m);
      l(() => {
        n(_, i(xt)), n(I, i(et));
      }), v(t, r);
    };
    N(Xt, (t) => {
      i(et) && t(ge);
    });
  }
  var be = o(Xt, 2);
  {
    var xe = (t) => {
      var r = He(), d = e(r), _ = o(e(d), 2), m = e(_), I = o(_, 2), dt = e(I);
      l(
        (rt, U) => {
          n(m, rt), n(dt, U);
        },
        [() => a("render.empty_title"), () => a("render.empty_body")]
      ), v(t, r);
    }, he = f(() => !c()), ye = (t) => {
      var r = Ye(), d = e(r), _ = o(e(d), 2), m = e(_), I = o(_, 2), dt = e(I);
      l(
        (rt, U) => {
          n(m, rt), n(dt, U);
        },
        [() => a("render.loading_title"), () => a("common.loading")]
      ), v(t, r);
    }, ke = (t) => {
      var r = dr(), d = e(r);
      {
        var _ = (k) => {
          const T = f(() => s.importSummary);
          {
            let q = f(() => a("render.config_summary_title")), ct = f(() => a("render.config_summary_sub"));
            Tt(k, {
              get title() {
                return i(q);
              },
              get sub() {
                return i(ct);
              },
              bodyClass: "stack",
              children: (D, L) => {
                var R = Qe(), O = e(R), K = e(O), G = e(K), H = o(K), at = e(H), Y = o(O, 2), st = e(Y), it = e(st), pt = o(st), p = e(pt), $ = o(Y, 2), x = e($), j = e(x), B = o(x), h = e(B), F = o($, 2), V = e(F), Q = e(V), X = o(V), vt = e(X), lt = o(F, 2), Z = e(lt), nt = e(Z), _t = o(Z), u = e(_t);
                l(
                  (P, y, S, W, tt, ut, Lt, $e, je, Se) => {
                    n(G, P), n(at, y), n(it, S), n(p, W), n(j, tt), n(h, ut), n(Q, Lt), n(vt, $e), n(nt, je), n(u, Se);
                  },
                  [
                    () => a("render.summary_source_language"),
                    () => ve(i(T).source_language),
                    () => a("render.summary_translate_mode"),
                    () => i(T).use_auto_translate ? a("render.summary_translate_on") : a("render.summary_translate_off"),
                    () => a("render.summary_translate_backend"),
                    () => String(i(T).translate_backend || "—"),
                    () => a("render.summary_tts_provider"),
                    () => String(s.effectiveTts?.tts_provider || "—"),
                    () => a("render.summary_subtitle_mode"),
                    () => qt(s.renderSubtitleMode)
                  ]
                ), v(D, R);
              },
              $$slots: { default: !0 }
            });
          }
        };
        N(d, (k) => {
          s.importSummary && k(_);
        });
      }
      var m = o(d, 2);
      {
        var I = (k) => {
          var T = Xe(), q = e(T);
          l(() => n(q, s.notice)), v(k, T);
        };
        N(m, (k) => {
          s.notice && k(I);
        });
      }
      var dt = o(m, 2), rt = e(dt), U = e(rt);
      {
        const k = (ct) => {
          Ft(ct, {
            get kind() {
              return i(Yt).kind;
            },
            children: (D, L) => {
              var R = J();
              l(() => n(R, i(Yt).text)), v(D, R);
            },
            $$slots: { default: !0 }
          });
        };
        let T = f(() => a("render.execution_title")), q = f(() => a("render.execution_sub"));
        Tt(U, {
          get title() {
            return i(T);
          },
          get sub() {
            return i(q);
          },
          bodyClass: "stack",
          headerRight: k,
          children: (ct, D) => {
            var L = ar(), R = yt(L), O = e(R);
            {
              var K = (p) => {
                var $ = Ze(), x = e($);
                l((j) => n(x, j), [() => a("render.artifacts_empty")]), v(p, $);
              }, G = (p) => {
                var $ = ae(), x = yt($);
                te(x, 17, () => i(Gt), ee, (B, h) => {
                  const F = f(() => fe(i(h)));
                  var V = tr(), Q = e(V), X = e(Q), vt = e(X), lt = o(X, 2), Z = e(lt), nt = o(Q, 2);
                  Ft(nt, {
                    get kind() {
                      return i(F).kind;
                    },
                    children: (y, S) => {
                      var W = J();
                      l(() => n(W, i(F).text)), v(y, W);
                    },
                    $$slots: { default: !0 }
                  });
                  var _t = o(nt, 2), u = e(_t);
                  {
                    let y = f(() => !i(h).exists || !i(h).rel_path);
                    ft(u, {
                      get disabled() {
                        return i(y);
                      },
                      onclick: () => ie(i(h)),
                      children: (S, W) => {
                        var tt = J();
                        l((ut) => n(tt, ut), [() => a("common.open")]), v(S, tt);
                      },
                      $$slots: { default: !0 }
                    });
                  }
                  var P = o(u, 2);
                  {
                    let y = f(() => !i(h).exists || !i(h).path);
                    ft(P, {
                      get disabled() {
                        return i(y);
                      },
                      onclick: () => z(i(h).path),
                      children: (S, W) => {
                        var tt = J();
                        l((ut) => n(tt, ut), [() => a("common.reveal")]), v(S, tt);
                      },
                      $$slots: { default: !0 }
                    });
                  }
                  l(
                    (y, S) => {
                      n(vt, y), n(Z, S);
                    },
                    [
                      () => oe(i(h)),
                      () => de(i(h))
                    ]
                  ), v(B, V);
                });
                var j = o(x, 2);
                te(j, 17, () => s.extras, ee, (B, h) => {
                  var F = er(), V = e(F), Q = e(V), X = e(Q), vt = o(Q, 2), lt = e(vt), Z = o(V, 2);
                  Ft(Z, {
                    kind: "completed",
                    children: (u, P) => {
                      var y = J();
                      l((S) => n(y, S), [() => a("render.extra_ready")]), v(u, y);
                    },
                    $$slots: { default: !0 }
                  });
                  var nt = o(Z, 2), _t = e(nt);
                  {
                    let u = f(() => !i(h).path);
                    ft(_t, {
                      get disabled() {
                        return i(u);
                      },
                      onclick: () => z(i(h).path),
                      children: (P, y) => {
                        var S = J();
                        l((W) => n(S, W), [() => a("common.reveal")]), v(P, S);
                      },
                      $$slots: { default: !0 }
                    });
                  }
                  l(
                    (u, P) => {
                      n(X, u), n(lt, P);
                    },
                    [
                      () => String(i(h).label || a("render.extra_artifacts")),
                      () => a("render.extra_count", { count: String(i(h).count || 0) })
                    ]
                  ), v(B, F);
                }), v(p, $);
              };
              N(O, (p) => {
                !i(Gt).length && !s.extras.length ? p(K) : p(G, -1);
              });
            }
            var H = o(R, 2), at = e(H);
            {
              let p = f(() => !!s.busyAction || !i(Kt));
              ft(at, {
                variant: "strong",
                get disabled() {
                  return i(p);
                },
                onclick: A,
                children: ($, x) => {
                  var j = J();
                  l((B) => n(j, B), [() => a("render.export_video")]), v($, j);
                },
                $$slots: { default: !0 }
              });
            }
            var Y = o(at, 2);
            ft(Y, {
              onclick: () => b().navigate("diagnostics"),
              children: (p, $) => {
                var x = J();
                l((j) => n(x, j), [() => a("render.open_diagnostics")]), v(p, x);
              },
              $$slots: { default: !0 }
            });
            var st = o(Y, 2);
            ft(st, {
              onclick: E,
              children: (p, $) => {
                var x = J();
                l((j) => n(x, j), [() => a("render.reveal_output")]), v(p, x);
              },
              $$slots: { default: !0 }
            });
            var it = o(H, 2);
            {
              var pt = (p) => {
                var $ = rr(), x = e($);
                l((j) => n(x, j), [() => a("render.locked_hint_export")]), v(p, $);
              };
              N(it, (p) => {
                i(Kt) || p(pt);
              });
            }
            v(ct, L);
          },
          $$slots: { headerRight: !0, default: !0 }
        });
      }
      var Pt = o(rt, 2), At = e(Pt);
      {
        let k = f(() => a("render.preview_title")), T = f(() => a("render.preview_sub"));
        Tt(At, {
          get title() {
            return i(k);
          },
          get sub() {
            return i(T);
          },
          children: (q, ct) => {
            var D = nr(), L = yt(D);
            {
              var R = (u) => {
                var P = sr();
                l(() => De(P, "src", i(pe))), v(u, P);
              }, O = (u) => {
                var P = ir();
                v(u, P);
              };
              N(L, (u) => {
                i(wt) ? u(R) : u(O, -1);
              });
            }
            var K = o(L, 2), G = e(K), H = e(G), at = e(H), Y = o(H), st = e(Y), it = o(G, 2), pt = e(it), p = e(pt), $ = o(pt), x = e($), j = o(it, 2), B = e(j), h = e(B), F = o(B), V = e(F), Q = o(j, 2), X = e(Q), vt = e(X), lt = o(X), Z = e(lt), nt = o(K, 2), _t = e(nt);
            ft(_t, {
              variant: "primary",
              onclick: E,
              children: (u, P) => {
                var y = J();
                l((S) => n(y, S), [() => a("render.reveal")]), v(u, y);
              },
              $$slots: { default: !0 }
            }), l(
              (u, P, y, S, W, tt, ut, Lt) => {
                n(at, u), n(st, P), n(p, y), n(x, S), n(h, W), n(V, tt), n(vt, ut), n(Z, `${Lt ?? ""}\\artifacts\\render`);
              },
              [
                () => a("render.summary_preset"),
                () => a("render.summary_preset_value"),
                () => a("render.summary_audio_mix"),
                () => ce(s.effectiveTts.mix_mode),
                () => a("render.summary_subtitle_mode"),
                () => qt(s.renderSubtitleMode),
                () => a("render.summary_output_folder"),
                () => c()
              ]
            ), v(q, D);
          },
          $$slots: { default: !0 }
        });
      }
      var Dt = o(At, 2);
      {
        let k = f(() => a("render.current_title")), T = f(() => a("render.current_sub"));
        Tt(Dt, {
          get title() {
            return i(k);
          },
          get sub() {
            return i(T);
          },
          children: (q, ct) => {
            var D = or(), L = e(D), R = e(L), O = o(L, 2), K = e(O), G = o(O, 2);
            Je(G, {
              get percent() {
                return i(Ht);
              },
              style: "margin-top:14px"
            });
            var H = o(G, 2), at = e(H);
            l(
              (Y, st, it) => {
                n(R, Y), n(K, st), n(at, it);
              },
              [
                () => s.progress?.current_stage_label || a("render.current_idle"),
                () => le(),
                () => a("render.progress_value", { percent: String(i(Ht)) })
              ]
            ), v(q, D);
          },
          $$slots: { default: !0 }
        });
      }
      v(t, r);
    };
    N(be, (t) => {
      i(he) ? t(xe) : s.loading ? t(ye, 1) : t(ke, -1);
    });
  }
  v(Mt, Qt), Ne();
}
const se = ze(cr), br = se.mount, xr = se.unmount;
export {
  br as mount,
  xr as unmount
};
//# sourceMappingURL=render.js.map
