import { api, post } from './client';
import type { Recommendation } from '$lib/types';

export const recommendationsApi = {
  list: () => api<Recommendation[]>('/recommendations'),
  accept: (id: number) => post<Recommendation>(`/recommendations/${id}/accept`),
  ignore: (id: number) => post<Recommendation>(`/recommendations/${id}/ignore`),
  resolve: (id: number) => post<Recommendation>(`/recommendations/${id}/resolve`)
};
