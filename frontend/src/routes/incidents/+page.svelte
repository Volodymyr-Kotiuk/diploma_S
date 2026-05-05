<script lang="ts">
  import { onMount } from 'svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import { incidentsApi } from '$lib/api/incidents';
  import { nodesApi } from '$lib/api/nodes';
  import { shortDate } from '$lib/utils/formatters';
  import type { Incident, Node } from '$lib/types';

  let incidents: Incident[] = [];
  let nodes: Node[] = [];
  $: nodeNames = Object.fromEntries(nodes.map((node) => [node.id, node.name]));

  const severityLabels: Record<string, string> = {
    low: 'низький',
    medium: 'середній',
    high: 'високий',
    critical: 'критичний'
  };

  const typeLabels: Record<string, string> = {
    cpu_saturation: 'перевантаження CPU',
    memory_pressure: 'нестача пам’яті',
    swap_pressure: 'навантаження підкачки',
    disk_io_bottleneck: 'обмеження дискових операцій',
    network_pressure: 'навантаження мережі',
    thermal_risk: 'температурний ризик',
    resource_overcommit: 'перевиділення ресурсів',
    underutilization: 'недовикористання ресурсів',
    service_degradation: 'деградація сервісу',
    unknown_degradation: 'невизначена деградація'
  };

  const rootCauseLabels: Record<string, string> = {
    'CPU saturation': 'перевантаження CPU',
    'Memory pressure': 'нестача оперативної пам’яті',
    'Swap pressure': 'надмірне використання підкачки',
    'Disk I/O bottleneck': 'обмеження дискових операцій',
    'Network pressure': 'навантаження мережі',
    'Thermal risk': 'температурний ризик',
    'Resource overcommit': 'перевиділення ресурсів',
    Underutilization: 'недовикористання ресурсів',
    'Service degradation': 'деградація сервісу',
    'Unknown degradation': 'невизначена деградація'
  };

  onMount(async () => ([incidents, nodes] = await Promise.all([incidentsApi.list(), nodesApi.list()])));
</script>

<PageHeader title="Інциденти" />

<Card padded={false}>
  <div class="overflow-x-auto">
    <table class="min-w-full text-sm">
      <thead class="bg-slate-100 text-left text-xs uppercase tracking-normal text-slate-700"><tr><th class="px-4 py-3">Час</th><th>Вузол</th><th>Тип</th><th>Рівень</th><th>Причина</th><th>Статус</th><th>Дія</th></tr></thead>
      <tbody class="divide-y divide-slate-200">
        {#each incidents as incident}
          <tr><td class="px-4 py-3 text-slate-700">{shortDate(incident.started_at)}</td><td class="font-medium">{nodeNames[incident.node_id] || incident.node_id}</td><td>{typeLabels[incident.incident_type] || incident.incident_type}</td><td>{severityLabels[incident.severity] || incident.severity}</td><td class="font-medium">{incident.root_cause ? rootCauseLabels[incident.root_cause] || incident.root_cause : '—'}</td><td><StatusBadge status={incident.status} /></td><td><a class="font-medium text-brand-700" href={`/nodes/${incident.node_id}`}>Вузол</a></td></tr>
        {/each}
      </tbody>
    </table>
  </div>
</Card>
