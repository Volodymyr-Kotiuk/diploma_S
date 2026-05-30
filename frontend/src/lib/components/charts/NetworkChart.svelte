<script lang="ts">
  import LineChart from './LineChart.svelte';
  import type { ResourceMetric } from '$lib/types';
  export let metrics: ResourceMetric[] = [];
  export let height = 260;
</script>

<LineChart title="Мережевий обмін" {metrics} {height} fields={[{ key: 'network_sent_rate', label: 'Надіслано', color: '#0F766E', unit: 'bytes_per_second' }, { key: 'network_recv_rate', label: 'Отримано', color: '#2F4FDC', unit: 'bytes_per_second' }]} />
