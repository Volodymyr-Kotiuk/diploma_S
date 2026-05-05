<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import type { ResourceMetric } from '$lib/types';

  export let title = '';
  export let metrics: ResourceMetric[] = [];
  export let fields: { key: keyof ResourceMetric; label: string; color: string; unit?: string }[] = [];
  export let height = 260;

  let element: HTMLDivElement;
  let chart: import('echarts').ECharts | undefined;
  let echarts: typeof import('echarts') | undefined;

  function render() {
    if (!chart) return;
    chart.setOption({
      title: { text: title, left: 8, top: 6, textStyle: { fontSize: 13, fontWeight: 700, color: '#57534e' } },
      tooltip: { trigger: 'axis', backgroundColor: '#171717', borderColor: '#44403c', textStyle: { color: '#fafaf9' } },
      grid: { top: 48, right: 16, left: 42, bottom: 30 },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: metrics.map((m) => new Date(m.timestamp).toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })),
        axisLine: { lineStyle: { color: '#d6d3d1' } },
        axisLabel: { color: '#78716c' }
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#78716c' },
        splitLine: { lineStyle: { color: '#e7e5e4' } }
      },
      series: fields.map((field) => ({
        name: field.label,
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2.5, color: field.color },
        areaStyle: { opacity: 0.05, color: field.color },
        data: metrics.map((m) => Number(m[field.key] ?? 0))
      }))
    });
  }

  function resize() {
    chart?.resize();
  }

  onMount(async () => {
    echarts = await import('echarts');
    chart = echarts.init(element);
    render();
    window.addEventListener('resize', resize);
  });

  onDestroy(() => {
    if (typeof window !== 'undefined') window.removeEventListener('resize', resize);
    chart?.dispose();
  });

  $: if (chart && metrics) render();
</script>

<div bind:this={element} style={`height:${height}px`} class="w-full"></div>
