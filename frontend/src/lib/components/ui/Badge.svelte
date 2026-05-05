<script lang="ts">
  export let tone: 'slate' | 'green' | 'amber' | 'red' | 'blue' = 'slate';
  export let className = '';
  const tones = {
    slate: 'bg-slate-100 text-slate-700 border-slate-300',
    green: 'bg-emerald-50 text-emerald-800 border-emerald-300',
    amber: 'bg-amber-50 text-amber-800 border-amber-300',
    red: 'bg-red-50 text-red-800 border-red-300',
    blue: 'bg-blue-50 text-blue-800 border-blue-300'
  };
</script>

<span class={`inline-flex items-center rounded border px-2 py-0.5 text-[11px] font-semibold ${tones[tone]} ${className}`}>
  <slot />
</span>
