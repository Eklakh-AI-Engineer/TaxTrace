"""User / self API routes.

Endpoints:
    GET /api/v1/users/me — current user identity and role
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import AuthContext, get_auth_context

router = APIRouter(prefix="/api/v1", tags=["users"])


@router.get("/users/me")
def get_current_user(
    auth: AuthContext = Depends(get_auth_context),
) -> dict:
    """Return identity and role of the currently authenticated user."""
    return {
        "user_id": auth.user_id,
        "firm_id": auth.firm_id,
        "role": auth.role,
        "tenant_id": auth.tenant_id,
    }
