const L = [
  ["left", "L"],
  ["center", "C"],
  ["right", "R"]
], E = "vlt.voicePreviewText", P = "Xin chào, đây là giọng đọc thử nghiệm.", d = {
  "vi-VN": "vi-VN-HoaiMyNeural",
  "en-US": "en-US-JennyNeural",
  "en-GB": "en-GB-SoniaNeural",
  "zh-CN": "zh-CN-XiaoxiaoNeural",
  "ja-JP": "ja-JP-NanamiNeural",
  "ko-KR": "ko-KR-SunHiNeural"
}, T = {
  bottom_band: { x: 0, y: 0.78, w: 1, h: 0.22 }
};
function f(t) {
  const e = Number(t);
  return Number.isFinite(e) ? Math.min(600, Math.max(0, Math.round(e * 10) / 10)) : 0;
}
const h = ["top-left", "top-right", "bottom-left", "bottom-right"];
function p(t) {
  const e = Number(t);
  return Number.isFinite(e) ? Math.min(1, Math.max(0.02, e)) : 0.15;
}
function b(t) {
  const e = Number(t);
  return Number.isFinite(e) ? Math.min(1, Math.max(0, e)) : 1;
}
function S(t) {
  const e = Number(t);
  return Number.isFinite(e) ? Math.min(0.5, Math.max(0, e)) : 0.03;
}
function z(t) {
  const e = /* @__PURE__ */ new Set(), r = [];
  for (const n of Array.isArray(t) ? t : []) {
    if (!n || typeof n.family != "string" || !n.family.trim()) continue;
    const i = n.family.trim(), a = i.toLowerCase();
    e.has(a) || (e.add(a), r.push({ family: i, file: String(n.file || "") }));
  }
  return r.sort((n, i) => n.family.localeCompare(i.family));
}
function C(t) {
  const e = [];
  for (const r of Array.isArray(t) ? t : []) {
    if (!r || typeof r.voice_id != "string" || !r.voice_id.trim()) continue;
    const n = Array.isArray(r.style_tags) ? r.style_tags.map((i) => String(i || "").trim()).filter(Boolean) : [];
    e.push({
      provider: String(r.provider || "edge_tts"),
      voice_id: r.voice_id.trim(),
      label: String(r.label || r.voice_id).trim(),
      locale: String(r.locale || "").trim(),
      locale_label: String(r.locale_label || "").trim(),
      locale_label_en: String(r.locale_label_en || "").trim(),
      gender: String(r.gender || "").trim().toLowerCase(),
      gender_label: String(r.gender_label || "").trim(),
      gender_label_en: String(r.gender_label_en || "").trim(),
      short_name: String(r.short_name || "").trim(),
      style_tags: n,
      enabled: r.enabled !== !1
    });
  }
  return e;
}
function N(t, e) {
  const r = t.filter((n) => n.provider === e && n.enabled !== !1);
  return r.length ? r : t.filter((n) => n.provider === e);
}
function g(t) {
  const e = String(t || "").trim();
  if (!e) return "vi";
  const r = e.toLowerCase();
  return r.startsWith("english") ? "en" : r.startsWith("vietnam") ? "vi" : r.startsWith("chinese") ? "zh" : r.startsWith("japanese") ? "ja" : r.startsWith("korean") ? "ko" : r.split(/[-_\s]/, 1)[0] || "vi";
}
function v(t) {
  const e = g(t);
  return e === "en" ? "en-US" : e === "zh" ? "zh-CN" : e === "ja" ? "ja-JP" : e === "ko" ? "ko-KR" : e === "vi" ? "vi-VN" : e.includes("-") ? e : "";
}
function y(t, e) {
  const r = g(e);
  return !!t && !!r && t.toLowerCase().startsWith(`${r}-`);
}
function l(t, e) {
  const r = { female: 0, male: 1 }, n = r[t.gender] ?? 9, i = r[e.gender] ?? 9;
  return n !== i ? n - i : (t.short_name || t.label || t.voice_id).localeCompare(e.short_name || e.label || e.voice_id);
}
function R(t, e, r, n = "vi") {
  const i = N(t, e);
  if (i.some((o) => o.voice_id === r)) return r;
  const a = v(n), c = d[a], u = c ? i.find((o) => o.voice_id === c && o.enabled !== !1) : null;
  if (u) return u.voice_id;
  const m = i.filter((o) => o.locale === a || y(o.locale, n)).sort(l)[0];
  return m ? m.voice_id : i.filter((o) => o.gender === "female").sort(l)[0]?.voice_id || [...i].sort(l)[0]?.voice_id || r || "vi-VN-HoaiMyNeural";
}
function V(t, e, r) {
  return t.filter((n) => !(e && n.locale !== e || r && n.gender !== r));
}
function $(t, e, r) {
  return e === "vi" ? t.locale_label || t.locale_label_en || t.locale || r : t.locale_label_en || t.locale_label || t.locale || r;
}
function M(t, e) {
  return e === "vi" ? t.gender_label || t.gender_label_en || t.gender || "" : t.gender_label_en || t.gender_label || t.gender || "";
}
function k(t, e) {
  const r = t.short_name || t.label || t.voice_id, n = M(t, e), i = t.style_tags.length ? t.style_tags[0] : "", a = [n, i].filter(Boolean).join(", ");
  return a ? `${r} - ${a}` : r;
}
function I(t) {
  if (!t || typeof t != "object") return null;
  const e = t, r = {};
  for (const n of ["x", "y", "w", "h"]) {
    const i = Number(e[n]);
    if (!Number.isFinite(i) || i < 0 || i > 1) return null;
    r[n] = i;
  }
  return r.w <= 0 || r.h <= 0 || r.x + r.w > 1.0001 || r.y + r.h > 1.0001 ? null : r;
}
function s(t) {
  const e = Number(t);
  return Number.isFinite(e) ? Math.max(0.5, Math.min(2, Math.round(e * 20) / 20)) : 1;
}
function O(t) {
  return Math.max(-50, Math.min(50, Math.round((s(t) - 1) * 100)));
}
function j(t) {
  const e = Number(t);
  return Number.isFinite(e) ? s(1 + e / 100) : 1;
}
function A(t) {
  const e = Number(t);
  return Number.isFinite(e) ? Math.max(-30, Math.min(0, Math.round(e * 100) / 100)) : -15;
}
function x(t) {
  const e = Number(t);
  return Number.isFinite(e) ? Math.max(-40, Math.min(0, Math.round(e * 100) / 100)) : -20;
}
function _(t) {
  const e = Number(t);
  return Number.isFinite(e) ? Math.max(0, Math.min(1e4, Math.round(e))) : 0;
}
function B(t) {
  if (!t || typeof t != "object") return null;
  const e = t, r = String(e.normalized_path || "").trim(), n = String(e.original_path || "").trim();
  return !r && !n ? null : {
    original_path: n,
    normalized_path: r,
    original_filename: String(e.original_filename || "").trim(),
    duration_ms: Math.max(0, Math.round(Number(e.duration_ms) || 0)),
    volume_db: x(e.volume_db),
    loop: e.loop !== !1,
    fade_in_ms: _(e.fade_in_ms ?? 500),
    fade_out_ms: _(e.fade_out_ms ?? 1e3)
  };
}
function w(t) {
  const e = t && typeof t == "object" ? t : {}, r = String(e.aspect_ratio || "16:9").trim(), n = String(e.logo_position || "top-right").trim();
  return {
    aspect_ratio: r === "9:16" ? "9:16" : "16:9",
    background_path: String(e.background_path || "").trim(),
    background_original_filename: String(e.background_original_filename || "").trim(),
    logo_path: String(e.logo_path || "").trim(),
    logo_original_filename: String(e.logo_original_filename || "").trim(),
    logo_position: h.includes(n) ? n : "top-right",
    logo_scale: p(e.logo_scale ?? 0.15),
    logo_opacity: b(e.logo_opacity ?? 1),
    logo_margin: S(e.logo_margin ?? 0.03),
    intro_clip_path: String(e.intro_clip_path || "").trim(),
    intro_original_filename: String(e.intro_original_filename || "").trim(),
    outro_clip_path: String(e.outro_clip_path || "").trim(),
    outro_original_filename: String(e.outro_original_filename || "").trim(),
    head_trim_sec: f(e.head_trim_sec ?? 0),
    tail_trim_sec: f(e.tail_trim_sec ?? 0)
  };
}
function D(t) {
  const e = Number(t), r = Number.isFinite(e) ? Math.round(e * 10) / 10 : 0;
  return `${r > 0 ? "+" : ""}${r} dB`;
}
function W(t) {
  const e = Number(t) || 0;
  return `${e > 0 ? "+" : ""}${e}%`;
}
function U(t) {
  return `${s(t).toFixed(2).replace(/0$/, "").replace(/\.$/, "")}x`;
}
function G(t) {
  const e = Math.max(0, Math.round((Number(t) || 0) / 1e3)), r = Math.floor(e / 60), n = String(e % 60).padStart(2, "0");
  return `${r}:${n}`;
}
function H(t) {
  return t === "left" ? "left" : t === "right" ? "right" : "center";
}
function J(t) {
  const e = String(t || "").trim();
  return e ? `"${e}", "Segoe UI", sans-serif` : '"Segoe UI", sans-serif';
}
function K(t) {
  const e = String(t || "").trim();
  return /^#(?:[0-9a-f]{6}|[0-9a-f]{8})$/i.test(e) ? e.toUpperCase() : "#000000";
}
export {
  L as A,
  P as D,
  T as R,
  E as V,
  z as a,
  C as b,
  g as c,
  B as d,
  A as e,
  s as f,
  R as g,
  I as h,
  H as i,
  J as j,
  K as k,
  U as l,
  W as m,
  w as n,
  D as o,
  $ as p,
  v as q,
  j as r,
  l as s,
  O as t,
  N as u,
  k as v,
  V as w,
  G as x,
  x as y,
  _ as z
};
//# sourceMappingURL=helpers-BtNcAVZn.js.map
