"""Settings API routes.

Provides user preferences and application settings management.

Endpoints:
    GET  /api/v1/settings         - get current user settings
    PATCH /api/v1/settings         - update user preferences
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.database import get_db
from app.schemas import SettingsRead, SettingsUpdate

router = APIRouter(prefix="/api/v1", tags=["settings"])


@router.get("/settings", response_model=SettingsRead)
def get_settings(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    """Get current user's settings and preferences."""
    from app.models import User

    user = db.query(User).filter(User.id == auth.user_id).first()
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=404, detail="User not found")

    return SettingsRead(
        user_id=user.id,
        email=user.email,
        name=user.name,
        theme=user.theme if hasattr(user, 'theme') else "system",
        notifications_enabled=user.notifications_enabled if hasattr(user, 'notifications_enabled') else True,
        email_notifications=user.email_notifications if hasattr(user, 'email_notifications') else True,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.patch("/settings", response_model=SettingsRead)
def update_settings(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    """Update user preferences."""
    from app.models import User
    from datetime import datetime, timezone

    user = db.query(User).filter(User.id == auth.user_id).first()
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=404, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)

    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    return SettingsRead(
        user_id=user.id,
        email=user.email,
        name=user.name,
        theme=user.theme if hasattr(user, 'theme') else "system",
        notifications_enabled=user.notifications_enabled if hasattr(user, 'notifications_enabled') else True,
        email_notifications=user.email_notifications if hasattr(user, 'email_notifications') else True,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )