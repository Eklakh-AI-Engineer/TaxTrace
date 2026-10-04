import { render, screen, waitFor } from '@testing-library/react';
import ExceptionsPage from '@/app/exceptions/page';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock the period context
vi.mock('@/lib/period-context', () => ({
  usePeriod: vi.fn(() => ({
    selectedPeriod: { id: 'test-period-1', financial_year: '2026-27', tax_period: 'M1', status: 'open' },
    periods: [{ id: 'test-period-1', financial_year: '2026-27', tax_period: 'M1', status: 'open' }],
    setSelectedPeriod: vi.fn(),
    isLoading: false,
  })),
}));

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: any) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

// Mock api
vi.mock('@/lib/api', () => ({
  api: {
    exceptions: {
      list: vi.fn(),
      get: vi.fn(),
      makeDecision: vi.fn(),
      export: vi.fn(),
    },
  },
}));

describe('ExceptionsPage', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('renders page title', () => {
    render(<ExceptionsPage />);
    
    expect(screen.getByText('Exceptions')).toBeInTheDocument();
  });

  it('renders period selector', () => {
    render(<ExceptionsPage />);
    
    expect(screen.getByDisplayValue('2026-27 - M1 (open)')).toBeInTheDocument();
  });

  it('renders export button', () => {
    render(<ExceptionsPage />);
    
    expect(screen.getByText('Export CSV')).toBeInTheDocument();
  });
});