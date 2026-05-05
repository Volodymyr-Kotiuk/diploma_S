<script lang="ts">
  import { onMount } from 'svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import { nodesApi } from '$lib/api/nodes';
  import { recommendationsApi } from '$lib/api/recommendations';
  import { pushToast } from '$lib/stores/app';
  import type { Node, Recommendation } from '$lib/types';

  let recommendations: Recommendation[] = [];
  let nodes: Node[] = [];
  $: nodeNames = Object.fromEntries(nodes.map((node) => [node.id, node.name]));

  const priorityLabels: Record<string, string> = {
    low: 'низький',
    medium: 'середній',
    high: 'високий',
    critical: 'критичний'
  };

  const statusLabels: Record<string, string> = {
    new: 'нова',
    accepted: 'прийнята',
    ignored: 'проігнорована',
    resolved: 'закрита'
  };

  const typeLabels: Record<string, string> = {
    vertical_cpu_scaling: 'збільшення CPU',
    vertical_ram_scaling: 'збільшення RAM',
    horizontal_scaling: 'горизонтальне масштабування',
    downscale: 'зменшення ресурсів',
    storage_optimization: 'оптимізація диска',
    network_optimization: 'оптимізація мережі',
    process_optimization: 'оптимізація процесів',
    thermal_optimization: 'температурна оптимізація',
    overcommit_optimization: 'оптимізація перевиділення',
    no_scaling_recommended: 'масштабування не рекомендовано'
  };

  function priorityClass(priority: string) {
    if (priority === 'critical' || priority === 'high') return 'text-red-700';
    if (priority === 'medium') return 'text-amber-700';
    return 'text-emerald-700';
  }

  async function load() {
    [recommendations, nodes] = await Promise.all([recommendationsApi.list(), nodesApi.list()]);
  }
  async function setStatus(id: number, action: 'accept' | 'ignore' | 'resolve') {
    await recommendationsApi[action](id);
    pushToast('Статус рекомендації оновлено', 'success');
    await load();
  }
  onMount(load);
</script>

<PageHeader title="Рекомендації масштабування" />

<div class="grid gap-3 xl:grid-cols-2">
  {#each recommendations as rec}
    <Card>
      <div class="flex items-start justify-between gap-3 border-b border-line pb-3">
        <div>
          <h2 class="text-base font-semibold text-slate-950">{rec.title}</h2>
          <p class="mt-1 text-sm text-slate-700">{nodeNames[rec.node_id] || rec.node_id} · {typeLabels[rec.recommendation_type] || rec.recommendation_type} · {statusLabels[rec.status] || rec.status}</p>
        </div>
        <span class={`text-sm font-medium ${priorityClass(rec.priority)}`}>{priorityLabels[rec.priority] || rec.priority}</span>
      </div>
      <div class="mt-3 grid gap-3 text-sm md:grid-cols-2">
        <div>
          <p class="font-semibold text-slate-900">Причина</p>
          <p class="mt-1 text-slate-700">{rec.reason}</p>
        </div>
        <div>
          <p class="font-semibold text-slate-900">Поточний стан</p>
          <p class="mt-1 text-slate-700">CPU: {rec.current_cpu_cores ?? '—'} ядер · RAM: {rec.current_ram_mb ? Math.round(rec.current_ram_mb / 1024) : '—'} GB</p>
        </div>
        <div>
          <p class="font-semibold text-slate-900">Рекомендована дія</p>
          <p class="mt-1 text-slate-700">{rec.description}</p>
        </div>
        <div>
          <p class="font-semibold text-slate-900">Очікуваний ефект</p>
          <p class="mt-1 text-slate-700">{rec.expected_effect}</p>
        </div>
      </div>
      {#if Array.isArray(rec.action_steps_json)}
        <ul class="mt-4 space-y-2 text-sm text-slate-700">
          {#each rec.action_steps_json as action}
            <li class="rounded border border-line bg-slate-50 p-2">{action}</li>
          {/each}
        </ul>
      {/if}
      <div class="mt-4 flex flex-wrap gap-2">
        <Button size="sm" variant="secondary" on:click={() => setStatus(rec.id, 'accept')}>Прийняти</Button>
        <Button size="sm" variant="ghost" on:click={() => setStatus(rec.id, 'ignore')}>Ігнорувати</Button>
        <Button size="sm" variant="ghost" on:click={() => setStatus(rec.id, 'resolve')}>Закрити</Button>
      </div>
    </Card>
  {/each}
</div>
