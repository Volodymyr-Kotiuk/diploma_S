<script lang="ts">
  import LineChart from './LineChart.svelte';
  import type { ResourceMetric } from '$lib/types';
  export let metrics: ResourceMetric[] = [];
  export let height = 260;
</script>

<LineChart title="CPU у часі" {metrics} {height} fields={[{ key: 'cpu_usage_percent', label: 'CPU %', color: '#2F4FDC' }, { key: 'load_average_1m', label: 'Навантаження 1 хв', color: '#D97706' }]} />
