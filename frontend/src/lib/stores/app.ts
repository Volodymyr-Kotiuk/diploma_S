import { writable } from 'svelte/store';

export interface ToastMessage {
  id: number;
  type: 'success' | 'error' | 'info';
  message: string;
}

export const toasts = writable<ToastMessage[]>([]);

export function pushToast(message: string, type: ToastMessage['type'] = 'info') {
  const id = Date.now() + Math.round(Math.random() * 1000);
  toasts.update((items) => [...items, { id, type, message }]);
  setTimeout(() => {
    toasts.update((items) => items.filter((item) => item.id !== id));
  }, 4200);
}
