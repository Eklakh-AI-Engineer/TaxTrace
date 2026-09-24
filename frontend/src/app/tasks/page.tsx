'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Clock } from 'lucide-react';
import { Task } from '@/lib/types';

export default function TasksPage() {
  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => api.tasks.list(),
  });

  if (isLoading) {
    return <div className="p-8">Loading tasks...</div>;
  }

  const columns = [
    { id: 'open', title: 'Open', color: 'bg-slate-100' },
    { id: 'in_progress', title: 'In Progress', color: 'bg-blue-50' },
    { id: 'blocked', title: 'Blocked', color: 'bg-red-50' },
    { id: 'completed', title: 'Completed', color: 'bg-green-50' },
  ];

  return (
    <div className="p-8 h-full flex flex-col">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-slate-900">Tasks</h1>
        <p className="mt-2 text-sm text-slate-700">Manage follow-ups for exceptions and notices.</p>
      </div>

      <div className="flex-1 flex gap-6 overflow-x-auto pb-4">
        {columns.map((column) => (
          <div key={column.id} className={`flex flex-col flex-none w-80 rounded-lg p-4 ${column.color}`}>
            <h3 className="font-medium text-slate-900 mb-4">{column.title}</h3>
            <div className="flex-1 overflow-y-auto space-y-4">
              {tasks?.filter(t => t.status === column.id).map(task => (
                <div key={task.id} className="bg-white p-4 rounded shadow-sm border border-slate-200">
                  <div className="text-xs font-semibold text-indigo-600 mb-1 uppercase tracking-wider">
                    {task.source_type.replace('_', ' ')}
                  </div>
                  <h4 className="text-sm font-medium text-slate-900 mb-2">{task.title}</h4>
                  {task.due_date && (
                    <div className="flex items-center text-xs text-slate-500">
                      <Clock className="w-3 h-3 mr-1" />
                      {new Date(task.due_date).toLocaleDateString()}
                    </div>
                  )}
                </div>
              ))}
              {tasks?.filter(t => t.status === column.id).length === 0 && (
                <div className="text-sm text-slate-500 text-center py-4 border-2 border-dashed border-slate-300 rounded">
                  No tasks
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
