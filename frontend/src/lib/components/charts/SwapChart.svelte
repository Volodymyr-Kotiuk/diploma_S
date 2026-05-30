<script lang="ts">
  import LineChart from './LineChart.svelte';
  import type { ResourceMetric } from '$lib/types';
  export let metrics: ResourceMetric[] = [];
  export let height = 260;
</script>

<LineChart title="Підкачка у часі" {metrics} {height} fields={[{ key: 'swap_usage_percent', label: 'Підкачка %', color: '#64748B' }]} />
