<script lang="ts">
  import LineChart from './LineChart.svelte';
  import type { ResourceMetric } from '$lib/types';
  export let metrics: ResourceMetric[] = [];
</script>

<LineChart title="Підкачка у часі" {metrics} fields={[{ key: 'swap_usage_percent', label: 'Підкачка %', color: '#92400e' }]} />
