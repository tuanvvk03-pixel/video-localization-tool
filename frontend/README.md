# Frontend (Svelte + TypeScript) — incremental rewrite foundation

This is the **strangler-fig** foundation for migrating the desktop UI off the
hand-rolled vanilla JS in `desktop/static/` one screen at a time, **without a
big-bang rewrite**. The legacy app keeps running; new screens are authored in
Svelte + TS, compiled to self-contained ES modules, and mounted by the existing
`app.js` router through its `mount(host, ctx)` / `unmount()` interface.

## Layout

```
frontend/
  src/
    lib/
      api.ts       typed client for the {ok,data}/{ok,error} backend contract
      types.ts     API contract types (JobProgress, JobRecord, …)
      screen.ts    Screen interface + screenFromComponent() Svelte bridge
    screens/       *.svelte screens (one per UI screen as they migrate)
    entries/       *.ts build entries that export mount/unmount per screen
  vite.config.ts   library build → ../desktop/static/next/<entry>.js
```

## Build

```bash
cd frontend
npm install
npm run build      # one-shot → desktop/static/next/*.js (committed)
npm run dev        # rebuild on change (vite build --watch)
npm run check      # svelte-check (types)
```

The Svelte runtime and scoped CSS are bundled into each output module
(`emitCss:false`), so the Python server serves them with no extra steps. Built
output under `desktop/static/next/` **is committed** so the app runs without a
build; `node_modules/` is not.

## Verify (Playwright E2E)

```bash
npm run e2e        # boots the Python server, runs browser tests, tears it down
```

`e2e/diagnostics.spec.ts` loads the real app in Chromium against the real server
and asserts the migrated Svelte screen mounts through the legacy `app.js` router
(strangler-fig) with no page errors — proving the build → serve → mount pipeline
end to end. Add a spec per screen as it migrates. (First run needs the browser:
`npx playwright install chromium`.)

## Migrate a screen (strangler step)

1. Create `src/screens/Foo.svelte` (props: `{ ctx }`) and port the legacy
   `screens/foo.js` markup/logic, calling the typed `api.ts` helpers.
2. Add `src/entries/foo.ts`:
   ```ts
   import Foo from "../screens/Foo.svelte";
   import { screenFromComponent } from "../lib/screen";
   const s = screenFromComponent(Foo);
   export const mount = s.mount;
   export const unmount = s.unmount;
   ```
3. Add `foo` to `lib.entry` in `vite.config.ts`, `npm run build`.
4. In `desktop/static/app.js`, swap the screen's import to the built module:
   ```js
   import { mount as mountFoo, unmount as unmountFoo } from "./next/foo.js";
   ```
   Verify in the running app, then delete the legacy `screens/foo.js`.

Suggested order by ROI: `settings` (2876 lines) → `review` (subtitle editor —
the product core, invest in a virtualized cue list) → `render` → `import` → rest.
