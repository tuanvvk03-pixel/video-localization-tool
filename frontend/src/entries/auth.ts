// Build entry → ../desktop/static/next/auth.js. The login gate isn't a normal
// router screen: app.js mounts it with an `onAuthed` callback (not a ctx), so
// this entry exposes a bespoke mount(host, { onAuthed }) / unmount() instead of
// the screenFromComponent bridge.
import { mount as svelteMount, unmount as svelteUnmount } from "svelte";
import AuthForm from "../screens/auth/AuthForm.svelte";

let app: ReturnType<typeof svelteMount> | null = null;

export function mount(host: HTMLElement, opts: { onAuthed?: () => void } = {}): void {
  host.replaceChildren();
  app = svelteMount(AuthForm, { target: host, props: { onAuthed: opts.onAuthed ?? (() => {}) } });
}

export function unmount(): void {
  if (app) {
    svelteUnmount(app);
    app = null;
  }
}
