"""Tasks API routes.

Per API_SPEC.md §11:
    POST   /api/v1/tasks
    GET    /api/v1/tasks
    GET    /api/v1/tasks/{task_id}
    PATCH  /api/v1/tasks/{task_id}
    DELETE /api/v1/tasks/{task_id}
    POST   /api/v1/tasks/{task_id}/draft-message
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.database import get_db
from app.permissions import Role, require_role
from app.schemas import (
    MessageDraftRequest,
    MessageDraftResponse,
    PaginatedResponse,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)
from app.services import communication_service, task_service

router = APIRouter(prefix="/api/v1", tags=["tasks"])


@router.post(
    "/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(Role.STAFF))],
)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> TaskRead:
    """Create a new task or follow-up item. Requires staff or higher."""
    task = task_service.create_task(db, auth=auth, payload=payload)
    return TaskRead.model_validate(task)


@router.get("/tasks", response_model=PaginatedResponse[TaskRead])
def list_tasks(
    status: str | None = Query(default=None),
    client_id: str | None = Query(default=None),
    assigned_to: str | None = Query(default=None),
    overdue_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> PaginatedResponse[TaskRead]:
    """Retrieve filtered, paginated tasks for the authenticated firm."""
    items, total = task_service.list_tasks(
        db,
        auth=auth,
        status_filter=status,
        client_id=client_id,
        assigned_to=assigned_to,
        overdue_only=overdue_only,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[TaskRead.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> TaskRead:
    """Retrieve details for a single task."""
    task = task_service.get_task(db, auth=auth, task_id=task_id)
    return TaskRead.model_validate(task)


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskRead,
    dependencies=[Depends(require_role(Role.STAFF))],
)
def update_task(
    task_id: str,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> TaskRead:
    """Update task status, assignee, or metadata. Requires staff or higher."""
    task = task_service.update_task(db, auth=auth, task_id=task_id, payload=payload)
    return TaskRead.model_validate(task)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(Role.SENIOR))],
)
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> None:
    """Delete a task. Requires senior role or higher."""
    task_service.delete_task(db, auth=auth, task_id=task_id)


@router.post(
    "/tasks/{task_id}/draft-message",
    response_model=MessageDraftResponse,
    dependencies=[Depends(require_role(Role.STAFF))],
)
def draft_follow_up_message(
    task_id: str,
    payload: MessageDraftRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> MessageDraftResponse:
    """Generate a polite, evidence-grounded follow-up draft to vendor/client."""
    return communication_service.draft_follow_up_message(
        db,
        auth=auth,
        task_id=task_id,
        payload=payload,
    )
