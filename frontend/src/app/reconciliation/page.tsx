'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Period } from '@/lib/types';
import { FileText, Download, ArrowRight, Settings, Play, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { usePeriod } from '@/lib/period-context';

export default function ReconciliationPage() {
  const queryClient = useQueryClient();
  const { selectedPeriod, periods, setSelectedPeriod, isLoading: periodsLoading } = usePeriod();
  const periodId = selectedPeriod?.id;
  const [ruleVersion, setRuleVersion] = useState('recon-rule-v1');
  const [running, setRunning] = useState(false);

  const { data: summary, isLoading: summaryLoading, refetch: refetchSummary } = useQuery({
    queryKey: ['reconciliationSummary', periodId],
    queryFn: () => api.reconciliations.getSummary(periodId!),
    enabled: !!periodId,
  });

  const { data: exceptionsData, isLoading: exceptionsLoading } = useQuery({
    queryKey: ['exceptions', periodId],
    queryFn: () => api.reconciliations.listExceptions(periodId!),
    enabled: !!periodId,
  });

  const runMutation = useMutation({
    mutationFn: (payload: { client_id: string; period_id: string; rule_version: string }) =>
      api.reconciliations.run(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliationSummary', periodId] });
      queryClient.invalidateQueries({ queryKey: ['exceptions', periodId] });
      setRunning(false);
    },
    onError: (error) => {
      setRunning(false);
      alert(`Failed to run reconciliation: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const exportMutation = useMutation({
    mutationFn: (format: 'csv' | 'xlsx') => api.reconciliations.export(periodId!, format),
    onSuccess: (blob, format) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `reconciliation-report-${periodId}-${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
    onError: () => alert('Failed to export report'),
  });

  const exceptions = Array.isArray(exceptionsData) ? exceptionsData : (exceptionsData as any)?.items || [];

  if (periodsLoading) {
    return <div className="p-8 flex items-center justify-center">Loading periods...</div>;
  }

  if (!periodId) {
    return (
      <div className="p-8 space-y-8">
        <h1 className="text-2xl font-semibold text-slate-900">Reconciliation</h1>
        <div className="bg-white shadow sm:rounded-lg p-8 text-center">
          <Settings className="w-12 h-12 mx-auto text-slate-300 mb-4" />
          <h3 className="text-lg font-medium text-slate-900 mb-2">Select a Compliance Period</h3>
          <p className="text-sm text-slate-500 mb-6 max-w-md mx-auto">
            Choose a period from the dropdown below to run or review reconciliations.
          </p>
          <select
            value={selectedPeriod?.id || ''}
            onChange={(e) => {
              const period = periods.find(p => p.id === e.target.value);
              setSelectedPeriod(period || null);
            }}
            className="inline-flex items-center px-4 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
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

  // Render exceptions table
  function renderExceptionsTable() {
    if (exceptionsLoading) {
      return <div className="p-8 text-center text-slate-500">Loading exceptions...</div>;
    }

    if (exceptions.length === 0) {
      return (
        <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
          <table className="min-w-full divide-y divide-slate-300">
            <thead className="bg-slate-50">
              <tr>
                <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-slate-900">ID</th>
                <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Type</th>
                <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Severity</th>
                <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Status</th>
                <th className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              <tr>
                <td colSpan={5} className="py-12 text-center text-sm text-slate-500">
                  No exceptions found for this period.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      );
    }

    return (
      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
        <table className="min-w-full divide-y divide-slate-300">
          <thead className="bg-slate-50">
            <tr>
              <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-slate-900">ID</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Type</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Severity</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Status</th>
              <th className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {exceptions.map((exception: any) => (
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
                  <a
                    href={`/exceptions/${exception.id}`}
                    className="text-indigo-600 hover:text-indigo-900 inline-flex items-center gap-1"
                  >
                    Review
                    <ArrowRight className="w-4 h-4" />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (periodsLoading) {
    return <div className="p-8 flex items-center justify-center">Loading periods...</div>;
  }

  if (!periodId) {
    return (
      <div className="p-8 space-y-8">
        <h1 className="text-2xl font-semibold text-slate-900">Reconciliation</h1>
        <div className="bg-white shadow sm:rounded-lg p-8 text-center">
          <Settings className="w-12 h-12 mx-auto text-slate-300 mb-4" />
          <h3 className="text-lg font-medium text-slate-900 mb-2">Select a Compliance Period</h3>
          <p className="text-sm text-slate-500 mb-6 max-w-md mx-auto">
            Choose a period from the dropdown below to run or review reconciliations.
          </p>
          <select
            value={selectedPeriod?.id || ''}
            onChange={(e) => {
              const period = periods.find(p => p.id === e.target.value);
              setSelectedPeriod(period || null);
            }}
            className="inline-flex items-center px-4 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
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

  return (
    <div className="p-8 space-y-8">
      <div className="sm:flex sm:items-center sm:justify-between mb-8">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-slate-900">Reconciliation</h1>
          <p className="mt-2 text-sm text-slate-700">
            Run and review GST purchase register vs GSTR-2B reconciliations.
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
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
        </div>
      </div>

      {/* Run Reconciliation Card */}
      <div className="bg-white shadow sm:rounded-lg p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Run Reconciliation</h2>
            <p className="mt-1 text-sm text-slate-500">
              Compare Purchase Register against GSTR-2B for the selected period.
            </p>
          </div>
          <div className="flex items-center gap-4">
            <select
              value={ruleVersion}
              onChange={(e) => setRuleVersion(e.target.value)}
              className="px-3 py-1.5 text-sm rounded-lg border border-slate-300 bg-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
            >
              <option value="recon-rule-v1">Standard Rules (v1)</option>
            </select>
            <button
              onClick={() => runMutation.mutate({
                client_id: selectedPeriod?.client_id || '',
                period_id: periodId!,
                rule_version: ruleVersion,
              })}
              disabled={running || !periodId}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {running ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Running…
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Reconciliation
                </>
              )}
            </button>
          </div>
        </div>

        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-1">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-green-800">Matched</span>
              </div>
              <p className="text-3xl font-bold text-green-900">{summary.matched}</p>
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-1">
                <AlertCircle className="w-5 h-5 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-800">Partial Match</span>
              </div>
              <p className="text-3xl font-bold text-yellow-900">{summary.partial_match}</p>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-1">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <span className="text-sm font-medium text-red-800">Missing in 2B</span>
              </div>
              <p className="text-3xl font-bold text-red-900">{summary.missing_in_2b}</p>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-1">
                <FileText className="w-5 h-5 text-slate-600" />
                <span className="text-sm font-medium text-slate-800">Other</span>
              </div>
              <p className="text-3xl font-bold text-slate-900">
                {summary.missing_in_books + summary.duplicates + summary.review_required}
              </p>
            </div>
          </div>
        )}

        <div className="border-t border-slate-200 pt-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Exceptions</h3>
          {renderExceptionsTable()}

          <div className="mt-4 flex items-center justify-between">
            <button
              onClick={() => exportMutation.mutate('csv')}
              disabled={exportMutation.isPending}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
            <button
              onClick={() => exportMutation.mutate('xlsx')}
              disabled={exportMutation.isPending}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50"
            >
              <Download className="w-4 h-4" />
              Export XLSX
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}