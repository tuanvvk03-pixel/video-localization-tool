// Build entry: compiled to ../desktop/static/next/demo.js, exporting the
// router's mount/unmount interface. app.js can register it like a legacy screen:
//
//   import { mount, unmount } from "./next/demo.js";
//
import Demo from "../screens/Demo.svelte";
import { screenFromComponent } from "../lib/screen";

const screen = screenFromComponent(Demo);

export const mount = screen.mount;
export const unmount = screen.unmount;
