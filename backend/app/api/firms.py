"""Firm management API routes.

Endpoints:
    GET   /api/v1/firms/me     — current firm context
    POST  /api/v1/firms        — create firm
    PATCH /api/v1/firms/me     — update firm settings
    GET   /api/v1/firms/me/members — list firm members
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.database import get_db
from app.permissions import Role, require_role
from app.schemas import FirmCreate, FirmRead, FirmUpdate, MembershipRead
from app.services import firm_service

router = APIRouter(prefix="/api/v1", tags=["firms"])


@router.get("/firms/me", response_model=FirmRead)
def get_current_firm(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> FirmRead:
    """Return the firm for the currently authenticated user."""
    firm = firm_service.get_firm(db, auth=auth)
    return FirmRead.model_validate(firm)


@router.post("/firms", response_model=FirmRead, status_code=201)
def create_firm(
    payload: FirmCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> FirmRead:
    """Create a new firm. The authenticated user becomes the owner."""
    firm = firm_service.create_firm(db, auth=auth, payload=payload)
    return FirmRead.model_validate(firm)


@router.patch("/firms/me", response_model=FirmRead)
def update_firm(
    payload: FirmUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_role(Role.OWNER)),
) -> FirmRead:
    """Update firm settings. Requires owner role."""
    firm = firm_service.update_firm(db, auth=auth, payload=payload)
    return FirmRead.model_validate(firm)


@router.get("/firms/me/members", response_model=list[MembershipRead])
def list_members(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> list[MembershipRead]:
    """List all members of the current firm."""
    members = firm_service.list_members(db, auth=auth)
    return [MembershipRead.model_validate(m) for m in members]
