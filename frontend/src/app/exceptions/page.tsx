'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { usePeriod } from '@/lib/period-context';
import Link from 'next/link';
import { Download, FileText } from 'lucide-react';

export default function ExceptionsPage() {
  const { selectedPeriod, periods, setSelectedPeriod, isLoading: periodsLoading } = usePeriod();
  const periodId = selectedPeriod?.id;

  const { data: exceptions, isLoading } = useQuery({
    queryKey: ['exceptions', periodId],
    queryFn: () => api.exceptions.list(periodId!),
    enabled: !!periodId,
  });

  const handleExport = async (format: 'csv' | 'xlsx' = 'csv') => {
    if (!periodId) return;
    try {
      const blob = await api.exceptions.export(periodId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `reconciliation-report-${periodId}-${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      alert('Failed to export report');
    }
  };

  if (periodsLoading) {
    return <div className="p-8">Loading periods...</div>;
  }

  if (!periodId) {
    return (
      <div className="p-8 space-y-8">
        <h1 className="text-2xl font-semibold text-slate-900">Exceptions</h1>
        <div className="bg-white shadow sm:rounded-lg p-8 text-center">
          <p className="text-sm text-slate-500 mb-4">Select a compliance period to view exceptions.</p>
          <select
            value={selectedPeriod?.id || ''}
            onChange={(e) => {
              const period = periods.find(p => p.id === e.target.value);
              setSelectedPeriod(period || null);
            }}
            className="inline-flex items-center px-4 py-2 text-sm rounded-lg border border-slate-300 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
          >
            <option value="">Select a period...</option>
            {periods.map((p) => (
              <option key={p.id} value={p.id}>
                {p.financial_year} - {p.tax_period} ({p.status})
              </option>
            ))}
          </select>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return <div className="p-8">Loading exceptions...</div>;
  }

  return (
    <div className="p-8">
      <div className="sm:flex sm:items-center mb-8">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-slate-900">Exceptions</h1>
          <p className="mt-2 text-sm text-slate-700">
            A list of all reconciliation exceptions requiring review.
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex items-center gap-3">
          <select
            value={periodId}
            onChange={(e) => {
              const period = periods.find(p => p.id === e.target.value);
              setSelectedPeriod(period || null);
            }}
            className="px-3 py-1.5 text-sm rounded-lg border border-slate-300 bg-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
          >
            {periods.map((p) => (
              <option key={p.id} value={p.id}>
                {p.financial_year} - {p.tax_period} ({p.status})
              </option>
            ))}
          </select>
          <button
            onClick={() => handleExport('csv')}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
        <table className="min-w-full divide-y divide-slate-300">
          <thead className="bg-slate-50">
            <tr>
              <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-slate-900">ID</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Type</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Severity</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Status</th>
              <th className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                <span className="sr-only">Review</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {exceptions?.map((exception) => (
              <tr key={exception.id}>
                <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-slate-900">
                  {exception.id.substring(0, 8)}...
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500">{exception.type}</td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500">
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    exception.severity === 'high' ? 'bg-red-100 text-red-800' :
                    exception.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {exception.severity}
                  </span>
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500">{exception.status}</td>
                <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                  <Link href={`/exceptions/${exception.id}`} className="text-indigo-600 hover:text-indigo-900">
                    Review<span className="sr-only">, {exception.id}</span>
                  </Link>
                </td>
              </tr>
            ))}
            {exceptions?.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-sm text-slate-500">
                  No exceptions found for this period.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
