import { Y as u, D as h, Z as o, W as S, F as T, _ as Y, $ as b } from "./api-vHpIWCot.js";
function n(r, s) {
  return r === s || r?.[b] === s;
}
function v(r = {}, s, i, e) {
  var c = (
    /** @type {ComponentContext} */
    u.r
  ), d = (
    /** @type {Effect} */
    T
  );
  return h(() => {
    var f, a;
    return o(() => {
      f = a, a = [], S(() => {
        n(i(...a), r) || (s(r, ...a), f && n(i(...f), r) && s(null, ...f));
      });
    }), () => {
      let t = d;
      for (; t !== c && t.parent !== null && t.parent.f & Y; )
        t = t.parent;
      const p = () => {
        a && n(i(...a), r) && s(null, ...a);
      }, w = t.teardown;
      t.teardown = () => {
        p(), w?.();
      };
    };
  }), r;
}
export {
  v as b
};
//# sourceMappingURL=this-_Wc-LPs7.js.map
