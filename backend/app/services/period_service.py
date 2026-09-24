"""Period management service.

Periods represent compliance/tax periods for a client. All queries
are tenant-scoped and every mutation creates an audit event.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthContext
from app.models import Client, Period
from app.schemas import PeriodCreate, PeriodUpdate
from app.services import audit_service


def _tenant_periods(db: Session, tenant_id: str):
    """Base query filtered by tenant."""
    return db.query(Period).filter(Period.tenant_id == tenant_id)


def list_periods(
    db: Session,
    *,
    auth: AuthContext,
    client_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Period], int]:
    """Return paginated periods, optionally filtered by client."""
    query = _tenant_periods(db, auth.tenant_id)

    if client_id:
        query = query.filter(Period.client_id == client_id)

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(Period.created_at.desc()).offset(offset).limit(page_size).all()
    return items, total


def get_period(db: Session, *, auth: AuthContext, period_id: str) -> Period:
    """Fetch a single period, enforcing tenant scope."""
    period = (
        _tenant_periods(db, auth.tenant_id)
        .filter(Period.id == period_id)
        .first()
    )
    if period is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Period not found.",
        )
    return period


def create_period(
    db: Session,
    *,
    auth: AuthContext,
    payload: PeriodCreate,
) -> Period:
    """Create a new compliance period for a client.

    Validates that the client exists and belongs to the same tenant.
    """
    # Verify client belongs to tenant.
    client = (
        db.query(Client)
        .filter(Client.id == payload.client_id, Client.tenant_id == auth.tenant_id)
        .first()
    )
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found in this tenant.",
        )

    # Check for duplicate active period.
    existing = (
        _tenant_periods(db, auth.tenant_id)
        .filter(
            Period.client_id == payload.client_id,
            Period.financial_year == payload.financial_year,
            Period.tax_period == payload.tax_period,
            Period.status != "closed",
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active period already exists for this client, financial year and tax period.",
        )

    period = Period(
        firm_id=auth.firm_id,
        client_id=payload.client_id,
        tenant_id=auth.tenant_id,
        financial_year=payload.financial_year,
        tax_period=payload.tax_period,
        status=payload.status,
    )
    db.add(period)
    db.flush()

    audit_service.log_event(
        db,
        auth=auth,
        entity_type="period",
        entity_id=period.id,
        event_type="period.created",
        payload={
            "client_id": payload.client_id,
            "financial_year": payload.financial_year,
            "tax_period": payload.tax_period,
        },
    )

    db.commit()
    db.refresh(period)
    return period


def update_period(
    db: Session,
    *,
    auth: AuthContext,
    period_id: str,
    payload: PeriodUpdate,
) -> Period:
    """Update a period's status."""
    period = get_period(db, auth=auth, period_id=period_id)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return period

    for field, value in update_data.items():
        setattr(period, field, value)

    audit_service.log_event(
        db,
        auth=auth,
        entity_type="period",
        entity_id=period.id,
        event_type="period.updated",
        payload=update_data,
    )

    db.commit()
    db.refresh(period)
    return period
