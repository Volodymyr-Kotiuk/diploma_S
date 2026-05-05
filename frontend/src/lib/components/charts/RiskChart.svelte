<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  export let points: { label: string; value: number }[] = [];
  let element: HTMLDivElement;
  let chart: import('echarts').ECharts | undefined;

  function render() {
    chart?.setOption({
      title: { text: 'Оцінка ризику', left: 8, top: 6, textStyle: { fontSize: 13, fontWeight: 700, color: '#57534e' } },
      tooltip: { trigger: 'axis', backgroundColor: '#171717', borderColor: '#44403c', textStyle: { color: '#fafaf9' } },
      grid: { top: 48, right: 16, left: 38, bottom: 30 },
      xAxis: { type: 'category', data: points.map((p) => p.label), axisLabel: { color: '#78716c' } },
      yAxis: { type: 'value', max: 100, axisLabel: { color: '#78716c' }, splitLine: { lineStyle: { color: '#e7e5e4' } } },
      series: [{ type: 'bar', data: points.map((p) => p.value), itemStyle: { color: '#d97706', borderRadius: [2, 2, 0, 0] } }]
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
