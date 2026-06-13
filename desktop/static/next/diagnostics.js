import { t as c, F as tr, G as Xa, H as pa, I as rr, E as er, N as ir, J as sr, d as dr, p as vr, s as N, w as at, x as lr, f as ja, i as oa, g as t, l as e, a as v, b as cr, e as _, A as or, h as a, j as i, u as S, o as C, n as w, c as ga, q as nr, m as _r, k as ur } from "./chunks/api-vHpIWCot.js";
import { o as fr } from "./chunks/index-client-CjB8cgHo.js";
import { e as ma, i as ba } from "./chunks/each-BE197-93.js";
import { a as pr } from "./chunks/input-D0G7l_P3.js";
import { b as gr } from "./chunks/this-_Wc-LPs7.js";
import { s as mr } from "./chunks/events-OW5kxpYF.js";
import { B as Y } from "./chunks/Button-GpBM5g0S.js";
import { S as tt } from "./chunks/StatusBadge-DT3lodBA.js";
import { s as br } from "./chunks/screen-DRq5NjFu.js";
function xr(na, ta, d = !1, u = !1, Z = !1, Sa = !1) {
  var D = na, P = "";
  if (d)
    var T = (
      /** @type {Element} */
      na
    );
  c(() => {
    var B = (
      /** @type {Effect} */
      tr
    );
    if (P !== (P = ta() ?? "")) {
      if (d) {
        B.nodes = null, T.innerHTML = /** @type {string} */
        P, P !== "" && Xa(
          /** @type {TemplateNode} */
          pa(T),
          /** @type {TemplateNode} */
          T.lastChild
        );
        return;
      }
      if (B.nodes !== null && (rr(
        B.nodes.start,
        /** @type {TemplateNode} */
        B.nodes.end
      ), B.nodes = null), P !== "") {
        var n = u ? ir : Z ? sr : void 0, E = (
          /** @type {HTMLTemplateElement | SVGElement | MathMLElement} */
          er(u ? "svg" : Z ? "math" : "template", n)
        );
        E.innerHTML = /** @type {any} */
        P;
        var F = u || Z ? E : (
          /** @type {HTMLTemplateElement} */
          E.content
        );
        if (Xa(
          /** @type {TemplateNode} */
          pa(F),
          /** @type {TemplateNode} */
          F.lastChild
        ), u || Z)
          for (; pa(F); )
            D.before(
              /** @type {TemplateNode} */
              pa(F)
            );
        else
          D.before(F);
      }
    }
  });
}
var hr = w('<div class="error-banner" data-testid="diag-error"><div class="error-code">UI</div> <div class="error-message"> </div></div>'), $r = w('<div class="card" data-testid="diag-empty"><div class="empty-card"><div class="empty-icon">⌘</div> <h3> </h3> <p> </p></div></div>'), yr = w('<div class="card" data-testid="diag-loading"><div class="empty-card"><div class="empty-icon">…</div> <h3> </h3> <p> </p></div></div>'), kr = w('<button type="button"> </button>'), wr = w('<div class="small-muted"> </div>'), Ar = w('<div class="logline"></div>'), jr = w('<div class="card"><div class="card-header"><div><div class="card-title"> </div> <div class="card-sub"> </div></div> <label class="checkbox-row"><input type="checkbox"/> </label></div> <div class="card-body"><div class="logbox"><!></div></div></div>'), Sr = w('<div class="meta-empty"> </div>'), Pr = w('<div class="artifact"><div><div class="artifact-name"> </div> <small> </small></div> <!> <div class="toolbar"><!> <!> <!></div></div>'), Er = w('<div class="artifact"><div><div class="artifact-name"> </div> <small> </small></div> <!> <div class="toolbar"><!> <!></div></div>'), rt = w("<!> <!>", 1), qr = w('<div class="card"><div class="card-header"><div><div class="card-title"> </div> <div class="card-sub"> </div></div></div> <div class="card-body card-body--scroll"><div class="artifact-list"><!></div></div></div>'), Nr = w('<div class="card"><div class="card-header"><div><div class="card-title"> </div> <div class="card-sub"> </div></div></div> <div class="card-body"><pre class="mini-json"> </pre></div></div>'), Tr = w('<div class="screen stack" data-testid="diag-screen"><div class="pipeline"><div class="stage"><span class="dot running"></span><span> </span></div> <div class="stage"><span class="dot done"></span><span> </span></div> <div class="stage"><span class="dot queued"></span><span> </span></div></div> <div class="tabs"></div> <div class="state-grid"><!> <div class="stack"><div class="card"><div class="card-header"><div><div class="card-title"> </div> <div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="section-block"><div style="font-weight:800"> </div> <div class="small-muted" style="margin-top:6px"> </div></div> <div class="toolbar"><!> <!></div></div></div> <div class="card"><div class="card-header"><div><div class="card-title"> </div> <div class="card-sub"> </div></div></div> <div class="card-body"><div class="settings-context"><div class="context-pill"><strong> </strong> </div> <div class="context-pill"><strong> </strong> </div> <div class="context-pill"><strong> </strong> </div> <div class="context-pill"><strong> </strong> </div></div></div></div></div></div></div>');
function Br(na, ta) {
  vr(ta, !0);
  const d = (r, s) => (ta.ctx?.t ?? ((f) => f))(r, s), u = () => String(ta.ctx?.jobWorkspace || ""), Z = ["logs", "artifacts", "state"], Sa = {
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
  let D = N(!0), P = N(""), T = N("logs"), B = N(!0), n = N(null), E = N(null), F = N(at([])), xa = N(at([])), Q = N(""), _a = null, ha = "", ra = N(void 0);
  async function ua() {
    const [r, s, f] = await Promise.all([
      ga("/api/job-progress", { job_workspace: u() }),
      ga("/api/status", { job_workspace: u() }),
      ga("/api/list-artifacts", { job_workspace: u() })
    ]);
    _(n, r, !0), _(E, s, !0), _(F, Array.isArray(f.canonical) ? f.canonical : [], !0), _(xa, Array.isArray(f.extras) ? f.extras : [], !0);
  }
  async function it() {
    if (!u()) {
      _(D, !1);
      return;
    }
    _(Q, ""), _(D, !0);
    try {
      await ua(), _(D, !1), st();
    } catch (r) {
      _(D, !1), _(Q, Na(r), !0);
    }
  }
  function st() {
    Pa(), u() && (ha = String(t(n)?.current_stage || ""), _a = mr(u(), {
      onProgress: (r) => {
        _(n, r, !0), t(ra) && t(T) === "logs" && t(B) && (t(ra).scrollTop = t(ra).scrollHeight);
        const s = String(r?.current_stage || "");
        s !== ha && (ha = s, ua().catch(() => {
        }));
      },
      onDone: () => {
        ua().catch(() => {
        });
      }
    }));
  }
  function Pa() {
    _a && (_a(), _a = null);
  }
  async function Ea(r, s) {
    _(Q, ""), _(P, r, !0);
    try {
      await s();
    } catch (f) {
      _(Q, Na(f), !0);
    } finally {
      _(P, "");
    }
  }
  const dt = () => Ea("refresh", ua), qa = (r) => Ea("reveal", async () => {
    await ga("/api/reveal", { path: r });
  });
  function vt(r) {
    if (!r?.rel_path) return;
    const s = new URLSearchParams({ workspace: u(), rel: r.rel_path });
    window.open(`/media?${s.toString()}`, "_blank", "noopener");
  }
  async function $a(r) {
    if (r)
      try {
        await navigator.clipboard.writeText(String(r));
      } catch {
      }
  }
  function Na(r) {
    return r instanceof or ? r.summary || r.message : r?.message || d("error.generic");
  }
  function lt(r) {
    const s = r.rel_path ? Sa[r.rel_path] : void 0;
    return s ? d(s) : r.label || r.rel_path || "";
  }
  function ct(r) {
    const s = Number(r) || 0;
    return s >= 1024 * 1024 ? `${(s / (1024 * 1024)).toFixed(1)} MB` : s >= 1024 ? `${(s / 1024).toFixed(1)} KB` : `${s} B`;
  }
  function ot(r) {
    const s = Number(r) || 0;
    return s ? new Date(s * 1e3).toLocaleString() : "—";
  }
  function nt(r) {
    return String(r || "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
  }
  function _t(r) {
    let s = nt(r);
    return s = s.replace(/\b(INFO|OK)\b/g, '<span class="ok">$1</span>'), s = s.replace(/\b(RUN|RUNNING)\b/g, '<span class="run">$1</span>'), s = s.replace(/\b(WARN|WAIT|BLOCKED|ERROR|FAILED)\b/g, '<span class="warn">$1</span>'), s = s.replace(/([A-Za-z]:\\[^ <>\n]+|artifacts\/[^ <>\n]+|input\/[^ <>\n]+)/g, '<span class="path">$1</span>'), s;
  }
  const Ta = S(() => Array.isArray(t(n)?.log_tail) ? t(n).log_tail : []), Ba = S(() => t(F).filter((r) => r.exists)), ut = S(() => ({
    workspace: u(),
    lifecycle: t(n)?.lifecycle || "idle",
    status: t(n)?.status || "",
    current_stage: t(n)?.current_stage || "",
    current_stage_label: t(n)?.current_stage_label || "",
    overall_percent: t(n)?.overall_percent || 0,
    voice_edit_status: t(E)?.voice_edit_status || "",
    voice_edited: !!t(E)?.voice_edited,
    required_action: t(E)?.required_action || null,
    last_error: t(n)?.last_error || null,
    log_tail: t(n)?.log_tail || []
  })), ft = S(() => Math.max(0, Math.min(100, Number(t(n)?.overall_percent) || 0)));
  lr(() => {
    u(), it();
  }), fr(Pa);
  var La = rt(), Ma = ja(La);
  {
    var pt = (r) => {
      var s = hr(), f = e(a(s), 2), q = a(f);
      c(() => i(q, t(Q))), v(r, s);
    };
    oa(Ma, (r) => {
      t(Q) && r(pt);
    });
  }
  var gt = e(Ma, 2);
  {
    var mt = (r) => {
      var s = $r(), f = a(s), q = e(a(f), 2), ea = a(q), ia = e(q, 2), X = a(ia);
      c(
        (sa, da) => {
          i(ea, sa), i(X, da);
        },
        [() => d("diag.empty_title"), () => d("diag.empty_body")]
      ), v(r, s);
    }, bt = S(() => !u()), xt = (r) => {
      var s = yr(), f = a(s), q = e(a(f), 2), ea = a(q), ia = e(q, 2), X = a(ia);
      c(
        (sa, da) => {
          i(ea, sa), i(X, da);
        },
        [() => d("diag.loading_title"), () => d("common.loading")]
      ), v(r, s);
    }, ht = (r) => {
      var s = Tr(), f = a(s), q = a(f), ea = e(a(q)), ia = a(ea), X = e(q, 2), sa = e(a(X)), da = a(sa), $t = e(X, 2), yt = e(a($t)), kt = a(yt), Ra = e(f, 2);
      ma(Ra, 21, () => Z, ba, (p, g) => {
        var o = kr(), x = a(o);
        c(
          ($) => {
            nr(o, 1, `tab ${t(T) === t(g) ? "active" : ""}`), i(x, $);
          },
          [() => d(`diag.tab.${t(g)}`)]
        ), _r("click", o, () => _(T, t(g), !0)), v(p, o);
      });
      var wt = e(Ra, 2), Ca = a(wt);
      {
        var At = (p) => {
          var g = jr(), o = a(g), x = a(o), $ = a(x), z = a($), K = e($, 2), U = a(K), G = e(x, 2), I = a(G), J = e(I), W = e(o, 2), H = a(W), y = a(H);
          {
            var L = (m) => {
              var j = wr(), l = a(j);
              c((M) => i(l, M), [() => d("diag.logs.empty")]), v(m, j);
            }, aa = (m) => {
              var j = ur(), l = ja(j);
              ma(l, 17, () => t(Ta), ba, (M, V) => {
                var O = Ar();
                xr(O, () => _t(String(t(V) || "")), !0), v(M, O);
              }), v(m, j);
            };
            oa(y, (m) => {
              t(Ta).length ? m(aa, -1) : m(L);
            });
          }
          gr(H, (m) => _(ra, m), () => t(ra)), c(
            (m, j, l) => {
              i(z, m), i(U, j), i(J, ` ${l ?? ""}`);
            },
            [
              () => d("diag.logs.title"),
              () => d("diag.logs.sub"),
              () => d("diag.auto_scroll")
            ]
          ), pr(I, () => t(B), (m) => _(B, m)), v(p, g);
        }, jt = (p) => {
          var g = qr(), o = a(g), x = a(o), $ = a(x), z = a($), K = e($, 2), U = a(K), G = e(o, 2), I = a(G), J = a(I);
          {
            var W = (y) => {
              var L = Sr(), aa = a(L);
              c((m) => i(aa, m), [() => d("diag.artifacts.empty")]), v(y, L);
            }, H = (y) => {
              var L = rt(), aa = ja(L);
              ma(aa, 17, () => t(Ba), ba, (j, l) => {
                var M = Pr(), V = a(M), O = a(V), ya = a(O), ka = e(O, 2), wa = a(ka), va = e(V, 2);
                tt(va, {
                  kind: "completed",
                  children: (b, A) => {
                    var h = C();
                    c((k) => i(h, k), [() => d("status.completed")]), v(b, h);
                  },
                  $$slots: { default: !0 }
                });
                var Aa = e(va, 2), la = a(Aa);
                {
                  let b = S(() => !t(l).rel_path);
                  Y(la, {
                    get disabled() {
                      return t(b);
                    },
                    onclick: () => vt(t(l)),
                    children: (A, h) => {
                      var k = C();
                      c((ca) => i(k, ca), [() => d("common.open")]), v(A, k);
                    },
                    $$slots: { default: !0 }
                  });
                }
                var fa = e(la, 2);
                {
                  let b = S(() => !t(l).path);
                  Y(fa, {
                    get disabled() {
                      return t(b);
                    },
                    onclick: () => qa(t(l).path),
                    children: (A, h) => {
                      var k = C();
                      c((ca) => i(k, ca), [() => d("common.reveal")]), v(A, k);
                    },
                    $$slots: { default: !0 }
                  });
                }
                var R = e(fa, 2);
                {
                  let b = S(() => !t(l).path);
                  Y(R, {
                    get disabled() {
                      return t(b);
                    },
                    onclick: () => $a(t(l).path),
                    children: (A, h) => {
                      var k = C();
                      c((ca) => i(k, ca), [() => d("diag.copy_path")]), v(A, k);
                    },
                    $$slots: { default: !0 }
                  });
                }
                c(
                  (b, A, h) => {
                    i(ya, b), i(wa, `${A ?? ""} • ${h ?? ""}`);
                  },
                  [
                    () => lt(t(l)),
                    () => ct(t(l).size_bytes),
                    () => ot(t(l).modified_unix)
                  ]
                ), v(j, M);
              });
              var m = e(aa, 2);
              ma(m, 17, () => t(xa), ba, (j, l) => {
                var M = Er(), V = a(M), O = a(V), ya = a(O), ka = e(O, 2), wa = a(ka), va = e(V, 2);
                tt(va, {
                  kind: "completed",
                  children: (R, b) => {
                    var A = C();
                    c((h) => i(A, h), [() => d("status.completed")]), v(R, A);
                  },
                  $$slots: { default: !0 }
                });
                var Aa = e(va, 2), la = a(Aa);
                {
                  let R = S(() => !t(l).path);
                  Y(la, {
                    get disabled() {
                      return t(R);
                    },
                    onclick: () => qa(t(l).path),
                    children: (b, A) => {
                      var h = C();
                      c((k) => i(h, k), [() => d("common.reveal")]), v(b, h);
                    },
                    $$slots: { default: !0 }
                  });
                }
                var fa = e(la, 2);
                {
                  let R = S(() => !t(l).path);
                  Y(fa, {
                    get disabled() {
                      return t(R);
                    },
                    onclick: () => $a(t(l).path),
                    children: (b, A) => {
                      var h = C();
                      c((k) => i(h, k), [() => d("diag.copy_path")]), v(b, h);
                    },
                    $$slots: { default: !0 }
                  });
                }
                c(
                  (R, b) => {
                    i(ya, R), i(wa, b);
                  },
                  [
                    () => String(t(l).label || d("diag.artifacts.extra")),
                    () => d("diag.artifacts.extra_count", { count: String(t(l).count || 0) })
                  ]
                ), v(j, M);
              }), v(y, L);
            };
            oa(J, (y) => {
              !t(Ba).length && !t(xa).length ? y(W) : y(H, -1);
            });
          }
          c(
            (y, L) => {
              i(z, y), i(U, L);
            },
            [
              () => d("diag.artifacts.title"),
              () => d("diag.artifacts.sub")
            ]
          ), v(p, g);
        }, St = (p) => {
          var g = Nr(), o = a(g), x = a(o), $ = a(x), z = a($), K = e($, 2), U = a(K), G = e(o, 2), I = a(G), J = a(I);
          c(
            (W, H, y) => {
              i(z, W), i(U, H), i(J, y);
            },
            [
              () => d("diag.state.title"),
              () => d("diag.state.sub"),
              () => JSON.stringify(t(ut), null, 2)
            ]
          ), v(p, g);
        };
        oa(Ca, (p) => {
          t(T) === "logs" ? p(At) : t(T) === "artifacts" ? p(jt, 1) : p(St, -1);
        });
      }
      var Pt = e(Ca, 2), Da = a(Pt), Fa = a(Da), Et = a(Fa), Ia = a(Et), qt = a(Ia), Nt = e(Ia, 2), Tt = a(Nt), Bt = e(Fa, 2), Ha = a(Bt), Oa = a(Ha), Lt = a(Oa), Mt = e(Oa, 2), Rt = a(Mt), Ct = e(Ha, 2), za = a(Ct);
      {
        let p = S(() => !!t(P));
        Y(za, {
          variant: "primary",
          get disabled() {
            return t(p);
          },
          onclick: dt,
          children: (g, o) => {
            var x = C();
            c(($) => i(x, $), [() => d("common.refresh")]), v(g, x);
          },
          $$slots: { default: !0 }
        });
      }
      var Dt = e(za, 2);
      Y(Dt, {
        onclick: () => $a(u()),
        children: (p, g) => {
          var o = C();
          c((x) => i(o, x), [() => d("diag.copy_path")]), v(p, o);
        },
        $$slots: { default: !0 }
      });
      var Ft = e(Da, 2), Ka = a(Ft), It = a(Ka), Ua = a(It), Ht = a(Ua), Ot = e(Ua, 2), zt = a(Ot), Kt = e(Ka, 2), Ut = a(Kt), Ga = a(Ut), Ja = a(Ga), Gt = a(Ja), Jt = e(Ja), Wa = e(Ga, 2), Va = a(Wa), Wt = a(Va), Vt = e(Va), Ya = e(Wa, 2), Za = a(Ya), Yt = a(Za), Zt = e(Za), Qt = e(Ya, 2), Qa = a(Qt), Xt = a(Qa), ar = e(Qa);
      c(
        (p, g, o, x, $, z, K, U, G, I, J, W, H, y) => {
          i(ia, p), i(da, g), i(kt, o), i(qt, x), i(Tt, $), i(Lt, z), i(Rt, `${K ?? ""} • ${t(ft) ?? ""}%`), i(Ht, U), i(zt, G), i(Gt, `${I ?? ""}:`), i(Jt, ` ${J ?? ""}`), i(Wt, `${W ?? ""}:`), i(Vt, ` ${(t(n)?.lifecycle || "idle") ?? ""}`), i(Yt, `${H ?? ""}:`), i(Zt, ` ${(t(E)?.voice_edit_status || "not_started") ?? ""}`), i(Xt, `${y ?? ""}:`), i(ar, ` ${(t(E)?.required_action || "—") ?? ""}`);
        },
        [
          () => d("diag.pipeline_logs"),
          () => d("diag.pipeline_artifacts"),
          () => d("diag.pipeline_state"),
          () => d("diag.summary.title"),
          () => d("diag.summary.sub"),
          () => t(n)?.current_stage_label || d("diag.summary.idle"),
          () => t(n)?.status_label || d("status.waiting"),
          () => d("diag.quick_state.title"),
          () => d("diag.quick_state.sub"),
          () => d("diag.quick_state.workspace"),
          () => u() || "—",
          () => d("diag.quick_state.lifecycle"),
          () => d("diag.quick_state.voice_status"),
          () => d("diag.quick_state.required_action")
        ]
      ), v(r, s);
    };
    oa(gt, (r) => {
      t(bt) ? r(mt) : t(D) ? r(xt, 1) : r(ht, -1);
    });
  }
  v(na, La), cr();
}
dr(["click"]);
const et = br(Br), zr = et.mount, Kr = et.unmount;
export {
  zr as mount,
  Kr as unmount
};
//# sourceMappingURL=diagnostics.js.map
