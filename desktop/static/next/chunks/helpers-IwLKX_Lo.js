const L = [
  ["left", "L"],
  ["center", "C"],
  ["right", "R"]
], P = "vlt.voicePreviewText", E = "Xin chào, đây là giọng đọc thử nghiệm.", h = {
  "vi-VN": "vi-VN-HoaiMyNeural",
  "en-US": "en-US-JennyNeural",
  "en-GB": "en-GB-SoniaNeural",
  "zh-CN": "zh-CN-XiaoxiaoNeural",
  "ja-JP": "ja-JP-NanamiNeural",
  "ko-KR": "ko-KR-SunHiNeural"
}, T = {
  bottom_band: { x: 0, y: 0.78, w: 1, h: 0.22 }
};
function _(t) {
  const r = Number(t);
  return Number.isFinite(r) ? Math.min(600, Math.max(0, Math.round(r * 10) / 10)) : 0;
}
function s(t, r, e, n) {
  const o = Number(t);
  return Number.isFinite(o) ? Math.min(e, Math.max(r, o)) : n;
}
const b = ["top-left", "top-right", "bottom-left", "bottom-right"];
function p(t) {
  const r = Number(t);
  return Number.isFinite(r) ? Math.min(1, Math.max(0.02, r)) : 0.15;
}
function S(t) {
  const r = Number(t);
  return Number.isFinite(r) ? Math.min(1, Math.max(0, r)) : 1;
}
function N(t) {
  const r = Number(t);
  return Number.isFinite(r) ? Math.min(0.5, Math.max(0, r)) : 0.03;
}
function C(t) {
  const r = /* @__PURE__ */ new Set(), e = [];
  for (const n of Array.isArray(t) ? t : []) {
    if (!n || typeof n.family != "string" || !n.family.trim()) continue;
    const o = n.family.trim(), a = o.toLowerCase();
    r.has(a) || (r.add(a), e.push({ family: o, file: String(n.file || "") }));
  }
  return e.sort((n, o) => n.family.localeCompare(o.family));
}
function R(t) {
  const r = [];
  for (const e of Array.isArray(t) ? t : []) {
    if (!e || typeof e.voice_id != "string" || !e.voice_id.trim()) continue;
    const n = Array.isArray(e.style_tags) ? e.style_tags.map((o) => String(o || "").trim()).filter(Boolean) : [];
    r.push({
      provider: String(e.provider || "edge_tts"),
      voice_id: e.voice_id.trim(),
      label: String(e.label || e.voice_id).trim(),
      locale: String(e.locale || "").trim(),
      locale_label: String(e.locale_label || "").trim(),
      locale_label_en: String(e.locale_label_en || "").trim(),
      gender: String(e.gender || "").trim().toLowerCase(),
      gender_label: String(e.gender_label || "").trim(),
      gender_label_en: String(e.gender_label_en || "").trim(),
      short_name: String(e.short_name || "").trim(),
      style_tags: n,
      enabled: e.enabled !== !1
    });
  }
  return r;
}
function v(t, r) {
  const e = t.filter((n) => n.provider === r && n.enabled !== !1);
  return e.length ? e : t.filter((n) => n.provider === r);
}
function d(t) {
  const r = String(t || "").trim();
  if (!r) return "vi";
  const e = r.toLowerCase();
  return e.startsWith("english") ? "en" : e.startsWith("vietnam") ? "vi" : e.startsWith("chinese") ? "zh" : e.startsWith("japanese") ? "ja" : e.startsWith("korean") ? "ko" : e.split(/[-_\s]/, 1)[0] || "vi";
}
function M(t) {
  const r = d(t);
  return r === "en" ? "en-US" : r === "zh" ? "zh-CN" : r === "ja" ? "ja-JP" : r === "ko" ? "ko-KR" : r === "vi" ? "vi-VN" : r.includes("-") ? r : "";
}
function y(t, r) {
  const e = d(r);
  return !!t && !!e && t.toLowerCase().startsWith(`${e}-`);
}
function l(t, r) {
  const e = { female: 0, male: 1 }, n = e[t.gender] ?? 9, o = e[r.gender] ?? 9;
  return n !== o ? n - o : (t.short_name || t.label || t.voice_id).localeCompare(r.short_name || r.label || r.voice_id);
}
function V(t, r, e, n = "vi") {
  const o = v(t, r);
  if (o.some((i) => i.voice_id === e)) return e;
  const a = M(n), u = h[a], m = u ? o.find((i) => i.voice_id === u && i.enabled !== !1) : null;
  if (m) return m.voice_id;
  const f = o.filter((i) => i.locale === a || y(i.locale, n)).sort(l)[0];
  return f ? f.voice_id : o.filter((i) => i.gender === "female").sort(l)[0]?.voice_id || [...o].sort(l)[0]?.voice_id || e || "vi-VN-HoaiMyNeural";
}
function $(t, r, e) {
  return t.filter((n) => !(r && n.locale !== r || e && n.gender !== e));
}
function k(t, r, e) {
  return r === "vi" ? t.locale_label || t.locale_label_en || t.locale || e : t.locale_label_en || t.locale_label || t.locale || e;
}
function x(t, r) {
  return r === "vi" ? t.gender_label || t.gender_label_en || t.gender || "" : t.gender_label_en || t.gender_label || t.gender || "";
}
function I(t, r) {
  const e = t.short_name || t.label || t.voice_id, n = x(t, r), o = t.style_tags.length ? t.style_tags[0] : "", a = [n, o].filter(Boolean).join(", ");
  return a ? `${e} - ${a}` : e;
}
function O(t) {
  if (!t || typeof t != "object") return null;
  const r = t, e = {};
  for (const n of ["x", "y", "w", "h"]) {
    const o = Number(r[n]);
    if (!Number.isFinite(o) || o < 0 || o > 1) return null;
    e[n] = o;
  }
  return e.w <= 0 || e.h <= 0 || e.x + e.w > 1.0001 || e.y + e.h > 1.0001 ? null : e;
}
function c(t) {
  const r = Number(t);
  return Number.isFinite(r) ? Math.max(0.5, Math.min(2, Math.round(r * 20) / 20)) : 1;
}
function j(t) {
  return Math.max(-50, Math.min(50, Math.round((c(t) - 1) * 100)));
}
function A(t) {
  const r = Number(t);
  return Number.isFinite(r) ? c(1 + r / 100) : 1;
}
function B(t) {
  const r = Number(t);
  return Number.isFinite(r) ? Math.max(-30, Math.min(0, Math.round(r * 100) / 100)) : -15;
}
function F(t) {
  const r = Number(t);
  return Number.isFinite(r) ? Math.max(-40, Math.min(0, Math.round(r * 100) / 100)) : -20;
}
function g(t) {
  const r = Number(t);
  return Number.isFinite(r) ? Math.max(0, Math.min(1e4, Math.round(r))) : 0;
}
function w(t) {
  if (!t || typeof t != "object") return null;
  const r = t, e = String(r.normalized_path || "").trim(), n = String(r.original_path || "").trim();
  return !e && !n ? null : {
    original_path: n,
    normalized_path: e,
    original_filename: String(r.original_filename || "").trim(),
    duration_ms: Math.max(0, Math.round(Number(r.duration_ms) || 0)),
    volume_db: F(r.volume_db),
    loop: r.loop !== !1,
    fade_in_ms: g(r.fade_in_ms ?? 500),
    fade_out_ms: g(r.fade_out_ms ?? 1e3)
  };
}
function D(t) {
  const r = t && typeof t == "object" ? t : {}, e = String(r.aspect_ratio || "16:9").trim(), n = String(r.logo_position || "top-right").trim();
  return {
    aspect_ratio: ["source", "16:9", "9:16", "1:1"].includes(e) ? e : "16:9",
    background_path: String(r.background_path || "").trim(),
    background_original_filename: String(r.background_original_filename || "").trim(),
    logo_path: String(r.logo_path || "").trim(),
    logo_original_filename: String(r.logo_original_filename || "").trim(),
    logo_position: b.includes(n) ? n : "top-right",
    logo_scale: p(r.logo_scale ?? 0.15),
    logo_opacity: S(r.logo_opacity ?? 1),
    logo_margin: N(r.logo_margin ?? 0.03),
    intro_clip_path: String(r.intro_clip_path || "").trim(),
    intro_original_filename: String(r.intro_original_filename || "").trim(),
    outro_clip_path: String(r.outro_clip_path || "").trim(),
    outro_original_filename: String(r.outro_original_filename || "").trim(),
    head_trim_sec: _(r.head_trim_sec ?? 0),
    tail_trim_sec: _(r.tail_trim_sec ?? 0),
    transform_speed: s(r.transform_speed ?? 1, 0.5, 2, 1),
    transform_hflip: !!r.transform_hflip,
    transform_zoom: s(r.transform_zoom ?? 1, 1, 1.5, 1),
    transform_brightness: s(r.transform_brightness ?? 0, -0.3, 0.3, 0),
    transform_contrast: s(r.transform_contrast ?? 1, 0.5, 1.5, 1),
    transform_saturation: s(r.transform_saturation ?? 1, 0, 2, 1)
  };
}
function W(t, r) {
  Math.abs(r.transform_speed - 1) > 1e-6 && (t.transform_speed = r.transform_speed), r.transform_hflip && (t.transform_hflip = !0), Math.abs(r.transform_zoom - 1) > 1e-6 && (t.transform_zoom = r.transform_zoom), Math.abs(r.transform_brightness) > 1e-6 && (t.transform_brightness = r.transform_brightness), Math.abs(r.transform_contrast - 1) > 1e-6 && (t.transform_contrast = r.transform_contrast), Math.abs(r.transform_saturation - 1) > 1e-6 && (t.transform_saturation = r.transform_saturation);
}
function U(t) {
  const r = Number(t), e = Number.isFinite(r) ? Math.round(r * 10) / 10 : 0;
  return `${e > 0 ? "+" : ""}${e} dB`;
}
function G(t) {
  const r = Number(t) || 0;
  return `${r > 0 ? "+" : ""}${r}%`;
}
function H(t) {
  return `${c(t).toFixed(2).replace(/0$/, "").replace(/\.$/, "")}x`;
}
function J(t) {
  const r = Math.max(0, Math.round((Number(t) || 0) / 1e3)), e = Math.floor(r / 60), n = String(r % 60).padStart(2, "0");
  return `${e}:${n}`;
}
function K(t) {
  return t === "left" ? "left" : t === "right" ? "right" : "center";
}
function X(t) {
  const r = String(t || "").trim();
  return r ? `"${r}", "Segoe UI", sans-serif` : '"Segoe UI", sans-serif';
}
function Y(t) {
  const r = String(t || "").trim();
  return /^#(?:[0-9a-f]{6}|[0-9a-f]{8})$/i.test(r) ? r.toUpperCase() : "#000000";
}
export {
  L as A,
  g as B,
  E as D,
  T as R,
  P as V,
  W as a,
  C as b,
  R as c,
  d,
  w as e,
  B as f,
  c as g,
  V as h,
  O as i,
  K as j,
  X as k,
  Y as l,
  H as m,
  D as n,
  G as o,
  U as p,
  k as q,
  A as r,
  M as s,
  l as t,
  j as u,
  I as v,
  v as w,
  $ as x,
  J as y,
  F as z
};
//# sourceMappingURL=helpers-IwLKX_Lo.js.map
