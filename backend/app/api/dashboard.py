"""Partner Monitoring Dashboard API routes.

Provides CA Partners and Seniors with oversight over overdue items,
pending exception reviews, and upcoming statutory notice deadlines.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.database import get_db
from app.permissions import Role, require_role
from app.schemas import DashboardOverviewResponse
from app.services import dashboard_service

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get(
    "/overview",
    response_model=DashboardOverviewResponse,
    dependencies=[Depends(require_role(Role.SENIOR))],
)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> DashboardOverviewResponse:
    """Return high-level operational metrics and overdue items for Partners/Seniors."""
    return dashboard_service.get_dashboard_overview(db, auth=auth)
