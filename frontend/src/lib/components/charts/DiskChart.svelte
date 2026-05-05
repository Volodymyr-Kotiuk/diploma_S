<script lang="ts">
  import LineChart from './LineChart.svelte';
  import type { ResourceMetric } from '$lib/types';
  export let metrics: ResourceMetric[] = [];
</script>

<LineChart title="Дискові операції" {metrics} fields={[{ key: 'disk_read_rate', label: 'Читання B/s', color: '#b45309' }, { key: 'disk_write_rate', label: 'Запис B/s', color: '#dc2626' }]} />
