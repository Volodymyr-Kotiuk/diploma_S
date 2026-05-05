<script lang="ts">
  import Topbar from './Topbar.svelte';
  export let onRefresh: (() => void) | undefined = undefined;
</script>

<div class="min-h-screen bg-surface text-slate-900">
  <Topbar {onRefresh} />
  <main class="mx-auto w-full max-w-[1480px] px-4 py-5 lg:px-6">
    <slot />
  </main>
</div>
