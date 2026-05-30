<script lang="ts">
  import { onMount } from 'svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
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

<section class="rounded-lg border border-[#d7dde6] bg-white p-6">
  <div class="overflow-x-auto">
    <table class="min-w-full text-sm">
      <thead class="bg-[#f8fafc] text-left text-xs font-bold uppercase tracking-[0.04em] text-[#475569]">
        <tr>
          <th class="border-b border-[#e5e9f0] px-[14px] py-3">Час</th>
          <th class="border-b border-[#e5e9f0] px-[14px] py-3">Вузол</th>
          <th class="border-b border-[#e5e9f0] px-[14px] py-3">Тип</th>
          <th class="border-b border-[#e5e9f0] px-[14px] py-3">Рівень</th>
          <th class="border-b border-[#e5e9f0] px-[14px] py-3">Причина</th>
          <th class="border-b border-[#e5e9f0] px-[14px] py-3">Статус</th>
          <th class="border-b border-[#e5e9f0] px-[14px] py-3 text-right">Дія</th>
        </tr>
      </thead>
      <tbody>
        {#each incidents as incident}
          <tr>
            <td class="border-b border-[#e5e9f0] px-[14px] py-4 align-middle text-[#475569]">{shortDate(incident.started_at)}</td>
            <td class="border-b border-[#e5e9f0] px-[14px] py-4 align-middle font-semibold text-[#111827]">{nodeNames[incident.node_id] || incident.node_id}</td>
            <td class="border-b border-[#e5e9f0] px-[14px] py-4 align-middle text-[#1f2937]">{typeLabels[incident.incident_type] || incident.incident_type}</td>
            <td class="border-b border-[#e5e9f0] px-[14px] py-4 align-middle text-[#1f2937]">{severityLabels[incident.severity] || incident.severity}</td>
            <td class="border-b border-[#e5e9f0] px-[14px] py-4 align-middle font-medium text-[#111827]">{incident.root_cause ? rootCauseLabels[incident.root_cause] || incident.root_cause : '—'}</td>
            <td class="border-b border-[#e5e9f0] px-[14px] py-4 align-middle"><StatusBadge status={incident.status} /></td>
            <td class="border-b border-[#e5e9f0] px-[14px] py-4 text-right align-middle"><a class="font-medium text-[#1d4ed8]" href={`/nodes/${incident.node_id}`}>Вузол</a></td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</section>
