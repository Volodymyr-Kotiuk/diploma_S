<script lang="ts">
  export let rows = 4;
</script>

<div class="space-y-3">
  {#each Array(rows) as _}
    <div class="h-14 rounded-lg border border-[#d7dde6] bg-white"></div>
  {/each}
</div>
