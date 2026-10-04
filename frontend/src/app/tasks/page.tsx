'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Task } from '@/lib/types';
import { Plus, Mail, MessageCircle, X, Send } from 'lucide-react';
import { TaskCard } from '@/components/TaskCard';

type Column = { id: string; title: string; color: string; border: string };

const COLUMNS: Column[] = [
  { id: 'open', title: 'Open', color: 'bg-slate-50', border: 'border-slate-200' },
  { id: 'in_progress', title: 'In Progress', color: 'bg-blue-50', border: 'border-blue-200' },
  { id: 'blocked', title: 'Blocked', color: 'bg-red-50', border: 'border-red-200' },
  { id: 'completed', title: 'Completed', color: 'bg-green-50', border: 'border-green-200' },
];

/* ─── Create Task Modal ─── */
function CreateTaskModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [assignee, setAssignee] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.tasks.create({
        title,
        description: description || undefined,
        due_date: dueDate || undefined,
        owner_id: assignee || undefined,
      });
      onCreated();
      onClose();
    } catch {
      alert('Failed to create task');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-2xl w-full max-w-lg p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">Create Task</h2>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Title *</label>
          <input required value={title} onChange={e => setTitle(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none" />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
          <textarea value={description} onChange={e => setDescription(e.target.value)} rows={3}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none" />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Due Date</label>
            <input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Assign To</label>
            <input value={assignee} onChange={e => setAssignee(e.target.value)} placeholder="user-id"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none" />
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50">Cancel</button>
          <button type="submit" disabled={submitting}
            className="px-4 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2">
            {submitting ? 'Creating…' : <><Plus className="w-4 h-4" /> Create Task</>}
          </button>
        </div>
      </form>
    </div>
  );
}

/* ─── Draft Message Modal ─── */
function DraftMessageModal({ task, onClose }: { task: Task; onClose: () => void }) {
  const [channel, setChannel] = useState<'email' | 'whatsapp'>('email');
  const [draft, setDraft] = useState<{ subject: string | null; message_body: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const generateDraft = async () => {
    setLoading(true);
    try {
      const result = await api.tasks.draftMessage(task.id, channel, 'vendor');
      setDraft(result);
    } catch {
      alert('Failed to generate draft');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl p-6 space-y-4 max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">Draft Follow-up Message</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
        </div>

        <p className="text-sm text-slate-600">Task: <span className="font-medium text-slate-900">{task.title}</span></p>

        <div className="flex gap-3">
          <button onClick={() => setChannel('email')}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-lg border ${channel === 'email' ? 'bg-indigo-50 border-indigo-300 text-indigo-700' : 'border-slate-300 text-slate-700 hover:bg-slate-50'}`}>
            <Mail className="w-4 h-4" /> Email
          </button>
          <button onClick={() => setChannel('whatsapp')}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-lg border ${channel === 'whatsapp' ? 'bg-green-50 border-green-300 text-green-700' : 'border-slate-300 text-slate-700 hover:bg-slate-50'}`}>
            <MessageCircle className="w-4 h-4" /> WhatsApp
          </button>
        </div>

        <button onClick={generateDraft} disabled={loading}
          className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50">
          <Send className="w-4 h-4" /> {loading ? 'Generating…' : 'Generate Draft'}
        </button>

        {draft && (
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-2">
            {draft.subject && (
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Subject</span>
                <p className="text-sm text-slate-900 font-medium">{draft.subject}</p>
              </div>
            )}
            <div>
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Body</span>
              <pre className="text-sm text-slate-800 whitespace-pre-wrap font-sans mt-1">{draft.message_body}</pre>
            </div>
          </div>
        )}

        <div className="flex justify-end pt-2">
          <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50">Close</button>
        </div>
      </div>
    </div>
  );
}


export default function TasksPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [draftTask, setDraftTask] = useState<Task | null>(null);

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => api.tasks.list(),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => api.tasks.update(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  });

  const handleStatusChange = (id: string, status: string) => {
    updateMutation.mutate({ id, status });
  };

  if (isLoading) {
    return (
      <div className="p-8 flex items-center gap-3 text-slate-500">
        <div className="w-5 h-5 border-2 border-slate-300 border-t-indigo-500 rounded-full animate-spin" />
        Loading tasks…
      </div>
    );
  }

  const taskList = Array.isArray(tasks) ? tasks : ((tasks as unknown as { items?: Task[] })?.items) || [];

  return (
    <div className="p-8 h-full flex flex-col">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Tasks</h1>
          <p className="mt-1 text-sm text-slate-600">Manage follow-ups for exceptions and notices.</p>
        </div>
        <button onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm">
          <Plus className="w-4 h-4" /> New Task
        </button>
      </div>

      <div className="flex-1 flex gap-6 overflow-x-auto pb-4">
        {COLUMNS.map((column) => {
          const colTasks = taskList.filter((t) => t.status === column.id);
          return (
            <div key={column.id} className={`flex flex-col flex-none w-80 rounded-xl p-4 ${column.color} border ${column.border}`}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-slate-900">{column.title}</h3>
                <span className="text-xs font-semibold bg-white/80 text-slate-600 px-2 py-0.5 rounded-full">{colTasks.length}</span>
              </div>
              <div className="flex-1 overflow-y-auto space-y-3">
                {colTasks.map((task: Task) => (
                  <TaskCard key={task.id} task={task} onStatusChange={handleStatusChange} onDraft={setDraftTask} />
                ))}
                {colTasks.length === 0 && (
                  <div className="text-sm text-slate-400 text-center py-8 border-2 border-dashed border-slate-300/50 rounded-lg">
                    No tasks
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {showCreate && (
        <CreateTaskModal
          onClose={() => setShowCreate(false)}
          onCreated={() => queryClient.invalidateQueries({ queryKey: ['tasks'] })}
        />
      )}

      {draftTask && (
        <DraftMessageModal task={draftTask} onClose={() => setDraftTask(null)} />
      )}
    </div>
  );
}
