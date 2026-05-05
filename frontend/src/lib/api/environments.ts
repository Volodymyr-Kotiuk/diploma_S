import { api, post, put, del } from './client';
import type { Environment } from '$lib/types';

export const environmentsApi = {
  list: () => api<Environment[]>('/environments'),
  get: (id: number) => api<Environment>(`/environments/${id}`),
  create: (payload: Partial<Environment>) => post<Environment>('/environments', payload),
  update: (id: number, payload: Partial<Environment>) => put<Environment>(`/environments/${id}`, payload),
  remove: (id: number) => del<{ status: string }>(`/environments/${id}`)
};
