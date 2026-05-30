<script lang="ts">
  import { onMount } from 'svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
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
    return type === 'remote_agent' ? 'Реальний вузол' : 'Віртуальний вузол';
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

<section class="mb-6 rounded-lg border border-[#d7dde6] bg-white p-5">
  <div class="grid gap-3 md:grid-cols-[1fr_180px_180px_auto]">
    <input class="h-10 rounded-md border border-[#cbd5e1] bg-white px-3 text-[15px]" bind:value={search} placeholder="Пошук вузла" />
    <select bind:value={status} class="h-10 rounded-md border border-[#cbd5e1] bg-white px-3 text-[15px]">
      <option value="">Усі статуси</option>
      <option value="waiting">очікує</option>
      <option value="online">онлайн</option>
      <option value="healthy">справний</option>
      <option value="warning">попередження</option>
      <option value="critical">критичний</option>
      <option value="offline">офлайн</option>
    </select>
    <select bind:value={nodeType} class="h-10 rounded-md border border-[#cbd5e1] bg-white px-3 text-[15px]">
      <option value="">Усі типи</option>
      <option value="remote_agent">Реальний вузол</option>
      <option value="virtual_node">Віртуальний вузол</option>
    </select>
    <Button on:click={load}>Фільтрувати</Button>
  </div>
</section>

{#if nodes.length === 0}
  <EmptyState title="Додайте вузол" text="Підключіть реальну машину для збору метрик або створіть віртуальний вузол для тестового сценарію." />
{:else}
  <section class="rounded-lg border border-[#d7dde6] bg-white p-6">
    <div class="overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead class="bg-[#f8fafc] text-left text-xs font-bold uppercase tracking-[0.04em] text-[#475569]">
          <tr>
            <th class="border-b border-[#e5e9f0] px-[14px] py-3">Назва</th>
            <th class="border-b border-[#e5e9f0] px-[14px] py-3">Тип</th>
            <th class="border-b border-[#e5e9f0] px-[14px] py-3">Статус</th>
            <th class="border-b border-[#e5e9f0] px-[14px] py-3 text-right">CPU %</th>
            <th class="border-b border-[#e5e9f0] px-[14px] py-3 text-right">RAM %</th>
            <th class="border-b border-[#e5e9f0] px-[14px] py-3">Останній сигнал</th>
            <th class="border-b border-[#e5e9f0] px-[14px] py-3 text-right">Інциденти</th>
            <th class="border-b border-[#e5e9f0] px-[14px] py-3 text-right">Дії</th>
          </tr>
        </thead>
        <tbody>
          {#each nodes as node}
            <tr>
              <td class="border-b border-[#e5e9f0] px-[14px] py-4 align-middle font-semibold text-[#1d4ed8]">
                <a href={`/nodes/${node.id}`}>{node.name}</a>
                <p class="text-xs font-normal text-slate-500">{node.hostname || node.description || 'ім’я хоста невідоме'}</p>
              </td>
              <td class="border-b border-[#e5e9f0] px-[14px] py-4 align-middle text-[#1f2937]">{typeLabel(node.node_type)}</td>
              <td class="border-b border-[#e5e9f0] px-[14px] py-4 align-middle"><StatusBadge status={node.status} /></td>
              <td class="border-b border-[#e5e9f0] px-[14px] py-4 text-right align-middle tabular-nums">{percent(latestMetrics[node.id]?.cpu_usage_percent)}</td>
              <td class="border-b border-[#e5e9f0] px-[14px] py-4 text-right align-middle tabular-nums">{percent(latestMetrics[node.id]?.ram_usage_percent)}</td>
              <td class="border-b border-[#e5e9f0] px-[14px] py-4 align-middle text-[#475569]">{shortDate(node.last_heartbeat_at)}</td>
              <td class="border-b border-[#e5e9f0] px-[14px] py-4 text-right align-middle tabular-nums">{incidentCounts[node.id] || 0}</td>
              <td class="border-b border-[#e5e9f0] px-[14px] py-4 text-right align-middle">
                <div class="inline-flex gap-2 whitespace-nowrap">
                  <a href={`/nodes/${node.id}`}><Button size="sm" variant="secondary">Відкрити</Button></a>
                  <Button size="sm" variant="danger" on:click={() => removeNode(node)}>Видалити</Button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </section>
{/if}
