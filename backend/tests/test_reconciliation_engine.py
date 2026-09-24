"""Unit tests for the deterministic reconciliation engine.

Tests:
- Exact matching on GSTIN, normalized invoice, and tax values within tolerance.
- Value mismatch and partial component matching.
- Controlled fuzzy candidate matching.
- Duplicate invoice detection on book side.
- Unmatched invoice detection (MISSING_IN_2B, MISSING_IN_BOOKS).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.models import Transaction
from app.reconciliation.engine import ReconciliationEngine
from app.reconciliation.rules import ExceptionType, MatchStatus


def _create_mock_tx(
    tx_id: str,
    invoice_raw: str,
    invoice_norm: str,
    gstin: str,
    taxable: float,
    cgst: float,
    sgst: float,
    igst: float = 0.0,
    source_doc: str = "doc_1",
) -> Transaction:
    tx = Transaction(
        id=tx_id,
        firm_id="firm-alpha",
        client_id="client-1",
        period_id="period-1",
        tenant_id="firm-alpha",
        source_document_id=source_doc,
        source_row_reference=f"row:{tx_id}",
        supplier_gstin=gstin,
        invoice_number_raw=invoice_raw,
        invoice_number_normalized=invoice_norm,
        invoice_date=date(2025, 4, 15),
        taxable_value=taxable,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        cess=0.0,
        currency="INR",
    )
    return tx


def test_engine_exact_match():
    engine = ReconciliationEngine()
    book = [_create_mock_tx("b1", "INV/001", "INV001", "29AAAAA0000A1Z5", 1000.0, 90.0, 90.0)]
    portal = [_create_mock_tx("p1", "INV-001", "INV001", "29AAAAA0000A1Z5", 1000.0, 90.0, 90.0)]

    results, stats = engine.reconcile(book, portal)

    assert stats.matched == 1
    assert stats.total_book_transactions == 1
    assert stats.total_portal_transactions == 1
    assert len(results) == 1
    assert results[0].status == MatchStatus.MATCHED
    assert results[0].score == 1.0
    assert results[0].exception_type == ExceptionType.MATCHED


def test_engine_value_mismatch():
    engine = ReconciliationEngine()
    book = [_create_mock_tx("b1", "INV/002", "INV002", "29AAAAA0000A1Z5", 5000.0, 450.0, 450.0)]
    # Portal has much higher tax value
    portal = [_create_mock_tx("p1", "INV002", "INV002", "29AAAAA0000A1Z5", 5000.0, 900.0, 900.0)]

    results, stats = engine.reconcile(book, portal)

    assert stats.matched == 0
    assert stats.partial_match == 1
    assert results[0].status == MatchStatus.PARTIAL_MATCH
    assert results[0].exception_type == ExceptionType.VALUE_MISMATCH
    assert "SIGNIFICANT_VALUE_DISCREPANCY" in (results[0].reason_code or "")


def test_engine_fuzzy_candidate_match():
    engine = ReconciliationEngine()
    # Slight typo in invoice number between books and portal
    book = [_create_mock_tx("b1", "INV-2025-099", "INV2025099", "29AAAAA0000A1Z5", 2000.0, 180.0, 180.0)]
    portal = [_create_mock_tx("p1", "INV-2025-098", "INV2025098", "29AAAAA0000A1Z5", 2000.0, 180.0, 180.0)]

    results, stats = engine.reconcile(book, portal)

    assert stats.review_required == 1
    assert results[0].status == MatchStatus.CANDIDATE
    assert results[0].exception_type == ExceptionType.REVIEW_REQUIRED
    assert results[0].score >= 0.80


def test_engine_duplicate_book_invoice():
    engine = ReconciliationEngine()
    # Same supplier and invoice number entered twice in purchase register
    b1 = _create_mock_tx("b1", "INV/DUP", "INVDUP", "29AAAAA0000A1Z5", 1000.0, 90.0, 90.0)
    b2 = _create_mock_tx("b2", "INV/DUP", "INVDUP", "29AAAAA0000A1Z5", 1000.0, 90.0, 90.0)
    portal = [_create_mock_tx("p1", "INV/DUP", "INVDUP", "29AAAAA0000A1Z5", 1000.0, 90.0, 90.0)]

    results, stats = engine.reconcile([b1, b2], portal)

    assert stats.duplicates == 2
    duplicate_results = [r for r in results if r.exception_type == ExceptionType.DUPLICATE]
    assert len(duplicate_results) == 2


def test_engine_missing_in_2b_and_books():
    engine = ReconciliationEngine()
    book = [_create_mock_tx("b1", "INV-ONLY-BOOKS", "INVONLYBOOKS", "29AAAAA0000A1Z5", 1000.0, 90.0, 90.0)]
    portal = [_create_mock_tx("p1", "INV-ONLY-2B", "INVONLY2B", "27BBBBB1111B1Z2", 2000.0, 0.0, 0.0, igst=360.0)]

    results, stats = engine.reconcile(book, portal)

    assert stats.missing_in_2b == 1
    assert stats.missing_in_books == 1
    assert any(r.exception_type == ExceptionType.MISSING_IN_2B for r in results)
    assert any(r.exception_type == ExceptionType.MISSING_IN_BOOKS for r in results)
