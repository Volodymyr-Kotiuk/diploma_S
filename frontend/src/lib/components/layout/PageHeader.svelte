<script lang="ts">
  export let title: string;
  export let description = '';
</script>

<div class="mb-4 flex flex-col gap-3 border-b border-line pb-4 md:flex-row md:items-end md:justify-between">
  <div class="min-w-0">
    <h1 class="text-xl font-semibold tracking-normal text-slate-950 md:text-2xl">{title}</h1>
    {#if description}
      <p class="mt-1 max-w-3xl text-sm text-slate-700">{description}</p>
    {/if}
  </div>
  <slot name="actions" />
</div>
