import { api, post } from './client';
import type { Report } from '$lib/types';

export const reportsApi = {
  list: () => api<Report[]>('/reports'),
  environment: (id: number) => post<Report>(`/reports/environment/${id}`),
  node: (id: number) => post<Report>(`/reports/node/${id}`)
};
