import { a0 as k, a1 as f, a2 as h, W as _, Z as b } from "./api-vHpIWCot.js";
function i(e, a, v = a) {
  var c = /* @__PURE__ */ new WeakSet();
  k(e, "input", async (r) => {
    var l = r ? e.defaultValue : e.value;
    if (l = s(e) ? n(l) : l, v(l), f !== null && c.add(f), await h(), l !== (l = a())) {
      var u = e.selectionStart, o = e.selectionEnd, t = e.value.length;
      if (e.value = l ?? "", o !== null) {
        var d = e.value.length;
        u === o && o === t && d > t ? (e.selectionStart = d, e.selectionEnd = d) : (e.selectionStart = u, e.selectionEnd = Math.min(o, d));
      }
    }
  }), // If we are hydrating and the value has since changed,
  // then use the updated value from the input instead.
  // If defaultValue is set, then value == defaultValue
  // TODO Svelte 6: remove input.value check and set to empty string?
  _(a) == null && e.value && (v(s(e) ? n(e.value) : e.value), f !== null && c.add(f)), b(() => {
    var r = a();
    if (e === document.activeElement) {
      var l = (
        /** @type {Batch} */
        f
      );
      if (c.has(l))
        return;
    }
    s(e) && r === n(e.value) || e.type === "date" && !r && !e.value || r !== e.value && (e.value = r ?? "");
  });
}
function y(e, a, v = a) {
  k(e, "change", (c) => {
    var r = c ? e.defaultChecked : e.checked;
    v(r);
  }), // If we are hydrating and the value has since changed,
  // then use the update value from the input instead.
  // If defaultChecked is set, then checked == defaultChecked
  _(a) == null && v(e.checked), b(() => {
    var c = a();
    e.checked = !!c;
  });
}
function s(e) {
  var a = e.type;
  return a === "number" || a === "range";
}
function n(e) {
  return e === "" ? null : +e;
}
export {
  y as a,
  i as b
};
//# sourceMappingURL=input-D0G7l_P3.js.map
