<script lang="ts">
  import Topbar from './Topbar.svelte';
  export let onRefresh: (() => void) | undefined = undefined;
</script>

<div class="min-h-screen bg-[#f3f5f8] text-slate-900">
  <Topbar {onRefresh} />
  <main class="w-full px-6 py-6 md:px-9">
    <slot />
  </main>
</div>
