import { api } from './client';
import type { DashboardSummary, Incident } from '$lib/types';

export const dashboardApi = {
  summary: () => api<DashboardSummary>('/dashboard/summary'),
  recentIncidents: () => api<Incident[]>('/dashboard/recent-incidents'),
  riskOverview: () => api<Array<{ node_id: number; node: string; status: string; risk_score: number; root_cause: string }>>('/dashboard/risk-overview')
};
