import { d as Wa, p as Xa, s as D, w as $t, x as Ya, c as w, e as c, i as F, g as e, l as i, Q as nt, t as p, j as s, R as vt, m as at, a as v, b as Za, h as a, f as Lt, o as k, r as je, K as we, n as A, u as b, A as tr, O as ke, M as er } from "./chunks/api-vHpIWCot.js";
import { o as ar } from "./chunks/index-client-CjB8cgHo.js";
import { e as Pe, i as rr } from "./chunks/each-BE197-93.js";
import { b as or } from "./chunks/input-D0G7l_P3.js";
import { n as Q } from "./chunks/helpers-BtNcAVZn.js";
import { B as O } from "./chunks/Button-GpBM5g0S.js";
import { S as ir } from "./chunks/StatusBadge-DT3lodBA.js";
import { s as sr } from "./chunks/screen-DRq5NjFu.js";
var lr = A('<div class="error-banner"><div class="error-code">UI</div><div class="error-message"> </div></div>'), dr = A('<div class="info-banner"> </div>'), nr = A("<option> </option>"), vr = A('<div class="toolbar"><input class="input" style="max-width:320px" type="text"/> <!></div> <div class="small-muted"> </div>', 1), _r = A('<div class="small-muted"> </div> <div class="toolbar"><!> <!> <!></div> <div class="small-muted"> </div>', 1), cr = A('<div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option><option> </option></select></div>'), pr = A('<div class="empty-card"><div class="empty-icon">＋</div><h3> </h3><p> </p></div>'), ur = A('<a target="_blank" rel="noopener"> </a>'), gr = A('<tr><td><div class="row-title"> </div><div class="small-muted"> </div></td><td><!></td><td><!></td></tr>'), fr = A('<table class="review-table"><thead><tr><th> </th><th> </th><th> </th></tr></thead><tbody></tbody></table>'), mr = A('<div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option></select></div> <div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/></div> <div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/></div> <!></div> <div class="clip-row"><div class="clip-col"><div class="row-title"> </div> <div class="small-muted"> </div> <div class="toolbar"><!> <!></div></div> <div class="clip-col"><div class="row-title"> </div> <div class="small-muted"> </div> <div class="toolbar"><!> <!></div></div> <div class="clip-col"><div class="row-title"> </div> <div class="small-muted"> </div> <div class="toolbar"><!> <!></div></div></div> <div class="toolbar"><!></div></div></div> <div class="card"><div class="card-header"><div><div class="card-title"> </div> <div class="card-sub"> </div></div></div> <div class="card-body"><!></div></div>', 1), hr = A('<div class="screen stack" data-testid="projects-screen"><!> <!> <div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option>edge_tts</option><option>azure_tts</option></select></div> <div class="field"><label> </label> <select class="input"><option> </option><!></select></div> <div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option></select></div></div> <!></div></div> <!></div>');
function br(Ae, Ot) {
  Xa(Ot, !0);
  const r = (t, o) => (Ot.ctx?.t ?? ((d) => d))(t, o);
  let jt = D(""), g = D(""), S = D($t([])), it = D($t({})), Nt = D($t([])), x = $t({
    tts_provider: "edge_tts",
    tts_voice: "",
    mix_mode: "replace_original_speech"
  }), wt = D(""), rt = D(!1), X = D(""), _t = D(""), N = D(null), T = null;
  ar(() => {
    T && clearInterval(T);
  }), Ya(() => {
    Se();
  });
  async function Se() {
    try {
      const t = await w("/api/list-voices", {});
      c(
        Nt,
        Array.isArray(t.voices) ? t.voices.filter((o) => o && o.voice_id && o.enabled !== !1) : [],
        !0
      );
    } catch {
    }
  }
  async function U(t, o) {
    c(_t, ""), c(wt, t, !0), c(X, "");
    try {
      await o();
    } catch (d) {
      c(_t, d instanceof tr ? d.summary || d.message : d?.message || "error", !0);
    } finally {
      c(wt, "");
    }
  }
  const E = () => !!e(wt) || e(rt), Ee = () => U("create", async () => {
    const t = e(jt).trim();
    if (!t) throw new Error(r("projects.name_required"));
    const o = await w("/api/init-project", {
      project_name: t,
      config_overrides: {
        tts_provider: x.tts_provider,
        tts_voice: x.tts_voice.trim(),
        mix_mode: x.mix_mode,
        translate_backend: "block_v2"
      }
    });
    c(g, String(o.project_root || ""), !0), c(X, r("projects.created"), !0), await ct();
  }), Ce = () => U("add", async () => {
    if (!e(g)) throw new Error(r("projects.create_first"));
    const t = await er({
      filters: ["Video files (*.mp4;*.mov;*.mkv;*.webm)", "All files (*.*)"]
    });
    if (t?.cancelled) return;
    const o = t?.paths || [];
    if (!o.length) throw new Error(t?.error || r("projects.pick_unavailable"));
    let d = 0;
    const h = [];
    for (const $ of o)
      try {
        await w("/api/add-video-to-project", { project_root: e(g), video: $ }), d++;
      } catch {
        h.push($.split(/[\\/]/).pop() || $);
      }
    c(X, r("projects.added", { count: d }) + (h.length ? ` (${r("projects.add_failed", { count: h.length })})` : "")), await ct();
  });
  async function ct() {
    if (!e(g)) return;
    const t = await w("/api/get-project", { project_root: e(g) });
    c(S, Array.isArray(t.videos) ? t.videos : [], !0);
    const o = {};
    for (const d of t.statuses || []) o[String(d.video_id)] = d;
    c(it, o, !0), await Ie();
  }
  async function Ie() {
    if (e(g))
      try {
        const t = await w("/api/render-settings/status", { job_workspace: e(g) });
        c(N, Q(t.render || {}), !0);
      } catch {
      }
  }
  function kt() {
    const t = e(N) || Q({}), o = {
      aspect_ratio: t.aspect_ratio,
      background_path: t.background_path,
      background_original_filename: t.background_original_filename,
      head_trim_sec: t.head_trim_sec,
      tail_trim_sec: t.tail_trim_sec
    };
    return t.logo_path && Object.assign(o, {
      logo_path: t.logo_path,
      logo_original_filename: t.logo_original_filename,
      logo_position: t.logo_position,
      logo_scale: t.logo_scale,
      logo_opacity: t.logo_opacity,
      logo_margin: t.logo_margin
    }), t.intro_clip_path && Object.assign(o, {
      intro_clip_path: t.intro_clip_path,
      intro_original_filename: t.intro_original_filename
    }), t.outro_clip_path && Object.assign(o, {
      outro_clip_path: t.outro_clip_path,
      outro_original_filename: t.outro_original_filename
    }), o;
  }
  function pt(t) {
    c(N, Q({ ...e(N) || {}, ...t }), !0);
  }
  const Le = () => U("brand_save", async () => {
    const t = await w("/api/render-settings/save", { job_workspace: e(g), render: kt() });
    c(N, Q(t.render), !0), c(X, r("projects.brand_saved"), !0);
  }), Oe = () => U("brand_logo", async () => {
    const t = await ke({
      filters: ["Image files (*.png;*.jpg;*.jpeg;*.webp)", "All files (*.*)"]
    });
    if (t?.cancelled) return;
    if (!t?.ok || !t.path) throw new Error(t?.error || r("projects.pick_unavailable"));
    await w("/api/render-settings/save", { job_workspace: e(g), render: kt() });
    const o = await w("/api/render-logo/upload", { job_workspace: e(g), image_path: t.path });
    c(N, Q(o.render), !0);
  }), Ne = () => U("brand_logo_rm", async () => {
    const t = await w("/api/render-logo/remove", { job_workspace: e(g) });
    c(N, Q(t.render), !0);
  }), Rt = (t) => U(`brand_${t}`, async () => {
    const o = await ke({
      filters: ["Video files (*.mp4;*.mov;*.mkv;*.webm)", "All files (*.*)"]
    });
    if (o?.cancelled) return;
    if (!o?.ok || !o.path) throw new Error(o?.error || r("projects.pick_unavailable"));
    await w("/api/render-settings/save", { job_workspace: e(g), render: kt() });
    const d = await w(`/api/render-${t}/upload`, { job_workspace: e(g), clip_path: o.path });
    c(N, Q(d.render), !0);
  }), Vt = (t) => U(`brand_${t}_rm`, async () => {
    const o = await w(`/api/render-${t}/remove`, { job_workspace: e(g) });
    c(N, Q(o.render), !0);
  }), Re = () => U("run", async () => {
    if (!e(g) || !e(S).length) throw new Error(r("projects.no_videos"));
    c(rt, !0);
    try {
      await w("/api/run-project", { project_root: e(g), async: !0 }), Ve();
    } catch (t) {
      throw c(rt, !1), t;
    }
  });
  function Ve() {
    T && clearInterval(T), T = setInterval(
      async () => {
        try {
          await ct(), e(S).length && e(S).every((t) => qe(e(it)[t.video_id])) && (c(rt, !1), T && (clearInterval(T), T = null), c(X, r("projects.done"), !0));
        } catch {
        }
      },
      3e3
    );
  }
  function ot(t) {
    return String(t?.current_stage || t?.status || "queued");
  }
  function qe(t) {
    const o = ot(t);
    return o.includes("rendered") || o.includes("failed");
  }
  function ze(t) {
    const o = ot(t);
    return o.includes("failed") ? "blocked" : o.includes("rendered") ? "completed" : e(rt) ? "running" : "queued";
  }
  function De(t) {
    const o = String(t?.workspace || "");
    return o ? `/media?${new URLSearchParams({
      workspace: o,
      rel: "artifacts/render/final.mp4",
      v: String(Date.now())
    }).toString()}` : "";
  }
  const Fe = b(() => e(S).filter((t) => ot(e(it)[t.video_id]).includes("rendered")).length), Ue = b(() => e(S).filter((t) => ot(e(it)[t.video_id]).includes("failed")).length), u = b(() => e(N) || Q({})), Pt = (t) => (t || "").split(/[\\/]/).pop();
  var qt = hr(), zt = a(qt);
  {
    var Ke = (t) => {
      var o = lr(), d = i(a(o)), h = a(d);
      p(() => s(h, e(_t))), v(t, o);
    };
    F(zt, (t) => {
      e(_t) && t(Ke);
    });
  }
  var Dt = i(zt, 2);
  {
    var Me = (t) => {
      var o = dr(), d = a(o);
      p(() => s(d, e(X))), v(t, o);
    };
    F(Dt, (t) => {
      e(X) && t(Me);
    });
  }
  var Ft = i(Dt, 2), Ut = a(Ft), Qe = a(Ut), Kt = a(Qe), Te = a(Kt), Ge = i(Kt), He = a(Ge), Je = i(Ut, 2), Mt = a(Je), Qt = a(Mt), Tt = a(Qt), We = a(Tt), Y = i(Tt, 2), Bt = a(Y);
  Bt.value = Bt.__value = "edge_tts";
  var Gt = i(Bt);
  Gt.value = Gt.__value = "azure_tts";
  var Ht;
  nt(Y);
  var Jt = i(Qt, 2), Wt = a(Jt), Xe = a(Wt), Z = i(Wt, 2), ut = a(Z), Ye = a(ut);
  ut.value = ut.__value = "";
  var Ze = i(ut);
  Pe(Ze, 17, () => e(Nt), rr, (t, o) => {
    var d = nr(), h = a(d), $ = {};
    p(() => {
      s(h, e(o).short_name || e(o).label || e(o).voice_id), $ !== ($ = e(o).voice_id) && (d.value = (d.__value = e(o).voice_id) ?? "");
    }), v(t, d);
  });
  var Xt;
  nt(Z);
  var ta = i(Jt, 2), Yt = a(ta), ea = a(Yt), tt = i(Yt, 2), gt = a(tt), aa = a(gt);
  gt.value = gt.__value = "replace_original_speech";
  var ft = i(gt), ra = a(ft);
  ft.value = ft.__value = "duck_original_speech";
  var At = i(ft), oa = a(At);
  At.value = At.__value = "keep_music_replace_voice";
  var Zt;
  nt(tt);
  var ia = i(Mt, 2);
  {
    var sa = (t) => {
      var o = vr(), d = Lt(o), h = a(d), $ = i(h, 2);
      {
        let C = b(E);
        O($, {
          variant: "primary",
          get disabled() {
            return e(C);
          },
          onclick: Ee,
          children: (M, mt) => {
            var j = k();
            p((P) => s(j, P), [() => r("projects.create")]), v(M, j);
          },
          $$slots: { default: !0 }
        });
      }
      var K = i(d, 2), G = a(K);
      p(
        (C, M) => {
          je(h, "placeholder", C), s(G, M);
        },
        [
          () => r("projects.name_placeholder"),
          () => r("projects.create_hint")
        ]
      ), or(h, () => e(jt), (C) => c(jt, C)), v(t, o);
    }, la = (t) => {
      var o = _r(), d = Lt(o), h = a(d), $ = i(d, 2), K = a($);
      {
        let j = b(E);
        O(K, {
          variant: "secondary",
          get disabled() {
            return e(j);
          },
          onclick: Ce,
          children: (P, st) => {
            var R = k();
            p((B) => s(R, B), [() => r("projects.add_videos")]), v(P, R);
          },
          $$slots: { default: !0 }
        });
      }
      var G = i(K, 2);
      {
        let j = b(() => E() || !e(S).length);
        O(G, {
          variant: "strong",
          get disabled() {
            return e(j);
          },
          onclick: Re,
          children: (P, st) => {
            var R = k();
            p((B) => s(R, B), [
              () => e(rt) ? r("projects.running") : r("projects.run_all")
            ]), v(P, R);
          },
          $$slots: { default: !0 }
        });
      }
      var C = i(G, 2);
      {
        let j = b(E);
        O(C, {
          get disabled() {
            return e(j);
          },
          onclick: () => U("refresh", ct),
          children: (P, st) => {
            var R = k();
            p((B) => s(R, B), [() => r("projects.refresh")]), v(P, R);
          },
          $$slots: { default: !0 }
        });
      }
      var M = i($, 2), mt = a(M);
      p(
        (j, P) => {
          s(h, `${j ?? ""}: ${e(g) ?? ""}`), s(mt, P);
        },
        [
          () => r("projects.open_label"),
          () => r("projects.cfg_locked_hint")
        ]
      ), v(t, o);
    };
    F(ia, (t) => {
      e(g) ? t(la, -1) : t(sa);
    });
  }
  var da = i(Ft, 2);
  {
    var na = (t) => {
      var o = mr(), d = Lt(o), h = a(d), $ = a(h), K = a($), G = a(K), C = i(K), M = a(C), mt = i(h, 2), j = a(mt), P = a(j), st = a(P), R = a(st), B = i(st, 2), ht = a(B), va = a(ht);
      ht.value = ht.__value = "16:9";
      var St = i(ht), _a = a(St);
      St.value = St.__value = "9:16";
      var te;
      nt(B);
      var ee = i(P, 2), ae = a(ee), ca = a(ae), re = i(ae, 2), oe = i(ee, 2), ie = a(oe), pa = a(ie), se = i(ie, 2), ua = i(oe, 2);
      {
        var ga = (l) => {
          var _ = cr(), m = a(_), f = a(m), n = i(m, 2), y = a(n), H = a(y);
          y.value = y.__value = "top-left";
          var V = i(y), lt = a(V);
          V.value = V.__value = "top-right";
          var J = i(V), dt = a(J);
          J.value = J.__value = "bottom-left";
          var I = i(J), L = a(I);
          I.value = I.__value = "bottom-right";
          var q;
          nt(n), p(
            (W, bt, yt, Et, Ct) => {
              s(f, W), s(H, bt), s(lt, yt), s(dt, Et), s(L, Ct), q !== (q = e(u).logo_position) && (n.value = (n.__value = e(u).logo_position) ?? "", vt(n, e(u).logo_position));
            },
            [
              () => r("settings.render_layout.logo_position"),
              () => r("settings.render_layout.pos_top_left"),
              () => r("settings.render_layout.pos_top_right"),
              () => r("settings.render_layout.pos_bottom_left"),
              () => r("settings.render_layout.pos_bottom_right")
            ]
          ), at("change", n, (W) => pt({ logo_position: W.target.value })), v(l, _);
        };
        F(ua, (l) => {
          e(u).logo_path && l(ga);
        });
      }
      var le = i(j, 2), de = a(le), ne = a(de), fa = a(ne), ve = i(ne, 2), ma = a(ve), ha = i(ve, 2), _e = a(ha);
      {
        let l = b(E);
        O(_e, {
          variant: "secondary",
          get disabled() {
            return e(l);
          },
          onclick: Oe,
          children: (_, m) => {
            var f = k();
            p((n) => s(f, n), [() => r("settings.render_layout.upload_logo")]), v(_, f);
          },
          $$slots: { default: !0 }
        });
      }
      var ba = i(_e, 2);
      {
        var ya = (l) => {
          {
            let _ = b(E);
            O(l, {
              get disabled() {
                return e(_);
              },
              onclick: Ne,
              children: (m, f) => {
                var n = k();
                p((y) => s(n, y), [() => r("settings.render_layout.remove_logo")]), v(m, n);
              },
              $$slots: { default: !0 }
            });
          }
        };
        F(ba, (l) => {
          e(u).logo_path && l(ya);
        });
      }
      var ce = i(de, 2), pe = a(ce), xa = a(pe), ue = i(pe, 2), $a = a(ue), ja = i(ue, 2), ge = a(ja);
      {
        let l = b(E);
        O(ge, {
          variant: "secondary",
          get disabled() {
            return e(l);
          },
          onclick: () => Rt("intro"),
          children: (_, m) => {
            var f = k();
            p((n) => s(f, n), [() => r("settings.render_layout.upload_intro")]), v(_, f);
          },
          $$slots: { default: !0 }
        });
      }
      var wa = i(ge, 2);
      {
        var ka = (l) => {
          {
            let _ = b(E);
            O(l, {
              get disabled() {
                return e(_);
              },
              onclick: () => Vt("intro"),
              children: (m, f) => {
                var n = k();
                p((y) => s(n, y), [() => r("settings.render_layout.remove_clip")]), v(m, n);
              },
              $$slots: { default: !0 }
            });
          }
        };
        F(wa, (l) => {
          e(u).intro_clip_path && l(ka);
        });
      }
      var Pa = i(ce, 2), fe = a(Pa), Ba = a(fe), me = i(fe, 2), Aa = a(me), Sa = i(me, 2), he = a(Sa);
      {
        let l = b(E);
        O(he, {
          variant: "secondary",
          get disabled() {
            return e(l);
          },
          onclick: () => Rt("outro"),
          children: (_, m) => {
            var f = k();
            p((n) => s(f, n), [() => r("settings.render_layout.upload_outro")]), v(_, f);
          },
          $$slots: { default: !0 }
        });
      }
      var Ea = i(he, 2);
      {
        var Ca = (l) => {
          {
            let _ = b(E);
            O(l, {
              get disabled() {
                return e(_);
              },
              onclick: () => Vt("outro"),
              children: (m, f) => {
                var n = k();
                p((y) => s(n, y), [() => r("settings.render_layout.remove_clip")]), v(m, n);
              },
              $$slots: { default: !0 }
            });
          }
        };
        F(Ea, (l) => {
          e(u).outro_clip_path && l(Ca);
        });
      }
      var Ia = i(le, 2), La = a(Ia);
      {
        let l = b(E);
        O(La, {
          variant: "primary",
          get disabled() {
            return e(l);
          },
          onclick: Le,
          children: (_, m) => {
            var f = k();
            p((n) => s(f, n), [() => r("settings.render_layout.save")]), v(_, f);
          },
          $$slots: { default: !0 }
        });
      }
      var Oa = i(d, 2), be = a(Oa), Na = a(be), ye = a(Na), Ra = a(ye), Va = i(ye, 2), qa = a(Va), za = i(be, 2), Da = a(za);
      {
        var Fa = (l) => {
          var _ = pr(), m = i(a(_)), f = a(m), n = i(m), y = a(n);
          p(
            (H, V) => {
              s(f, H), s(y, V);
            },
            [
              () => r("projects.empty_title"),
              () => r("projects.empty_body")
            ]
          ), v(l, _);
        }, Ua = (l) => {
          var _ = fr(), m = a(_), f = a(m), n = a(f), y = a(n), H = i(n), V = a(H), lt = i(H), J = a(lt), dt = i(m);
          Pe(dt, 21, () => e(S), (I) => I.video_id, (I, L) => {
            const q = b(() => e(it)[e(L).video_id]);
            var W = gr(), bt = a(W), yt = a(bt), Et = a(yt), Ct = i(yt), Ka = a(Ct), xe = i(bt), Ma = a(xe);
            {
              let z = b(() => ze(e(q)));
              ir(Ma, {
                get kind() {
                  return e(z);
                },
                children: (et, $e) => {
                  var xt = k();
                  p((It) => s(xt, It), [() => ot(e(q))]), v(et, xt);
                },
                $$slots: { default: !0 }
              });
            }
            var Qa = i(xe), Ta = a(Qa);
            {
              var Ga = (z) => {
                var et = ur(), $e = a(et);
                p(
                  (xt, It) => {
                    je(et, "href", xt), s($e, It);
                  },
                  [() => De(e(L)), () => r("projects.open_output")]
                ), v(z, et);
              }, Ha = b(() => ot(e(q)).includes("rendered")), Ja = (z) => {
                var et = k("—");
                v(z, et);
              };
              F(Ta, (z) => {
                e(Ha) ? z(Ga) : z(Ja, -1);
              });
            }
            p(
              (z) => {
                s(Et, e(L).video_id), s(Ka, `${z ?? ""}${e(L).is_long ? " · long" : ""}`);
              },
              [() => (e(L).source_path || "").split(/[\\/]/).pop()]
            ), v(I, W);
          }), p(
            (I, L, q) => {
              s(y, I), s(V, L), s(J, q);
            },
            [
              () => r("projects.col_video"),
              () => r("projects.col_status"),
              () => r("projects.col_output")
            ]
          ), v(l, _);
        };
        F(Da, (l) => {
          e(S).length ? l(Ua, -1) : l(Fa);
        });
      }
      p(
        (l, _, m, f, n, y, H, V, lt, J, dt, I, L, q, W) => {
          s(G, l), s(M, _), s(R, m), s(va, f), s(_a, n), te !== (te = e(u).aspect_ratio) && (B.value = (B.__value = e(u).aspect_ratio) ?? "", vt(B, e(u).aspect_ratio)), s(ca, `${y ?? ""} (${e(u).head_trim_sec ?? ""}s)`), we(re, e(u).head_trim_sec), s(pa, `${H ?? ""} (${e(u).tail_trim_sec ?? ""}s)`), we(se, e(u).tail_trim_sec), s(fa, V), s(ma, lt), s(xa, J), s($a, dt), s(Ba, I), s(Aa, L), s(Ra, q), s(qa, W);
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
          () => e(u).logo_path ? Pt(e(u).logo_original_filename || e(u).logo_path) : r("settings.render_layout.no_logo"),
          () => r("settings.render_layout.intro_clip"),
          () => e(u).intro_clip_path ? Pt(e(u).intro_original_filename || e(u).intro_clip_path) : r("settings.render_layout.no_clip"),
          () => r("settings.render_layout.outro_clip"),
          () => e(u).outro_clip_path ? Pt(e(u).outro_original_filename || e(u).outro_clip_path) : r("settings.render_layout.no_clip"),
          () => r("projects.videos_title", { count: e(S).length }),
          () => r("projects.progress_summary", {
            done: e(Fe),
            failed: e(Ue),
            total: e(S).length
          })
        ]
      ), at("change", B, (l) => pt({ aspect_ratio: l.target.value })), at("change", re, (l) => pt({ head_trim_sec: Number(l.target.value) })), at("change", se, (l) => pt({ tail_trim_sec: Number(l.target.value) })), v(t, o);
    };
    F(da, (t) => {
      e(g) && t(na);
    });
  }
  p(
    (t, o, d, h, $, K, G, C, M) => {
      s(Te, t), s(He, o), s(We, d), Y.disabled = !!e(g), Ht !== (Ht = x.tts_provider) && (Y.value = (Y.__value = x.tts_provider) ?? "", vt(Y, x.tts_provider)), s(Xe, h), Z.disabled = !!e(g), s(Ye, $), Xt !== (Xt = x.tts_voice) && (Z.value = (Z.__value = x.tts_voice) ?? "", vt(Z, x.tts_voice)), s(ea, K), tt.disabled = !!e(g), s(aa, G), s(ra, C), s(oa, M), Zt !== (Zt = x.mix_mode) && (tt.value = (tt.__value = x.mix_mode) ?? "", vt(tt, x.mix_mode));
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
  ), at("change", Y, (t) => x.tts_provider = t.target.value), at("change", Z, (t) => x.tts_voice = t.target.value), at("change", tt, (t) => x.mix_mode = t.target.value), v(Ae, qt), Za();
}
Wa(["change"]);
const Be = sr(br), Ar = Be.mount, Sr = Be.unmount;
export {
  Ar as mount,
  Sr as unmount
};
//# sourceMappingURL=projects.js.map
