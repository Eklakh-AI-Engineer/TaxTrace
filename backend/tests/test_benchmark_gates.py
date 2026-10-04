"""Benchmark gate tests for CI.

These tests run the reconciliation engine on the pilot dataset and assert
minimum precision/recall thresholds. They are designed to be fast and
deterministic.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.parsers.csv_parser import parse_csv_transactions
from app.parsers.normalizer import parse_decimal
from app.reconciliation.engine import ReconciliationEngine
from app.reconciliation.rules import ExceptionType


class SimpleTransaction:
    """Lightweight transaction for benchmarking."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def normalize_invoice_key(invoice: str | None) -> str:
    import re
    if not invoice:
        return ""
    return re.sub(r"[\s\/\-\_\.]+", "", str(invoice).strip().upper())


def load_pilot_data():
    """Load pilot dataset and return book_txs, portal_txs, ground_truth."""
    base = Path(__file__).parent.parent.parent / "evaluations" / "datasets"
    
    books_content = (base / "pilot_books.csv").read_bytes()
    gstr2b_content = (base / "pilot_gstr2b.csv").read_bytes()
    
    with open(base / "ground_truth.json") as f:
        ground_truth_raw = json.load(f)
    
    ground_truth = {
        normalize_invoice_key(item["invoice"]): item["expected_status"]
        for item in ground_truth_raw
    }
    
    # Normalize fuzzy_match -> matched (since normalizer removes hyphens)
    normalized_ground_truth = {}
    for inv, lbl in ground_truth.items():
        if lbl == "fuzzy_match":
            normalized_ground_truth[inv] = "matched"
        else:
            normalized_ground_truth[inv] = lbl
    
    def load_txs(content):
        parsed = parse_csv_transactions(content)
        txs = []
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
            txs.append(tx)
        return txs
    
    book_txs = load_txs(books_content)
    portal_txs = load_txs(gstr2b_content)
    
    return book_txs, portal_txs, normalized_ground_truth


def map_engine_exception_to_ground_truth(exc_type: ExceptionType) -> str:
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


class TestReconciliationBenchmarkGates:
    """Benchmark gates that must pass for pilot readiness."""
    
    @pytest.fixture(scope="class")
    def benchmark_results(self):
        book_txs, portal_txs, ground_truth = load_pilot_data()
        engine = ReconciliationEngine()
        results, stats = engine.reconcile(book_txs, portal_txs)
        
        predicted = {}
        for r in results:
            invoice = r.book_tx.invoice_number_raw if r.book_tx else r.portal_tx.invoice_number_raw
            if invoice:
                predicted[normalize_invoice_key(invoice)] = map_engine_exception_to_ground_truth(r.exception_type)
        
        # Compute per-class metrics
        all_classes = set(ground_truth.values()) | set(predicted.values())
        metrics = {}
        for cls in all_classes:
            metrics[cls] = {"tp": 0, "fp": 0, "fn": 0}
        
        for invoice, expected in ground_truth.items():
            pred = predicted.get(invoice, "not_predicted")
            if pred == expected:
                metrics[expected]["tp"] += 1
            else:
                metrics[expected]["fn"] += 1
                if pred != "not_predicted":
                    metrics[pred]["fp"] += 1
        
        for invoice, pred in predicted.items():
            if invoice not in ground_truth:
                metrics[pred]["fp"] += 1
        
        # Calculate precision, recall, f1
        for cls in metrics:
            tp = metrics[cls]["tp"]
            fp = metrics[cls]["fp"]
            fn = metrics[cls]["fn"]
            precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            metrics[cls]["precision"] = precision
            metrics[cls]["recall"] = recall
            metrics[cls]["f1"] = f1
        
        return metrics, stats
    
    def test_matched_precision_gate(self, benchmark_results):
        """Matched precision must be >= 0.90"""
        metrics, _ = benchmark_results
        assert metrics["matched"]["precision"] >= 0.90, (
            f"Matched precision {metrics['matched']['precision']:.3f} < 0.90"
        )
    
    def test_matched_recall_gate(self, benchmark_results):
        """Matched recall must be >= 0.85"""
        metrics, _ = benchmark_results
        assert metrics["matched"]["recall"] >= 0.85, (
            f"Matched recall {metrics['matched']['recall']:.3f} < 0.85"
        )
    
    def test_missing_in_2b_precision_gate(self, benchmark_results):
        """Missing in 2B precision must be >= 0.90"""
        metrics, _ = benchmark_results
        assert metrics["missing_in_2b"]["precision"] >= 0.90
    
    def test_missing_in_2b_recall_gate(self, benchmark_results):
        """Missing in 2B recall must be >= 0.85"""
        metrics, _ = benchmark_results
        assert metrics["missing_in_2b"]["recall"] >= 0.85
    
    def test_value_mismatch_precision_gate(self, benchmark_results):
        """Value mismatch precision must be >= 0.90"""
        metrics, _ = benchmark_results
        assert metrics["value_mismatch"]["precision"] >= 0.90
    
    def test_value_mismatch_recall_gate(self, benchmark_results):
        """Value mismatch recall must be >= 0.85"""
        metrics, _ = benchmark_results
        assert metrics["value_mismatch"]["recall"] >= 0.85
    
    def test_engine_summary_stats(self, benchmark_results):
        """Basic sanity checks on engine summary."""
        _, stats = benchmark_results
        assert stats.total_book_transactions == 200
        assert stats.total_portal_transactions == 181
        assert stats.matched >= 150  # At least 75% exact match rate
        assert stats.missing_in_2b >= 15  # At least some missing invoices detected