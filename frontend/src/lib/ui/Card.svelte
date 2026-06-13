<script lang="ts">
  // Faithful wrapper of the standard `.card` with the common
  // header (`.card-header` → `.card-title` / `.card-sub`) + `.card-body` layout.
  // Pass `title`/`sub` for the header, `headerRight` snippet for a right-aligned
  // header node (e.g. a status pill or checkbox), `bodyClass` for body modifiers
  // ("stack", "card-body--scroll", …), and the default children as the body.
  // The header is omitted entirely when there is no title/sub/headerRight, so
  // cards that render a bespoke body (e.g. an empty-state) still match.
  import type { Snippet } from "svelte";

  let {
    title = "",
    sub = "",
    bodyClass = "",
    headerRight,
    children,
    ...rest
  }: {
    title?: string;
    sub?: string;
    bodyClass?: string;
    headerRight?: Snippet;
    children?: Snippet;
    [key: string]: unknown;
  } = $props();
</script>

<div class="card" {...rest}>
  {#if title || sub || headerRight}
    <div class="card-header">
      <div>
        {#if title}<div class="card-title">{title}</div>{/if}
        {#if sub}<div class="card-sub">{sub}</div>{/if}
      </div>
      {#if headerRight}{@render headerRight()}{/if}
    </div>
  {/if}
  <div class={bodyClass ? `card-body ${bodyClass}` : "card-body"}>{@render children?.()}</div>
</div>
