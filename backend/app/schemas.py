"""Pydantic schemas for API request/response validation.

Schemas follow CODING_RULES.md Section 6:
    - request/response schemas are explicit
    - consistent error format
    - pagination for collections
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Common / shared schemas
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    """Standard error response body per API_SPEC.md Section 1."""

    code: str
    message: str
    request_id: str | None = None
    details: dict | None = None


class ErrorResponse(BaseModel):
    """Wrapper for error payloads."""

    error: ErrorDetail


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated collection response."""

    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool


class PaginationParams(BaseModel):
    """Query parameters for paginated endpoints."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


# ---------------------------------------------------------------------------
# Firm schemas
# ---------------------------------------------------------------------------


class FirmCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    status: str = "active"
    plan: Optional[str] = None


class FirmRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: str
    plan: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FirmUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    plan: Optional[str] = None


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    email: str = Field(..., max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    status: str = "active"


# ---------------------------------------------------------------------------
# Firm membership schemas
# ---------------------------------------------------------------------------


class MembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    firm_id: str
    user_id: str
    role: str
    created_at: datetime


class MembershipCreate(BaseModel):
    user_id: str
    role: str = "staff"


# ---------------------------------------------------------------------------
# Client schemas
# ---------------------------------------------------------------------------


class ClientCreate(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=255)
    gstin: Optional[str] = Field(default=None, max_length=30)
    pan_reference: Optional[str] = Field(default=None, max_length=20)
    status: str = "active"


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    firm_id: str
    tenant_id: str
    display_name: str
    gstin: Optional[str] = None
    pan_reference: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class ClientUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    gstin: Optional[str] = Field(default=None, max_length=30)
    pan_reference: Optional[str] = Field(default=None, max_length=20)
    status: Optional[str] = None


# ---------------------------------------------------------------------------
# Period schemas
# ---------------------------------------------------------------------------


class PeriodCreate(BaseModel):
    client_id: str
    financial_year: str = Field(..., min_length=4, max_length=50)
    tax_period: str = Field(..., min_length=1, max_length=50)
    status: str = "open"


class PeriodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    firm_id: str
    client_id: str
    tenant_id: str
    financial_year: str
    tax_period: str
    status: str
    created_at: datetime


class PeriodUpdate(BaseModel):
    status: Optional[str] = None


# ---------------------------------------------------------------------------
# Document metadata schemas (read-only in Stage 1; upload API in Stage 2)
# ---------------------------------------------------------------------------


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    firm_id: str
    client_id: str
    period_id: Optional[str] = None
    tenant_id: str
    document_type: str
    original_filename: str
    content_hash: str
    mime_type: str
    size_bytes: int
    processing_status: str
    uploaded_by: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None


class DocumentUploadResponse(BaseModel):
    """Response per API_SPEC.md §5 for POST /documents."""

    document_id: str
    status: str
    content_hash: str
    original_filename: str
    extracted_transactions_count: int = 0


# ---------------------------------------------------------------------------
# Transaction schemas
# ---------------------------------------------------------------------------


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    firm_id: str
    client_id: str
    period_id: str
    tenant_id: str
    source_document_id: str
    source_row_reference: Optional[str] = None
    supplier_gstin: Optional[str] = None
    invoice_number_raw: Optional[str] = None
    invoice_number_normalized: Optional[str] = None
    invoice_date: Optional[date] = None
    taxable_value: Optional[float] = None
    cgst: Optional[float] = None
    sgst: Optional[float] = None
    igst: Optional[float] = None
    cess: Optional[float] = None
    currency: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Audit event schemas
# ---------------------------------------------------------------------------


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    firm_id: str
    tenant_id: str
    entity_type: str
    entity_id: str
    event_type: str
    payload_json: Optional[dict] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Reconciliation schemas
# ---------------------------------------------------------------------------


class ReconciliationRunRequest(BaseModel):
    client_id: str
    period_id: str
    rule_version: str = "recon-rule-v1"


class ReconciliationSummary(BaseModel):
    matched: int = 0
    partial_match: int = 0
    missing_in_2b: int = 0
    missing_in_books: int = 0
    duplicates: int = 0
    review_required: int = 0
    total_exceptions: int = 0


class ReconciliationRunResponse(BaseModel):
    period_id: str
    status: str
    summary: ReconciliationSummary
    total_matches_created: int
    total_exceptions_created: int


# ---------------------------------------------------------------------------
# Exception & Evidence schemas
# ---------------------------------------------------------------------------


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    firm_id: str
    tenant_id: str
    exception_id: Optional[str] = None
    evidence_type: str
    source_document_id: Optional[str] = None
    source_row_reference: Optional[str] = None
    source_field: Optional[str] = None
    source_text: Optional[str] = None
    meta_data: Optional[dict] = None
    created_at: datetime


class ExceptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    firm_id: str
    period_id: str
    tenant_id: str
    match_id: Optional[str] = None
    type: str
    severity: str
    status: str
    reason_code: Optional[str] = None
    explanation: Optional[str] = None
    created_by_system: bool
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ExceptionDetailRead(ExceptionRead):
    evidence: list[EvidenceRead] = []


class ExceptionUpdate(BaseModel):
    status: Optional[str] = Field(default=None, pattern="^(open|in_review|accepted|rejected|resolved)$")
    explanation: Optional[str] = None
    assigned_to: Optional[str] = None


class ExceptionDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(accepted|rejected|resolved|needs_info)$")
    comment: str = Field(..., min_length=1, max_length=1000)


class AIExplanationRequest(BaseModel):
    mode: str = "concise"


class AIExplanationResponse(BaseModel):
    explanation_id: str
    summary: str
    facts: list[str]
    possible_causes: list[str]
    suggested_next_steps: list[str]
    confidence: float
    evidence_ids: list[str]


# ---------------------------------------------------------------------------
# Notice schemas
# ---------------------------------------------------------------------------


class NoticeCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    firm_id: str
    client_id: str
    period_id: Optional[str] = None
    tenant_id: str
    source_document_id: str
    notice_type: str
    reference_number: Optional[str] = None
    issue_date: Optional[date] = None
    response_deadline: Optional[date] = None
    status: str
    created_at: datetime
    updated_at: datetime


class NoticeExtractionResponse(BaseModel):
    notice_case_id: str
    notice_type: str
    reference_number: Optional[str] = None
    taxpayer_gstin: Optional[str] = None
    taxpayer_name: Optional[str] = None
    issue_date: Optional[date] = None
    response_deadline: Optional[date] = None
    demand_tax_amount: Optional[float] = None
    cited_sections: list[str] = []
    evidence_created_count: int = 0


# ---------------------------------------------------------------------------
# Draft schemas
# ---------------------------------------------------------------------------


class DraftCreateRequest(BaseModel):
    instructions: str = Field(
        default="Prepare a formal, evidence-backed preliminary reply addressing all points.",
        max_length=2000,
    )


class DraftRead(BaseModel):
    id: str
    notice_case_id: str
    status: str  # draft, under_review, approved
    content: str
    cited_sections: list[str] = []
    missing_information: list[str] = []
    approved_by: Optional[str] = None
    approval_comment: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None


class DraftApproveRequest(BaseModel):
    comment: str = Field(..., min_length=3, max_length=1000)


# ---------------------------------------------------------------------------
# Task & Follow-up schemas
# ---------------------------------------------------------------------------


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    client_id: Optional[str] = None
    source_type: str = Field(default="manual", max_length=50)
    source_id: Optional[str] = None
    exception_id: Optional[str] = None
    notice_case_id: Optional[str] = None
    assigned_to: Optional[str] = None  # maps to owner_id
    due_date: Optional[date] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    status: Optional[str] = Field(default=None, max_length=50)  # open, in_progress, blocked, completed, cancelled
    assigned_to: Optional[str] = None
    due_date: Optional[date] = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    firm_id: str
    client_id: Optional[str] = None
    tenant_id: str
    source_type: str
    source_id: Optional[str] = None
    exception_id: Optional[str] = None
    notice_case_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str
    owner_id: Optional[str] = None
    due_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime


class MessageDraftRequest(BaseModel):
    channel: str = Field(default="email")  # email, whatsapp
    recipient_type: str = Field(default="vendor")  # vendor, client
    custom_instructions: Optional[str] = Field(default=None, max_length=1000)


class MessageDraftResponse(BaseModel):
    task_id: str
    channel: str
    recipient_type: str
    subject: Optional[str] = None
    message_body: str
    evidence_references: list[str] = []


# ---------------------------------------------------------------------------
# Knowledge Base schemas
# ---------------------------------------------------------------------------


class KnowledgeSourceCreate(BaseModel):
    source_type: str = Field(..., min_length=1, max_length=50)  # act, circular, faq, guidance, case_law
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)  # raw text content to ingest
    url: Optional[str] = Field(default=None, max_length=500)
    publisher: Optional[str] = Field(default=None, max_length=255)
    version: Optional[str] = Field(default=None, max_length=100)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    meta_data: Optional[dict] = None


class KnowledgeSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    source_type: str
    title: str
    url: Optional[str] = None
    publisher: Optional[str] = None
    version: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    meta_data: Optional[dict] = None
    created_at: datetime


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)


class KnowledgeSearchResponse(BaseModel):
    results: list[dict]


# ---------------------------------------------------------------------------
# Settings schemas
# ---------------------------------------------------------------------------


class SettingsRead(BaseModel):
    user_id: str
    email: str
    name: str
    theme: str  # "light", "dark", "system"
    notifications_enabled: bool
    email_notifications: bool
    created_at: datetime
    updated_at: datetime


class SettingsUpdate(BaseModel):
    theme: Optional[str] = Field(default=None, pattern="^(light|dark|system)$")
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None


# ---------------------------------------------------------------------------
# Retention & Deletion schemas
# ---------------------------------------------------------------------------


class RetentionPolicyRead(BaseModel):
    policies: dict[str, int]


class RetentionPolicyExecuteRequest(BaseModel):
    policies: Optional[dict[str, int]] = None
    dry_run: bool = True


class RetentionPolicyExecuteResponse(BaseModel):
    dry_run: bool
    results: dict[str, int]
    executed_at: datetime


class SoftDeleteRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=500)


class SoftDeleteResponse(BaseModel):
    entity_type: str
    entity_id: str
    status: str
    deleted_at: datetime


# ---------------------------------------------------------------------------
# Partner Monitoring Dashboard schemas
# ---------------------------------------------------------------------------


class DashboardTaskMetric(BaseModel):
    total_open: int = 0
    in_progress: int = 0
    blocked: int = 0
    completed: int = 0
    overdue: int = 0


class DashboardExceptionMetric(BaseModel):
    total_unresolved: int = 0
    open: int = 0
    in_review: int = 0


class DashboardNoticeMetric(BaseModel):
    total_active: int = 0
    urgent_deadlines_within_7_days: int = 0


class DashboardOperationalMetric(BaseModel):
    estimated_hours_saved: float = 0.0
    manual_overrides: int = 0
    ai_drafts_generated: int = 0

class DashboardOverviewResponse(BaseModel):
    firm_id: str
    generated_at: datetime
    tasks: DashboardTaskMetric
    exceptions: DashboardExceptionMetric
    notices: DashboardNoticeMetric
    operations: DashboardOperationalMetric = Field(default_factory=DashboardOperationalMetric)
    overdue_task_items: list[TaskRead] = []

