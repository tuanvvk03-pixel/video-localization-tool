// Minimal i18n loader — fetches /i18n/<lang>.json, exposes t() with {var}
// interpolation, applies to [data-i18n*] attributes across the DOM.
//
// Usage:
//   import { loadLang, t, applyDom, getLang, setLang } from "./i18n/i18n.js";
//   await loadLang(getLang());
//   // ... build DOM with data-i18n="key" ...
//   applyDom();

const LS_KEY = "lang";
const SUPPORTED = ["vi", "en"];
const DEFAULT = "vi";

let dict = {};
let currentLang = readStoredLang();
const listeners = new Set();

function readStoredLang() {
  try {
    const stored = localStorage.getItem(LS_KEY);
    if (stored && SUPPORTED.includes(stored)) return stored;
  } catch (_) {
    /* localStorage may be blocked */
  }
  return DEFAULT;
}

export function getLang() {
  return currentLang;
}

export function setLang(lang) {
  if (!SUPPORTED.includes(lang)) return currentLang;
  try {
    localStorage.setItem(LS_KEY, lang);
  } catch (_) {
    /* ignore */
  }
  currentLang = lang;
  return currentLang;
}

export function onLangChange(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export async function loadLang(lang) {
  const target = SUPPORTED.includes(lang) ? lang : DEFAULT;
  const res = await fetch(`/i18n/${target}.json`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch /i18n/${target}.json: HTTP ${res.status}`);
  dict = await res.json();
  currentLang = target;
  document.documentElement.setAttribute("lang", target);
  applyDom();
  for (const fn of listeners) {
    try {
      fn(target);
    } catch (e) {
      console.error("i18n listener failed", e);
    }
  }
  return target;
}

function lookup(key) {
  if (!key) return undefined;
  const parts = String(key).split(".");
  let cursor = dict;
  for (const p of parts) {
    if (cursor && typeof cursor === "object" && p in cursor) {
      cursor = cursor[p];
    } else {
      return undefined;
    }
  }
  return cursor;
}

export function t(key, vars) {
  const raw = lookup(key);
  if (raw == null) return key;
  if (typeof raw !== "string") return String(raw);
  if (!vars) return raw;
  return raw.replace(/\{(\w+)\}/g, (_, name) =>
    Object.prototype.hasOwnProperty.call(vars, name) ? String(vars[name]) : `{${name}}`,
  );
}

export function applyDom(root) {
  const scope = root || document;
  scope.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  scope.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });
  scope.querySelectorAll("[data-i18n-title]").forEach((el) => {
    el.title = t(el.dataset.i18nTitle);
  });
  scope.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
    el.setAttribute("aria-label", t(el.dataset.i18nAriaLabel));
  });
}
