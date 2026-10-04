"""Partner Monitoring Dashboard Service.

Provides CA Partners with high-level oversight across tasks, notices, and exceptions
per PRD §4.1 (CA Partner needs), PRD §5 ("As a partner, I can see overdue items"),
and SECURITY.md §5.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.auth import AuthContext
from app.models import ExceptionRecord, NoticeCase, Task
from app.schemas import (
    DashboardExceptionMetric,
    DashboardNoticeMetric,
    DashboardOperationalMetric,
    DashboardOverviewResponse,
    DashboardTaskMetric,
    TaskRead,
)


def get_dashboard_overview(
    db: Session,
    *,
    auth: AuthContext,
) -> DashboardOverviewResponse:
    """Aggregate tenant-scoped metrics for CA Partner oversight."""
    today = date.today()
    seven_days_later = today + timedelta(days=7)

    # 1. Tasks breakdown
    all_tasks = db.query(Task).filter(Task.tenant_id == auth.tenant_id).all()
    open_count = sum(1 for t in all_tasks if t.status == "open")
    in_prog_count = sum(1 for t in all_tasks if t.status == "in_progress")
    blocked_count = sum(1 for t in all_tasks if t.status == "blocked")
    completed_count = sum(1 for t in all_tasks if t.status == "completed")

    overdue_items = [
        t
        for t in all_tasks
        if t.due_date and t.due_date < today and t.status in {"open", "in_progress", "blocked"}
    ]

    task_metrics = DashboardTaskMetric(
        total_open=open_count,
        in_progress=in_prog_count,
        blocked=blocked_count,
        completed=completed_count,
        overdue=len(overdue_items),
    )

    # 2. Exceptions breakdown
    all_exceptions = (
        db.query(ExceptionRecord)
        .filter(ExceptionRecord.tenant_id == auth.tenant_id)
        .all()
    )
    exc_open = sum(1 for e in all_exceptions if e.status == "open")
    exc_in_review = sum(1 for e in all_exceptions if e.status == "in_review")
    total_unresolved = sum(1 for e in all_exceptions if e.status not in {"resolved", "accepted"})

    exc_metrics = DashboardExceptionMetric(
        total_unresolved=total_unresolved,
        open=exc_open,
        in_review=exc_in_review,
    )

    # 3. Notices breakdown
    all_notices = (
        db.query(NoticeCase)
        .filter(NoticeCase.tenant_id == auth.tenant_id)
        .all()
    )
    active_notices = [n for n in all_notices if n.status not in {"closed", "approved"}]
    urgent_deadlines = sum(
        1
        for n in active_notices
        if n.response_deadline and today <= n.response_deadline <= seven_days_later
    )

    notice_metrics = DashboardNoticeMetric(
        total_active=len(active_notices),
        urgent_deadlines_within_7_days=urgent_deadlines,
    )

    from app.models import AuditEvent, Match
    
    # 4. Operational metrics
    ai_drafts = db.query(AuditEvent).filter(
        AuditEvent.tenant_id == auth.tenant_id,
        AuditEvent.event_type.in_(["notice_draft_generated", "exception_explanation_generated"])
    ).count()

    manual_overrides = db.query(AuditEvent).filter(
        AuditEvent.tenant_id == auth.tenant_id,
        AuditEvent.event_type == "exception_overridden"
    ).count()

    matched_txns = db.query(Match).filter(
        Match.tenant_id == auth.tenant_id,
        Match.status == "accepted"
    ).count()
    
    # Assumption: 3 minutes saved per matched transaction
    hours_saved = matched_txns * (3 / 60)
    
    ops_metrics = DashboardOperationalMetric(
        estimated_hours_saved=round(hours_saved, 1),
        manual_overrides=manual_overrides,
        ai_drafts_generated=ai_drafts
    )

    return DashboardOverviewResponse(
        firm_id=auth.firm_id,
        generated_at=datetime.now(timezone.utc),
        tasks=task_metrics,
        exceptions=exc_metrics,
        notices=notice_metrics,
        operations=ops_metrics,
        overdue_task_items=[TaskRead.model_validate(t) for t in overdue_items],
    )
