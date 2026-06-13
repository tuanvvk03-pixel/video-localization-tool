<script lang="ts">
  import { post } from "../lib/api";
  import type { ScreenCtx } from "../lib/screen";

  let { ctx }: { ctx: ScreenCtx } = $props();

  let status = $state<"idle" | "loading" | "ok" | "error">("idle");
  let detail = $state("");

  async function ping() {
    status = "loading";
    detail = "";
    try {
      const data = await post<{ status?: string }>("/api/ping", {});
      status = "ok";
      detail = data?.status ? `server: ${data.status}` : "pong";
    } catch (e) {
      status = "error";
      detail = (e as Error)?.message || "request failed";
    }
  }

  // Auto-ping on mount so the screen demonstrates a live backend call.
  $effect(() => {
    void ping();
  });
</script>

<section class="next-demo">
  <h2>Svelte foundation — live</h2>
  <p class="muted">
    This screen is compiled from <code>frontend/src/screens/Demo.svelte</code>
    and mounted by the legacy router via the <code>mount/unmount</code> bridge.
  </p>
  <div class="row">
    <button onclick={ping} disabled={status === "loading"}>
      {status === "loading" ? "Pinging…" : "Ping backend"}
    </button>
    <span class="badge" data-state={status}>{status}{detail ? ` · ${detail}` : ""}</span>
  </div>
  {#if ctx?.jobWorkspace}
    <p class="muted">workspace: {ctx.jobWorkspace}</p>
  {/if}
</section>

<style>
  .next-demo { padding: 16px; font-family: system-ui, sans-serif; }
  .muted { color: #888; font-size: 0.9em; }
  .row { display: flex; gap: 12px; align-items: center; margin: 12px 0; }
  .badge { padding: 2px 8px; border-radius: 6px; background: #eee; }
  .badge[data-state="ok"] { background: #d6f5d6; }
  .badge[data-state="error"] { background: #f5d6d6; }
  .badge[data-state="loading"] { background: #f5efd6; }
</style>
