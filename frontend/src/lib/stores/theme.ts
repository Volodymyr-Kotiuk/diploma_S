import { browser } from '$app/environment';
import { writable } from 'svelte/store';

export type Theme = 'light' | 'dark';

export const theme = writable<Theme>('light');

export function initTheme() {
  if (!browser) return;
  document.documentElement.classList.remove('dark');
  localStorage.setItem('theme', 'light');
  theme.set('light');
}
