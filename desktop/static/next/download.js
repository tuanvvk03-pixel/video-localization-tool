import { d as Xt, p as Yt, w as Zt, x as ta, f as B, i as y, g as s, l as i, o as x, t as p, j as c, a as _, r as D, K as aa, m as oa, b as ea, s as pt, c as T, A as C, h as l, u as k, n as g, e as F, q as ra } from "./chunks/api-vHpIWCot.js";
import { e as sa, i as da } from "./chunks/each-BE197-93.js";
import { b as na, a as la } from "./chunks/input-D0G7l_P3.js";
import { p as ia, B as $ } from "./chunks/Button-GpBM5g0S.js";
import { s as ua } from "./chunks/screen-DRq5NjFu.js";
var ca = g('<div class="error-banner" data-testid="download-error"><div class="error-code"> </div> <div class="error-message"> </div></div>'), va = g('<img class="download-queue-thumb" alt="" loading="lazy"/>'), pa = g('<div class="download-queue-meta small-muted"> </div> <!>', 1), _a = g('<div class="small-muted"> </div>'), fa = g('<div class="info-banner"> </div> <!>', 1), ba = g('<div class="download-queue-row stack"><div class="download-queue-head"><div class="download-queue-url"> </div> <div> </div></div> <!> <!> <!> <!></div>'), ma = g('<div class="card"><div class="card-body stack"><div class="card-title"> </div> <label class="checkbox-row"><input type="checkbox"/> <span> </span></label> <div class="download-queue-list"></div></div></div>'), ha = g('<!> <div class="screen download-screen" data-testid="download-screen"><div class="dlhero"><h2> </h2> <p> </p></div> <div class="card dlbox"><div class="card-body stack"><div class="field"><label for="dl-urls"> </label> <textarea id="dl-urls" class="input download-url-textarea" rows="8"></textarea></div> <div class="toolbar download-toolbar"><!> <!> <!></div> <div class="warning-banner"> </div> <div class="field"><label for="dl-output"> </label> <input id="dl-output" class="input" type="text"/></div> <div class="toolbar download-footer-actions"><!> <!></div></div></div> <!></div>', 1);
function ga(ft, O) {
  Yt(O, !0);
  let f = ia(O, "ctx", 7);
  const d = (t, o) => (f()?.t ?? ((e) => e))(t, o);
  function bt() {
    return {
      urlsText: "",
      outputRoot: "",
      outputTouched: !1,
      forceReuse: !1,
      lines: [],
      busy: "",
      lastJobWorkspace: ""
    };
  }
  let a = Zt(f()?.downloadState || bt());
  f() && (f().downloadState = a);
  let E = pt(""), U = pt("UI");
  const M = () => String(f()?.workspaceRoot || "").trim();
  function I() {
    F(E, "");
  }
  function R(t) {
    const o = t instanceof C ? t : null;
    F(U, o?.shortCode || "UI", !0), F(
      E,
      o ? o.summary || o.message : t?.message || d("error.generic"),
      !0
    );
  }
  function mt(t) {
    return String(t || "").split(/\r?\n/).map((o) => o.trim()).filter(Boolean);
  }
  async function ht() {
    if (a.outputTouched && a.outputRoot.trim()) return;
    const t = M();
    if (t) {
      a.outputRoot = t, a.outputTouched = !1;
      return;
    }
    try {
      const o = await T("/api/default-download-root", {}), e = String(o.workspace_root || "").trim();
      e && (a.outputRoot = e, a.outputTouched = !1);
    } catch {
    }
  }
  async function gt() {
    I();
    try {
      const t = await T("/api/default-download-root", {}), o = String(t.workspace_root || "").trim();
      if (!o) throw new Error(d("download.default_folder_failed"));
      a.outputRoot = o, a.outputTouched = !0;
    } catch (t) {
      R(t);
    }
  }
  async function wt() {
    if (I(), !a.outputRoot.trim()) {
      R(new Error(d("download.output_required")));
      return;
    }
    const o = mt(a.urlsText);
    if (!o.length) {
      R(new Error(d("download.urls_required")));
      return;
    }
    a.busy = "analyze", a.lines = o.map((e) => ({
      url: e,
      phase: "pending",
      message: d("download.phase_pending"),
      probe: null,
      jobWorkspace: ""
    }));
    for (let e = 0; e < o.length; e += 1) {
      const r = o[e];
      a.lines[e] = {
        ...a.lines[e],
        phase: "probing",
        message: d("download.phase_probing")
      };
      try {
        const n = await T("/api/probe-video-url", { url: r });
        a.lines[e] = {
          url: r,
          phase: "ready",
          message: d("download.phase_ready"),
          probe: n,
          jobWorkspace: ""
        };
      } catch (n) {
        const h = n instanceof C ? n.message : String(n || "");
        a.lines[e] = {
          url: r,
          phase: "error",
          message: h,
          probe: null,
          jobWorkspace: ""
        };
      }
    }
    a.busy = "";
  }
  async function yt(t) {
    I();
    const o = a.outputRoot.trim();
    if (!o) {
      R(new Error(d("download.output_required")));
      return;
    }
    const e = a.lines[t];
    if (!(!e || e.phase !== "ready")) {
      a.busy = `download:${t}`, a.lines[t] = {
        ...e,
        phase: "downloading",
        message: d("download.phase_downloading")
      };
      try {
        const r = await T("/api/init-job-from-url", { url: e.url, workspace_root: o, force: !!a.forceReuse }), n = String(r.job_workspace || "").trim();
        a.lines[t] = {
          ...e,
          phase: "done",
          message: d("download.phase_done"),
          jobWorkspace: n
        }, a.lastJobWorkspace = n, a.busy = "";
      } catch (r) {
        const n = r instanceof C ? r.message : String(r || "");
        a.lines[t] = {
          ...e,
          phase: "error",
          message: n,
          jobWorkspace: e.jobWorkspace
        }, a.busy = "";
      }
    }
  }
  function xt() {
    const t = a.lastJobWorkspace.trim();
    t && K(t);
  }
  function K(t) {
    const o = String(t || "").trim();
    if (!o || !f()?.navigate) return;
    f().jobWorkspace = o;
    const e = a.outputRoot.trim();
    if (e) {
      f().workspaceRoot = e;
      try {
        localStorage.setItem("workspace_root", e);
      } catch {
      }
      const r = document.getElementById("workspaceRootInput");
      r && (r.value = e);
    }
    f().preflightAfterOpenJob = !0, f().navigate("edit", { stepIndex: 0 });
  }
  async function kt() {
    I();
    const t = M() || a.outputRoot.trim();
    if (!t) {
      R(new Error(d("download.workspace_missing")));
      return;
    }
    try {
      await T("/api/reveal", { path: t });
    } catch (o) {
      R(o);
    }
  }
  function $t(t) {
    const o = Math.max(0, Math.round(Number(t) || 0));
    if (!o) return "—";
    const e = Math.floor(o / 3600), r = Math.floor(o % 3600 / 60), n = o % 60;
    return e > 0 ? `${e}:${String(r).padStart(2, "0")}:${String(n).padStart(2, "0")}` : `${r}:${String(n).padStart(2, "0")}`;
  }
  const Rt = k(() => !!(M() || a.outputRoot.trim()));
  ta(() => {
    ht();
  });
  var L = ha(), N = B(L);
  {
    var St = (t) => {
      var o = ca(), e = l(o), r = l(e), n = i(e, 2), h = l(n);
      p(() => {
        c(r, s(U)), c(h, s(E));
      }), _(t, o);
    };
    y(N, (t) => {
      s(E) && t(St);
    });
  }
  var jt = i(N, 2), G = l(jt), H = l(G), Wt = l(H), qt = i(H, 2), Tt = l(qt), Q = i(G, 2), Et = l(Q), V = l(Et), X = l(V), It = l(X), Y = i(X, 2), Z = i(V, 2), tt = l(Z);
  {
    let t = k(() => !!a.busy);
    $(tt, {
      variant: "strong",
      get disabled() {
        return s(t);
      },
      onclick: wt,
      children: (o, e) => {
        var r = x();
        p((n) => c(r, n), [() => d("download.analyze")]), _(o, r);
      },
      $$slots: { default: !0 }
    });
  }
  var at = i(tt, 2);
  {
    let t = k(() => !!a.busy);
    $(at, {
      variant: "secondary",
      get disabled() {
        return s(t);
      },
      onclick: () => {
        a.lines = [], a.busy = "";
      },
      children: (o, e) => {
        var r = x();
        p((n) => c(r, n), [() => d("download.clear_queue")]), _(o, r);
      },
      $$slots: { default: !0 }
    });
  }
  var Pt = i(at, 2);
  {
    let t = k(() => !!a.busy);
    $(Pt, {
      get disabled() {
        return s(t);
      },
      onclick: gt,
      children: (o, e) => {
        var r = x();
        p((n) => c(r, n), [() => d("download.use_default_folder")]), _(o, r);
      },
      $$slots: { default: !0 }
    });
  }
  var ot = i(Z, 2), Jt = l(ot), et = i(ot, 2), rt = l(et), Mt = l(rt), z = i(rt, 2), zt = i(et, 2), st = l(zt);
  {
    let t = k(() => !a.lastJobWorkspace || !!a.busy);
    $(st, {
      variant: "primary",
      get disabled() {
        return s(t);
      },
      onclick: xt,
      children: (o, e) => {
        var r = x();
        p((n) => c(r, n), [() => d("download.open_edit")]), _(o, r);
      },
      $$slots: { default: !0 }
    });
  }
  var At = i(st, 2);
  {
    let t = k(() => !s(Rt));
    $(At, {
      variant: "secondary",
      get disabled() {
        return s(t);
      },
      onclick: kt,
      children: (o, e) => {
        var r = x();
        p((n) => c(r, n), [() => d("download.open_workspace")]), _(o, r);
      },
      $$slots: { default: !0 }
    });
  }
  var Bt = i(Q, 2);
  {
    var Dt = (t) => {
      var o = ma(), e = l(o), r = l(e), n = l(r), h = i(r, 2), P = l(h), Ct = i(P, 2), Ft = l(Ct), Ot = i(h, 2);
      sa(Ot, 21, () => a.lines, da, (W, u, Ut) => {
        var dt = ba(), nt = l(dt), lt = l(nt), Kt = l(lt), it = i(lt, 2), Lt = l(it), ut = i(nt, 2);
        {
          var Nt = (v) => {
            var b = pa(), m = B(b), J = l(m), S = i(m, 2);
            {
              var w = (j) => {
                var q = va();
                p((A) => D(q, "src", A), [() => String(s(u).probe.thumbnail)]), _(j, q);
              };
              y(S, (j) => {
                s(u).probe.thumbnail && j(w);
              });
            }
            p((j) => c(J, j), [
              () => d("download.probe_summary", {
                title: s(u).probe.title || s(u).probe.video_id || "—",
                duration: $t(s(u).probe.duration),
                extractor: s(u).probe.extractor || "—"
              })
            ]), _(v, b);
          };
          y(ut, (v) => {
            s(u).probe && s(u).phase === "ready" && v(Nt);
          });
        }
        var ct = i(ut, 2);
        {
          var Gt = (v) => {
            var b = _a(), m = l(b);
            p(() => c(m, s(u).message)), _(v, b);
          };
          y(ct, (v) => {
            s(u).phase === "error" && s(u).message && v(Gt);
          });
        }
        var vt = i(ct, 2);
        {
          var Ht = (v) => {
            {
              let b = k(() => !!a.busy);
              $(v, {
                variant: "primary",
                get disabled() {
                  return s(b);
                },
                onclick: () => yt(Ut),
                children: (m, J) => {
                  var S = x();
                  p((w) => c(S, w), [() => d("download.confirm_download")]), _(m, S);
                },
                $$slots: { default: !0 }
              });
            }
          };
          y(vt, (v) => {
            s(u).phase === "ready" && v(Ht);
          });
        }
        var Qt = i(vt, 2);
        {
          var Vt = (v) => {
            var b = fa(), m = B(b), J = l(m), S = i(m, 2);
            $(S, {
              variant: "secondary",
              onclick: () => K(s(u).jobWorkspace),
              children: (w, j) => {
                var q = x();
                p((A) => c(q, A), [() => d("download.open_this_edit")]), _(w, q);
              },
              $$slots: { default: !0 }
            }), p((w) => c(J, w), [
              () => d("download.done_notice", { path: s(u).jobWorkspace })
            ]), _(v, b);
          };
          y(Qt, (v) => {
            s(u).phase === "done" && s(u).jobWorkspace && v(Vt);
          });
        }
        p(
          (v) => {
            c(Kt, s(u).url), ra(it, 1, `download-queue-status download-queue-status--${s(u).phase ?? ""}`), c(Lt, v);
          },
          [
            () => s(u).phase === "error" ? d("download.status_error") : s(u).message || s(u).phase
          ]
        ), _(W, dt);
      }), p(
        (W, u) => {
          c(n, W), c(Ft, u);
        },
        [
          () => d("download.queue_title"),
          () => d("download.force_reuse")
        ]
      ), la(P, () => a.forceReuse, (W) => a.forceReuse = W), _(t, o);
    };
    y(Bt, (t) => {
      a.lines.length && t(Dt);
    });
  }
  p(
    (t, o, e, r, n, h, P) => {
      c(Wt, t), c(Tt, o), c(It, e), D(Y, "placeholder", r), c(Jt, n), c(Mt, h), D(z, "placeholder", P), aa(z, a.outputRoot);
    },
    [
      () => d("rail.download"),
      () => d("download.sub"),
      () => d("download.urls_label"),
      () => d("download.urls_placeholder"),
      () => d("download.ytdlp_warning"),
      () => d("download.output_root_label"),
      () => d("download.output_root_placeholder")
    ]
  ), na(Y, () => a.urlsText, (t) => a.urlsText = t), oa("input", z, (t) => {
    a.outputRoot = t.currentTarget.value, a.outputTouched = !0;
  }), _(ft, L), ea();
}
Xt(["input"]);
const _t = ua(ga), Ra = _t.mount, Sa = _t.unmount;
export {
  Ra as mount,
  Sa as unmount
};
//# sourceMappingURL=download.js.map
