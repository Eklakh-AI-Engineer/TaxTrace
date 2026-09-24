"""Exception management API routes.

Per API_SPEC.md §7:
    GET   /api/v1/exceptions/{exception_id}
    PATCH /api/v1/exceptions/{exception_id}
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.database import get_db
from app.schemas import (
    AIExplanationRequest,
    AIExplanationResponse,
    EvidenceRead,
    ExceptionDecisionRequest,
    ExceptionDetailRead,
    ExceptionUpdate,
)
from app.services import ai_service, reconciliation_service

router = APIRouter(prefix="/api/v1", tags=["exceptions"])


@router.get("/exceptions/{exception_id}", response_model=ExceptionDetailRead)
def get_exception_detail(
    exception_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> ExceptionDetailRead:
    """Retrieve an exception and all attached provenance evidence records."""
    exc, evidence_list = reconciliation_service.get_exception_detail(
        db,
        auth=auth,
        exception_id=exception_id,
    )
    detail = ExceptionDetailRead.model_validate(exc)
    detail.evidence = [EvidenceRead.model_validate(ev) for ev in evidence_list]
    return detail


@router.patch("/exceptions/{exception_id}", response_model=ExceptionDetailRead)
def update_exception(
    exception_id: str,
    payload: ExceptionUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> ExceptionDetailRead:
    """Update status, explanation, or assignment of an exception."""
    exc, evidence_list = reconciliation_service.update_exception(
        db,
        auth=auth,
        exception_id=exception_id,
        payload=payload,
    )
    detail = ExceptionDetailRead.model_validate(exc)
    detail.evidence = [EvidenceRead.model_validate(ev) for ev in evidence_list]
    return detail


@router.post("/exceptions/{exception_id}/decision", response_model=ExceptionDetailRead)
def record_exception_decision(
    exception_id: str,
    payload: ExceptionDecisionRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> ExceptionDetailRead:
    """Record an explicit human decision on an exception (accepted, rejected, resolved, needs_info)."""
    exc = ai_service.record_exception_decision(
        db, auth=auth, exception_id=exception_id, payload=payload
    )
    _, evidence_list = reconciliation_service.get_exception_detail(
        db, auth=auth, exception_id=exception_id
    )
    detail = ExceptionDetailRead.model_validate(exc)
    detail.evidence = [EvidenceRead.model_validate(ev) for ev in evidence_list]
    return detail


@router.post("/exceptions/{exception_id}/explanation", response_model=AIExplanationResponse)
def explain_exception(
    exception_id: str,
    payload: AIExplanationRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> AIExplanationResponse:
    """Generate an evidence-grounded AI explanation for an exception."""
    return ai_service.explain_exception(
        db, auth=auth, exception_id=exception_id, payload=payload
    )

