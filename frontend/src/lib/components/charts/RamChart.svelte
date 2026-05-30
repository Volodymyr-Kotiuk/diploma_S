<script lang="ts">
  import LineChart from './LineChart.svelte';
  import type { ResourceMetric } from '$lib/types';
  export let metrics: ResourceMetric[] = [];
  export let height = 260;
</script>

<LineChart title="RAM у часі" {metrics} {height} fields={[{ key: 'ram_usage_percent', label: 'RAM %', color: '#22A06B' }]} />
