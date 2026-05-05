<script lang="ts">
  import LineChart from './LineChart.svelte';
  import type { ResourceMetric } from '$lib/types';
  export let metrics: ResourceMetric[] = [];
</script>

<LineChart title="CPU у часі" {metrics} fields={[{ key: 'cpu_usage_percent', label: 'CPU %', color: '#d97706' }, { key: 'load_average_1m', label: 'Навантаження 1 хв', color: '#2563eb' }]} />
