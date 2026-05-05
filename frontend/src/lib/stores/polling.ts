import { writable } from 'svelte/store';

export const pollingEnabled = writable(true);
export const pollingIntervalMs = writable(5000);
