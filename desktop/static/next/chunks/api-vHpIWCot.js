var Gn = Object.defineProperty;
var Mr = (e) => {
  throw TypeError(e);
};
var Yn = (e, t, r) => t in e ? Gn(e, t, { enumerable: !0, configurable: !0, writable: !0, value: r }) : e[t] = r;
var U = (e, t, r) => Yn(e, typeof t != "symbol" ? t + "" : t, r), tr = (e, t, r) => t.has(e) || Mr("Cannot " + r);
var a = (e, t, r) => (tr(e, t, "read from private field"), r ? r.call(e) : t.get(e)), g = (e, t, r) => t.has(e) ? Mr("Cannot add the same private member more than once") : t instanceof WeakSet ? t.add(e) : t.set(e, r), p = (e, t, r, n) => (tr(e, t, "write to private field"), n ? n.call(e, r) : t.set(e, r), r), m = (e, t, r) => (tr(e, t, "access private method"), r);
var $r;
typeof window < "u" && (($r = window.__svelte ?? (window.__svelte = {})).v ?? ($r.v = /* @__PURE__ */ new Set())).add("5");
const Bs = 1, Hs = 2, Vs = 4, qs = 8, Us = 16, Gs = 1, Ys = 4, $s = 8, zs = 16, $n = 1, zn = 2, M = Symbol("uninitialized"), zr = "http://www.w3.org/1999/xhtml", Ws = "http://www.w3.org/2000/svg", Ks = "http://www.w3.org/1998/Math/MathML", Wn = "@attach", Wr = !1;
var Kr = Array.isArray, Kn = Array.prototype.indexOf, jt = Array.prototype.includes, Zn = Array.from, Jn = Object.defineProperty, _t = Object.getOwnPropertyDescriptor, Xn = Object.getOwnPropertyDescriptors, Qn = Object.prototype, ei = Array.prototype, Zr = Object.getPrototypeOf, Cr = Object.isExtensible;
const ti = () => {
};
function ri(e) {
  for (var t = 0; t < e.length; t++)
    e[t]();
}
function Jr() {
  var e, t, r = new Promise((n, i) => {
    e = n, t = i;
  });
  return { promise: r, resolve: e, reject: t };
}
function Zs(e, t) {
  if (Array.isArray(e))
    return e;
  if (t === void 0 || !(Symbol.iterator in e))
    return Array.from(e);
  const r = [];
  for (const n of e)
    if (r.push(n), r.length === t) break;
  return r;
}
const L = 2, tt = 4, Wt = 8, Er = 1 << 24, ne = 16, oe = 32, Te = 64, fr = 128, J = 512, C = 1024, I = 2048, ce = 4096, X = 8192, le = 16384, at = 32768, Ir = 1 << 25, rt = 65536, Dt = 1 << 17, ni = 1 << 18, ft = 1 << 19, ii = 1 << 20, Js = 1 << 25, Be = 65536, xt = 1 << 21, $e = 1 << 22, Se = 1 << 23, pt = Symbol("$state"), Xs = Symbol("legacy props"), si = Symbol(""), Rt = Symbol("attributes"), lr = Symbol("class"), ur = Symbol("style"), ot = Symbol("text"), Mt = Symbol("form reset"), Kt = new class extends Error {
  constructor() {
    super(...arguments);
    U(this, "name", "StaleReactionError");
    U(this, "message", "The reaction that called `getAbortSignal()` was re-run or destroyed");
  }
}(), Zt = (
  // We gotta write it like this because after downleveling the pure comment may end up in the wrong location
  !!globalThis.document?.contentType && /* @__PURE__ */ globalThis.document.contentType.includes("xml")
);
function ai() {
  throw new Error("https://svelte.dev/e/async_derived_orphan");
}
function ea(e, t, r) {
  throw new Error("https://svelte.dev/e/each_key_duplicate");
}
function fi(e) {
  throw new Error("https://svelte.dev/e/effect_in_teardown");
}
function li() {
  throw new Error("https://svelte.dev/e/effect_in_unowned_derived");
}
function ui(e) {
  throw new Error("https://svelte.dev/e/effect_orphan");
}
function oi() {
  throw new Error("https://svelte.dev/e/effect_update_depth_exceeded");
}
function ta(e) {
  throw new Error("https://svelte.dev/e/props_invalid_value");
}
function ci() {
  throw new Error("https://svelte.dev/e/state_descriptors_fixed");
}
function hi() {
  throw new Error("https://svelte.dev/e/state_prototype_fixed");
}
function di() {
  throw new Error("https://svelte.dev/e/state_unsafe_mutation");
}
function vi() {
  throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror");
}
function _i() {
  console.warn("https://svelte.dev/e/derived_inert");
}
function pi() {
  console.warn("https://svelte.dev/e/select_multiple_invalid_value");
}
function wi() {
  console.warn("https://svelte.dev/e/svelte_boundary_reset_noop");
}
function Xr(e) {
  return e === this.v;
}
function gi(e, t) {
  return e != e ? t == t : e !== t || e !== null && typeof e == "object" || typeof e == "function";
}
function Qr(e) {
  return !gi(e, this.v);
}
let yi = !1, V = null;
function nt(e) {
  V = e;
}
function bi(e, t = !1, r) {
  V = {
    p: V,
    i: !1,
    c: null,
    e: null,
    s: e,
    x: null,
    r: (
      /** @type {Effect} */
      E
    ),
    l: null
  };
}
function Ei(e) {
  var t = (
    /** @type {ComponentContext} */
    V
  ), r = t.e;
  if (r !== null) {
    t.e = null;
    for (var n of r)
      bn(n);
  }
  return t.i = !0, V = t.p, /** @type {T} */
  {};
}
function en() {
  return !0;
}
let Pe = [];
function tn() {
  var e = Pe;
  Pe = [], ri(e);
}
function Ae(e) {
  if (Pe.length === 0 && !wt) {
    var t = Pe;
    queueMicrotask(() => {
      t === Pe && tn();
    });
  }
  Pe.push(e);
}
function mi() {
  for (; Pe.length > 0; )
    tn();
}
function rn(e) {
  var t = E;
  if (t === null)
    return y.f |= Se, e;
  if ((t.f & at) === 0 && (t.f & tt) === 0)
    throw e;
  me(e, t);
}
function me(e, t) {
  for (; t !== null; ) {
    if ((t.f & fr) !== 0) {
      if ((t.f & at) === 0)
        throw e;
      try {
        t.b.error(e);
        return;
      } catch (r) {
        e = r;
      }
    }
    t = t.parent;
  }
  throw e;
}
const ki = -7169;
function R(e, t) {
  e.f = e.f & ki | t;
}
function mr(e) {
  (e.f & J) !== 0 || e.deps === null ? R(e, C) : R(e, ce);
}
function nn(e) {
  if (e !== null)
    for (const t of e)
      (t.f & L) === 0 || (t.f & Be) === 0 || (t.f ^= Be, nn(
        /** @type {Derived} */
        t.deps
      ));
}
function sn(e, t, r) {
  (e.f & I) !== 0 ? t.add(e) : (e.f & ce) !== 0 && r.add(e), nn(e.deps), R(e, C);
}
function Si(e) {
  let t = 0, r = Ot(0), n;
  return () => {
    Or() && (ke(r), Ji(() => (t === 0 && (n = rs(() => e(() => gt(r)))), t += 1, () => {
      Ae(() => {
        t -= 1, t === 0 && (n?.(), n = void 0, gt(r));
      });
    })));
  };
}
var Ai = rt | ft;
function Ti(e, t, r, n) {
  new Oi(e, t, r, n);
}
var W, br, K, Ce, x, Z, j, Y, _e, Ie, be, We, mt, kt, pe, Yt, N, Ni, Pi, Ri, or, Ct, It, cr, hr;
class Oi {
  /**
   * @param {TemplateNode} node
   * @param {BoundaryProps} props
   * @param {((anchor: Node) => void)} children
   * @param {((error: unknown) => unknown) | undefined} [transform_error]
   */
  constructor(t, r, n, i) {
    g(this, N);
    /** @type {Boundary | null} */
    U(this, "parent");
    U(this, "is_pending", !1);
    /**
     * API-level transformError transform function. Transforms errors before they reach the `failed` snippet.
     * Inherited from parent boundary, or defaults to identity.
     * @type {(error: unknown) => unknown}
     */
    U(this, "transform_error");
    /** @type {TemplateNode} */
    g(this, W);
    /** @type {TemplateNode | null} */
    g(this, br, null);
    /** @type {BoundaryProps} */
    g(this, K);
    /** @type {((anchor: Node) => void)} */
    g(this, Ce);
    /** @type {Effect} */
    g(this, x);
    /** @type {Effect | null} */
    g(this, Z, null);
    /** @type {Effect | null} */
    g(this, j, null);
    /** @type {Effect | null} */
    g(this, Y, null);
    /** @type {DocumentFragment | null} */
    g(this, _e, null);
    g(this, Ie, 0);
    g(this, be, 0);
    g(this, We, !1);
    /** @type {Set<Effect>} */
    g(this, mt, /* @__PURE__ */ new Set());
    /** @type {Set<Effect>} */
    g(this, kt, /* @__PURE__ */ new Set());
    /**
     * A source containing the number of pending async deriveds/expressions.
     * Only created if `$effect.pending()` is used inside the boundary,
     * otherwise updating the source results in needless `Batch.ensure()`
     * calls followed by no-op flushes
     * @type {Source<number> | null}
     */
    g(this, pe, null);
    g(this, Yt, Si(() => (p(this, pe, Ot(a(this, Ie))), () => {
      p(this, pe, null);
    })));
    p(this, W, t), p(this, K, r), p(this, Ce, (s) => {
      var f = (
        /** @type {Effect} */
        E
      );
      f.b = this, f.f |= fr, n(s);
    }), this.parent = /** @type {Effect} */
    E.b, this.transform_error = i ?? this.parent?.transform_error ?? ((s) => s), p(this, x, En(() => {
      m(this, N, or).call(this);
    }, Ai));
  }
  /**
   * Defer an effect inside a pending boundary until the boundary resolves
   * @param {Effect} effect
   */
  defer_effect(t) {
    sn(t, a(this, mt), a(this, kt));
  }
  /**
   * Returns `false` if the effect exists inside a boundary whose pending snippet is shown
   * @returns {boolean}
   */
  is_rendered() {
    return !this.is_pending && (!this.parent || this.parent.is_rendered());
  }
  has_pending_snippet() {
    return !!a(this, K).pending;
  }
  /**
   * Update the source that powers `$effect.pending()` inside this boundary,
   * and controls when the current `pending` snippet (if any) is removed.
   * Do not call from inside the class
   * @param {1 | -1} d
   * @param {Batch} batch
   */
  update_pending_count(t, r) {
    m(this, N, cr).call(this, t, r), p(this, Ie, a(this, Ie) + t), !(!a(this, pe) || a(this, We)) && (p(this, We, !0), Ae(() => {
      p(this, We, !1), a(this, pe) && Vt(a(this, pe), a(this, Ie));
    }));
  }
  get_effect_pending() {
    return a(this, Yt).call(this), ke(
      /** @type {Source<number>} */
      a(this, pe)
    );
  }
  /** @param {unknown} error */
  error(t) {
    if (!a(this, K).onerror && !a(this, K).failed)
      throw t;
    b?.is_fork ? (a(this, Z) && b.skip_effect(a(this, Z)), a(this, j) && b.skip_effect(a(this, j)), a(this, Y) && b.skip_effect(a(this, Y)), b.oncommit(() => {
      m(this, N, hr).call(this, t);
    })) : m(this, N, hr).call(this, t);
  }
}
W = new WeakMap(), br = new WeakMap(), K = new WeakMap(), Ce = new WeakMap(), x = new WeakMap(), Z = new WeakMap(), j = new WeakMap(), Y = new WeakMap(), _e = new WeakMap(), Ie = new WeakMap(), be = new WeakMap(), We = new WeakMap(), mt = new WeakMap(), kt = new WeakMap(), pe = new WeakMap(), Yt = new WeakMap(), N = new WeakSet(), Ni = function() {
  try {
    p(this, Z, re(() => a(this, Ce).call(this, a(this, W))));
  } catch (t) {
    this.error(t);
  }
}, /**
 * @param {unknown} error The deserialized error from the server's hydration comment
 */
