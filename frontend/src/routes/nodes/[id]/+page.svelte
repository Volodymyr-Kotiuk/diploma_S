<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
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
  $: currentRecommendations = recommendations.slice(0, 1);

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

  function metricLabel(metric?: string | null) {
    const labels: Record<string, string> = {
      cpu_usage_percent: 'Використання CPU',
      cpu_usage_percent_avg: 'Середнє використання CPU',
      load_average_1m: 'Середнє навантаження за 1 хв',
      ram_usage_percent: 'Використання RAM',
      ram_usage_percent_avg: 'Середнє використання RAM',
      ram_available_mb: 'Доступна RAM',
      swap_usage_percent: 'Використання підкачки',
      disk_read_rate: 'Швидкість читання з диска',
      disk_write_rate: 'Швидкість запису на диск',
      network_sent_rate: 'Вихідний мережевий трафік',
      network_recv_rate: 'Вхідний мережевий трафік',
      temperature_celsius: 'Температура',
      service_latency_ms: 'Затримка сервісу',
      service_error_rate: 'Частка помилок сервісу',
      anomaly_score: 'Оцінка аномалії',
      allocated_cpu_cores: 'Виділені ядра CPU',
      allocated_ram_mb: 'Виділена RAM',
      environment_allocated_cpu: 'CPU середовища',
      environment_allocated_ram_mb: 'RAM середовища',
      swap_pressure_condition: 'Умова навантаження підкачки'
    };
    return metric ? labels[metric] || metric : '—';
  }

  function boundedPercent(value?: number | null) {
    return Math.max(0, Math.min(100, Math.round(value ?? 0)));
  }

  function usageColor(value?: number | null) {
    const current = value ?? 0;
    if (current >= 90) return '#dc2626';
    if (current >= 75) return '#d97706';
    return '#2F4FDC';
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
    const generatedReport = await reportsApi.node(id);
    await reportsApi.download(generatedReport);
    pushToast('PDF-звіт створено та завантажено', 'success');
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
  <div class="node-page">
    <header class="node-heading">
      <div>
        <h1>Вузол: {node.name}</h1>
        <p>Діагностика обчислювальних ресурсів вузла</p>
      </div>
      <div class="node-actions">
        <Button on:click={runDiagnostics} className="node-action-primary">Запустити діагностику</Button>
        <Button variant="secondary" on:click={report} className="node-action">Експорт</Button>
        <Button variant="danger" on:click={removeNode} className="node-action-danger">Видалити вузол</Button>
      </div>
    </header>

    <section class="overview-grid">
      <div class="node-info">
        <div class="info-row">
          <span>Тип:</span>
          <strong>{typeLabel(node.node_type)}</strong>
        </div>
        <div class="info-row">
          <span>Статус:</span>
          <StatusBadge status={node.status} />
        </div>
        <div class="info-row">
          <span>Роль:</span>
          <strong>{roleLabel(node.role)}</strong>
        </div>
        <div class="info-row">
          <span>Ім’я хоста:</span>
          <strong>{node.hostname || '—'}</strong>
        </div>
        <div class="info-row">
          <span>Останній сигнал агента:</span>
          <strong>{shortDate(node.last_heartbeat_at)}</strong>
        </div>
        <div class="info-row">
          <span>Останні метрики:</span>
          <strong>{shortDate(latest?.timestamp)}</strong>
        </div>
      </div>

      {#if isVirtual}
        <div class="scenario-panel">
          <h2>Сценарій для віртуального вузла</h2>
          <p>Запустіть один сценарій деградації для генерації метрик і рекомендацій.</p>
          <div class="scenario-controls">
            <select bind:value={scenarioType}>
              {#each scenarioOptions as option}
                <option value={option.value}>{option.label}</option>
              {/each}
            </select>
            <Button on:click={runScenario} disabled={scenarioRunning} className="scenario-button">
              {scenarioRunning ? 'Виконується...' : 'Запустити сценарій'}
            </Button>
          </div>
        </div>
      {/if}

      {#if isAgent}
        <div class="scenario-panel">
          <h2>Підключення агента</h2>
          <p>
            {agentWaiting
              ? 'Запустіть команду на потрібному ПК або сервері, щоб система почала отримувати сигнали й метрики.'
              : 'Система отримує метрики з цієї машини. Команду можна використати для повторного запуску агента.'}
          </p>
          <div class="agent-steps">
            <a href={agentsApi.downloadUrl()} download="agent.py">Завантажити agent.py</a>
            <pre><code>{dependencyCommand}</code></pre>
            <pre><code>{installCommand}</code></pre>
            <Button size="sm" variant="secondary" on:click={copyInstallCommand}>Скопіювати команду</Button>
          </div>
        </div>
      {/if}
    </section>

    {#if latest}
      <section class="plain-section">
        <h2>Поточні метрики</h2>
        <div class="table-wrap">
          <table class="metric-table">
            <thead>
              <tr>
                <th>Показник</th>
                <th>Значення</th>
                <th></th>
                <th>Деталі</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>CPU</td>
                <td><strong>{percent(latest.cpu_usage_percent)}</strong></td>
                <td><span class="meter"><span style={`width: ${boundedPercent(latest.cpu_usage_percent)}%; background: ${usageColor(latest.cpu_usage_percent)}`}></span></span></td>
                <td>{latest.cpu_core_count || node.allocated_cpu_cores || 0} ядра</td>
              </tr>
              <tr>
                <td>RAM</td>
                <td><strong>{percent(latest.ram_usage_percent)}</strong></td>
                <td><span class="meter"><span style={`width: ${boundedPercent(latest.ram_usage_percent)}%; background: ${usageColor(latest.ram_usage_percent)}`}></span></span></td>
                <td>{mbToGb(latest.ram_used_mb)} / {mbToGb(latest.ram_total_mb)}</td>
              </tr>
              <tr>
                <td>Диск</td>
                <td><strong>{percent(latest.disk_usage_percent)}</strong></td>
                <td><span class="meter"><span style={`width: ${boundedPercent(latest.disk_usage_percent)}%; background: ${usageColor(latest.disk_usage_percent)}`}></span></span></td>
                <td>{latest.disk_used_gb || 0} GB / {latest.disk_total_gb || node.disk_total_gb || 0} GB</td>
              </tr>
              <tr>
                <td>Мережа</td>
                <td><strong>{bytesRate(Math.max(latest.network_recv_rate || 0, latest.network_sent_rate || 0))}</strong></td>
                <td></td>
                <td>макс. отримання/передавання</td>
              </tr>
              <tr>
                <td>Підкачка</td>
                <td><strong>{percent(latest.swap_usage_percent)}</strong></td>
                <td><span class="meter"><span style={`width: ${boundedPercent(latest.swap_usage_percent)}%; background: ${usageColor(latest.swap_usage_percent)}`}></span></span></td>
                <td>swap</td>
              </tr>
              <tr>
                <td>Процеси</td>
                <td><strong>{latest.process_count || 0}</strong></td>
                <td></td>
                <td></td>
              </tr>
              <tr>
                <td>Час роботи</td>
                <td><strong>{uptime(latest.uptime_seconds)}</strong></td>
                <td></td>
                <td></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="plain-section charts-section">
        <h2>Графіки метрик</h2>
        <div class="chart-grid">
          <div><CpuChart {metrics} height={240} /></div>
          <div><RamChart {metrics} height={240} /></div>
          <div><DiskChart {metrics} height={240} /></div>
          <div><NetworkChart {metrics} height={240} /></div>
          <div><SwapChart {metrics} height={190} /></div>
        </div>
      </section>
    {:else}
      <EmptyState title="Метрики ще не отримані" text={isAgent ? 'Запустіть агент збору метрик на цій машині.' : 'Запустіть сценарій для віртуального вузла, щоб згенерувати історію метрик.'} />
    {/if}

    <section class="plain-section diagnosis-section">
      <h2>Діагностика</h2>
      {#if diagnosis}
        <div class="diagnosis-summary">
          <div>
            <span>Першопричина:</span>
            <strong>{rootCauseLabel(diagnosis.root_cause)}</strong>
          </div>
          <div>
            <span>Статус:</span>
            <StatusBadge status={diagnosis.severity || 'unknown'} />
          </div>
          <div>
            <span>Рівень:</span>
            <strong>{severityLabel(diagnosis.severity)}</strong>
          </div>
          <div>
            <span>Впевненість:</span>
            <strong>{Math.round(diagnosis.confidence)}%</strong>
          </div>
          <div>
            <span>Ризик вузла:</span>
            <strong>{Math.round(diagnosis.risk_score)}</strong>
          </div>
        </div>
        <p class="diagnosis-text">{helperText[diagnosis.diagnosis_type] || diagnosis.explanation}</p>
        {#if diagnosis.evidence_json?.evidence?.length}
          <table class="evidence-table">
            <thead>
              <tr>
                <th>Метрика</th>
                <th>Значення / поріг</th>
                <th>Опис</th>
              </tr>
            </thead>
            <tbody>
              {#each diagnosis.evidence_json.evidence as ev}
                <tr>
                  <td><strong>{metricLabel(ev.metric)}</strong></td>
                  <td>{String(ev.current_value)} / {String(ev.threshold)}</td>
                  <td>{ev.explanation}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        {/if}
      {:else}
        <p class="section-note">Діагностику ще не виконано.</p>
      {/if}
    </section>

    <section class="plain-section recommendations-section">
      <h2>Рекомендації</h2>
      {#each currentRecommendations as rec}
        <div class="recommendation-text">
          <p>{rec.description}</p>
          <p>{rec.reason}</p>
          {#if Array.isArray(rec.action_steps_json)}
            <ul>
              {#each rec.action_steps_json as action}
                <li>{action}</li>
              {/each}
            </ul>
          {/if}
        </div>
      {:else}
        <p class="section-note">Рекомендацій ще немає.</p>
      {/each}
    </section>

    <section class="plain-section incidents-section">
      <h2>Інциденти</h2>
      {#if incidents.length}
        {#each incidents as incident}
          <div class="incident-row">
            <div>
              <div class="incident-title">
                <strong>{rootCauseLabel(incident.title)}</strong>
                <StatusBadge status={incident.status} />
              </div>
              <p>{incident.description}</p>
            </div>
            <time>{shortDate(incident.started_at)}</time>
          </div>
        {/each}
      {:else}
        <p class="section-note">Інцидентів немає.</p>
      {/if}
    </section>
  </div>
{/if}

<style>
  .node-page {
    color: #111827;
    font-size: 14px;
  }

  .node-heading {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 24px;
    margin-bottom: 34px;
  }

  .node-heading h1 {
    margin: 0;
    font-size: 24px;
    line-height: 1.2;
    font-weight: 700;
  }

  .node-heading p {
    margin: 10px 0 0;
    color: #52627a;
    font-size: 14px;
  }

  .node-actions {
    display: flex;
    gap: 14px;
    white-space: nowrap;
  }

  :global(.node-action-primary),
  :global(.node-action),
  :global(.node-action-danger),
  :global(.scenario-button) {
    height: 38px;
    padding-inline: 18px;
    font-size: 14px;
  }

  .overview-grid {
    display: grid;
    grid-template-columns: minmax(320px, 0.9fr) minmax(420px, 1fr);
    gap: 56px;
    margin-bottom: 36px;
  }

  .node-info {
    display: grid;
    gap: 13px;
    max-width: 520px;
  }

  .info-row {
    display: grid;
    grid-template-columns: 220px 1fr;
    align-items: center;
    gap: 16px;
  }

  .info-row span {
    color: #52627a;
    font-weight: 600;
  }

  .info-row strong {
    font-weight: 700;
  }

  .scenario-panel {
    min-height: 126px;
    border-left: 1px solid #d7dde6;
    padding-left: 34px;
  }

  .scenario-panel h2,
  .plain-section h2 {
    margin: 0;
    color: #111827;
    font-size: 16px;
    line-height: 1.25;
    font-weight: 700;
  }

  .scenario-panel p {
    margin: 12px 0 28px;
    color: #52627a;
  }

  .scenario-controls {
    display: grid;
    grid-template-columns: minmax(260px, 1fr) auto;
    gap: 24px;
    align-items: center;
  }

  .scenario-controls select {
    height: 38px;
    width: 100%;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    background: transparent;
    padding: 0 12px;
    color: #111827;
  }

  .agent-steps {
    display: grid;
    gap: 10px;
    margin-top: 16px;
  }

  .agent-steps a {
    width: fit-content;
    color: #1d4ed8;
    font-weight: 700;
  }

  .agent-steps pre {
    margin: 0;
    overflow-x: auto;
    border: 1px solid #d7dde6;
    border-radius: 4px;
    padding: 10px;
    background: rgba(255, 255, 255, 0.45);
  }

  .plain-section {
    margin-bottom: 28px;
  }

  .plain-section h2 {
    margin-bottom: 12px;
  }

  .table-wrap {
    border-top: 1px solid #d7dde6;
  }

  .metric-table,
  .evidence-table {
    width: 100%;
    border-collapse: collapse;
  }

  .metric-table th,
  .metric-table td,
  .evidence-table th,
  .evidence-table td {
    border-bottom: 1px solid #d7dde6;
    padding: 8px 8px;
    text-align: left;
    vertical-align: middle;
  }

  .metric-table th,
  .evidence-table th {
    color: #52627a;
    font-size: 13px;
    font-weight: 700;
  }

  .metric-table td:nth-child(1) {
    width: 22%;
  }

  .metric-table td:nth-child(2) {
    width: 8%;
    font-variant-numeric: tabular-nums;
  }

  .metric-table td:nth-child(3) {
    width: 23%;
  }

  .meter {
    display: block;
    width: 220px;
    max-width: 100%;
    height: 2px;
    background: transparent;
  }

  .meter span {
    display: block;
    height: 100%;
  }

  .chart-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    column-gap: 56px;
    row-gap: 34px;
  }

  .chart-grid > div {
    min-width: 0;
  }

  .diagnosis-summary {
    display: grid;
    grid-template-columns: 1.45fr 1fr 0.7fr 0.7fr 0.7fr;
    gap: 28px;
    margin-top: 6px;
  }

  .diagnosis-summary span {
    display: block;
    margin-bottom: 8px;
    color: #52627a;
    font-weight: 600;
  }

  .diagnosis-summary strong {
    font-weight: 700;
  }

  .diagnosis-text,
  .recommendation-text p,
  .incident-row p,
  .section-note {
    color: #334155;
    line-height: 1.5;
  }

  .diagnosis-text {
    margin: 16px 0 10px;
  }

  .evidence-table {
    margin-top: 10px;
  }

  .recommendation-text p {
    margin: 0 0 6px;
  }

  .recommendation-text ul {
    margin: 8px 0 0;
    padding-left: 22px;
  }

  .recommendation-text li {
    margin-bottom: 4px;
  }

  .incident-row {
    display: grid;
    grid-template-columns: 1fr 140px;
    gap: 20px;
    border-top: 1px solid #d7dde6;
    padding: 12px 0;
  }

  .incident-title {
    display: flex;
    align-items: center;
    gap: 18px;
    margin-bottom: 4px;
  }

  .incident-row p {
    margin: 0;
  }

  .incident-row time {
    color: #52627a;
    text-align: right;
    white-space: nowrap;
  }

  @media (max-width: 900px) {
    .node-heading,
    .node-actions {
      flex-wrap: wrap;
    }

    .overview-grid,
    .chart-grid,
    .diagnosis-summary {
      grid-template-columns: 1fr;
    }

    .scenario-panel {
      border-left: 0;
      border-top: 1px solid #d7dde6;
      padding-left: 0;
      padding-top: 24px;
    }

    .scenario-controls,
    .info-row,
    .incident-row {
      grid-template-columns: 1fr;
    }

    .incident-row time {
      text-align: left;
    }
  }
</style>
