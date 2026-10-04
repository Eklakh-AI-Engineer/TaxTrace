'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { KnowledgeSource, KnowledgeSearchRequest } from '@/lib/types';
import { Search, Plus, FileText, Globe, Trash2, Loader2, Brain } from 'lucide-react';

export default function KnowledgePage() {
  const [activeTab, setActiveTab] = useState<'search' | 'sources'>('sources');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLimit, setSearchLimit] = useState(5);
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    source_type: 'act',
    title: '',
    content: '',
    url: '',
    publisher: '',
    version: '',
    effective_from: '',
    effective_to: '',
  });

  const queryClient = useQueryClient();

  const { data: sourcesData, isLoading: sourcesLoading, refetch: refetchSources } = useQuery({
    queryKey: ['knowledgeSources'],
    queryFn: () => api.knowledge.listSources(),
  });

  const { data: searchResults, isLoading: searchLoading } = useQuery({
    queryKey: ['knowledgeSearch', searchQuery, searchLimit],
    queryFn: () => api.knowledge.search({ query: searchQuery, limit: searchLimit }),
    enabled: !!searchQuery.trim(),
  });

  const createMutation = useMutation({
    mutationFn: (payload: any) => api.knowledge.createSource(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledgeSources'] });
      setShowCreate(false);
      setCreateForm({
        source_type: 'act',
        title: '',
        content: '',
        url: '',
        publisher: '',
        version: '',
        effective_from: '',
        effective_to: '',
      });
    },
    onError: () => alert('Failed to create knowledge source'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/knowledge/sources/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${process.env.NEXT_PUBLIC_DEV_TOKEN}` },
    }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['knowledgeSources'] }),
    onError: () => alert('Failed to delete source'),
  });

  const sources = Array.isArray(sourcesData) ? sourcesData : (sourcesData as any)?.items || [];
  const results = searchResults?.results || [];

  return (
    <div className="p-8 space-y-8">
      <div className="sm:flex sm:items-center sm:justify-between mb-8">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-slate-900 flex items-center gap-2">
            <Brain className="w-6 h-6 text-indigo-600" />
            Knowledge Base
          </h1>
          <p className="mt-2 text-sm text-slate-700">
            Manage legal authorities and search the knowledge base for grounded AI drafting.
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <button
            onClick={() => { setShowCreate(true); setActiveTab('sources'); }}
            className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm"
          >
            <Plus className="w-4 h-4" /> Add Source
          </button>
        </div>
      </div>

      <div className="border-b border-slate-200 mb-6">
        <nav className="flex gap-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('search')}
            className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === 'search'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Search className="w-4 h-4" /> Search
          </button>
          <button
            onClick={() => setActiveTab('sources')}
            className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === 'sources'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <FileText className="w-4 h-4" /> Sources
          </button>
        </nav>
      </div>

      {activeTab === 'search' && (
        <SearchTab
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          searchLimit={searchLimit}
          setSearchLimit={setSearchLimit}
          searchLoading={searchLoading}
          results={results}
          queryClient={queryClient}
        />
      )}

      {activeTab === 'sources' && (
        <SourcesTab
          sources={sources}
          sourcesLoading={sourcesLoading}
          showCreate={showCreate}
          setShowCreate={setShowCreate}
          createForm={createForm}
          setCreateForm={setCreateForm}
          createMutation={createMutation}
          deleteMutation={deleteMutation}
        />
      )}
    </div>
  );
}

function SearchTab({
  searchQuery,
  setSearchQuery,
  searchLimit,
  setSearchLimit,
  searchLoading,
  results,
  queryClient,
}: {
  searchQuery: string;
  setSearchQuery: (v: string) => void;
  searchLimit: number;
  setSearchLimit: (v: number) => void;
  searchLoading: boolean;
  results: any[];
  queryClient: any;
}) {
  const handleSearch = () => {
    queryClient.invalidateQueries({ queryKey: ['knowledgeSearch', searchQuery, searchLimit] });
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <Search className="w-5 h-5 text-indigo-600" />
          Search Knowledge Base
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Search Query</label>
            <textarea
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              rows={3}
              placeholder="Enter your legal question or search terms..."
              className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
            />
          </div>
          <div className="flex items-center gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Max Results</label>
              <select
                value={searchLimit}
                onChange={(e) => setSearchLimit(Number(e.target.value))}
                className="px-3 py-2 rounded-lg border border-slate-300 bg-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
              >
                <option value={3}>3</option>
                <option value={5}>5</option>
                <option value={10}>10</option>
              </select>
            </div>
            <button
              onClick={handleSearch}
              disabled={!searchQuery.trim() || searchLoading}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              <Search className="w-4 h-4" />
              {searchLoading ? 'Searching…' : 'Search'}
            </button>
          </div>
        </div>
      </div>

      {searchQuery && !searchLoading && results.length === 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 text-center">
          <p className="text-sm text-amber-800">No results found for "{searchQuery}". Try different search terms.</p>
        </div>
      )}

      {results.length > 0 ? (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-900">Results ({results.length})</h3>
          <div className="space-y-3">
            {results.map((result) => (
              <div key={result.chunk_id} className="bg-white border border-slate-200 rounded-lg p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700">
                        {result.source_type?.toUpperCase() ?? 'SOURCE'}
                      </span>
                      <span className="text-sm font-medium text-slate-900 truncate">{result.title}</span>
                    </div>
                    {result.section && (
                      <p className="text-xs text-slate-500 mb-2">Section: {result.section}</p>
                    )}
                    <p className="text-sm text-slate-700 line-clamp-3">{result.content}</p>
                    <div className="flex items-center gap-2 mt-2 pt-2 border-t border-slate-100">
                      {result.url && (
                        <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
                          <Globe className="w-3 h-3" /> View Source
                        </a>
                      )}
                      {result.version && (
                        <span className="text-xs text-slate-500">v{result.version}</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function SourcesTab({
  sources,
  sourcesLoading,
  showCreate,
  setShowCreate,
  createForm,
  setCreateForm,
  createMutation,
  deleteMutation,
}: {
  sources: any[];
  sourcesLoading: boolean;
  showCreate: boolean;
  setShowCreate: (v: boolean) => void;
  createForm: any;
  setCreateForm: (v: any) => void;
  createMutation: any;
  deleteMutation: any;
}) {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-indigo-600" />
          Knowledge Sources
        </h2>

        {sourcesLoading ? (
          <div className="p-8 text-center text-slate-500">Loading sources...</div>
        ) : (
          <>
            <div className="mb-4">
              <button
                onClick={() => setShowCreate(true)}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
              >
                <Plus className="w-4 h-4" /> Add Source
              </button>
            </div>

            {sources.length > 0 ? (
              <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
                <table className="min-w-full divide-y divide-slate-300">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-slate-900">Title</th>
                      <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Type</th>
                      <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Publisher</th>
                      <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Version</th>
                      <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Effective</th>
                      <th className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                        <span className="sr-only">Actions</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white">
                    {sources.map((source) => (
                      <tr key={source.id}>
                        <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-slate-900 truncate max-w-xs">
                          {source.title}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500">
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700">
                            {source.source_type?.toUpperCase()}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500">{source.publisher || '—'}</td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500">{source.version || '—'}</td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500">
                          {source.effective_from ? new Date(source.effective_from).toLocaleDateString() : '—'}
                        </td>
                        <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                          <button
                            onClick={() => {
                              if (confirm('Delete this knowledge source?')) {
                                deleteMutation.mutate(source.id);
                              }
                            }}
                            className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12">
                <FileText className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                <p className="text-lg font-medium text-slate-900 mb-2">No knowledge sources yet</p>
                <p className="text-sm text-slate-500 mb-6">Add your first legal authority source to enable grounded AI drafting.</p>
                <button
                  onClick={() => setShowCreate(true)}
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
                >
                  <Plus className="w-4 h-4" /> Add Source
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

