<script lang="ts">
  import { toasts } from '$lib/stores/app';
</script>

<div class="fixed right-4 top-4 z-50 space-y-2">
  {#each $toasts as toast}
    <div
      class={`w-[min(360px,calc(100vw-2rem))] rounded-lg border px-4 py-3 text-sm shadow-panel ${
        toast.type === 'error'
          ? 'border-red-200 bg-red-50 text-red-800'
          : toast.type === 'success'
            ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
            : 'border-line bg-white text-slate-800'
      }`}
    >
      {toast.message}
    </div>
  {/each}
</div>
