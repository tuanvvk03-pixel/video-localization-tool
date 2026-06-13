// Build entry → ../desktop/static/next/app_settings.js (router mount/unmount).
import AppSettings from "../screens/app_settings/AppSettings.svelte";
import { screenFromComponent } from "../lib/screen";

const screen = screenFromComponent(AppSettings);

export const mount = screen.mount;
export const unmount = screen.unmount;
