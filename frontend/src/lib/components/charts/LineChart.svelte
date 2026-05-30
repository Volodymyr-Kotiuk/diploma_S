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

  function hexToRgba(hex: string, alpha: number) {
    const normalized = hex.replace('#', '');
    if (normalized.length !== 6) return `rgba(47, 79, 220, ${alpha})`;
    const value = Number.parseInt(normalized, 16);
    const red = (value >> 16) & 255;
    const green = (value >> 8) & 255;
    const blue = value & 255;
    return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
  }

  function formatBytesRate(value: number) {
    if (Math.abs(value) >= 1024 * 1024) return `${(value / 1024 / 1024).toFixed(value >= 10 * 1024 * 1024 ? 0 : 1)} MB/s`;
    if (Math.abs(value) >= 1024) return `${(value / 1024).toFixed(value >= 10 * 1024 ? 0 : 1)} KB/s`;
    return `${Math.round(value)} B/s`;
  }

  function formatValue(value: number, unit?: string) {
    if (unit === 'bytes_per_second') return formatBytesRate(value);
    if (unit === 'percent') return `${Math.round(value)}%`;
    return Number.isInteger(value) ? String(value) : value.toFixed(1);
  }

  function render() {
    if (!chart) return;
    const maxValue = Math.max(
      0,
      ...fields.flatMap((field) => metrics.map((metric) => Number(metric[field.key] ?? 0)))
    );
    const axisUnit = fields.every((field) => field.unit === 'bytes_per_second')
      ? 'bytes_per_second'
      : fields.every((field) => field.unit === 'percent')
        ? 'percent'
        : undefined;
    const gridLeft = axisUnit === 'bytes_per_second' ? 78 : axisUnit === 'percent' ? 52 : 60;
    chart.setOption({
      animation: false,
      color: fields.map((field) => field.color),
      title: {
        text: title,
        left: 0,
        top: 0,
        textStyle: {
          fontSize: 14,
          fontWeight: 700,
          color: '#111827'
        }
      },
      legend:
        fields.length > 1
          ? {
              top: 0,
              right: 0,
              itemWidth: 28,
              itemHeight: 3,
              icon: 'rect',
              textStyle: { color: '#4b5563', fontSize: 12 }
            }
          : { show: false },
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#ffffff',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        axisPointer: { type: 'line', lineStyle: { color: 'rgba(0, 0, 0, 0.12)', width: 1 } },
        formatter: (params: unknown) => {
          const rows = Array.isArray(params) ? params : [params];
          const first = rows[0] as { axisValueLabel?: string; axisValue?: string } | undefined;
          const title = first?.axisValueLabel || first?.axisValue || '';
          const body = rows
            .map((row) => {
              const item = row as { marker?: string; seriesName?: string; value?: number };
              const field = fields.find((entry) => entry.label === item.seriesName);
              return `${item.marker || ''}${item.seriesName || ''}: ${formatValue(Number(item.value ?? 0), field?.unit)}`;
            })
            .join('<br/>');
          return `${title}<br/>${body}`;
        },
        textStyle: { color: '#111827', fontSize: 12 },
        extraCssText: 'box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08); border-radius: 3px;'
      },
      grid: { top: 44, right: 18, left: gridLeft, bottom: 34, containLabel: false },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: metrics.map((m) => new Date(m.timestamp).toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })),
        axisTick: { show: true, alignWithLabel: true, lineStyle: { color: 'rgba(0, 0, 0, 0.1)', width: 1 } },
        axisLine: { lineStyle: { color: 'rgba(0, 0, 0, 0.1)', width: 1 } },
        axisLabel: { color: '#666666', fontSize: 12, hideOverlap: true, margin: 8 }
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: maxValue <= 100 ? 100 : undefined,
        axisTick: { show: false },
        axisLine: { show: false },
        axisLabel: {
          color: '#666666',
          fontSize: 12,
          margin: 10,
          formatter: (value: number) => formatValue(Number(value), axisUnit)
        },
        splitNumber: maxValue <= 100 ? 5 : 4,
        splitLine: { lineStyle: { color: 'rgba(0, 0, 0, 0.1)', width: 1 } }
      },
      series: fields.map((field) => ({
        name: field.label,
        type: 'line',
        smooth: false,
        symbol: 'circle',
        symbolSize: 5,
        showSymbol: true,
        emphasis: { focus: 'series' },
        connectNulls: true,
        itemStyle: { color: field.color, borderColor: '#ffffff', borderWidth: 1 },
        lineStyle: { width: 2, color: field.color },
        areaStyle: { color: hexToRgba(field.color, 0.1), opacity: 1 },
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
