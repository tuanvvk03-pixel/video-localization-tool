/** Lets child screens refresh the Edit wizard shell (stepper) without importing edit.js. */

let _refresh = () => {};

export function registerEditShellRefresh(fn) {
  _refresh = typeof fn === "function" ? fn : () => {};
}

export function requestEditShellRefresh() {
  _refresh();
}
