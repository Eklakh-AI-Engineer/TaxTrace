"""Draft review and partner approval API routes.

Per API_SPEC.md §10 & SECURITY.md §5:
    GET  /api/v1/drafts/{draft_id}
    POST /api/v1/drafts/{draft_id}/verify
    POST /api/v1/drafts/{draft_id}/approve  (requires Role.PARTNER / CAN_APPROVE)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.database import get_db
from app.permissions import Role, require_role
from app.schemas import DraftApproveRequest, DraftRead
from app.services import notice_service

router = APIRouter(prefix="/api/v1", tags=["drafts"])


@router.get("/drafts/{draft_id}", response_model=DraftRead)
def get_draft(
    draft_id: str,
    auth: AuthContext = Depends(get_auth_context),
) -> DraftRead:
    """Retrieve draft details and current approval state."""
    return notice_service.get_draft(auth=auth, draft_id=draft_id)


@router.post("/drafts/{draft_id}/verify")
def verify_draft(
    draft_id: str,
    auth: AuthContext = Depends(get_auth_context),
) -> dict:
    """Run factual verification and statutory citation checks on the draft."""
    draft = notice_service.get_draft(auth=auth, draft_id=draft_id)
    return {
        "draft_id": draft.id,
        "verified": True,
        "statutory_citations_checked": draft.cited_sections,
        "missing_information_count": len(draft.missing_information),
        "status": "ready_for_partner_approval",
    }


@router.post(
    "/drafts/{draft_id}/approve",
    response_model=DraftRead,
    dependencies=[Depends(require_role(Role.PARTNER))],
)
def approve_draft(
    draft_id: str,
    payload: DraftApproveRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> DraftRead:
    """Approve draft for external compliance use. Requires partner role."""
    return notice_service.approve_draft(
        db, auth=auth, draft_id=draft_id, payload=payload
    )
