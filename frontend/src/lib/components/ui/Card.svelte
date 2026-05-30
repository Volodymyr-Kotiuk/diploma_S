<script lang="ts">
  export let className = '';
  export let padded = true;
</script>

<section
  class={`ops-panel rounded-lg ${padded ? 'p-5' : ''} ${className}`}
>
  <slot />
</section>
