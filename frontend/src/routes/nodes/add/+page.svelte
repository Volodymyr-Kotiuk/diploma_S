<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
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

<PageHeader
  title="Додати вузол"
>
  <a slot="actions" href="/dashboard"><Button variant="secondary">Повернутися на головний екран</Button></a>
</PageHeader>

<div class="grid gap-4 xl:grid-cols-[320px_1fr]">
  <Card>
    <h2 class="text-base font-semibold text-slate-950">Тип вузла</h2>
    <div class="mt-4 space-y-2">
      <button
        class={`w-full rounded border px-3 py-3 text-left text-sm ${mode === 'agent' ? 'border-brand-700 bg-slate-100 font-semibold text-slate-950' : 'border-line text-slate-800'}`}
        on:click={() => selectMode('agent')}
      >
        Підключити реальну машину
        <span class="block text-xs font-normal text-slate-700">Для ПК або сервера, де буде запущено агент збору метрик.</span>
      </button>
      <button
        class={`w-full rounded border px-3 py-3 text-left text-sm ${mode === 'virtual' ? 'border-brand-700 bg-slate-100 font-semibold text-slate-950' : 'border-line text-slate-800'}`}
        on:click={() => selectMode('virtual')}
      >
        Віртуальний вузол
        <span class="block text-xs font-normal text-slate-700">Тестова модель ресурсу для сценаріїв навантаження.</span>
      </button>
    </div>
  </Card>

  <Card>
    <h2 class="text-base font-semibold text-slate-950">
      {mode === 'agent' ? 'Підключити реальну машину' : 'Віртуальний вузол'}
    </h2>
    <div class="mt-4 grid gap-4 md:grid-cols-2">
      <label class="text-sm font-medium text-slate-800">
        Назва вузла
        <input bind:value={name} class="mt-1 h-9 w-full rounded border border-slate-300 bg-white px-3 text-sm" />
      </label>
      <label class="text-sm font-medium text-slate-800">
        Роль, необов’язково
        <select bind:value={role} class="mt-1 h-9 w-full rounded border border-slate-300 bg-white px-3 text-sm">
          {#each roles as item}
            <option value={item.value}>{item.label}</option>
          {/each}
        </select>
      </label>
      {#if mode === 'virtual'}
        <label class="text-sm font-medium text-slate-800">
          Ядра CPU
          <input type="number" min="1" bind:value={cpu} class="mt-1 h-9 w-full rounded border border-slate-300 bg-white px-3 text-sm" />
        </label>
        <label class="text-sm font-medium text-slate-800">
          Оперативна пам’ять, MB
          <input type="number" min="512" step="512" bind:value={ram} class="mt-1 h-9 w-full rounded border border-slate-300 bg-white px-3 text-sm" />
        </label>
        <label class="text-sm font-medium text-slate-800">
          Диск, GB
          <input type="number" min="10" bind:value={disk} class="mt-1 h-9 w-full rounded border border-slate-300 bg-white px-3 text-sm" />
        </label>
      {/if}
    </div>
    <div class="mt-5">
      {#if mode === 'agent'}
        <Button on:click={createAgentNode}>Створити реальний вузол</Button>
      {:else}
        <Button on:click={createVirtualNode}>Створити віртуальний вузол</Button>
      {/if}
    </div>

    {#if agentResult}
      <section class="mt-6 border-t border-line pt-4 text-sm">
        <div class="flex flex-col gap-1 md:flex-row md:items-baseline md:justify-between">
          <h3 class="text-base font-semibold text-slate-950">Підключення агента</h3>
          <span class="text-slate-700">Статус: очікує підключення агента</span>
        </div>

        <div class="mt-4 space-y-4">
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
            <pre class="mt-2 overflow-x-auto rounded border border-line bg-white p-3"><code>{agentResult.install_command}</code></pre>
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
  </Card>
</div>
