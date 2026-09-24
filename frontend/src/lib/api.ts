import { DashboardMetrics, Exception, Task, NoticeCase } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const DEV_TOKEN = process.env.NEXT_PUBLIC_DEV_TOKEN;

async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${DEV_TOKEN}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

export const api = {
  dashboard: {
    getOverview: () => fetchAPI<DashboardMetrics>('/dashboard/overview'),
  },
  exceptions: {
    list: (periodId: string) => fetchAPI<Exception[]>(`/reconciliations/${periodId}/exceptions`),
    get: (id: string) => fetchAPI<Exception>(`/exceptions/${id}`),
    makeDecision: (id: string, action: string, reason?: string) => 
      fetchAPI<Exception>(`/exceptions/${id}/decision`, {
        method: 'POST',
        body: JSON.stringify({ action, reason }),
      }),
  },
  tasks: {
    list: () => fetchAPI<Task[]>('/tasks'),
  },
  notices: {
    list: () => fetchAPI<NoticeCase[]>('/notices'),
  }
};
