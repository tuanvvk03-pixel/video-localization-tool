import { d as qa, p as Ra, s as z, w as Nt, x as Va, c as j, e as _, i as H, g as t, l as i, Q as bt, t as p, j as o, R as xt, m as F, a as c, b as Da, h as r, f as ie, o as k, r as oe, K as vt, z as Ma, n as O, u as x, A as Ua, O as dr, M as Ka } from "./chunks/api-vHpIWCot.js";
import { o as Ta } from "./chunks/index-client-CjB8cgHo.js";
import { e as se, i as _r } from "./chunks/each-BE197-93.js";
import { b as vr } from "./chunks/input-D0G7l_P3.js";
import { n as Y, a as Qa } from "./chunks/helpers-IwLKX_Lo.js";
import { B as E } from "./chunks/Button-GpBM5g0S.js";
import { S as Ga } from "./chunks/StatusBadge-DT3lodBA.js";
import { s as Ha } from "./chunks/screen-DRq5NjFu.js";
var Ja = O('<div class="error-banner"><div class="error-code">UI</div><div class="error-message"> </div></div>'), Wa = O('<div class="info-banner"> </div>'), cr = O("<option> </option>"), Xa = O('<div class="toolbar"><input class="input" style="max-width:320px" type="text"/> <!></div> <div class="small-muted"> </div>', 1), Ya = O('<div class="small-muted"> </div> <div class="toolbar"><!> <!> <!> <!></div> <div class="small-muted"> </div> <div class="toolbar"><select class="input" style="max-width:240px"><option> </option><!></select> <!> <!></div> <div class="toolbar"><input class="input" style="max-width:240px" type="text"/> <!></div> <div class="small-muted"> </div>', 1), Za = O('<div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option><option> </option></select></div>'), ti = O('<div class="empty-card"><div class="empty-icon">＋</div><h3> </h3><p> </p></div>'), ei = O('<a target="_blank" rel="noopener"> </a>'), ri = O('<tr><td><div class="row-title"> </div><div class="small-muted"> </div></td><td><!></td><td><!></td></tr>'), ai = O('<table class="review-table"><thead><tr><th> </th><th> </th><th> </th></tr></thead><tbody></tbody></table>'), ii = O('<div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option></select></div> <div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/></div> <div class="field"><label> </label> <input class="input" type="number" min="0" max="600" step="0.5"/></div> <!></div> <div class="clip-row"><div class="clip-col"><div class="row-title"> </div> <div class="small-muted"> </div> <div class="toolbar"><!> <!></div></div> <div class="clip-col"><div class="row-title"> </div> <div class="small-muted"> </div> <div class="toolbar"><!> <!></div></div> <div class="clip-col"><div class="row-title"> </div> <div class="small-muted"> </div> <div class="toolbar"><!> <!></div></div></div> <div class="stack" style="gap:6px;margin-top:8px"><div class="card-title"> </div><div class="card-sub"> </div></div> <label class="checkbox-row"><input type="checkbox"/> </label> <div class="field-grid"><div class="field"><label> </label> <input class="input" type="range" min="0.8" max="1.2" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="1" max="1.3" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="-0.2" max="0.2" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0.7" max="1.3" step="0.01"/></div> <div class="field"><label> </label> <input class="input" type="range" min="0.5" max="1.5" step="0.01"/></div></div> <div class="toolbar"><!></div></div></div> <div class="card"><div class="card-header"><div><div class="card-title"> </div> <div class="card-sub"> </div></div></div> <div class="card-body"><!></div></div>', 1), oi = O('<div class="screen stack" data-testid="projects-screen"><!> <!> <div class="card"><div class="card-header"><div><div class="card-title"> </div><div class="card-sub"> </div></div></div> <div class="card-body stack"><div class="field-grid"><div class="field"><label> </label> <select class="input"><option>edge_tts</option><option>azure_tts</option></select></div> <div class="field"><label> </label> <select class="input"><option> </option><!></select></div> <div class="field"><label> </label> <select class="input"><option> </option><option> </option><option> </option></select></div></div> <!></div></div> <!></div>');
function si(ur, le) {
  Ra(le, !0);
  const a = (e, s) => (le.ctx?.t ?? ((n) => n))(e, s);
  let Dt = z(""), u = z(""), q = z(Nt([])), yt = z(Nt({})), ne = z(Nt([])), P = z(Nt({
    tts_provider: "edge_tts",
    tts_voice: "",
    mix_mode: "replace_original_speech"
  })), Mt = z(""), ct = z(!1), M = z(""), St = z(""), U = z(null), de = z(Nt([])), R = z(""), Et = z(""), Z = null;
  Ta(() => {
    Z && clearInterval(Z);
  }), Va(() => {
    hr(), Ut();
  });
  async function Ut() {
    try {
      const e = await j("/api/presets/list", {});
      _(de, Array.isArray(e.presets) ? e.presets : [], !0);
    } catch {
    }
  }
  const gr = () => C("preset_save", async () => {
    const e = t(Et).trim();
    if (!e) throw new Error(a("projects.preset_name_required"));
    if (!t(u)) throw new Error(a("projects.create_first"));
    await j("/api/presets/save", { name: e, project_root: t(u) }), _(Et, ""), _(M, a("projects.preset_saved"), !0), await Ut();
  }), mr = () => C("preset_apply", async () => {
    !t(R) || !t(u) || (await j("/api/presets/apply", {
      preset_id: t(R),
      project_root: t(u)
    }), _(M, a("projects.preset_applied"), !0), await $t());
  }), fr = () => C("preset_delete", async () => {
    !t(R) || !window.confirm(a("projects.preset_confirm_delete")) || (await j("/api/presets/delete", { preset_id: t(R) }), _(R, ""), await Ut());
  });
  async function hr() {
    try {
      const e = await j("/api/list-voices", {});
      _(
        ne,
        Array.isArray(e.voices) ? e.voices.filter((s) => s && s.voice_id && s.enabled !== !1) : [],
        !0
      );
    } catch {
    }
  }
  async function C(e, s) {
    _(St, ""), _(Mt, e, !0), _(M, "");
    try {
      await s();
    } catch (n) {
      _(St, n instanceof Ua ? n.summary || n.message : n?.message || "error", !0);
    } finally {
      _(Mt, "");
    }
  }
  const N = () => !!t(Mt) || t(ct), br = () => C("create", async () => {
    const e = t(Dt).trim();
    if (!e) throw new Error(a("projects.name_required"));
    const s = await j("/api/init-project", {
      project_name: e,
      config_overrides: {
        tts_provider: t(P).tts_provider,
        tts_voice: t(P).tts_voice.trim(),
        mix_mode: t(P).mix_mode,
        translate_backend: "block_v2"
      }
    });
    _(u, String(s.project_root || ""), !0), _(M, a("projects.created"), !0), await $t();
  }), xr = () => C("add", async () => {
    if (!t(u)) throw new Error(a("projects.create_first"));
    const e = await Ka({
      filters: ["Video files (*.mp4;*.mov;*.mkv;*.webm)", "All files (*.*)"]
    });
    if (e?.cancelled) return;
    const s = e?.paths || [];
    if (!s.length) throw new Error(e?.error || a("projects.pick_unavailable"));
    let n = 0;
    const w = [];
    for (const S of s)
      try {
        await j("/api/add-video-to-project", { project_root: t(u), video: S }), n++;
      } catch {
        w.push(S.split(/[\\/]/).pop() || S);
      }
    _(M, a("projects.added", { count: n }) + (w.length ? ` (${a("projects.add_failed", { count: w.length })})` : "")), await $t();
  });
  async function $t() {
    if (!t(u)) return;
    const e = await j("/api/get-project", { project_root: t(u) });
    _(q, Array.isArray(e.videos) ? e.videos : [], !0);
    const s = {};
    for (const n of e.statuses || []) s[String(n.video_id)] = n;
    _(yt, s, !0), e.config && _(
      P,
      {
        tts_provider: e.config.tts_provider || "edge_tts",
        tts_voice: e.config.tts_voice || "",
        mix_mode: e.config.mix_mode || "replace_original_speech"
      },
      !0
    ), await yr();
  }
  async function yr() {
    if (t(u))
      try {
        const e = await j("/api/render-settings/status", { job_workspace: t(u) });
        _(U, Y(e.render || {}), !0);
      } catch {
      }
  }
  function Kt() {
    const e = t(U) || Y({}), s = {
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
    }), Qa(s, e), s;
  }
  function K(e) {
    _(U, Y({ ...t(U) || {}, ...e }), !0);
  }
  const $r = () => C("brand_save", async () => {
    const e = await j("/api/render-settings/save", { job_workspace: t(u), render: Kt() });
    _(U, Y(e.render), !0), _(M, a("projects.brand_saved"), !0);
  }), jr = () => C("brand_logo", async () => {
    const e = await dr({
      filters: ["Image files (*.png;*.jpg;*.jpeg;*.webp)", "All files (*.*)"]
    });
    if (e?.cancelled) return;
    if (!e?.ok || !e.path) throw new Error(e?.error || a("projects.pick_unavailable"));
    await j("/api/render-settings/save", { job_workspace: t(u), render: Kt() });
    const s = await j("/api/render-logo/upload", { job_workspace: t(u), image_path: e.path });
    _(U, Y(s.render), !0);
  }), wr = () => C("brand_logo_rm", async () => {
    const e = await j("/api/render-logo/remove", { job_workspace: t(u) });
    _(U, Y(e.render), !0);
  }), _e = (e) => C(`brand_${e}`, async () => {
    const s = await dr({
      filters: ["Video files (*.mp4;*.mov;*.mkv;*.webm)", "All files (*.*)"]
    });
    if (s?.cancelled) return;
    if (!s?.ok || !s.path) throw new Error(s?.error || a("projects.pick_unavailable"));
    await j("/api/render-settings/save", { job_workspace: t(u), render: Kt() });
    const n = await j(`/api/render-${e}/upload`, { job_workspace: t(u), clip_path: s.path });
    _(U, Y(n.render), !0);
  }), ve = (e) => C(`brand_${e}_rm`, async () => {
    const s = await j(`/api/render-${e}/remove`, { job_workspace: t(u) });
    _(U, Y(s.render), !0);
  }), kr = () => C("run", async () => {
    if (!t(u) || !t(q).length) throw new Error(a("projects.no_videos"));
    _(ct, !0);
    try {
      await j("/api/run-project", { project_root: t(u), async: !0 }), Ar();
    } catch (e) {
      throw _(ct, !1), e;
    }
  }), Pr = () => C("export", async () => {
    if (!t(u)) return;
    const e = await j("/api/export-project", { project_root: t(u) });
    _(M, a("projects.exported", { count: (e.exported || []).length, dir: e.export_dir }), !0);
    try {
      await j("/api/reveal", { path: e.export_dir });
    } catch {
    }
  });
  function Ar() {
    Z && clearInterval(Z), Z = setInterval(
      async () => {
        try {
          await $t(), t(q).length && t(q).every((e) => Br(t(yt)[e.video_id])) && (_(ct, !1), Z && (clearInterval(Z), Z = null), _(M, a("projects.done"), !0));
        } catch {
        }
      },
      3e3
    );
  }
  function pt(e) {
    return String(e?.current_stage || e?.status || "queued");
  }
  function Br(e) {
    const s = pt(e);
    return s.includes("rendered") || s.includes("failed");
  }
  function Nr(e) {
    const s = pt(e);
    return s.includes("failed") ? "blocked" : s.includes("rendered") ? "completed" : t(ct) ? "running" : "queued";
  }
  function Sr(e) {
    const s = String(e?.workspace || "");
    return s ? `/media?${new URLSearchParams({
      workspace: s,
      rel: "artifacts/render/final.mp4",
      v: String(Date.now())
    }).toString()}` : "";
  }
  const ce = x(() => t(q).filter((e) => pt(t(yt)[e.video_id]).includes("rendered")).length), Er = x(() => t(q).filter((e) => pt(t(yt)[e.video_id]).includes("failed")).length), d = x(() => t(U) || Y({})), Tt = (e) => (e || "").split(/[\\/]/).pop();
  var pe = oi(), ue = r(pe);
  {
    var zr = (e) => {
      var s = Ja(), n = i(r(s)), w = r(n);
      p(() => o(w, t(St))), c(e, s);
    };
    H(ue, (e) => {
      t(St) && e(zr);
    });
  }
  var ge = i(ue, 2);
  {
    var Fr = (e) => {
      var s = Wa(), n = r(s);
      p(() => o(n, t(M))), c(e, s);
    };
    H(ge, (e) => {
      t(M) && e(Fr);
    });
  }
  var me = i(ge, 2), fe = r(me), Cr = r(fe), he = r(Cr), Ir = r(he), Lr = i(he), Or = r(Lr), qr = i(fe, 2), be = r(qr), xe = r(be), ye = r(xe), Rr = r(ye), ot = i(ye, 2), Qt = r(ot);
  Qt.value = Qt.__value = "edge_tts";
  var $e = i(Qt);
  $e.value = $e.__value = "azure_tts";
  var je;
  bt(ot);
  var we = i(xe, 2), ke = r(we), Vr = r(ke), st = i(ke, 2), zt = r(st), Dr = r(zt);
  zt.value = zt.__value = "";
  var Mr = i(zt);
  se(Mr, 17, () => t(ne), _r, (e, s) => {
    var n = cr(), w = r(n), S = {};
    p(() => {
      o(w, t(s).short_name || t(s).label || t(s).voice_id), S !== (S = t(s).voice_id) && (n.value = (n.__value = t(s).voice_id) ?? "");
    }), c(e, n);
  });
  var Pe;
  bt(st);
  var Ur = i(we, 2), Ae = r(Ur), Kr = r(Ae), lt = i(Ae, 2), Ft = r(lt), Tr = r(Ft);
  Ft.value = Ft.__value = "replace_original_speech";
  var Ct = i(Ft), Qr = r(Ct);
  Ct.value = Ct.__value = "duck_original_speech";
  var Gt = i(Ct), Gr = r(Gt);
  Gt.value = Gt.__value = "keep_music_replace_voice";
  var Be;
  bt(lt);
  var Hr = i(be, 2);
  {
    var Jr = (e) => {
      var s = Xa(), n = ie(s), w = r(n), S = i(w, 2);
      {
        let I = x(N);
        E(S, {
          variant: "primary",
          get disabled() {
            return t(I);
          },
          onclick: br,
          children: (W, jt) => {
            var nt = k();
            p((dt) => o(nt, dt), [() => a("projects.create")]), c(W, nt);
          },
          $$slots: { default: !0 }
        });
      }
      var J = i(n, 2), tt = r(J);
      p(
        (I, W) => {
          oe(w, "placeholder", I), o(tt, W);
        },
        [
          () => a("projects.name_placeholder"),
          () => a("projects.create_hint")
        ]
      ), vr(w, () => t(Dt), (I) => _(Dt, I)), c(e, s);
    }, Wr = (e) => {
      var s = Ya(), n = ie(s), w = r(n), S = i(n, 2), J = r(S);
      {
        let f = x(N);
        E(J, {
          variant: "secondary",
          get disabled() {
            return t(f);
          },
          onclick: xr,
          children: (h, A) => {
            var g = k();
            p((y) => o(g, y), [() => a("projects.add_videos")]), c(h, g);
          },
          $$slots: { default: !0 }
        });
      }
      var tt = i(J, 2);
      {
        let f = x(() => N() || !t(q).length);
        E(tt, {
          variant: "strong",
          get disabled() {
            return t(f);
          },
          onclick: kr,
          children: (h, A) => {
            var g = k();
            p((y) => o(g, y), [
              () => t(ct) ? a("projects.running") : a("projects.run_all")
            ]), c(h, g);
          },
          $$slots: { default: !0 }
        });
      }
      var I = i(tt, 2);
      {
        let f = x(() => N() || t(ce) === 0);
        E(I, {
          get disabled() {
            return t(f);
          },
          onclick: Pr,
          children: (h, A) => {
            var g = k();
            p((y) => o(g, y), [() => a("projects.export_all")]), c(h, g);
          },
          $$slots: { default: !0 }
        });
      }
      var W = i(I, 2);
      {
        let f = x(N);
        E(W, {
          get disabled() {
            return t(f);
          },
          onclick: () => C("refresh", $t),
          children: (h, A) => {
            var g = k();
            p((y) => o(g, y), [() => a("projects.refresh")]), c(h, g);
          },
          $$slots: { default: !0 }
        });
      }
      var jt = i(S, 2), nt = r(jt), dt = i(jt, 2), T = r(dt), ut = r(T), et = r(ut);
      ut.value = ut.__value = "";
      var gt = i(ut);
      se(gt, 17, () => t(de), _r, (f, h) => {
        var A = cr(), g = r(A), y = {};
        p(() => {
          o(g, t(h).name), y !== (y = t(h).id) && (A.value = (A.__value = t(h).id) ?? "");
        }), c(f, A);
      });
      var It;
      bt(T);
      var _t = i(T, 2);
      {
        let f = x(() => N() || !t(R));
        E(_t, {
          get disabled() {
            return t(f);
          },
          onclick: mr,
          children: (h, A) => {
            var g = k();
            p((y) => o(g, y), [() => a("projects.preset_apply")]), c(h, g);
          },
          $$slots: { default: !0 }
        });
      }
      var Ht = i(_t, 2);
      {
        let f = x(() => N() || !t(R));
        E(Ht, {
          get disabled() {
            return t(f);
          },
          onclick: fr,
          children: (h, A) => {
            var g = k();
            p((y) => o(g, y), [() => a("projects.preset_delete")]), c(h, g);
          },
          $$slots: { default: !0 }
        });
      }
      var mt = i(dt, 2), wt = r(mt), Lt = i(wt, 2);
      {
        let f = x(N);
        E(Lt, {
          get disabled() {
            return t(f);
          },
          onclick: gr,
          children: (h, A) => {
            var g = k();
            p((y) => o(g, y), [() => a("projects.preset_save")]), c(h, g);
          },
          $$slots: { default: !0 }
        });
      }
      var Ot = i(mt, 2), qt = r(Ot);
      p(
        (f, h, A, g, y) => {
          o(w, `${f ?? ""}: ${t(u) ?? ""}`), o(nt, h), o(et, A), It !== (It = t(R)) && (T.value = (T.__value = t(R)) ?? "", xt(T, t(R))), oe(wt, "placeholder", g), o(qt, y);
        },
        [
          () => a("projects.open_label"),
          () => a("projects.cfg_locked_hint"),
          () => a("projects.preset_select"),
          () => a("projects.preset_name_placeholder"),
          () => a("projects.preset_hint")
        ]
      ), F("change", T, (f) => _(R, f.target.value, !0)), vr(wt, () => t(Et), (f) => _(Et, f)), c(e, s);
    };
    H(Hr, (e) => {
      t(u) ? e(Wr, -1) : e(Jr);
    });
  }
  var Xr = i(me, 2);
  {
    var Yr = (e) => {
      var s = ii(), n = ie(s), w = r(n), S = r(w), J = r(S), tt = r(J), I = i(J), W = r(I), jt = i(w, 2), nt = r(jt), dt = r(nt), T = r(dt), ut = r(T), et = i(T, 2), gt = r(et), It = r(gt);
      gt.value = gt.__value = "16:9";
      var _t = i(gt), Ht = r(_t);
      _t.value = _t.__value = "9:16";
      var mt = i(_t), wt = r(mt);
      mt.value = mt.__value = "1:1";
      var Lt;
      bt(et);
      var Ot = i(dt, 2), qt = r(Ot), f = r(qt), h = i(qt, 2), A = i(Ot, 2), g = r(A), y = r(g), Ne = i(g, 2), Zr = i(A, 2);
      {
        var ta = (l) => {
          var m = Za(), $ = r(m), b = r($), v = i($, 2), B = r(v), rt = r(B);
          B.value = B.__value = "top-left";
          var Q = i(B), kt = r(Q);
          Q.value = Q.__value = "top-right";
          var at = i(Q), Pt = r(at);
          at.value = at.__value = "bottom-left";
          var V = i(at), D = r(V);
          V.value = V.__value = "bottom-right";
          var G;
          bt(v), p(
            (it, ft, ht, At, Bt) => {
              o(b, it), o(rt, ft), o(kt, ht), o(Pt, At), o(D, Bt), G !== (G = t(d).logo_position) && (v.value = (v.__value = t(d).logo_position) ?? "", xt(v, t(d).logo_position));
            },
            [
              () => a("settings.render_layout.logo_position"),
              () => a("settings.render_layout.pos_top_left"),
              () => a("settings.render_layout.pos_top_right"),
              () => a("settings.render_layout.pos_bottom_left"),
              () => a("settings.render_layout.pos_bottom_right")
            ]
          ), F("change", v, (it) => K({ logo_position: it.target.value })), c(l, m);
        };
        H(Zr, (l) => {
          t(d).logo_path && l(ta);
        });
      }
      var Se = i(nt, 2), Ee = r(Se), ze = r(Ee), ea = r(ze), Fe = i(ze, 2), ra = r(Fe), aa = i(Fe, 2), Ce = r(aa);
      {
        let l = x(N);
        E(Ce, {
          variant: "secondary",
          get disabled() {
            return t(l);
          },
          onclick: jr,
          children: (m, $) => {
            var b = k();
            p((v) => o(b, v), [() => a("settings.render_layout.upload_logo")]), c(m, b);
          },
          $$slots: { default: !0 }
        });
      }
      var ia = i(Ce, 2);
      {
        var oa = (l) => {
          {
            let m = x(N);
            E(l, {
              get disabled() {
                return t(m);
              },
              onclick: wr,
              children: ($, b) => {
                var v = k();
                p((B) => o(v, B), [() => a("settings.render_layout.remove_logo")]), c($, v);
              },
              $$slots: { default: !0 }
            });
          }
        };
        H(ia, (l) => {
          t(d).logo_path && l(oa);
        });
      }
      var Ie = i(Ee, 2), Le = r(Ie), sa = r(Le), Oe = i(Le, 2), la = r(Oe), na = i(Oe, 2), qe = r(na);
      {
        let l = x(N);
        E(qe, {
          variant: "secondary",
          get disabled() {
            return t(l);
          },
          onclick: () => _e("intro"),
          children: (m, $) => {
            var b = k();
            p((v) => o(b, v), [() => a("settings.render_layout.upload_intro")]), c(m, b);
          },
          $$slots: { default: !0 }
        });
      }
      var da = i(qe, 2);
      {
        var _a = (l) => {
          {
            let m = x(N);
            E(l, {
              get disabled() {
                return t(m);
              },
              onclick: () => ve("intro"),
              children: ($, b) => {
                var v = k();
                p((B) => o(v, B), [() => a("settings.render_layout.remove_clip")]), c($, v);
              },
              $$slots: { default: !0 }
            });
          }
        };
        H(da, (l) => {
          t(d).intro_clip_path && l(_a);
        });
      }
      var va = i(Ie, 2), Re = r(va), ca = r(Re), Ve = i(Re, 2), pa = r(Ve), ua = i(Ve, 2), De = r(ua);
      {
        let l = x(N);
        E(De, {
          variant: "secondary",
          get disabled() {
            return t(l);
          },
          onclick: () => _e("outro"),
          children: (m, $) => {
            var b = k();
            p((v) => o(b, v), [() => a("settings.render_layout.upload_outro")]), c(m, b);
          },
          $$slots: { default: !0 }
        });
      }
      var ga = i(De, 2);
      {
        var ma = (l) => {
          {
            let m = x(N);
            E(l, {
              get disabled() {
                return t(m);
              },
              onclick: () => ve("outro"),
              children: ($, b) => {
                var v = k();
                p((B) => o(v, B), [() => a("settings.render_layout.remove_clip")]), c($, v);
              },
              $$slots: { default: !0 }
            });
          }
        };
        H(ga, (l) => {
          t(d).outro_clip_path && l(ma);
        });
      }
      var Me = i(Se, 2), Ue = r(Me), fa = r(Ue), ha = i(Ue), ba = r(ha), Ke = i(Me, 2), Jt = r(Ke), xa = i(Jt, 1, !0), Te = i(Ke, 2), Qe = r(Te), Ge = r(Qe), ya = r(Ge), He = i(Ge, 2), Je = i(Qe, 2), We = r(Je), $a = r(We), Xe = i(We, 2), Ye = i(Je, 2), Ze = r(Ye), ja = r(Ze), tr = i(Ze, 2), er = i(Ye, 2), rr = r(er), wa = r(rr), ar = i(rr, 2), ka = i(er, 2), ir = r(ka), Pa = r(ir), or = i(ir, 2), Aa = i(Te, 2), Ba = r(Aa);
      {
        let l = x(N);
        E(Ba, {
          variant: "primary",
          get disabled() {
            return t(l);
          },
          onclick: $r,
          children: (m, $) => {
            var b = k();
            p((v) => o(b, v), [() => a("settings.render_layout.save")]), c(m, b);
          },
          $$slots: { default: !0 }
        });
      }
      var Na = i(n, 2), sr = r(Na), Sa = r(sr), lr = r(Sa), Ea = r(lr), za = i(lr, 2), Fa = r(za), Ca = i(sr, 2), Ia = r(Ca);
      {
        var La = (l) => {
          var m = ti(), $ = i(r(m)), b = r($), v = i($), B = r(v);
          p(
            (rt, Q) => {
              o(b, rt), o(B, Q);
            },
            [
              () => a("projects.empty_title"),
              () => a("projects.empty_body")
            ]
          ), c(l, m);
        }, Oa = (l) => {
          var m = ai(), $ = r(m), b = r($), v = r(b), B = r(v), rt = i(v), Q = r(rt), kt = i(rt), at = r(kt), Pt = i($);
          se(Pt, 21, () => t(q), (V) => V.video_id, (V, D) => {
            const G = x(() => t(yt)[t(D).video_id]);
            var it = ri(), ft = r(it), ht = r(ft), At = r(ht), Bt = i(ht), Wt = r(Bt), Rt = i(ft), Xt = r(Rt);
            {
              let L = x(() => Nr(t(G)));
              Ga(Xt, {
                get kind() {
                  return t(L);
                },
                children: (X, nr) => {
                  var Vt = k();
                  p((ae) => o(Vt, ae), [() => pt(t(G))]), c(X, Vt);
                },
                $$slots: { default: !0 }
              });
            }
            var Yt = i(Rt), Zt = r(Yt);
            {
              var te = (L) => {
                var X = ei(), nr = r(X);
                p(
                  (Vt, ae) => {
                    oe(X, "href", Vt), o(nr, ae);
                  },
                  [() => Sr(t(D)), () => a("projects.open_output")]
                ), c(L, X);
              }, ee = x(() => pt(t(G)).includes("rendered")), re = (L) => {
                var X = k("—");
                c(L, X);
              };
              H(Zt, (L) => {
                t(ee) ? L(te) : L(re, -1);
              });
            }
            p(
              (L) => {
                o(At, t(D).video_id), o(Wt, `${L ?? ""}${t(D).is_long ? " · long" : ""}`);
              },
              [() => (t(D).source_path || "").split(/[\\/]/).pop()]
            ), c(V, it);
          }), p(
            (V, D, G) => {
              o(B, V), o(Q, D), o(at, G);
            },
            [
              () => a("projects.col_video"),
              () => a("projects.col_status"),
              () => a("projects.col_output")
            ]
          ), c(l, m);
        };
        H(Ia, (l) => {
          t(q).length ? l(Oa, -1) : l(La);
        });
      }
      p(
        (l, m, $, b, v, B, rt, Q, kt, at, Pt, V, D, G, it, ft, ht, At, Bt, Wt, Rt, Xt, Yt, Zt, te, ee, re, L, X) => {
          o(tt, l), o(W, m), o(ut, $), o(It, b), o(Ht, v), o(wt, B), Lt !== (Lt = t(d).aspect_ratio) && (et.value = (et.__value = t(d).aspect_ratio) ?? "", xt(et, t(d).aspect_ratio)), o(f, `${rt ?? ""} (${t(d).head_trim_sec ?? ""}s)`), vt(h, t(d).head_trim_sec), o(y, `${Q ?? ""} (${t(d).tail_trim_sec ?? ""}s)`), vt(Ne, t(d).tail_trim_sec), o(ea, kt), o(ra, at), o(sa, Pt), o(la, V), o(ca, D), o(pa, G), o(fa, it), o(ba, ft), Ma(Jt, t(d).transform_hflip), o(xa, ht), o(ya, `${At ?? ""} (${Bt ?? ""}x)`), vt(He, t(d).transform_speed), o($a, `${Wt ?? ""} (${Rt ?? ""}%)`), vt(Xe, t(d).transform_zoom), o(ja, `${Xt ?? ""} (${Yt ?? ""})`), vt(tr, t(d).transform_brightness), o(wa, `${Zt ?? ""} (${te ?? ""})`), vt(ar, t(d).transform_contrast), o(Pa, `${ee ?? ""} (${re ?? ""})`), vt(or, t(d).transform_saturation), o(Ea, L), o(Fa, X);
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
          () => t(d).logo_path ? Tt(t(d).logo_original_filename || t(d).logo_path) : a("settings.render_layout.no_logo"),
          () => a("settings.render_layout.intro_clip"),
          () => t(d).intro_clip_path ? Tt(t(d).intro_original_filename || t(d).intro_clip_path) : a("settings.render_layout.no_clip"),
          () => a("settings.render_layout.outro_clip"),
          () => t(d).outro_clip_path ? Tt(t(d).outro_original_filename || t(d).outro_clip_path) : a("settings.render_layout.no_clip"),
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
          () => a("projects.videos_title", { count: t(q).length }),
          () => a("projects.progress_summary", {
            done: t(ce),
            failed: t(Er),
            total: t(q).length
          })
        ]
      ), F("change", et, (l) => K({ aspect_ratio: l.target.value })), F("change", h, (l) => K({ head_trim_sec: Number(l.target.value) })), F("change", Ne, (l) => K({ tail_trim_sec: Number(l.target.value) })), F("change", Jt, (l) => K({ transform_hflip: l.target.checked })), F("input", He, (l) => K({ transform_speed: Number(l.target.value) })), F("input", Xe, (l) => K({ transform_zoom: Number(l.target.value) })), F("input", tr, (l) => K({ transform_brightness: Number(l.target.value) })), F("input", ar, (l) => K({ transform_contrast: Number(l.target.value) })), F("input", or, (l) => K({ transform_saturation: Number(l.target.value) })), c(e, s);
    };
    H(Xr, (e) => {
      t(u) && e(Yr);
    });
  }
  p(
    (e, s, n, w, S, J, tt, I, W) => {
      o(Ir, e), o(Or, s), o(Rr, n), ot.disabled = !!t(u), je !== (je = t(P).tts_provider) && (ot.value = (ot.__value = t(P).tts_provider) ?? "", xt(ot, t(P).tts_provider)), o(Vr, w), st.disabled = !!t(u), o(Dr, S), Pe !== (Pe = t(P).tts_voice) && (st.value = (st.__value = t(P).tts_voice) ?? "", xt(st, t(P).tts_voice)), o(Kr, J), lt.disabled = !!t(u), o(Tr, tt), o(Qr, I), o(Gr, W), Be !== (Be = t(P).mix_mode) && (lt.value = (lt.__value = t(P).mix_mode) ?? "", xt(lt, t(P).mix_mode));
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
  ), F("change", ot, (e) => t(P).tts_provider = e.target.value), F("change", st, (e) => t(P).tts_voice = e.target.value), F("change", lt, (e) => t(P).mix_mode = e.target.value), c(ur, pe), Da();
}
qa(["change", "input"]);
const pr = Ha(si), gi = pr.mount, mi = pr.unmount;
export {
  gi as mount,
  mi as unmount
};
//# sourceMappingURL=projects.js.map
