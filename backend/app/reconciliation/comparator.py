"""Deterministic financial and identifier comparators for tax reconciliation.

Follows CODING_RULES.md §3:
- Exact Decimal comparisons
- Explicit rounding tolerances
- Zero floating point arithmetic
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from difflib import SequenceMatcher
from typing import Any

from app.parsers.normalizer import parse_decimal

# Default tolerance for GST round-off differences in Indian tax filings (₹1.00)
ROUNDING_TOLERANCE = Decimal("1.00")


def are_amounts_equal(
    val1: Decimal | float | None,
    val2: Decimal | float | None,
    tolerance: Decimal = ROUNDING_TOLERANCE,
) -> bool:
    """Compare two monetary values within a deterministic rounding tolerance."""
    d1 = parse_decimal(val1)
    d2 = parse_decimal(val2)
    return abs(d1 - d2) <= tolerance


def calculate_amount_difference(
    val1: Decimal | float | None,
    val2: Decimal | float | None,
) -> Decimal:
    """Return signed difference between two amounts: val1 - val2."""
    d1 = parse_decimal(val1)
    d2 = parse_decimal(val2)
    return d1 - d2


def are_gstins_equal(gstin1: str | None, gstin2: str | None) -> bool:
    """Compare two GSTINs case-insensitively and stripped of whitespace."""
    if not gstin1 or not gstin2:
        return False
    return gstin1.strip().upper() == gstin2.strip().upper()


def are_invoices_equal(inv1: str | None, inv2: str | None) -> bool:
    """Compare normalized invoice numbers."""
    if not inv1 or not inv2:
        return False
    return inv1.strip().upper() == inv2.strip().upper()


def invoice_similarity_score(inv1: str | None, inv2: str | None) -> float:
    """Compute normalized string similarity between two invoice strings (0.0 to 1.0)."""
    if not inv1 or not inv2:
        return 0.0
    s1 = inv1.strip().upper()
    s2 = inv2.strip().upper()
    if s1 == s2:
        return 1.0
    return SequenceMatcher(None, s1, s2).ratio()


def are_dates_close(d1: date | None, d2: date | None, max_days: int = 30) -> bool:
    """Check if two invoice dates fall within an acceptable calendar window."""
    if not d1 or not d2:
        return True  # If one date is missing, do not hard-fail on date
    return abs((d1 - d2).days) <= max_days
