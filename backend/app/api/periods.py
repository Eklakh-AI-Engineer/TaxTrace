"""Period management API routes.

Endpoints:
    GET   /api/v1/periods              — list periods (paginated, filterable by client)
    POST  /api/v1/periods              — create period
    GET   /api/v1/periods/{period_id}  — get period detail
    PATCH /api/v1/periods/{period_id}  — update period (status change)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.database import get_db
from app.schemas import PaginatedResponse, PeriodCreate, PeriodRead, PeriodUpdate
from app.services import period_service

router = APIRouter(prefix="/api/v1", tags=["periods"])


@router.get("/periods", response_model=PaginatedResponse[PeriodRead])
def list_periods(
    client_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> PaginatedResponse[PeriodRead]:
    """List periods for the current firm, optionally filtered by client."""
    items, total = period_service.list_periods(
        db,
        auth=auth,
        client_id=client_id,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[PeriodRead.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.post("/periods", response_model=PeriodRead, status_code=201)
def create_period(
    payload: PeriodCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> PeriodRead:
    """Create a new compliance period for a client."""
    period = period_service.create_period(db, auth=auth, payload=payload)
    return PeriodRead.model_validate(period)


@router.get("/periods/{period_id}", response_model=PeriodRead)
def get_period(
    period_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> PeriodRead:
    """Get period detail by ID (tenant-scoped)."""
    period = period_service.get_period(db, auth=auth, period_id=period_id)
    return PeriodRead.model_validate(period)


@router.patch("/periods/{period_id}", response_model=PeriodRead)
def update_period(
    period_id: str,
    payload: PeriodUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> PeriodRead:
    """Update a period's status."""
    period = period_service.update_period(
        db, auth=auth, period_id=period_id, payload=payload,
    )
    return PeriodRead.model_validate(period)
