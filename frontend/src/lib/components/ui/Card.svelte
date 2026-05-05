<script lang="ts">
  export let className = '';
  export let padded = true;
</script>

<section
  class={`ops-panel rounded ${padded ? 'p-4' : ''} ${className}`}
>
  <slot />
</section>
