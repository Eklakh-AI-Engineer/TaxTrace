"""Reconciliation service.

Orchestrates multi-pass deterministic reconciliation, persists Match rows,
ExceptionRecord rows, linked Evidence artifacts, and records audit trail events.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthContext
from app.models import Client, Document, Evidence, ExceptionRecord, Match, Period, Transaction
from app.reconciliation.engine import MatchResult, ReconciliationEngine, ReconciliationSummaryStats
from app.reconciliation.rules import ExceptionSeverity, ExceptionStatus, ExceptionType, MatchStatus
from app.schemas import (
    ExceptionDetailRead,
    ExceptionRead,
    ExceptionUpdate,
    ReconciliationRunResponse,
    ReconciliationSummary,
)
from app.services import audit_service
import csv
import io
from datetime import datetime


def run_reconciliation(
    db: Session,
    *,
    auth: AuthContext,
    client_id: str,
    period_id: str,
    rule_version: str = "recon-rule-v1",
) -> ReconciliationRunResponse:
    """Run deterministic reconciliation for a client and period.

    1. Enforce tenant boundary on client and period.
    2. Retrieve transactions belonging to this period and client.
    3. Partition into Book side and Portal side.
    4. Clear any previous uncommitted / open automated matches for this period.
    5. Run ReconciliationEngine.
    6. Persist Match and ExceptionRecord rows.
    7. Generate Evidence records for all exceptions and discrepancies.
    8. Emit append-only AuditEvent.
    """
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

    # Validate period
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

    # 2. Retrieve transactions for this period and client
    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.client_id == client_id,
            Transaction.period_id == period_id,
            Transaction.tenant_id == auth.tenant_id,
        )
        .all()
    )

    if not transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transactions found for this period. Please upload Purchase Register or GSTR-2B first.",
        )

    # Get source document types to segregate Books vs Portal
    doc_ids = {tx.source_document_id for tx in transactions}
    docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
    doc_type_map = {d.id: d.document_type.lower() for d in docs}

    book_txs: list[Transaction] = []
    portal_txs: list[Transaction] = []

    for tx in transactions:
        doc_type = doc_type_map.get(tx.source_document_id, "")
        if "2b" in doc_type or "portal" in doc_type or "gstr" in doc_type:
            portal_txs.append(tx)
        else:
            book_txs.append(tx)

    # 3. Clean up existing matches/exceptions for this period to allow re-runs
    db.query(Evidence).filter(
        Evidence.tenant_id == auth.tenant_id,
        Evidence.exception_id.in_(
            db.query(ExceptionRecord.id).filter(ExceptionRecord.period_id == period_id)
        ),
    ).delete(synchronize_session=False)

    db.query(ExceptionRecord).filter(
        ExceptionRecord.tenant_id == auth.tenant_id,
        ExceptionRecord.period_id == period_id,
    ).delete(synchronize_session=False)

    db.query(Match).filter(
        Match.tenant_id == auth.tenant_id,
        Match.period_id == period_id,
    ).delete(synchronize_session=False)

    db.flush()

    # 4. Execute deterministic engine
    engine = ReconciliationEngine()
    results, stats = engine.reconcile(book_records=book_txs, portal_records=portal_txs)

    created_matches = 0
    created_exceptions = 0

    # 5. Persist Matches and Exceptions
    for r in results:
        match_obj: Match | None = None

        if r.book_tx is not None:
            match_obj = Match(
                firm_id=auth.firm_id,
                period_id=period_id,
                tenant_id=auth.tenant_id,
                book_transaction_id=r.book_tx.id,
                portal_transaction_id=r.portal_tx.id if r.portal_tx else None,
                status=r.status.value,
                match_score=r.score,
                rule_version=rule_version,
            )
            db.add(match_obj)
            db.flush()
            created_matches += 1

        # Create Exception record if not a clean 100% exact match
        if r.exception_type and r.exception_type != ExceptionType.MATCHED:
            exc_record = ExceptionRecord(
                firm_id=auth.firm_id,
                period_id=period_id,
                tenant_id=auth.tenant_id,
                match_id=match_obj.id if match_obj else None,
                type=r.exception_type.value,
                severity=r.severity.value,
                status=ExceptionStatus.OPEN.value,
                reason_code=r.reason_code,
                explanation=r.explanation,
                created_by_system=True,
            )
            db.add(exc_record)
            db.flush()
            created_exceptions += 1

            # 6. Generate linked Evidence record
            evidence_source_doc = (
                r.book_tx.source_document_id
                if r.book_tx
                else (r.portal_tx.source_document_id if r.portal_tx else None)
            )
            evidence_row_ref = (
                r.book_tx.source_row_reference
                if r.book_tx
                else (r.portal_tx.source_row_reference if r.portal_tx else None)
            )

            evidence = Evidence(
                firm_id=auth.firm_id,
                tenant_id=auth.tenant_id,
                exception_id=exc_record.id,
                evidence_type="reconciliation_diff",
                source_document_id=evidence_source_doc,
                source_row_reference=evidence_row_ref,
                source_text=r.explanation,
                meta_data=r.evidence_diff,
            )
            db.add(evidence)

    # 7. Audit log event
    audit_service.log_event(
        db,
        auth=auth,
        entity_type="reconciliation",
        entity_id=period_id,
        event_type="reconciliation.executed",
        payload={
            "client_id": client_id,
            "period_id": period_id,
            "rule_version": rule_version,
            "matched_count": stats.matched,
            "partial_count": stats.partial_match,
            "missing_in_2b_count": stats.missing_in_2b,
            "missing_in_books_count": stats.missing_in_books,
            "duplicates_count": stats.duplicates,
        },
    )

    db.commit()

    summary = ReconciliationSummary(
        matched=stats.matched,
        partial_match=stats.partial_match,
        missing_in_2b=stats.missing_in_2b,
        missing_in_books=stats.missing_in_books,
        duplicates=stats.duplicates,
        review_required=stats.review_required,
        total_exceptions=created_exceptions,
    )

    return ReconciliationRunResponse(
        period_id=period_id,
        status="completed",
        summary=summary,
        total_matches_created=created_matches,
        total_exceptions_created=created_exceptions,
    )


def get_reconciliation_summary(
    db: Session,
    *,
    auth: AuthContext,
    period_id: str,
) -> ReconciliationSummary:
    """Return summary statistics of exceptions for a given period."""
    # Ensure period belongs to tenant
    period = (
        db.query(Period)
        .filter(Period.id == period_id, Period.tenant_id == auth.tenant_id)
        .first()
    )
    if period is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Period not found in this tenant.",
        )

    # Compute live counts from DB
    exceptions = (
        db.query(ExceptionRecord)
        .filter(
            ExceptionRecord.period_id == period_id,
            ExceptionRecord.tenant_id == auth.tenant_id,
        )
        .all()
    )

    matched_count = (
        db.query(Match)
        .filter(
            Match.period_id == period_id,
            Match.tenant_id == auth.tenant_id,
            Match.status == MatchStatus.MATCHED.value,
        )
        .count()
    )

    partial_match = sum(1 for e in exceptions if e.type in ["PARTIAL_MATCH", "VALUE_MISMATCH"])
    missing_in_2b = sum(1 for e in exceptions if e.type == "MISSING_IN_2B")
    missing_in_books = sum(1 for e in exceptions if e.type == "MISSING_IN_BOOKS")
    duplicates = sum(1 for e in exceptions if e.type == "DUPLICATE")
    review_required = sum(1 for e in exceptions if e.type == "REVIEW_REQUIRED")

    return ReconciliationSummary(
        matched=matched_count,
        partial_match=partial_match,
        missing_in_2b=missing_in_2b,
        missing_in_books=missing_in_books,
        duplicates=duplicates,
        review_required=review_required,
        total_exceptions=len(exceptions),
    )


def list_period_exceptions(
    db: Session,
    *,
    auth: AuthContext,
    period_id: str,
    exception_type: str | None = None,
    severity: str | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ExceptionRecord], int]:
    """List paginated exceptions for a period with filters."""
    query = db.query(ExceptionRecord).filter(
        ExceptionRecord.period_id == period_id,
        ExceptionRecord.tenant_id == auth.tenant_id,
    )

    if exception_type:
        query = query.filter(ExceptionRecord.type == exception_type)
    if severity:
        query = query.filter(ExceptionRecord.severity == severity)
    if status_filter:
        query = query.filter(ExceptionRecord.status == status_filter)

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(ExceptionRecord.created_at.desc()).offset(offset).limit(page_size).all()
    return items, total


def get_exception_detail(
    db: Session,
    *,
    auth: AuthContext,
    exception_id: str,
) -> tuple[ExceptionRecord, list[Evidence]]:
    """Retrieve an exception record and its attached evidence items."""
    exc = (
        db.query(ExceptionRecord)
        .filter(
            ExceptionRecord.id == exception_id,
            ExceptionRecord.tenant_id == auth.tenant_id,
        )
        .first()
    )
    if exc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exception record not found.",
        )

    evidence_list = (
        db.query(Evidence)
        .filter(
            Evidence.exception_id == exception_id,
            Evidence.tenant_id == auth.tenant_id,
        )
        .all()
    )
    return exc, evidence_list


def update_exception(
    db: Session,
    *,
    auth: AuthContext,
    exception_id: str,
    payload: ExceptionUpdate,
) -> tuple[ExceptionRecord, list[Evidence]]:
    """Update status, explanation annotation, or assignment of an exception."""
    exc, evidence = get_exception_detail(db, auth=auth, exception_id=exception_id)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return exc, evidence

    for field_name, value in update_data.items():
        setattr(exc, field_name, value)

    audit_service.log_event(
        db,
        auth=auth,
        entity_type="exception",
        entity_id=exc.id,
        event_type="exception.updated",
        payload=update_data,
    )

    db.commit()
    db.refresh(exc)
    return exc, evidence


def export_reconciliation_report(
    db: Session,
    *,
    auth: AuthContext,
    period_id: str,
    format: str = "csv",
) -> tuple[bytes, str]:
    """Export reconciliation report as CSV or XLSX."""
    # Validate period belongs to tenant
    period = (
        db.query(Period)
        .filter(Period.id == period_id, Period.tenant_id == auth.tenant_id)
        .first()
    )
    if period is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Period not found in this tenant.",
        )

    # Get all exceptions for the period
    exceptions = (
        db.query(ExceptionRecord)
        .filter(
            ExceptionRecord.period_id == period_id,
            ExceptionRecord.tenant_id == auth.tenant_id,
        )
        .order_by(ExceptionRecord.created_at.asc())
        .all()
    )

    # Get matches for matched records
    matches = (
        db.query(Match)
        .filter(
            Match.period_id == period_id,
            Match.tenant_id == auth.tenant_id,
        )
        .all()
    )
    match_map = {m.id: m for m in matches}

    # Prepare CSV data
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        "Exception ID",
        "Type",
        "Severity",
        "Status",
        "Reason Code",
        "System Explanation",
        "Book Invoice Number",
        "Book Supplier GSTIN",
        "Book Taxable Value",
        "Book CGST",
        "Book SGST",
        "Book IGST",
        "Book CESS",
        "Portal Invoice Number",
        "Portal Supplier GSTIN",
        "Portal Taxable Value",
        "Portal CGST",
        "Portal SGST",
        "Portal IGST",
        "Portal CESS",
        "Match Score",
        "Match Status",
        "Rule Version",
        "Evidence References",
        "Created At",
        "Updated At",
    ])

    for exc in exceptions:
        match = match_map.get(exc.match_id) if exc.match_id else None
        book_tx = match.book_transaction if match and match.book_transaction_id else None
        portal_tx = match.portal_transaction if match and match.portal_transaction_id else None

        # Get evidence references
        evidence_list = (
            db.query(Evidence)
            .filter(
                Evidence.exception_id == exc.id,
                Evidence.tenant_id == auth.tenant_id,
            )
            .all()
        )
        evidence_refs = "; ".join([
            f"{e.evidence_type}:{e.source_row_reference or e.id}"
            for e in evidence_list
        ])

        writer.writerow([
            exc.id,
            exc.type,
            exc.severity,
            exc.status,
            exc.reason_code or "",
            exc.explanation or "",
            book_tx.invoice_number_raw if book_tx else "",
            book_tx.supplier_gstin if book_tx else "",
            str(book_tx.taxable_value) if book_tx and book_tx.taxable_value else "",
            str(book_tx.cgst) if book_tx and book_tx.cgst else "",
            str(book_tx.sgst) if book_tx and book_tx.sgst else "",
            str(book_tx.igst) if book_tx and book_tx.igst else "",
            str(book_tx.cess) if book_tx and book_tx.cess else "",
            portal_tx.invoice_number_raw if portal_tx else "",
            portal_tx.supplier_gstin if portal_tx else "",
            str(portal_tx.taxable_value) if portal_tx and portal_tx.taxable_value else "",
            str(portal_tx.cgst) if portal_tx and portal_tx.cgst else "",
            str(portal_tx.sgst) if portal_tx and portal_tx.sgst else "",
            str(portal_tx.igst) if portal_tx and portal_tx.igst else "",
            str(portal_tx.cess) if portal_tx and portal_tx.cess else "",
            str(match.match_score) if match and match.match_score else "",
            match.status if match else "",
            match.rule_version if match else "",
            evidence_refs,
            exc.created_at.isoformat() if exc.created_at else "",
            exc.updated_at.isoformat() if exc.updated_at else "",
        ])

    csv_bytes = output.getvalue().encode('utf-8')
    filename = f"reconciliation_report_{period_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return csv_bytes, filename
