<script lang="ts">
  import LineChart from './LineChart.svelte';
  import type { ResourceMetric } from '$lib/types';
  export let metrics: ResourceMetric[] = [];
  export let height = 260;
</script>

<LineChart title="Дискові операції" {metrics} {height} fields={[{ key: 'disk_read_rate', label: 'Читання', color: '#D97706', unit: 'bytes_per_second' }, { key: 'disk_write_rate', label: 'Запис', color: '#DC2626', unit: 'bytes_per_second' }]} />
