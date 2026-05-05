<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import MetricCard from '$lib/components/ui/MetricCard.svelte';
  import RiskBadge from '$lib/components/ui/RiskBadge.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import CpuChart from '$lib/components/charts/CpuChart.svelte';
  import DiskChart from '$lib/components/charts/DiskChart.svelte';
  import NetworkChart from '$lib/components/charts/NetworkChart.svelte';
  import RamChart from '$lib/components/charts/RamChart.svelte';
  import SwapChart from '$lib/components/charts/SwapChart.svelte';
  import { agentsApi } from '$lib/api/agents';
  import { diagnosticsApi } from '$lib/api/diagnostics';
  import { incidentsApi } from '$lib/api/incidents';
  import { nodesApi } from '$lib/api/nodes';
  import { reportsApi } from '$lib/api/reports';
  import { simulationApi } from '$lib/api/simulation';
  import { bytesRate, mbToGb, percent, shortDate, uptime } from '$lib/utils/formatters';
  import { helperText } from '$lib/utils/constants';
  import { pushToast } from '$lib/stores/app';
  import type { Diagnostic, Incident, Node, Recommendation, ResourceMetric } from '$lib/types';

  let node: Node | null = null;
  let metrics: ResourceMetric[] = [];
  let diagnostics: Diagnostic[] = [];
  let incidents: Incident[] = [];
  let recommendations: Recommendation[] = [];
  let installCommand = '';
  let scenarioType = 'cpu_saturation';
  let scenarioRunning = false;
  const dependencyCommand = 'pip install psutil requests';

  const scenarioOptions = [
    { value: 'cpu_saturation', label: 'Перевантаження CPU' },
    { value: 'memory_pressure', label: 'Нестача пам’яті' },
    { value: 'disk_io_bottleneck', label: 'Проблема диска' },
    { value: 'network_pressure', label: 'Навантаження мережі' },
    { value: 'underutilization', label: 'Недовикористання ресурсів' }
  ];

  $: id = Number($page.params.id);
  $: latest = metrics[metrics.length - 1];
  $: diagnosis = diagnostics[0];
  $: isAgent = node?.node_type === 'remote_agent';
  $: isVirtual = node?.node_type === 'virtual_node' || node?.node_type === 'simulated_vm';
  $: agentWaiting = isAgent && (!node?.last_heartbeat_at || node.status === 'waiting' || node.status === 'offline');

  function typeLabel(type?: string) {
    return type === 'remote_agent' ? 'Реальний вузол' : 'Віртуальний вузол';
  }

  function severityLabel(severity?: string | null) {
    const labels: Record<string, string> = {
      low: 'низький',
      medium: 'середній',
      high: 'високий',
      critical: 'критичний'
    };
    return severity ? labels[severity] || severity : '—';
  }

  function rootCauseLabel(value?: string | null) {
    const labels: Record<string, string> = {
      'CPU saturation': 'Перевантаження CPU',
      'Memory pressure': 'Нестача оперативної пам’яті',
      'Swap pressure': 'Надмірне використання підкачки',
      'Disk I/O bottleneck': 'Обмеження дискових операцій',
      'Network pressure': 'Навантаження мережі',
      'Thermal risk': 'Температурний ризик',
      'Resource overcommit': 'Перевиділення ресурсів',
      Underutilization: 'Недовикористання ресурсів',
      'Service degradation': 'Деградація сервісу',
      'Unknown degradation': 'Невизначена деградація'
    };
    return value ? labels[value] || value : '—';
  }

  function roleLabel(role?: string | null) {
    const labels: Record<string, string> = {
      server: 'Сервер',
      service: 'Сервіс/API',
      database: 'База даних',
      other: 'Інше'
    };
    return role && role !== 'unknown' ? labels[role] || role : '—';
  }

  async function load() {
    [node, metrics, diagnostics, recommendations] = await Promise.all([
      nodesApi.get(id),
      nodesApi.metrics(id),
      nodesApi.diagnostics(id),
      nodesApi.recommendations(id)
    ]);
    incidents = await incidentsApi.list(`?node_id=${id}`);
    if (node.node_type === 'remote_agent') {
      installCommand = (await agentsApi.installCommand(id)).install_command;
    }
  }

  async function runDiagnostics() {
    await diagnosticsApi.run(id);
    pushToast('Діагностику виконано', 'success');
    await load();
  }

  async function runScenario() {
    scenarioRunning = true;
    try {
      await simulationApi.runNodeScenario(id, { scenario_type: scenarioType, duration_seconds: 300, intensity: 0.9 });
      pushToast('Сценарій виконано', 'success');
      await load();
    } finally {
      scenarioRunning = false;
    }
  }

  async function report() {
    await reportsApi.node(id);
    pushToast('PDF-звіт створено', 'success');
  }

  async function removeNode() {
    await nodesApi.remove(id);
    pushToast('Вузол видалено', 'success');
    await goto('/dashboard');
  }

  async function copyInstallCommand() {
    try {
      await navigator.clipboard.writeText(installCommand);
      pushToast('Команду скопійовано', 'success');
    } catch {
      pushToast('Не вдалося скопіювати команду', 'error');
    }
  }

  onMount(load);
