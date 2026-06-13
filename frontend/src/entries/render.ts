// Build entry → ../desktop/static/next/render.js (router mount/unmount).
import Render from "../screens/render/Render.svelte";
import { screenFromComponent } from "../lib/screen";

const screen = screenFromComponent(Render);

export const mount = screen.mount;
export const unmount = screen.unmount;
