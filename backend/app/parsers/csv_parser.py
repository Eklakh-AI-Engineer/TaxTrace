"""CSV and Tabular parser for Purchase Registers and GSTR-2B exports.

Extracts rows into canonical dictionary records suitable for Transaction entity creation.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from app.parsers.normalizer import (
    clean_string,
    normalize_invoice_number,
    parse_date,
    parse_decimal,
)

# Common column name permutations found in Indian CA Tally / Busy / Excel books
COLUMN_MAPPINGS = {
    "gstin": ["gstin", "supplier_gstin", "party_gstin", "gstin_of_supplier", "gst_no", "party_gst"],
    "invoice_number": ["invoice_number", "invoice_no", "inv_no", "inv_num", "bill_no", "voucher_no", "doc_no"],
    "invoice_date": ["invoice_date", "inv_date", "date", "bill_date", "doc_date"],
    "taxable_value": ["taxable_value", "taxable_amount", "taxable_val", "taxable", "tax_val", "basic_amount"],
    "cgst": ["cgst", "cgst_amount", "central_tax", "cgst_val"],
    "sgst": ["sgst", "sgst_amount", "state_ut_tax", "state_tax", "sgst_val", "utgst"],
    "igst": ["igst", "igst_amount", "integrated_tax", "igst_val"],
    "cess": ["cess", "cess_amount", "cess_val"],
}


def _match_column(headers: list[str], field_key: str) -> str | None:
    """Find the best matching header for a standardized field."""
    aliases = COLUMN_MAPPINGS.get(field_key, [])
    header_lower_map = {h.strip().lower().replace(" ", "_"): h for h in headers}

    for alias in aliases:
        if alias in header_lower_map:
            return header_lower_map[alias]
    return None


def parse_csv_transactions(content_bytes: bytes) -> list[dict[str, Any]]:
    """Parse CSV bytes and extract canonical transaction dictionaries.

    Returns a list of dicts:
        - source_row_reference
        - supplier_gstin
        - invoice_number_raw
        - invoice_number_normalized
        - invoice_date
        - taxable_value (Decimal)
        - cgst (Decimal)
        - sgst (Decimal)
        - igst (Decimal)
        - cess (Decimal)
    """
    text = content_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))

    rows = list(reader)
    if not rows:
        return []

    # Find the header row (first non-empty row)
    header_idx = -1
    for i, row in enumerate(rows):
        if any(cell.strip() for cell in row):
            header_idx = i
            break

    if header_idx == -1:
        return []

    headers = rows[header_idx]
    col_map = {
        key: _match_column(headers, key)
        for key in COLUMN_MAPPINGS.keys()
    }

    # Index mapping
    header_indices: dict[str, int] = {}
    for standard_col, actual_col in col_map.items():
        if actual_col:
            header_indices[standard_col] = headers.index(actual_col)

    transactions: list[dict[str, Any]] = []

    for row_num, row in enumerate(rows[header_idx + 1:], start=header_idx + 2):
        if not any(cell.strip() for cell in row):
            continue  # Skip empty rows

        def get_val(key: str) -> str | None:
            idx = header_indices.get(key)
            if idx is not None and idx < len(row):
                return clean_string(row[idx])
            return None

        inv_raw = get_val("invoice_number")
        inv_norm = normalize_invoice_number(inv_raw)
        gstin = clean_string(get_val("gstin"))
        inv_date = parse_date(get_val("invoice_date"))

        taxable = parse_decimal(get_val("taxable_value"))
        cgst = parse_decimal(get_val("cgst"))
        sgst = parse_decimal(get_val("sgst"))
        igst = parse_decimal(get_val("igst"))
        cess = parse_decimal(get_val("cess"))

        # Skip rows with no financial substance or invoice identifier
        if not inv_raw and taxable == 0 and cgst == 0 and sgst == 0 and igst == 0:
            continue

        transactions.append({
            "source_row_reference": f"row:{row_num}",
            "supplier_gstin": gstin.upper() if gstin else None,
            "invoice_number_raw": inv_raw,
            "invoice_number_normalized": inv_norm,
            "invoice_date": inv_date,
            "taxable_value": taxable,
            "cgst": cgst,
            "sgst": sgst,
            "igst": igst,
            "cess": cess,
            "currency": "INR",
        })

    return transactions
