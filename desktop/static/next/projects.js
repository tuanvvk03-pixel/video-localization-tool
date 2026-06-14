import { d as Ir, p as Lr, s as E, w as Pt, x as Or, c as w, e as _, i as H, g as t, l as i, Q as ft, t as p, j as o, R as ht, m as z, a as c, b as qr, h as a, f as re, o as A, r as ie, K as vt, z as Rr, n as O, u as y, A as Vr, O as sa, M as Dr } from "./chunks/api-vHpIWCot.js";
import { o as Mr } from "./chunks/index-client-CjB8cgHo.js";
import { e as oe, i as la } from "./chunks/each-BE197-93.js";
import { b as na } from "./chunks/input-D0G7l_P3.js";
import { n as X, a as Ur } from "./chunks/helpers-CRY6gGMH.js";
import { B as F } from "./chunks/Button-GpBM5g0S.js";
import { S as Kr } from "./chunks/StatusBadge-DT3lodBA.js";
import { s as Tr } from "./chunks/screen-DRq5NjFu.js";
var Qr = O('<div class="error-banner"><div class="error-code">UI</div><div class="error-message"> </div></div>'), Gr = O('<div class="info-banner"> </div>'), da = O("<option> </option>"), Hr = O('<div class="toolbar"><input class="input" style="max-width:320px" type="text"/> <!></div> <div class="small-muted"> </div>', 1), Jr = O('<div class="small-muted"> </div> <div class="toolbar"><!> <!> <!></div> <div class="small-muted"> </div> <div class="toolbar"><select class="input" style="max-width:240px"><option> </option><!></select> <!> <!></div> <div class="toolbar"><input class="input" style="max-width:240px" type="text"/> <!></div> <div class="small-muted"> </div>', 1), Wr = O('<div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option><option> </option></select></div>'), Xr = O('<div class="empty-card"><div class="empty-icon">＋</div><h3> </h3><p> </p></div>'), Yr = O('<a target="_blank" rel="noopener"> </a>'), Zr = O('<tr><td><div class="row-title"> </div><div class="small-muted"> </div></td><td><!></td><td><!></td></tr>'), ti = O('<table class="review-table"><thead><tr><th> </th><th> </th><th> </th></tr></thead><tbody></tbody></table>'), ei = O('<div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option></select></div> <div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/></div> <div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/></div> <!></div> <div class="clip-row"><div class="clip-col"><div class="row-title"> </div> <div class="small-muted"> </div> <div class="toolbar"><!> <!></div></div> <div class="clip-col"><div class="row-title"> </div> <div class="small-muted"> </div> <div class="toolbar"><!> <!></div></div> <div class="clip-col"><div class="row-title"> </div> <div class="small-muted"> </div> <div class="toolbar"><!> <!></div></div></div> <div class="stack" style="gap:6px;margin-top:8px"><div class="card-title"> </div><div class="card-sub"> </div></div> <label class="checkbox-row"><input type="checkbox"/> </label> <div class="field-grid"><div class="field"><label> </label> <input class="input" type="range" min="0.8" max="1.2" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="1" max="1.3" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="-0.2" max="0.2" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0.7" max="1.3" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0.5" max="1.5" step="0.01"/></div></div> <div class="toolbar"><!></div></div></div> <div class="card"><div class="card-header"><div><div class="card-title"> </div> <div class="card-sub"> </div></div></div> <div class="card-body"><!></div></div>', 1), ai = O('<div class="screen stack" data-testid="projects-screen"><!> <!> <div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option>edge_tts</option><option>azure_tts</option></select></div> <div class="field"><label> </label> <select class="input"><option> </option><!></select></div> <div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option></select></div></div> <!></div></div> <!></div>');
function ri(va, se) {
  Lr(se, !0);
  const r = (e, s) => (se.ctx?.t ?? ((n) => n))(e, s);
  let Rt = E(""), u = E(""), q = E(Pt([])), bt = E(Pt({})), le = E(Pt([])), k = E(Pt({
    tts_provider: "edge_tts",
    tts_voice: "",
    mix_mode: "replace_original_speech"
  })), Vt = E(""), ct = E(!1), J = E(""), At = E(""), U = E(null), ne = E(Pt([])), R = E(""), Bt = E(""), Y = null;
  Mr(() => {
    Y && clearInterval(Y);
  }), Or(() => {
    ga(), Dt();
  });
  async function Dt() {
    try {
      const e = await w("/api/presets/list", {});
      _(ne, Array.isArray(e.presets) ? e.presets : [], !0);
    } catch {
    }
  }
  const ca = () => C("preset_save", async () => {
    const e = t(Bt).trim();
    if (!e) throw new Error(r("projects.preset_name_required"));
    if (!t(u)) throw new Error(r("projects.create_first"));
    await w("/api/presets/save", { name: e, project_root: t(u) }), _(Bt, ""), _(J, r("projects.preset_saved"), !0), await Dt();
  }), pa = () => C("preset_apply", async () => {
    !t(R) || !t(u) || (await w("/api/presets/apply", {
      preset_id: t(R),
      project_root: t(u)
    }), _(J, r("projects.preset_applied"), !0), await xt());
  }), ua = () => C("preset_delete", async () => {
    !t(R) || !window.confirm(r("projects.preset_confirm_delete")) || (await w("/api/presets/delete", { preset_id: t(R) }), _(R, ""), await Dt());
  });
  async function ga() {
    try {
      const e = await w("/api/list-voices", {});
      _(
        le,
        Array.isArray(e.voices) ? e.voices.filter((s) => s && s.voice_id && s.enabled !== !1) : [],
        !0
      );
    } catch {
    }
  }
  async function C(e, s) {
    _(At, ""), _(Vt, e, !0), _(J, "");
    try {
      await s();
    } catch (n) {
      _(At, n instanceof Vr ? n.summary || n.message : n?.message || "error", !0);
    } finally {
      _(Vt, "");
    }
  }
  const S = () => !!t(Vt) || t(ct), ma = () => C("create", async () => {
    const e = t(Rt).trim();
    if (!e) throw new Error(r("projects.name_required"));
    const s = await w("/api/init-project", {
      project_name: e,
      config_overrides: {
        tts_provider: t(k).tts_provider,
        tts_voice: t(k).tts_voice.trim(),
        mix_mode: t(k).mix_mode,
        translate_backend: "block_v2"
      }
    });
    _(u, String(s.project_root || ""), !0), _(J, r("projects.created"), !0), await xt();
  }), fa = () => C("add", async () => {
    if (!t(u)) throw new Error(r("projects.create_first"));
    const e = await Dr({
      filters: ["Video files (*.mp4;*.mov;*.mkv;*.webm)", "All files (*.*)"]
    });
    if (e?.cancelled) return;
    const s = e?.paths || [];
    if (!s.length) throw new Error(e?.error || r("projects.pick_unavailable"));
    let n = 0;
    const j = [];
    for (const B of s)
      try {
        await w("/api/add-video-to-project", { project_root: t(u), video: B }), n++;
      } catch {
        j.push(B.split(/[\\/]/).pop() || B);
      }
    _(J, r("projects.added", { count: n }) + (j.length ? ` (${r("projects.add_failed", { count: j.length })})` : "")), await xt();
  });
  async function xt() {
    if (!t(u)) return;
    const e = await w("/api/get-project", { project_root: t(u) });
    _(q, Array.isArray(e.videos) ? e.videos : [], !0);
    const s = {};
    for (const n of e.statuses || []) s[String(n.video_id)] = n;
    _(bt, s, !0), e.config && _(
      k,
      {
        tts_provider: e.config.tts_provider || "edge_tts",
        tts_voice: e.config.tts_voice || "",
        mix_mode: e.config.mix_mode || "replace_original_speech"
      },
      !0
    ), await ha();
  }
  async function ha() {
    if (t(u))
      try {
        const e = await w("/api/render-settings/status", { job_workspace: t(u) });
        _(U, X(e.render || {}), !0);
      } catch {
      }
  }
  function Mt() {
    const e = t(U) || X({}), s = {
      aspect_ratio: e.aspect_ratio,
      background_path: e.background_path,
      background_original_filename: e.background_original_filename,
      head_trim_sec: e.head_trim_sec,
      tail_trim_sec: e.tail_trim_sec
    };
    return e.logo_path && Object.assign(s, {
      logo_path: e.logo_path,
      logo_original_filename: e.logo_original_filename,
      logo_position: e.logo_position,
      logo_scale: e.logo_scale,
      logo_opacity: e.logo_opacity,
      logo_margin: e.logo_margin
    }), e.intro_clip_path && Object.assign(s, {
      intro_clip_path: e.intro_clip_path,
      intro_original_filename: e.intro_original_filename
    }), e.outro_clip_path && Object.assign(s, {
      outro_clip_path: e.outro_clip_path,
      outro_original_filename: e.outro_original_filename
    }), Ur(s, e), s;
  }
  function K(e) {
    _(U, X({ ...t(U) || {}, ...e }), !0);
  }
  const ba = () => C("brand_save", async () => {
    const e = await w("/api/render-settings/save", { job_workspace: t(u), render: Mt() });
    _(U, X(e.render), !0), _(J, r("projects.brand_saved"), !0);
  }), xa = () => C("brand_logo", async () => {
    const e = await sa({
      filters: ["Image files (*.png;*.jpg;*.jpeg;*.webp)", "All files (*.*)"]
    });
    if (e?.cancelled) return;
    if (!e?.ok || !e.path) throw new Error(e?.error || r("projects.pick_unavailable"));
    await w("/api/render-settings/save", { job_workspace: t(u), render: Mt() });
    const s = await w("/api/render-logo/upload", { job_workspace: t(u), image_path: e.path });
    _(U, X(s.render), !0);
  }), ya = () => C("brand_logo_rm", async () => {
    const e = await w("/api/render-logo/remove", { job_workspace: t(u) });
    _(U, X(e.render), !0);
  }), de = (e) => C(`brand_${e}`, async () => {
    const s = await sa({
      filters: ["Video files (*.mp4;*.mov;*.mkv;*.webm)", "All files (*.*)"]
    });
    if (s?.cancelled) return;
    if (!s?.ok || !s.path) throw new Error(s?.error || r("projects.pick_unavailable"));
    await w("/api/render-settings/save", { job_workspace: t(u), render: Mt() });
    const n = await w(`/api/render-${e}/upload`, { job_workspace: t(u), clip_path: s.path });
    _(U, X(n.render), !0);
  }), _e = (e) => C(`brand_${e}_rm`, async () => {
    const s = await w(`/api/render-${e}/remove`, { job_workspace: t(u) });
    _(U, X(s.render), !0);
  }), $a = () => C("run", async () => {
    if (!t(u) || !t(q).length) throw new Error(r("projects.no_videos"));
    _(ct, !0);
    try {
      await w("/api/run-project", { project_root: t(u), async: !0 }), ja();
    } catch (e) {
      throw _(ct, !1), e;
    }
  });
  function ja() {
    Y && clearInterval(Y), Y = setInterval(
      async () => {
        try {
          await xt(), t(q).length && t(q).every((e) => wa(t(bt)[e.video_id])) && (_(ct, !1), Y && (clearInterval(Y), Y = null), _(J, r("projects.done"), !0));
        } catch {
        }
      },
      3e3
    );
  }
  function pt(e) {
    return String(e?.current_stage || e?.status || "queued");
  }
  function wa(e) {
    const s = pt(e);
    return s.includes("rendered") || s.includes("failed");
  }
  function ka(e) {
    const s = pt(e);
    return s.includes("failed") ? "blocked" : s.includes("rendered") ? "completed" : t(ct) ? "running" : "queued";
  }
  function Pa(e) {
    const s = String(e?.workspace || "");
    return s ? `/media?${new URLSearchParams({
      workspace: s,
      rel: "artifacts/render/final.mp4",
      v: String(Date.now())
    }).toString()}` : "";
  }
  const Aa = y(() => t(q).filter((e) => pt(t(bt)[e.video_id]).includes("rendered")).length), Ba = y(() => t(q).filter((e) => pt(t(bt)[e.video_id]).includes("failed")).length), d = y(() => t(U) || X({})), Ut = (e) => (e || "").split(/[\\/]/).pop();
  var ve = ai(), ce = a(ve);
  {
    var Na = (e) => {
      var s = Qr(), n = i(a(s)), j = a(n);
      p(() => o(j, t(At))), c(e, s);
    };
    H(ce, (e) => {
      t(At) && e(Na);
    });
  }
  var pe = i(ce, 2);
  {
    var Sa = (e) => {
      var s = Gr(), n = a(s);
      p(() => o(n, t(J))), c(e, s);
    };
    H(pe, (e) => {
      t(J) && e(Sa);
    });
  }
  var ue = i(pe, 2), ge = a(ue), Ea = a(ge), me = a(Ea), za = a(me), Fa = i(me), Ca = a(Fa), Ia = i(ge, 2), fe = a(Ia), he = a(fe), be = a(he), La = a(be), ot = i(be, 2), Kt = a(ot);
  Kt.value = Kt.__value = "edge_tts";
  var xe = i(Kt);
  xe.value = xe.__value = "azure_tts";
  var ye;
  ft(ot);
  var $e = i(he, 2), je = a($e), Oa = a(je), st = i(je, 2), Nt = a(st), qa = a(Nt);
  Nt.value = Nt.__value = "";
  var Ra = i(Nt);
  oe(Ra, 17, () => t(le), la, (e, s) => {
    var n = da(), j = a(n), B = {};
    p(() => {
      o(j, t(s).short_name || t(s).label || t(s).voice_id), B !== (B = t(s).voice_id) && (n.value = (n.__value = t(s).voice_id) ?? "");
    }), c(e, n);
  });
  var we;
  ft(st);
  var Va = i($e, 2), ke = a(Va), Da = a(ke), lt = i(ke, 2), St = a(lt), Ma = a(St);
  St.value = St.__value = "replace_original_speech";
  var Et = i(St), Ua = a(Et);
  Et.value = Et.__value = "duck_original_speech";
  var Tt = i(Et), Ka = a(Tt);
  Tt.value = Tt.__value = "keep_music_replace_voice";
  var Pe;
  ft(lt);
  var Ta = i(fe, 2);
  {
    var Qa = (e) => {
      var s = Hr(), n = re(s), j = a(n), B = i(j, 2);
      {
        let V = y(S);
        F(B, {
          variant: "primary",
          get disabled() {
            return t(V);
          },
          onclick: ma,
          children: (T, zt) => {
            var tt = A();
            p((I) => o(tt, I), [() => r("projects.create")]), c(T, tt);
          },
          $$slots: { default: !0 }
        });
      }
      var W = i(n, 2), Z = a(W);
      p(
        (V, T) => {
          ie(j, "placeholder", V), o(Z, T);
        },
        [
          () => r("projects.name_placeholder"),
          () => r("projects.create_hint")
        ]
      ), na(j, () => t(Rt), (V) => _(Rt, V)), c(e, s);
    }, Ga = (e) => {
      var s = Jr(), n = re(s), j = a(n), B = i(n, 2), W = a(B);
      {
        let f = y(S);
        F(W, {
          variant: "secondary",
          get disabled() {
            return t(f);
          },
          onclick: fa,
          children: (b, N) => {
            var m = A();
            p(($) => o(m, $), [() => r("projects.add_videos")]), c(b, m);
          },
          $$slots: { default: !0 }
        });
      }
      var Z = i(W, 2);
      {
        let f = y(() => S() || !t(q).length);
        F(Z, {
          variant: "strong",
          get disabled() {
            return t(f);
          },
          onclick: $a,
          children: (b, N) => {
            var m = A();
            p(($) => o(m, $), [
              () => t(ct) ? r("projects.running") : r("projects.run_all")
            ]), c(b, m);
          },
          $$slots: { default: !0 }
        });
      }
      var V = i(Z, 2);
      {
        let f = y(S);
        F(V, {
          get disabled() {
            return t(f);
          },
          onclick: () => C("refresh", xt),
          children: (b, N) => {
            var m = A();
            p(($) => o(m, $), [() => r("projects.refresh")]), c(b, m);
          },
          $$slots: { default: !0 }
        });
      }
      var T = i(B, 2), zt = a(T), tt = i(T, 2), I = a(tt), nt = a(I), Qt = a(nt);
      nt.value = nt.__value = "";
      var et = i(nt);
      oe(et, 17, () => t(ne), la, (f, b) => {
        var N = da(), m = a(N), $ = {};
        p(() => {
          o(m, t(b).name), $ !== ($ = t(b).id) && (N.value = (N.__value = t(b).id) ?? "");
        }), c(f, N);
      });
      var dt;
      ft(I);
      var Ft = i(I, 2);
      {
        let f = y(() => S() || !t(R));
        F(Ft, {
          get disabled() {
            return t(f);
          },
          onclick: pa,
          children: (b, N) => {
            var m = A();
            p(($) => o(m, $), [() => r("projects.preset_apply")]), c(b, m);
          },
          $$slots: { default: !0 }
        });
      }
      var yt = i(Ft, 2);
      {
        let f = y(() => S() || !t(R));
        F(yt, {
          get disabled() {
            return t(f);
          },
          onclick: ua,
          children: (b, N) => {
            var m = A();
            p(($) => o(m, $), [() => r("projects.preset_delete")]), c(b, m);
          },
          $$slots: { default: !0 }
        });
      }
      var Ct = i(tt, 2), ut = a(Ct), It = i(ut, 2);
      {
        let f = y(S);
        F(It, {
          get disabled() {
            return t(f);
          },
          onclick: ca,
          children: (b, N) => {
            var m = A();
            p(($) => o(m, $), [() => r("projects.preset_save")]), c(b, m);
          },
          $$slots: { default: !0 }
        });
      }
      var Lt = i(Ct, 2), Gt = a(Lt);
      p(
        (f, b, N, m, $) => {
          o(j, `${f ?? ""}: ${t(u) ?? ""}`), o(zt, b), o(Qt, N), dt !== (dt = t(R)) && (I.value = (I.__value = t(R)) ?? "", ht(I, t(R))), ie(ut, "placeholder", m), o(Gt, $);
        },
        [
          () => r("projects.open_label"),
          () => r("projects.cfg_locked_hint"),
          () => r("projects.preset_select"),
          () => r("projects.preset_name_placeholder"),
          () => r("projects.preset_hint")
        ]
      ), z("change", I, (f) => _(R, f.target.value, !0)), na(ut, () => t(Bt), (f) => _(Bt, f)), c(e, s);
    };
    H(Ta, (e) => {
      t(u) ? e(Ga, -1) : e(Qa);
    });
  }
  var Ha = i(ue, 2);
  {
    var Ja = (e) => {
      var s = ei(), n = re(s), j = a(n), B = a(j), W = a(B), Z = a(W), V = i(W), T = a(V), zt = i(j, 2), tt = a(zt), I = a(tt), nt = a(I), Qt = a(nt), et = i(nt, 2), dt = a(et), Ft = a(dt);
      dt.value = dt.__value = "16:9";
      var yt = i(dt), Ct = a(yt);
      yt.value = yt.__value = "9:16";
      var ut;
      ft(et);
      var It = i(I, 2), Lt = a(It), Gt = a(Lt), f = i(Lt, 2), b = i(It, 2), N = a(b), m = a(N), $ = i(N, 2), Wa = i(b, 2);
      {
        var Xa = (l) => {
          var g = Wr(), x = a(g), h = a(x), v = i(x, 2), P = a(v), at = a(P);
          P.value = P.__value = "top-left";
          var Q = i(P), $t = a(Q);
          Q.value = Q.__value = "top-right";
          var rt = i(Q), jt = a(rt);
          rt.value = rt.__value = "bottom-left";
          var D = i(rt), M = a(D);
          D.value = D.__value = "bottom-right";
          var G;
          ft(v), p(
            (it, gt, mt, wt, kt) => {
              o(h, it), o(at, gt), o($t, mt), o(jt, wt), o(M, kt), G !== (G = t(d).logo_position) && (v.value = (v.__value = t(d).logo_position) ?? "", ht(v, t(d).logo_position));
            },
            [
              () => r("settings.render_layout.logo_position"),
              () => r("settings.render_layout.pos_top_left"),
              () => r("settings.render_layout.pos_top_right"),
              () => r("settings.render_layout.pos_bottom_left"),
              () => r("settings.render_layout.pos_bottom_right")
            ]
          ), z("change", v, (it) => K({ logo_position: it.target.value })), c(l, g);
        };
        H(Wa, (l) => {
          t(d).logo_path && l(Xa);
        });
      }
      var Ae = i(tt, 2), Be = a(Ae), Ne = a(Be), Ya = a(Ne), Se = i(Ne, 2), Za = a(Se), tr = i(Se, 2), Ee = a(tr);
      {
        let l = y(S);
        F(Ee, {
          variant: "secondary",
          get disabled() {
            return t(l);
          },
          onclick: xa,
          children: (g, x) => {
            var h = A();
            p((v) => o(h, v), [() => r("settings.render_layout.upload_logo")]), c(g, h);
          },
          $$slots: { default: !0 }
        });
      }
      var er = i(Ee, 2);
      {
        var ar = (l) => {
          {
            let g = y(S);
            F(l, {
              get disabled() {
                return t(g);
              },
              onclick: ya,
              children: (x, h) => {
                var v = A();
                p((P) => o(v, P), [() => r("settings.render_layout.remove_logo")]), c(x, v);
              },
              $$slots: { default: !0 }
            });
          }
        };
        H(er, (l) => {
          t(d).logo_path && l(ar);
        });
      }
      var ze = i(Be, 2), Fe = a(ze), rr = a(Fe), Ce = i(Fe, 2), ir = a(Ce), or = i(Ce, 2), Ie = a(or);
      {
        let l = y(S);
        F(Ie, {
          variant: "secondary",
          get disabled() {
            return t(l);
          },
          onclick: () => de("intro"),
          children: (g, x) => {
            var h = A();
            p((v) => o(h, v), [() => r("settings.render_layout.upload_intro")]), c(g, h);
          },
          $$slots: { default: !0 }
        });
      }
      var sr = i(Ie, 2);
      {
        var lr = (l) => {
          {
            let g = y(S);
            F(l, {
              get disabled() {
                return t(g);
              },
              onclick: () => _e("intro"),
              children: (x, h) => {
                var v = A();
                p((P) => o(v, P), [() => r("settings.render_layout.remove_clip")]), c(x, v);
              },
              $$slots: { default: !0 }
            });
          }
        };
        H(sr, (l) => {
          t(d).intro_clip_path && l(lr);
        });
      }
      var nr = i(ze, 2), Le = a(nr), dr = a(Le), Oe = i(Le, 2), _r = a(Oe), vr = i(Oe, 2), qe = a(vr);
      {
        let l = y(S);
        F(qe, {
          variant: "secondary",
          get disabled() {
            return t(l);
          },
          onclick: () => de("outro"),
          children: (g, x) => {
            var h = A();
            p((v) => o(h, v), [() => r("settings.render_layout.upload_outro")]), c(g, h);
          },
          $$slots: { default: !0 }
        });
      }
      var cr = i(qe, 2);
      {
        var pr = (l) => {
          {
            let g = y(S);
            F(l, {
              get disabled() {
                return t(g);
              },
              onclick: () => _e("outro"),
              children: (x, h) => {
                var v = A();
                p((P) => o(v, P), [() => r("settings.render_layout.remove_clip")]), c(x, v);
              },
              $$slots: { default: !0 }
            });
          }
        };
        H(cr, (l) => {
          t(d).outro_clip_path && l(pr);
        });
      }
      var Re = i(Ae, 2), Ve = a(Re), ur = a(Ve), gr = i(Ve), mr = a(gr), De = i(Re, 2), Ht = a(De), fr = i(Ht, 1, !0), Me = i(De, 2), Ue = a(Me), Ke = a(Ue), hr = a(Ke), Te = i(Ke, 2), Qe = i(Ue, 2), Ge = a(Qe), br = a(Ge), He = i(Ge, 2), Je = i(Qe, 2), We = a(Je), xr = a(We), Xe = i(We, 2), Ye = i(Je, 2), Ze = a(Ye), yr = a(Ze), ta = i(Ze, 2), $r = i(Ye, 2), ea = a($r), jr = a(ea), aa = i(ea, 2), wr = i(Me, 2), kr = a(wr);
      {
        let l = y(S);
        F(kr, {
          variant: "primary",
          get disabled() {
            return t(l);
          },
          onclick: ba,
          children: (g, x) => {
            var h = A();
            p((v) => o(h, v), [() => r("settings.render_layout.save")]), c(g, h);
          },
          $$slots: { default: !0 }
        });
      }
      var Pr = i(n, 2), ra = a(Pr), Ar = a(ra), ia = a(Ar), Br = a(ia), Nr = i(ia, 2), Sr = a(Nr), Er = i(ra, 2), zr = a(Er);
      {
        var Fr = (l) => {
          var g = Xr(), x = i(a(g)), h = a(x), v = i(x), P = a(v);
          p(
            (at, Q) => {
              o(h, at), o(P, Q);
            },
            [
              () => r("projects.empty_title"),
              () => r("projects.empty_body")
            ]
          ), c(l, g);
        }, Cr = (l) => {
          var g = ti(), x = a(g), h = a(x), v = a(h), P = a(v), at = i(v), Q = a(at), $t = i(at), rt = a($t), jt = i(x);
          oe(jt, 21, () => t(q), (D) => D.video_id, (D, M) => {
            const G = y(() => t(bt)[t(M).video_id]);
            var it = Zr(), gt = a(it), mt = a(gt), wt = a(mt), kt = i(mt), Jt = a(kt), Ot = i(gt), Wt = a(Ot);
            {
              let L = y(() => ka(t(G)));
              Kr(Wt, {
                get kind() {
                  return t(L);
                },
                children: (_t, oa) => {
                  var qt = A();
                  p((ae) => o(qt, ae), [() => pt(t(G))]), c(_t, qt);
                },
                $$slots: { default: !0 }
              });
            }
            var Xt = i(Ot), Yt = a(Xt);
            {
              var Zt = (L) => {
                var _t = Yr(), oa = a(_t);
                p(
                  (qt, ae) => {
                    ie(_t, "href", qt), o(oa, ae);
                  },
                  [() => Pa(t(M)), () => r("projects.open_output")]
                ), c(L, _t);
              }, te = y(() => pt(t(G)).includes("rendered")), ee = (L) => {
                var _t = A("—");
                c(L, _t);
              };
              H(Yt, (L) => {
                t(te) ? L(Zt) : L(ee, -1);
              });
            }
            p(
              (L) => {
                o(wt, t(M).video_id), o(Jt, `${L ?? ""}${t(M).is_long ? " · long" : ""}`);
              },
              [() => (t(M).source_path || "").split(/[\\/]/).pop()]
            ), c(D, it);
          }), p(
            (D, M, G) => {
              o(P, D), o(Q, M), o(rt, G);
            },
            [
              () => r("projects.col_video"),
              () => r("projects.col_status"),
              () => r("projects.col_output")
            ]
          ), c(l, g);
        };
        H(zr, (l) => {
          t(q).length ? l(Cr, -1) : l(Fr);
        });
      }
      p(
        (l, g, x, h, v, P, at, Q, $t, rt, jt, D, M, G, it, gt, mt, wt, kt, Jt, Ot, Wt, Xt, Yt, Zt, te, ee, L) => {
          o(Z, l), o(T, g), o(Qt, x), o(Ft, h), o(Ct, v), ut !== (ut = t(d).aspect_ratio) && (et.value = (et.__value = t(d).aspect_ratio) ?? "", ht(et, t(d).aspect_ratio)), o(Gt, `${P ?? ""} (${t(d).head_trim_sec ?? ""}s)`), vt(f, t(d).head_trim_sec), o(m, `${at ?? ""} (${t(d).tail_trim_sec ?? ""}s)`), vt($, t(d).tail_trim_sec), o(Ya, Q), o(Za, $t), o(rr, rt), o(ir, jt), o(dr, D), o(_r, M), o(ur, G), o(mr, it), Rr(Ht, t(d).transform_hflip), o(fr, gt), o(hr, `${mt ?? ""} (${wt ?? ""}x)`), vt(Te, t(d).transform_speed), o(br, `${kt ?? ""} (${Jt ?? ""}%)`), vt(He, t(d).transform_zoom), o(xr, `${Ot ?? ""} (${Wt ?? ""})`), vt(Xe, t(d).transform_brightness), o(yr, `${Xt ?? ""} (${Yt ?? ""})`), vt(ta, t(d).transform_contrast), o(jr, `${Zt ?? ""} (${te ?? ""})`), vt(aa, t(d).transform_saturation), o(Br, ee), o(Sr, L);
        },
        [
          () => r("projects.brand_title"),
          () => r("projects.brand_sub"),
          () => r("settings.render_layout.aspect_ratio"),
          () => r("settings.render_layout.aspect_16_9"),
          () => r("settings.render_layout.aspect_9_16"),
          () => r("settings.render_layout.head_trim"),
          () => r("settings.render_layout.tail_trim"),
          () => r("settings.render_layout.logo_title"),
          () => t(d).logo_path ? Ut(t(d).logo_original_filename || t(d).logo_path) : r("settings.render_layout.no_logo"),
          () => r("settings.render_layout.intro_clip"),
          () => t(d).intro_clip_path ? Ut(t(d).intro_original_filename || t(d).intro_clip_path) : r("settings.render_layout.no_clip"),
          () => r("settings.render_layout.outro_clip"),
          () => t(d).outro_clip_path ? Ut(t(d).outro_original_filename || t(d).outro_clip_path) : r("settings.render_layout.no_clip"),
          () => r("settings.render_layout.tx_title"),
          () => r("settings.render_layout.tx_sub"),
          () => r("settings.render_layout.tx_hflip"),
          () => r("settings.render_layout.tx_speed"),
          () => t(d).transform_speed.toFixed(2),
          () => r("settings.render_layout.tx_zoom"),
          () => Math.round((t(d).transform_zoom - 1) * 100),
          () => r("settings.render_layout.tx_brightness"),
          () => t(d).transform_brightness.toFixed(2),
          () => r("settings.render_layout.tx_contrast"),
          () => t(d).transform_contrast.toFixed(2),
          () => r("settings.render_layout.tx_saturation"),
          () => t(d).transform_saturation.toFixed(2),
          () => r("projects.videos_title", { count: t(q).length }),
          () => r("projects.progress_summary", {
            done: t(Aa),
            failed: t(Ba),
            total: t(q).length
          })
        ]
      ), z("change", et, (l) => K({ aspect_ratio: l.target.value })), z("change", f, (l) => K({ head_trim_sec: Number(l.target.value) })), z("change", $, (l) => K({ tail_trim_sec: Number(l.target.value) })), z("change", Ht, (l) => K({ transform_hflip: l.target.checked })), z("input", Te, (l) => K({ transform_speed: Number(l.target.value) })), z("input", He, (l) => K({ transform_zoom: Number(l.target.value) })), z("input", Xe, (l) => K({ transform_brightness: Number(l.target.value) })), z("input", ta, (l) => K({ transform_contrast: Number(l.target.value) })), z("input", aa, (l) => K({ transform_saturation: Number(l.target.value) })), c(e, s);
    };
    H(Ha, (e) => {
      t(u) && e(Ja);
    });
  }
  p(
    (e, s, n, j, B, W, Z, V, T) => {
      o(za, e), o(Ca, s), o(La, n), ot.disabled = !!t(u), ye !== (ye = t(k).tts_provider) && (ot.value = (ot.__value = t(k).tts_provider) ?? "", ht(ot, t(k).tts_provider)), o(Oa, j), st.disabled = !!t(u), o(qa, B), we !== (we = t(k).tts_voice) && (st.value = (st.__value = t(k).tts_voice) ?? "", ht(st, t(k).tts_voice)), o(Da, W), lt.disabled = !!t(u), o(Ma, Z), o(Ua, V), o(Ka, T), Pe !== (Pe = t(k).mix_mode) && (lt.value = (lt.__value = t(k).mix_mode) ?? "", ht(lt, t(k).mix_mode));
    },
    [
      () => r("projects.title"),
      () => r("projects.sub"),
      () => r("projects.cfg_provider"),
      () => r("projects.cfg_voice"),
      () => r("projects.cfg_voice_default"),
      () => r("projects.cfg_mix"),
      () => r("settings.tts.mix_replace"),
      () => r("settings.tts.mix_duck"),
      () => r("settings.tts.mix_keep_music")
    ]
  ), z("change", ot, (e) => t(k).tts_provider = e.target.value), z("change", st, (e) => t(k).tts_voice = e.target.value), z("change", lt, (e) => t(k).mix_mode = e.target.value), c(va, ve), qr();
}
Ir(["change", "input"]);
const _a = Tr(ri), ci = _a.mount, pi = _a.unmount;
export {
  ci as mount,
  pi as unmount
};
//# sourceMappingURL=projects.js.map
