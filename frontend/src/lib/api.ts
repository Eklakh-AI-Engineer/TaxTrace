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
  AIExplanationResponse,
  Client,
  ClientCreate,
  ClientUpdate,
  KnowledgeSearchRequest,
  KnowledgeSearchResponse,
  KnowledgeSource,
  KnowledgeSourceCreate,
  Settings,
  SettingsUpdate,
  ReconciliationRunRequest,
  ReconciliationRunResponse,
  ReconciliationSummary,
  ExceptionRead,
  PaginatedResponse,
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
  clients: {
    list: (params?: { status?: string; search?: string; page?: number; page_size?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.status) searchParams.set('status', params.status);
      if (params?.search) searchParams.set('search', params.search);
      if (params?.page) searchParams.set('page', params.page.toString());
      if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
      return fetchAPI<{ items: Client[]; total: number; page: number; page_size: number; has_next: boolean }>(
        `/clients?${searchParams.toString()}`
      );
    },
    create: (data: ClientCreate) => fetchAPI<Client>('/clients', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    get: (id: string) => fetchAPI<Client>(`/clients/${id}`),
    update: (id: string, data: ClientUpdate) => fetchAPI<Client>(`/clients/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  },
  reconciliations: {
    run: (payload: ReconciliationRunRequest) => fetchAPI<ReconciliationRunResponse>('/reconciliations', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
    getSummary: (periodId: string) => fetchAPI<ReconciliationSummary>(`/reconciliations/${periodId}`),
    listExceptions: (periodId: string, params?: { type?: string; severity?: string; status?: string; page?: number; page_size?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.type) searchParams.set('type', params.type);
      if (params?.severity) searchParams.set('severity', params.severity);
      if (params?.status) searchParams.set('status', params.status);
      if (params?.page) searchParams.set('page', params.page.toString());
      if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
      return fetchAPI<PaginatedResponse<ExceptionRead>>(
        `/reconciliations/${periodId}/exceptions?${searchParams.toString()}`
      );
    },
    export: (periodId: string, format: 'csv' | 'xlsx' = 'csv') => 
      fetchBlob(`/reconciliations/${periodId}/export?format=${format}`),
  },
  exceptions: {
    list: (periodId: string, params?: { type?: string; severity?: string; status?: string; page?: number; page_size?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.type) searchParams.set('type', params.type);
      if (params?.severity) searchParams.set('severity', params.severity);
      if (params?.status) searchParams.set('status', params.status);
      if (params?.page) searchParams.set('page', params.page.toString());
      if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
      return fetchAPI<{ items: any[]; total: number; page: number; page_size: number; has_next: boolean }>(
        `/reconciliations/${periodId}/exceptions?${searchParams.toString()}`
      );
    },
    get: (id: string) => fetchAPI<any>(`/exceptions/${id}`),
    makeDecision: (id: string, action: string, reason?: string) => 
      fetchAPI<any>(`/exceptions/${id}/decision`, {
        method: 'POST',
        body: JSON.stringify({ action, reason }),
      }),
    explain: (id: string, mode: string = 'standard') => fetchAPI<AIExplanationResponse>(`/exceptions/${id}/explanation`, {
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
    list: () => fetchAPI<any[]>('/notices'),
    get: (id: string) => fetchAPI<any>(`/notices/${id}`),
    extract: (id: string) => fetchAPI<any>(`/notices/${id}/extract`, { method: 'POST' }),
    generateDraft: (id: string, payload: any) => fetchAPI<any>(`/notices/${id}/draft`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
    approveDraft: (draftId: string, payload: any) => fetchAPI<any>(`/drafts/${draftId}/approve`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  },
  knowledge: {
    search: (payload: { query: string; limit?: number }) => fetchAPI<{ results: any[] }>('/knowledge/search', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
    listSources: (params?: { page?: number; page_size?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.page) searchParams.set('page', params.page.toString());
      if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
      return fetchAPI<{ items: any[]; total: number; page: number; page_size: number; has_next: boolean }>(
        `/knowledge/sources?${searchParams.toString()}`
      );
    },
    createSource: (payload: any) => fetchAPI<any>('/knowledge/sources', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
    getSource: (id: string) => fetchAPI<any>(`/knowledge/sources/${id}`),
  },
  settings: {
    get: () => fetchAPI<any>('/settings'),
    update: (payload: any) => fetchAPI<any>('/settings', {
      method: 'PATCH',
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
