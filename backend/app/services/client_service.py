"""Client management service.

All queries are scoped to the authenticated tenant. Every mutation
creates an audit event.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthContext
from app.models import Client
from app.schemas import ClientCreate, ClientUpdate
from app.services import audit_service


def _tenant_clients(db: Session, tenant_id: str):
    """Base query filtered by tenant."""
    return db.query(Client).filter(Client.tenant_id == tenant_id)


def list_clients(
    db: Session,
    *,
    auth: AuthContext,
    status_filter: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Client], int]:
    """Return paginated clients for the tenant.

    Returns (items, total_count).
    """
    query = _tenant_clients(db, auth.tenant_id)

    if status_filter:
        query = query.filter(Client.status == status_filter)

    if search:
        like = f"%{search}%"
        query = query.filter(
            Client.display_name.ilike(like)
            | Client.gstin.ilike(like)
        )

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(Client.created_at.desc()).offset(offset).limit(page_size).all()
    return items, total


def get_client(db: Session, *, auth: AuthContext, client_id: str) -> Client:
    """Fetch a single client, enforcing tenant scope."""
    client = (
        _tenant_clients(db, auth.tenant_id)
        .filter(Client.id == client_id)
        .first()
    )
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found.",
        )
    return client


def create_client(
    db: Session,
    *,
    auth: AuthContext,
    payload: ClientCreate,
) -> Client:
    """Create a new client under the authenticated firm/tenant."""
    client = Client(
        firm_id=auth.firm_id,
        tenant_id=auth.tenant_id,
        display_name=payload.display_name,
        gstin=payload.gstin,
        pan_reference=payload.pan_reference,
        status=payload.status,
    )
    db.add(client)
    db.flush()

    audit_service.log_event(
        db,
        auth=auth,
        entity_type="client",
        entity_id=client.id,
        event_type="client.created",
        payload={"display_name": payload.display_name, "gstin": payload.gstin},
    )

    db.commit()
    db.refresh(client)
    return client


def update_client(
    db: Session,
    *,
    auth: AuthContext,
    client_id: str,
    payload: ClientUpdate,
) -> Client:
    """Update a client's mutable fields."""
    client = get_client(db, auth=auth, client_id=client_id)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return client

    for field, value in update_data.items():
        setattr(client, field, value)

    audit_service.log_event(
        db,
        auth=auth,
        entity_type="client",
        entity_id=client.id,
        event_type="client.updated",
        payload=update_data,
    )

    db.commit()
    db.refresh(client)
    return client
