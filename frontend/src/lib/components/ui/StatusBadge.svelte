<script lang="ts">
  export let status = 'unknown';
  $: dotClass =
    status === 'healthy' || status === 'online' || status === 'low'
      ? 'bg-[#16a34a]'
      : status === 'warning' || status === 'medium'
        ? 'bg-[#D97706]'
        : status === 'critical' || status === 'high'
          ? 'bg-[#DC2626]'
          : status === 'resolved' || status === 'accepted'
            ? 'bg-[#16a34a]'
            : status === 'open' || status === 'new' || status === 'acknowledged'
              ? 'bg-[#D97706]'
              : 'bg-[#64748b]';
  const labels: Record<string, string> = {
    waiting: 'очікує',
    online: 'онлайн',
    offline: 'офлайн',
    healthy: 'справний',
    warning: 'попередження',
    critical: 'критичний',
    low: 'низький',
    medium: 'середній',
    high: 'високий',
    open: 'активний',
    acknowledged: 'підтверджений',
    resolved: 'закритий',
    new: 'нова',
    accepted: 'прийнята',
    ignored: 'проігнорована',
    unknown: 'невідомо'
  };
</script>

<span class="inline-flex items-center gap-2 text-sm font-medium text-[#1f2937]">
  <span class={`h-2 w-2 rounded-full ${dotClass}`}></span>
  {labels[status] || status}
</span>
