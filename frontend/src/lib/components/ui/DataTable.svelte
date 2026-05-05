<script lang="ts">
  export let columns: { key: string; label: string }[] = [];
  export let rows: Record<string, unknown>[] = [];
</script>

<div class="overflow-x-auto rounded border border-line bg-white">
  <table class="min-w-full divide-y divide-line text-sm">
    <thead class="bg-slate-100 text-left text-xs uppercase tracking-normal text-slate-700">
      <tr>
        {#each columns as column}
          <th class="px-4 py-3 font-semibold">{column.label}</th>
        {/each}
      </tr>
    </thead>
    <tbody class="divide-y divide-slate-200">
      {#each rows as row}
        <tr>
          {#each columns as column}
            <td class="px-4 py-3 text-slate-800">{row[column.key] ?? '—'}</td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>
