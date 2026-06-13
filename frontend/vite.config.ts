import { resolve } from "node:path";
import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

// Each file under src/entries/*.ts is built into a self-contained ES module
// under ../desktop/static/next/<name>.js that exports `mount(host, ctx)` and
// `unmount()`. The existing vanilla app.js router imports those exactly like a
// legacy screen, so screens can migrate to Svelte one at a time (strangler-fig)
// without a big-bang rewrite. The Svelte runtime is bundled in (not external),
// so the Python server can serve the output with no extra dependencies.
export default defineConfig({
  // emitCss:false makes each component inject its scoped styles via JS at mount,
  // so the built screen module is fully self-contained (no separate .css to load).
  plugins: [svelte({ emitCss: false })],
  build: {
    outDir: resolve(__dirname, "../desktop/static/next"),
    emptyOutDir: true,
    target: "es2020",
    sourcemap: true,
    // Library mode: preserve each entry's exports (mount/unmount) as the public
    // API and bundle the Svelte runtime in, so each output is a self-contained
    // ES module the Python server can serve directly.
    lib: {
      entry: {
        demo: resolve(__dirname, "src/entries/demo.ts"),
        diagnostics: resolve(__dirname, "src/entries/diagnostics.ts"),
        settings: resolve(__dirname, "src/entries/settings.ts"),
        review: resolve(__dirname, "src/entries/review.ts"),
        import: resolve(__dirname, "src/entries/import.ts"),
        render: resolve(__dirname, "src/entries/render.ts"),
        download: resolve(__dirname, "src/entries/download.ts"),
        auth: resolve(__dirname, "src/entries/auth.ts"),
        account: resolve(__dirname, "src/entries/account.ts"),
        app_settings: resolve(__dirname, "src/entries/app_settings.ts"),
      },
      formats: ["es"],
    },
    rollupOptions: {
      output: {
        entryFileNames: "[name].js",
        chunkFileNames: "chunks/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash][extname]",
      },
    },
  },
});
