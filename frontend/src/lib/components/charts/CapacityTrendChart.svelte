<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import type { CapacityForecast } from '$lib/types';
  export let forecasts: CapacityForecast[] = [];
  let element: HTMLDivElement;
  let chart: import('echarts').ECharts | undefined;

  function render() {
    chart?.setOption({
      title: { text: 'Прогноз місткості', left: 8, top: 6, textStyle: { fontSize: 13, fontWeight: 700, color: '#57534e' } },
      tooltip: { trigger: 'axis', backgroundColor: '#171717', borderColor: '#44403c', textStyle: { color: '#fafaf9' } },
      legend: { top: 8, right: 8 },
      grid: { top: 52, right: 18, left: 40, bottom: 28 },
      xAxis: { type: 'category', data: forecasts.map((f) => f.metric_name), axisLabel: { color: '#78716c' } },
      yAxis: { type: 'value', max: 100, axisLabel: { color: '#78716c' }, splitLine: { lineStyle: { color: '#e7e5e4' } } },
      series: [
        { name: 'Поточне', type: 'bar', data: forecasts.map((f) => f.current_value ?? 0), itemStyle: { color: '#d97706', borderRadius: [2, 2, 0, 0] } },
        { name: 'Прогноз', type: 'bar', data: forecasts.map((f) => f.predicted_value ?? 0), itemStyle: { color: '#2563eb', borderRadius: [2, 2, 0, 0] } }
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