Pi = function(t) {
  const r = a(this, K).failed;
  r && p(this, Y, re(() => {
    r(
      a(this, W),
      () => t,
      () => () => {
      }
    );
  }));
}, Ri = function() {
  const t = a(this, K).pending;
  t && (this.is_pending = !0, p(this, j, re(() => t(a(this, W)))), Ae(() => {
    var r = p(this, _e, document.createDocumentFragment()), n = it();
    r.append(n), p(this, Z, m(this, N, It).call(this, () => re(() => a(this, Ce).call(this, n)))), a(this, be) === 0 && (a(this, W).before(r), p(this, _e, null), yt(
      /** @type {Effect} */
      a(this, j),
      () => {
        p(this, j, null);
      }
    ), m(this, N, Ct).call(
      this,
      /** @type {Batch} */
      b
    ));
  }));
}, or = function() {
  try {
    if (this.is_pending = this.has_pending_snippet(), p(this, be, 0), p(this, Ie, 0), p(this, Z, re(() => {
      a(this, Ce).call(this, a(this, W));
    })), a(this, be) > 0) {
      var t = p(this, _e, document.createDocumentFragment());
      On(a(this, Z), t);
      const r = (
        /** @type {(anchor: Node) => void} */
        a(this, K).pending
      );
      p(this, j, re(() => r(a(this, W))));
    } else
      m(this, N, Ct).call(
        this,
        /** @type {Batch} */
        b
      );
  } catch (r) {
    this.error(r);
  }
}, /**
 * @param {Batch} batch
 */
Ct = function(t) {
  this.is_pending = !1, t.transfer_effects(a(this, mt), a(this, kt));
}, /**
 * @template T
 * @param {() => T} fn
 */
It = function(t) {
  var r = E, n = y, i = V;
  he(a(this, x)), Q(a(this, x)), nt(a(this, x).ctx);
  try {
    return He.ensure(), t();
  } catch (s) {
    return rn(s), null;
  } finally {
    he(r), Q(n), nt(i);
  }
}, /**
 * Updates the pending count associated with the currently visible pending snippet,
 * if any, such that we can replace the snippet with content once work is done
 * @param {1 | -1} d
 * @param {Batch} batch
 */
cr = function(t, r) {
  var n;
  if (!this.has_pending_snippet()) {
    this.parent && m(n = this.parent, N, cr).call(n, t, r);
    return;
  }
  p(this, be, a(this, be) + t), a(this, be) === 0 && (m(this, N, Ct).call(this, r), a(this, j) && yt(a(this, j), () => {
    p(this, j, null);
  }), a(this, _e) && (a(this, W).before(a(this, _e)), p(this, _e, null)));
}, /**
 * @param {unknown} error
 */
