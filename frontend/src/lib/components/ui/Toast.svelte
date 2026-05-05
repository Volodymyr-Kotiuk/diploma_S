<script lang="ts">
  import { toasts } from '$lib/stores/app';
</script>

<div class="fixed right-4 top-4 z-50 space-y-2">
  {#each $toasts as toast}
    <div
      class={`w-[min(360px,calc(100vw-2rem))] rounded border px-4 py-3 text-sm ${
        toast.type === 'error'
          ? 'border-rose-300 bg-rose-50 text-rose-800'
          : toast.type === 'success'
            ? 'border-emerald-300 bg-emerald-50 text-emerald-800'
            : 'border-slate-300 bg-white text-slate-800'
      }`}
    >
      {toast.message}
    </div>
  {/each}
</div>
