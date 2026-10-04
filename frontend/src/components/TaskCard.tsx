'use client';

import { useState } from 'react';
import { Task } from '@/lib/types';
import { Clock, ChevronDown, X, User, AlertTriangle } from 'lucide-react';

type Column = { id: string; title: string; color: string; border: string };

const COLUMNS: Column[] = [
  { id: 'open', title: 'Open', color: 'bg-slate-50', border: 'border-slate-200' },
  { id: 'in_progress', title: 'In Progress', color: 'bg-blue-50', border: 'border-blue-200' },
  { id: 'blocked', title: 'Blocked', color: 'bg-red-50', border: 'border-red-200' },
  { id: 'completed', title: 'Completed', color: 'bg-green-50', border: 'border-green-200' },
];

export function TaskCard({ task, onStatusChange, onDraft }: {
  task: Task;
  onStatusChange: (id: string, status: string) => void;
  onDraft: (task: Task) => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const isOverdue = task.due_date && task.status !== 'completed' && new Date(task.due_date) < new Date();

  return (
    <div className={`bg-white p-4 rounded-lg shadow-sm border ${isOverdue ? 'border-red-300 ring-1 ring-red-100' : 'border-slate-200'} transition-all hover:shadow-md`}>
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">
          {task.source_type?.replace('_', ' ') || 'manual'}
        </span>
        <div className="relative">
          <button onClick={() => setMenuOpen(!menuOpen)} className="text-slate-400 hover:text-slate-600" aria-label="Task options">
            <ChevronDown className="w-4 h-4" />
          </button>
          {menuOpen && (
            <div className="absolute right-0 top-6 z-10 w-40 bg-white rounded-lg shadow-lg border border-slate-200 py-1">
              {COLUMNS.filter(c => c.id !== task.status).map(col => (
                <button
                  key={col.id}
                  onClick={() => { onStatusChange(task.id, col.id); setMenuOpen(false); }}
                  className="block w-full text-left px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
                >
                  Move to {col.title}
                </button>
              ))}
              <hr className="my-1 border-slate-100" />
              <button
                onClick={() => { onDraft(task); setMenuOpen(false); }}
                className="block w-full text-left px-3 py-1.5 text-sm text-indigo-600 hover:bg-indigo-50"
              >
                Draft Follow-up
              </button>
            </div>
          )}
        </div>
      </div>

      <h4 className="text-sm font-medium text-slate-900 mb-2 leading-snug">{task.title}</h4>

      {task.description && (
        <p className="text-xs text-slate-500 mb-2 line-clamp-2">{task.description}</p>
      )}

      <div className="flex items-center gap-3 text-xs text-slate-500">
        {task.due_date && (
          <span className={`flex items-center gap-1 ${isOverdue ? 'text-red-600 font-semibold' : ''}`}>
            {isOverdue && <AlertTriangle className="w-3 h-3" />}
            <Clock className="w-3 h-3" />
            {new Date(task.due_date).toLocaleDateString()}
          </span>
        )}
        {task.owner_id && (
          <span className="flex items-center gap-1">
            <User className="w-3 h-3" />
            {task.owner_id.replace('user_', '').replace('user-', '')}
          </span>
        )}
      </div>
    </div>
  );
}