hr = function(t) {
  a(this, Z) && (F(a(this, Z)), p(this, Z, null)), a(this, j) && (F(a(this, j)), p(this, j, null)), a(this, Y) && (F(a(this, Y)), p(this, Y, null));
  var r = a(this, K).onerror;
  let n = a(this, K).failed;
  var i = !1, s = !1;
  const f = () => {
    if (i) {
      wi();
      return;
    }
    i = !0, s && vi(), a(this, Y) !== null && yt(a(this, Y), () => {
      p(this, Y, null);
    }), m(this, N, It).call(this, () => {
      m(this, N, or).call(this);
    });
  }, l = (u) => {
    try {
      s = !0, r?.(u, f), s = !1;
    } catch (o) {
      me(o, a(this, x) && a(this, x).parent);
    }
    n && p(this, Y, m(this, N, It).call(this, () => {
      try {
        return re(() => {
          var o = (
            /** @type {Effect} */
            E
          );
          o.b = this, o.f |= fr, n(
            a(this, W),
            () => u,
            () => f
          );
        });
      } catch (o) {
        return me(
          o,
          /** @type {Effect} */
          a(this, x).parent
        ), null;
      }
    }));
  };
  Ae(() => {
    var u;
    try {
      u = this.transform_error(t);
    } catch (o) {
      me(o, a(this, x) && a(this, x).parent);
      return;
    }
    u !== null && typeof u == "object" && typeof /** @type {any} */
    u.then == "function" ? u.then(
      l,
      /** @param {unknown} e */
      (o) => me(o, a(this, x) && a(this, x).parent)
    ) : l(u);
  });
};
function an(e, t, r, n) {
  const i = kr;
  var s = e.filter((h) => !h.settled), f = t.map(i);
  if (r.length === 0 && s.length === 0) {
    n(f);
    return;
  }
  var l = (
    /** @type {Effect} */
    E
  ), u = Mi(), o = s.length === 1 ? s[0].promise : s.length > 1 ? Promise.all(s.map((h) => h.promise)) : null;
  function v(h) {
    if ((l.f & le) === 0) {
      u();
      try {
        n([...f, ...h]);
      } catch (_) {
        me(_, l);
      }
      Bt();
    }
  }
  var d = fn();
  if (r.length === 0) {
    o.then(() => v([])).finally(d);
    return;
  }
  function c() {
    Promise.all(r.map((h) => /* @__PURE__ */ Ci(h))).then(v).catch((h) => me(h, l)).finally(d);
  }
  o ? o.then(() => {
    u(), c(), Bt();
  }) : c();
}
function Mi() {
  var e = (
    /** @type {Effect} */
    E
  ), t = y, r = V, n = (
    /** @type {Batch} */
    b
  );
  return function(s = !0) {
    he(e), Q(t), nt(r), s && (e.f & le) === 0 && (n?.activate(), n?.apply());
  };
}
function Bt(e = !0) {
  he(null), Q(null), nt(null), e && b?.deactivate();
}
function fn() {
  var e = (
    /** @type {Effect} */
    E
  ), t = e.b, r = (
    /** @type {Batch} */
    b
  ), n = !!t?.is_rendered();
  return t?.update_pending_count(1, r), r.increment(n, e), () => {
    t?.update_pending_count(-1, r), r.decrement(n, e);
  };
}
// @__NO_SIDE_EFFECTS__
function kr(e) {
  var t = L | I;
  return E !== null && (E.f |= ft), {
    ctx: V,
    deps: null,
    effects: null,
    equals: Xr,
    f: t,
    fn: e,
    reactions: null,
    rv: 0,
    v: (
      /** @type {V} */
      M
    ),
    wv: 0,
    parent: E,
    ac: null
  };
}
const ct = Symbol("obsolete");
// @__NO_SIDE_EFFECTS__
function Ci(e, t, r) {
  let n = (
    /** @type {Effect | null} */
    E
  );
  n === null && ai();
  var i = (
    /** @type {Promise<V>} */
    /** @type {unknown} */
    void 0
  ), s = Ot(
    /** @type {V} */
    M
  ), f = !y, l = /* @__PURE__ */ new Set();
  return Zi(() => {
    var u = (
      /** @type {Effect} */
      E
    ), o = Jr();
    i = o.promise;
    try {
      Promise.resolve(e()).then(o.resolve, (h) => {
        h !== Kt && o.reject(h);
      }).finally(Bt);
    } catch (h) {
      o.reject(h), Bt();
    }
    var v = (
      /** @type {Batch} */
      b
    );
    if (f) {
      if ((u.f & at) !== 0)
        var d = fn();
      if (
        // boundary can be null if the async derived is inside an $effect.root not connected to the component render tree
        n.b?.is_rendered()
      )
        v.async_deriveds.get(u)?.reject(ct);
      else
        for (const h of l.values())
          h.reject(ct);
      l.add(o), v.async_deriveds.set(u, o);
    }
    const c = (h, _ = void 0) => {
      d?.(), l.delete(o), _ !== ct && (v.activate(), _ ? (s.f |= Se, Vt(s, _)) : ((s.f & Se) !== 0 && (s.f ^= Se), Vt(s, h)), v.deactivate());
    };
    o.promise.then(c, (h) => c(null, h || "unknown"));
  }), Nr(() => {
    for (const u of l)
      u.reject(ct);
  }), new Promise((u) => {
    function o(v) {
      function d() {
        v === i ? u(s) : o(i);
      }
      v.then(d, d);
    }
    o(i);
  });
}
// @__NO_SIDE_EFFECTS__
function ra(e) {
  const t = /* @__PURE__ */ kr(e);
  return Nn(t), t;
}
// @__NO_SIDE_EFFECTS__
function na(e) {
  const t = /* @__PURE__ */ kr(e);
  return t.equals = Qr, t;
}
function Ii(e) {
  var t = e.effects;
  if (t !== null) {
    e.effects = null;
    for (var r = 0; r < t.length; r += 1)
      F(
        /** @type {Effect} */
        t[r]
      );
  }
}
function Sr(e) {
  var t, r = E, n = e.parent;
  if (!Oe && n !== null && e.v !== M && // if it was never evaluated before, it's guaranteed to fail downstream, so we try to execute instead
  (n.f & (le | X)) !== 0)
    return _i(), e.v;
  he(n);
  try {
    e.f &= ~Be, Ii(e), t = Cn(e);
  } finally {
    he(r);
  }
  return t;
}
function ln(e) {
  var t = Sr(e);
  if (!e.equals(t) && (e.wv = Rn(), (!b?.is_fork || e.deps === null) && (b !== null ? (b.capture(e, t, !0), dr?.capture(e, t, !0)) : e.v = t, e.deps === null))) {
    R(e, C);
    return;
  }
  Oe || (ie !== null ? (Or() || b?.is_fork) && ie.set(e, t) : mr(e));
}
function Li(e) {
  if (e.effects !== null)
    for (const t of e.effects)
      (t.teardown || t.ac) && (t.teardown?.(), t.ac?.abort(Kt), t.fn !== null && (t.teardown = ti), t.ac = null, Et(t, 0), Rr(t));
}
function un(e) {
  if (e.effects !== null)
    for (const t of e.effects)
      t.teardown && t.fn !== null && st(t);
}
let rr = null, Ue = null, b = null, dr = null, ie = null, vr = null, wt = !1, nr = !1, Ye = null, Lt = null;
var Lr = 0;
let Fi = 1;
var Ke, Ee, Le, Ze, Je, Xe, we, Qe, B, St, ge, ee, ae, et, Fe, k, _r, ht, pr, on, cn, Ge, ji, dt;
const $t = class $t {
  constructor() {
    g(this, k);
    U(this, "id", Fi++);
    /** True as soon as `#process` was called */
    g(this, Ke, !1);
    U(this, "linked", !0);
    /** @type {Batch | null} */
    g(this, Ee, null);
    /** @type {Batch | null} */
    g(this, Le, null);
    /** @type {Map<Effect, ReturnType<typeof deferred<any>>>} */
    U(this, "async_deriveds", /* @__PURE__ */ new Map());
    /**
     * The current values of any signals that are updated in this batch.
     * Tuple format: [value, is_derived] (note: is_derived is false for deriveds, too, if they were overridden via assignment)
     * They keys of this map are identical to `this.#previous`
     * @type {Map<Value, [any, boolean]>}
     */
    U(this, "current", /* @__PURE__ */ new Map());
    /**
     * The values of any signals (sources and deriveds) that are updated in this batch _before_ those updates took place.
     * They keys of this map are identical to `this.#current`
     * @type {Map<Value, any>}
     */
    U(this, "previous", /* @__PURE__ */ new Map());
    /**
     * When the batch is committed (and the DOM is updated), we need to remove old branches
     * and append new ones by calling the functions added inside (if/each/key/etc) blocks
     * @type {Set<(batch: Batch) => void>}
     */
    g(this, Ze, /* @__PURE__ */ new Set());
    /**
     * If a fork is discarded, we need to destroy any effects that are no longer needed
     * @type {Set<(batch: Batch) => void>}
     */
    g(this, Je, /* @__PURE__ */ new Set());
    /**
     * The number of async effects that are currently in flight
     */
    g(this, Xe, 0);
    /**
     * Async effects that are currently in flight, _not_ inside a pending boundary
     * @type {Map<Effect, number>}
     */
    g(this, we, /* @__PURE__ */ new Map());
    /**
     * A deferred that resolves when the batch is committed, used with `settled()`
     * TODO replace with Promise.withResolvers once supported widely enough
     * @type {{ promise: Promise<void>, resolve: (value?: any) => void, reject: (reason: unknown) => void } | null}
     */
    g(this, Qe, null);
    /**
     * The root effects that need to be flushed
     * @type {Effect[]}
     */
    g(this, B, []);
    /**
     * Effects created while this batch was active.
     * @type {Effect[]}
     */
    g(this, St, []);
    /**
     * Deferred effects (which run after async work has completed) that are DIRTY
     * @type {Set<Effect>}
     */
    g(this, ge, /* @__PURE__ */ new Set());
    /**
     * Deferred effects that are MAYBE_DIRTY
     * @type {Set<Effect>}
     */
    g(this, ee, /* @__PURE__ */ new Set());
    /**
     * A map of branches that still exist, but will be destroyed when this batch
     * is committed — we skip over these during `process`.
     * The value contains child effects that were dirty/maybe_dirty before being reset,
     * so they can be rescheduled if the branch survives.
     * @type {Map<Effect, { d: Effect[], m: Effect[] }>}
     */
    g(this, ae, /* @__PURE__ */ new Map());
    /**
     * Inverse of #skipped_branches which we need to tell prior batches to unskip them when committing
     * @type {Set<Effect>}
     */
    g(this, et, /* @__PURE__ */ new Set());
    U(this, "is_fork", !1);
    g(this, Fe, !1);
    Ue === null ? rr = Ue = this : (p(Ue, Le, this), p(this, Ee, Ue)), Ue = this;
  }
  /**
   * Add an effect to the #skipped_branches map and reset its children
   * @param {Effect} effect
   */
  skip_effect(t) {
    a(this, ae).has(t) || a(this, ae).set(t, { d: [], m: [] }), a(this, et).delete(t);
  }
  /**
   * Remove an effect from the #skipped_branches map and reschedule
   * any tracked dirty/maybe_dirty child effects
   * @param {Effect} effect
   * @param {(e: Effect) => void} callback
   */
  unskip_effect(t, r = (n) => this.schedule(n)) {
    var n = a(this, ae).get(t);
    if (n) {
      a(this, ae).delete(t);
      for (var i of n.d)
        R(i, I), r(i);
      for (i of n.m)
        R(i, ce), r(i);
    }
    a(this, et).add(t);
  }
  /**
   * Associate a change to a given source with the current
   * batch, noting its previous and current values
   * @param {Value} source
   * @param {any} value
   * @param {boolean} [is_derived]
   */
  capture(t, r, n = !1) {
    t.v !== M && !this.previous.has(t) && this.previous.set(t, t.v), (t.f & Se) === 0 && (this.current.set(t, [r, n]), ie?.set(t, r)), this.is_fork || (t.v = r);
  }
  activate() {
    b = this;
  }
  deactivate() {
    b = null, ie = null;
  }
  flush() {
    try {
      nr = !0, b = this, m(this, k, ht).call(this);
    } finally {
      Lr = 0, vr = null, Ye = null, Lt = null, nr = !1, b = null, ie = null, De.clear();
    }
  }
  discard() {
    for (const t of a(this, Je)) t(this);
    a(this, Je).clear();
    for (const t of this.async_deriveds.values())
      t.reject(ct);
    m(this, k, dt).call(this), a(this, Qe)?.resolve();
  }
  /**
   * @param {Effect} effect
   */
  register_created_effect(t) {
    a(this, St).push(t);
  }
  /**
   * @param {boolean} blocking
   * @param {Effect} effect
   */
  increment(t, r) {
    if (p(this, Xe, a(this, Xe) + 1), t) {
      let n = a(this, we).get(r) ?? 0;
      a(this, we).set(r, n + 1);
    }
  }
  /**
   * @param {boolean} blocking
   * @param {Effect} effect
   */
  decrement(t, r) {
    if (p(this, Xe, a(this, Xe) - 1), t) {
      let n = a(this, we).get(r) ?? 0;
      n === 1 ? a(this, we).delete(r) : a(this, we).set(r, n - 1);
    }
    a(this, Fe) || (p(this, Fe, !0), Ae(() => {
      p(this, Fe, !1), this.linked && this.flush();
    }));
  }
  /**
   * @param {Set<Effect>} dirty_effects
   * @param {Set<Effect>} maybe_dirty_effects
   */
  transfer_effects(t, r) {
    for (const n of t)
      a(this, ge).add(n);
    for (const n of r)
      a(this, ee).add(n);
    t.clear(), r.clear();
  }
  /** @param {(batch: Batch) => void} fn */
  oncommit(t) {
    a(this, Ze).add(t);
  }
  /** @param {(batch: Batch) => void} fn */
  ondiscard(t) {
    a(this, Je).add(t);
  }
  settled() {
    return (a(this, Qe) ?? p(this, Qe, Jr())).promise;
  }
  static ensure() {
    if (b === null) {
      const t = b = new $t();
      !nr && !wt && Ae(() => {
        a(t, Ke) || t.flush();
      });
    }
    return b;
  }
  apply() {
    {
      ie = null;
      return;
    }
  }
  /**
   *
   * @param {Effect} effect
   */
  schedule(t) {
    if (vr = t, t.b?.is_pending && (t.f & (tt | Wt | Er)) !== 0 && (t.f & at) === 0) {
      t.b.defer_effect(t);
      return;
    }
    for (var r = t; r.parent !== null; ) {
      r = r.parent;
      var n = r.f;
      if (Ye !== null && r === E && (y === null || (y.f & L) === 0))
        return;
      if ((n & (Te | oe)) !== 0) {
        if ((n & C) === 0)
          return;
        r.f ^= C;
      }
    }
    a(this, B).push(r);
  }
};
Ke = new WeakMap(), Ee = new WeakMap(), Le = new WeakMap(), Ze = new WeakMap(), Je = new WeakMap(), Xe = new WeakMap(), we = new WeakMap(), Qe = new WeakMap(), B = new WeakMap(), St = new WeakMap(), ge = new WeakMap(), ee = new WeakMap(), ae = new WeakMap(), et = new WeakMap(), Fe = new WeakMap(), k = new WeakSet(), _r = function() {
  if (this.is_fork) return !0;
  for (const n of a(this, we).keys()) {
    for (var t = n, r = !1; t.parent !== null; ) {
      if (a(this, ae).has(t)) {
        r = !0;
        break;
      }
      t = t.parent;
    }
    if (!r)
      return !0;
  }
  return !1;
}, ht = function() {
  var u, o, v;
  p(this, Ke, !0), Lr++ > 1e3 && (m(this, k, dt).call(this), xi());
  for (const d of a(this, ge))
    a(this, ee).delete(d), R(d, I), this.schedule(d);
  for (const d of a(this, ee))
    R(d, ce), this.schedule(d);
  const t = a(this, B);
  p(this, B, []), this.apply();
  var r = Ye = [], n = [], i = Lt = [];
  for (const d of t)
    try {
      m(this, k, pr).call(this, d, r, n);
    } catch (c) {
      throw vn(d), m(this, k, _r).call(this) || this.discard(), c;
    }
  if (b = null, i.length > 0) {
    var s = $t.ensure();
    for (const d of i)
      s.schedule(d);
  }
  if (Ye = null, Lt = null, m(this, k, _r).call(this)) {
    m(this, k, Ge).call(this, n), m(this, k, Ge).call(this, r);
    for (const [d, c] of a(this, ae))
      dn(d, c);
    i.length > 0 && /** @type {unknown} */
    m(u = b, k, ht).call(u);
    return;
  }
  const f = m(this, k, on).call(this);
  if (f) {
    m(this, k, Ge).call(this, n), m(this, k, Ge).call(this, r), m(o = f, k, cn).call(o, this);
    return;
  }
  a(this, ge).clear(), a(this, ee).clear();
  for (const d of a(this, Ze)) d(this);
  a(this, Ze).clear(), dr = this, Fr(n), Fr(r), dr = null, a(this, Qe)?.resolve();
  var l = (
    /** @type {Batch | null} */
    /** @type {unknown} */
    b
  );
  if (a(this, Xe) === 0 && (a(this, B).length === 0 || l !== null) && m(this, k, dt).call(this), a(this, B).length > 0)
    if (l !== null) {
      const d = l;
      a(d, B).push(...a(this, B).filter((c) => !a(d, B).includes(c)));
    } else
      l = this;
  l !== null && m(v = l, k, ht).call(v);
}, /**
 * Traverse the effect tree, executing effects or stashing
 * them for later execution as appropriate
 * @param {Effect} root
 * @param {Effect[]} effects
 * @param {Effect[]} render_effects
 */
pr = function(t, r, n) {
  t.f ^= C;
  for (var i = t.first; i !== null; ) {
    var s = i.f, f = (s & (oe | Te)) !== 0, l = f && (s & C) !== 0, u = l || (s & X) !== 0 || a(this, ae).has(i);
    if (!u && i.fn !== null) {
      f ? i.f ^= C : (s & tt) !== 0 ? r.push(i) : Nt(i) && ((s & ne) !== 0 && a(this, ee).add(i), st(i));
      var o = i.first;
      if (o !== null) {
        i = o;
        continue;
      }
    }
    for (; i !== null; ) {
      var v = i.next;
      if (v !== null) {
        i = v;
        break;
      }
      i = i.parent;
    }
  }
}, on = function() {
  for (var t = a(this, Ee); t !== null; ) {
    if (!t.is_fork) {
      for (const [r, [, n]] of this.current)
        if (t.current.has(r) && !n)
          return t;
    }
    t = a(t, Ee);
  }
  return null;
}, /**
 * @param {Batch} batch
 */
cn = function(t) {
  var n;
  for (const [i, s] of t.current)
    !this.previous.has(i) && t.previous.has(i) && this.previous.set(i, t.previous.get(i)), this.current.set(i, s);
  for (const [i, s] of t.async_deriveds) {
    const f = this.async_deriveds.get(i);
    f && s.promise.then(f.resolve).catch(f.reject);
  }
  t.async_deriveds.clear(), this.transfer_effects(a(t, ge), a(t, ee));
  const r = (i) => {
    var s = i.reactions;
    if (s !== null)
      for (const u of s) {
        var f = u.f;
        if ((f & L) !== 0)
          r(
            /** @type {Derived} */
            u
          );
        else {
          var l = (
            /** @type {Effect} */
            u
          );
          f & ($e | ne) && !this.async_deriveds.has(l) && (a(this, ee).delete(l), R(l, I), this.schedule(l));
        }
      }
  };
  for (const i of this.current.keys())
    r(i);
  this.oncommit(() => t.discard()), m(n = t, k, dt).call(n), b = this, m(this, k, ht).call(this);
}, /**
 * @param {Effect[]} effects
 */
