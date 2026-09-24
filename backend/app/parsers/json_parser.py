"""Parser for GST Portal GSTR-2B JSON exports.

Handles nested JSON schemas (e.g. b2b invoices, inv items).
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from app.parsers.normalizer import (
    clean_string,
    normalize_invoice_number,
    parse_date,
    parse_decimal,
)


def parse_gstr2b_json(content_bytes: bytes) -> list[dict[str, Any]]:
    """Parse GSTR-2B JSON bytes and extract canonical transaction dictionaries.

    Supports the official GSTN GSTR-2B schema containing 'data' -> 'docdata' -> 'b2b' invoices.
    """
    text = content_bytes.decode("utf-8-sig", errors="replace")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []

    transactions: list[dict[str, Any]] = []

    # Support both wrapped {"data": {"docdata": ...}} and direct docdata
    doc_data = data.get("data", {}).get("docdata", {}) if isinstance(data, dict) else {}
    if not doc_data and isinstance(data, dict):
        doc_data = data.get("docdata", data)

    b2b_list = doc_data.get("b2b", []) if isinstance(doc_data, dict) else []

    row_counter = 0

    for supplier in b2b_list:
        supplier_gstin = clean_string(supplier.get("ctin"))
        inv_list = supplier.get("inv", [])

        for inv in inv_list:
            row_counter += 1
            inv_raw = clean_string(inv.get("inum"))
            inv_norm = normalize_invoice_number(inv_raw)
            inv_date = parse_date(inv.get("dt"))

            # Items inside the invoice
            items = inv.get("items", [])
            total_taxable = Decimal("0.00")
            total_cgst = Decimal("0.00")
            total_sgst = Decimal("0.00")
            total_igst = Decimal("0.00")
            total_cess = Decimal("0.00")

            if items:
                for itm in items:
                    total_taxable += parse_decimal(itm.get("txval"))
                    total_cgst += parse_decimal(itm.get("camt"))
                    total_sgst += parse_decimal(itm.get("samt"))
                    total_igst += parse_decimal(itm.get("iamt"))
                    total_cess += parse_decimal(itm.get("csamt"))
            else:
                # If invoice level amounts are provided directly
                total_taxable = parse_decimal(inv.get("val"))
                total_cgst = parse_decimal(inv.get("camt"))
                total_sgst = parse_decimal(inv.get("samt"))
                total_igst = parse_decimal(inv.get("iamt"))
                total_cess = parse_decimal(inv.get("csamt"))

            transactions.append({
                "source_row_reference": f"gstr2b:b2b:{supplier_gstin or 'unknown'}:{inv_raw or row_counter}",
                "supplier_gstin": supplier_gstin.upper() if supplier_gstin else None,
                "invoice_number_raw": inv_raw,
                "invoice_number_normalized": inv_norm,
                "invoice_date": inv_date,
                "taxable_value": total_taxable,
                "cgst": total_cgst,
                "sgst": total_sgst,
                "igst": total_igst,
                "cess": total_cess,
                "currency": "INR",
            })

    return transactions
