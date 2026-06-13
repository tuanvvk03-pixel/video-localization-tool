import { T as c, t as l, P as v, g as n, a as f, u as m, h as _, n as g } from "./api-vHpIWCot.js";
import { p as t, r as h } from "./Button-GpBM5g0S.js";
var u = /* @__PURE__ */ new Set(["$$slots", "$$events", "$$legacy", "percent", "wide"]), w = g('<div><div class="fill"></div></div>');
function $(r, e) {
  let a = t(e, "percent", 3, 0), i = t(e, "wide", 3, !1), d = h(e, u);
  const o = m(() => Math.max(0, Math.min(100, Number(a()) || 0)));
  var s = w();
  c(s, () => ({
    class: i() ? "progress progress--wide" : "progress",
    ...d
  }));
  var p = _(s);
  l(() => v(p, `width:${n(o) ?? ""}%`)), f(r, s);
}
export {
  $ as P
};
//# sourceMappingURL=ProgressBar-BACn-l7Z.js.map
