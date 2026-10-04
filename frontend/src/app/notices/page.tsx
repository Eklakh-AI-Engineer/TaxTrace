'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { api } from '@/lib/api';
import { NoticeCase } from '@/lib/types';
import { FileWarning, Clock, AlertTriangle, ArrowRight } from 'lucide-react';

export default function NoticesPage() {
  const { data: notices, isLoading, isError } = useQuery({
    queryKey: ['notices'],
    queryFn: () => api.notices.list(),
  });

  if (isLoading) {
    return (
      <div className="p-8 flex items-center gap-3 text-slate-500">
        <div className="w-5 h-5 border-2 border-slate-300 border-t-indigo-500 rounded-full animate-spin" />
        Loading notices…
      </div>
    );
  }

  if (isError) {
    return <div className="p-8 text-red-500">Failed to load notices.</div>;
  }

  const noticeList = Array.isArray(notices) ? notices : ((notices as unknown as { items?: NoticeCase[] })?.items) || [];

  return (
    <div className="p-8 space-y-8">
      <div className="sm:flex sm:items-center mb-8">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-slate-900">Notices</h1>
          <p className="mt-2 text-sm text-slate-700">
            Manage compliance notices and track response deadlines.
          </p>
        </div>
      </div>

      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
        <table className="min-w-full divide-y divide-slate-300">
          <thead className="bg-slate-50">
            <tr>
              <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-slate-900">Notice Type</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Reference</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Status</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Response Deadline</th>
              <th className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {noticeList.map((notice) => (
              <tr key={notice.id}>
                <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-slate-900">
                  <span className="inline-flex items-center gap-1.5">
                    <FileWarning className="w-4 h-4 text-orange-500" />
                    {notice.notice_type}
                  </span>
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500 font-mono">
                  {notice.reference_number || '—'}
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500">
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    notice.status === 'received' ? 'bg-blue-100 text-blue-800' :
                    notice.status === 'facts_extracted' ? 'bg-yellow-100 text-yellow-800' :
                    notice.status === 'draft_generated' ? 'bg-purple-100 text-purple-800' :
                    notice.status === 'approved' ? 'bg-green-100 text-green-800' :
                    'bg-slate-100 text-slate-800'
                  }`}>
                    {notice.status.replace('_', ' ').toUpperCase()}
                  </span>
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500">
                  {notice.response_deadline ? (
                    <span className={`flex items-center gap-1 ${
                      new Date(notice.response_deadline) < new Date() ? 'text-red-600 font-semibold' : ''
                    }`}>
                      <Clock className="w-3.5 h-3.5" />
                      {new Date(notice.response_deadline).toLocaleDateString()}
                      {new Date(notice.response_deadline) < new Date() && (
                        <AlertTriangle className="w-3.5 h-3.5" />
                      )}
                    </span>
                  ) : (
                    <span className="text-slate-400">No deadline</span>
                  )}
                </td>
                <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                  <Link
                    href={`/notices/${notice.id}`}
                    className="text-indigo-600 hover:text-indigo-900 inline-flex items-center gap-1"
                  >
                    View Details
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </td>
              </tr>
            ))}
            {noticeList.length === 0 && (
              <tr>
                <td colSpan={5} className="py-12 text-center">
                  <div className="flex flex-col items-center gap-3 text-slate-500">
                    <FileWarning className="w-12 h-12 text-slate-300" />
                    <p className="text-lg font-medium">No notices found</p>
                    <p className="text-sm">Upload a notice PDF to get started</p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}