</script>

{#if node}
  <PageHeader title={`Вузол: ${node.name}`} description="Діагностика обчислювальних ресурсів вузла">
    <div slot="actions" class="flex gap-2">
      <Button on:click={runDiagnostics}>Запустити діагностику</Button>
      <Button variant="secondary" on:click={report}>Експорт</Button>
      <Button variant="danger" on:click={removeNode}>Видалити вузол</Button>
    </div>
  </PageHeader>

  <section class="mb-5 border-b border-line pb-4">
    <div class="grid gap-x-6 gap-y-3 text-sm md:grid-cols-3 xl:grid-cols-6">
      <div>
        <p class="text-slate-600">Тип</p>
        <p class="mt-1 font-medium text-slate-950">{typeLabel(node.node_type)}</p>
      </div>
      <div>
        <p class="text-slate-600">Статус</p>
        <div class="mt-1"><StatusBadge status={node.status} /></div>
      </div>
      <div>
        <p class="text-slate-600">Ім’я хоста</p>
        <p class="mt-1 font-medium text-slate-950">{node.hostname || '—'}</p>
      </div>
      <div>
        <p class="text-slate-600">Роль</p>
        <p class="mt-1 font-medium text-slate-950">{roleLabel(node.role)}</p>
      </div>
      <div>
        <p class="text-slate-600">Останній сигнал агента</p>
        <p class="mt-1 font-medium text-slate-950">{shortDate(node.last_heartbeat_at)}</p>
      </div>
      <div>
        <p class="text-slate-600">Останні метрики</p>
        <p class="mt-1 font-medium text-slate-950">{shortDate(latest?.timestamp)}</p>
      </div>
    </div>
    {#if node.description}
      <p class="mt-4 text-sm text-slate-700">{node.description}</p>
    {/if}
  </section>

  {#if isAgent}
    <section class="mb-5 border-b border-line pb-4">
      <div class="flex flex-col gap-1 md:flex-row md:items-baseline md:justify-between">
        <h2 class="text-base font-semibold text-slate-950">Підключення агента</h2>
        <span class="text-sm text-slate-700">{agentWaiting ? 'Агент ще не підключений' : 'Агент передає метрики'}</span>
      </div>
      <p class="mt-2 text-sm text-slate-700">
        {agentWaiting
          ? 'Запустіть команду на потрібному ПК або сервері, щоб система почала отримувати сигнали й метрики.'
          : 'Система отримує метрики з цієї машини. Команду можна використати для повторного запуску агента.'}
      </p>

      <div class="mt-4 space-y-4 text-sm">
        <div>
          <p class="font-medium text-slate-900">1. Завантажте файл агента</p>
          <a
            class="mt-2 inline-flex h-8 items-center justify-center rounded border border-line bg-white px-3 text-sm font-medium text-slate-900"
            href={agentsApi.downloadUrl()}
            download="agent.py"
          >
            Завантажити agent.py
          </a>
        </div>

        <div>
          <p class="font-medium text-slate-900">2. Встановіть залежності на машині, яку потрібно підключити</p>
          <pre class="mt-2 overflow-x-auto rounded border border-line bg-white p-3"><code>{dependencyCommand}</code></pre>
        </div>

        <div>
          <p class="font-medium text-slate-900">3. Запустіть агент</p>
          <pre class="mt-2 overflow-x-auto rounded border border-line bg-white p-3"><code>{installCommand}</code></pre>
          <div class="mt-2">
            <Button size="sm" variant="secondary" on:click={copyInstallCommand}>Скопіювати команду</Button>
          </div>
        </div>
      </div>
    </section>
  {/if}

  {#if isVirtual}
    <section class="mb-5 border-b border-line pb-4">
      <div class="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 class="text-base font-semibold text-slate-950">Сценарій для віртуального вузла</h2>
          <p class="mt-1 text-sm text-slate-700">Запустіть один сценарій деградації для генерації метрик і рекомендацій.</p>
        </div>
        <div class="flex flex-col gap-3 md:flex-row">
        <select bind:value={scenarioType} class="h-9 rounded border border-slate-200 bg-white px-3 text-sm md:w-[280px]">
          {#each scenarioOptions as option}
            <option value={option.value}>{option.label}</option>
          {/each}
        </select>
        <Button on:click={runScenario} disabled={scenarioRunning}>{scenarioRunning ? 'Виконується...' : 'Запустити сценарій'}</Button>
        </div>
      </div>
    </section>
  {/if}

  {#if latest}
    <section class="mb-6">
      <h2 class="mb-3 text-base font-semibold text-slate-950">Поточні метрики</h2>
      <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-7">
        <MetricCard label="CPU" value={percent(latest.cpu_usage_percent)} progress={latest.cpu_usage_percent || 0} accent="bg-brand-600" helper={`${latest.cpu_core_count || node.allocated_cpu_cores || 0} ядер`} />
        <MetricCard label="RAM" value={percent(latest.ram_usage_percent)} progress={latest.ram_usage_percent || 0} accent="bg-sky-500" helper={`${mbToGb(latest.ram_used_mb)} / ${mbToGb(latest.ram_total_mb)}`} />
        <MetricCard label="Диск" value={percent(latest.disk_usage_percent)} progress={latest.disk_usage_percent || 0} accent="bg-amber-500" helper={`${latest.disk_used_gb || 0} / ${latest.disk_total_gb || node.disk_total_gb || 0} GB`} />
        <MetricCard label="Мережа" value={bytesRate(Math.max(latest.network_recv_rate || 0, latest.network_sent_rate || 0))} accent="bg-indigo-500" helper="макс. отримання/передавання" />
        <MetricCard label="Підкачка" value={percent(latest.swap_usage_percent)} progress={latest.swap_usage_percent || 0} accent="bg-slate-500" />
        <MetricCard label="Процеси" value={latest.process_count || 0} accent="bg-slate-500" />
        <MetricCard label="Час роботи" value={uptime(latest.uptime_seconds)} accent="bg-slate-500" />
      </div>
    </section>

    <section class="mb-6">
      <h2 class="mb-3 text-base font-semibold text-slate-950">Графіки метрик</h2>
      <div class="grid gap-4 xl:grid-cols-2">
        <div class="rounded bg-white p-3"><CpuChart {metrics} /></div>
        <div class="rounded bg-white p-3"><RamChart {metrics} /></div>
        <div class="rounded bg-white p-3"><DiskChart {metrics} /></div>
        <div class="rounded bg-white p-3"><NetworkChart {metrics} /></div>
        <div class="rounded bg-white p-3"><SwapChart {metrics} /></div>
      </div>
    </section>
  {:else}
    <EmptyState title="Метрики ще не отримані" text={isAgent ? 'Запустіть агент збору метрик на цій машині.' : 'Запустіть сценарій для віртуального вузла, щоб згенерувати історію метрик.'} />
  {/if}

  <div class="space-y-6">
    <section class="border-t border-line pt-4">
      <h2 class="text-base font-semibold text-slate-950">Діагностика</h2>
      {#if diagnosis}
        <div class="mt-4">
          <div class="grid gap-3 text-sm md:grid-cols-4">
            <div><p class="text-slate-600">Першопричина</p><p class="mt-1 font-semibold">{rootCauseLabel(diagnosis.root_cause)}</p></div>
            <div><p class="text-slate-600">Рівень</p><p class="mt-1 font-semibold">{severityLabel(diagnosis.severity)}</p></div>
            <div><p class="text-slate-600">Впевненість</p><p class="mt-1 font-semibold">{Math.round(diagnosis.confidence)}%</p></div>
            <div><p class="text-slate-600">Ризик вузла</p><div class="mt-1"><RiskBadge value={diagnosis.risk_score} /></div></div>
          </div>
          <p class="mt-3 text-sm text-slate-700">{helperText[diagnosis.diagnosis_type] || diagnosis.explanation}</p>
          <div class="mt-4 space-y-2">
            {#each diagnosis.evidence_json?.evidence || [] as ev}
              <div class="rounded bg-slate-50 p-3 text-sm ring-1 ring-slate-200/70">
                <span class="font-medium">{ev.metric}</span>: {String(ev.current_value)} / поріг {String(ev.threshold)}
                <p class="mt-1 text-slate-700">{ev.explanation}</p>
              </div>
            {/each}
          </div>
        </div>
      {:else}
        <p class="mt-3 text-sm text-slate-700">Діагностику ще не виконано.</p>
      {/if}
    </section>

    <section class="border-t border-line pt-4">
      <h2 class="text-base font-semibold text-slate-950">Рекомендації вузла</h2>
      <ol class="mt-4 space-y-4">
        {#each recommendations.slice(0, 4) as rec}
          <li class="border-b border-line pb-4 text-sm last:border-b-0 last:pb-0">
            <p class="font-medium text-slate-950">{rec.title}</p>
            <p class="mt-1 text-slate-700">{rec.description}</p>
            <p class="mt-2 text-slate-700"><span class="font-medium">Причина:</span> {rec.reason}</p>
            {#if Array.isArray(rec.action_steps_json)}
              <ul class="mt-2 list-disc space-y-1 pl-5 text-slate-700">
                {#each rec.action_steps_json as action}
                  <li>{action}</li>
                {/each}
              </ul>
            {/if}
          </li>
        {:else}
          <p class="text-sm text-slate-700">Рекомендацій ще немає.</p>
        {/each}
      </ol>
    </section>

    <section class="border-t border-line pt-4">
      <h2 class="text-base font-semibold text-slate-950">Інциденти вузла</h2>
      <div class="mt-3 divide-y divide-line">
        {#each incidents as incident}
          <div class="py-3 text-sm">
            <div class="flex flex-col gap-1 md:flex-row md:justify-between md:gap-3">
              <span class="font-medium text-slate-950">{incident.title}</span>
              <span class="text-slate-700">{shortDate(incident.started_at)}</span>
            </div>
            <p class="mt-1 text-slate-700">{incident.description}</p>
          </div>
        {:else}
          <p class="text-sm text-slate-700">Інцидентів немає.</p>
        {/each}
      </div>
    </section>
  </div>
{/if}
