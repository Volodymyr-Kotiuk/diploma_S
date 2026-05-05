export function percent(value?: number | null): string {
  return `${Math.round(value ?? 0)}%`;
}

export function mbToGb(value?: number | null): string {
  if (!value) return '0 GB';
  return `${(value / 1024).toFixed(value >= 10240 ? 0 : 1)} GB`;
}

export function bytesRate(value?: number | null): string {
  const bytes = value ?? 0;
  if (bytes > 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB/s`;
  if (bytes > 1024) return `${(bytes / 1024).toFixed(1)} KB/s`;
  return `${Math.round(bytes)} B/s`;
}

export function shortDate(value?: string | null): string {
  if (!value) return 'немає даних';
  return new Intl.DateTimeFormat('uk-UA', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(value));
}

export function uptime(seconds?: number | null): string {
  if (!seconds) return 'невідомо';
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  if (days) return `${days} д ${hours} год`;
  return `${hours} год`;
}
