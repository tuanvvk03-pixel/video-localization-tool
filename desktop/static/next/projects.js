import { d as Ua, p as Ka, s as F, w as Et, x as Ta, c as j, e as _, i as K, g as t, l as i, Q as yt, t as c, j as o, R as $t, m as C, a as v, b as Qa, h as r, f as le, o as P, r as ne, K as pt, z as Ga, n as O, u as x, A as Ha, O as vr, M as Ja } from "./chunks/api-vHpIWCot.js";
import { o as Wa } from "./chunks/index-client-CjB8cgHo.js";
import { e as de, i as cr } from "./chunks/each-BE197-93.js";
import { b as pr } from "./chunks/input-D0G7l_P3.js";
import { n as Y, a as Xa } from "./chunks/helpers-IwLKX_Lo.js";
import { B as z } from "./chunks/Button-GpBM5g0S.js";
import { S as Ya } from "./chunks/StatusBadge-DT3lodBA.js";
import { s as Za } from "./chunks/screen-DRq5NjFu.js";
var ti = O('<div class="error-banner"><div class="error-code">UI</div><div class="error-message"> </div></div>'), ei = O('<div class="info-banner"> </div>'), ur = O("<option> </option>"), ri = O('<div class="toolbar"><input class="input" style="max-width:320px" type="text"/> <!></div> <div class="small-muted"> </div>', 1), ai = O('<div class="small-muted"> </div> <div class="toolbar"><!> <!> <!> <!></div> <div class="small-muted"> </div> <div class="toolbar"><select class="input" style="max-width:240px"><option> </option><!></select> <!> <!></div> <div class="toolbar"><input class="input" style="max-width:240px" type="text"/> <!></div> <div class="small-muted"> </div>', 1), ii = O('<div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option><option> </option></select></div>'), oi = O('<div class="empty-card"><div class="empty-icon">＋</div><h3> </h3><p> </p></div>'), gr = O('<div class="small-muted"> </div>'), si = O('<a target="_blank" rel="noopener"> </a>'), li = O('<tr><td><div class="row-title"> </div><div class="small-muted"> </div></td><td><!> <!></td><td><!></td></tr>'), ni = O('<table class="review-table"><thead><tr><th> </th><th> </th><th> </th></tr></thead><tbody></tbody></table>'), di = O('<div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option></select></div> <div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/></div> <div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/></div> <!></div> <div class="clip-row"><div class="clip-col"><div class="row-title"> </div> <div class="small-muted"> </div> <div class="toolbar"><!> <!></div></div> <div class="clip-col"><div class="row-title"> </div> <div class="small-muted"> </div> <div class="toolbar"><!> <!></div></div> <div class="clip-col"><div class="row-title"> </div> <div class="small-muted"> </div> <div class="toolbar"><!> <!></div></div></div> <div class="stack" style="gap:6px;margin-top:8px"><div class="card-title"> </div><div class="card-sub"> </div></div> <label class="checkbox-row"><input type="checkbox"/> </label> <div class="field-grid"><div class="field"><label> </label> <input class="input" type="range" min="0.8" max="1.2" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="1" max="1.3" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="-0.2" max="0.2" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0.7" max="1.3" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0.5" max="1.5" step="0.01"/></div></div> <div class="toolbar"><!></div></div></div> <div class="card"><div class="card-header"><div><div class="card-title"> </div> <div class="card-sub"> </div></div></div> <div class="card-body"><!></div></div>', 1), _i = O('<div class="screen stack" data-testid="projects-screen"><!> <!> <div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option>edge_tts</option><option>azure_tts</option></select></div> <div class="field"><label> </label> <select class="input"><option> </option><!></select></div> <div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option></select></div></div> <!></div></div> <!></div>');
function vi(fr, _e) {
  Ka(_e, !0);
  const a = (e, s) => (_e.ctx?.t ?? ((n) => n))(e, s);
  let Ut = F(""), u = F(""), V = F(Et([])), jt = F(Et({})), ve = F(Et([])), A = F(Et({
    tts_provider: "edge_tts",
    tts_voice: "",
    mix_mode: "replace_original_speech"
  })), Kt = F(""), ut = F(!1), T = F(""), zt = F(""), Q = F(null), ce = F(Et([])), D = F(""), Ft = F(""), Z = null;
  Wa(() => {
    Z && clearInterval(Z);
  }), Ta(() => {
    yr(), Tt();
  });
  async function Tt() {
    try {
      const e = await j("/api/presets/list", {});
      _(ce, Array.isArray(e.presets) ? e.presets : [], !0);
    } catch {
    }
  }
  const hr = () => I("preset_save", async () => {
    const e = t(Ft).trim();
    if (!e) throw new Error(a("projects.preset_name_required"));
    if (!t(u)) throw new Error(a("projects.create_first"));
    await j("/api/presets/save", { name: e, project_root: t(u) }), _(Ft, ""), _(T, a("projects.preset_saved"), !0), await Tt();
  }), br = () => I("preset_apply", async () => {
    !t(D) || !t(u) || (await j("/api/presets/apply", {
      preset_id: t(D),
      project_root: t(u)
    }), _(T, a("projects.preset_applied"), !0), await wt());
  }), xr = () => I("preset_delete", async () => {
    !t(D) || !window.confirm(a("projects.preset_confirm_delete")) || (await j("/api/presets/delete", { preset_id: t(D) }), _(D, ""), await Tt());
  });
  async function yr() {
    try {
      const e = await j("/api/list-voices", {});
      _(
        ve,
        Array.isArray(e.voices) ? e.voices.filter((s) => s && s.voice_id && s.enabled !== !1) : [],
        !0
      );
    } catch {
    }
  }
  async function I(e, s) {
    _(zt, ""), _(Kt, e, !0), _(T, "");
    try {
      await s();
    } catch (n) {
      _(zt, n instanceof Ha ? n.summary || n.message : n?.message || "error", !0);
    } finally {
      _(Kt, "");
    }
  }
  const S = () => !!t(Kt) || t(ut), $r = () => I("create", async () => {
    const e = t(Ut).trim();
    if (!e) throw new Error(a("projects.name_required"));
    const s = await j("/api/init-project", {
      project_name: e,
      config_overrides: {
        tts_provider: t(A).tts_provider,
        tts_voice: t(A).tts_voice.trim(),
        mix_mode: t(A).mix_mode,
        translate_backend: "block_v2"
      }
    });
    _(u, String(s.project_root || ""), !0), _(T, a("projects.created"), !0), await wt();
  }), jr = () => I("add", async () => {
    if (!t(u)) throw new Error(a("projects.create_first"));
    const e = await Ja({
      filters: ["Video files (*.mp4;*.mov;*.mkv;*.webm)", "All files (*.*)"]
    });
    if (e?.cancelled) return;
    const s = e?.paths || [];
    if (!s.length) throw new Error(e?.error || a("projects.pick_unavailable"));
    let n = 0;
    const w = [];
    for (const E of s)
      try {
        await j("/api/add-video-to-project", { project_root: t(u), video: E }), n++;
      } catch {
        w.push(E.split(/[\\/]/).pop() || E);
      }
    _(T, a("projects.added", { count: n }) + (w.length ? ` (${a("projects.add_failed", { count: w.length })})` : "")), await wt();
  });
  async function wt() {
    if (!t(u)) return;
    const e = await j("/api/get-project", { project_root: t(u) });
    _(V, Array.isArray(e.videos) ? e.videos : [], !0);
    const s = {};
    for (const n of e.statuses || []) s[String(n.video_id)] = n;
    _(jt, s, !0), e.config && _(
      A,
      {
        tts_provider: e.config.tts_provider || "edge_tts",
        tts_voice: e.config.tts_voice || "",
        mix_mode: e.config.mix_mode || "replace_original_speech"
      },
      !0
    ), await wr();
  }
  async function wr() {
    if (t(u))
      try {
        const e = await j("/api/render-settings/status", { job_workspace: t(u) });
        _(Q, Y(e.render || {}), !0);
      } catch {
      }
  }
  function Qt() {
    const e = t(Q) || Y({}), s = {
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
    }), Xa(s, e), s;
  }
  function G(e) {
    _(Q, Y({ ...t(Q) || {}, ...e }), !0);
  }
  const kr = () => I("brand_save", async () => {
    const e = await j("/api/render-settings/save", { job_workspace: t(u), render: Qt() });
    _(Q, Y(e.render), !0), _(T, a("projects.brand_saved"), !0);
  }), Pr = () => I("brand_logo", async () => {
    const e = await vr({
      filters: ["Image files (*.png;*.jpg;*.jpeg;*.webp)", "All files (*.*)"]
    });
    if (e?.cancelled) return;
    if (!e?.ok || !e.path) throw new Error(e?.error || a("projects.pick_unavailable"));
    await j("/api/render-settings/save", { job_workspace: t(u), render: Qt() });
    const s = await j("/api/render-logo/upload", { job_workspace: t(u), image_path: e.path });
    _(Q, Y(s.render), !0);
  }), Ar = () => I("brand_logo_rm", async () => {
    const e = await j("/api/render-logo/remove", { job_workspace: t(u) });
    _(Q, Y(e.render), !0);
  }), pe = (e) => I(`brand_${e}`, async () => {
    const s = await vr({
      filters: ["Video files (*.mp4;*.mov;*.mkv;*.webm)", "All files (*.*)"]
    });
    if (s?.cancelled) return;
    if (!s?.ok || !s.path) throw new Error(s?.error || a("projects.pick_unavailable"));
    await j("/api/render-settings/save", { job_workspace: t(u), render: Qt() });
    const n = await j(`/api/render-${e}/upload`, { job_workspace: t(u), clip_path: s.path });
    _(Q, Y(n.render), !0);
  }), ue = (e) => I(`brand_${e}_rm`, async () => {
    const s = await j(`/api/render-${e}/remove`, { job_workspace: t(u) });
    _(Q, Y(s.render), !0);
  }), Br = () => I("run", async () => {
    if (!t(u) || !t(V).length) throw new Error(a("projects.no_videos"));
    _(ut, !0);
    try {
      await j("/api/run-project", { project_root: t(u), async: !0 }), Sr();
    } catch (e) {
      throw _(ut, !1), e;
    }
  }), Nr = () => I("export", async () => {
    if (!t(u)) return;
    const e = await j("/api/export-project", { project_root: t(u) });
    _(T, a("projects.exported", { count: (e.exported || []).length, dir: e.export_dir }), !0);
    try {
      await j("/api/reveal", { path: e.export_dir });
    } catch {
    }
  });
  function Sr() {
    Z && clearInterval(Z), Z = setInterval(
      async () => {
        try {
          await wt(), t(V).length && t(V).every((e) => Er(t(jt)[e.video_id])) && (_(ut, !1), Z && (clearInterval(Z), Z = null), _(T, a("projects.done"), !0));
        } catch {
        }
      },
      3e3
    );
  }
  function st(e) {
    return String(e?.current_stage || e?.status || "queued");
  }
  function Er(e) {
    const s = st(e);
    return s.includes("rendered") || s.includes("failed");
  }
  function zr(e) {
    const s = st(e);
    return s.includes("failed") ? "blocked" : s.includes("rendered") ? "completed" : t(ut) ? "running" : "queued";
  }
  function Fr(e) {
    const s = String(e?.workspace || "");
    return s ? `/media?${new URLSearchParams({
      workspace: s,
      rel: "artifacts/render/final.mp4",
      v: String(Date.now())
    }).toString()}` : "";
  }
  const ge = x(() => t(V).filter((e) => st(t(jt)[e.video_id]).includes("rendered")).length), Cr = x(() => t(V).filter((e) => st(t(jt)[e.video_id]).includes("failed")).length), d = x(() => t(Q) || Y({})), Gt = (e) => (e || "").split(/[\\/]/).pop();
  var me = _i(), fe = r(me);
  {
    var Ir = (e) => {
      var s = ti(), n = i(r(s)), w = r(n);
      c(() => o(w, t(zt))), v(e, s);
    };
    K(fe, (e) => {
      t(zt) && e(Ir);
    });
  }
  var he = i(fe, 2);
  {
    var Lr = (e) => {
      var s = ei(), n = r(s);
      c(() => o(n, t(T))), v(e, s);
    };
    K(he, (e) => {
      t(T) && e(Lr);
    });
  }
  var be = i(he, 2), xe = r(be), Or = r(xe), ye = r(Or), qr = r(ye), Rr = i(ye), Vr = r(Rr), Dr = i(xe, 2), $e = r(Dr), je = r($e), we = r(je), Mr = r(we), lt = i(we, 2), Ht = r(lt);
  Ht.value = Ht.__value = "edge_tts";
  var ke = i(Ht);
  ke.value = ke.__value = "azure_tts";
  var Pe;
  yt(lt);
  var Ae = i(je, 2), Be = r(Ae), Ur = r(Be), nt = i(Be, 2), Ct = r(nt), Kr = r(Ct);
  Ct.value = Ct.__value = "";
  var Tr = i(Ct);
  de(Tr, 17, () => t(ve), cr, (e, s) => {
    var n = ur(), w = r(n), E = {};
    c(() => {
      o(w, t(s).short_name || t(s).label || t(s).voice_id), E !== (E = t(s).voice_id) && (n.value = (n.__value = t(s).voice_id) ?? "");
    }), v(e, n);
  });
  var Ne;
  yt(nt);
  var Qr = i(Ae, 2), Se = r(Qr), Gr = r(Se), dt = i(Se, 2), It = r(dt), Hr = r(It);
  It.value = It.__value = "replace_original_speech";
  var Lt = i(It), Jr = r(Lt);
  Lt.value = Lt.__value = "duck_original_speech";
  var Jt = i(Lt), Wr = r(Jt);
  Jt.value = Jt.__value = "keep_music_replace_voice";
  var Ee;
  yt(dt);
  var Xr = i($e, 2);
  {
    var Yr = (e) => {
      var s = ri(), n = le(s), w = r(n), E = i(w, 2);
      {
        let q = x(S);
        z(E, {
          variant: "primary",
          get disabled() {
            return t(q);
          },
          onclick: $r,
          children: (X, kt) => {
            var _t = P();
            c((vt) => o(_t, vt), [() => a("projects.create")]), v(X, _t);
          },
          $$slots: { default: !0 }
        });
      }
      var W = i(n, 2), tt = r(W);
      c(
        (q, X) => {
          ne(w, "placeholder", q), o(tt, X);
        },
        [
          () => a("projects.name_placeholder"),
          () => a("projects.create_hint")
        ]
      ), pr(w, () => t(Ut), (q) => _(Ut, q)), v(e, s);
    }, Zr = (e) => {
      var s = ai(), n = le(s), w = r(n), E = i(n, 2), W = r(E);
      {
        let f = x(S);
        z(W, {
          variant: "secondary",
          get disabled() {
            return t(f);
          },
          onclick: jr,
          children: (h, B) => {
            var g = P();
            c((y) => o(g, y), [() => a("projects.add_videos")]), v(h, g);
          },
          $$slots: { default: !0 }
        });
      }
      var tt = i(W, 2);
      {
        let f = x(() => S() || !t(V).length);
        z(tt, {
          variant: "strong",
          get disabled() {
            return t(f);
          },
          onclick: Br,
          children: (h, B) => {
            var g = P();
            c((y) => o(g, y), [
              () => t(ut) ? a("projects.running") : a("projects.run_all")
            ]), v(h, g);
          },
          $$slots: { default: !0 }
        });
      }
      var q = i(tt, 2);
      {
        let f = x(() => S() || t(ge) === 0);
        z(q, {
          get disabled() {
            return t(f);
          },
          onclick: Nr,
          children: (h, B) => {
            var g = P();
            c((y) => o(g, y), [() => a("projects.export_all")]), v(h, g);
          },
          $$slots: { default: !0 }
        });
      }
      var X = i(q, 2);
      {
        let f = x(S);
        z(X, {
          get disabled() {
            return t(f);
          },
          onclick: () => I("refresh", wt),
          children: (h, B) => {
            var g = P();
            c((y) => o(g, y), [() => a("projects.refresh")]), v(h, g);
          },
          $$slots: { default: !0 }
        });
      }
      var kt = i(E, 2), _t = r(kt), vt = i(kt, 2), H = r(vt), gt = r(H), et = r(gt);
      gt.value = gt.__value = "";
      var mt = i(gt);
      de(mt, 17, () => t(ce), cr, (f, h) => {
        var B = ur(), g = r(B), y = {};
        c(() => {
          o(g, t(h).name), y !== (y = t(h).id) && (B.value = (B.__value = t(h).id) ?? "");
        }), v(f, B);
      });
      var Ot;
      yt(H);
      var ct = i(H, 2);
      {
        let f = x(() => S() || !t(D));
        z(ct, {
          get disabled() {
            return t(f);
          },
          onclick: br,
          children: (h, B) => {
            var g = P();
            c((y) => o(g, y), [() => a("projects.preset_apply")]), v(h, g);
          },
          $$slots: { default: !0 }
        });
      }
      var Wt = i(ct, 2);
      {
        let f = x(() => S() || !t(D));
        z(Wt, {
          get disabled() {
            return t(f);
          },
          onclick: xr,
          children: (h, B) => {
            var g = P();
            c((y) => o(g, y), [() => a("projects.preset_delete")]), v(h, g);
          },
          $$slots: { default: !0 }
        });
      }
      var ft = i(vt, 2), Pt = r(ft), qt = i(Pt, 2);
      {
        let f = x(S);
        z(qt, {
          get disabled() {
            return t(f);
          },
          onclick: hr,
          children: (h, B) => {
            var g = P();
            c((y) => o(g, y), [() => a("projects.preset_save")]), v(h, g);
          },
          $$slots: { default: !0 }
        });
      }
      var Rt = i(ft, 2), Vt = r(Rt);
      c(
        (f, h, B, g, y) => {
          o(w, `${f ?? ""}: ${t(u) ?? ""}`), o(_t, h), o(et, B), Ot !== (Ot = t(D)) && (H.value = (H.__value = t(D)) ?? "", $t(H, t(D))), ne(Pt, "placeholder", g), o(Vt, y);
        },
        [
          () => a("projects.open_label"),
          () => a("projects.cfg_locked_hint"),
          () => a("projects.preset_select"),
          () => a("projects.preset_name_placeholder"),
          () => a("projects.preset_hint")
        ]
      ), C("change", H, (f) => _(D, f.target.value, !0)), pr(Pt, () => t(Ft), (f) => _(Ft, f)), v(e, s);
    };
    K(Xr, (e) => {
      t(u) ? e(Zr, -1) : e(Yr);
    });
  }
  var ta = i(be, 2);
  {
    var ea = (e) => {
      var s = di(), n = le(s), w = r(n), E = r(w), W = r(E), tt = r(W), q = i(W), X = r(q), kt = i(w, 2), _t = r(kt), vt = r(_t), H = r(vt), gt = r(H), et = i(H, 2), mt = r(et), Ot = r(mt);
      mt.value = mt.__value = "16:9";
      var ct = i(mt), Wt = r(ct);
      ct.value = ct.__value = "9:16";
      var ft = i(ct), Pt = r(ft);
      ft.value = ft.__value = "1:1";
      var qt;
      yt(et);
      var Rt = i(vt, 2), Vt = r(Rt), f = r(Vt), h = i(Vt, 2), B = i(Rt, 2), g = r(B), y = r(g), ze = i(g, 2), ra = i(B, 2);
      {
        var aa = (l) => {
          var m = ii(), $ = r(m), b = r($), p = i($, 2), N = r(p), rt = r(N);
          N.value = N.__value = "top-left";
          var J = i(N), At = r(J);
          J.value = J.__value = "top-right";
          var at = i(J), Bt = r(at);
          at.value = at.__value = "bottom-left";
          var M = i(at), U = r(M);
          M.value = M.__value = "bottom-right";
          var R;
          yt(p), c(
            (it, ht, bt, Nt, St) => {
              o(b, it), o(rt, ht), o(At, bt), o(Bt, Nt), o(U, St), R !== (R = t(d).logo_position) && (p.value = (p.__value = t(d).logo_position) ?? "", $t(p, t(d).logo_position));
            },
            [
              () => a("settings.render_layout.logo_position"),
              () => a("settings.render_layout.pos_top_left"),
              () => a("settings.render_layout.pos_top_right"),
              () => a("settings.render_layout.pos_bottom_left"),
              () => a("settings.render_layout.pos_bottom_right")
            ]
          ), C("change", p, (it) => G({ logo_position: it.target.value })), v(l, m);
        };
        K(ra, (l) => {
          t(d).logo_path && l(aa);
        });
      }
      var Fe = i(_t, 2), Ce = r(Fe), Ie = r(Ce), ia = r(Ie), Le = i(Ie, 2), oa = r(Le), sa = i(Le, 2), Oe = r(sa);
      {
        let l = x(S);
        z(Oe, {
          variant: "secondary",
          get disabled() {
            return t(l);
          },
          onclick: Pr,
          children: (m, $) => {
            var b = P();
            c((p) => o(b, p), [() => a("settings.render_layout.upload_logo")]), v(m, b);
          },
          $$slots: { default: !0 }
        });
      }
      var la = i(Oe, 2);
      {
        var na = (l) => {
          {
            let m = x(S);
            z(l, {
              get disabled() {
                return t(m);
              },
              onclick: Ar,
              children: ($, b) => {
                var p = P();
                c((N) => o(p, N), [() => a("settings.render_layout.remove_logo")]), v($, p);
              },
              $$slots: { default: !0 }
            });
          }
        };
        K(la, (l) => {
          t(d).logo_path && l(na);
        });
      }
      var qe = i(Ce, 2), Re = r(qe), da = r(Re), Ve = i(Re, 2), _a = r(Ve), va = i(Ve, 2), De = r(va);
      {
        let l = x(S);
        z(De, {
          variant: "secondary",
          get disabled() {
            return t(l);
          },
          onclick: () => pe("intro"),
          children: (m, $) => {
            var b = P();
            c((p) => o(b, p), [() => a("settings.render_layout.upload_intro")]), v(m, b);
          },
          $$slots: { default: !0 }
        });
      }
      var ca = i(De, 2);
      {
        var pa = (l) => {
          {
            let m = x(S);
            z(l, {
              get disabled() {
                return t(m);
              },
              onclick: () => ue("intro"),
              children: ($, b) => {
                var p = P();
                c((N) => o(p, N), [() => a("settings.render_layout.remove_clip")]), v($, p);
              },
              $$slots: { default: !0 }
            });
          }
        };
        K(ca, (l) => {
          t(d).intro_clip_path && l(pa);
        });
      }
      var ua = i(qe, 2), Me = r(ua), ga = r(Me), Ue = i(Me, 2), ma = r(Ue), fa = i(Ue, 2), Ke = r(fa);
      {
        let l = x(S);
        z(Ke, {
          variant: "secondary",
          get disabled() {
            return t(l);
          },
          onclick: () => pe("outro"),
          children: (m, $) => {
            var b = P();
            c((p) => o(b, p), [() => a("settings.render_layout.upload_outro")]), v(m, b);
          },
          $$slots: { default: !0 }
        });
      }
      var ha = i(Ke, 2);
      {
        var ba = (l) => {
          {
            let m = x(S);
            z(l, {
              get disabled() {
                return t(m);
              },
              onclick: () => ue("outro"),
              children: ($, b) => {
                var p = P();
                c((N) => o(p, N), [() => a("settings.render_layout.remove_clip")]), v($, p);
              },
              $$slots: { default: !0 }
            });
          }
        };
        K(ha, (l) => {
          t(d).outro_clip_path && l(ba);
        });
      }
      var Te = i(Fe, 2), Qe = r(Te), xa = r(Qe), ya = i(Qe), $a = r(ya), Ge = i(Te, 2), Xt = r(Ge), ja = i(Xt, 1, !0), He = i(Ge, 2), Je = r(He), We = r(Je), wa = r(We), Xe = i(We, 2), Ye = i(Je, 2), Ze = r(Ye), ka = r(Ze), tr = i(Ze, 2), er = i(Ye, 2), rr = r(er), Pa = r(rr), ar = i(rr, 2), ir = i(er, 2), or = r(ir), Aa = r(or), sr = i(or, 2), Ba = i(ir, 2), lr = r(Ba), Na = r(lr), nr = i(lr, 2), Sa = i(He, 2), Ea = r(Sa);
      {
        let l = x(S);
        z(Ea, {
          variant: "primary",
          get disabled() {
            return t(l);
          },
          onclick: kr,
          children: (m, $) => {
            var b = P();
            c((p) => o(b, p), [() => a("settings.render_layout.save")]), v(m, b);
          },
          $$slots: { default: !0 }
        });
      }
      var za = i(n, 2), dr = r(za), Fa = r(dr), _r = r(Fa), Ca = r(_r), Ia = i(_r, 2), La = r(Ia), Oa = i(dr, 2), qa = r(Oa);
      {
        var Ra = (l) => {
          var m = oi(), $ = i(r(m)), b = r($), p = i($), N = r(p);
          c(
            (rt, J) => {
              o(b, rt), o(N, J);
            },
            [
              () => a("projects.empty_title"),
              () => a("projects.empty_body")
            ]
          ), v(l, m);
        }, Va = (l) => {
          var m = ni(), $ = r(m), b = r($), p = r(b), N = r(p), rt = i(p), J = r(rt), At = i(rt), at = r(At), Bt = i($);
          de(Bt, 21, () => t(V), (M) => M.video_id, (M, U) => {
            const R = x(() => t(jt)[t(U).video_id]);
            var it = li(), ht = r(it), bt = r(ht), Nt = r(bt), St = i(bt), Yt = r(St), Dt = i(ht), Mt = r(Dt);
            {
              let k = x(() => zr(t(R)));
              Ya(Mt, {
                get kind() {
                  return t(k);
                },
                children: (L, xt) => {
                  var ot = P();
                  c((se) => o(ot, se), [() => st(t(R))]), v(L, ot);
                },
                $$slots: { default: !0 }
              });
            }
            var Zt = i(Mt, 2);
            {
              var te = (k) => {
                var L = gr(), xt = r(L);
                c((ot) => o(xt, ot), [() => a("projects.tag_no_dub")]), v(k, L);
              }, ee = (k) => {
                var L = gr(), xt = r(L);
                c((ot) => o(xt, ot), [() => a("projects.tag_dub")]), v(k, L);
              }, re = x(() => st(t(R)).includes("rendered"));
              K(Zt, (k) => {
                t(R)?.no_dub ? k(te) : t(re) && k(ee, 1);
              });
            }
            var ae = i(Dt), ie = r(ae);
            {
              var oe = (k) => {
                var L = si(), xt = r(L);
                c(
                  (ot, se) => {
                    ne(L, "href", ot), o(xt, se);
                  },
                  [() => Fr(t(U)), () => a("projects.open_output")]
                ), v(k, L);
              }, Da = x(() => st(t(R)).includes("rendered")), Ma = (k) => {
                var L = P("—");
                v(k, L);
              };
              K(ie, (k) => {
                t(Da) ? k(oe) : k(Ma, -1);
              });
            }
            c(
              (k) => {
                o(Nt, t(U).video_id), o(Yt, `${k ?? ""}${t(U).is_long ? " · long" : ""}`);
              },
              [() => (t(U).source_path || "").split(/[\\/]/).pop()]
            ), v(M, it);
          }), c(
            (M, U, R) => {
              o(N, M), o(J, U), o(at, R);
            },
            [
              () => a("projects.col_video"),
              () => a("projects.col_status"),
              () => a("projects.col_output")
            ]
          ), v(l, m);
        };
        K(qa, (l) => {
          t(V).length ? l(Va, -1) : l(Ra);
        });
      }
      c(
        (l, m, $, b, p, N, rt, J, At, at, Bt, M, U, R, it, ht, bt, Nt, St, Yt, Dt, Mt, Zt, te, ee, re, ae, ie, oe) => {
          o(tt, l), o(X, m), o(gt, $), o(Ot, b), o(Wt, p), o(Pt, N), qt !== (qt = t(d).aspect_ratio) && (et.value = (et.__value = t(d).aspect_ratio) ?? "", $t(et, t(d).aspect_ratio)), o(f, `${rt ?? ""} (${t(d).head_trim_sec ?? ""}s)`), pt(h, t(d).head_trim_sec), o(y, `${J ?? ""} (${t(d).tail_trim_sec ?? ""}s)`), pt(ze, t(d).tail_trim_sec), o(ia, At), o(oa, at), o(da, Bt), o(_a, M), o(ga, U), o(ma, R), o(xa, it), o($a, ht), Ga(Xt, t(d).transform_hflip), o(ja, bt), o(wa, `${Nt ?? ""} (${St ?? ""}x)`), pt(Xe, t(d).transform_speed), o(ka, `${Yt ?? ""} (${Dt ?? ""}%)`), pt(tr, t(d).transform_zoom), o(Pa, `${Mt ?? ""} (${Zt ?? ""})`), pt(ar, t(d).transform_brightness), o(Aa, `${te ?? ""} (${ee ?? ""})`), pt(sr, t(d).transform_contrast), o(Na, `${re ?? ""} (${ae ?? ""})`), pt(nr, t(d).transform_saturation), o(Ca, ie), o(La, oe);
        },
        [
          () => a("projects.brand_title"),
          () => a("projects.brand_sub"),
          () => a("settings.render_layout.aspect_ratio"),
          () => a("settings.render_layout.aspect_16_9"),
          () => a("settings.render_layout.aspect_9_16"),
          () => a("settings.render_layout.aspect_1_1"),
          () => a("settings.render_layout.head_trim"),
          () => a("settings.render_layout.tail_trim"),
          () => a("settings.render_layout.logo_title"),
          () => t(d).logo_path ? Gt(t(d).logo_original_filename || t(d).logo_path) : a("settings.render_layout.no_logo"),
          () => a("settings.render_layout.intro_clip"),
          () => t(d).intro_clip_path ? Gt(t(d).intro_original_filename || t(d).intro_clip_path) : a("settings.render_layout.no_clip"),
          () => a("settings.render_layout.outro_clip"),
          () => t(d).outro_clip_path ? Gt(t(d).outro_original_filename || t(d).outro_clip_path) : a("settings.render_layout.no_clip"),
          () => a("settings.render_layout.tx_title"),
          () => a("settings.render_layout.tx_sub"),
          () => a("settings.render_layout.tx_hflip"),
          () => a("settings.render_layout.tx_speed"),
          () => t(d).transform_speed.toFixed(2),
          () => a("settings.render_layout.tx_zoom"),
          () => Math.round((t(d).transform_zoom - 1) * 100),
          () => a("settings.render_layout.tx_brightness"),
          () => t(d).transform_brightness.toFixed(2),
          () => a("settings.render_layout.tx_contrast"),
          () => t(d).transform_contrast.toFixed(2),
          () => a("settings.render_layout.tx_saturation"),
          () => t(d).transform_saturation.toFixed(2),
          () => a("projects.videos_title", { count: t(V).length }),
          () => a("projects.progress_summary", {
            done: t(ge),
            failed: t(Cr),
            total: t(V).length
          })
        ]
      ), C("change", et, (l) => G({ aspect_ratio: l.target.value })), C("change", h, (l) => G({ head_trim_sec: Number(l.target.value) })), C("change", ze, (l) => G({ tail_trim_sec: Number(l.target.value) })), C("change", Xt, (l) => G({ transform_hflip: l.target.checked })), C("input", Xe, (l) => G({ transform_speed: Number(l.target.value) })), C("input", tr, (l) => G({ transform_zoom: Number(l.target.value) })), C("input", ar, (l) => G({ transform_brightness: Number(l.target.value) })), C("input", sr, (l) => G({ transform_contrast: Number(l.target.value) })), C("input", nr, (l) => G({ transform_saturation: Number(l.target.value) })), v(e, s);
    };
    K(ta, (e) => {
      t(u) && e(ea);
    });
  }
  c(
    (e, s, n, w, E, W, tt, q, X) => {
      o(qr, e), o(Vr, s), o(Mr, n), lt.disabled = !!t(u), Pe !== (Pe = t(A).tts_provider) && (lt.value = (lt.__value = t(A).tts_provider) ?? "", $t(lt, t(A).tts_provider)), o(Ur, w), nt.disabled = !!t(u), o(Kr, E), Ne !== (Ne = t(A).tts_voice) && (nt.value = (nt.__value = t(A).tts_voice) ?? "", $t(nt, t(A).tts_voice)), o(Gr, W), dt.disabled = !!t(u), o(Hr, tt), o(Jr, q), o(Wr, X), Ee !== (Ee = t(A).mix_mode) && (dt.value = (dt.__value = t(A).mix_mode) ?? "", $t(dt, t(A).mix_mode));
    },
    [
      () => a("projects.title"),
      () => a("projects.sub"),
      () => a("projects.cfg_provider"),
      () => a("projects.cfg_voice"),
      () => a("projects.cfg_voice_default"),
      () => a("projects.cfg_mix"),
      () => a("settings.tts.mix_replace"),
      () => a("settings.tts.mix_duck"),
      () => a("settings.tts.mix_keep_music")
    ]
  ), C("change", lt, (e) => t(A).tts_provider = e.target.value), C("change", nt, (e) => t(A).tts_voice = e.target.value), C("change", dt, (e) => t(A).mix_mode = e.target.value), v(fr, me), Qa();
}
Ua(["change", "input"]);
const mr = Za(vi), xi = mr.mount, yi = mr.unmount;
export {
  xi as mount,
  yi as unmount
};
//# sourceMappingURL=projects.js.map
