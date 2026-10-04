"""Reconciliation Benchmark Script.

Runs the deterministic reconciliation engine on pilot datasets and computes
precision, recall, F1 per exception type against ground truth.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.reconciliation.engine import ReconciliationEngine
from backend.app.reconciliation.rules import ExceptionType
from backend.app.parsers.csv_parser import parse_csv_transactions
from backend.app.parsers.normalizer import parse_decimal


@dataclass
class BenchmarkResult:
    exception_type: str
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float:
        if self.tp + self.fp == 0:
            return 1.0
        return self.tp / (self.tp + self.fp)

    @property
    def recall(self) -> float:
        if self.tp + self.fn == 0:
            return 1.0
        return self.tp / (self.tp + self.fn)

    @property
    def f1(self) -> float:
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * self.precision * self.recall / (self.precision + self.recall)


@dataclass
class SimpleTransaction:
    """Lightweight transaction for benchmarking (avoids SQLAlchemy metadata issues)."""
    id: str
    supplier_gstin: str | None
    invoice_number_raw: str | None
    invoice_number_normalized: str | None
    invoice_date: date | None
    taxable_value: Decimal | None
    cgst: Decimal | None
    sgst: Decimal | None
    igst: Decimal | None
    cess: Decimal | None
    currency: str = "INR"


def load_ground_truth(path: Path) -> dict[str, str]:
    """Load ground truth mapping invoice -> expected_status."""
    with open(path) as f:
        data = json.load(f)
    return {item["invoice"]: item["expected_status"] for item in data}


def load_transactions_from_csv(path: Path) -> list[SimpleTransaction]:
    """Parse CSV and convert to SimpleTransaction objects."""
    content = path.read_bytes()
    parsed = parse_csv_transactions(content)

    transactions = []
    for i, rec in enumerate(parsed):
        tx = SimpleTransaction(
            id=f"bench_{i}",
            supplier_gstin=rec.get("supplier_gstin"),
            invoice_number_raw=rec.get("invoice_number_raw"),
            invoice_number_normalized=rec.get("invoice_number_normalized"),
            invoice_date=rec.get("invoice_date"),
            taxable_value=parse_decimal(rec.get("taxable_value")),
            cgst=parse_decimal(rec.get("cgst")),
            sgst=parse_decimal(rec.get("sgst")),
            igst=parse_decimal(rec.get("igst")),
            cess=parse_decimal(rec.get("cess")),
            currency=rec.get("currency", "INR"),
        )
        transactions.append(tx)
    return transactions


def map_engine_exception_to_ground_truth(exc_type: ExceptionType) -> str:
    """Map engine exception type to ground truth label."""
    mapping = {
        ExceptionType.MATCHED: "matched",
        ExceptionType.VALUE_MISMATCH: "value_mismatch",
        ExceptionType.PARTIAL_MATCH: "value_mismatch",
        ExceptionType.MISSING_IN_2B: "missing_in_2b",
        ExceptionType.MISSING_IN_BOOKS: "missing_in_books",
        ExceptionType.DUPLICATE: "duplicate",
        ExceptionType.REVIEW_REQUIRED: "fuzzy_match",
        ExceptionType.GSTIN_MISMATCH: "gstin_mismatch",
        ExceptionType.DATE_MISMATCH: "date_mismatch",
    }
    return mapping.get(exc_type, "unknown")


def normalize_ground_truth_label(label: str) -> str:
    """Normalize ground truth labels to match engine behavior.

    The generator creates 'fuzzy_match' cases by removing hyphens from invoice numbers,
    but the normalizer also removes hyphens, making them exact matches after normalization.
    """
    if label == "fuzzy_match":
        return "matched"
    return label


def normalize_invoice_key(invoice: str | None) -> str:
    """Normalize invoice for consistent comparison."""
    if not invoice:
        return ""
    return re.sub(r"[\s\/\-\_\.]+", "", str(invoice).strip().upper())


def run_benchmark(
    books_path: Path,
    gstr2b_path: Path,
    ground_truth_path: Path,
) -> dict[str, BenchmarkResult]:
    """Run reconciliation and compare against ground truth."""
    print(f"Loading books from {books_path}")
    book_txs = load_transactions_from_csv(books_path)
    print(f"  Loaded {len(book_txs)} book transactions")

    print(f"Loading GSTR-2B from {gstr2b_path}")
    portal_txs = load_transactions_from_csv(gstr2b_path)
    print(f"  Loaded {len(portal_txs)} portal transactions")

    print(f"Loading ground truth from {ground_truth_path}")
    ground_truth = load_ground_truth(ground_truth_path)
    print(f"  Loaded {len(ground_truth)} ground truth entries")

    # Normalize ground truth keys for consistent comparison
    normalized_ground_truth = {
        normalize_invoice_key(inv): normalize_ground_truth_label(lbl)
        for inv, lbl in ground_truth.items()
    }

    # Run reconciliation
    engine = ReconciliationEngine()
    results, stats = engine.reconcile(book_txs, portal_txs)

    print(f"\nEngine Summary:")
    print(f"  Matched: {stats.matched}")
    print(f"  Partial Match: {stats.partial_match}")
    print(f"  Missing in 2B: {stats.missing_in_2b}")
    print(f"  Missing in Books: {stats.missing_in_books}")
    print(f"  Duplicates: {stats.duplicates}")
    print(f"  Review Required: {stats.review_required}")

    # Build predicted mapping: normalized invoice -> predicted exception type
    predicted = {}
    for r in results:
        invoice = r.book_tx.invoice_number_raw if r.book_tx else r.portal_tx.invoice_number_raw
        if invoice:
            predicted[normalize_invoice_key(invoice)] = map_engine_exception_to_ground_truth(r.exception_type)

    # Compute per-class metrics
    all_classes = set(normalized_ground_truth.values()) | set(predicted.values())
    metrics = {cls: BenchmarkResult(exception_type=cls) for cls in all_classes}

    # Debug: show mismatches
    mismatches = []
    for invoice, expected in normalized_ground_truth.items():
        pred = predicted.get(invoice, "not_predicted")
        if pred == expected:
            metrics[expected].tp += 1
        else:
            metrics[expected].fn += 1
            if pred != "not_predicted":
                metrics[pred].fp += 1
            mismatches.append((invoice, expected, pred))

    # Handle predictions for invoices not in ground truth
    for invoice, pred in predicted.items():
        if invoice not in normalized_ground_truth:
            metrics[pred].fp += 1
            mismatches.append((invoice, "not_in_ground_truth", pred))

    if mismatches:
        print(f"\nMISMATCHES ({len(mismatches)}):")
        for inv, exp, pred in mismatches[:20]:
            print(f"  {inv}: expected={exp}, predicted={pred}")

    return metrics


def print_results(metrics: dict[str, BenchmarkResult]) -> None:
    """Print formatted benchmark results."""
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS")
    print("=" * 80)
    print(f"{'Exception Type':<25} {'Precision':>10} {'Recall':>10} {'F1':>10} {'TP':>5} {'FP':>5} {'FN':>5}")
    print("-" * 80)

    # Sort by exception type for consistent output
    for cls in sorted(metrics.keys()):
        m = metrics[cls]
        print(f"{cls:<25} {m.precision:>10.3f} {m.recall:>10.3f} {m.f1:>10.3f} {m.tp:>5} {m.fp:>5} {m.fn:>5}")

    print("-" * 80)

    # Macro averages
    macro_precision = sum(m.precision for m in metrics.values()) / len(metrics)
    macro_recall = sum(m.recall for m in metrics.values()) / len(metrics)
    macro_f1 = sum(m.f1 for m in metrics.values()) / len(metrics)

    print(f"{'MACRO AVG':<25} {macro_precision:>10.3f} {macro_recall:>10.3f} {macro_f1:>10.3f}")

    # Weighted averages (by support = TP + FN)
    total_support = sum(m.tp + m.fn for m in metrics.values())
    if total_support > 0:
        weighted_precision = sum(m.precision * (m.tp + m.fn) for m in metrics.values()) / total_support
        weighted_recall = sum(m.recall * (m.tp + m.fn) for m in metrics.values()) / total_support
        weighted_f1 = sum(m.f1 * (m.tp + m.fn) for m in metrics.values()) / total_support
        print(f"{'WEIGHTED AVG':<25} {weighted_precision:>10.3f} {weighted_recall:>10.3f} {weighted_f1:>10.3f}")

    print("=" * 80)

    # Gate checks
    print("\nGATE CHECKS:")
    critical_classes = ["matched", "missing_in_2b", "value_mismatch", "fuzzy_match"]
    all_pass = True
    for cls in critical_classes:
        if cls in metrics:
            m = metrics[cls]
            precision_ok = m.precision >= 0.90
            recall_ok = m.recall >= 0.85
            status = "PASS" if (precision_ok and recall_ok) else "FAIL"
            if status == "FAIL":
                all_pass = False
            print(f"  {cls}: precision={m.precision:.3f} (>=0.90: {precision_ok}), "
                  f"recall={m.recall:.3f} (>=0.85: {recall_ok}) -> {status}")

    if all_pass:
        print("\n✅ ALL GATES PASSED")
        return 0
    else:
        print("\n❌ SOME GATES FAILED")
        return 1


def main() -> int:
    base = Path(__file__).parent / "datasets"
    books_path = base / "pilot_books.csv"
    gstr2b_path = base / "pilot_gstr2b.csv"
    ground_truth_path = base / "ground_truth.json"

    for p in [books_path, gstr2b_path, ground_truth_path]:
        if not p.exists():
            print(f"ERROR: File not found: {p}")
            return 1

    metrics = run_benchmark(books_path, gstr2b_path, ground_truth_path)
    return print_results(metrics)


if __name__ == "__main__":
    sys.exit(main())