Ge = function(t) {
  for (var r = 0; r < t.length; r += 1)
    sn(t[r], a(this, ge), a(this, ee));
}, ji = function() {
  var d;
  for (let c = rr; c !== null; c = a(c, Le)) {
    var t = c.id < this.id, r = [];
    for (const [h, [_, w]] of this.current) {
      if (c.current.has(h)) {
        var n = (
          /** @type {[any, boolean]} */
          c.current.get(h)[0]
        );
        if (t && _ !== n)
          c.current.set(h, [_, w]);
        else
          continue;
      }
      r.push(h);
    }
    if (t)
      for (const [h, _] of this.async_deriveds) {
        const w = c.async_deriveds.get(h);
        w && _.promise.then(w.resolve).catch(w.reject);
      }
    var i = [...c.current.keys()].filter(
      (h) => !/** @type {[any, boolean]} */
      c.current.get(h)[1]
    );
    if (!(!a(c, Ke) || i.length === 0)) {
      var s = i.filter((h) => !this.current.has(h));
      if (s.length === 0)
        t && c.discard();
      else if (r.length > 0) {
        if (t)
          for (const h of a(this, et))
            c.unskip_effect(h, (_) => {
              var w;
              (_.f & (ne | $e)) !== 0 ? c.schedule(_) : m(w = c, k, Ge).call(w, [_]);
            });
        c.activate();
        var f = /* @__PURE__ */ new Set(), l = /* @__PURE__ */ new Map();
        for (var u of r)
          hn(u, s, f, l);
        l = /* @__PURE__ */ new Map();
        var o = [...c.current].filter(([h, _]) => {
          const w = this.current.get(h);
          return w ? w[0] !== _[0] || w[1] !== _[1] : !0;
        }).map(([h]) => h);
        if (o.length > 0)
          for (const h of a(this, St))
            (h.f & (le | X | Dt)) === 0 && Ar(h, o, l) && ((h.f & ($e | ne)) !== 0 ? (R(h, I), c.schedule(h)) : a(c, ge).add(h));
        if (a(c, B).length > 0 && !a(c, Fe)) {
          c.apply();
          for (var v of a(c, B))
            m(d = c, k, pr).call(d, v, [], []);
          p(c, B, []);
        }
        c.deactivate();
      }
    }
  }
}, dt = function() {
  if (this.linked) {
    var t = a(this, Ee), r = a(this, Le);
    t === null ? rr = r : p(t, Le, r), r === null ? Ue = t : p(r, Ee, t), this.linked = !1;
  }
};
let He = $t;
function Di(e) {
  var t = wt;
  wt = !0;
  try {
    for (var r; ; ) {
      if (mi(), b === null)
        return (
          /** @type {T} */
          r
        );
      b.flush();
    }
  } finally {
    wt = t;
  }
}
function xi() {
  try {
    oi();
  } catch (e) {
    me(e, vr);
  }
}
let ve = null;
function Fr(e) {
  var t = e.length;
  if (t !== 0) {
    for (var r = 0; r < t; ) {
      var n = e[r++];
      if ((n.f & (le | X)) === 0 && Nt(n) && (ve = /* @__PURE__ */ new Set(), st(n), n.deps === null && n.first === null && n.nodes === null && n.teardown === null && n.ac === null && Sn(n), ve?.size > 0)) {
        De.clear();
        for (const i of ve) {
          if ((i.f & (le | X)) !== 0) continue;
          const s = [i];
          let f = i.parent;
          for (; f !== null; )
            ve.has(f) && (ve.delete(f), s.push(f)), f = f.parent;
          for (let l = s.length - 1; l >= 0; l--) {
            const u = s[l];
            (u.f & (le | X)) === 0 && st(u);
          }
        }
        ve.clear();
      }
    }
    ve = null;
  }
}
function hn(e, t, r, n) {
  if (!r.has(e) && (r.add(e), e.reactions !== null))
    for (const i of e.reactions) {
      const s = i.f;
      (s & L) !== 0 ? hn(
        /** @type {Derived} */
        i,
        t,
        r,
        n
      ) : (s & ($e | ne)) !== 0 && (s & I) === 0 && Ar(i, t, n) && (R(i, I), Tr(
        /** @type {Effect} */
        i
      ));
    }
}
function Ar(e, t, r) {
  const n = r.get(e);
  if (n !== void 0) return n;
  if (e.deps !== null)
    for (const i of e.deps) {
      if (jt.call(t, i))
        return !0;
      if ((i.f & L) !== 0 && Ar(
        /** @type {Derived} */
        i,
        t,
        r
      ))
        return r.set(
          /** @type {Derived} */
          i,
          !0
        ), !0;
    }
  return r.set(e, !1), !1;
}
function Tr(e) {
  b.schedule(e);
}
function dn(e, t) {
  if (!((e.f & oe) !== 0 && (e.f & C) !== 0)) {
    (e.f & I) !== 0 ? t.d.push(e) : (e.f & ce) !== 0 && t.m.push(e), R(e, C);
    for (var r = e.first; r !== null; )
      dn(r, t), r = r.next;
  }
}
function vn(e) {
  R(e, C);
  for (var t = e.first; t !== null; )
    vn(t), t = t.next;
}
let Ht = /* @__PURE__ */ new Set();
const De = /* @__PURE__ */ new Map();
let _n = !1;
function Ot(e, t) {
  var r = {
    f: 0,
    // TODO ideally we could skip this altogether, but it causes type errors
    v: e,
    reactions: null,
    equals: Xr,
    rv: 0,
    wv: 0
  };
  return r;
}
// @__NO_SIDE_EFFECTS__
function ye(e, t) {
  const r = Ot(e);
  return Nn(r), r;
}
// @__NO_SIDE_EFFECTS__
function ia(e, t = !1, r = !0) {
  const n = Ot(e);
  return t || (n.equals = Qr), n;
}
function Ne(e, t, r = !1) {
  y !== null && // since we are untracking the function inside `$inspect.with` we need to add this check
  // to ensure we error if state is set inside an inspect effect
  (!se || (y.f & Dt) !== 0) && en() && (y.f & (L | ne | $e | Dt)) !== 0 && (ue === null || !ue.has(e)) && di();
  let n = r ? vt(t) : t;
  return Vt(e, n, Lt);
}
function Vt(e, t, r = null) {
  if (!e.equals(t)) {
    De.set(e, Oe ? t : e.v);
    var n = He.ensure();
    if (n.capture(e, t), (e.f & L) !== 0) {
      const i = (
        /** @type {Derived} */
        e
      );
      (e.f & I) !== 0 && Sr(i), ie === null && mr(i);
    }
    e.wv = Rn(), pn(e, I, r), E !== null && (E.f & C) !== 0 && (E.f & (oe | Te)) === 0 && (z === null ? es([e]) : z.push(e)), !n.is_fork && Ht.size > 0 && !_n && Bi();
  }
  return t;
}
function Bi() {
  _n = !1;
  for (const e of Ht) {
    (e.f & C) !== 0 && R(e, ce);
    let t;
    try {
      t = Nt(e);
    } catch {
      t = !0;
    }
    t && st(e);
  }
  Ht.clear();
}
function gt(e) {
  Ne(e, e.v + 1);
}
function pn(e, t, r) {
  var n = e.reactions;
  if (n !== null)
    for (var i = n.length, s = 0; s < i; s++) {
      var f = n[s], l = f.f, u = (l & I) === 0;
      if (u && R(f, t), (l & Dt) !== 0)
        Ht.add(
          /** @type {Effect} */
          f
        );
      else if ((l & L) !== 0) {
        var o = (
          /** @type {Derived} */
          f
        );
        ie?.delete(o), (l & Be) === 0 && (l & J && (E === null || (E.f & xt) === 0) && (f.f |= Be), pn(o, ce, r));
      } else if (u) {
        var v = (
          /** @type {Effect} */
          f
        );
        (l & ne) !== 0 && ve !== null && ve.add(v), r !== null ? r.push(v) : Tr(v);
      }
    }
}
function vt(e) {
  if (typeof e != "object" || e === null || pt in e)
    return e;
  const t = Zr(e);
  if (t !== Qn && t !== ei)
    return e;
  var r = /* @__PURE__ */ new Map(), n = Kr(e), i = /* @__PURE__ */ ye(0), s = xe, f = (l) => {
    if (xe === s)
      return l();
    var u = y, o = xe;
    Q(null), Vr(s);
    var v = l();
    return Q(u), Vr(o), v;
  };
  return n && r.set("length", /* @__PURE__ */ ye(
    /** @type {any[]} */
    e.length
  )), new Proxy(
    /** @type {any} */
    e,
    {
      defineProperty(l, u, o) {
        (!("value" in o) || o.configurable === !1 || o.enumerable === !1 || o.writable === !1) && ci();
        var v = r.get(u);
        return v === void 0 ? f(() => {
          var d = /* @__PURE__ */ ye(o.value);
          return r.set(u, d), d;
        }) : Ne(v, o.value, !0), !0;
      },
      deleteProperty(l, u) {
        var o = r.get(u);
        if (o === void 0) {
          if (u in l) {
            const v = f(() => /* @__PURE__ */ ye(M));
            r.set(u, v), gt(i);
          }
        } else
          Ne(o, M), gt(i);
        return !0;
      },
      get(l, u, o) {
        if (u === pt)
          return e;
        var v = r.get(u), d = u in l;
        if (v === void 0 && (!d || _t(l, u)?.writable) && (v = f(() => {
          var h = vt(d ? l[u] : M), _ = /* @__PURE__ */ ye(h);
          return _;
        }), r.set(u, v)), v !== void 0) {
          var c = ke(v);
          return c === M ? void 0 : c;
        }
        return Reflect.get(l, u, o);
      },
      getOwnPropertyDescriptor(l, u) {
        var o = Reflect.getOwnPropertyDescriptor(l, u);
        if (o && "value" in o) {
          var v = r.get(u);
          v && (o.value = ke(v));
        } else if (o === void 0) {
          var d = r.get(u), c = d?.v;
          if (d !== void 0 && c !== M)
            return {
              enumerable: !0,
              configurable: !0,
              value: c,
              writable: !0
            };
        }
        return o;
      },
      has(l, u) {
        if (u === pt)
          return !0;
        var o = r.get(u), v = o !== void 0 && o.v !== M || Reflect.has(l, u);
        if (o !== void 0 || E !== null && (!v || _t(l, u)?.writable)) {
          o === void 0 && (o = f(() => {
            var c = v ? vt(l[u]) : M, h = /* @__PURE__ */ ye(c);
            return h;
          }), r.set(u, o));
          var d = ke(o);
          if (d === M)
            return !1;
        }
        return v;
      },
      set(l, u, o, v) {
        var d = r.get(u), c = u in l;
        if (n && u === "length")
          for (var h = o; h < /** @type {Source<number>} */
          d.v; h += 1) {
            var _ = r.get(h + "");
            _ !== void 0 ? Ne(_, M) : h in l && (_ = f(() => /* @__PURE__ */ ye(M)), r.set(h + "", _));
          }
        if (d === void 0)
          (!c || _t(l, u)?.writable) && (d = f(() => /* @__PURE__ */ ye(void 0)), Ne(d, vt(o)), r.set(u, d));
        else {
          c = d.v !== M;
          var w = f(() => vt(o));
          Ne(d, w);
        }
        var A = Reflect.getOwnPropertyDescriptor(l, u);
        if (A?.set && A.set.call(v, o), !c) {
          if (n && typeof u == "string") {
            var T = (
              /** @type {Source<number>} */
              r.get("length")
            ), P = Number(u);
            Number.isInteger(P) && P >= T.v && Ne(T, P + 1);
          }
          gt(i);
        }
        return !0;
      },
      ownKeys(l) {
        ke(i);
        var u = Reflect.ownKeys(l).filter((d) => {
          var c = r.get(d);
          return c === void 0 || c.v !== M;
        });
        for (var [o, v] of r)
          v.v !== M && !(o in l) && u.push(o);
        return u;
      },
      setPrototypeOf() {
        hi();
      }
    }
  );
}
function jr(e) {
  try {
    if (e !== null && typeof e == "object" && pt in e)
      return e[pt];
  } catch {
  }
  return e;
}
function Hi(e, t) {
  return Object.is(jr(e), jr(t));
}
var Dr, wn, gn, yn;
function Vi() {
  if (Dr === void 0) {
    Dr = window, wn = /Firefox/.test(navigator.userAgent);
    var e = Element.prototype, t = Node.prototype, r = Text.prototype;
    gn = _t(t, "firstChild").get, yn = _t(t, "nextSibling").get, Cr(e) && (e[lr] = void 0, e[Rt] = null, e[ur] = void 0, e.__e = void 0), Cr(r) && (r[ot] = void 0);
  }
}
function it(e = "") {
  return document.createTextNode(e);
}
// @__NO_SIDE_EFFECTS__
function qt(e) {
  return (
    /** @type {TemplateNode | null} */
    gn.call(e)
  );
}
// @__NO_SIDE_EFFECTS__
function Jt(e) {
  return (
    /** @type {TemplateNode | null} */
    yn.call(e)
  );
}
function sa(e, t) {
  return /* @__PURE__ */ qt(e);
}
function aa(e, t = !1) {
  {
    var r = /* @__PURE__ */ qt(e);
    return r instanceof Comment && r.data === "" ? /* @__PURE__ */ Jt(r) : r;
  }
}
function fa(e, t = 1, r = !1) {
  let n = e;
  for (; t--; )
    n = /** @type {TemplateNode} */
    /* @__PURE__ */ Jt(n);
  return n;
}
function la(e) {
  e.textContent = "";
}
function qi() {
  return !1;
}
function Ui(e, t, r) {
  return t == null || t === zr ? (
    /** @type {T extends keyof HTMLElementTagNameMap ? HTMLElementTagNameMap[T] : Element} */
    r ? document.createElement(e, { is: r }) : document.createElement(e)
  ) : (
    /** @type {T extends keyof HTMLElementTagNameMap ? HTMLElementTagNameMap[T] : Element} */
    r ? document.createElementNS(t, e, { is: r }) : document.createElementNS(t, e)
  );
}
function Gi(e, t) {
  if (t) {
    const r = document.body;
    e.autofocus = !0, Ae(() => {
      document.activeElement === r && e.focus();
    });
  }
}
let xr = !1;
function Yi() {
  xr || (xr = !0, document.addEventListener(
    "reset",
    (e) => {
      Promise.resolve().then(() => {
        if (!e.defaultPrevented)
          for (
            const t of
            /**@type {HTMLFormElement} */
            e.target.elements
          )
            t[Mt]?.();
      });
    },
    // In the capture phase to guarantee we get noticed of it (no possibility of stopPropagation)
    { capture: !0 }
  ));
}
function Xt(e) {
  var t = y, r = E;
  Q(null), he(null);
  try {
    return e();
  } finally {
    Q(t), he(r);
  }
}
function $i(e, t, r, n = r) {
  e.addEventListener(t, () => Xt(r));
  const i = (
    /** @type {any} */
    e[Mt]
  );
  i ? e[Mt] = () => {
    i(), n(!0);
  } : e[Mt] = () => n(!0), Yi();
}
function zi(e) {
  E === null && (y === null && ui(), li()), Oe && fi();
}
function Wi(e, t) {
  var r = t.last;
  r === null ? t.last = t.first = e : (r.next = e, e.prev = r, t.last = e);
}
function de(e, t) {
  var r = E;
  r !== null && (r.f & X) !== 0 && (e |= X);
  var n = {
    ctx: V,
    deps: null,
    nodes: null,
    f: e | I | J,
    first: null,
    fn: t,
    last: null,
    next: null,
    parent: r,
    b: r && r.b,
    prev: null,
    teardown: null,
    wv: 0,
    ac: null
  };
  b?.register_created_effect(n);
  var i = n;
  if ((e & tt) !== 0)
    Ye !== null ? Ye.push(n) : He.ensure().schedule(n);
  else if (t !== null) {
    try {
      st(n);
    } catch (f) {
      throw F(n), f;
    }
    i.deps === null && i.teardown === null && i.nodes === null && i.first === i.last && // either `null`, or a singular child
    (i.f & ft) === 0 && (i = i.first, (e & ne) !== 0 && (e & rt) !== 0 && i !== null && (i.f |= rt));
  }
  if (i !== null && (i.parent = r, r !== null && Wi(i, r), y !== null && (y.f & L) !== 0 && (e & Te) === 0)) {
    var s = (
      /** @type {Derived} */
      y
    );
    (s.effects ?? (s.effects = [])).push(i);
  }
  return n;
}
function Or() {
  return y !== null && !se;
}
function Nr(e) {
  const t = de(Wt, null);
  return R(t, C), t.teardown = e, t;
}
function ua(e) {
  zi();
  var t = (
    /** @type {Effect} */
    E.f
  ), r = !y && (t & oe) !== 0 && V !== null && !V.i;
  if (r) {
    var n = (
      /** @type {ComponentContext} */
      V
    );
    (n.e ?? (n.e = [])).push(e);
  } else
    return bn(e);
}
function bn(e) {
  return de(tt | ii, e);
}
function Ki(e) {
  He.ensure();
  const t = de(Te | ft, e);
  return (r = {}) => new Promise((n) => {
    r.outro ? yt(t, () => {
      F(t), n(void 0);
    }) : (F(t), n(void 0));
  });
}
function Pr(e) {
  return de(tt, e);
}
function Zi(e) {
  return de($e | ft, e);
}
function Ji(e, t = 0) {
  return de(Wt | t, e);
}
function oa(e, t = [], r = [], n = []) {
  an(n, t, r, (i) => {
    de(Wt, () => {
      e(...i.map(ke));
    });
  });
}
function En(e, t = 0) {
  var r = de(ne | t, e);
  return r;
}
function mn(e, t = 0) {
  var r = de(Er | t, e);
  return r;
}
function re(e) {
  return de(oe | ft, e);
}
function kn(e) {
  var t = e.teardown;
  if (t !== null) {
    const r = Oe, n = y;
    Hr(!0), Q(null);
    try {
      t.call(null);
    } finally {
      Hr(r), Q(n);
    }
  }
}
function Rr(e, t = !1) {
  var r = e.first;
  for (e.first = e.last = null; r !== null; ) {
    const i = r.ac;
    i !== null && Xt(() => {
      i.abort(Kt);
    });
    var n = r.next;
    (r.f & Te) !== 0 ? r.parent = null : F(r, t), r = n;
  }
}
function Xi(e) {
  for (var t = e.first; t !== null; ) {
    var r = t.next;
    (t.f & oe) === 0 && F(t), t = r;
  }
}
function F(e, t = !0) {
  var r = !1;
  (t || (e.f & ni) !== 0) && e.nodes !== null && e.nodes.end !== null && (Qi(
    e.nodes.start,
    /** @type {TemplateNode} */
    e.nodes.end
  ), r = !0), e.f |= Ir, Rr(e, t && !r), Et(e, 0);
  var n = e.nodes && e.nodes.t;
  if (n !== null)
    for (const s of n)
      s.stop();
  kn(e), e.f ^= Ir, e.f |= le;
  var i = e.parent;
  i !== null && i.first !== null && Sn(e), e.next = e.prev = e.teardown = e.ctx = e.deps = e.fn = e.nodes = e.ac = e.b = null;
}
function Qi(e, t) {
  for (; e !== null; ) {
    var r = e === t ? null : /* @__PURE__ */ Jt(e);
    e.remove(), e = r;
  }
}
function Sn(e) {
  var t = e.parent, r = e.prev, n = e.next;
  r !== null && (r.next = n), n !== null && (n.prev = r), t !== null && (t.first === e && (t.first = n), t.last === e && (t.last = r));
}
function yt(e, t, r = !0) {
  var n = [];
  An(e, n, !0);
  var i = () => {
    r && F(e), t && t();
  }, s = n.length;
  if (s > 0) {
    var f = () => --s || i();
    for (var l of n)
      l.out(f);
  } else
    i();
}
function An(e, t, r) {
  if ((e.f & X) === 0) {
    e.f ^= X;
    var n = e.nodes && e.nodes.t;
    if (n !== null)
      for (const l of n)
        (l.is_global || r) && t.push(l);
    for (var i = e.first; i !== null; ) {
      var s = i.next;
      if ((i.f & Te) === 0) {
        var f = (i.f & rt) !== 0 || // If this is a branch effect without a block effect parent,
        // it means the parent block effect was pruned. In that case,
        // transparency information was transferred to the branch effect.
        (i.f & oe) !== 0 && (e.f & ne) !== 0;
        An(i, t, f ? r : !1);
      }
      i = s;
    }
  }
}
function Br(e) {
  Tn(e, !0);
}
function Tn(e, t) {
  if ((e.f & X) !== 0) {
    e.f ^= X, (e.f & C) === 0 && (R(e, I), He.ensure().schedule(e));
    for (var r = e.first; r !== null; ) {
      var n = r.next, i = (r.f & rt) !== 0 || (r.f & oe) !== 0;
      Tn(r, i ? t : !1), r = n;
    }
    var s = e.nodes && e.nodes.t;
    if (s !== null)
      for (const f of s)
        (f.is_global || t) && f.in();
  }
}
function On(e, t) {
  if (e.nodes)
    for (var r = e.nodes.start, n = e.nodes.end; r !== null; ) {
      var i = r === n ? null : /* @__PURE__ */ Jt(r);
      t.append(r), r = i;
    }
}
let Ft = !1, Oe = !1;
function Hr(e) {
  Oe = e;
}
let y = null, se = !1;
function Q(e) {
  y = e;
}
let E = null;
function he(e) {
  E = e;
}
let ue = null;
function Nn(e) {
  y !== null && (ue ?? (ue = /* @__PURE__ */ new Set())).add(e);
}
let H = null, G = 0, z = null;
function es(e) {
  z = e;
}
let Pn = 1, Re = 0, xe = Re;
function Vr(e) {
  xe = e;
}
function Rn() {
  return ++Pn;
}
function Nt(e) {
  var t = e.f;
  if ((t & I) !== 0)
    return !0;
  if (t & L && (e.f &= ~Be), (t & ce) !== 0) {
    for (var r = (
      /** @type {Value[]} */
      e.deps
    ), n = r.length, i = 0; i < n; i++) {
      var s = r[i];
      if (Nt(
        /** @type {Derived} */
        s
      ) && ln(
        /** @type {Derived} */
        s
      ), s.wv > e.wv)
        return !0;
    }
    (t & J) !== 0 && // During time traveling we don't want to reset the status so that
    // traversal of the graph in the other batches still happens
    ie === null && R(e, C);
  }
  return !1;
}
function Mn(e, t, r = !0) {
  var n = e.reactions;
  if (n !== null && !(ue !== null && ue.has(e)))
    for (var i = 0; i < n.length; i++) {
      var s = n[i];
      (s.f & L) !== 0 ? Mn(
        /** @type {Derived} */
        s,
        t,
        !1
      ) : t === s && (r ? R(s, I) : (s.f & C) !== 0 && R(s, ce), Tr(
        /** @type {Effect} */
        s
      ));
    }
}
function Cn(e) {
  var w;
  var t = H, r = G, n = z, i = y, s = ue, f = V, l = se, u = xe, o = e.f;
  H = /** @type {null | Value[]} */
  null, G = 0, z = null, y = (o & (oe | Te)) === 0 ? e : null, ue = null, nt(e.ctx), se = !1, xe = ++Re, e.ac !== null && (Xt(() => {
    e.ac.abort(Kt);
  }), e.ac = null);
  try {
    e.f |= xt;
    var v = (
      /** @type {Function} */
      e.fn
    ), d = v();
    e.f |= at;
    var c = e.deps, h = b?.is_fork;
    if (H !== null) {
      var _;
      if (h || Et(e, G), c !== null && G > 0)
        for (c.length = G + H.length, _ = 0; _ < H.length; _++)
          c[G + _] = H[_];
      else
        e.deps = c = H;
      if (Or() && (e.f & J) !== 0)
        for (_ = G; _ < c.length; _++)
          ((w = c[_]).reactions ?? (w.reactions = [])).push(e);
    } else !h && c !== null && G < c.length && (Et(e, G), c.length = G);
    if (en() && z !== null && !se && c !== null && (e.f & (L | ce | I)) === 0)
      for (_ = 0; _ < /** @type {Source[]} */
      z.length; _++)
        Mn(
          z[_],
          /** @type {Effect} */
          e
        );
    if (i !== null && i !== e) {
      if (Re++, i.deps !== null)
        for (let A = 0; A < r; A += 1)
          i.deps[A].rv = Re;
      if (t !== null)
        for (const A of t)
          A.rv = Re;
      z !== null && (n === null ? n = z : n.push(.../** @type {Source[]} */
      z));
    }
    return (e.f & Se) !== 0 && (e.f ^= Se), d;
  } catch (A) {
    return rn(A);
  } finally {
    e.f ^= xt, H = t, G = r, z = n, y = i, ue = s, nt(f), se = l, xe = u;
  }
}
function ts(e, t) {
  let r = t.reactions;
  if (r !== null) {
    var n = Kn.call(r, e);
    if (n !== -1) {
      var i = r.length - 1;
      i === 0 ? r = t.reactions = null : (r[n] = r[i], r.pop());
    }
  }
  if (r === null && (t.f & L) !== 0 && // Destroying a child effect while updating a parent effect can cause a dependency to appear
  // to be unused, when in fact it is used by the currently-updating parent. Checking `new_deps`
  // allows us to skip the expensive work of disconnecting and immediately reconnecting it
  (H === null || !jt.call(H, t))) {
    var s = (
      /** @type {Derived} */
      t
    );
    (s.f & J) !== 0 && (s.f ^= J, s.f &= ~Be), s.v !== M && mr(s), Li(s), Et(s, 0);
  }
}
function Et(e, t) {
  var r = e.deps;
  if (r !== null)
    for (var n = t; n < r.length; n++)
      ts(e, r[n]);
}
function st(e) {
  var t = e.f;
  if ((t & le) === 0) {
    R(e, C);
    var r = E, n = Ft;
    E = e, Ft = !0;
    try {
      (t & (ne | Er)) !== 0 ? Xi(e) : Rr(e), kn(e);
      var i = Cn(e);
      e.teardown = typeof i == "function" ? i : null, e.wv = Pn;
      var s;
      Wr && yi && (e.f & I) !== 0 && e.deps;
    } finally {
      Ft = n, E = r;
    }
  }
}
async function ca() {
  await Promise.resolve(), Di();
}
function ke(e) {
  var t = e.f, r = (t & L) !== 0;
  if (y !== null && !se) {
    var n = E !== null && (E.f & le) !== 0;
    if (!n && (ue === null || !ue.has(e))) {
      var i = y.deps;
      if ((y.f & xt) !== 0)
        e.rv < Re && (e.rv = Re, H === null && i !== null && i[G] === e ? G++ : H === null ? H = [e] : H.push(e));
      else {
        y.deps ?? (y.deps = []), jt.call(y.deps, e) || y.deps.push(e);
        var s = e.reactions;
        s === null ? e.reactions = [y] : jt.call(s, y) || s.push(y);
      }
    }
  }
  if (Oe && De.has(e))
    return De.get(e);
  if (r) {
    var f = (
      /** @type {Derived} */
      e
    );
    if (Oe) {
      var l = f.v;
      return ((f.f & C) === 0 && f.reactions !== null || Ln(f)) && (l = Sr(f)), De.set(f, l), l;
    }
    var u = (f.f & J) === 0 && !se && y !== null && (Ft || (y.f & J) !== 0), o = (f.f & at) === 0;
    Nt(f) && (u && (f.f |= J), ln(f)), u && !o && (un(f), In(f));
  }
  if (ie?.has(e))
    return ie.get(e);
  if ((e.f & Se) !== 0)
    throw e.v;
  return e.v;
}
function In(e) {
  if (e.f |= J, e.deps !== null)
    for (const t of e.deps)
      (t.reactions ?? (t.reactions = [])).push(e), (t.f & L) !== 0 && (t.f & J) === 0 && (un(
        /** @type {Derived} */
        t
      ), In(
        /** @type {Derived} */
        t
      ));
}
function Ln(e) {
  if (e.v === M) return !0;
  if (e.deps === null) return !1;
  for (const t of e.deps)
    if (De.has(t) || (t.f & L) !== 0 && Ln(
      /** @type {Derived} */
      t
    ))
      return !0;
  return !1;
}
function rs(e) {
  var t = se;
  try {
    return se = !0, e();
  } finally {
    se = t;
  }
}
const Me = Symbol("events"), Fn = /* @__PURE__ */ new Set(), wr = /* @__PURE__ */ new Set();
function jn(e, t, r, n = {}) {
  function i(s) {
    if (n.capture || gr.call(t, s), !s.cancelBubble)
      return Xt(() => r?.call(this, s));
  }
  return e.startsWith("pointer") || e.startsWith("touch") || e === "wheel" ? Ae(() => {
    t.addEventListener(e, i, n);
  }) : t.addEventListener(e, i, n), i;
}
function ha(e, t, r, n, i) {
  var s = { capture: n, passive: i }, f = jn(e, t, r, s);
  (t === document.body || // @ts-ignore
  t === window || // @ts-ignore
  t === document || // Firefox has quirky behavior, it can happen that we still get "canplay" events when the element is already removed
  t instanceof HTMLMediaElement) && Nr(() => {
    t.removeEventListener(e, f, s);
  });
}
function ns(e, t, r) {
  (t[Me] ?? (t[Me] = {}))[e] = r;
}
function is(e) {
  for (var t = 0; t < e.length; t++)
    Fn.add(e[t]);
  for (var r of wr)
    r(e);
}
let qr = null;
function gr(e) {
  var t = this, r = (
    /** @type {Node} */
    t.ownerDocument
  ), n = e.type, i = e.composedPath?.() || [], s = (
    /** @type {null | Element} */
    i[0] || e.target
  );
  qr = e;
  var f = 0, l = qr === e && e[Me];
  if (l) {
    var u = i.indexOf(l);
    if (u !== -1 && (t === document || t === /** @type {any} */
    window)) {
      e[Me] = t;
      return;
    }
    var o = i.indexOf(t);
    if (o === -1)
      return;
    u <= o && (f = u);
  }
  if (s = /** @type {Element} */
  i[f] || e.target, s !== t) {
    Jn(e, "currentTarget", {
      configurable: !0,
      get() {
        return s || r;
      }
    });
    var v = y, d = E;
    Q(null), he(null);
    try {
      for (var c, h = []; s !== null && s !== t; ) {
        try {
          var _ = s[Me]?.[n];
          _ != null && (!/** @type {any} */
          s.disabled || // DOM could've been updated already by the time this is reached, so we check this as well
          // -> the target could not have been disabled because it emits the event in the first place
          e.target === s) && _.call(s, e);
        } catch (w) {
          c ? h.push(w) : c = w;
        }
        if (e.cancelBubble) break;
        f++, s = f < i.length ? (
          /** @type {Element} */
          i[f]
        ) : null;
      }
      if (c) {
        for (let w of h)
          queueMicrotask(() => {
            throw w;
          });
        throw c;
      }
    } finally {
      e[Me] = t, delete e.currentTarget, Q(v), he(d);
    }
  }
}
const ss = (
  // We gotta write it like this because after downleveling the pure comment may end up in the wrong location
  globalThis?.window?.trustedTypes && /* @__PURE__ */ globalThis.window.trustedTypes.createPolicy("svelte-trusted-html", {
    /** @param {string} html */
    createHTML: (e) => e
  })
);
function as(e) {
  return (
    /** @type {string} */
    ss?.createHTML(e) ?? e
  );
}
function fs(e) {
  var t = Ui("template");
  return t.innerHTML = as(e.replaceAll("<!>", "<!---->")), t.content;
}
function Ut(e, t) {
  var r = (
    /** @type {Effect} */
    E
  );
  r.nodes === null && (r.nodes = { start: e, end: t, a: null, t: null });
}
// @__NO_SIDE_EFFECTS__
function da(e, t) {
  var r = (t & $n) !== 0, n = (t & zn) !== 0, i, s = !e.startsWith("<!>");
  return () => {
    i === void 0 && (i = fs(s ? e : "<!>" + e), r || (i = /** @type {TemplateNode} */
    /* @__PURE__ */ qt(i)));
    var f = (
      /** @type {TemplateNode} */
      n || wn ? document.importNode(i, !0) : i.cloneNode(!0)
    );
    if (r) {
      var l = (
        /** @type {TemplateNode} */
        /* @__PURE__ */ qt(f)
      ), u = (
        /** @type {TemplateNode} */
        f.lastChild
      );
      Ut(l, u);
    } else
      Ut(f, f);
    return f;
  };
}
function va(e = "") {
  {
    var t = it(e + "");
    return Ut(t, t), t;
  }
}
function _a() {
  var e = document.createDocumentFragment(), t = document.createComment(""), r = it();
  return e.append(t, r), Ut(t, r), e;
}
function pa(e, t) {
  e !== null && e.before(
    /** @type {Node} */
    t
  );
}
function ls(e) {
  return e.endsWith("capture") && e !== "gotpointercapture" && e !== "lostpointercapture";
}
const us = [
  "beforeinput",
  "click",
  "change",
  "dblclick",
  "contextmenu",
  "focusin",
  "focusout",
  "input",
  "keydown",
  "keyup",
  "mousedown",
  "mousemove",
  "mouseout",
  "mouseover",
  "mouseup",
  "pointerdown",
  "pointermove",
  "pointerout",
  "pointerover",
  "pointerup",
  "touchend",
  "touchmove",
  "touchstart"
];
function os(e) {
  return us.includes(e);
}
const cs = {
  // no `class: 'className'` because we handle that separately
  formnovalidate: "formNoValidate",
  ismap: "isMap",
  nomodule: "noModule",
  playsinline: "playsInline",
  readonly: "readOnly",
  defaultvalue: "defaultValue",
  defaultchecked: "defaultChecked",
  srcobject: "srcObject",
  novalidate: "noValidate",
  allowfullscreen: "allowFullscreen",
  disablepictureinpicture: "disablePictureInPicture",
  disableremoteplayback: "disableRemotePlayback"
};
function hs(e) {
  return e = e.toLowerCase(), cs[e] ?? e;
}
const ds = ["touchstart", "touchmove"];
function vs(e) {
  return ds.includes(e);
}
function wa(e, t) {
  var r = t == null ? "" : typeof t == "object" ? `${t}` : t;
  r !== /** @type {any} */
  (e[ot] ?? (e[ot] = e.nodeValue)) && (e[ot] = r, e.nodeValue = `${r}`);
}
function ga(e, t) {
  return _s(e, t);
}
const Pt = /* @__PURE__ */ new Map();
function _s(e, { target: t, anchor: r, props: n = {}, events: i, context: s, intro: f = !0, transformError: l }) {
  Vi();
  var u = void 0, o = Ki(() => {
    var v = r ?? t.appendChild(it());
    Ti(
      /** @type {TemplateNode} */
      v,
      {
        pending: () => {
        }
      },
      (h) => {
        bi({});
        var _ = (
          /** @type {ComponentContext} */
          V
        );
        s && (_.c = s), i && (n.$$events = i), u = e(h, n) || {}, Ei();
      },
      l
    );
    var d = /* @__PURE__ */ new Set(), c = (h) => {
      for (var _ = 0; _ < h.length; _++) {
        var w = h[_];
        if (!d.has(w)) {
          d.add(w);
          var A = vs(w);
          for (const Ve of [t, document]) {
            var T = Pt.get(Ve);
            T === void 0 && (T = /* @__PURE__ */ new Map(), Pt.set(Ve, T));
            var P = T.get(w);
            P === void 0 ? (Ve.addEventListener(w, gr, { passive: A }), T.set(w, 1)) : T.set(w, P + 1);
          }
        }
      }
    };
    return c(Zn(Fn)), wr.add(c), () => {
      for (var h of d)
        for (const A of [t, document]) {
          var _ = (
            /** @type {Map<string, number>} */
            Pt.get(A)
          ), w = (
            /** @type {number} */
            _.get(h)
          );
          --w == 0 ? (A.removeEventListener(h, gr), _.delete(h), _.size === 0 && Pt.delete(A)) : _.set(h, w);
        }
      wr.delete(c), v !== r && v.parentNode?.removeChild(v);
    };
  });
  return yr.set(u, o), u;
}
let yr = /* @__PURE__ */ new WeakMap();
function ya(e, t) {
  const r = yr.get(e);
  return r ? (yr.delete(e), r(t)) : Promise.resolve();
}
var te, fe, $, je, At, Tt, zt;
class ps {
  /**
   * @param {TemplateNode} anchor
   * @param {boolean} transition
   */
  constructor(t, r = !0) {
    /** @type {TemplateNode} */
    U(this, "anchor");
    /** @type {Map<Batch, Key>} */
    g(this, te, /* @__PURE__ */ new Map());
    /**
     * Map of keys to effects that are currently rendered in the DOM.
     * These effects are visible and actively part of the document tree.
     * Example:
     * ```
     * {#if condition}
     * 	foo
     * {:else}
     * 	bar
     * {/if}
     * ```
     * Can result in the entries `true->Effect` and `false->Effect`
     * @type {Map<Key, Effect>}
     */
    g(this, fe, /* @__PURE__ */ new Map());
    /**
     * Similar to #onscreen with respect to the keys, but contains branches that are not yet
     * in the DOM, because their insertion is deferred.
     * @type {Map<Key, Branch>}
     */
    g(this, $, /* @__PURE__ */ new Map());
    /**
     * Keys of effects that are currently outroing
     * @type {Set<Key>}
     */
    g(this, je, /* @__PURE__ */ new Set());
    /**
     * Whether to pause (i.e. outro) on change, or destroy immediately.
     * This is necessary for `<svelte:element>`
     */
    g(this, At, !0);
    /**
     * @param {Batch} batch
     */
    g(this, Tt, (t) => {
      if (a(this, te).has(t)) {
        var r = (
          /** @type {Key} */
          a(this, te).get(t)
        ), n = a(this, fe).get(r);
        if (n)
          Br(n), a(this, je).delete(r);
        else {
          var i = a(this, $).get(r);
          i && (Br(i.effect), a(this, fe).set(r, i.effect), a(this, $).delete(r), i.fragment.lastChild.remove(), this.anchor.before(i.fragment), n = i.effect);
        }
        for (const [s, f] of a(this, te)) {
          if (a(this, te).delete(s), s === t)
            break;
          const l = a(this, $).get(f);
          l && (F(l.effect), a(this, $).delete(f));
        }
        for (const [s, f] of a(this, fe)) {
          if (s === r || a(this, je).has(s)) continue;
          const l = () => {
            if (Array.from(a(this, te).values()).includes(s)) {
              var o = document.createDocumentFragment();
              On(f, o), o.append(it()), a(this, $).set(s, { effect: f, fragment: o });
            } else
              F(f);
            a(this, je).delete(s), a(this, fe).delete(s);
          };
          a(this, At) || !n ? (a(this, je).add(s), yt(f, l, !1)) : l();
        }
      }
    });
    /**
     * @param {Batch} batch
     */
    g(this, zt, (t) => {
      a(this, te).delete(t);
      const r = Array.from(a(this, te).values());
      for (const [n, i] of a(this, $))
        r.includes(n) || (F(i.effect), a(this, $).delete(n));
    });
    this.anchor = t, p(this, At, r);
  }
  /**
   *
   * @param {any} key
   * @param {null | ((target: TemplateNode) => void)} fn
   */
  ensure(t, r) {
    var n = (
      /** @type {Batch} */
      b
    ), i = qi();
    if (r && !a(this, fe).has(t) && !a(this, $).has(t))
      if (i) {
        var s = document.createDocumentFragment(), f = it();
        s.append(f), a(this, $).set(t, {
          effect: re(() => r(f)),
          fragment: s
        });
      } else
        a(this, fe).set(
          t,
          re(() => r(this.anchor))
        );
    if (a(this, te).set(n, t), i) {
      for (const [l, u] of a(this, fe))
        l === t ? n.unskip_effect(u) : n.skip_effect(u);
      for (const [l, u] of a(this, $))
        l === t ? n.unskip_effect(u.effect) : n.skip_effect(u.effect);
      n.oncommit(a(this, Tt)), n.ondiscard(a(this, zt));
    } else
      a(this, Tt).call(this, n);
  }
}
te = new WeakMap(), fe = new WeakMap(), $ = new WeakMap(), je = new WeakMap(), At = new WeakMap(), Tt = new WeakMap(), zt = new WeakMap();
function ba(e, t, r = !1) {
  var n = new ps(e), i = r ? rt : 0;
  function s(f, l) {
    n.ensure(f, l);
  }
  En(() => {
    var f = !1;
    t((l, u = 0) => {
      f = !0, s(u, l);
    }), f || s(-1, null);
  }, i);
}
function ws(e, t) {
  var r = void 0, n;
  mn(() => {
    r !== (r = t()) && (n && (F(n), n = null), r && (n = re(() => {
      Pr(() => (
        /** @type {(node: Element) => void} */
        r(e)
      ));
    })));
  });
}
function Dn(e) {
  var t, r, n = "";
  if (typeof e == "string" || typeof e == "number") n += e;
  else if (typeof e == "object") if (Array.isArray(e)) {
    var i = e.length;
    for (t = 0; t < i; t++) e[t] && (r = Dn(e[t])) && (n && (n += " "), n += r);
  } else for (r in e) e[r] && (n && (n += " "), n += r);
  return n;
}
function gs() {
  for (var e, t, r = 0, n = "", i = arguments.length; r < i; r++) (e = arguments[r]) && (t = Dn(e)) && (n && (n += " "), n += t);
  return n;
}
function ys(e) {
  return typeof e == "object" ? gs(e) : e ?? "";
}
const Ur = [...` 	
\r\f \v\uFEFF`];
function bs(e, t, r) {
  var n = e == null ? "" : "" + e;
  if (r) {
    for (var i of Object.keys(r))
      if (r[i])
        n = n ? n + " " + i : i;
      else if (n.length)
        for (var s = i.length, f = 0; (f = n.indexOf(i, f)) >= 0; ) {
          var l = f + s;
          (f === 0 || Ur.includes(n[f - 1])) && (l === n.length || Ur.includes(n[l])) ? n = (f === 0 ? "" : n.substring(0, f)) + n.substring(l + 1) : f = l;
        }
  }
  return n === "" ? null : n;
}
function Gr(e, t = !1) {
  var r = t ? " !important;" : ";", n = "";
  for (var i of Object.keys(e)) {
    var s = e[i];
    s != null && s !== "" && (n += " " + i + ": " + s + r);
  }
  return n;
}
function ir(e) {
  return e[0] !== "-" || e[1] !== "-" ? e.toLowerCase() : e;
}
function Es(e, t) {
  if (t) {
    var r = "", n, i;
    if (Array.isArray(t) ? (n = t[0], i = t[1]) : n = t, e) {
      e = String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g, "").trim();
      var s = !1, f = 0, l = !1, u = [];
      n && u.push(...Object.keys(n).map(ir)), i && u.push(...Object.keys(i).map(ir));
      var o = 0, v = -1;
      const w = e.length;
      for (var d = 0; d < w; d++) {
        var c = e[d];
        if (l ? c === "/" && e[d - 1] === "*" && (l = !1) : s ? s === c && (s = !1) : c === "/" && e[d + 1] === "*" ? l = !0 : c === '"' || c === "'" ? s = c : c === "(" ? f++ : c === ")" && f--, !l && s === !1 && f === 0) {
          if (c === ":" && v === -1)
            v = d;
          else if (c === ";" || d === w - 1) {
            if (v !== -1) {
              var h = ir(e.substring(o, v).trim());
              if (!u.includes(h)) {
                c !== ";" && d++;
                var _ = e.substring(o, d).trim();
                r += " " + _ + ";";
              }
            }
            o = d + 1, v = -1;
          }
        }
      }
    }
    return n && (r += Gr(n)), i && (r += Gr(i, !0)), r = r.trim(), r === "" ? null : r;
  }
  return e == null ? null : String(e);
}
function ms(e, t, r, n, i, s) {
  var f = (
    /** @type {any} */
    e[lr]
  );
  if (f !== r || f === void 0) {
    var l = bs(r, n, s);
    l == null ? e.removeAttribute("class") : t ? e.className = l : e.setAttribute("class", l), e[lr] = r;
  } else if (s && i !== s)
    for (var u in s) {
      var o = !!s[u];
      (i == null || o !== !!i[u]) && e.classList.toggle(u, o);
    }
  return s;
}
function sr(e, t = {}, r, n) {
  for (var i in r) {
    var s = r[i];
    t[i] !== s && (r[i] == null ? e.style.removeProperty(i) : e.style.setProperty(i, s, n));
  }
}
function ks(e, t, r, n) {
  var i = (
    /** @type {any} */
    e[ur]
  );
  if (i !== t) {
    var s = Es(t, n);
    s == null ? e.removeAttribute("style") : e.style.cssText = s, e[ur] = t;
  } else n && (Array.isArray(n) ? (sr(e, r?.[0], n[0]), sr(e, r?.[1], n[1], "important")) : sr(e, r, n));
  return n;
}
function Gt(e, t, r = !1) {
  if (e.multiple) {
    if (t == null)
      return;
    if (!Kr(t))
      return pi();
    for (var n of e.options)
      n.selected = t.includes(bt(n));
    return;
  }
  for (n of e.options) {
    var i = bt(n);
    if (Hi(i, t)) {
      n.selected = !0;
      return;
    }
  }
  (!r || t !== void 0) && (e.selectedIndex = -1);
}
function xn(e) {
  var t = new MutationObserver(() => {
    Gt(e, e.__value);
  });
  t.observe(e, {
    // Listen to option element changes
    childList: !0,
    subtree: !0,
    // because of <optgroup>
    // Listen to option element value attribute changes
    // (doesn't get notified of select value changes,
    // because that property is not reflected as an attribute)
    attributes: !0,
    attributeFilter: ["value"]
  }), Nr(() => {
    t.disconnect();
  });
}
function Ea(e, t, r = t) {
  var n = /* @__PURE__ */ new WeakSet(), i = !0;
  $i(e, "change", (s) => {
    var f = s ? "[selected]" : ":checked", l;
    if (e.multiple)
      l = [].map.call(e.querySelectorAll(f), bt);
    else {
      var u = e.querySelector(f) ?? // will fall back to first non-disabled option if no option is selected
      e.querySelector("option:not([disabled])");
      l = u && bt(u);
    }
    r(l), e.__value = l, b !== null && n.add(b);
  }), Pr(() => {
    var s = t();
    if (e === document.activeElement) {
      var f = (
        /** @type {Batch} */
        b
      );
      if (n.has(f))
        return;
    }
    if (Gt(e, s, i), i && s === void 0) {
      var l = e.querySelector(":checked");
      l !== null && (s = bt(l), r(s));
    }
    e.__value = s, i = !1;
  }), xn(e);
}
function bt(e) {
  return "__value" in e ? e.__value : e.value;
}
const lt = Symbol("class"), ut = Symbol("style"), Bn = Symbol("is custom element"), Hn = Symbol("is html"), Ss = Zt ? "input" : "INPUT", As = Zt ? "option" : "OPTION", Ts = Zt ? "select" : "SELECT", Os = Zt ? "progress" : "PROGRESS";
function ma(e, t) {
  var r = Qt(e);
  r.value === (r.value = // treat null and undefined the same for the initial value
  t ?? void 0) || // @ts-expect-error
  // `progress` elements always need their value set when it's `0`
  e.value === t && (t !== 0 || e.nodeName !== Os) || (e.value = t ?? "");
}
function ka(e, t) {
  var r = Qt(e);
  r.checked !== (r.checked = // treat null and undefined the same for the initial value
  t ?? void 0) && (e.checked = t);
}
function Ns(e, t) {
  t ? e.hasAttribute("selected") || e.setAttribute("selected", "") : e.removeAttribute("selected");
}
function ar(e, t, r, n) {
  var i = Qt(e);
  i[t] !== (i[t] = r) && (t === "loading" && (e[si] = r), r == null ? e.removeAttribute(t) : typeof r != "string" && Vn(e).includes(t) ? e[t] = r : e.setAttribute(t, r));
}
function Ps(e, t, r, n, i = !1, s = !1) {
  var f = Qt(e), l = f[Bn], u = !f[Hn], o = t || {}, v = e.nodeName === As;
  for (var d in t)
    d in r || (r[d] = null);
  r.class ? r.class = ys(r.class) : r[lt] && (r.class = null), r[ut] && (r.style ?? (r.style = null));
  var c = Vn(e);
  if (e.nodeName === Ss && "type" in r && ("value" in r || "__value" in r)) {
    var h = r.type;
    (h !== o.type || h === void 0 && e.hasAttribute("type")) && (o.type = h, ar(e, "type", h));
  }
  for (const S in r) {
    let O = r[S];
    if (v && S === "value" && O == null) {
      e.value = e.__value = "", o[S] = O;
      continue;
    }
    if (S === "class") {
      var _ = e.namespaceURI === "http://www.w3.org/1999/xhtml";
      ms(e, _, O, n, t?.[lt], r[lt]), o[S] = O, o[lt] = r[lt];
      continue;
    }
    if (S === "style") {
      ks(e, O, t?.[ut], r[ut]), o[S] = O, o[ut] = r[ut];
      continue;
    }
    var w = o[S];
    if (!(O === w && !(O === void 0 && e.hasAttribute(S)))) {
      o[S] = O;
      var A = S[0] + S[1];
      if (A !== "$$")
        if (A === "on") {
          const q = {}, qe = "$$" + S;
          let D = S.slice(2);
          var T = os(D);
          if (ls(D) && (D = D.slice(0, -7), q.capture = !0), !T && w) {
            if (O != null) continue;
            e.removeEventListener(D, o[qe], q), o[qe] = null;
          }
          if (T)
            ns(D, e, O), is([D]);
          else if (O != null) {
            let qn = function(Un) {
              o[S].call(this, Un);
            };
            o[qe] = jn(D, e, qn, q);
          }
        } else if (S === "style")
          ar(e, S, O);
        else if (S === "autofocus")
          Gi(
            /** @type {HTMLElement} */
            e,
            !!O
          );
        else if (!l && (S === "__value" || S === "value" && O != null))
          e.value = e.__value = O;
        else if (S === "selected" && v)
          Ns(
            /** @type {HTMLOptionElement} */
            e,
            O
          );
        else {
          var P = S;
          u || (P = hs(P));
          var Ve = P === "defaultValue" || P === "defaultChecked";
          if (O == null && !l && !Ve)
            if (f[S] = null, P === "value" || P === "checked") {
              let q = (
                /** @type {HTMLInputElement} */
                e
              );
              const qe = t === void 0;
              if (P === "value") {
                let D = q.defaultValue;
                q.removeAttribute(P), q.defaultValue = D, q.value = q.__value = qe ? D : null;
              } else {
                let D = q.defaultChecked;
                q.removeAttribute(P), q.defaultChecked = D, q.checked = qe ? D : !1;
              }
            } else
              e.removeAttribute(S);
          else Ve || c.includes(P) && (l || typeof O != "string") ? (e[P] = O, P in f && (f[P] = M)) : typeof O != "function" && ar(e, P, O);
        }
    }
  }
  return o;
}
function Sa(e, t, r = [], n = [], i = [], s, f = !1, l = !1) {
  an(i, r, n, (u) => {
    var o = void 0, v = {}, d = e.nodeName === Ts, c = !1;
    if (mn(() => {
      var _ = t(...u.map(ke)), w = Ps(
        e,
        o,
        _,
        s,
        f,
        l
      );
      c && d && "value" in _ && Gt(
        /** @type {HTMLSelectElement} */
        e,
        _.value
      );
      for (let T of Object.getOwnPropertySymbols(v))
        _[T] || F(v[T]);
      for (let T of Object.getOwnPropertySymbols(_)) {
        var A = _[T];
        T.description === Wn && (!o || A !== o[T]) && (v[T] && F(v[T]), v[T] = re(() => ws(e, () => A))), w[T] = A;
      }
      o = w;
    }), d) {
      var h = (
        /** @type {HTMLSelectElement} */
        e
      );
      Pr(() => {
        Gt(
          h,
          /** @type {Record<string | symbol, any>} */
          o.value,
          !0
        ), xn(h);
      });
    }
    c = !0;
  });
}
function Qt(e) {
  return (
    /** @type {Record<string | symbol, unknown>} **/
    /** @type {any} */
    e[Rt] ?? (e[Rt] = {
      [Bn]: e.nodeName.includes("-"),
      [Hn]: e.namespaceURI === zr
    })
  );
}
var Yr = /* @__PURE__ */ new Map();
function Vn(e) {
  var t = e.getAttribute("is") || e.nodeName, r = Yr.get(t);
  if (r) return r;
  Yr.set(t, r = []);
  for (var n, i = e, s = Element.prototype; s !== i; ) {
    n = Xn(i);
    for (var f in n)
      n[f].set && // better safe than sorry, we don't want spread attributes to mess with HTML content
      f !== "innerHTML" && f !== "textContent" && f !== "innerText" && r.push(f);
    i = Zr(i);
  }
  return r;
}
class ze extends Error {
  constructor(t) {
    super(t.message || t.code || "ApiError"), this.code = t.code || "unknown", this.shortCode = t.short_code || t.code || "unknown", this.summary = t.summary || "", this.logTail = Array.isArray(t.log_tail) ? t.log_tail : [], this.status = t.status || 0;
  }
}
async function er(e, t) {
  let r;
  try {
    r = await fetch(e, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(t ?? {})
    });
  } catch (i) {
    throw new ze({
      code: "network_error",
      short_code: "NET",
      message: i?.message || "Network error",
      status: 0
    });
  }
  let n;
  try {
    n = await r.json();
  } catch {
    throw new ze({
      code: "http_error",
      short_code: "HTTP",
      message: `HTTP ${r.status}`,
      status: r.status
    });
  }
  if (!n.ok) {
    const i = n.error || { code: "unknown", message: "Unknown error" };
    throw new ze({ ...i, status: r.status });
  }
  return n.data;
}
function Rs(e) {
  return !!e && typeof e == "object" && e.async === !0;
}
async function Aa(e, t, r = {}) {
  if (!Rs(t)) return t;
  const n = r.intervalMs ?? 800;
  for (; ; ) {
    await new Promise((f) => setTimeout(f, n));
    let i;
    try {
      i = await er("/api/job-progress", { job_workspace: e });
    } catch {
      continue;
    }
    r.onProgress?.(i);
    const s = i.job;
    if (s) {
      if (s.state === "succeeded") {
        const f = s.result;
        if (f && f.ok === !1)
          throw new ze(f.error || { code: "run_failed", message: "Run failed" });
        return f?.data ?? {};
      }
      if (s.state === "failed")
        throw new ze({ code: "run_failed", message: s.error || "Run failed" });
      if (s.state === "cancelled")
        throw new ze({ code: "cancelled", message: "Run was cancelled." });
    }
  }
}
function Ms() {
  const e = window;
  return !!(e.pywebview && e.pywebview.api && e.pywebview.api.pick_file);
}
async function Ta(e) {
  if (Ms())
    try {
      const r = await window.pywebview.api.pick_file(e ?? null);
      if (r && (r.path || r.cancelled)) return r;
    } catch (t) {
      return { ok: !1, error: t?.message || String(t) };
    }
  try {
    const t = await er("/api/pick-file", {
      filters: e ?? null
    });
    return t?.cancelled ? { ok: !0, cancelled: !0 } : { ok: !0, path: t?.path || "" };
  } catch (t) {
    return { ok: !1, error: t?.message || String(t) };
  }
}
async function Cs(e) {
  const t = window.pywebview?.api;
  if (!t?.pick_file) return { ok: !1, unavailable: !0 };
  try {
    return await t.pick_file(e || null) || { ok: !1, error: "empty_response" };
  } catch (r) {
    return { ok: !1, error: r?.message || String(r) };
  }
}
async function Is(e) {
  const t = window.pywebview?.api;
  if (typeof t?.pick_files != "function") return { ok: !1, unavailable: !0 };
  try {
    return await t.pick_files(e || null) || { ok: !1, error: "empty_response" };
  } catch (r) {
    return { ok: !1, error: r?.message || String(r) };
  }
}
async function Ls(e) {
  try {
    return { ok: !0, ...await er("/api/pick-file", { filters: e }) };
  } catch (t) {
    return { ok: !1, error: t?.message || String(t) };
  }
}
async function Fs(e) {
  try {
    return { ok: !0, ...await er("/api/pick-files", { filters: e }) };
  } catch (t) {
    return { ok: !1, error: t?.message || String(t) };
  }
}
function js(e) {
  return !e || e.unavailable === !0 ? !1 : e.ok === !0 && (!!e.path || e.cancelled === !0);
}
function Ds(e) {
  return !e || e.unavailable === !0 ? !1 : e.ok === !0 && Array.isArray(e.paths) && e.paths.length > 0 ? !0 : e.ok === !0 && e.cancelled === !0;
}
async function Oa(e = {}) {
  const { filters: t = null, fallbackInput: r = null } = e, n = await Cs(t);
  if (js(n)) return n;
  const i = await Ls(t);
  return i.ok ? i : r ? (r.click(), { ok: !0, browser_fallback: !0 }) : i.ok === !1 ? i : n;
}
async function Na(e = {}) {
  const { filters: t = null, fallbackInput: r = null } = e, n = await Is(t);
  if (Ds(n)) return n;
  const i = await Fs(t);
  return i.ok ? i : r ? (r.click(), { ok: !0, browser_fallback: !0 }) : i.ok === !1 ? i : n;
}
export {
  pt as $,
  ze as A,
  ga as B,
  ya as C,
  Pr as D,
  Ui as E,
  E as F,
  Ut as G,
  qt as H,
  Qi as I,
  Ks as J,
  ma as K,
  ha as L,
  Na as M,
  Ws as N,
  Oa as O,
  ks as P,
  xn as Q,
  Gt as R,
  ti as S,
  Sa as T,
  ys as U,
  Aa as V,
  rs as W,
  Ta as X,
  V as Y,
  Ji as Z,
  Ir as _,
  pa as a,
  $i as a0,
  b as a1,
  ca as a2,
  Ns as a3,
  it as a4,
  En as a5,
  Vt as a6,
  re as a7,
  ea as a8,
  qi as a9,
  Oe as aA,
  $s as aB,
  Gs as aC,
  kr as aD,
  zs as aE,
  Xs as aF,
  Vs as aa,
  na as ab,
  Hs as ac,
  Ot as ad,
  Bs as ae,
  Us as af,
  ia as ag,
  Kr as ah,
  Zn as ai,
  Js as aj,
  le as ak,
  Br as al,
  yt as am,
  X as an,
  Ae as ao,
  oe as ap,
  qs as aq,
  la as ar,
  On as as,
  F as at,
  Jt as au,
  rt as av,
  ps as aw,
  _t as ax,
  ta as ay,
  Ys as az,
  Ei as b,
  er as c,
  is as d,
  Ne as e,
  aa as f,
  ke as g,
  sa as h,
  ba as i,
  wa as j,
  _a as k,
  fa as l,
  ns as m,
  da as n,
  va as o,
  bi as p,
  ms as q,
  ar as r,
  ye as s,
  oa as t,
  ra as u,
  Zs as v,
  vt as w,
  ua as x,
  Ea as y,
  ka as z
};
//# sourceMappingURL=api-vHpIWCot.js.map
