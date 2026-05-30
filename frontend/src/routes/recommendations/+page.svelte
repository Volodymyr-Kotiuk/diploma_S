<script lang="ts">
  import { onMount } from 'svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
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

<section class="rounded-lg border border-[#d7dde6] bg-white p-5">
  {#each recommendations as rec}
    <div class="border-b border-[#e5e9f0] py-4 first:pt-0 last:border-b-0 last:pb-0">
      <div class="flex items-start justify-between gap-4">
        <div>
          <h2 class="text-base font-semibold text-slate-950">{rec.title}</h2>
          <p class="mt-1 text-sm text-slate-600">{nodeNames[rec.node_id] || rec.node_id} · {typeLabels[rec.recommendation_type] || rec.recommendation_type}</p>
        </div>
        <div class="flex flex-col items-end gap-2 text-sm">
          <span class="font-medium text-[#1f2937]">{priorityLabels[rec.priority] || rec.priority}</span>
          <StatusBadge status={rec.status} />
        </div>
      </div>
      <div class="mt-3 grid gap-3 text-sm md:grid-cols-2">
        <div>
          <p class="font-semibold text-slate-900">Причина</p>
          <p class="mt-1 text-slate-600">{rec.reason}</p>
        </div>
        <div>
          <p class="font-semibold text-slate-900">Поточний стан</p>
          <p class="mt-1 text-slate-600">CPU: {rec.current_cpu_cores ?? '—'} ядер · RAM: {rec.current_ram_mb ? Math.round(rec.current_ram_mb / 1024) : '—'} GB</p>
        </div>
        <div>
          <p class="font-semibold text-slate-900">Рекомендована дія</p>
          <p class="mt-1 text-slate-600">{rec.description}</p>
        </div>
        <div>
          <p class="font-semibold text-slate-900">Очікуваний ефект</p>
          <p class="mt-1 text-slate-600">{rec.expected_effect}</p>
        </div>
      </div>
      {#if Array.isArray(rec.action_steps_json)}
        <ul class="mt-4 list-disc space-y-1 pl-5 text-sm text-slate-600">
          {#each rec.action_steps_json as action}
            <li>{action}</li>
          {/each}
        </ul>
      {/if}
      <div class="mt-4 flex flex-wrap gap-2">
        <Button size="sm" variant="secondary" on:click={() => setStatus(rec.id, 'accept')}>Прийняти</Button>
        <Button size="sm" variant="ghost" on:click={() => setStatus(rec.id, 'ignore')}>Ігнорувати</Button>
        <Button size="sm" variant="ghost" on:click={() => setStatus(rec.id, 'resolve')}>Закрити</Button>
      </div>
    </div>
  {/each}
</section>
