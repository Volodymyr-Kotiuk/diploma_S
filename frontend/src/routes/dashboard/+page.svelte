<script lang="ts">
  import { onMount } from 'svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import LoadingSkeleton from '$lib/components/ui/LoadingSkeleton.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import { nodesApi } from '$lib/api/nodes';
  import { pushToast } from '$lib/stores/app';
  import { percent, shortDate } from '$lib/utils/formatters';
  import type { Node, ResourceMetric } from '$lib/types';

  let loading = true;
  let error = '';
  let nodes: Node[] = [];
  let latestByNode: Record<number, ResourceMetric | undefined> = {};

  function typeLabel(type: string) {
    return type === 'remote_agent' ? 'Реальний вузол' : 'Віртуальний вузол';
  }

  async function load() {
    loading = true;
    error = '';
    try {
      nodes = await nodesApi.list();
      const metricPairs = await Promise.all(
        nodes.map(async (node) => {
          const metrics = await nodesApi.metrics(node.id, 1);
          return [node.id, metrics[metrics.length - 1]] as const;
        })
      );
      latestByNode = Object.fromEntries(metricPairs);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Не вдалося завантажити вузли';
    } finally {
      loading = false;
    }
  }

  async function removeNode(id: number) {
    await nodesApi.remove(id);
    pushToast('Вузол видалено', 'success');
    await load();
  }

  onMount(load);
</script>

{#if loading}
  <LoadingSkeleton rows={5} />
{:else if error}
  <Card><p class="text-sm text-rose-600">{error}</p></Card>
{:else}
  <section class="border-b border-line pb-5">
    <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-lg font-semibold text-slate-950">Додати обчислювальний вузол</h1>
        
      </div>
      <a href="/nodes/add"><Button>Перейти до створення вузла</Button></a>
    </div>
  </section>

  <Card className="mt-5">
    <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <h2 class="text-base font-semibold text-slate-950">Додані обчислювальні вузли</h2>
        
      </div>
    </div>

    {#if nodes.length === 0}
      <EmptyState
        title="Вузли ще не додані"
        text="Додайте реальний ПК або сервер для збору метрик чи створіть віртуальний вузол для тестової діагностики."
      >
        <div class="mt-4 flex flex-wrap justify-center gap-2">
          <a href="/nodes/add"><Button size="sm">Перейти до створення вузла</Button></a>
        </div>
      </EmptyState>
    {:else}
      <div class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="border-y border-line bg-slate-50 text-left text-xs font-semibold uppercase tracking-normal text-slate-700">
            <tr>
              <th class="px-3 py-2">Назва</th>
              <th class="px-3 py-2">Тип</th>
              <th class="px-3 py-2">Статус</th>
              <th class="px-3 py-2">CPU</th>
              <th class="px-3 py-2">RAM</th>
              <th class="px-3 py-2">Останнє оновлення</th>
              <th class="px-3 py-2 text-right">Дія</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-line">
            {#each nodes as node}
              {@const latest = latestByNode[node.id]}
              <tr>
                <td class="px-3 py-3">
                  <a class="font-medium text-brand-700" href={`/nodes/${node.id}`}>{node.name}</a>
                  {#if node.description}
                    <p class="mt-1 max-w-[360px] truncate text-xs text-slate-600">{node.description}</p>
                  {/if}
                </td>
                <td class="px-3 py-3 text-slate-700">{typeLabel(node.node_type)}</td>
                <td class="px-3 py-3"><StatusBadge status={node.status} /></td>
                <td class="px-3 py-3 text-slate-800">{latest ? percent(latest.cpu_usage_percent) : '—'}</td>
                <td class="px-3 py-3 text-slate-800">{latest ? percent(latest.ram_usage_percent) : '—'}</td>
                <td class="px-3 py-3 text-slate-700">{shortDate(latest?.timestamp || node.last_heartbeat_at)}</td>
                <td class="px-3 py-3">
                  <div class="flex justify-end gap-2">
                    <a href={`/nodes/${node.id}`}><Button size="sm" variant="secondary">Відкрити</Button></a>
                    <Button size="sm" variant="danger" on:click={() => removeNode(node.id)}>Видалити</Button>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </Card>
{/if}
