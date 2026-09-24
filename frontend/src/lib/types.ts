export interface DashboardMetrics {
  open_exceptions: number;
  high_priority_exceptions: number;
  notice_deadlines_30d: number;
  overdue_tasks: number;
  tasks_in_progress: number;
  blocked_tasks: number;
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

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: string;
  source_type: string;
  due_date?: string;
  owner_id?: string;
}

export interface NoticeCase {
  id: string;
  notice_type: string;
  reference_number?: string;
  issue_date?: string;
  response_deadline?: string;
  status: string;
}
