import { API_BASE, api, post } from './client';
import type { Report } from '$lib/types';

function filenameFromDisposition(disposition: string | null, fallback: string) {
  const match = disposition?.match(/filename="?([^"]+)"?/i);
  return match?.[1] || fallback;
}

async function downloadReport(report: Report) {
  const response = await fetch(`${API_BASE}/reports/${report.id}/download`);
  if (!response.ok) {
    throw new Error('Не вдалося завантажити PDF-звіт');
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filenameFromDisposition(response.headers.get('content-disposition'), `report_${report.id}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export const reportsApi = {
  list: () => api<Report[]>('/reports'),
  environment: (id: number) => post<Report>(`/reports/environment/${id}`),
  node: (id: number) => post<Report>(`/reports/node/${id}`),
  download: downloadReport
};
