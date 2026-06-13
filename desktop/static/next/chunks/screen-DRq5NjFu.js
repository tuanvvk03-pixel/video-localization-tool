import { B as e, C as u } from "./api-vHpIWCot.js";
function p(r) {
  let n = null;
  return {
    mount(o, t) {
      o.replaceChildren(), n = e(r, { target: o, props: { ctx: t } });
    },
    unmount() {
      n && (u(n), n = null);
    }
  };
}
export {
  p as s
};
//# sourceMappingURL=screen-DRq5NjFu.js.map
