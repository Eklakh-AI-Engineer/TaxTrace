export interface DashboardMetrics {
  firm_id: string;
  generated_at: string;
  tasks: {
    total_open: number;
    in_progress: number;
    blocked: number;
    completed: number;
    overdue: number;
  };
  exceptions: {
    total_unresolved: number;
    open: number;
    in_review: number;
  };
  notices: {
    total_active: number;
    urgent_deadlines_within_7_days: number;
  };
  operations?: {
    estimated_hours_saved: number;
    manual_overrides: number;
    ai_drafts_generated: number;
  };
  overdue_task_items: Task[];
}

export interface Exception {
  id: string;
  type: string;
  severity: string;
  status: string;
  reason_code?: string;
  explanation?: string;
  created_by_system: boolean;
  assigned_to?: string;
  created_at: string;
}

export interface ExceptionDetail extends Exception {
  evidence: Evidence[];
}

export interface Evidence {
  id: string;
  evidence_type: string;
  source_document_id?: string;
  source_row_reference?: string;
  source_field?: string;
  source_text?: string;
  source_url?: string;
  source_version?: string;
  meta_data?: Record<string, any>;
  created_at: string;
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: string;
  source_type: string;
  client_id?: string;
  exception_id?: string;
  notice_case_id?: string;
  due_date?: string;
  owner_id?: string;
  created_at?: string;
}

export interface DraftMessageResponse {
  task_id: string;
  channel: string;
  subject: string | null;
  message_body: string;
  evidence_references: string[];
}

export interface NoticeCase {
  id: string;
  notice_type: string;
  reference_number?: string;
  issue_date?: string;
  response_deadline?: string;
  status: string;
}

export interface NoticeDetail extends NoticeCase {
  client_id: string;
  period_id?: string;
  source_document_id: string;
  taxpayer_gstin?: string;
  taxpayer_name?: string;
  tax_period?: string;
  demand_tax_amount?: number;
  cited_sections: string[];
  extracted_facts: Record<string, any>;
  evidence: Evidence[];
}

export interface ExtractionResponse {
  notice_case_id: string;
  notice_type: string;
  reference_number?: string;
  taxpayer_gstin?: string;
  taxpayer_name?: string;
  issue_date?: string;
  response_deadline?: string;
  demand_tax_amount?: number;
  cited_sections: string[];
  evidence_created_count: number;
}

export interface Draft {
  id: string;
  tenant_id: string;
  notice_case_id: string;
  status: string;
  content: string;
  cited_sections: string[];
  missing_information: string[];
  approved_by?: string;
  approval_comment?: string;
  created_at: string;
  approved_at?: string;
}

export interface DraftCreateRequest {
  instructions: string;
}

export interface DraftApproveRequest {
  comment: string;
}

export interface Period {
  id: string;
  firm_id: string;
  client_id: string;
  tenant_id: string;
  financial_year: string;
  tax_period: string;
  status: string;
  created_at: string;
}
