<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import type { CapacityForecast } from '$lib/types';
  export let forecasts: CapacityForecast[] = [];
  let element: HTMLDivElement;
  let chart: import('echarts').ECharts | undefined;

  function metricLabel(metric: string) {
    return (
      {
        cpu_usage_percent: 'CPU',
        ram_usage_percent: 'RAM',
        disk_usage_percent: 'Диск',
        underutilization: 'Недовикористання'
      }[metric] || metric
    );
  }

  function render() {
    chart?.setOption({
      title: { text: 'Прогноз місткості', left: 0, top: 0, textStyle: { fontSize: 13, fontWeight: 600, color: '#111827' } },
      tooltip: { trigger: 'axis', backgroundColor: '#ffffff', borderColor: '#d8dee8', borderWidth: 1, textStyle: { color: '#111827', fontSize: 12 } },
      legend: { top: 4, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { color: '#64748b', fontSize: 11 } },
      grid: { top: 50, right: 18, left: 40, bottom: 28 },
      xAxis: { type: 'category', data: forecasts.map((f) => metricLabel(f.metric_name)), axisTick: { show: false }, axisLabel: { color: '#64748b', fontSize: 11 } },
      yAxis: { type: 'value', max: 100, splitNumber: 3, axisTick: { show: false }, axisLine: { show: false }, axisLabel: { color: '#64748b', fontSize: 11 }, splitLine: { lineStyle: { color: '#eef2f6' } } },
      series: [
        { name: 'Поточне', type: 'bar', data: forecasts.map((f) => f.current_value ?? 0), barMaxWidth: 34, itemStyle: { color: '#D97706', borderRadius: [3, 3, 0, 0] } },
        { name: 'Прогноз', type: 'bar', data: forecasts.map((f) => f.predicted_value ?? 0), barMaxWidth: 34, itemStyle: { color: '#2F4FDC', borderRadius: [3, 3, 0, 0] } }
      ]
    });
  }

  function resize() {
    chart?.resize();
  }

  onMount(async () => {
    const echarts = await import('echarts');
    chart = echarts.init(element);
    render();
    window.addEventListener('resize', resize);
  });

  onDestroy(() => {
    if (typeof window !== 'undefined') window.removeEventListener('resize', resize);
    chart?.dispose();
  });

  $: if (chart && forecasts) render();
</script>

<div bind:this={element} class="h-[260px] w-full"></div>
