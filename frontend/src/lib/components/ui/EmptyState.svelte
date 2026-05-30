<script lang="ts">
  import { Inbox } from 'lucide-svelte';
  export let title = 'Немає даних';
  export let text = 'Після збору метрик тут з’явиться інформація.';
</script>

<div class="flex min-h-[180px] flex-col items-center justify-center rounded-lg border border-dashed border-[#d7dde6] bg-white p-6 text-center">
  <Inbox class="h-7 w-7 text-slate-400" />
  <h3 class="mt-3 text-base font-semibold text-slate-900">{title}</h3>
  <p class="mt-1 max-w-md text-sm text-slate-600">{text}</p>
  <slot />
</div>
