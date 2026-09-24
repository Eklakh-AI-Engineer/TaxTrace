"""Client management API routes.

Endpoints:
    GET   /api/v1/clients              — list clients (paginated, searchable)
    POST  /api/v1/clients              — create client
    GET   /api/v1/clients/{client_id}  — get client detail
    PATCH /api/v1/clients/{client_id}  — update client
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.database import get_db
from app.schemas import ClientCreate, ClientRead, ClientUpdate, PaginatedResponse
from app.services import client_service

router = APIRouter(prefix="/api/v1", tags=["clients"])


@router.get("/clients", response_model=PaginatedResponse[ClientRead])
def list_clients(
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> PaginatedResponse[ClientRead]:
    """List clients for the current firm with optional filtering."""
    items, total = client_service.list_clients(
        db,
        auth=auth,
        status_filter=status,
        search=search,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[ClientRead.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.post("/clients", response_model=ClientRead, status_code=201)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> ClientRead:
    """Create a new client under the current firm."""
    client = client_service.create_client(db, auth=auth, payload=payload)
    return ClientRead.model_validate(client)


@router.get("/clients/{client_id}", response_model=ClientRead)
def get_client(
    client_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> ClientRead:
    """Get client detail by ID (tenant-scoped)."""
    client = client_service.get_client(db, auth=auth, client_id=client_id)
    return ClientRead.model_validate(client)


@router.patch("/clients/{client_id}", response_model=ClientRead)
def update_client(
    client_id: str,
    payload: ClientUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> ClientRead:
    """Update a client's mutable fields."""
    client = client_service.update_client(
        db, auth=auth, client_id=client_id, payload=payload,
    )
    return ClientRead.model_validate(client)
