import { d as Be, p as Ce, s as k, w as et, x as qe, c as N, e as _, i as z, g as e, l as s, Q as nt, t as p, j as d, R as _t, m as pt, a as l, b as De, h as r, f as Vt, o as F, r as zt, n as y, u as P, A as Re, M as Ue } from "./chunks/api-vHpIWCot.js";
import { o as Ve } from "./chunks/index-client-CjB8cgHo.js";
import { e as Ft, i as ze } from "./chunks/each-BE197-93.js";
import { b as Fe } from "./chunks/input-D0G7l_P3.js";
import { B as rt } from "./chunks/Button-GpBM5g0S.js";
import { S as Le } from "./chunks/StatusBadge-DT3lodBA.js";
import { s as Me } from "./chunks/screen-DRq5NjFu.js";
var Ke = y('<div class="error-banner"><div class="error-code">UI</div><div class="error-message"> </div></div>'), Ne = y('<div class="info-banner"> </div>'), Oe = y("<option> </option>"), Qe = y('<div class="toolbar"><input class="input" style="max-width:320px" type="text"/> <!></div> <div class="small-muted"> </div>', 1), Te = y('<div class="small-muted"> </div> <div class="toolbar"><!> <!> <!></div> <div class="small-muted"> </div>', 1), Ge = y('<div class="empty-card"><div class="empty-icon">＋</div><h3> </h3><p> </p></div>'), He = y('<a target="_blank" rel="noopener"> </a>'), Je = y('<tr><td><div class="row-title"> </div><div class="small-muted"> </div></td><td><!></td><td><!></td></tr>'), We = y('<table class="review-table"><thead><tr><th> </th><th> </th><th> </th></tr></thead><tbody></tbody></table>'), Xe = y('<div class="card"><div class="card-header"><div><div class="card-title"> </div> <div class="card-sub"> </div></div></div> <div class="card-body"><!></div></div>'), Ye = y('<div class="screen stack" data-testid="projects-screen"><!> <!> <div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option>edge_tts</option><option>azure_tts</option></select></div> <div class="field"><label> </label> <select class="input"><option> </option><!></select></div> <div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option></select></div></div> <!></div></div> <!></div>');
function Ze(Mt, ut) {
  Ce(ut, !0);
  const i = (t, a) => (ut.ctx?.t ?? ((o) => o))(t, a);
  let at = k(""), f = k(""), g = k(et([])), L = k(et({})), ft = k(et([])), u = et({
    tts_provider: "edge_tts",
    tts_voice: "",
    mix_mode: "replace_original_speech"
  }), it = k(""), R = k(!1), U = k(""), O = k(""), S = null;
  Ve(() => {
    S && clearInterval(S);
  }), qe(() => {
    Kt();
  });
  async function Kt() {
    try {
      const t = await N("/api/list-voices", {});
      _(
        ft,
        Array.isArray(t.voices) ? t.voices.filter((a) => a && a.voice_id && a.enabled !== !1) : [],
        !0
      );
    } catch {
    }
  }
  async function Q(t, a) {
    _(O, ""), _(it, t, !0), _(U, "");
    try {
      await a();
    } catch (o) {
      _(O, o instanceof Re ? o.summary || o.message : o?.message || "error", !0);
    } finally {
      _(it, "");
    }
  }
  const T = () => !!e(it) || e(R), Nt = () => Q("create", async () => {
    const t = e(at).trim();
    if (!t) throw new Error(i("projects.name_required"));
    const a = await N("/api/init-project", {
      project_name: t,
      config_overrides: {
        tts_provider: u.tts_provider,
        tts_voice: u.tts_voice.trim(),
        mix_mode: u.mix_mode,
        translate_backend: "block_v2"
      }
    });
    _(f, String(a.project_root || ""), !0), _(U, i("projects.created"), !0), await G();
  }), Ot = () => Q("add", async () => {
    if (!e(f)) throw new Error(i("projects.create_first"));
    const t = await Ue({
      filters: ["Video files (*.mp4;*.mov;*.mkv;*.webm)", "All files (*.*)"]
    });
    if (t?.cancelled) return;
    const a = t?.paths || [];
    if (!a.length) throw new Error(t?.error || i("projects.pick_unavailable"));
    let o = 0;
    const v = [];
    for (const c of a)
      try {
        await N("/api/add-video-to-project", { project_root: e(f), video: c }), o++;
      } catch {
        v.push(c.split(/[\\/]/).pop() || c);
      }
    _(U, i("projects.added", { count: o }) + (v.length ? ` (${i("projects.add_failed", { count: v.length })})` : "")), await G();
  });
  async function G() {
    if (!e(f)) return;
    const t = await N("/api/get-project", { project_root: e(f) });
    _(g, Array.isArray(t.videos) ? t.videos : [], !0);
    const a = {};
    for (const o of t.statuses || []) a[String(o.video_id)] = o;
    _(L, a, !0);
  }
  const Qt = () => Q("run", async () => {
    if (!e(f) || !e(g).length) throw new Error(i("projects.no_videos"));
    _(R, !0);
    try {
      await N("/api/run-project", { project_root: e(f), async: !0 }), Tt();
    } catch (t) {
      throw _(R, !1), t;
    }
  });
  function Tt() {
    S && clearInterval(S), S = setInterval(
      async () => {
        try {
          await G(), e(g).length && e(g).every((t) => Gt(e(L)[t.video_id])) && (_(R, !1), S && (clearInterval(S), S = null), _(U, i("projects.done"), !0));
        } catch {
        }
      },
      3e3
    );
  }
  function V(t) {
    return String(t?.current_stage || t?.status || "queued");
  }
  function Gt(t) {
    const a = V(t);
    return a.includes("rendered") || a.includes("failed");
  }
  function Ht(t) {
    const a = V(t);
    return a.includes("failed") ? "blocked" : a.includes("rendered") ? "completed" : e(R) ? "running" : "queued";
  }
  function Jt(t) {
    const a = String(t?.workspace || "");
    return a ? `/media?${new URLSearchParams({
      workspace: a,
      rel: "artifacts/render/final.mp4",
      v: String(Date.now())
    }).toString()}` : "";
  }
  const Wt = P(() => e(g).filter((t) => V(e(L)[t.video_id]).includes("rendered")).length), Xt = P(() => e(g).filter((t) => V(e(L)[t.video_id]).includes("failed")).length);
  var mt = Ye(), gt = r(mt);
  {
    var Yt = (t) => {
      var a = Ke(), o = s(r(a)), v = r(o);
      p(() => d(v, e(O))), l(t, a);
    };
    z(gt, (t) => {
      e(O) && t(Yt);
    });
  }
  var ht = s(gt, 2);
  {
    var Zt = (t) => {
      var a = Ne(), o = r(a);
      p(() => d(o, e(U))), l(t, a);
    };
    z(ht, (t) => {
      e(U) && t(Zt);
    });
  }
  var xt = s(ht, 2), bt = r(xt), te = r(bt), jt = r(te), ee = r(jt), re = s(jt), ae = r(re), ie = s(bt, 2), yt = r(ie), wt = r(yt), $t = r(wt), oe = r($t), I = s($t, 2), ot = r(I);
  ot.value = ot.__value = "edge_tts";
  var kt = s(ot);
  kt.value = kt.__value = "azure_tts";
  var Pt;
  nt(I);
  var St = s(wt, 2), At = r(St), se = r(At), B = s(At, 2), H = r(B), de = r(H);
  H.value = H.__value = "";
  var ve = s(H);
  Ft(ve, 17, () => e(ft), ze, (t, a) => {
    var o = Oe(), v = r(o), c = {};
    p(() => {
      d(v, e(a).short_name || e(a).label || e(a).voice_id), c !== (c = e(a).voice_id) && (o.value = (o.__value = e(a).voice_id) ?? "");
    }), l(t, o);
  });
  var Et;
  nt(B);
  var le = s(St, 2), It = r(le), ce = r(It), C = s(It, 2), J = r(C), ne = r(J);
  J.value = J.__value = "replace_original_speech";
  var W = s(J), _e = r(W);
  W.value = W.__value = "duck_original_speech";
  var st = s(W), pe = r(st);
  st.value = st.__value = "keep_music_replace_voice";
  var Bt;
  nt(C);
  var ue = s(yt, 2);
  {
    var fe = (t) => {
      var a = Qe(), o = Vt(a), v = r(o), c = s(v, 2);
      {
        let h = P(T);
        rt(c, {
          variant: "primary",
          get disabled() {
            return e(h);
          },
          onclick: Nt,
          children: ($, X) => {
            var m = F();
            p((x) => d(m, x), [() => i("projects.create")]), l($, m);
          },
          $$slots: { default: !0 }
        });
      }
      var A = s(o, 2), E = r(A);
      p(
        (h, $) => {
          zt(v, "placeholder", h), d(E, $);
        },
        [
          () => i("projects.name_placeholder"),
          () => i("projects.create_hint")
        ]
      ), Fe(v, () => e(at), (h) => _(at, h)), l(t, a);
    }, me = (t) => {
      var a = Te(), o = Vt(a), v = r(o), c = s(o, 2), A = r(c);
      {
        let m = P(T);
        rt(A, {
          variant: "secondary",
          get disabled() {
            return e(m);
          },
          onclick: Ot,
          children: (x, b) => {
            var n = F();
            p((j) => d(n, j), [() => i("projects.add_videos")]), l(x, n);
          },
          $$slots: { default: !0 }
        });
      }
      var E = s(A, 2);
      {
        let m = P(() => T() || !e(g).length);
        rt(E, {
          variant: "strong",
          get disabled() {
            return e(m);
          },
          onclick: Qt,
          children: (x, b) => {
            var n = F();
            p((j) => d(n, j), [
              () => e(R) ? i("projects.running") : i("projects.run_all")
            ]), l(x, n);
          },
          $$slots: { default: !0 }
        });
      }
      var h = s(E, 2);
      {
        let m = P(T);
        rt(h, {
          get disabled() {
            return e(m);
          },
          onclick: () => Q("refresh", G),
          children: (x, b) => {
            var n = F();
            p((j) => d(n, j), [() => i("projects.refresh")]), l(x, n);
          },
          $$slots: { default: !0 }
        });
      }
      var $ = s(c, 2), X = r($);
      p(
        (m, x) => {
          d(v, `${m ?? ""}: ${e(f) ?? ""}`), d(X, x);
        },
        [
          () => i("projects.open_label"),
          () => i("projects.cfg_locked_hint")
        ]
      ), l(t, a);
    };
    z(ue, (t) => {
      e(f) ? t(me, -1) : t(fe);
    });
  }
  var ge = s(xt, 2);
  {
    var he = (t) => {
      var a = Xe(), o = r(a), v = r(o), c = r(v), A = r(c), E = s(c, 2), h = r(E), $ = s(o, 2), X = r($);
      {
        var m = (b) => {
          var n = Ge(), j = s(r(n)), dt = r(j), Y = s(j), vt = r(Y);
          p(
            (Z, lt) => {
              d(dt, Z), d(vt, lt);
            },
            [
              () => i("projects.empty_title"),
              () => i("projects.empty_body")
            ]
          ), l(b, n);
        }, x = (b) => {
          var n = We(), j = r(n), dt = r(j), Y = r(dt), vt = r(Y), Z = s(Y), lt = r(Z), xe = s(Z), be = r(xe), je = s(j);
          Ft(je, 21, () => e(g), (M) => M.video_id, (M, q) => {
            const K = P(() => e(L)[e(q).video_id]);
            var Ct = Je(), qt = r(Ct), Dt = r(qt), ye = r(Dt), we = s(Dt), $e = r(we), Rt = s(qt), ke = r(Rt);
            {
              let w = P(() => Ht(e(K)));
              Le(ke, {
                get kind() {
                  return e(w);
                },
                children: (D, Ut) => {
                  var tt = F();
                  p((ct) => d(tt, ct), [() => V(e(K))]), l(D, tt);
                },
                $$slots: { default: !0 }
              });
            }
            var Pe = s(Rt), Se = r(Pe);
            {
              var Ae = (w) => {
                var D = He(), Ut = r(D);
                p(
                  (tt, ct) => {
                    zt(D, "href", tt), d(Ut, ct);
                  },
                  [() => Jt(e(q)), () => i("projects.open_output")]
                ), l(w, D);
              }, Ee = P(() => V(e(K)).includes("rendered")), Ie = (w) => {
                var D = F("—");
                l(w, D);
              };
              z(Se, (w) => {
                e(Ee) ? w(Ae) : w(Ie, -1);
              });
            }
            p(
              (w) => {
                d(ye, e(q).video_id), d($e, `${w ?? ""}${e(q).is_long ? " · long" : ""}`);
              },
              [() => (e(q).source_path || "").split(/[\\/]/).pop()]
            ), l(M, Ct);
          }), p(
            (M, q, K) => {
              d(vt, M), d(lt, q), d(be, K);
            },
            [
              () => i("projects.col_video"),
              () => i("projects.col_status"),
              () => i("projects.col_output")
            ]
          ), l(b, n);
        };
        z(X, (b) => {
          e(g).length ? b(x, -1) : b(m);
        });
      }
      p(
        (b, n) => {
          d(A, b), d(h, n);
        },
        [
          () => i("projects.videos_title", { count: e(g).length }),
          () => i("projects.progress_summary", {
            done: e(Wt),
            failed: e(Xt),
            total: e(g).length
          })
        ]
      ), l(t, a);
    };
    z(ge, (t) => {
      e(f) && t(he);
    });
  }
  p(
    (t, a, o, v, c, A, E, h, $) => {
      d(ee, t), d(ae, a), d(oe, o), I.disabled = !!e(f), Pt !== (Pt = u.tts_provider) && (I.value = (I.__value = u.tts_provider) ?? "", _t(I, u.tts_provider)), d(se, v), B.disabled = !!e(f), d(de, c), Et !== (Et = u.tts_voice) && (B.value = (B.__value = u.tts_voice) ?? "", _t(B, u.tts_voice)), d(ce, A), C.disabled = !!e(f), d(ne, E), d(_e, h), d(pe, $), Bt !== (Bt = u.mix_mode) && (C.value = (C.__value = u.mix_mode) ?? "", _t(C, u.mix_mode));
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
  ), pt("change", I, (t) => u.tts_provider = t.target.value), pt("change", B, (t) => u.tts_voice = t.target.value), pt("change", C, (t) => u.mix_mode = t.target.value), l(Mt, mt), De();
}
Be(["change"]);
const Lt = Me(Ze), dr = Lt.mount, vr = Lt.unmount;
export {
  dr as mount,
  vr as unmount
};
//# sourceMappingURL=projects.js.map
