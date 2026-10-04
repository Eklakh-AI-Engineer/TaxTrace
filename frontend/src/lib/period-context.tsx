'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Period } from '@/lib/types';

interface PeriodContextType {
  selectedPeriod: Period | null;
  setSelectedPeriod: (period: Period | null) => void;
  periods: Period[];
  isLoading: boolean;
  refetch: () => void;
}

const PeriodContext = createContext<PeriodContextType | undefined>(undefined);

export function PeriodProvider({ children }: { children: ReactNode }) {
  const [selectedPeriodId, setSelectedPeriodId] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('selectedPeriodId');
    }
    return null;
  });

  const { data: periods, isLoading, refetch } = useQuery({
    queryKey: ['periods'],
    queryFn: () => api.periods.list(),
  });

  const periodList: Period[] = Array.isArray(periods) ? periods : (periods as any)?.items || [];

  const selectedPeriod = periodList.find((p: Period) => p.id === selectedPeriodId) || null;

  const setSelectedPeriod = (period: Period | null) => {
    if (period) {
      setSelectedPeriodId(period.id);
      localStorage.setItem('selectedPeriodId', period.id);
    } else {
      setSelectedPeriodId(null);
      localStorage.removeItem('selectedPeriodId');
    }
  };

  useEffect(() => {
    if (selectedPeriodId && !periodList.find((p: Period) => p.id === selectedPeriodId)) {
      setSelectedPeriodId(null);
      localStorage.removeItem('selectedPeriodId');
    }
  }, [periodList, selectedPeriodId]);

  return (
    <PeriodContext.Provider value={{
      selectedPeriod,
      setSelectedPeriod,
      periods: periodList,
      isLoading,
      refetch,
    }}>
      {children}
    </PeriodContext.Provider>
  );
}

export function usePeriod() {
  const context = useContext(PeriodContext);
  if (!context) {
    throw new Error('usePeriod must be used within a PeriodProvider');
  }
  return context;
}