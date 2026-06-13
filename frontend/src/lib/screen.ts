// Bridge between Svelte components and the legacy app.js router, whose screens
// are plain objects with `mount(host, ctx)` / `unmount()`. screenFromComponent
// wraps a Svelte 5 component so a migrated screen plugs into that exact
// interface — the strangler-fig seam.

import { mount as svelteMount, unmount as svelteUnmount } from "svelte";
import type { Component } from "svelte";

/** The shared app context the legacy router passes to every screen. */
export interface ScreenCtx {
  navigate: (name: string, options?: Record<string, unknown>) => void;
  /** Shared i18n translator from the app (desktop/static/i18n/i18n.js). */
  t: (key: string, vars?: Record<string, unknown>) => string;
  /** Current UI language code ("vi" | "en"), from the shared i18n module. */
  getLang?: () => string;
  /** Sync the edit-wizard gate after a run (shared editWizardGate.js). */
  applyJobStatusToEditGate?: (ctx: ScreenCtx, statusData: Record<string, unknown>) => void;
  jobWorkspace?: string;
  parentProject?: string;
  parentProjectRoot?: string;
  importConfig?: { job_workspace: string; [k: string]: unknown } | null;
  [key: string]: unknown;
}

export interface Screen {
  mount(host: HTMLElement, ctx: ScreenCtx): void;
  unmount(): void;
}

/** Adapt a Svelte component (props: { ctx }) into a router Screen. */
export function screenFromComponent(
  Comp: Component<{ ctx: ScreenCtx }>,
): Screen {
  let app: ReturnType<typeof svelteMount> | null = null;
  return {
    mount(host: HTMLElement, ctx: ScreenCtx) {
      host.replaceChildren();
      app = svelteMount(Comp, { target: host, props: { ctx } });
    },
    unmount() {
      if (app) {
        svelteUnmount(app);
        app = null;
      }
    },
  };
}
