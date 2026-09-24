"""Task management service.

Implements PRD §5 Follow-up, DATA_SPEC §14 Task, API_SPEC §11 Tasks, and SECURITY.md §3 Tenant Isolation.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthContext
from app.models import Client, ExceptionRecord, FirmMembership, NoticeCase, Task
from app.schemas import TaskCreate, TaskUpdate
from app.services import audit_service


ALLOWED_TASK_STATUSES = {"open", "in_progress", "blocked", "completed", "cancelled"}


def create_task(
    db: Session,
    *,
    auth: AuthContext,
    payload: TaskCreate,
) -> Task:
    """Create a new operational or follow-up task with tenant validation.

    Ensures that:
    1. Assigned owner (if provided) is an active member of the current firm.
    2. Linked client, exception, or notice (if provided) belongs to the authenticated tenant.
    """
    # 1. Validate assigned user belongs to this firm
    if payload.assigned_to:
        membership = (
            db.query(FirmMembership)
            .filter(
                FirmMembership.firm_id == auth.firm_id,
                FirmMembership.user_id == payload.assigned_to,
            )
            .first()
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Assigned user '{payload.assigned_to}' is not a member of this firm.",
            )

    # 2. Validate client if specified
    if payload.client_id:
        client = (
            db.query(Client)
            .filter(
                Client.id == payload.client_id,
                Client.tenant_id == auth.tenant_id,
            )
            .first()
        )
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Linked client not found in current tenant.",
            )

    # 3. Validate exception if specified
    if payload.exception_id:
        exc = (
            db.query(ExceptionRecord)
            .filter(
                ExceptionRecord.id == payload.exception_id,
                ExceptionRecord.tenant_id == auth.tenant_id,
            )
            .first()
        )
        if not exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Linked exception record not found in current tenant.",
            )

    # 4. Validate notice case if specified
    if payload.notice_case_id:
        notice = (
            db.query(NoticeCase)
            .filter(
                NoticeCase.id == payload.notice_case_id,
                NoticeCase.tenant_id == auth.tenant_id,
            )
            .first()
        )
        if not notice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Linked notice case not found in current tenant.",
            )

    task = Task(
        firm_id=auth.firm_id,
        tenant_id=auth.tenant_id,
        client_id=payload.client_id,
        source_type=payload.source_type,
        source_id=payload.source_id,
        exception_id=payload.exception_id,
        notice_case_id=payload.notice_case_id,
        title=payload.title,
        description=payload.description,
        status="open",
        owner_id=payload.assigned_to,
        due_date=payload.due_date,
    )
    db.add(task)
    db.flush()

    audit_service.log_event(
        db,
        auth=auth,
        entity_type="task",
        entity_id=task.id,
        event_type="TASK_CREATED",
        payload={
            "title": task.title,
            "status": task.status,
            "owner_id": task.owner_id,
            "client_id": task.client_id,
            "exception_id": task.exception_id,
            "notice_case_id": task.notice_case_id,
            "due_date": task.due_date.isoformat() if task.due_date else None,
        },
    )
    db.commit()
    db.refresh(task)
    return task


def get_task(
    db: Session,
    *,
    auth: AuthContext,
    task_id: str,
) -> Task:
    """Retrieve a single task strictly scoped to the caller's tenant."""
    task = (
        db.query(Task)
        .filter(
            Task.id == task_id,
            Task.tenant_id == auth.tenant_id,
        )
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )
    return task


def list_tasks(
    db: Session,
    *,
    auth: AuthContext,
    status_filter: str | None = None,
    client_id: str | None = None,
    assigned_to: str | None = None,
    overdue_only: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Task], int]:
    """Retrieve paginated tasks strictly scoped to the tenant with flexible filtering."""
    query = db.query(Task).filter(Task.tenant_id == auth.tenant_id)

    if status_filter:
        query = query.filter(Task.status == status_filter)
    if client_id:
        query = query.filter(Task.client_id == client_id)
    if assigned_to:
        query = query.filter(Task.owner_id == assigned_to)
    if overdue_only:
        today = date.today()
        query = query.filter(
            Task.due_date < today,
            Task.status.in_(["open", "in_progress", "blocked"]),
        )

    total = query.count()
    items = (
        query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def update_task(
    db: Session,
    *,
    auth: AuthContext,
    task_id: str,
    payload: TaskUpdate,
) -> Task:
    """Update task details with tenant isolation and audit logging."""
    task = get_task(db, auth=auth, task_id=task_id)

    changes: dict[str, dict[str, str | None]] = {}

    if payload.title is not None and payload.title != task.title:
        changes["title"] = {"old": task.title, "new": payload.title}
        task.title = payload.title

    if payload.description is not None:
        task.description = payload.description

    if payload.status is not None:
        if payload.status not in ALLOWED_TASK_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid task status '{payload.status}'. Allowed: {sorted(ALLOWED_TASK_STATUSES)}",
            )
        if payload.status != task.status:
            changes["status"] = {"old": task.status, "new": payload.status}
            task.status = payload.status

    if payload.assigned_to is not None and payload.assigned_to != task.owner_id:
        # Validate that the new assignee is a member of this firm
        membership = (
            db.query(FirmMembership)
            .filter(
                FirmMembership.firm_id == auth.firm_id,
                FirmMembership.user_id == payload.assigned_to,
            )
            .first()
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Assigned user '{payload.assigned_to}' is not a member of this firm.",
            )
        changes["assigned_to"] = {"old": task.owner_id, "new": payload.assigned_to}
        task.owner_id = payload.assigned_to

    if payload.due_date is not None and payload.due_date != task.due_date:
        changes["due_date"] = {
            "old": task.due_date.isoformat() if task.due_date else None,
            "new": payload.due_date.isoformat(),
        }
        task.due_date = payload.due_date

    task.updated_at = datetime.now(timezone.utc)

    if changes:
        audit_service.log_event(
            db,
            auth=auth,
            entity_type="task",
            entity_id=task.id,
            event_type="TASK_UPDATED",
            payload={"changes": changes},
        )

    db.commit()
    db.refresh(task)
    return task


def delete_task(
    db: Session,
    *,
    auth: AuthContext,
    task_id: str,
) -> None:
    """Delete a task strictly scoped to the tenant with audit logging."""
    task = get_task(db, auth=auth, task_id=task_id)

    audit_service.log_event(
        db,
        auth=auth,
        entity_type="task",
        entity_id=task.id,
        event_type="TASK_DELETED",
        payload={"title": task.title, "status": task.status},
    )

    db.delete(task)
    db.commit()
