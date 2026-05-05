<script lang="ts">
  export let label: string;
  export let value: string | number;
  export let helper = '';
  export let accent = 'bg-brand-500';
  export let progress: number | null = null;
</script>

<section class="min-h-[104px] rounded bg-white p-3 ring-1 ring-slate-200/70">
  <div class="flex items-start justify-between gap-4">
    <div>
      <p class="text-xs font-semibold uppercase text-slate-600">{label}</p>
      <p class="mt-1 text-2xl font-semibold tracking-normal text-slate-950">{value}</p>
    </div>
  </div>
  {#if progress !== null}
    <div class="mt-3 h-2 rounded-sm bg-slate-200">
      <div class={`h-2 rounded-sm ${accent}`} style={`width: ${Math.min(Math.max(progress, 0), 100)}%`}></div>
    </div>
  {/if}
  {#if helper}
    <p class="mt-2 text-sm text-slate-700">{helper}</p>
  {/if}
</section>
