// Build entry → ../desktop/static/next/download.js (router mount/unmount).
import Download from "../screens/download/Download.svelte";
import { screenFromComponent } from "../lib/screen";

const screen = screenFromComponent(Download);

export const mount = screen.mount;
export const unmount = screen.unmount;
