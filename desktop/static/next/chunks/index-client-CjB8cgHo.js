import { Y as e, x as f, W as t } from "./api-vHpIWCot.js";
function c(n) {
  throw new Error("https://svelte.dev/e/lifecycle_outside_component");
}
function u(n) {
  e === null && c(), f(() => {
    const o = t(n);
    if (typeof o == "function") return (
      /** @type {() => void} */
      o
    );
  });
}
function r(n) {
  e === null && c(), u(() => () => t(n));
}
export {
  r as o
};
//# sourceMappingURL=index-client-CjB8cgHo.js.map
