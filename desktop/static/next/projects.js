import { d as kr, p as Pr, s as M, w as Pt, x as Br, c as w, e as p, i as U, g as t, l as r, Q as gt, t as u, j as s, R as mt, m as k, a as _, b as Ar, h as a, f as Ut, o as P, r as We, K as it, z as Nr, n as S, u as h, A as Sr, O as Xe, M as zr } from "./chunks/api-vHpIWCot.js";
import { o as Er } from "./chunks/index-client-CjB8cgHo.js";
import { e as Ye, i as Fr } from "./chunks/each-BE197-93.js";
import { b as Cr } from "./chunks/input-D0G7l_P3.js";
import { n as G, a as Ir } from "./chunks/helpers-CRY6gGMH.js";
import { B as L } from "./chunks/Button-GpBM5g0S.js";
import { S as Lr } from "./chunks/StatusBadge-DT3lodBA.js";
import { s as Or } from "./chunks/screen-DRq5NjFu.js";
var Rr = S('<div class="error-banner"><div class="error-code">UI</div><div class="error-message"> </div></div>'), Vr = S('<div class="info-banner"> </div>'), qr = S("<option> </option>"), Dr = S('<div class="toolbar"><input class="input" style="max-width:320px" type="text"/> <!></div> <div class="small-muted"> </div>', 1), Mr = S('<div class="small-muted"> </div> <div class="toolbar"><!> <!> <!></div> <div class="small-muted"> </div>', 1), Ur = S('<div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option><option> </option></select></div>'), Kr = S('<div class="empty-card"><div class="empty-icon">＋</div><h3> </h3><p> </p></div>'), Tr = S('<a target="_blank" rel="noopener"> </a>'), Qr = S('<tr><td><div class="row-title"> </div><div class="small-muted"> </div></td><td><!></td><td><!></td></tr>'), Gr = S('<table class="review-table"><thead><tr><th> </th><th> </th><th> </th></tr></thead><tbody></tbody></table>'), Hr = S('<div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option></select></div> <div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/></div> <div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/></div> <!></div> <div class="clip-row"><div class="clip-col"><div class="row-title"> </div> <div class="small-muted"> </div> <div class="toolbar"><!> <!></div></div> <div class="clip-col"><div class="row-title"> </div> <div class="small-muted"> </div> <div class="toolbar"><!> <!></div></div> <div class="clip-col"><div class="row-title"> </div> <div class="small-muted"> </div> <div class="toolbar"><!> <!></div></div></div> <div class="stack" style="gap:6px;margin-top:8px"><div class="card-title"> </div><div class="card-sub"> </div></div> <label class="checkbox-row"><input type="checkbox"/> </label> <div class="field-grid"><div class="field"><label> </label> <input class="input" type="range" min="0.8" max="1.2" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="1" max="1.3" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="-0.2" max="0.2" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0.7" max="1.3" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0.5" max="1.5" step="0.01"/></div></div> <div class="toolbar"><!></div></div></div> <div class="card"><div class="card-header"><div><div class="card-title"> </div> <div class="card-sub"> </div></div></div> <div class="card-body"><!></div></div>', 1), Jr = S('<div class="screen stack" data-testid="projects-screen"><!> <!> <div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option>edge_tts</option><option>azure_tts</option></select></div> <div class="field"><label> </label> <select class="input"><option> </option><!></select></div> <div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option></select></div></div> <!></div></div> <!></div>');
function Wr(ta, Kt) {
  Pr(Kt, !0);
  const i = (e, o) => (Kt.ctx?.t ?? ((n) => n))(e, o);
  let Bt = M(""), g = M(""), z = M(Pt([])), dt = M(Pt({})), Tt = M(Pt([])), y = Pt({
    tts_provider: "edge_tts",
    tts_voice: "",
    mix_mode: "replace_original_speech"
  }), At = M(""), ot = M(!1), Z = M(""), ft = M(""), O = M(null), H = null;
  Er(() => {
    H && clearInterval(H);
  }), Br(() => {
    ea();
  });
  async function ea() {
    try {
      const e = await w("/api/list-voices", {});
      p(
        Tt,
        Array.isArray(e.voices) ? e.voices.filter((o) => o && o.voice_id && o.enabled !== !1) : [],
        !0
      );
    } catch {
    }
  }
  async function K(e, o) {
    p(ft, ""), p(At, e, !0), p(Z, "");
    try {
      await o();
    } catch (n) {
      p(ft, n instanceof Sr ? n.summary || n.message : n?.message || "error", !0);
    } finally {
      p(At, "");
    }
  }
  const E = () => !!t(At) || t(ot), aa = () => K("create", async () => {
    const e = t(Bt).trim();
    if (!e) throw new Error(i("projects.name_required"));
    const o = await w("/api/init-project", {
      project_name: e,
      config_overrides: {
        tts_provider: y.tts_provider,
        tts_voice: y.tts_voice.trim(),
        mix_mode: y.mix_mode,
        translate_backend: "block_v2"
      }
    });
    p(g, String(o.project_root || ""), !0), p(Z, i("projects.created"), !0), await bt();
  }), ra = () => K("add", async () => {
    if (!t(g)) throw new Error(i("projects.create_first"));
    const e = await zr({
      filters: ["Video files (*.mp4;*.mov;*.mkv;*.webm)", "All files (*.*)"]
    });
    if (e?.cancelled) return;
    const o = e?.paths || [];
    if (!o.length) throw new Error(e?.error || i("projects.pick_unavailable"));
    let n = 0;
    const b = [];
    for (const $ of o)
      try {
        await w("/api/add-video-to-project", { project_root: t(g), video: $ }), n++;
      } catch {
        b.push($.split(/[\\/]/).pop() || $);
      }
    p(Z, i("projects.added", { count: n }) + (b.length ? ` (${i("projects.add_failed", { count: b.length })})` : "")), await bt();
  });
  async function bt() {
    if (!t(g)) return;
    const e = await w("/api/get-project", { project_root: t(g) });
    p(z, Array.isArray(e.videos) ? e.videos : [], !0);
    const o = {};
    for (const n of e.statuses || []) o[String(n.video_id)] = n;
    p(dt, o, !0), await ia();
  }
  async function ia() {
    if (t(g))
      try {
        const e = await w("/api/render-settings/status", { job_workspace: t(g) });
        p(O, G(e.render || {}), !0);
      } catch {
      }
  }
  function Nt() {
    const e = t(O) || G({}), o = {
      aspect_ratio: e.aspect_ratio,
      background_path: e.background_path,
      background_original_filename: e.background_original_filename,
      head_trim_sec: e.head_trim_sec,
      tail_trim_sec: e.tail_trim_sec
    };
    return e.logo_path && Object.assign(o, {
      logo_path: e.logo_path,
      logo_original_filename: e.logo_original_filename,
      logo_position: e.logo_position,
      logo_scale: e.logo_scale,
      logo_opacity: e.logo_opacity,
      logo_margin: e.logo_margin
    }), e.intro_clip_path && Object.assign(o, {
      intro_clip_path: e.intro_clip_path,
      intro_original_filename: e.intro_original_filename
    }), e.outro_clip_path && Object.assign(o, {
      outro_clip_path: e.outro_clip_path,
      outro_original_filename: e.outro_original_filename
    }), Ir(o, e), o;
  }
  function R(e) {
    p(O, G({ ...t(O) || {}, ...e }), !0);
  }
  const oa = () => K("brand_save", async () => {
    const e = await w("/api/render-settings/save", { job_workspace: t(g), render: Nt() });
    p(O, G(e.render), !0), p(Z, i("projects.brand_saved"), !0);
  }), sa = () => K("brand_logo", async () => {
    const e = await Xe({
      filters: ["Image files (*.png;*.jpg;*.jpeg;*.webp)", "All files (*.*)"]
    });
    if (e?.cancelled) return;
    if (!e?.ok || !e.path) throw new Error(e?.error || i("projects.pick_unavailable"));
    await w("/api/render-settings/save", { job_workspace: t(g), render: Nt() });
    const o = await w("/api/render-logo/upload", { job_workspace: t(g), image_path: e.path });
    p(O, G(o.render), !0);
  }), la = () => K("brand_logo_rm", async () => {
    const e = await w("/api/render-logo/remove", { job_workspace: t(g) });
    p(O, G(e.render), !0);
  }), Qt = (e) => K(`brand_${e}`, async () => {
    const o = await Xe({
      filters: ["Video files (*.mp4;*.mov;*.mkv;*.webm)", "All files (*.*)"]
    });
    if (o?.cancelled) return;
    if (!o?.ok || !o.path) throw new Error(o?.error || i("projects.pick_unavailable"));
    await w("/api/render-settings/save", { job_workspace: t(g), render: Nt() });
    const n = await w(`/api/render-${e}/upload`, { job_workspace: t(g), clip_path: o.path });
    p(O, G(n.render), !0);
  }), Gt = (e) => K(`brand_${e}_rm`, async () => {
    const o = await w(`/api/render-${e}/remove`, { job_workspace: t(g) });
    p(O, G(o.render), !0);
  }), na = () => K("run", async () => {
    if (!t(g) || !t(z).length) throw new Error(i("projects.no_videos"));
    p(ot, !0);
    try {
      await w("/api/run-project", { project_root: t(g), async: !0 }), da();
    } catch (e) {
      throw p(ot, !1), e;
    }
  });
  function da() {
    H && clearInterval(H), H = setInterval(
      async () => {
        try {
          await bt(), t(z).length && t(z).every((e) => va(t(dt)[e.video_id])) && (p(ot, !1), H && (clearInterval(H), H = null), p(Z, i("projects.done"), !0));
        } catch {
        }
      },
      3e3
    );
  }
  function st(e) {
    return String(e?.current_stage || e?.status || "queued");
  }
  function va(e) {
    const o = st(e);
    return o.includes("rendered") || o.includes("failed");
  }
  function _a(e) {
    const o = st(e);
    return o.includes("failed") ? "blocked" : o.includes("rendered") ? "completed" : t(ot) ? "running" : "queued";
  }
  function ca(e) {
    const o = String(e?.workspace || "");
    return o ? `/media?${new URLSearchParams({
      workspace: o,
      rel: "artifacts/render/final.mp4",
      v: String(Date.now())
    }).toString()}` : "";
  }
  const pa = h(() => t(z).filter((e) => st(t(dt)[e.video_id]).includes("rendered")).length), ua = h(() => t(z).filter((e) => st(t(dt)[e.video_id]).includes("failed")).length), d = h(() => t(O) || G({})), St = (e) => (e || "").split(/[\\/]/).pop();
  var Ht = Jr(), Jt = a(Ht);
  {
    var ga = (e) => {
      var o = Rr(), n = r(a(o)), b = a(n);
      u(() => s(b, t(ft))), _(e, o);
    };
    U(Jt, (e) => {
      t(ft) && e(ga);
    });
  }
  var Wt = r(Jt, 2);
  {
    var ma = (e) => {
      var o = Vr(), n = a(o);
      u(() => s(n, t(Z))), _(e, o);
    };
    U(Wt, (e) => {
      t(Z) && e(ma);
    });
  }
  var Xt = r(Wt, 2), Yt = a(Xt), fa = a(Yt), Zt = a(fa), ba = a(Zt), ha = r(Zt), xa = a(ha), ya = r(Yt, 2), te = a(ya), ee = a(te), ae = a(ee), $a = a(ae), tt = r(ae, 2), zt = a(tt);
  zt.value = zt.__value = "edge_tts";
  var re = r(zt);
  re.value = re.__value = "azure_tts";
  var ie;
  gt(tt);
  var oe = r(ee, 2), se = a(oe), ja = a(se), et = r(se, 2), ht = a(et), wa = a(ht);
  ht.value = ht.__value = "";
  var ka = r(ht);
  Ye(ka, 17, () => t(Tt), Fr, (e, o) => {
    var n = qr(), b = a(n), $ = {};
    u(() => {
      s(b, t(o).short_name || t(o).label || t(o).voice_id), $ !== ($ = t(o).voice_id) && (n.value = (n.__value = t(o).voice_id) ?? "");
    }), _(e, n);
  });
  var le;
  gt(et);
  var Pa = r(oe, 2), ne = a(Pa), Ba = a(ne), at = r(ne, 2), xt = a(at), Aa = a(xt);
  xt.value = xt.__value = "replace_original_speech";
  var yt = r(xt), Na = a(yt);
  yt.value = yt.__value = "duck_original_speech";
  var Et = r(yt), Sa = a(Et);
  Et.value = Et.__value = "keep_music_replace_voice";
  var de;
  gt(at);
  var za = r(te, 2);
  {
    var Ea = (e) => {
      var o = Dr(), n = Ut(o), b = a(n), $ = r(b, 2);
      {
        let F = h(E);
        L($, {
          variant: "primary",
          get disabled() {
            return t(F);
          },
          onclick: aa,
          children: (Q, $t) => {
            var j = P();
            u((B) => s(j, B), [() => i("projects.create")]), _(Q, j);
          },
          $$slots: { default: !0 }
        });
      }
      var T = r(n, 2), J = a(T);
      u(
        (F, Q) => {
          We(b, "placeholder", F), s(J, Q);
        },
        [
          () => i("projects.name_placeholder"),
          () => i("projects.create_hint")
        ]
      ), Cr(b, () => t(Bt), (F) => p(Bt, F)), _(e, o);
    }, Fa = (e) => {
      var o = Mr(), n = Ut(o), b = a(n), $ = r(n, 2), T = a($);
      {
        let j = h(E);
        L(T, {
          variant: "secondary",
          get disabled() {
            return t(j);
          },
          onclick: ra,
          children: (B, vt) => {
            var V = P();
            u((A) => s(V, A), [() => i("projects.add_videos")]), _(B, V);
          },
          $$slots: { default: !0 }
        });
      }
      var J = r(T, 2);
      {
        let j = h(() => E() || !t(z).length);
        L(J, {
          variant: "strong",
          get disabled() {
            return t(j);
          },
          onclick: na,
          children: (B, vt) => {
            var V = P();
            u((A) => s(V, A), [
              () => t(ot) ? i("projects.running") : i("projects.run_all")
            ]), _(B, V);
          },
          $$slots: { default: !0 }
        });
      }
      var F = r(J, 2);
      {
        let j = h(E);
        L(F, {
          get disabled() {
            return t(j);
          },
          onclick: () => K("refresh", bt),
          children: (B, vt) => {
            var V = P();
            u((A) => s(V, A), [() => i("projects.refresh")]), _(B, V);
          },
          $$slots: { default: !0 }
        });
      }
      var Q = r($, 2), $t = a(Q);
      u(
        (j, B) => {
          s(b, `${j ?? ""}: ${t(g) ?? ""}`), s($t, B);
        },
        [
          () => i("projects.open_label"),
          () => i("projects.cfg_locked_hint")
        ]
      ), _(e, o);
    };
    U(za, (e) => {
      t(g) ? e(Fa, -1) : e(Ea);
    });
  }
  var Ca = r(Xt, 2);
  {
    var Ia = (e) => {
      var o = Hr(), n = Ut(o), b = a(n), $ = a(b), T = a($), J = a(T), F = r(T), Q = a(F), $t = r(b, 2), j = a($t), B = a(j), vt = a(B), V = a(vt), A = r(vt, 2), jt = a(A), La = a(jt);
      jt.value = jt.__value = "16:9";
      var Ft = r(jt), Oa = a(Ft);
      Ft.value = Ft.__value = "9:16";
      var ve;
      gt(A);
      var _e = r(B, 2), ce = a(_e), Ra = a(ce), pe = r(ce, 2), ue = r(_e, 2), ge = a(ue), Va = a(ge), me = r(ge, 2), qa = r(ue, 2);
      {
        var Da = (l) => {
          var c = Ur(), f = a(c), m = a(f), v = r(f, 2), x = a(v), W = a(x);
          x.value = x.__value = "top-left";
          var q = r(x), _t = a(q);
          q.value = q.__value = "top-right";
          var X = r(q), ct = a(X);
          X.value = X.__value = "bottom-left";
          var C = r(X), I = a(C);
          C.value = C.__value = "bottom-right";
          var D;
          gt(v), u(
            (Y, lt, nt, pt, ut) => {
              s(m, Y), s(W, lt), s(_t, nt), s(ct, pt), s(I, ut), D !== (D = t(d).logo_position) && (v.value = (v.__value = t(d).logo_position) ?? "", mt(v, t(d).logo_position));
            },
            [
              () => i("settings.render_layout.logo_position"),
              () => i("settings.render_layout.pos_top_left"),
              () => i("settings.render_layout.pos_top_right"),
              () => i("settings.render_layout.pos_bottom_left"),
              () => i("settings.render_layout.pos_bottom_right")
            ]
          ), k("change", v, (Y) => R({ logo_position: Y.target.value })), _(l, c);
        };
        U(qa, (l) => {
          t(d).logo_path && l(Da);
        });
      }
      var fe = r(j, 2), be = a(fe), he = a(be), Ma = a(he), xe = r(he, 2), Ua = a(xe), Ka = r(xe, 2), ye = a(Ka);
      {
        let l = h(E);
        L(ye, {
          variant: "secondary",
          get disabled() {
            return t(l);
          },
          onclick: sa,
          children: (c, f) => {
            var m = P();
            u((v) => s(m, v), [() => i("settings.render_layout.upload_logo")]), _(c, m);
          },
          $$slots: { default: !0 }
        });
      }
      var Ta = r(ye, 2);
      {
        var Qa = (l) => {
          {
            let c = h(E);
            L(l, {
              get disabled() {
                return t(c);
              },
              onclick: la,
              children: (f, m) => {
                var v = P();
                u((x) => s(v, x), [() => i("settings.render_layout.remove_logo")]), _(f, v);
              },
              $$slots: { default: !0 }
            });
          }
        };
        U(Ta, (l) => {
          t(d).logo_path && l(Qa);
        });
      }
      var $e = r(be, 2), je = a($e), Ga = a(je), we = r(je, 2), Ha = a(we), Ja = r(we, 2), ke = a(Ja);
      {
        let l = h(E);
        L(ke, {
          variant: "secondary",
          get disabled() {
            return t(l);
          },
          onclick: () => Qt("intro"),
          children: (c, f) => {
            var m = P();
            u((v) => s(m, v), [() => i("settings.render_layout.upload_intro")]), _(c, m);
          },
          $$slots: { default: !0 }
        });
      }
      var Wa = r(ke, 2);
      {
        var Xa = (l) => {
          {
            let c = h(E);
            L(l, {
              get disabled() {
                return t(c);
              },
              onclick: () => Gt("intro"),
              children: (f, m) => {
                var v = P();
                u((x) => s(v, x), [() => i("settings.render_layout.remove_clip")]), _(f, v);
              },
              $$slots: { default: !0 }
            });
          }
        };
        U(Wa, (l) => {
          t(d).intro_clip_path && l(Xa);
        });
      }
      var Ya = r($e, 2), Pe = a(Ya), Za = a(Pe), Be = r(Pe, 2), tr = a(Be), er = r(Be, 2), Ae = a(er);
      {
        let l = h(E);
        L(Ae, {
          variant: "secondary",
          get disabled() {
            return t(l);
          },
          onclick: () => Qt("outro"),
          children: (c, f) => {
            var m = P();
            u((v) => s(m, v), [() => i("settings.render_layout.upload_outro")]), _(c, m);
          },
          $$slots: { default: !0 }
        });
      }
      var ar = r(Ae, 2);
      {
        var rr = (l) => {
          {
            let c = h(E);
            L(l, {
              get disabled() {
                return t(c);
              },
              onclick: () => Gt("outro"),
              children: (f, m) => {
                var v = P();
                u((x) => s(v, x), [() => i("settings.render_layout.remove_clip")]), _(f, v);
              },
              $$slots: { default: !0 }
            });
          }
        };
        U(ar, (l) => {
          t(d).outro_clip_path && l(rr);
        });
      }
      var Ne = r(fe, 2), Se = a(Ne), ir = a(Se), or = r(Se), sr = a(or), ze = r(Ne, 2), Ct = a(ze), lr = r(Ct, 1, !0), Ee = r(ze, 2), Fe = a(Ee), Ce = a(Fe), nr = a(Ce), Ie = r(Ce, 2), Le = r(Fe, 2), Oe = a(Le), dr = a(Oe), Re = r(Oe, 2), Ve = r(Le, 2), qe = a(Ve), vr = a(qe), De = r(qe, 2), Me = r(Ve, 2), Ue = a(Me), _r = a(Ue), Ke = r(Ue, 2), cr = r(Me, 2), Te = a(cr), pr = a(Te), Qe = r(Te, 2), ur = r(Ee, 2), gr = a(ur);
      {
        let l = h(E);
        L(gr, {
          variant: "primary",
          get disabled() {
            return t(l);
          },
          onclick: oa,
          children: (c, f) => {
            var m = P();
            u((v) => s(m, v), [() => i("settings.render_layout.save")]), _(c, m);
          },
          $$slots: { default: !0 }
        });
      }
      var mr = r(n, 2), Ge = a(mr), fr = a(Ge), He = a(fr), br = a(He), hr = r(He, 2), xr = a(hr), yr = r(Ge, 2), $r = a(yr);
      {
        var jr = (l) => {
          var c = Kr(), f = r(a(c)), m = a(f), v = r(f), x = a(v);
          u(
            (W, q) => {
              s(m, W), s(x, q);
            },
            [
              () => i("projects.empty_title"),
              () => i("projects.empty_body")
            ]
          ), _(l, c);
        }, wr = (l) => {
          var c = Gr(), f = a(c), m = a(f), v = a(m), x = a(v), W = r(v), q = a(W), _t = r(W), X = a(_t), ct = r(f);
          Ye(ct, 21, () => t(z), (C) => C.video_id, (C, I) => {
            const D = h(() => t(dt)[t(I).video_id]);
            var Y = Qr(), lt = a(Y), nt = a(lt), pt = a(nt), ut = r(nt), It = a(ut), wt = r(lt), Lt = a(wt);
            {
              let N = h(() => _a(t(D)));
              Lr(Lt, {
                get kind() {
                  return t(N);
                },
                children: (rt, Je) => {
                  var kt = P();
                  u((Mt) => s(kt, Mt), [() => st(t(D))]), _(rt, kt);
                },
                $$slots: { default: !0 }
              });
            }
            var Ot = r(wt), Rt = a(Ot);
            {
              var Vt = (N) => {
                var rt = Tr(), Je = a(rt);
                u(
                  (kt, Mt) => {
                    We(rt, "href", kt), s(Je, Mt);
                  },
                  [() => ca(t(I)), () => i("projects.open_output")]
                ), _(N, rt);
              }, qt = h(() => st(t(D)).includes("rendered")), Dt = (N) => {
                var rt = P("—");
                _(N, rt);
              };
              U(Rt, (N) => {
                t(qt) ? N(Vt) : N(Dt, -1);
              });
            }
            u(
              (N) => {
                s(pt, t(I).video_id), s(It, `${N ?? ""}${t(I).is_long ? " · long" : ""}`);
              },
              [() => (t(I).source_path || "").split(/[\\/]/).pop()]
            ), _(C, Y);
          }), u(
            (C, I, D) => {
              s(x, C), s(q, I), s(X, D);
            },
            [
              () => i("projects.col_video"),
              () => i("projects.col_status"),
              () => i("projects.col_output")
            ]
          ), _(l, c);
        };
        U($r, (l) => {
          t(z).length ? l(wr, -1) : l(jr);
        });
      }
      u(
        (l, c, f, m, v, x, W, q, _t, X, ct, C, I, D, Y, lt, nt, pt, ut, It, wt, Lt, Ot, Rt, Vt, qt, Dt, N) => {
          s(J, l), s(Q, c), s(V, f), s(La, m), s(Oa, v), ve !== (ve = t(d).aspect_ratio) && (A.value = (A.__value = t(d).aspect_ratio) ?? "", mt(A, t(d).aspect_ratio)), s(Ra, `${x ?? ""} (${t(d).head_trim_sec ?? ""}s)`), it(pe, t(d).head_trim_sec), s(Va, `${W ?? ""} (${t(d).tail_trim_sec ?? ""}s)`), it(me, t(d).tail_trim_sec), s(Ma, q), s(Ua, _t), s(Ga, X), s(Ha, ct), s(Za, C), s(tr, I), s(ir, D), s(sr, Y), Nr(Ct, t(d).transform_hflip), s(lr, lt), s(nr, `${nt ?? ""} (${pt ?? ""}x)`), it(Ie, t(d).transform_speed), s(dr, `${ut ?? ""} (${It ?? ""}%)`), it(Re, t(d).transform_zoom), s(vr, `${wt ?? ""} (${Lt ?? ""})`), it(De, t(d).transform_brightness), s(_r, `${Ot ?? ""} (${Rt ?? ""})`), it(Ke, t(d).transform_contrast), s(pr, `${Vt ?? ""} (${qt ?? ""})`), it(Qe, t(d).transform_saturation), s(br, Dt), s(xr, N);
        },
        [
          () => i("projects.brand_title"),
          () => i("projects.brand_sub"),
          () => i("settings.render_layout.aspect_ratio"),
          () => i("settings.render_layout.aspect_16_9"),
          () => i("settings.render_layout.aspect_9_16"),
          () => i("settings.render_layout.head_trim"),
          () => i("settings.render_layout.tail_trim"),
          () => i("settings.render_layout.logo_title"),
          () => t(d).logo_path ? St(t(d).logo_original_filename || t(d).logo_path) : i("settings.render_layout.no_logo"),
          () => i("settings.render_layout.intro_clip"),
          () => t(d).intro_clip_path ? St(t(d).intro_original_filename || t(d).intro_clip_path) : i("settings.render_layout.no_clip"),
          () => i("settings.render_layout.outro_clip"),
          () => t(d).outro_clip_path ? St(t(d).outro_original_filename || t(d).outro_clip_path) : i("settings.render_layout.no_clip"),
          () => i("settings.render_layout.tx_title"),
          () => i("settings.render_layout.tx_sub"),
          () => i("settings.render_layout.tx_hflip"),
          () => i("settings.render_layout.tx_speed"),
          () => t(d).transform_speed.toFixed(2),
          () => i("settings.render_layout.tx_zoom"),
          () => Math.round((t(d).transform_zoom - 1) * 100),
          () => i("settings.render_layout.tx_brightness"),
          () => t(d).transform_brightness.toFixed(2),
          () => i("settings.render_layout.tx_contrast"),
          () => t(d).transform_contrast.toFixed(2),
          () => i("settings.render_layout.tx_saturation"),
          () => t(d).transform_saturation.toFixed(2),
          () => i("projects.videos_title", { count: t(z).length }),
          () => i("projects.progress_summary", {
            done: t(pa),
            failed: t(ua),
            total: t(z).length
          })
        ]
      ), k("change", A, (l) => R({ aspect_ratio: l.target.value })), k("change", pe, (l) => R({ head_trim_sec: Number(l.target.value) })), k("change", me, (l) => R({ tail_trim_sec: Number(l.target.value) })), k("change", Ct, (l) => R({ transform_hflip: l.target.checked })), k("input", Ie, (l) => R({ transform_speed: Number(l.target.value) })), k("input", Re, (l) => R({ transform_zoom: Number(l.target.value) })), k("input", De, (l) => R({ transform_brightness: Number(l.target.value) })), k("input", Ke, (l) => R({ transform_contrast: Number(l.target.value) })), k("input", Qe, (l) => R({ transform_saturation: Number(l.target.value) })), _(e, o);
    };
    U(Ca, (e) => {
      t(g) && e(Ia);
    });
  }
  u(
    (e, o, n, b, $, T, J, F, Q) => {
      s(ba, e), s(xa, o), s($a, n), tt.disabled = !!t(g), ie !== (ie = y.tts_provider) && (tt.value = (tt.__value = y.tts_provider) ?? "", mt(tt, y.tts_provider)), s(ja, b), et.disabled = !!t(g), s(wa, $), le !== (le = y.tts_voice) && (et.value = (et.__value = y.tts_voice) ?? "", mt(et, y.tts_voice)), s(Ba, T), at.disabled = !!t(g), s(Aa, J), s(Na, F), s(Sa, Q), de !== (de = y.mix_mode) && (at.value = (at.__value = y.mix_mode) ?? "", mt(at, y.mix_mode));
    },
    [
      () => i("projects.title"),
      () => i("projects.sub"),
      () => i("projects.cfg_provider"),
      () => i("projects.cfg_voice"),
      () => i("projects.cfg_voice_default"),
      () => i("projects.cfg_mix"),
      () => i("settings.tts.mix_replace"),
      () => i("settings.tts.mix_duck"),
      () => i("settings.tts.mix_keep_music")
    ]
  ), k("change", tt, (e) => y.tts_provider = e.target.value), k("change", et, (e) => y.tts_voice = e.target.value), k("change", at, (e) => y.mix_mode = e.target.value), _(ta, Ht), Ar();
}
kr(["change", "input"]);
const Ze = Or(Wr), oi = Ze.mount, si = Ze.unmount;
export {
  oi as mount,
  si as unmount
};
//# sourceMappingURL=projects.js.map
