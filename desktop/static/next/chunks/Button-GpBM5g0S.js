import { a5 as I, av as R, aw as O, ax as m, ay as D, az as y, g as c, w as L, e as F, aA as M, F as N, ak as Y, aB as C, W as z, aC as K, aD as x, ab as U, aE as j, $ as q, aF as G, p as W, T as Z, a as $, b as H, n as J, S as Q, u as V, h as X } from "./api-vHpIWCot.js";
let b = !1;
function k(e) {
  var r = b;
  try {
    return b = !1, [e(), b];
  } finally {
    b = r;
  }
}
function ee(e, r, ...n) {
  var t = new O(e);
  I(() => {
    const i = r() ?? null;
    t.ensure(i, i && ((s) => i(s, ...n)));
  }, R);
}
const re = {
  get(e, r) {
    if (!e.exclude.has(r))
      return e.props[r];
  },
  set(e, r) {
    return !1;
  },
  getOwnPropertyDescriptor(e, r) {
    if (!e.exclude.has(r) && r in e.props)
      return {
        enumerable: !0,
        configurable: !0,
        value: e.props[r]
      };
  },
  has(e, r) {
    return e.exclude.has(r) ? !1 : r in e.props;
  },
  ownKeys(e) {
    return Reflect.ownKeys(e.props).filter((r) => !e.exclude.has(r));
  }
};
// @__NO_SIDE_EFFECTS__
function ae(e, r, n) {
  return new Proxy(
    { props: e, exclude: r },
    re
  );
}
function A(e, r, n, t) {
  var i = !0, s = (n & C) !== 0, u = (n & j) !== 0, f = (
    /** @type {V} */
    t
  ), h = !0, S = (
    /** @type {Derived<V> | undefined} */
    void 0
  ), P = () => u && i ? (S ?? (S = x(
    /** @type {() => V} */
    t
  )), c(S)) : (h && (h = !1, f = u ? z(
    /** @type {() => V} */
    t
  ) : (
    /** @type {V} */
    t
  )), f);
  let l;
  if (s) {
    var T = q in e || G in e;
    l = m(e, r)?.set ?? (T && r in e ? (a) => e[r] = a : void 0);
  }
  var _, g = !1;
  s ? [_, g] = k(() => (
    /** @type {V} */
    e[r]
  )) : _ = /** @type {V} */
  e[r], _ === void 0 && t !== void 0 && (_ = P(), l && (D(), l(_)));
  var o;
  if (o = () => {
    var a = (
      /** @type {V} */
      e[r]
    );
    return a === void 0 ? P() : (h = !0, a);
  }, (n & y) === 0)
    return o;
  if (l) {
    var w = e.$$legacy;
    return (
      /** @type {() => V} */
      (function(a, v) {
        return arguments.length > 0 ? ((!v || w || g) && l(v ? o() : a), a) : o();
      })
    );
  }
  var p = !1, d = ((n & K) !== 0 ? x : U)(() => (p = !1, o()));
  s && c(d);
  var B = (
    /** @type {Effect} */
    N
  );
  return (
    /** @type {() => V} */
    (function(a, v) {
      if (arguments.length > 0) {
        const E = v ? c(d) : s ? L(a) : a;
        return F(d, E), p = !0, f !== void 0 && (f = E), a;
      }
      return M && p || (B.f & Y) !== 0 ? d.v : c(d);
    })
  );
}
var ne = /* @__PURE__ */ new Set([
  "$$slots",
  "$$events",
  "$$legacy",
  "variant",
  "class",
  "children"
]), te = J("<button><!></button>");
function ie(e, r) {
  W(r, !0);
  let n = A(r, "variant", 3, ""), t = A(r, "class", 3, ""), i = /* @__PURE__ */ ae(r, ne);
  const s = V(() => ["btn", n(), t()].filter(Boolean).join(" "));
  var u = te();
  Z(u, () => ({ type: "button", class: c(s), ...i }));
  var f = X(u);
  ee(f, () => r.children ?? Q), $(e, u), H();
}
export {
  ie as B,
  A as p,
  ae as r,
  ee as s
};
//# sourceMappingURL=Button-GpBM5g0S.js.map
