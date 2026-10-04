'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useParams } from 'next/navigation';
import { ArrowLeft, Check, X, HelpCircle } from 'lucide-react';
import Link from 'next/link';

export default function ExceptionDetail() {
  const params = useParams();
  const queryClient = useQueryClient();
  const id = params.id as string;

  const { data: exception, isLoading } = useQuery({
    queryKey: ['exception', id],
    queryFn: () => api.exceptions.get(id),
  });

  const decisionMutation = useMutation({
    mutationFn: ({ action, reason }: { action: string; reason?: string }) => 
      api.exceptions.makeDecision(id, action, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exception', id] });
      queryClient.invalidateQueries({ queryKey: ['exceptions'] });
    },
  });

  if (isLoading) {
    return <div className="p-8">Loading exception...</div>;
  }

  if (!exception) {
    return <div className="p-8 text-red-500">Exception not found.</div>;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-6">
        <Link href="/exceptions" className="flex items-center text-sm text-indigo-600 hover:text-indigo-900">
          <ArrowLeft className="mr-1 h-4 w-4" />
          Back to Exceptions
        </Link>
      </div>

      <div className="bg-white shadow sm:rounded-lg mb-8">
        <div className="px-4 py-5 sm:px-6 flex justify-between items-center border-b border-slate-200">
          <div>
            <h3 className="text-lg font-medium leading-6 text-slate-900">Exception Detail</h3>
            <p className="mt-1 max-w-2xl text-sm text-slate-500">Review discrepancy and make a decision.</p>
          </div>
          <div className="flex space-x-3">
            <span className={`inline-flex items-center rounded-md px-2.5 py-0.5 text-sm font-medium ${
              exception.status === 'open' ? 'bg-blue-100 text-blue-800' :
              exception.status === 'resolved' ? 'bg-green-100 text-green-800' :
              'bg-slate-100 text-slate-800'
            }`}>
              {exception.status.toUpperCase()}
            </span>
            <span className={`inline-flex items-center rounded-md px-2.5 py-0.5 text-sm font-medium ${
              exception.severity === 'high' ? 'bg-red-100 text-red-800' :
              exception.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
              'bg-green-100 text-green-800'
            }`}>
              {exception.severity.toUpperCase()}
            </span>
          </div>
        </div>
        
        <div className="px-4 py-5 sm:p-6">
          <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-slate-500">Exception Type</dt>
              <dd className="mt-1 text-sm text-slate-900 font-mono">{exception.type}</dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-slate-500">Reason Code</dt>
              <dd className="mt-1 text-sm text-slate-900">{exception.reason_code || 'None'}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-sm font-medium text-slate-500">Explanation</dt>
              <dd className="mt-1 text-sm text-slate-900 bg-slate-50 p-4 rounded-md border border-slate-200 whitespace-pre-wrap">
                {exception.explanation || 'No explanation available.'}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {exception.status !== 'resolved' && exception.status !== 'accepted' && (
        <div className="bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:px-6 border-b border-slate-200">
            <h3 className="text-lg font-medium leading-6 text-slate-900">Actions</h3>
          </div>
          <div className="px-4 py-5 sm:p-6 flex space-x-4">
            <button
              onClick={() => decisionMutation.mutate({ action: 'accept' })}
              disabled={decisionMutation.isPending}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
            >
              <Check className="mr-2 h-4 w-4" />
              Accept
            </button>
            <button
              onClick={() => decisionMutation.mutate({ action: 'reject' })}
              disabled={decisionMutation.isPending}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
            >
              <X className="mr-2 h-4 w-4" />
              Reject
            </button>
            <button
              onClick={() => decisionMutation.mutate({ action: 'needs_info', reason: 'Requested info from client' })}
              disabled={decisionMutation.isPending}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-amber-600 hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 disabled:opacity-50"
            >
              <HelpCircle className="mr-2 h-4 w-4" />
              Needs Info
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
