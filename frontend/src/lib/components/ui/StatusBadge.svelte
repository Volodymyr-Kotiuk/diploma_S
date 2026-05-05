<script lang="ts">
  export let status = 'unknown';
  let toneClass = 'text-slate-700';
  $: toneClass =
    status === 'healthy' || status === 'online'
      ? 'text-emerald-700'
      : status === 'warning'
        ? 'text-amber-700'
        : status === 'critical'
          ? 'text-red-700'
          : 'text-slate-700';
  const labels: Record<string, string> = {
    waiting: 'очікує',
    online: 'онлайн',
    offline: 'офлайн',
    healthy: 'справний',
    warning: 'попередження',
    critical: 'критичний',
    open: 'відкритий',
    acknowledged: 'підтверджений',
    resolved: 'закритий',
    unknown: 'невідомо'
  };
</script>

<span class={`text-sm font-medium ${toneClass}`}>{labels[status] || status}</span>
