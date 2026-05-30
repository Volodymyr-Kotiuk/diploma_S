<script lang="ts">
  import { RefreshCw } from 'lucide-svelte';
  import Button from '$lib/components/ui/Button.svelte';
  export let onRefresh: (() => void) | undefined = undefined;
</script>

<header class="border-b border-[#d7dde6] bg-white">
  <div class="grid min-h-[82px] grid-cols-[1fr_auto] items-center gap-4 px-6 py-4 md:px-9">
    <div class="min-w-0">
      <a href="/dashboard" class="block text-[18px] font-bold leading-tight text-[#111827]">Система діагностики та масштабування</a>
      <p class="mt-2 max-w-3xl truncate text-[14px] font-normal text-[#52627a]">Віртуалізовані обчислювальні ресурси у комп'ютерних мережах</p>
    </div>
    <div class="flex justify-end">
      {#if onRefresh}
        <Button variant="secondary" size="sm" on:click={onRefresh} title="Оновити">
          <RefreshCw class="h-4 w-4" />
          <span class="hidden sm:inline">Оновити</span>
        </Button>
      {/if}
    </div>
  </div>
</header>
