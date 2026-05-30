<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  export let points: { label: string; value: number }[] = [];
  let element: HTMLDivElement;
  let chart: import('echarts').ECharts | undefined;

  function render() {
    chart?.setOption({
      title: { text: 'Оцінка ризику', left: 0, top: 0, textStyle: { fontSize: 13, fontWeight: 600, color: '#111827' } },
      tooltip: { trigger: 'axis', backgroundColor: '#ffffff', borderColor: '#d8dee8', borderWidth: 1, textStyle: { color: '#111827', fontSize: 12 } },
      grid: { top: 46, right: 18, left: 38, bottom: 30 },
      xAxis: { type: 'category', data: points.map((p) => p.label), axisTick: { show: false }, axisLabel: { color: '#64748b', fontSize: 11 } },
      yAxis: { type: 'value', max: 100, splitNumber: 3, axisTick: { show: false }, axisLine: { show: false }, axisLabel: { color: '#64748b', fontSize: 11 }, splitLine: { lineStyle: { color: '#eef2f6' } } },
      series: [{ type: 'bar', data: points.map((p) => p.value), barMaxWidth: 34, itemStyle: { color: '#D97706', borderRadius: [3, 3, 0, 0] } }]
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

  $: if (chart && points) render();
</script>

<div bind:this={element} class="h-[260px] w-full"></div>
