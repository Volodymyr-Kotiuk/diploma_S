<script lang="ts">
  import LineChart from './LineChart.svelte';
  import type { ResourceMetric } from '$lib/types';
  export let metrics: ResourceMetric[] = [];
</script>

<LineChart title="RAM у часі" {metrics} fields={[{ key: 'ram_usage_percent', label: 'RAM %', color: '#16a34a' }]} />
