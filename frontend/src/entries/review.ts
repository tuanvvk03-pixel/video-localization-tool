// Build entry → ../desktop/static/next/review.js (router mount/unmount).
import Review from "../screens/review/Review.svelte";
import { screenFromComponent } from "../lib/screen";

const screen = screenFromComponent(Review);

export const mount = screen.mount;
export const unmount = screen.unmount;
