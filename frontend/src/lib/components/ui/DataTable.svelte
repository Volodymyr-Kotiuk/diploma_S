<script lang="ts">
  export let columns: { key: string; label: string }[] = [];
  export let rows: Record<string, unknown>[] = [];
</script>

<div class="overflow-x-auto rounded-lg border border-[#d7dde6] bg-white">
  <table class="min-w-full divide-y divide-line text-sm">
    <thead class="bg-slate-50 text-left text-[11px] uppercase tracking-normal text-slate-500">
      <tr>
        {#each columns as column}
          <th class="px-4 py-3 font-semibold">{column.label}</th>
        {/each}
      </tr>
    </thead>
    <tbody class="divide-y divide-slate-100">
      {#each rows as row}
        <tr>
          {#each columns as column}
            <td class="px-4 py-3.5 text-slate-800">{row[column.key] ?? '—'}</td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>
