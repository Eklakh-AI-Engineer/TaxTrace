"""Notice management API routes.

Per API_SPEC.md §9:
    POST /api/v1/notices
    GET  /api/v1/notices/{notice_case_id}
    POST /api/v1/notices/{notice_case_id}/extract
    POST /api/v1/notices/{notice_case_id}/draft
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.database import get_db
from app.permissions import Role, require_role
from app.schemas import (
    DraftCreateRequest,
    DraftRead,
    NoticeCaseRead,
    NoticeExtractionResponse,
)
from app.services import document_service, notice_service

router = APIRouter(prefix="/api/v1", tags=["notices"])


@router.post(
    "/notices",
    response_model=NoticeCaseRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(Role.STAFF))],
)
async def upload_notice(
    client_id: str = Form(...),
    period_id: str | None = Form(default=None),
    file: UploadFile = Form(...),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> NoticeCaseRead:
    """Upload a tax notice file (PDF/Text) and initialize a NoticeCase."""
    filename = file.filename or "notice.pdf"
    mime_type = file.content_type or "application/pdf"

    # Save document first in the Evidence Vault
    doc, _ = document_service.upload_document(
        db,
        auth=auth,
        client_id=client_id,
        period_id=period_id,
        document_type="notice_pdf",
        filename=filename,
        mime_type=mime_type,
        file_obj=file.file,
    )

    notice = notice_service.create_notice_case(
        db,
        auth=auth,
        client_id=client_id,
        period_id=period_id,
        document_id=doc.id,
        notice_type="OTHER",
    )
    return NoticeCaseRead.model_validate(notice)


@router.get("/notices/{notice_case_id}", response_model=NoticeCaseRead)
def get_notice_case(
    notice_case_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> NoticeCaseRead:
    """Get metadata for a notice case."""
    notice = notice_service.get_notice_case(db, auth=auth, notice_case_id=notice_case_id)
    return NoticeCaseRead.model_validate(notice)


@router.post("/notices/{notice_case_id}/extract", response_model=NoticeExtractionResponse)
def extract_notice_facts(
    notice_case_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> NoticeExtractionResponse:
    """Extract structured facts (GSTIN, dates, sections, amounts) from the notice."""
    return notice_service.extract_notice_facts(
        db, auth=auth, notice_case_id=notice_case_id
    )


@router.post("/notices/{notice_case_id}/draft", response_model=DraftRead)
def generate_notice_draft(
    notice_case_id: str,
    payload: DraftCreateRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> DraftRead:
    """Generate an evidence-grounded preliminary reply draft for a notice."""
    return notice_service.generate_notice_draft(
        db, auth=auth, notice_case_id=notice_case_id, payload=payload
    )
