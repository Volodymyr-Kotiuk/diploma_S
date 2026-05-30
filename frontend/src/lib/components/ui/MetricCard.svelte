<script lang="ts">
  export let label: string;
  export let value: string | number;
  export let helper = '';
  export let accent = 'bg-brand-500';
  export let progress: number | null = null;
</script>

<section class="min-h-[96px] rounded-lg border border-[#d7dde6] bg-white p-4 shadow-panel">
  <div class="flex items-start justify-between gap-4">
    <div>
      <p class="text-[11px] font-semibold uppercase text-slate-500">{label}</p>
      <p class="mt-1 text-[23px] font-semibold leading-tight tracking-normal text-slate-950">{value}</p>
    </div>
  </div>
  {#if progress !== null}
    <div class="mt-3 h-1.5 rounded-full bg-slate-100">
      <div class={`h-1.5 rounded-full ${accent}`} style={`width: ${Math.min(Math.max(progress, 0), 100)}%`}></div>
    </div>
  {/if}
  {#if helper}
    <p class="mt-2 text-xs text-slate-500">{helper}</p>
  {/if}
</section>
