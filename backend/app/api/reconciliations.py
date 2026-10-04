"""Reconciliation API routes.

Per API_SPEC.md §6:
    POST /api/v1/reconciliations
    GET  /api/v1/reconciliations/{period_id}
    GET  /api/v1/reconciliations/{period_id}/exceptions
    GET  /api/v1/reconciliations/{period_id}/export
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status, Response
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.database import get_db
from app.permissions import Role, require_role
from app.schemas import (
    ExceptionRead,
    PaginatedResponse,
    ReconciliationRunRequest,
    ReconciliationRunResponse,
    ReconciliationSummary,
)
from app.services import reconciliation_service

router = APIRouter(prefix="/api/v1", tags=["reconciliations"])


@router.post(
    "/reconciliations",
    response_model=ReconciliationRunResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(Role.SENIOR))],
)
def run_reconciliation(
    payload: ReconciliationRunRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> ReconciliationRunResponse:
    """Trigger a deterministic reconciliation run for a client and period."""
    return reconciliation_service.run_reconciliation(
        db,
        auth=auth,
        client_id=payload.client_id,
        period_id=payload.period_id,
        rule_version=payload.rule_version,
    )


@router.get("/reconciliations/{period_id}", response_model=ReconciliationSummary)
def get_reconciliation_summary(
    period_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> ReconciliationSummary:
    """Get reconciliation summary metrics for a compliance period."""
    return reconciliation_service.get_reconciliation_summary(
        db,
        auth=auth,
        period_id=period_id,
    )


@router.get("/reconciliations/{period_id}/exceptions", response_model=PaginatedResponse[ExceptionRead])
def list_reconciliation_exceptions(
    period_id: str,
    type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> PaginatedResponse[ExceptionRead]:
    """Retrieve filtered, paginated exception records for a period."""
    items, total = reconciliation_service.list_period_exceptions(
        db,
        auth=auth,
        period_id=period_id,
        exception_type=type,
        severity=severity,
        status_filter=status,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[ExceptionRead.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/reconciliations/{period_id}/export")
def export_reconciliation_report(
    period_id: str,
    format: str = Query(default="csv", pattern="^(csv|xlsx)$"),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> Response:
    """Export reconciliation report as CSV or XLSX."""
    csv_bytes, filename = reconciliation_service.export_reconciliation_report(
        db,
        auth=auth,
        period_id=period_id,
        format=format,
    )
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
