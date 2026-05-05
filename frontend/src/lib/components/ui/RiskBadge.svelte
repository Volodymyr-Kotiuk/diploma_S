<script lang="ts">
  export let value = 0;
  let toneClass = 'text-emerald-700';
  $: toneClass = value >= 75 ? 'text-red-700' : value >= 40 ? 'text-amber-700' : 'text-emerald-700';
</script>

<span class={`text-sm font-medium ${toneClass}`}>Ризик {Math.round(value)}</span>
