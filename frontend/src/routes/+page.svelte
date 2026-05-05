<script lang="ts">
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  onMount(() => goto('/dashboard'));
</script>

<div class="text-sm text-slate-700">Відкриваємо головний екран...</div>
