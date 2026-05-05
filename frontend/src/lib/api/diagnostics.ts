import { api, post } from './client';
import type { Diagnostic } from '$lib/types';

export const diagnosticsApi = {
  list: () => api<Diagnostic[]>('/diagnostics'),
  run: (nodeId: number) => post<Diagnostic>(`/diagnostics/run/${nodeId}`),
  acknowledge: (id: number) => post<Diagnostic>(`/diagnostics/${id}/acknowledge`),
  resolve: (id: number) => post<Diagnostic>(`/diagnostics/${id}/resolve`)
};
