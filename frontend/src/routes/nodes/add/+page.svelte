<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { ArrowLeft } from 'lucide-svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import { agentsApi, type AgentTokenResponse } from '$lib/api/agents';
  import { nodesApi } from '$lib/api/nodes';
  import { pushToast } from '$lib/stores/app';

  let mode: 'agent' | 'virtual' = 'agent';
  let name = '';
  let role = '';
  let cpu = 2;
  let ram = 4096;
  let disk = 80;
  let agentResult: AgentTokenResponse | null = null;
  const dependencyCommand = 'pip install psutil requests';

  const roles = [
    { value: '', label: 'Не вказано' },
    { value: 'server', label: 'Сервер' },
    { value: 'service', label: 'Сервіс/API' },
    { value: 'database', label: 'База даних' },
    { value: 'other', label: 'Інше' }
  ];

  function selectMode(nextMode: 'agent' | 'virtual') {
    mode = nextMode;
    agentResult = null;
  }

  async function createAgentNode() {
    agentResult = await agentsApi.register({
      name: name || 'Реальний вузол',
      role: role || undefined
    });
    pushToast('Реальний вузол створено', 'success');
  }

  async function createVirtualNode() {
    const node = await nodesApi.create({
      name: name || 'Віртуальний вузол',
      node_type: 'virtual_node',
      role: role || 'unknown',
      status: 'waiting',
      allocated_cpu_cores: cpu,
      allocated_ram_mb: ram,
      max_cpu_cores: Math.max(cpu * 4, cpu),
      max_ram_mb: Math.max(ram * 4, ram),
      disk_total_gb: disk
    });
    pushToast('Віртуальний вузол створено', 'success');
    await goto(`/nodes/${node.id}`);
  }

  async function copyCommand() {
    if (!agentResult) return;
    try {
      await navigator.clipboard.writeText(agentResult.install_command);
      pushToast('Команду скопійовано', 'success');
    } catch {
      pushToast('Не вдалося скопіювати команду', 'error');
    }
  }

  onMount(() => {
    const type = $page.url.searchParams.get('type');
    if (type === 'virtual') mode = 'virtual';
    if (type === 'agent') mode = 'agent';
  });
</script>

