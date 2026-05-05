<script lang="ts">
  import { RefreshCw } from 'lucide-svelte';
  import Button from '$lib/components/ui/Button.svelte';
  export let onRefresh: (() => void) | undefined = undefined;
</script>

<header class="border-b border-line bg-white px-4 py-3 lg:px-6">
  <div class="mx-auto grid max-w-[1480px] grid-cols-[1fr_auto_1fr] items-center gap-4">
    <div></div>
    <div class="text-center">
      <a href="/dashboard" class="text-base font-semibold text-slate-950">Система діагностики</a>
      <p class="mt-0.5 text-xs text-slate-600">Система діагностики обчислювальних вузлів і формування рекомендацій масштабування.</p>
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
