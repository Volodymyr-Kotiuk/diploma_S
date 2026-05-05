import { api, post, put, del } from './client';
import type { CapacityForecast, Diagnostic, Node, Recommendation, ResourceMetric } from '$lib/types';

export const nodesApi = {
  list: (query = '') => api<Node[]>(`/nodes${query}`),
  get: (id: number) => api<Node>(`/nodes/${id}`),
  create: (payload: Partial<Node>) => post<Node>('/nodes', payload),
  update: (id: number, payload: Partial<Node>) => put<Node>(`/nodes/${id}`, payload),
  remove: (id: number) => del<{ status: string }>(`/nodes/${id}`),
  metrics: (id: number, limit = 120) => api<ResourceMetric[]>(`/nodes/${id}/metrics?limit=${limit}`),
  diagnostics: (id: number) => api<Diagnostic[]>(`/nodes/${id}/diagnostics`),
  recommendations: (id: number) => api<Recommendation[]>(`/nodes/${id}/recommendations`),
  capacity: (id: number) => api<CapacityForecast[]>(`/nodes/${id}/capacity`)
};
