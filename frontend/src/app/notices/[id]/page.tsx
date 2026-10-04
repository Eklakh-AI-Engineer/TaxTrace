'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { NoticeDetail, Draft, Evidence, ExtractionResponse } from '@/lib/types';
import { ArrowLeft, FileText, AlertTriangle, CheckCircle2, XCircle, Clock, Gavel, Send, Edit2, Download } from 'lucide-react';
import Link from 'next/link';

export default function NoticeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const id = params.id as string;
  const [activeTab, setActiveTab] = useState<'facts' | 'draft'>('facts');
  const [draft, setDraft] = useState<Draft | null>(null);
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [approvalComment, setApprovalComment] = useState('');

  const { data: notice, isLoading: noticeLoading, error: noticeError } = useQuery({
    queryKey: ['notice', id],
    queryFn: () => api.notices.get(id),
    enabled: !!id,
  });

  const { data: extraction, isLoading: extractionLoading } = useQuery({
    queryKey: ['notice-extraction', id],
    queryFn: () => api.notices.extract(id),
    enabled: !!id && notice?.status === 'received',
  });

  const generateDraftMutation = useMutation({
    mutationFn: (instructions: string) => api.notices.generateDraft(id, { instructions }),
    onSuccess: (data) => {
      setDraft(data);
      setActiveTab('draft');
      queryClient.invalidateQueries({ queryKey: ['notice', id] });
    },
    onError: () => alert('Failed to generate draft'),
  });

  const approveDraftMutation = useMutation({
    mutationFn: (comment: string) => api.notices.approveDraft(draft!.id, { comment }),
    onSuccess: () => {
      setShowApproveDialog(false);
      setApprovalComment('');
      queryClient.invalidateQueries({ queryKey: ['notice', id] });
      router.refresh();
    },
    onError: () => alert('Failed to approve draft'),
  });

  if (noticeLoading) {
    return <div className="p-8 flex items-center justify-center">Loading notice...</div>;
  }

  if (noticeError || !notice) {
    return <div className="p-8 text-red-500">Notice not found.</div>;
  }

  const isPartner = typeof window !== 'undefined' && localStorage.getItem('user_role') === 'partner';

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-6">
        <Link href="/notices" className="flex items-center text-sm text-indigo-600 hover:text-indigo-900">
          <ArrowLeft className="mr-1 h-4 w-4" />
          Back to Notices
        </Link>
      </div>

      <div className="bg-white shadow sm:rounded-lg mb-8">
        <div className="px-6 py-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">{notice.notice_type}</h2>
            <p className="mt-1 text-sm text-slate-500">Reference: {notice.reference_number || 'N/A'}</p>
          </div>
          <div className="flex items-center gap-4">
            <span className={`inline-flex items-center rounded-md px-3 py-1 text-sm font-medium ${
              notice.status === 'received' ? 'bg-blue-100 text-blue-800' :
              notice.status === 'facts_extracted' ? 'bg-yellow-100 text-yellow-800' :
              notice.status === 'draft_generated' ? 'bg-purple-100 text-purple-800' :
              notice.status === 'approved' ? 'bg-green-100 text-green-800' :
              'bg-slate-100 text-slate-800'
            }`}>
              {notice.status.replace('_', ' ').toUpperCase()}
            </span>
            {notice.response_deadline && (
              <div className="flex items-center gap-1 text-sm text-slate-600">
                <Clock className="w-4 h-4" />
                Deadline: {new Date(notice.response_deadline).toLocaleDateString()}
                {(new Date(notice.response_deadline) < new Date()) && (
                  <span className="text-red-600 font-semibold ml-1">(OVERDUE)</span>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="px-6 py-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-slate-50 p-4 rounded-lg">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Taxpayer GSTIN</p>
              <p className="text-sm font-medium text-slate-900 font-mono mt-1">{notice.taxpayer_gstin || 'Not extracted'}</p>
            </div>
            <div className="bg-slate-50 p-4 rounded-lg">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Taxpayer Name</p>
              <p className="text-sm font-medium text-slate-900 mt-1">{notice.taxpayer_name || 'Not extracted'}</p>
            </div>
            <div className="bg-slate-50 p-4 rounded-lg">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Issue Date</p>
              <p className="text-sm font-medium text-slate-900 mt-1">{notice.issue_date ? new Date(notice.issue_date).toLocaleDateString() : 'Not extracted'}</p>
            </div>
            <div className="bg-slate-50 p-4 rounded-lg">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Demand Amount</p>
              <p className="text-sm font-medium text-slate-900 mt-1">{notice.demand_tax_amount ? `₹${notice.demand_tax_amount.toLocaleString()}` : 'Not extracted'}</p>
            </div>
          </div>

          <div className="border-t border-slate-200 pt-6 mb-6">
            <h3 className="text-lg font-medium text-slate-900 mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-500" />
              Cited Sections ({notice.cited_sections.length})
            </h3>
            {notice.cited_sections.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {notice.cited_sections.map((section) => (
                  <span key={section} className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                    Section {section}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500">No sections cited in notice</p>
            )}
          </div>
        </div>
      </div>

      <div className="border-b border-slate-200 mb-6">
        <nav className="flex gap-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('facts')}
            className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === 'facts'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <FileText className="w-4 h-4" /> Extracted Facts & Evidence
          </button>
          <button
            onClick={() => setActiveTab('draft')}
            className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === 'draft'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Gavel className="w-4 h-4" /> Response Draft
          </button>
        </nav>
      </div>

      {activeTab === 'facts' && (
        <div className="space-y-6">
          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-6 py-4 border-b border-slate-200">
              <h3 className="text-lg font-medium text-slate-900 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                All Extracted Fields
              </h3>
            </div>
            <div className="p-6">
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-6">
                {Object.entries(notice.extracted_facts).map(([key, value]) => (
                  <div key={key}>
                    <dt className="text-sm font-medium text-slate-500 capitalize">{key.replace(/_/g, ' ')}</dt>
                    <dd className="mt-1 text-sm text-slate-900 font-mono bg-slate-50 p-3 rounded border border-slate-200 whitespace-pre-wrap">
                      {value !== null && value !== undefined ? JSON.stringify(value, null, 2) : '—'}
                    </dd>
                  </div>
                ))}
              </dl>
              {Object.keys(notice.extracted_facts).length === 0 && (
                <p className="text-sm text-slate-500">No facts extracted yet. Run extraction first.</p>
              )}
            </div>
          </div>

          {extractionLoading && (
            <div className="bg-white shadow sm:rounded-lg p-6 text-center">
              <div className="flex items-center justify-center gap-2 text-slate-500">
                <div className="w-5 h-5 border-2 border-slate-300 border-t-indigo-500 rounded-full animate-spin" />
                Running extraction...
              </div>
            </div>
          )}

          {!extractionLoading && notice.status === 'received' && (
            <div className="bg-white shadow sm:rounded-lg p-6 text-center">
              <button
                onClick={() => {
                  queryClient.invalidateQueries({ queryKey: ['notice-extraction', id] });
                  queryClient.invalidateQueries({ queryKey: ['notice', id] });
                }}
                className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
              >
                <FileText className="w-4 h-4" /> Extract Facts from Notice
              </button>
            </div>
          )}

          {!extractionLoading && extraction && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-center gap-2 text-green-800 mb-2">
                <CheckCircle2 className="w-5 h-5" />
                <span className="font-medium">Extraction Complete</span>
              </div>
              <p className="text-sm text-green-700">Found {extraction.evidence_created_count} evidence items. {extraction.cited_sections.length} sections cited.</p>
            </div>
          )}

          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-6 py-4 border-b border-slate-200">
              <h3 className="text-lg font-medium text-slate-900 flex items-center gap-2">
                <FileText className="w-5 h-5 text-emerald-500" />
                Evidence Records ({notice.evidence.length})
              </h3>
            </div>
            <div className="p-6">
              {notice.evidence.length > 0 ? (
                <div className="space-y-4">
                  {notice.evidence.map((ev) => (
                    <div key={ev.id} className="border border-slate-200 rounded-lg p-4 bg-slate-50/50">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700">
                              {ev.evidence_type.replace('_', ' ').toUpperCase()}
                            </span>
                            {ev.source_field && (
                              <span className="text-xs text-slate-500">Field: {ev.source_field}</span>
                            )}
                          </div>
                          <p className="text-sm text-slate-900 font-mono whitespace-pre-wrap">{ev.source_text}</p>
                          {ev.meta_data && Object.keys(ev.meta_data).length > 0 && (
                            <details className="mt-2">
                              <summary className="text-xs text-slate-500 cursor-pointer">View metadata</summary>
                              <pre className="mt-1 text-xs text-slate-600 bg-slate-100 p-2 rounded">{JSON.stringify(ev.meta_data, null, 2)}</pre>
                            </details>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500 text-center py-8">No evidence records attached</p>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'draft' && (
        <div className="space-y-6">
          {!draft && notice.status !== 'draft_generated' && notice.status !== 'approved' && (
            <div className="bg-white shadow sm:rounded-lg p-8 text-center">
              <FileText className="w-12 h-12 mx-auto text-slate-300 mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">No Draft Generated Yet</h3>
              <p className="text-sm text-slate-500 mb-6 max-w-md mx-auto">
                Generate an AI-assisted preliminary response draft based on the extracted facts and cited sections.
              </p>
              <button
                onClick={() => generateDraftMutation.mutate('Draft a preliminary reply denying the demand and requesting clarification on the alleged discrepancies.')}
                disabled={generateDraftMutation.isPending}
                className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
                {generateDraftMutation.isPending ? 'Generating…' : 'Generate Draft'}
              </button>
            </div>
          )}

          {draft && (
            <div className="bg-white shadow sm:rounded-lg">
              <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
                <h3 className="text-lg font-medium text-slate-900 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-indigo-500" />
                  Preliminary Response Draft
                </h3>
                <span className={`inline-flex items-center rounded-md px-2.5 py-0.5 text-sm font-medium ${
                  draft.status === 'under_review' ? 'bg-blue-100 text-blue-800' :
                  draft.status === 'approved' ? 'bg-green-100 text-green-800' :
                  'bg-slate-100 text-slate-800'
                }`}>
                  {draft.status.toUpperCase().replace('_', ' ')}
                </span>
              </div>
              <div className="p-6 space-y-6">
                {draft.cited_sections.length > 0 && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-blue-800 mb-2 flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" /> Cited Sections ({draft.cited_sections.length})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {draft.cited_sections.map((section) => (
                        <span key={section} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-700 border border-blue-200">
                          Section {section}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {draft.missing_information.length > 0 && (
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-amber-800 mb-2 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" /> Missing Information Required
                    </h4>
                    <ul className="text-sm text-amber-700 space-y-1">
                      {draft.missing_information.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="flex-shrink-0 mt-0.5">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Draft Content (Editable)</label>
                  <textarea
                    value={draft.content}
                    onChange={(e) => setDraft({ ...draft, content: e.target.value })}
                    rows={20}
                    className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm font-mono focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
                    spellCheck={false}
                  />
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                  <div className="flex items-center gap-4">
                    <button
                      onClick={() => {
                        const blob = new Blob([draft.content], { type: 'text/plain' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `draft-${draft.id}.txt`;
                        a.click();
                        URL.revokeObjectURL(url);
                      }}
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50"
                    >
                      <Download className="w-4 h-4" /> Download
                    </button>
                    {isPartner && draft.status === 'under_review' && (
                      <button
                        onClick={() => setShowApproveDialog(true)}
                        className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-green-600 text-white hover:bg-green-700"
                      >
                        <CheckCircle2 className="w-4 h-4" /> Approve for Use
                      </button>
                    )}
                  </div>
                  <div className="text-xs text-slate-500">
                    Created: {new Date(draft.created_at).toLocaleString()}
                    {draft.approved_at && <span className="ml-4">Approved: {new Date(draft.approved_at).toLocaleString()}</span>}
                    {draft.approved_by && <span className="ml-4">By: {draft.approved_by}</span>}
                  </div>
                </div>
              </div>
            </div>
          )}

          {draft && draft.status === 'approved' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
              <div className="flex items-center justify-center gap-2 text-green-800 mb-2">
                <CheckCircle2 className="w-6 h-6" />
                <span className="font-medium text-lg">Draft Approved</span>
              </div>
              <p className="text-sm text-green-700">This draft has been approved by a partner and is ready for external compliance use.</p>
              {draft.approval_comment && (
                <p className="mt-2 text-sm text-green-700"><strong>Approval comment:</strong> {draft.approval_comment}</p>
              )}
            </div>
          )}
        </div>
      )}

      {showApproveDialog && draft && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Approve Draft</h2>
              <button onClick={() => setShowApproveDialog(false)} className="text-slate-400 hover:text-slate-600">
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <p className="text-sm text-slate-600">
              You are about to approve this draft for external compliance use. This action requires partner authorization and will be logged in the audit trail.
            </p>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Approval Comment (required)</label>
              <textarea
                value={approvalComment}
                onChange={(e) => setApprovalComment(e.target.value)}
                rows={3}
                required
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
                placeholder="Enter reason for approval..."
              />
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setShowApproveDialog(false)}
                className="px-4 py-2 text-sm rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={() => approveDraftMutation.mutate(approvalComment)}
                disabled={approveDraftMutation.isPending || !approvalComment.trim()}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
              >
                <CheckCircle2 className="w-4 h-4" />
                {approveDraftMutation.isPending ? 'Approving…' : 'Confirm Approval'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}