<div class="add-page">
  <header class="add-heading">
    <h1>Додати вузол</h1>
    <a href="/dashboard">
      <Button variant="secondary" className="return-button">
        <ArrowLeft class="h-4 w-4" />
        Повернутися на головний екран
      </Button>
    </a>
  </header>

  <div class="add-layout">
    <aside class="type-column">
      <h2>Тип вузла</h2>
      <div class="type-options">
      <button
        class:active-type={mode === 'agent'}
        class="type-option"
        on:click={() => selectMode('agent')}
      >
        <span>Підключити реальну машину</span>
        <small>Для ПК або сервера, де буде запущено агент збору метрик.</small>
      </button>
      <button
        class:active-type={mode === 'virtual'}
        class="type-option"
        on:click={() => selectMode('virtual')}
      >
        <span>Віртуальний вузол</span>
        <small>Тестова модель ресурсу для сценаріїв навантаження.</small>
      </button>
      </div>
    </aside>

    <section class="form-column">
      <h2>
      {mode === 'agent' ? 'Підключити реальну машину' : 'Віртуальний вузол'}
      </h2>
      <div class="form-grid">
      <label>
        <span>Назва вузла</span>
        <input bind:value={name} placeholder="Введіть назву вузла" />
      </label>
      <label>
        <span>Роль, необов’язково</span>
        <select bind:value={role}>
          {#each roles as item}
            <option value={item.value}>{item.label}</option>
          {/each}
        </select>
      </label>
      {#if mode === 'virtual'}
        <label>
          <span>Ядра CPU</span>
          <input type="number" min="1" bind:value={cpu} />
        </label>
        <label>
          <span>Оперативна пам’ять, MB</span>
          <input type="number" min="512" step="512" bind:value={ram} />
        </label>
        <label>
          <span>Диск, GB</span>
          <input type="number" min="10" bind:value={disk} />
        </label>
      {/if}
      </div>
      <div class="form-actions">
      {#if mode === 'agent'}
        <Button on:click={createAgentNode}>Створити реальний вузол</Button>
      {:else}
        <Button on:click={createVirtualNode}>Створити віртуальний вузол</Button>
      {/if}
      </div>

      {#if agentResult}
        <section class="agent-result">
        <div class="flex flex-col gap-1 md:flex-row md:items-baseline md:justify-between">
          <h3 class="text-base font-semibold text-slate-950">Підключення агента</h3>
          <span class="text-slate-700">Статус: очікує підключення агента</span>
        </div>

        <div class="mt-4 space-y-4">
          <div>
            <p class="font-medium text-slate-900">1. Завантажте файл агента</p>
            <a
              class="mt-2 inline-flex h-[34px] items-center justify-center rounded-md border border-[#cbd5e1] bg-white px-3 text-sm font-semibold text-[#1f2937]"
              href={agentsApi.downloadUrl()}
              download="agent.py"
            >
              Завантажити agent.py
            </a>
          </div>

          <div>
            <p class="font-medium text-slate-900">2. Встановіть залежності на машині, яку потрібно підключити</p>
            <pre class="mt-2 overflow-x-auto rounded-md border border-[#e5e9f0] bg-[#f8fafc] p-3"><code>{dependencyCommand}</code></pre>
          </div>

          <div>
            <p class="font-medium text-slate-900">3. Запустіть агент</p>
            <pre class="mt-2 overflow-x-auto rounded-md border border-[#e5e9f0] bg-[#f8fafc] p-3"><code>{agentResult.install_command}</code></pre>
          </div>
        </div>

        <div class="mt-3 grid gap-2 md:grid-cols-2">
          <p><span class="text-slate-600">ID вузла:</span> {agentResult.node.id}</p>
          <p><span class="text-slate-600">Фрагмент токена:</span> {agentResult.token_preview}</p>
        </div>
        <div class="mt-4 flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" on:click={copyCommand}>Скопіювати команду</Button>
          <a href={`/nodes/${agentResult.node.id}`}><Button size="sm">Перейти до вузла</Button></a>
        </div>
        </section>
      {/if}
    </section>
  </div>
</div>

<style>
  .add-page {
    color: #111827;
  }

  .add-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    min-height: 128px;
    border-bottom: 1px solid #d7dde6;
  }

  .add-heading h1 {
    margin: 0;
    font-size: 32px;
    line-height: 1.2;
    font-weight: 700;
  }

  :global(.return-button) {
    height: 58px;
    padding-inline: 26px;
    border-radius: 3px;
    font-size: 17px;
    font-weight: 500;
    background: transparent;
  }

  .add-layout {
    display: grid;
    grid-template-columns: minmax(280px, 420px) minmax(0, 1fr);
    min-height: 620px;
    padding-top: 44px;
  }

  .type-column {
    border-right: 1px solid #d7dde6;
    padding-right: 32px;
  }

  .type-column h2,
  .form-column h2 {
    margin: 0 0 32px;
    font-size: 24px;
    line-height: 1.2;
    font-weight: 700;
  }

  .type-options {
    display: grid;
    gap: 16px;
  }

  .type-option {
    position: relative;
    width: 100%;
    min-height: 142px;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    background: transparent;
    padding: 26px 24px;
    text-align: left;
  }

  .type-option.active-type {
    border-color: #2f5cff;
    background: rgba(255, 255, 255, 0.24);
  }

  .type-option.active-type::before {
    content: "";
    position: absolute;
    left: -1px;
    top: 18px;
    width: 4px;
    height: 38px;
    background: #2f5cff;
  }

  .type-option span {
    display: block;
    font-size: 20px;
    line-height: 1.25;
    font-weight: 700;
    color: #111827;
  }

  .type-option small {
    display: block;
    margin-top: 8px;
    color: #52627a;
    font-size: 18px;
    line-height: 1.45;
  }

  .form-column {
    min-width: 0;
    padding-left: 58px;
  }

  .form-grid {
    display: grid;
    grid-template-columns: minmax(0, 0.9fr) minmax(0, 1fr);
    gap: 26px 54px;
  }

  .form-grid label {
    display: block;
  }

  .form-grid label span {
    display: block;
    margin-bottom: 12px;
    color: #334155;
    font-size: 17px;
    font-weight: 600;
  }

  .form-grid input,
  .form-grid select {
    width: 100%;
    height: 64px;
    border: 1px solid #cbd5e1;
    border-radius: 3px;
    background: transparent;
    padding: 0 22px;
    color: #111827;
    font-size: 20px;
  }

  .form-grid input::placeholder {
    color: #8a97aa;
  }

  .form-actions {
    margin-top: 34px;
  }

  .form-actions :global(button) {
    height: 58px;
    padding-inline: 26px;
    border-radius: 3px;
    font-size: 18px;
    font-weight: 500;
  }

  .agent-result {
    min-width: 0;
    max-width: 100%;
    margin-top: 34px;
    border-top: 1px solid #d7dde6;
    padding-top: 24px;
    font-size: 14px;
    overflow: hidden;
  }

  .agent-result pre {
    max-width: 100%;
    min-width: 0;
    overflow-x: auto;
    border-radius: 3px;
    white-space: pre;
  }

  .agent-result code {
    display: block;
    min-width: 0;
  }

  @media (max-width: 980px) {
    .add-heading {
      align-items: flex-start;
      flex-direction: column;
      justify-content: center;
      padding: 28px 0;
    }

    .add-layout,
    .form-grid {
      grid-template-columns: 1fr;
    }

    .type-column {
      border-right: 0;
      border-bottom: 1px solid #d7dde6;
      padding-right: 0;
      padding-bottom: 32px;
    }

    .form-column {
      padding-left: 0;
      padding-top: 32px;
    }
  }
</style>
