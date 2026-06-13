<script lang="ts">
  // Faithful wrapper of the global `.progress > .fill` bar. `percent` is clamped
  // to 0..100; `wide` adds the `progress--wide` modifier used by Settings/Review.
  let {
    percent = 0,
    wide = false,
    ...rest
  }: { percent?: number; wide?: boolean; [key: string]: unknown } = $props();

  const pct = $derived(Math.max(0, Math.min(100, Number(percent) || 0)));
</script>

<div class={wide ? "progress progress--wide" : "progress"} {...rest}>
  <div class="fill" style="width:{pct}%"></div>
</div>
