import { D as C, E as q, d as P, p as S, x as W, l, h as r, i as z, t as h, g as n, j as u, r as E, m as F, a as f, b as N, s as b, e as d, c as R, n as x } from "./chunks/api-vHpIWCot.js";
import { s as T } from "./chunks/screen-DRq5NjFu.js";
function $(i, s) {
  C(() => {
    var e = i.getRootNode(), t = (
      /** @type {ShadowRoot} */
      e.host ? (
        /** @type {ShadowRoot} */
        e
      ) : (
        /** @type {Document} */
        e.head ?? /** @type {Document} */
        e.ownerDocument.head
      )
    );
    if (!t.querySelector("#" + s.hash)) {
      const o = q("style");
      o.id = s.hash, o.textContent = s.code, t.appendChild(o);
    }
  });
}
var A = x('<p class="muted svelte-1ha78o2"> </p>'), B = x('<section class="next-demo svelte-1ha78o2"><h2>Svelte foundation — live</h2> <p class="muted svelte-1ha78o2">This screen is compiled from <code>frontend/src/screens/Demo.svelte</code> and mounted by the legacy router via the <code>mount/unmount</code> bridge.</p> <div class="row svelte-1ha78o2"><button> </button> <span class="badge svelte-1ha78o2"> </span></div> <!></section>');
const G = {
  hash: "svelte-1ha78o2",
  code: '.next-demo.svelte-1ha78o2 {padding:16px;font-family:system-ui, sans-serif;}.muted.svelte-1ha78o2 {color:#888;font-size:0.9em;}.row.svelte-1ha78o2 {display:flex;gap:12px;align-items:center;margin:12px 0;}.badge.svelte-1ha78o2 {padding:2px 8px;border-radius:6px;background:#eee;}.badge[data-state="ok"].svelte-1ha78o2 {background:#d6f5d6;}.badge[data-state="error"].svelte-1ha78o2 {background:#f5d6d6;}.badge[data-state="loading"].svelte-1ha78o2 {background:#f5efd6;}'
};
function H(i, s) {
  S(s, !0), $(i, G);
  let e = b("idle"), t = b("");
  async function o() {
    d(e, "loading"), d(t, "");
    try {
      const a = await R("/api/ping", {});
      d(e, "ok"), d(t, a?.status ? `server: ${a.status}` : "pong", !0);
    } catch (a) {
      d(e, "error"), d(t, a?.message || "request failed", !0);
    }
  }
  W(() => {
    o();
  });
  var p = B(), v = l(r(p), 4), c = r(v), y = r(c), g = l(c, 2), _ = r(g), w = l(v, 2);
  {
    var D = (a) => {
      var m = A(), j = r(m);
      h(() => u(j, `workspace: ${s.ctx.jobWorkspace ?? ""}`)), f(a, m);
    };
    z(w, (a) => {
      s.ctx?.jobWorkspace && a(D);
    });
  }
  h(() => {
    c.disabled = n(e) === "loading", u(y, n(e) === "loading" ? "Pinging…" : "Ping backend"), E(g, "data-state", n(e)), u(_, `${n(e) ?? ""}${n(t) ? ` · ${n(t)}` : ""}`);
  }), F("click", c, o), f(i, p), N();
}
P(["click"]);
const k = T(H), K = k.mount, L = k.unmount;
export {
  K as mount,
  L as unmount
};
//# sourceMappingURL=demo.js.map
