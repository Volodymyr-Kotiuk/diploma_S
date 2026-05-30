<script lang="ts">
  export let variant: 'primary' | 'secondary' | 'ghost' | 'danger' = 'primary';
  export let size: 'sm' | 'md' = 'md';
  export let disabled = false;
  export let className = '';

  const variants = {
    primary: 'bg-[#2F4FDC] text-white border-[#2F4FDC]',
    secondary: 'bg-white text-[#1f2937] border-[#cbd5e1]',
    ghost: 'bg-white text-[#1f2937] border-[#cbd5e1]',
    danger: 'bg-[#DC2626] text-white border-[#DC2626]'
  };
  const sizes = {
    sm: 'h-[34px] px-3 text-sm',
    md: 'h-10 px-4 text-sm'
  };
</script>

<button
  class={`inline-flex items-center justify-center gap-1.5 rounded-md border font-semibold leading-none disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${sizes[size]} ${className}`}
  {disabled}
  on:click
  {...$$restProps}
>
  <slot />
</button>
