"""Document management service.

Orchestrates upload validation, secure storage, deduplication, parsing into
canonical transactions, evidence attachment, and audit logging.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthContext
from app.config import settings
from app.models import Client, Document, Evidence, Period, Transaction
from app.parsers.csv_parser import parse_csv_transactions
from app.parsers.json_parser import parse_gstr2b_json
from app.services import audit_service
from app.storage.backend import StorageBackend, get_storage_backend

ALLOWED_MIME_TYPES = {
    "text/csv",
    "application/json",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/plain",
}

ALLOWED_EXTENSIONS = {".csv", ".json", ".pdf", ".xlsx", ".xls", ".txt"}


def _validate_file_metadata(filename: str, mime_type: str, size_bytes: int) -> str:
    """Validate file extension, size, and mime type."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Basic MIME validation
    if mime_type not in ALLOWED_MIME_TYPES and not any(mime_type.startswith(p) for p in ["text/", "application/"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported MIME type '{mime_type}'.",
        )

    if size_bytes > settings.max_upload_size_bytes:
        max_mb = settings.max_upload_size_bytes // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {max_mb}MB.",
        )

    return ext


def list_documents(
    db: Session,
    *,
    auth: AuthContext,
    client_id: str | None = None,
    period_id: str | None = None,
    document_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Document], int]:
    """List documents for the tenant with optional filters."""
    query = db.query(Document).filter(Document.tenant_id == auth.tenant_id)

    if client_id:
        query = query.filter(Document.client_id == client_id)
    if period_id:
        query = query.filter(Document.period_id == period_id)
    if document_type:
        query = query.filter(Document.document_type == document_type)

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(Document.created_at.desc()).offset(offset).limit(page_size).all()
    return items, total


def get_document(db: Session, *, auth: AuthContext, document_id: str) -> Document:
    """Fetch single document metadata enforcing tenant isolation."""
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.tenant_id == auth.tenant_id)
        .first()
    )
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    return doc


def upload_document(
    db: Session,
    *,
    auth: AuthContext,
    client_id: str,
    period_id: str | None,
    document_type: str,
    filename: str,
    mime_type: str,
    file_obj: BinaryIO,
    storage: StorageBackend | None = None,
) -> tuple[Document, int]:
    """Handle document ingestion:

    1. Verify client & period exist and belong to this tenant.
    2. Stream file to storage and calculate SHA-256.
    3. Check duplicate content hash for the tenant.
    4. Save Document record.
    5. Parse transactions (for tabular/json documents) and save Transaction rows.
    6. Log audit event.
    """
    if storage is None:
        storage = get_storage_backend()

    # 1. Validate client
    client = (
        db.query(Client)
        .filter(Client.id == client_id, Client.tenant_id == auth.tenant_id)
        .first()
    )
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found in this tenant.",
        )

    # Validate period if provided
    if period_id:
        period = (
            db.query(Period)
            .filter(
                Period.id == period_id,
                Period.client_id == client_id,
                Period.tenant_id == auth.tenant_id,
            )
            .first()
        )
        if period is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Period not found or does not belong to this client.",
            )

    # 2. Check size and extension
    file_obj.seek(0, os.SEEK_END)
    size_bytes = file_obj.tell()
    file_obj.seek(0)

    ext = _validate_file_metadata(filename, mime_type, size_bytes)

    # 3. Store file and compute hash
    storage_uri, content_hash, written_bytes = storage.save(
        tenant_id=auth.tenant_id,
        file_obj=file_obj,
        extension=ext,
    )

    # 4. Check for duplicate content within this client/tenant (DATA_SPEC.md §4)
    existing_dup = (
        db.query(Document)
        .filter(
            Document.tenant_id == auth.tenant_id,
            Document.client_id == client_id,
            Document.content_hash == content_hash,
        )
        .first()
    )
    if existing_dup is not None:
        # Clean up newly written duplicate file
        storage.delete(storage_uri)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate document detected. Exact content previously uploaded as document '{existing_dup.id}'.",
        )

    # 5. Create Document record
    doc = Document(
        firm_id=auth.firm_id,
        client_id=client_id,
        period_id=period_id,
        tenant_id=auth.tenant_id,
        document_type=document_type,
        original_filename=filename,
        storage_uri=storage_uri,
        content_hash=content_hash,
        mime_type=mime_type,
        size_bytes=written_bytes,
        processing_status="processing",
        uploaded_by=auth.user_id,
    )
    db.add(doc)
    db.flush()

    # 6. Parse and extract canonical transactions if applicable
    extracted_count = 0
    try:
        content_bytes = storage.read(storage_uri)
        parsed_records: list[dict] = []

        if ext == ".csv":
            parsed_records = parse_csv_transactions(content_bytes)
        elif ext == ".json":
            parsed_records = parse_gstr2b_json(content_bytes)

        # Bulk insert transactions
        for rec in parsed_records:
            tx = Transaction(
                firm_id=auth.firm_id,
                client_id=client_id,
                period_id=period_id or "",  # Period can be assigned or linked
                tenant_id=auth.tenant_id,
                source_document_id=doc.id,
                source_row_reference=rec.get("source_row_reference"),
                supplier_gstin=rec.get("supplier_gstin"),
                invoice_number_raw=rec.get("invoice_number_raw"),
                invoice_number_normalized=rec.get("invoice_number_normalized"),
                invoice_date=rec.get("invoice_date"),
                taxable_value=rec.get("taxable_value"),
                cgst=rec.get("cgst"),
                sgst=rec.get("sgst"),
                igst=rec.get("igst"),
                cess=rec.get("cess"),
                currency=rec.get("currency", "INR"),
            )
            db.add(tx)
            extracted_count += 1

        doc.processing_status = "processed"
        doc.processed_at = datetime.now(timezone.utc)
    except Exception as exc:
        # Mark as failed but preserve document record for audit investigation
        doc.processing_status = "failed"
        audit_service.log_event(
            db,
            auth=auth,
            entity_type="document",
            entity_id=doc.id,
            event_type="document.processing_failed",
            payload={"error": str(exc), "filename": filename},
        )
        db.commit()
        db.refresh(doc)
        return doc, 0

    # 7. Audit log
    audit_service.log_event(
        db,
        auth=auth,
        entity_type="document",
        entity_id=doc.id,
        event_type="document.uploaded",
        payload={
            "filename": filename,
            "size_bytes": written_bytes,
            "content_hash": content_hash,
            "document_type": document_type,
            "extracted_transactions": extracted_count,
        },
    )

    db.commit()
    db.refresh(doc)
    return doc, extracted_count


def list_document_transactions(
    db: Session,
    *,
    auth: AuthContext,
    document_id: str,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Transaction], int]:
    """Return paginated normalized transactions for a document."""
    # Ensure document exists and belongs to tenant
    get_document(db, auth=auth, document_id=document_id)

    query = (
        db.query(Transaction)
        .filter(
            Transaction.source_document_id == document_id,
            Transaction.tenant_id == auth.tenant_id,
        )
        .order_by(Transaction.created_at.asc())
    )
    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    return items, total
