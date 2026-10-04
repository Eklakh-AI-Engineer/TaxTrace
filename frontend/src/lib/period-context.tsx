'use client';

import { createContext, useContext, useState, useEffect, useMemo, useRef, ReactNode } from 'react';
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

  const periodList: Period[] = Array.isArray(periods) ? periods : ((periods as unknown as { items?: Period[] })?.items) || [];

  // Clear selected period if it's no longer in the list
  const selectedPeriod = useMemo(() => {
    if (!selectedPeriodId) return null;
    return periodList.find((p: Period) => p.id === selectedPeriodId) || null;
  }, [periodList, selectedPeriodId]);

  // Clear invalid selection when periods change
  const clearedRef = useRef<Set<string>>(new Set());
  
  useEffect(() => {
    const listKey = periodList.map(p => p.id).join(',');
    if (selectedPeriodId && !periodList.find((p: Period) => p.id === selectedPeriodId)) {
      if (!clearedRef.current.has(listKey)) {
        clearedRef.current.add(listKey);
        localStorage.removeItem('selectedPeriodId');
        setSelectedPeriodId(null);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [periodList]);

  const setSelectedPeriod = (period: Period | null) => {
    if (period) {
      setSelectedPeriodId(period.id);
      localStorage.setItem('selectedPeriodId', period.id);
    } else {
      setSelectedPeriodId(null);
      localStorage.removeItem('selectedPeriodId');
    }
  };

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