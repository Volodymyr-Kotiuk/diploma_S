<script lang="ts">
  import LineChart from './LineChart.svelte';
  import type { ResourceMetric } from '$lib/types';
  export let metrics: ResourceMetric[] = [];
</script>

<LineChart title="Мережевий обмін" {metrics} fields={[{ key: 'network_sent_rate', label: 'Надіслано B/s', color: '#0891b2' }, { key: 'network_recv_rate', label: 'Отримано B/s', color: '#2563eb' }]} />
