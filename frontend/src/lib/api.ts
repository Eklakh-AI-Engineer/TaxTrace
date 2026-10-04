import {
  DashboardMetrics,
  Exception,
  ExceptionDetail,
  Task,
  NoticeCase,
  NoticeDetail,
  ExtractionResponse,
  Draft,
  DraftCreateRequest,
  DraftApproveRequest,
  DraftMessageResponse,
  Period,
} from './types';

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

async function fetchBlob(endpoint: string, options: RequestInit = {}): Promise<Blob> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${DEV_TOKEN}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.blob();
}

export const api = {
  dashboard: {
    getOverview: () => fetchAPI<DashboardMetrics>('/dashboard/overview'),
  },
  periods: {
    list: () => fetchAPI<Period[]>('/periods'),
  },
  exceptions: {
    list: (periodId: string) => fetchAPI<Exception[]>(`/reconciliations/${periodId}/exceptions`),
    get: (id: string) => fetchAPI<ExceptionDetail>(`/exceptions/${id}`),
    makeDecision: (id: string, action: string, reason?: string) => 
      fetchAPI<ExceptionDetail>(`/exceptions/${id}/decision`, {
        method: 'POST',
        body: JSON.stringify({ action, reason }),
      }),
    explain: (id: string, mode: string = 'standard') => fetchAPI<any>(`/exceptions/${id}/explanation`, {
      method: 'POST',
      body: JSON.stringify({ mode }),
    }),
    export: (periodId: string, format: 'csv' | 'xlsx' = 'csv') => 
      fetchBlob(`/reconciliations/${periodId}/export?format=${format}`),
  },
  tasks: {
    list: () => fetchAPI<Task[]>('/tasks'),
    create: (data: Partial<Task>) => fetchAPI<Task>('/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    update: (id: string, data: Partial<Task>) => fetchAPI<Task>(`/tasks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
    draftMessage: (id: string, channel: string, recipient_type: string) => fetchAPI<DraftMessageResponse>(`/tasks/${id}/draft-message`, {
      method: 'POST',
      body: JSON.stringify({ channel, recipient_type }),
    }),
  },
  notices: {
    list: () => fetchAPI<NoticeCase[]>('/notices'),
    get: (id: string) => fetchAPI<NoticeDetail>(`/notices/${id}`),
    extract: (id: string) => fetchAPI<ExtractionResponse>(`/notices/${id}/extract`, { method: 'POST' }),
    generateDraft: (id: string, payload: DraftCreateRequest) => fetchAPI<Draft>(`/notices/${id}/draft`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
    approveDraft: (draftId: string, payload: DraftApproveRequest) => fetchAPI<Draft>(`/drafts/${draftId}/approve`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  },
  chat: {
    send: (message: string) => fetchAPI<{reply: string, needs_confirmation: boolean}>('/chat/send', {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),
  }
};
