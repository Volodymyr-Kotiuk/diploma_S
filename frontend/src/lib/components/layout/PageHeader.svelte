<script lang="ts">
  export let title: string;
  export let description = '';
</script>

<div class="mb-6 border-b border-[#d7dde6] pb-5">
  <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
    <div class="min-w-0">
      <h1 class="m-0 text-[24px] font-bold leading-tight tracking-normal text-[#111827]">{title}</h1>
      {#if description}
        <p class="mt-1 max-w-3xl text-sm text-[#64748b]">{description}</p>
      {/if}
    </div>
    <div class="flex shrink-0 items-start justify-end gap-2">
      <slot name="actions" />
    </div>
  </div>
</div>
