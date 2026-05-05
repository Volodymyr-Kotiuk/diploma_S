import { api, post } from './client';
import type { CapacityForecast } from '$lib/types';

export const capacityApi = {
  get: (nodeId: number) => api<CapacityForecast[]>(`/capacity/${nodeId}`),
  run: (nodeId: number) => post<CapacityForecast[]>(`/capacity/run/${nodeId}`)
};
