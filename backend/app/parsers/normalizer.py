"""Normalization and extraction helpers for financial documents.

Follows CODING_RULES.md §3 and DATA_SPEC.md §5:
- Deterministic parsing
- Decimal representation for currency/taxes (Numeric(20,2))
- Standardized invoice normalization
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def clean_string(val: Any) -> str | None:
    """Trim and clean string values, returning None if empty."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def normalize_invoice_number(raw_invoice: str | None) -> str | None:
    """Normalize invoice numbers for reconciliation comparison.

    Removes special characters (/ - . _ whitespace) and uppercase.
    e.g. 'INV/2025-26/0012' -> 'INV2025260012'.
    """
    if not raw_invoice:
        return None
    s = str(raw_invoice).strip().upper()
    # Strip typical separators: /, -, _, space, dot
    normalized = re.sub(r"[\s\/\-\_\.]+", "", s)
    return normalized if normalized else None


def parse_decimal(val: Any, default: Decimal = Decimal("0.00")) -> Decimal:
    """Parse financial amounts deterministically into Decimal(20, 2).

    Handles string numbers with commas, currency symbols, and whitespace.
    """
    if val is None:
        return default
    if isinstance(val, (int, float, Decimal)):
        try:
            return round(Decimal(str(val)), 2)
        except (InvalidOperation, TypeError):
            return default

    s = str(val).strip().replace(",", "").replace("₹", "").replace("$", "")
    if not s:
        return default
    try:
        return round(Decimal(s), 2)
    except InvalidOperation:
        return default


def parse_date(val: Any) -> date | None:
    """Attempt to parse common date formats encountered in Indian tax filings:

    DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD, DD.MM.YYYY, etc.
    """
    if val is None:
        return None
    if isinstance(val, (date, datetime)):
        return val if isinstance(val, date) and not isinstance(val, datetime) else val.date()

    s = str(val).strip()
    if not s:
        return None

    formats = [
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d-%b-%Y",
        "%d-%b-%y",
        "%d/%m/%y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None
