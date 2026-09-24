"""Firm management service.

Handles firm CRUD with tenant enforcement. The firm's ``id`` is its
``tenant_id`` — this is the root of the tenant boundary.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthContext
from app.models import Firm, FirmMembership, User
from app.schemas import FirmCreate, FirmUpdate
from app.services import audit_service


def get_firm(db: Session, *, auth: AuthContext) -> Firm:
    """Return the firm for the current auth context.

    Enforces that the user can only access their own firm.
    """
    firm = db.get(Firm, auth.firm_id)
    if firm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Firm not found.",
        )
    return firm


def create_firm(db: Session, *, auth: AuthContext, payload: FirmCreate) -> Firm:
    """Create a new firm and set the creating user as owner.

    The firm ID is set to the tenant_id from auth context, establishing
    the tenant boundary.
    """
    # Check if firm already exists for this tenant.
    existing = db.get(Firm, auth.firm_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Firm already exists for this tenant.",
        )

    firm = Firm(
        id=auth.firm_id,
        name=payload.name,
        status=payload.status,
        plan=payload.plan,
    )
    db.add(firm)

    # Ensure the creating user exists.
    user = db.get(User, auth.user_id)
    if user is None:
        user = User(
            id=auth.user_id,
            email=f"{auth.user_id}@placeholder.local",
            name="System User",
            status="active",
        )
        db.add(user)

    # Create owner membership.
    membership = FirmMembership(
        firm_id=firm.id,
        user_id=auth.user_id,
        role="owner",
    )
    db.add(membership)

    audit_service.log_event(
        db,
        auth=auth,
        entity_type="firm",
        entity_id=firm.id,
        event_type="firm.created",
        payload={"name": payload.name},
    )

    db.commit()
    db.refresh(firm)
    return firm


def update_firm(db: Session, *, auth: AuthContext, payload: FirmUpdate) -> Firm:
    """Update permitted firm settings."""
    firm = get_firm(db, auth=auth)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return firm

    for field, value in update_data.items():
        setattr(firm, field, value)

    audit_service.log_event(
        db,
        auth=auth,
        entity_type="firm",
        entity_id=firm.id,
        event_type="firm.updated",
        payload=update_data,
    )

    db.commit()
    db.refresh(firm)
    return firm


def list_members(db: Session, *, auth: AuthContext) -> list[FirmMembership]:
    """List all memberships for the authenticated firm."""
    return (
        db.query(FirmMembership)
        .filter(FirmMembership.firm_id == auth.firm_id)
        .all()
    )


def add_member(
    db: Session,
    *,
    auth: AuthContext,
    user_id: str,
    role: str = "staff",
) -> FirmMembership:
    """Add a user to the firm with the given role."""
    # Check if membership already exists.
    existing = (
        db.query(FirmMembership)
        .filter(
            FirmMembership.firm_id == auth.firm_id,
            FirmMembership.user_id == user_id,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this firm.",
        )

    membership = FirmMembership(
        firm_id=auth.firm_id,
        user_id=user_id,
        role=role,
    )
    db.add(membership)

    audit_service.log_event(
        db,
        auth=auth,
        entity_type="firm_membership",
        entity_id=f"{auth.firm_id}:{user_id}",
        event_type="member.added",
        payload={"user_id": user_id, "role": role},
    )

    db.commit()
    db.refresh(membership)
    return membership
