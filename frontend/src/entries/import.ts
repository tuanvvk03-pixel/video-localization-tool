// Build entry → ../desktop/static/next/import.js (router mount/unmount).
import Import from "../screens/import/Import.svelte";
import { screenFromComponent } from "../lib/screen";

const screen = screenFromComponent(Import);

export const mount = screen.mount;
export const unmount = screen.unmount;
