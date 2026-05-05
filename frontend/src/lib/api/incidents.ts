import { api } from './client';
import type { Incident } from '$lib/types';

export const incidentsApi = {
  list: (query = '') => api<Incident[]>(`/incidents${query}`),
  get: (id: number) => api<Incident>(`/incidents/${id}`)
};
