'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { AlertTriangle, CheckSquare, Clock, FileWarning } from 'lucide-react';

export default function Dashboard() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['dashboardOverview'],
    queryFn: () => api.dashboard.getOverview(),
  });

  if (isLoading) {
    return <div className="p-8 text-slate-500">Loading dashboard...</div>;
  }

  if (isError) {
    return <div className="p-8 text-red-500">Failed to load dashboard metrics.</div>;
  }

  const stats = [
    { name: 'Open exceptions', value: data?.open_exceptions || 0, icon: AlertTriangle, color: 'text-amber-500' },
    { name: 'High priority', value: data?.high_priority_exceptions || 0, icon: AlertTriangle, color: 'text-red-500' },
    { name: 'Notice deadlines', value: data?.notice_deadlines_30d || 0, icon: FileWarning, color: 'text-orange-500' },
    { name: 'Overdue tasks', value: data?.overdue_tasks || 0, icon: Clock, color: 'text-rose-500' },
  ];

  return (
    <div className="p-8">
      <h1 className="text-2xl font-semibold text-slate-900 mb-6">Good morning</h1>
      
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6 border border-slate-100">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <stat.icon className={`h-6 w-6 ${stat.color}`} aria-hidden="true" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dt className="truncate text-sm font-medium text-slate-500">{stat.name}</dt>
                <dd className="text-3xl font-semibold tracking-tight text-slate-900">{stat.value}</dd>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
