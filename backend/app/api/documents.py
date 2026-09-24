"""Document API routes.

Per API_SPEC.md §5:
    POST /api/v1/documents
    GET  /api/v1/documents
    GET  /api/v1/documents/{document_id}
    GET  /api/v1/documents/{document_id}/download
    GET  /api/v1/documents/{document_id}/transactions
"""

from __future__ import annotations

import io
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.database import get_db
from app.permissions import Role, require_role
from app.schemas import (
    DocumentRead,
    DocumentUploadResponse,
    PaginatedResponse,
    TransactionRead,
)
from app.services import audit_service, document_service
from app.storage.backend import get_storage_backend

router = APIRouter(prefix="/api/v1", tags=["documents"])


@router.post(
    "/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(Role.STAFF))],
)
async def upload_document(
    client_id: str = Form(...),
    period_id: str | None = Form(default=None),
    document_type: str = Form(...),
    file: UploadFile = Form(...),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> DocumentUploadResponse:
    """Upload a compliance or evidence document (Purchase Register, GSTR-2B, Notice PDF)."""
    filename = file.filename or "unknown_upload"
    mime_type = file.content_type or "application/octet-stream"

    doc, count = document_service.upload_document(
        db,
        auth=auth,
        client_id=client_id,
        period_id=period_id,
        document_type=document_type,
        filename=filename,
        mime_type=mime_type,
        file_obj=file.file,
    )

    return DocumentUploadResponse(
        document_id=doc.id,
        status=doc.processing_status,
        content_hash=doc.content_hash,
        original_filename=doc.original_filename,
        extracted_transactions_count=count,
    )


@router.get("/documents", response_model=PaginatedResponse[DocumentRead])
def list_documents(
    client_id: str | None = Query(default=None),
    period_id: str | None = Query(default=None),
    document_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> PaginatedResponse[DocumentRead]:
    """List documents for the current tenant."""
    items, total = document_service.list_documents(
        db,
        auth=auth,
        client_id=client_id,
        period_id=period_id,
        document_type=document_type,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[DocumentRead.model_validate(d) for d in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/documents/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> DocumentRead:
    """Get metadata and processing state of a document."""
    doc = document_service.get_document(db, auth=auth, document_id=document_id)
    return DocumentRead.model_validate(doc)


@router.get("/documents/{document_id}/download")
def download_document(
    document_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    """Download stored document file with audit trail verification."""
    doc = document_service.get_document(db, auth=auth, document_id=document_id)
    storage = get_storage_backend()

    if not storage.exists(doc.storage_uri):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Underlying file not found in storage.",
        )

    # Log download event in audit trail
    audit_service.log_event(
        db,
        auth=auth,
        entity_type="document",
        entity_id=doc.id,
        event_type="document.downloaded",
        payload={"filename": doc.original_filename},
    )
    db.commit()

    safe_filename = quote(doc.original_filename)
    return StreamingResponse(
        storage.stream(doc.storage_uri),
        media_type=doc.mime_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"},
    )


@router.get("/documents/{document_id}/transactions", response_model=PaginatedResponse[TransactionRead])
def list_document_transactions(
    document_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> PaginatedResponse[TransactionRead]:
    """Retrieve normalized canonical transactions extracted from this document."""
    items, total = document_service.list_document_transactions(
        db,
        auth=auth,
        document_id=document_id,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[TransactionRead.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )
