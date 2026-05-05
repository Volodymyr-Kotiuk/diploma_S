<script lang="ts">
  export let rows = 4;
</script>

<div class="space-y-3">
  {#each Array(rows) as _}
    <div class="h-14 rounded border border-line bg-slate-100"></div>
  {/each}
</div>
