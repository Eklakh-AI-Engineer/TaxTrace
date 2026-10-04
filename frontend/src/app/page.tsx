'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { usePeriod } from '@/lib/period-context';
import { AlertTriangle, CheckSquare, Clock, FileWarning, ListTodo, Ban, TrendingUp, Calendar } from 'lucide-react';
import Link from 'next/link';

export default function Dashboard() {
  const { selectedPeriod, periods, setSelectedPeriod, isLoading: periodsLoading } = usePeriod();
  const periodId = selectedPeriod?.id;

  const { data, isLoading, isError } = useQuery({
    queryKey: ['dashboardOverview', periodId],
    queryFn: () => api.dashboard.getOverview(),
    enabled: !!periodId,
  });

  if (periodsLoading) {
    return (
      <div className="p-8 flex items-center gap-3 text-slate-500">
        <div className="w-5 h-5 border-2 border-slate-300 border-t-indigo-500 rounded-full animate-spin" />
        Loading periods…
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-8 flex items-center gap-3 text-slate-500">
        <div className="w-5 h-5 border-2 border-slate-300 border-t-indigo-500 rounded-full animate-spin" />
        Loading dashboard…
      </div>
    );
  }

  if (isError) {
    return <div className="p-8 text-red-500">Failed to load dashboard metrics.</div>;
  }

  if (!periodId) {
    return (
      <div className="p-8 space-y-8">
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <div className="bg-white shadow sm:rounded-lg p-8 text-center">
          <Calendar className="w-12 h-12 mx-auto text-slate-300 mb-4" />
          <h3 className="text-lg font-medium text-slate-900 mb-2">Select a Compliance Period</h3>
          <p className="text-sm text-slate-500 mb-6 max-w-md mx-auto">
            Choose a period from the dropdown below to view dashboard metrics, exceptions, and tasks for that period.
          </p>
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

  const stats = [
    { name: 'Open Exceptions', value: data?.exceptions?.open || 0, icon: AlertTriangle, color: 'text-amber-500', bg: 'bg-amber-50' },
    { name: 'Unresolved', value: data?.exceptions?.total_unresolved || 0, icon: AlertTriangle, color: 'text-red-500', bg: 'bg-red-50' },
    { name: 'Active Notices', value: data?.notices?.total_active || 0, icon: FileWarning, color: 'text-orange-500', bg: 'bg-orange-50' },
    { name: 'Urgent Deadlines (7d)', value: data?.notices?.urgent_deadlines_within_7_days || 0, icon: Clock, color: 'text-rose-500', bg: 'bg-rose-50' },
  ];

  const taskStats = [
    { name: 'Open', value: data?.tasks?.total_open || 0, color: 'text-slate-700' },
    { name: 'In Progress', value: data?.tasks?.in_progress || 0, color: 'text-blue-600' },
    { name: 'Blocked', value: data?.tasks?.blocked || 0, color: 'text-red-600' },
    { name: 'Completed', value: data?.tasks?.completed || 0, color: 'text-green-600' },
    { name: 'Overdue', value: data?.tasks?.overdue || 0, color: 'text-rose-600' },
  ];

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-slate-400" />
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

      {/* Top-level metrics */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className={`overflow-hidden rounded-xl ${stat.bg} px-5 py-5 border border-slate-100 shadow-sm`}>
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <stat.icon className={`h-6 w-6 ${stat.color}`} aria-hidden="true" />
              </div>
              <div className="ml-4 w-0 flex-1">
                <dt className="truncate text-sm font-medium text-slate-600">{stat.name}</dt>
                <dd className="text-3xl font-bold tracking-tight text-slate-900">{stat.value}</dd>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Task Summary */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <ListTodo className="w-5 h-5 text-indigo-500" /> Task Summary
          </h2>
          <Link href="/tasks" className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">
            View Board →
          </Link>
        </div>
        <div className="grid grid-cols-5 divide-x divide-slate-100">
          {taskStats.map((ts) => (
            <div key={ts.name} className="px-4 py-4 text-center">
              <p className="text-2xl font-bold text-slate-900">{ts.value}</p>
              <p className={`text-xs font-medium mt-1 ${ts.color}`}>{ts.name}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Overdue Tasks */}
      {data?.overdue_task_items && data.overdue_task_items.length > 0 && (
        <div className="rounded-xl border border-red-200 bg-red-50/50 shadow-sm">
          <div className="px-6 py-4 border-b border-red-100">
            <h2 className="text-base font-semibold text-red-800 flex items-center gap-2">
              <Ban className="w-5 h-5" /> Overdue Tasks ({data.overdue_task_items.length})
            </h2>
          </div>
          <ul className="divide-y divide-red-100">
            {data.overdue_task_items.map((t) => (
              <li key={t.id} className="px-6 py-3 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-900">{t.title}</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Due: {t.due_date ? new Date(t.due_date).toLocaleDateString() : '—'}
                    {t.owner_id && <> · Assigned: {t.owner_id}</>}
                  </p>
                </div>
                <span className="text-xs font-medium px-2 py-1 rounded bg-red-100 text-red-700">{t.status}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Operational Impact (Stage 9) */}
      <div className="rounded-xl border border-emerald-200 bg-emerald-50/30 shadow-sm">
        <div className="flex items-center px-6 py-4 border-b border-emerald-100">
          <h2 className="text-base font-semibold text-emerald-900 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-600" /> Operational Impact
          </h2>
        </div>
        <div className="grid grid-cols-3 divide-x divide-emerald-100">
          <div className="px-4 py-5 text-center">
            <p className="text-3xl font-bold text-emerald-700">{data?.operations?.estimated_hours_saved || 0}</p>
            <p className="text-xs font-medium mt-1 text-emerald-600 uppercase tracking-wider">Est. Hours Saved</p>
          </div>
          <div className="px-4 py-5 text-center">
            <p className="text-3xl font-bold text-emerald-700">{data?.operations?.ai_drafts_generated || 0}</p>
            <p className="text-xs font-medium mt-1 text-emerald-600 uppercase tracking-wider">AI Drafts Generated</p>
          </div>
          <div className="px-4 py-5 text-center">
            <p className="text-3xl font-bold text-emerald-700">{data?.operations?.manual_overrides || 0}</p>
            <p className="text-xs font-medium mt-1 text-emerald-600 uppercase tracking-wider">Manual Overrides</p>
          </div>
        </div>
      </div>
    </div>
  );
}
