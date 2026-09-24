"""Role-based permission enforcement.

Roles follow SECURITY.md Section 5:
    Owner > Partner > Senior > Staff > Viewer

Each role inherits permissions from roles below it. Permission checks
use a hierarchy comparison so ``require_role(Role.SENIOR)`` permits
owners, partners, and seniors but denies staff and viewers.
"""

from __future__ import annotations

from enum import Enum
from functools import wraps
from typing import Callable

from fastapi import Depends, HTTPException, status

from app.auth import AuthContext, get_auth_context


class Role(str, Enum):
    """Firm membership roles in descending authority."""

    OWNER = "owner"
    PARTNER = "partner"
    SENIOR = "senior"
    STAFF = "staff"
    VIEWER = "viewer"


# Lower number = higher authority.
_ROLE_HIERARCHY: dict[str, int] = {
    Role.OWNER: 0,
    Role.PARTNER: 1,
    Role.SENIOR: 2,
    Role.STAFF: 3,
    Role.VIEWER: 4,
}


def _role_level(role: str) -> int:
    """Return the numeric level for a role string.

    Unknown roles are treated as having no authority (level 99).
    """
    return _ROLE_HIERARCHY.get(role, 99)


def has_minimum_role(user_role: str, required_role: Role) -> bool:
    """Check whether *user_role* meets or exceeds *required_role*."""
    return _role_level(user_role) <= _role_level(required_role)


def check_permission(auth: AuthContext, required_role: Role) -> None:
    """Raise HTTP 403 if the user lacks the required role.

    Call this inside route handlers or service functions when a
    specific action needs elevated permissions (e.g. approvals).
    """
    if not has_minimum_role(auth.role, required_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This action requires at least the '{required_role.value}' role.",
        )


def require_role(minimum_role: Role) -> Callable:
    """FastAPI dependency factory that enforces a minimum role.

    Usage::

        @router.post("/firms/me", dependencies=[Depends(require_role(Role.OWNER))])
        def update_firm(...): ...

    The dependency resolves the ``AuthContext`` and verifies the role
    before the route handler executes.
    """

    def _dependency(auth: AuthContext = Depends(get_auth_context)) -> AuthContext:
        check_permission(auth, minimum_role)
        return auth

    return _dependency


# ---------------------------------------------------------------------------
# Permission constants for common actions
# ---------------------------------------------------------------------------

CAN_MANAGE_FIRM = Role.OWNER
CAN_APPROVE = Role.PARTNER
CAN_RECONCILE = Role.SENIOR
CAN_CREATE_TASK = Role.STAFF
CAN_VIEW = Role.VIEWER
