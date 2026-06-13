<script lang="ts">
  // Faithful wrapper of the global `.status` pill. `kind` is the lifecycle
  // modifier ("completed" | "running" | "blocked" | "queued" | …). Extra attrs
  // flow through via ...rest. Emitted markup matches the hand-written spans.
  import type { Snippet } from "svelte";

  let {
    kind = "",
    children,
    ...rest
  }: { kind?: string; children?: Snippet; [key: string]: unknown } = $props();
</script>

<span class={kind ? `status ${kind}` : "status"} {...rest}>{@render children?.()}</span>
