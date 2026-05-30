<script lang="ts">
  export let tone: 'slate' | 'green' | 'amber' | 'red' | 'blue' = 'slate';
  export let className = '';
  const tones = {
    slate: 'text-[#1f2937]',
    green: 'text-[#1f2937]',
    amber: 'text-[#1f2937]',
    red: 'text-[#1f2937]',
    blue: 'text-[#1f2937]'
  };
</script>

<span class={`inline-flex items-center text-sm font-medium ${tones[tone]} ${className}`}>
  <slot />
</span>
