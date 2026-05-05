<script lang="ts">
  import { onMount } from 'svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import { incidentsApi } from '$lib/api/incidents';
  import { nodesApi } from '$lib/api/nodes';
  import { percent, shortDate } from '$lib/utils/formatters';
  import { pushToast } from '$lib/stores/app';
  import type { Incident, Node, ResourceMetric } from '$lib/types';

  let nodes: Node[] = [];
  let incidents: Incident[] = [];
  let latestMetrics: Record<number, ResourceMetric | undefined> = {};
  let search = '';
  let status = '';
  let nodeType = '';

  $: incidentCounts = incidents.reduce<Record<number, number>>((acc, incident) => {
    acc[incident.node_id] = (acc[incident.node_id] || 0) + 1;
    return acc;
  }, {});

  function typeLabel(type: string) {
    return type === 'remote_agent' ? 'Агент' : 'Віртуальний';
  }

  async function load() {
    const params = new URLSearchParams();
    if (search) params.set('search', search);
    if (status) params.set('status', status);
    if (nodeType) params.set('node_type', nodeType);
    const query = params.toString() ? `?${params.toString()}` : '';
    nodes = await nodesApi.list(query);
    incidents = await incidentsApi.list();
    const metricRows = await Promise.all(nodes.map((node) => nodesApi.metrics(node.id, 1)));
    latestMetrics = Object.fromEntries(nodes.map((node, index) => [node.id, metricRows[index][0]]));
  }

  async function removeNode(node: Node) {
    await nodesApi.remove(node.id);
    pushToast('Вузол видалено', 'success');
    await load();
  }

  onMount(load);
</script>

<PageHeader title="Вузли">
  <a slot="actions" href="/nodes/add"><Button>Додати вузол</Button></a>
</PageHeader>

<Card className="mb-4">
  <div class="grid gap-3 md:grid-cols-[1fr_180px_180px_auto]">
    <input class="h-9 rounded border border-slate-200 bg-white px-3 text-sm" bind:value={search} placeholder="Пошук вузла" />
    <select bind:value={status} class="h-9 rounded border border-slate-200 bg-white px-3 text-sm">
      <option value="">Усі статуси</option>
      <option value="waiting">очікує</option>
      <option value="online">онлайн</option>
      <option value="healthy">справний</option>
      <option value="warning">попередження</option>
      <option value="critical">критичний</option>
      <option value="offline">офлайн</option>
    </select>
    <select bind:value={nodeType} class="h-9 rounded border border-slate-200 bg-white px-3 text-sm">
      <option value="">Усі типи</option>
      <option value="remote_agent">Реальний вузол</option>
      <option value="virtual_node">Віртуальний вузол</option>
    </select>
    <Button on:click={load}>Фільтрувати</Button>
  </div>
</Card>

{#if nodes.length === 0}
  <EmptyState title="Додайте вузол" text="Підключіть реальну машину для збору метрик або створіть віртуальний вузол для тестового сценарію." />
{:else}
  <Card padded={false}>
    <div class="overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead class="bg-slate-100 text-left text-xs uppercase tracking-normal text-slate-700">
          <tr>
            <th class="px-4 py-3">Назва</th>
            <th>Тип</th>
            <th>Статус</th>
            <th>CPU %</th>
            <th>RAM %</th>
            <th>Останній сигнал</th>
            <th>Інциденти</th>
            <th class="pr-4 text-right">Дії</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-200">
          {#each nodes as node}
            <tr>
              <td class="px-4 py-3 font-medium text-slate-950">
                {node.name}
                <p class="text-xs font-normal text-slate-700">{node.hostname || node.description || 'ім’я хоста невідоме'}</p>
              </td>
              <td>{typeLabel(node.node_type)}</td>
              <td><StatusBadge status={node.status} /></td>
              <td>{percent(latestMetrics[node.id]?.cpu_usage_percent)}</td>
              <td>{percent(latestMetrics[node.id]?.ram_usage_percent)}</td>
              <td>{shortDate(node.last_heartbeat_at)}</td>
              <td>{incidentCounts[node.id] || 0}</td>
              <td class="pr-4 text-right">
                <div class="inline-flex gap-2">
                  <a class="font-medium text-brand-700" href={`/nodes/${node.id}`}>Відкрити</a>
                  <button class="font-medium text-red-700" on:click={() => removeNode(node)}>Видалити</button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </Card>
{/if}
