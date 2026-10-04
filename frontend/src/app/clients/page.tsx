'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Client } from '@/lib/types';
import { Search, Plus, Edit, Trash2, Filter, X } from 'lucide-react';
import Link from 'next/link';

export default function ClientsPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);
  const [formData, setFormData] = useState({ display_name: '', gstin: '', pan_reference: '', status: 'active' });

  const queryClient = useQueryClient();

  const { data: clientsData, isLoading, error, refetch } = useQuery({
    queryKey: ['clients', search, statusFilter],
    queryFn: () => api.clients.list({ search, status: statusFilter }),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => api.clients.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      setShowCreate(false);
      setFormData({ display_name: '', gstin: '', pan_reference: '', status: 'active' });
    },
    onError: () => alert('Failed to create client'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => api.clients.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      setEditingClient(null);
    },
    onError: () => alert('Failed to update client'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/clients/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${process.env.NEXT_PUBLIC_DEV_TOKEN}` },
    }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['clients'] }),
    onError: () => alert('Failed to delete client'),
  });

  const clients = Array.isArray(clientsData) ? clientsData : (clientsData as any)?.items || [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editingClient) {
      updateMutation.mutate({ id: editingClient.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleEdit = (client: Client) => {
    setEditingClient(client);
    setFormData({
      display_name: client.display_name,
      gstin: client.gstin || '',
      pan_reference: client.pan_reference || '',
      status: client.status,
    });
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this client?')) {
      deleteMutation.mutate(id);
    }
  };

  const resetForm = () => {
    setEditingClient(null);
    setFormData({ display_name: '', gstin: '', pan_reference: '', status: 'active' });
  };

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-slate-300 border-t-indigo-500 rounded-full animate-spin" />
        <span className="ml-3 text-slate-500">Loading clients...</span>
      </div>
    );
  }

  if (error) {
    return <div className="p-8 text-red-500">Failed to load clients.</div>;
  }

  return (
    <div className="p-8 space-y-8">
      <div className="sm:flex sm:items-center sm:justify-between mb-8">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-slate-900">Clients</h1>
          <p className="mt-2 text-sm text-slate-700">
            Manage your firm's clients and their GST details.
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex items-center gap-3">
          <button
            onClick={() => { setShowCreate(true); resetForm(); }}
            className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm"
          >
            <Plus className="w-4 h-4" /> Add Client
          </button>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name, GSTIN, PAN..."
              className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
            />
          </div>
          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2.5 rounded-lg border border-slate-300 bg-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
            >
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
            {search || statusFilter ? (
              <button
                onClick={() => { setSearch(''); setStatusFilter(''); }}
                className="p-2.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            ) : null}
          </div>
        </div>
      </div>

      {/* Clients Table */}
      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
        <table className="min-w-full divide-y divide-slate-300">
          <thead className="bg-slate-50">
            <tr>
              <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-slate-900">Name</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">GSTIN</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">PAN</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Status</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Created</th>
              <th className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {clients.map((client: Client) => (
              <tr key={client.id}>
                <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-slate-900">{client.display_name}</td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500 font-mono">{client.gstin || '—'}</td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500 font-mono">{client.pan_reference || '—'}</td>
                <td className="whitespace-nowrap px-3 py-4 text-sm">
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    client.status === 'active' ? 'bg-green-100 text-green-800' :
                    client.status === 'inactive' ? 'bg-slate-100 text-slate-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {client.status}
                  </span>
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500">
                  {new Date(client.created_at).toLocaleDateString()}
                </td>
                <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => handleEdit(client)}
                      className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                      title="Edit"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(client.id)}
                      className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {clients.length === 0 && (
              <tr>
                <td colSpan={6} className="py-12 text-center text-sm text-slate-500">
                  No clients found. Click "Add Client" to create your first client.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Create/Edit Modal */}
      {(showCreate || editingClient) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-2xl w-full max-w-lg p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">
                {editingClient ? 'Edit Client' : 'Add Client'}
              </h2>
              <button
                type="button"
                onClick={() => { setShowCreate(false); setEditingClient(null); resetForm(); }}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Display Name *</label>
              <input
                required
                value={formData.display_name}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
                placeholder="e.g., ABC Traders"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">GSTIN</label>
                <input
                  value={formData.gstin}
                  onChange={(e) => setFormData({ ...formData, gstin: e.target.value.toUpperCase() })}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
                  placeholder="29AAAAA0000A1Z5"
                  maxLength={15}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">PAN Reference</label>
                <input
                  value={formData.pan_reference}
                  onChange={(e) => setFormData({ ...formData, pan_reference: e.target.value.toUpperCase() })}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
                  placeholder="AAAAA0000A"
                  maxLength={10}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => { setShowCreate(false); setEditingClient(null); resetForm(); }}
                className="px-4 py-2 text-sm rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createMutation.isPending || updateMutation.isPending}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {createMutation.isPending || updateMutation.isPending ? 'Saving…' : (editingClient ? 'Update' : 'Create')}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}