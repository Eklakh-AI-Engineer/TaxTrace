import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  usePathname: () => '/',
  useParams: () => ({}),
  useSearchParams: () => new URLSearchParams(),
}));

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: any) => (
    React.createElement('a', { href, ...props }, children)
  ),
}));

// Mock lucide-react icons
vi.mock('lucide-react', () => {
  const icons = [
    'Home', 'FileText', 'AlertTriangle', 'FileWarning', 'CheckSquare',
    'Search', 'Shield', 'Settings', 'MessageCircle', 'ArrowLeft',
    'ArrowRight', 'Download', 'Upload', 'Calendar', 'Clock', 'User',
    'Bot', 'CheckCircle2', 'XCircle', 'X', 'Plus', 'Mail', 'MessageCircle',
    'ChevronDown', 'Send', 'Ban', 'TrendingUp', 'Gavel', 'Edit2',
    'FileWarning', 'AlertTriangle', 'CheckCircle2', 'XCircle',
  ];
  const mockComponents: Record<string, any> = {};
  for (const icon of icons) {
    mockComponents[icon] = (props: any) => React.createElement('svg', { ...props, 'data-testid': icon.toLowerCase() });
  }
  return mockComponents;
});

// Mock tanstack/react-query
vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(({ queryKey, queryFn, enabled }: any) => {
    // Handle exceptions query
    if (queryKey?.[0] === 'exceptions' && enabled) {
      return {
        data: [
          {
            id: 'exc-1',
            type: 'VALUE_MISMATCH',
            severity: 'high',
            status: 'open',
            reason_code: 'SIGNIFICANT_VALUE_DISCREPANCY',
            explanation: 'Test explanation',
            created_by_system: true,
          },
          {
            id: 'exc-2',
            type: 'MISSING_IN_2B',
            severity: 'high',
            status: 'open',
            reason_code: 'NOT_FOUND_IN_GSTR2B',
            explanation: 'Missing in GSTR-2B',
            created_by_system: true,
          },
        ],
        isLoading: false,
        isError: false,
      };
    }
    // Handle periods query
    if (queryKey?.[0] === 'periods') {
      return {
        data: [{ id: 'test-period-1', financial_year: '2026-27', tax_period: 'M1', status: 'open' }],
        isLoading: false,
        isError: false,
      };
    }
    // Handle dashboard query
    if (queryKey?.[0] === 'dashboardOverview') {
      return {
        data: {
          firm_id: 'test_firm',
          generated_at: new Date().toISOString(),
          tasks: { total_open: 0, in_progress: 0, blocked: 0, completed: 0, overdue: 0 },
          exceptions: { total_unresolved: 0, open: 0, in_review: 0 },
          notices: { total_active: 0, urgent_deadlines_within_7_days: 0 },
          operations: { estimated_hours_saved: 0, manual_overrides: 0, ai_drafts_generated: 0 },
          overdue_task_items: [],
        },
        isLoading: false,
        isError: false,
      };
    }
    // Handle tasks query
    if (queryKey?.[0] === 'tasks') {
      return {
        data: [],
        isLoading: false,
        isError: false,
      };
    }
    return { data: undefined, isLoading: true, isError: false };
  }),
  useMutation: vi.fn(),
  useQueryClient: vi.fn(),
  QueryClient: vi.fn().mockImplementation(() => ({
    invalidateQueries: vi.fn(),
    setQueryData: vi.fn(),
    getQueryData: vi.fn(),
  })),
  QueryClientProvider: ({ children }: any) => children,
}));

// Mock api
vi.mock('@/lib/api', () => ({
  api: {
    dashboard: {
      getOverview: vi.fn(),
    },
    periods: {
      list: vi.fn(),
    },
    exceptions: {
      list: vi.fn(),
      get: vi.fn(),
      makeDecision: vi.fn(),
      export: vi.fn(),
    },
    tasks: {
      list: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      draftMessage: vi.fn(),
    },
    notices: {
      list: vi.fn(),
      get: vi.fn(),
      extract: vi.fn(),
      generateDraft: vi.fn(),
      approveDraft: vi.fn(),
    },
    chat: {
      send: vi.fn(),
    },
  },
}));

// Mock period context
vi.mock('@/lib/period-context', () => ({
  usePeriod: vi.fn(() => ({
    selectedPeriod: { id: 'test-period-1', financial_year: '2026-27', tax_period: 'M1', status: 'open' },
    periods: [{ id: 'test-period-1', financial_year: '2026-27', tax_period: 'M1', status: 'open' }],
    setSelectedPeriod: vi.fn(),
    isLoading: false,
  })),
  PeriodProvider: ({ children }: any) => children,
}));

// Mock utils
vi.mock('@/lib/utils', () => ({
  cn: (...args: any[]) => args.filter(Boolean).join(' '),
}));

// Global test utilities
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Need React for createElement in mocks
import React from 'react';
global.React = React;

// Suppress console errors in tests (optional)
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (args[0]?.includes?.('Warning: ReactDOM.render is no longer supported')) return;
    if (args[0]?.includes?.('act(...)')) return;
    originalError.call(console, ...args);
  };
});
afterAll(() => {
  console.error = originalError;
});