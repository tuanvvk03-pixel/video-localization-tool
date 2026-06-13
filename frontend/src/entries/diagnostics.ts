// Build entry → ../desktop/static/next/diagnostics.js, exposing the router's
// mount/unmount. Replaces the legacy screens/diagnostics.js once verified.
import Diagnostics from "../screens/Diagnostics.svelte";
import { screenFromComponent } from "../lib/screen";

const screen = screenFromComponent(Diagnostics);

export const mount = screen.mount;
export const unmount = screen.unmount;
