import { d as rt, p as it, w as st, x as lt, f as Ge, i as K, g as _, l as r, t as u, j as n, a as g, b as nt, s as ot, c as j, h as t, o as A, r as k, y as dt, n as m, e as Ne, u as H, z as vt, m as ct } from "./chunks/api-vHpIWCot.js";
import { e as le, i as ne } from "./chunks/each-BE197-93.js";
import { b as Q, a as _t } from "./chunks/input-D0G7l_P3.js";
import { p as pt, B as W } from "./chunks/Button-GpBM5g0S.js";
import { S as We } from "./chunks/StatusBadge-DT3lodBA.js";
import { s as ut } from "./chunks/screen-DRq5NjFu.js";
var gt = m('<div class="error-banner" data-testid="app-settings-error"><div class="error-code">UI</div><div class="error-message"> </div></div>'), yt = m('<div class="info-banner"> </div>'), mt = m('<div class="card"><div class="empty-card"><h3> </h3></div></div>'), Xe = m('<div class="app-settings-key-display"><code class="app-settings-key-masked"> </code> <!></div>'), bt = m('<div class="stack" style="gap:8px"><div class="small-muted"> </div> <!> <div class="field-grid"><div class="field"><label> </label> <input class="input" type="password"/></div> <div class="field"><label> </label> <input class="input" type="text"/></div></div></div>'), ht = m('<div class="card"><div class="card-body stack"><div class="card-title"> </div> <div class="card-sub"> </div> <label class="checkbox-row"><input type="checkbox"/> <span> </span></label> <!> <div class="small-muted"> </div></div></div>'), ft = m("<th> </th>"), kt = m('<tr><td style="white-space:pre-line"> </td><td style="white-space:pre-line"> </td><td style="white-space:pre-line"> </td><td style="white-space:pre-line"> </td><td><input type="checkbox"/></td><td><!></td></tr>'), zt = m('<div class="small-muted"> </div>'), xt = m('<audio class="audio-preview" controls="" preload="metadata"></audio>'), $t = m('<div class="card"><div class="card-body stack"><div class="card-title"> </div> <div class="field"><label for="as-lang"> </label> <select id="as-lang" class="input"><option>Tiếng Việt</option><option>English</option></select></div></div></div> <div class="card"><div class="card-body stack"><div class="card-title"> </div> <div class="card-sub"> </div> <!> <div class="field"><label for="as-key"> </label> <input id="as-key" class="input" type="password"/></div> <div class="field"><label for="as-model"> </label> <input id="as-model" class="input" type="text"/></div> <div class="small-muted"> </div> <div class="small-muted"> </div></div></div> <div class="card"><div class="card-body stack"><div class="card-title"> </div> <div class="card-sub"> </div> <div class="toolbar"><!></div></div></div> <!> <div class="card"><div class="card-body stack"><div class="card-title"> </div> <div class="card-sub"> </div> <div class="toolbar"><input class="input voice-catalog-search" type="search"/> <!></div> <div class="small-muted"> </div> <div class="table-wrap voice-catalog-table-wrap"><table><thead><tr></tr></thead><tbody></tbody></table></div> <!> <!></div></div> <div class="toolbar" style="margin-top:8px"><!></div>', 1), wt = m('<!> <div class="screen stack" data-testid="app-settings-screen"><div class="card"><div class="card-body"><div class="card-title"> </div> <div class="card-sub"> </div></div></div> <!> <!></div>', 1);
function St(Ye, oe) {
  it(oe, !0);
  let P = pt(oe, "ctx", 7);
  const i = (a, l) => (P()?.t ?? ((s) => s))(a, l), M = () => P()?.getLang?.() ?? "vi", C = () => String(P()?.jobWorkspace || "");
  function Ze() {
    return {
      loading: !1,
      language: M(),
      hasKey: !1,
      maskedKey: "",
      keyInput: "",
      translationModel: "",
      resolvedTranslationModel: "",
      azureFallbackEnabled: !1,
      azurePrimaryHasKey: !1,
      azurePrimaryMaskedKey: "",
      azurePrimaryKeyInput: "",
      azurePrimaryRegion: "",
      azureSecondaryHasKey: !1,
      azureSecondaryMaskedKey: "",
      azureSecondaryKeyInput: "",
      azureSecondaryRegion: "",
      azureResolvedProfiles: [],
      voiceCatalog: [],
      voiceQuery: "",
      voiceBusy: "",
      voicePreviewRel: "",
      voicePreviewBust: 0,
      advancedOpen: !1,
      notice: ""
    };
  }
  let e = st(P()?.appSettingsState || Ze());
  P() && (P().appSettingsState = e);
  let U = ot("");
  function V(a) {
    Ne(U, (a instanceof Error ? a.message : String(a)) || "", !0);
  }
  function de() {
    Ne(U, "");
  }
  function ve(a) {
    e.hasKey = !!a.has_openai_key, e.maskedKey = a.openai_key_masked || "", e.keyInput = "", e.translationModel = a.openai_translation_model || "", e.resolvedTranslationModel = a.resolved_openai_translation_model || "", e.azureFallbackEnabled = !!a.azure_speech?.fallback_enabled, e.azurePrimaryHasKey = !!a.azure_speech?.primary?.has_key, e.azurePrimaryMaskedKey = a.azure_speech?.primary?.key_masked || "", e.azurePrimaryKeyInput = "", e.azurePrimaryRegion = a.azure_speech?.primary?.region || "", e.azureSecondaryHasKey = !!a.azure_speech?.secondary?.has_key, e.azureSecondaryMaskedKey = a.azure_speech?.secondary?.key_masked || "", e.azureSecondaryKeyInput = "", e.azureSecondaryRegion = a.azure_speech?.secondary?.region || "", e.azureResolvedProfiles = Array.isArray(a.azure_speech?.resolved_profiles) ? a.azure_speech.resolved_profiles : [];
  }
  async function ea() {
    e.loading = !0, e.notice = "", de();
    try {
      const [a, l] = await Promise.all([
        j("/api/get-app-settings", {}),
        j("/api/list-voices", {})
      ]);
      e.loading = !1, e.language = a.language || M(), ve(a), e.voiceCatalog = X(l.voices || []);
    } catch (a) {
      e.loading = !1, V(a);
    }
  }
  async function aa() {
    de();
    const a = {
      language: e.language,
      openai_translation_model: (e.translationModel || "").trim(),
      azure_speech: {
        fallback_enabled: !!e.azureFallbackEnabled,
        primary: { region: (e.azurePrimaryRegion || "").trim() },
        secondary: { region: (e.azureSecondaryRegion || "").trim() }
      }
    };
    e.keyInput.trim() && (a.openai_api_key = e.keyInput.trim()), e.azurePrimaryKeyInput.trim() && (a.azure_speech.primary.key = e.azurePrimaryKeyInput.trim()), e.azureSecondaryKeyInput.trim() && (a.azure_speech.secondary.key = e.azureSecondaryKeyInput.trim());
    try {
      const l = await j("/api/save-app-settings", a);
      ve(l), e.notice = i("app_settings.notice_saved");
      const s = P()?.changeLang;
      l.language && l.language !== M() && typeof s == "function" && await s(l.language);
    } catch (l) {
      V(l);
    }
  }
  async function ta() {
    e.voiceBusy = "refresh", e.notice = "";
    try {
      const a = await j("/api/voices/refresh", {});
      e.voiceBusy = "", e.voiceCatalog = X(a.voices || []), e.notice = i("app_settings.voices_refresh_done");
    } catch (a) {
      e.voiceBusy = "", V(a);
    }
  }
  async function ra(a, l) {
    e.voiceBusy = `toggle:${a.provider}:${a.voice_id}`, e.notice = "";
    try {
      const s = await j("/api/voices/toggle", { provider: a.provider, voice_id: a.voice_id, enabled: l });
      e.voiceBusy = "", e.voiceCatalog = X(s.voices || []), e.notice = i("app_settings.voices_toggle_done");
    } catch (s) {
      e.voiceBusy = "", V(s);
    }
  }
  async function ia(a) {
    if (C()) {
      e.voiceBusy = `preview:${a.provider}:${a.voice_id}`, e.notice = "";
      try {
        const l = await j("/api/tts-preview", {
          job_workspace: C(),
          tts_provider: a.provider,
          tts_voice: a.voice_id,
          text: M() === "vi" ? "Xin chào, đây là giọng đọc thử nghiệm." : "Hello, this is a voice preview."
        });
        e.voiceBusy = "", e.voicePreviewRel = l.rel_path || "", e.voicePreviewBust = Number(l.cache_bust) || Date.now(), e.notice = i("app_settings.voices_preview_done");
      } catch (l) {
        e.voiceBusy = "", V(l);
      }
    }
  }
  function X(a) {
    const l = [];
    for (const s of Array.isArray(a) ? a : [])
      !s || !String(s.voice_id || "").trim() || l.push({
        provider: String(s.provider || "edge_tts"),
        voice_id: String(s.voice_id || "").trim(),
        label: String(s.label || s.voice_id).trim(),
        locale: String(s.locale || "").trim(),
        locale_label: String(s.locale_label || "").trim(),
        locale_label_en: String(s.locale_label_en || "").trim(),
        gender: String(s.gender || "").trim().toLowerCase(),
        gender_label: String(s.gender_label || "").trim(),
        gender_label_en: String(s.gender_label_en || "").trim(),
        short_name: String(s.short_name || "").trim(),
        style_tags: Array.isArray(s.style_tags) ? s.style_tags.map((h) => String(h || "").trim()).filter(Boolean) : [],
        enabled: s.enabled !== !1
      });
    return l;
  }
  function ce(a) {
    return M() === "vi" ? a.locale_label || a.locale_label_en || a.locale || "" : a.locale_label_en || a.locale_label || a.locale || "";
  }
  function _e(a) {
    return M() === "vi" ? a.gender_label || a.gender_label_en || a.gender || "" : a.gender_label_en || a.gender_label || a.gender || "";
  }
  function pe(a) {
    return a.style_tags.length ? a.style_tags.slice(0, 2).join(", ") : "neutral";
  }
  function sa(a, l) {
    const s = String(l || "").trim().toLowerCase(), h = [...a].sort((y, B) => `${y.locale}:${y.gender}:${y.voice_id}`.localeCompare(`${B.locale}:${B.gender}:${B.voice_id}`));
    return s ? h.filter((y) => [
      y.provider,
      y.voice_id,
      y.label,
      y.locale,
      ce(y),
      _e(y),
      pe(y)
    ].join(" ").toLowerCase().includes(s)) : h;
  }
  function la(a, l) {
    if (!C()) return "";
    const s = new URLSearchParams({ workspace: C(), rel: a });
    return l && s.set("v", String(l)), `/media?${s.toString()}`;
  }
  const J = H(() => sa(e.voiceCatalog, e.voiceQuery)), na = H(() => e.voiceCatalog.filter((a) => a.enabled !== !1).length), oa = H(() => (() => {
    const a = (e.azureResolvedProfiles || []).filter(Boolean).join(", ");
    return a ? i("app_settings.azure_hint_profiles", { profiles: a }) : i("app_settings.azure_hint_env");
  })());
  lt(() => {
    ea();
  });
  var ue = wt(), ge = Ge(ue);
  {
    var da = (a) => {
      var l = gt(), s = r(t(l)), h = t(s);
      u(() => n(h, _(U))), g(a, l);
    };
    K(ge, (a) => {
      _(U) && a(da);
    });
  }
  var va = r(ge, 2), ye = t(va), ca = t(ye), me = t(ca), _a = t(me), pa = r(me, 2), ua = t(pa), be = r(ye, 2);
  {
    var ga = (a) => {
      var l = yt(), s = t(l);
      u(() => n(s, e.notice)), g(a, l);
    };
    K(be, (a) => {
      e.notice && a(ga);
    });
  }
  var ya = r(be, 2);
  {
    var ma = (a) => {
      var l = mt(), s = t(l), h = t(s), y = t(h);
      u((B) => n(y, B), [() => i("common.loading")]), g(a, l);
    }, ba = (a) => {
      var l = $t(), s = Ge(l), h = t(s), y = t(h), B = t(y), ha = r(y, 2), he = t(ha), fa = t(he), fe = r(he, 2), Y = t(fe);
      Y.value = Y.__value = "vi";
      var ke = r(Y);
      ke.value = ke.__value = "en";
      var ze = r(s, 2), ka = t(ze), xe = t(ka), za = t(xe), $e = r(xe, 2), xa = t($e), we = r($e, 2);
      {
        var $a = (o) => {
          var d = Xe(), v = t(d), p = t(v), b = r(v, 2);
          We(b, {
            kind: "completed",
            children: (z, L) => {
              var f = A();
              u((w) => n(f, w), [() => i("app_settings.key_active")]), g(z, f);
            },
            $$slots: { default: !0 }
          }), u(() => n(p, e.maskedKey || "****")), g(o, d);
        };
        K(we, (o) => {
          e.hasKey && o($a);
        });
      }
      var Se = r(we, 2), Ke = t(Se), wa = t(Ke), Pe = r(Ke, 2), Be = r(Se, 2), Ie = t(Be), Sa = t(Ie), Re = r(Ie, 2), Me = r(Be, 2), Ka = t(Me), Pa = r(Me, 2), Ba = t(Pa), Ce = r(ze, 2), Ia = t(Ce), Le = t(Ia), Ra = t(Le), Ee = r(Le, 2), Ma = t(Ee), Ca = r(Ee, 2), La = t(Ca);
      W(La, {
        variant: "secondary",
        onclick: () => e.advancedOpen = !e.advancedOpen,
        children: (o, d) => {
          var v = A();
          u((p) => n(v, p), [
            () => e.advancedOpen ? i("app_settings.advanced_hide") : i("app_settings.advanced_show")
          ]), g(o, v);
        },
        $$slots: { default: !0 }
      });
      var je = r(Ce, 2);
      {
        var Ea = (o) => {
          var d = ht(), v = t(d), p = t(v), b = t(p), z = r(p, 2), L = t(z), f = r(z, 2), w = t(f), E = r(w, 2), F = t(E), I = r(f, 2);
          le(
            I,
            16,
            () => [
              { key: "Primary", titleKey: "app_settings.azure_primary_title" },
              {
                key: "Secondary",
                titleKey: "app_settings.azure_secondary_title"
              }
            ],
            ne,
            (x, c) => {
              var S = bt(), O = t(S), D = t(O), q = r(O, 2);
              {
                var Xa = ($) => {
                  var G = Xe(), N = t(G), ie = t(N), se = r(N, 2);
                  We(se, {
                    kind: "completed",
                    children: (at, Kt) => {
                      var qe = A();
                      u((tt) => n(qe, tt), [() => i("app_settings.key_active")]), g(at, qe);
                    },
                    $$slots: { default: !0 }
                  }), u(() => n(ie, e[`azure${c.key}MaskedKey`] || "****")), g($, G);
                };
                K(q, ($) => {
                  e[`azure${c.key}HasKey`] && $(Xa);
                });
              }
              var Ja = r(q, 2), De = t(Ja), ee = t(De), Ya = t(ee), ae = r(ee, 2), Za = r(De, 2), te = t(Za), et = t(te), re = r(te, 2);
              u(
                ($, G, N, ie, se) => {
                  n(D, $), k(ee, "for", `as-az-${c.key ?? ""}-key`), n(Ya, G), k(ae, "id", `as-az-${c.key ?? ""}-key`), k(ae, "placeholder", N), k(te, "for", `as-az-${c.key ?? ""}-region`), n(et, ie), k(re, "id", `as-az-${c.key ?? ""}-region`), k(re, "placeholder", se);
                },
                [
                  () => i(c.titleKey),
                  () => i("app_settings.azure_key_label"),
                  () => e[`azure${c.key}MaskedKey`] || i("app_settings.azure_key_placeholder"),
                  () => i("app_settings.azure_region_label"),
                  () => i("app_settings.azure_region_placeholder")
                ]
              ), Q(ae, () => e[`azure${c.key}KeyInput`], ($) => e[`azure${c.key}KeyInput`] = $), Q(re, () => e[`azure${c.key}Region`], ($) => e[`azure${c.key}Region`] = $), g(x, S);
            }
          );
          var R = r(I, 2), T = t(R);
          u(
            (x, c, S) => {
              n(b, x), n(L, c), n(F, S), n(T, _(oa));
            },
            [
              () => i("app_settings.azure_title"),
              () => i("app_settings.azure_sub"),
              () => i("app_settings.azure_fallback")
            ]
          ), _t(w, () => e.azureFallbackEnabled, (x) => e.azureFallbackEnabled = x), g(o, d);
        };
        K(je, (o) => {
          e.advancedOpen && o(Ea);
        });
      }
      var Ae = r(je, 2), ja = t(Ae), He = t(ja), Aa = t(He), Ve = r(He, 2), Ha = t(Ve), Fe = r(Ve, 2), Z = t(Fe), Va = r(Z, 2);
      {
        let o = H(() => !!e.voiceBusy);
        W(Va, {
          variant: "secondary",
          get disabled() {
            return _(o);
          },
          onclick: ta,
          children: (d, v) => {
            var p = A();
            u((b) => n(p, b), [
              () => e.voiceBusy === "refresh" ? i("app_settings.voices_refreshing") : i("app_settings.voices_refresh")
            ]), g(d, p);
          },
          $$slots: { default: !0 }
        });
      }
      var Te = r(Fe, 2), Fa = t(Te), Oe = r(Te, 2), Ta = t(Oe), Qe = t(Ta), Oa = t(Qe);
      le(
        Oa,
        20,
        () => [
          "voices_col_locale",
          "voices_col_voice",
          "voices_col_gender",
          "voices_col_style",
          "voices_col_enabled",
          "voices_col_preview"
        ],
        ne,
        (o, d) => {
          var v = ft(), p = t(v);
          u((b) => n(p, b), [() => i(`app_settings.${d}`)]), g(o, v);
        }
      );
      var Qa = r(Qe);
      le(Qa, 21, () => _(J).slice(0, 160), ne, (o, d) => {
        var v = kt(), p = t(v), b = t(p), z = r(p), L = t(z), f = r(z), w = t(f), E = r(f), F = t(E), I = r(E), R = t(I), T = r(I), x = t(T);
        {
          let c = H(() => !!e.voiceBusy || !C());
          W(x, {
            variant: "secondary",
            class: "voice-preview-btn",
            get disabled() {
              return _(c);
            },
            onclick: () => ia(_(d)),
            children: (S, O) => {
              var D = A();
              u((q) => n(D, q), [
                () => e.voiceBusy === `preview:${_(d).provider}:${_(d).voice_id}` ? i("app_settings.voices_previewing") : i("app_settings.voices_preview")
              ]), g(S, D);
            },
            $$slots: { default: !0 }
          });
        }
        u(
          (c, S, O) => {
            n(b, c), n(L, `${(_(d).short_name || _(d).label || _(d).voice_id) ?? ""}
${_(d).voice_id ?? ""}`), n(w, S), n(F, O), vt(R, _(d).enabled !== !1), R.disabled = !!e.voiceBusy;
          },
          [
            () => ce(_(d)),
            () => _e(_(d)),
            () => pe(_(d))
          ]
        ), ct("change", R, (c) => ra(_(d), c.currentTarget.checked)), g(o, v);
      });
      var Ue = r(Oe, 2);
      {
        var Ua = (o) => {
          var d = zt(), v = t(d);
          u((p) => n(v, p), [() => i("app_settings.voices_limited")]), g(o, d);
        };
        K(Ue, (o) => {
          _(J).length > 160 && o(Ua);
        });
      }
      var Da = r(Ue, 2);
      {
        var qa = (o) => {
          var d = xt();
          u((v) => k(d, "src", v), [
            () => la(e.voicePreviewRel, e.voicePreviewBust)
          ]), g(o, d);
        }, Ga = H(() => e.voicePreviewRel && C());
        K(Da, (o) => {
          _(Ga) && o(qa);
        });
      }
      var Na = r(Ae, 2), Wa = t(Na);
      W(Wa, {
        variant: "primary",
        onclick: aa,
        children: (o, d) => {
          var v = A();
          u((p) => n(v, p), [() => i("app_settings.save")]), g(o, v);
        },
        $$slots: { default: !0 }
      }), u(
        (o, d, v, p, b, z, L, f, w, E, F, I, R, T, x, c) => {
          n(B, o), n(fa, d), n(za, v), n(xa, p), n(wa, b), k(Pe, "placeholder", z), n(Sa, L), k(Re, "placeholder", f), n(Ka, w), n(Ba, E), n(Ra, F), n(Ma, I), n(Aa, R), n(Ha, T), k(Z, "placeholder", x), n(Fa, c);
        },
        [
          () => i("app_settings.language_title"),
          () => i("app_settings.language_label"),
          () => i("app_settings.api_key_title"),
          () => i("app_settings.api_key_sub"),
          () => i("app_settings.key_label"),
          () => e.maskedKey || i("app_settings.key_placeholder"),
          () => i("app_settings.translation_model_label"),
          () => e.resolvedTranslationModel || i("app_settings.translation_model_placeholder"),
          () => e.hasKey ? i("app_settings.key_edit_hint") : i("app_settings.key_hint"),
          () => i("app_settings.translation_model_hint", {
            model: e.resolvedTranslationModel || i("app_settings.translation_model_placeholder")
          }),
          () => i("app_settings.advanced_title"),
          () => i("app_settings.advanced_sub"),
          () => i("app_settings.voices_title"),
          () => i("app_settings.voices_sub"),
          () => i("app_settings.voices_search"),
          () => i("app_settings.voices_count", { count: _(J).length, enabled: _(na) })
        ]
      ), dt(fe, () => e.language, (o) => e.language = o), Q(Pe, () => e.keyInput, (o) => e.keyInput = o), Q(Re, () => e.translationModel, (o) => e.translationModel = o), Q(Z, () => e.voiceQuery, (o) => e.voiceQuery = o), g(a, l);
    };
    K(ya, (a) => {
      e.loading ? a(ma) : a(ba, -1);
    });
  }
  u(
    (a, l) => {
      n(_a, a), n(ua, l);
    },
    [() => i("app_settings.title"), () => i("app_settings.sub")]
  ), g(Ye, ue), nt();
}
rt(["change"]);
const Je = ut(St), Lt = Je.mount, Et = Je.unmount;
export {
  Lt as mount,
  Et as unmount
};
//# sourceMappingURL=app_settings.js.map
