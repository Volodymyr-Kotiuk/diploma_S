<script lang="ts">
  export let variant: 'primary' | 'secondary' | 'ghost' | 'danger' = 'primary';
  export let size: 'sm' | 'md' = 'md';
  export let disabled = false;
  export let className = '';

  const variants = {
    primary: 'bg-brand-700 text-white border-brand-700',
    secondary: 'bg-white text-slate-900 border-line',
    ghost: 'bg-transparent text-slate-800 border-line',
    danger: 'bg-red-700 text-white border-red-700'
  };
  const sizes = {
    sm: 'h-8 px-3 text-sm',
    md: 'h-9 px-4 text-sm'
  };
</script>

<button
  class={`inline-flex items-center justify-center gap-2 rounded border font-medium disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${sizes[size]} ${className}`}
  {disabled}
  on:click
  {...$$restProps}
>
  <slot />
</button>
