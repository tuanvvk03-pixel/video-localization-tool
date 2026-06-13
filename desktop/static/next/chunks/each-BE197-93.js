import { a4 as N, a5 as J, g as O, a6 as q, a1 as K, a7 as z, a8 as P, a9 as Q, aa as V, ab as W, ac as Z, ad as L, ae as $, af as j, ag as y, ah as ee, ai as H, aj as C, ak as ne, al as U, am as X, an as R, ao as re, ap as fe, aq as ae, ar as ie, as as le, at as ue, au as oe } from "./api-vHpIWCot.js";
function pe(e, r) {
  return r;
}
function se(e, r, l) {
  for (var s = [], c = r.length, i, u = r.length, p = 0; p < c; p++) {
    let E = r[p];
    X(
      E,
      () => {
        if (i) {
          if (i.pending.delete(E), i.done.add(E), i.pending.size === 0) {
            var v = (
              /** @type {Set<EachOutroGroup>} */
              e.outrogroups
            );
            D(e, H(i.done)), v.delete(i), v.size === 0 && (e.outrogroups = null);
          }
        } else
          u -= 1;
      },
      !1
    );
  }
  if (u === 0) {
    var a = s.length === 0 && l !== null;
    if (a) {
      var t = (
        /** @type {Element} */
        l
      ), f = (
        /** @type {Element} */
        t.parentNode
      );
      ie(f), f.append(t), e.items.clear();
    }
    D(e, r, !a);
  } else
    i = {
      pending: new Set(r),
      done: /* @__PURE__ */ new Set()
    }, (e.outrogroups ?? (e.outrogroups = /* @__PURE__ */ new Set())).add(i);
}
function D(e, r, l = !0) {
  var s;
  if (e.pending.size > 0) {
    s = /* @__PURE__ */ new Set();
    for (const u of e.pending.values())
      for (const p of u)
        s.add(
          /** @type {EachItem} */
          e.items.get(p).e
        );
  }
  for (var c = 0; c < r.length; c++) {
    var i = r[c];
    if (s?.has(i)) {
      i.f |= C;
      const u = document.createDocumentFragment();
      le(i, u);
    } else
      ue(r[c], l);
  }
}
var B;
function te(e, r, l, s, c, i = null) {
  var u = e, p = /* @__PURE__ */ new Map(), a = (r & V) !== 0;
  if (a) {
    var t = (
      /** @type {Element} */
      e
    );
    u = t.appendChild(N());
  }
  var f = null, E = W(() => {
    var d = l();
    return (
      /** @type {V[]} */
      ee(d) ? d : d == null ? [] : H(d)
    );
  }), v, m = /* @__PURE__ */ new Map(), w = !0;
  function I(d) {
    (A.effect.f & ne) === 0 && (A.pending.delete(d), A.fallback = f, ve(A, v, u, r, s), f !== null && (v.length === 0 ? (f.f & C) === 0 ? U(f) : (f.f ^= C, M(f, null, u)) : X(f, () => {
      f = null;
    })));
  }
  function n(d) {
    A.pending.delete(d);
  }
  var o = J(() => {
    v = /** @type {V[]} */
    O(E);
    for (var d = v.length, h = /* @__PURE__ */ new Set(), S = (
      /** @type {Batch} */
      K
    ), x = Q(), _ = 0; _ < d; _ += 1) {
      var k = v[_], b = s(k, _), g = w ? null : p.get(b);
      g ? (g.v && q(g.v, k), g.i && q(g.i, _), x && S.unskip_effect(g.e)) : (g = de(
        p,
        w ? u : B ?? (B = N()),
        k,
        b,
        _,
        c,
        r,
        l
      ), w || (g.e.f |= C), p.set(b, g)), h.add(b);
    }
    if (d === 0 && i && !f && (w ? f = z(() => i(u)) : (f = z(() => i(B ?? (B = N()))), f.f |= C)), d > h.size && P(), !w)
      if (m.set(S, h), x) {
        for (const [Y, G] of p)
          h.has(Y) || S.skip_effect(G.e);
        S.oncommit(I), S.ondiscard(n);
      } else
        I(S);
    O(E);
  }), A = { effect: o, items: p, pending: m, outrogroups: null, fallback: f };
  w = !1;
}
function F(e) {
  for (; e !== null && (e.f & fe) === 0; )
    e = e.next;
  return e;
}
function ve(e, r, l, s, c) {
  var i = (s & ae) !== 0, u = r.length, p = e.items, a = F(e.effect.first), t, f = null, E, v = [], m = [], w, I, n, o;
  if (i)
    for (o = 0; o < u; o += 1)
      w = r[o], I = c(w, o), n = /** @type {EachItem} */
      p.get(I).e, (n.f & C) === 0 && (n.nodes?.a?.measure(), (E ?? (E = /* @__PURE__ */ new Set())).add(n));
  for (o = 0; o < u; o += 1) {
    if (w = r[o], I = c(w, o), n = /** @type {EachItem} */
    p.get(I).e, e.outrogroups !== null)
      for (const g of e.outrogroups)
        g.pending.delete(n), g.done.delete(n);
    if ((n.f & R) !== 0 && (U(n), i && (n.nodes?.a?.unfix(), (E ?? (E = /* @__PURE__ */ new Set())).delete(n))), (n.f & C) !== 0)
      if (n.f ^= C, n === a)
        M(n, null, l);
      else {
        var A = f ? f.next : a;
        n === e.effect.last && (e.effect.last = n.prev), n.prev && (n.prev.next = n.next), n.next && (n.next.prev = n.prev), T(e, f, n), T(e, n, A), M(n, A, l), f = n, v = [], m = [], a = F(f.next);
        continue;
      }
    if (n !== a) {
      if (t !== void 0 && t.has(n)) {
        if (v.length < m.length) {
          var d = m[0], h;
          f = d.prev;
          var S = v[0], x = v[v.length - 1];
          for (h = 0; h < v.length; h += 1)
            M(v[h], d, l);
          for (h = 0; h < m.length; h += 1)
            t.delete(m[h]);
          T(e, S.prev, x.next), T(e, f, S), T(e, x, d), a = d, f = x, o -= 1, v = [], m = [];
        } else
          t.delete(n), M(n, a, l), T(e, n.prev, n.next), T(e, n, f === null ? e.effect.first : f.next), T(e, f, n), f = n;
        continue;
      }
      for (v = [], m = []; a !== null && a !== n; )
        (t ?? (t = /* @__PURE__ */ new Set())).add(a), m.push(a), a = F(a.next);
      if (a === null)
        continue;
    }
    (n.f & C) === 0 && v.push(n), f = n, a = F(n.next);
  }
  if (e.outrogroups !== null) {
    for (const g of e.outrogroups)
      g.pending.size === 0 && (D(e, H(g.done)), e.outrogroups?.delete(g));
    e.outrogroups.size === 0 && (e.outrogroups = null);
  }
  if (a !== null || t !== void 0) {
    var _ = [];
    if (t !== void 0)
      for (n of t)
        (n.f & R) === 0 && _.push(n);
    for (; a !== null; )
      (a.f & R) === 0 && a !== e.fallback && _.push(a), a = F(a.next);
    var k = _.length;
    if (k > 0) {
      var b = (s & V) !== 0 && u === 0 ? l : null;
      if (i) {
        for (o = 0; o < k; o += 1)
          _[o].nodes?.a?.measure();
        for (o = 0; o < k; o += 1)
          _[o].nodes?.a?.fix();
      }
      se(e, _, b);
    }
  }
  i && re(() => {
    if (E !== void 0)
      for (n of E)
        n.nodes?.a?.apply();
  });
}
function de(e, r, l, s, c, i, u, p) {
  var a = (u & $) !== 0 ? (u & j) === 0 ? y(l, !1, !1) : L(l) : null, t = (u & Z) !== 0 ? L(c) : null;
  return {
    v: a,
    i: t,
    e: z(() => (i(r, a ?? l, t ?? c, p), () => {
      e.delete(s);
    }))
  };
}
function M(e, r, l) {
  if (e.nodes)
    for (var s = e.nodes.start, c = e.nodes.end, i = r && (r.f & C) === 0 ? (
      /** @type {EffectNodes} */
      r.nodes.start
    ) : l; s !== null; ) {
      var u = (
        /** @type {TemplateNode} */
        oe(s)
      );
      if (i.before(s), s === c)
        return;
      s = u;
    }
}
function T(e, r, l) {
  r === null ? e.effect.first = l : r.next = l, l === null ? e.effect.last = r : l.prev = r;
}
export {
  te as e,
  pe as i
};
//# sourceMappingURL=each-BE197-93.js.map
