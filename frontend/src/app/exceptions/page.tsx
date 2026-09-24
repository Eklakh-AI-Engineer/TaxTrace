'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import Link from 'next/link';

// Using a hardcoded period_id for MVP since we don't have a period selector yet.
// In a real app, this would come from a context or URL parameter.
const DEFAULT_PERIOD_ID = 'test-period-1';

export default function ExceptionsPage() {
  const { data: exceptions, isLoading } = useQuery({
    queryKey: ['exceptions', DEFAULT_PERIOD_ID],
    queryFn: () => api.exceptions.list(DEFAULT_PERIOD_ID),
  });

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
                  No exceptions found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
