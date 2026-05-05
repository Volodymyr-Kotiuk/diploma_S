<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  import AppShell from '$lib/components/layout/AppShell.svelte';
  import Toast from '$lib/components/ui/Toast.svelte';
  import { initTheme } from '$lib/stores/theme';

  onMount(() => initTheme());
</script>

<AppShell>
  <slot />
</AppShell>
<Toast />
