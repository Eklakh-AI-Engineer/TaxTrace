"""Deterministic reconciliation engine.

Implements multi-pass matching per PRD.md §6:
1. Exact matching (GSTIN + Normalized Invoice + Tax amounts within ₹1 tolerance).
2. Normalized matching (GSTIN + Invoice match, but value discrepancy or tax bucket shift).
3. Controlled fuzzy candidate generation (High invoice similarity with matching supplier & values).
4. Unmatched exception classification (MISSING_IN_2B, MISSING_IN_BOOKS, DUPLICATE).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.models import Transaction
from app.parsers.normalizer import parse_decimal
from app.reconciliation.comparator import (
    ROUNDING_TOLERANCE,
    are_amounts_equal,
    are_dates_close,
    are_gstins_equal,
    are_invoices_equal,
    calculate_amount_difference,
    invoice_similarity_score,
)
from app.reconciliation.rules import (
    CURRENT_RULE_VERSION,
    ExceptionSeverity,
    ExceptionType,
    MatchStatus,
)


@dataclass
class MatchResult:
    book_tx: Transaction
    portal_tx: Transaction | None
    status: MatchStatus
    score: float
    rule_version: str = CURRENT_RULE_VERSION
    exception_type: ExceptionType | None = None
    severity: ExceptionSeverity = ExceptionSeverity.LOW
    reason_code: str | None = None
    explanation: str | None = None
    evidence_diff: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReconciliationSummaryStats:
    total_book_transactions: int = 0
    total_portal_transactions: int = 0
    matched: int = 0
    partial_match: int = 0
    missing_in_2b: int = 0
    missing_in_books: int = 0
    duplicates: int = 0
    review_required: int = 0


class ReconciliationEngine:
    """Executes deterministic multi-pass tax reconciliation."""

    def __init__(self, tolerance: Decimal = ROUNDING_TOLERANCE) -> None:
        self.tolerance = tolerance

    def reconcile(
        self,
        book_records: list[Transaction],
        portal_records: list[Transaction],
    ) -> tuple[list[MatchResult], ReconciliationSummaryStats]:
        results: list[MatchResult] = []
        matched_book_ids: set[str] = set()
        matched_portal_ids: set[str] = set()

        # Check for duplicates on book side
        book_invoice_counts: dict[tuple[str, str], list[Transaction]] = {}
        for b in book_records:
            gstin = (b.supplier_gstin or "").upper()
            inv = b.invoice_number_normalized or ""
            key = (gstin, inv)
            book_invoice_counts.setdefault(key, []).append(b)

        # Flag internal book duplicates
        for (gstin, inv), tx_list in book_invoice_counts.items():
            if len(tx_list) > 1 and gstin and inv:
                for tx in tx_list:
                    matched_book_ids.add(tx.id)
                    results.append(
                        MatchResult(
                            book_tx=tx,
                            portal_tx=None,
                            status=MatchStatus.REJECTED,
                            score=0.0,
                            exception_type=ExceptionType.DUPLICATE,
                            severity=ExceptionSeverity.HIGH,
                            reason_code="BOOK_DUPLICATE_INVOICE",
                            explanation=f"Duplicate invoice '{inv}' recorded {len(tx_list)} times in purchase register.",
                            evidence_diff={"duplicate_count": len(tx_list), "invoice_number": inv},
                        )
                    )

        available_books = [b for b in book_records if b.id not in matched_book_ids]
        available_portals = [p for p in portal_records]

        # -------------------------------------------------------------------
        # PASS 1: Exact Matching
        # -------------------------------------------------------------------
        for b in list(available_books):
            for p in list(available_portals):
                if p.id in matched_portal_ids or b.id in matched_book_ids:
                    continue

                if are_gstins_equal(b.supplier_gstin, p.supplier_gstin) and are_invoices_equal(
                    b.invoice_number_normalized, p.invoice_number_normalized
                ):
                    b_taxable = parse_decimal(b.taxable_value)
                    p_taxable = parse_decimal(p.taxable_value)
                    b_tax = parse_decimal(b.cgst) + parse_decimal(b.sgst) + parse_decimal(b.igst)
                    p_tax = parse_decimal(p.cgst) + parse_decimal(p.sgst) + parse_decimal(p.igst)

                    if are_amounts_equal(b_taxable, p_taxable, self.tolerance) and are_amounts_equal(
                        b_tax, p_tax, self.tolerance
                    ):
                        matched_book_ids.add(b.id)
                        matched_portal_ids.add(p.id)
                        available_books.remove(b)
                        available_portals.remove(p)

                        results.append(
                            MatchResult(
                                book_tx=b,
                                portal_tx=p,
                                status=MatchStatus.MATCHED,
                                score=1.0,
                                exception_type=ExceptionType.MATCHED,
                                severity=ExceptionSeverity.LOW,
                                reason_code="EXACT_MATCH",
                                explanation="Exact match on GSTIN, normalized invoice number, and tax values.",
                                evidence_diff={
                                    "book_taxable": str(b_taxable),
                                    "portal_taxable": str(p_taxable),
                                    "book_tax": str(b_tax),
                                    "portal_tax": str(p_tax),
                                },
                            )
                        )
                        break

        # -------------------------------------------------------------------
        # PASS 2: Normalized Value & Component Discrepancy Matching
        # -------------------------------------------------------------------
        for b in list(available_books):
            for p in list(available_portals):
                if p.id in matched_portal_ids or b.id in matched_book_ids:
                    continue

                if are_gstins_equal(b.supplier_gstin, p.supplier_gstin) and are_invoices_equal(
                    b.invoice_number_normalized, p.invoice_number_normalized
                ):
                    b_taxable = parse_decimal(b.taxable_value)
                    p_taxable = parse_decimal(p.taxable_value)
                    b_tax = parse_decimal(b.cgst) + parse_decimal(b.sgst) + parse_decimal(b.igst)
                    p_tax = parse_decimal(p.cgst) + parse_decimal(p.sgst) + parse_decimal(p.igst)

                    diff_taxable = calculate_amount_difference(b_taxable, p_taxable)
                    diff_tax = calculate_amount_difference(b_tax, p_tax)

                    matched_book_ids.add(b.id)
                    matched_portal_ids.add(p.id)
                    available_books.remove(b)
                    available_portals.remove(p)

                    # Sub-classification: Value mismatch or partial component match
                    if abs(diff_taxable) > Decimal("100.00") or abs(diff_tax) > Decimal("100.00"):
                        exc_type = ExceptionType.VALUE_MISMATCH
                        severity = ExceptionSeverity.HIGH
                        reason = "SIGNIFICANT_VALUE_DISCREPANCY"
                        explanation = (
                            f"Invoice number matched but tax value discrepancy: Books={b_tax}, Portal={p_tax}."
                        )
                    else:
                        exc_type = ExceptionType.PARTIAL_MATCH
                        severity = ExceptionSeverity.MEDIUM
                        reason = "TAX_COMPONENT_OR_MINOR_ROUNDING_MISMATCH"
                        explanation = f"Matched invoice with minor tax difference: diff_tax={diff_tax}."

                    results.append(
                        MatchResult(
                            book_tx=b,
                            portal_tx=p,
                            status=MatchStatus.PARTIAL_MATCH,
                            score=0.85,
                            exception_type=exc_type,
                            severity=severity,
                            reason_code=reason,
                            explanation=explanation,
                            evidence_diff={
                                "diff_taxable": str(diff_taxable),
                                "diff_tax": str(diff_tax),
                                "book_taxable": str(b_taxable),
                                "portal_taxable": str(p_taxable),
                            },
                        )
                    )
                    break

        # -------------------------------------------------------------------
        # PASS 3: Controlled Fuzzy Candidate Matching
        # -------------------------------------------------------------------
        for b in list(available_books):
            for p in list(available_portals):
                if p.id in matched_portal_ids or b.id in matched_book_ids:
                    continue

                if are_gstins_equal(b.supplier_gstin, p.supplier_gstin):
                    b_inv = b.invoice_number_normalized or ""
                    p_inv = p.invoice_number_normalized or ""
                    sim = invoice_similarity_score(b_inv, p_inv)

                    # High invoice similarity threshold (>= 0.80) with matching amounts
                    b_taxable = parse_decimal(b.taxable_value)
                    p_taxable = parse_decimal(p.taxable_value)

                    if sim >= 0.80 and are_amounts_equal(b_taxable, p_taxable, Decimal("10.00")):
                        matched_book_ids.add(b.id)
                        matched_portal_ids.add(p.id)
                        available_books.remove(b)
                        available_portals.remove(p)

                        results.append(
                            MatchResult(
                                book_tx=b,
                                portal_tx=p,
                                status=MatchStatus.CANDIDATE,
                                score=round(sim, 2),
                                exception_type=ExceptionType.REVIEW_REQUIRED,
                                severity=ExceptionSeverity.MEDIUM,
                                reason_code="FUZZY_INVOICE_CANDIDATE",
                                explanation=(
                                    f"Similar invoice candidate detected: Books='{b_inv}', "
                                    f"Portal='{p_inv}' (similarity: {round(sim*100, 1)}%)."
                                ),
                                evidence_diff={
                                    "similarity_score": round(sim, 4),
                                    "book_invoice": b_inv,
                                    "portal_invoice": p_inv,
                                },
                            )
                        )
                        break

        # -------------------------------------------------------------------
        # PASS 4: Unmatched Transactions
        # -------------------------------------------------------------------
        # Books not matched in 2B
        for b in available_books:
            results.append(
                MatchResult(
                    book_tx=b,
                    portal_tx=None,
                    status=MatchStatus.REJECTED,
                    score=0.0,
                    exception_type=ExceptionType.MISSING_IN_2B,
                    severity=ExceptionSeverity.HIGH,
                    reason_code="NOT_FOUND_IN_GSTR2B",
                    explanation=f"Invoice '{b.invoice_number_raw}' recorded in books is missing in GSTR-2B inward supplies.",
                    evidence_diff={
                        "supplier_gstin": b.supplier_gstin,
                        "invoice_number": b.invoice_number_raw,
                        "taxable_value": str(b.taxable_value),
                    },
                )
            )

        # 2B transactions not found in Books
        for p in available_portals:
            results.append(
                MatchResult(
                    book_tx=None,  # type: ignore
                    portal_tx=p,
                    status=MatchStatus.REJECTED,
                    score=0.0,
                    exception_type=ExceptionType.MISSING_IN_BOOKS,
                    severity=ExceptionSeverity.HIGH,
                    reason_code="NOT_FOUND_IN_PURCHASE_REGISTER",
                    explanation=f"Invoice '{p.invoice_number_raw}' from supplier '{p.supplier_gstin}' appears in GSTR-2B but is missing in books.",
                    evidence_diff={
                        "supplier_gstin": p.supplier_gstin,
                        "invoice_number": p.invoice_number_raw,
                        "taxable_value": str(p.taxable_value),
                    },
                )
            )

        # Calculate summary statistics
        stats = ReconciliationSummaryStats(
            total_book_transactions=len(book_records),
            total_portal_transactions=len(portal_records),
            matched=sum(1 for r in results if r.exception_type == ExceptionType.MATCHED),
            partial_match=sum(1 for r in results if r.exception_type in [ExceptionType.PARTIAL_MATCH, ExceptionType.VALUE_MISMATCH]),
            missing_in_2b=sum(1 for r in results if r.exception_type == ExceptionType.MISSING_IN_2B),
            missing_in_books=sum(1 for r in results if r.exception_type == ExceptionType.MISSING_IN_BOOKS),
            duplicates=sum(1 for r in results if r.exception_type == ExceptionType.DUPLICATE),
            review_required=sum(1 for r in results if r.exception_type == ExceptionType.REVIEW_REQUIRED),
        )

        return results, stats
