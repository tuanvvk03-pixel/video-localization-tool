<script lang="ts">
  // Faithful wrapper of the global `.btn` style used across every screen.
  // `variant` appends the modifier ("primary" | "secondary" | "strong" | ""),
  // and everything else (onclick, disabled, data-testid, title, style, …) flows
  // through via ...rest, so the emitted markup matches the hand-written buttons
  // it replaces — the look is unchanged by construction.
  import type { Snippet } from "svelte";

  // `class` is merged after the variant (e.g. <Button class="auth-submit"> →
  // "btn primary auth-submit"), so an extra style hook never clobbers `.btn`.
  let {
    variant = "",
    class: extra = "",
    children,
    ...rest
  }: { variant?: string; class?: string; children?: Snippet; [key: string]: unknown } = $props();

  const cls = $derived(["btn", variant, extra].filter(Boolean).join(" "));
</script>

<button type="button" class={cls} {...rest}>{@render children?.()}</button>
