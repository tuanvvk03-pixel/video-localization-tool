// Build entry → ../desktop/static/next/settings.js (router mount/unmount).
import Settings from "../screens/settings/Settings.svelte";
import { screenFromComponent } from "../lib/screen";

const screen = screenFromComponent(Settings);

export const mount = screen.mount;
export const unmount = screen.unmount;
