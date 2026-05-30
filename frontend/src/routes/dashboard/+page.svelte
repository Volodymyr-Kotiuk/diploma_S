<script lang="ts">
  import { onMount } from 'svelte';
  import { Plus } from 'lucide-svelte';
  import Button from '$lib/components/ui/Button.svelte';
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
  <div class="border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
{:else}
  <section class="pt-6">
    <h1 class="m-0 text-[32px] font-bold leading-tight text-[#111827]">Обчислювальні вузли</h1>
    <div class="mt-8">
      <a href="/nodes/add">
        <Button className="h-[43px] rounded-md px-5 text-[17px]">
          <Plus class="h-5 w-5" />
          Додати вузол
        </Button>
      </a>
    </div>
  </section>

  <section class="mt-8 border-t border-[#d7dde6]">
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
        <table class="min-w-full text-[17px]">
          <thead class="text-left text-[16px] font-bold text-[#111827]">
            <tr>
              <th class="border-b border-[#d7dde6] px-4 py-6">Назва</th>
              <th class="border-b border-[#d7dde6] px-4 py-6">Тип</th>
              <th class="border-b border-[#d7dde6] px-4 py-6">Статус</th>
              <th class="border-b border-[#d7dde6] px-4 py-6 text-left">CPU</th>
              <th class="border-b border-[#d7dde6] px-4 py-6 text-left">RAM</th>
              <th class="border-b border-[#d7dde6] px-4 py-6">Останнє оновлення</th>
              <th class="border-b border-[#d7dde6] px-4 py-6 text-center">Дії</th>
            </tr>
          </thead>
          <tbody>
            {#each nodes as node}
              {@const latest = latestByNode[node.id]}
              <tr>
                <td class="border-b border-[#d7dde6] px-4 py-5 align-middle">
                  <a class="font-bold text-[#0f4fd8]" href={`/nodes/${node.id}`}>{node.name}</a>
                  {#if node.description}
                    <p class="mt-1 max-w-[360px] truncate text-xs text-slate-500">{node.description}</p>
                  {/if}
                </td>
                <td class="border-b border-[#d7dde6] px-4 py-5 align-middle text-[#111827]">{typeLabel(node.node_type)}</td>
                <td class="border-b border-[#d7dde6] px-4 py-5 align-middle"><StatusBadge status={node.status} /></td>
                <td class="border-b border-[#d7dde6] px-4 py-5 align-middle tabular-nums text-[#111827]">{latest ? percent(latest.cpu_usage_percent) : '—'}</td>
                <td class="border-b border-[#d7dde6] px-4 py-5 align-middle tabular-nums text-[#111827]">{latest ? percent(latest.ram_usage_percent) : '—'}</td>
                <td class="border-b border-[#d7dde6] px-4 py-5 align-middle text-[#111827]">{shortDate(latest?.timestamp || node.last_heartbeat_at)}</td>
                <td class="border-b border-[#d7dde6] px-4 py-5 align-middle">
                  <div class="flex justify-center gap-3 whitespace-nowrap">
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
  </section>
{/if}
