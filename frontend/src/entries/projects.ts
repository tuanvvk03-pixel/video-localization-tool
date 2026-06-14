// Build entry → ../desktop/static/next/projects.js (router mount/unmount).
import Projects from "../screens/projects/Projects.svelte";
import { screenFromComponent } from "../lib/screen";

const screen = screenFromComponent(Projects);

export const mount = screen.mount;
export const unmount = screen.unmount;
