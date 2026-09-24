"""Parsers and normalization unit tests.

Verifies:
- Normalization of invoice numbers (stripping / - space and case insensitive).
- Decimal financial amounts are exact to 2 decimal places (Numeric(20,2)).
- Dates are parsed reliably.
- CSV parsing extracts canonical columns from varying header names.
- GSTR-2B JSON extracts inward supply invoices and item details.
"""

from __future__ import annotations

import json
from decimal import Decimal

from app.parsers.csv_parser import parse_csv_transactions
from app.parsers.json_parser import parse_gstr2b_json
from app.parsers.normalizer import (
    clean_string,
    normalize_invoice_number,
    parse_date,
    parse_decimal,
)


def test_normalize_invoice_number():
    assert normalize_invoice_number("INV/2025-26/0042") == "INV2025260042"
    assert normalize_invoice_number("inv-001") == "INV001"
    assert normalize_invoice_number("  BILL 109 / B ") == "BILL109B"
    assert normalize_invoice_number(None) is None


def test_parse_decimal():
    assert parse_decimal("1,250.50") == Decimal("1250.50")
    assert parse_decimal("₹ 500.00") == Decimal("500.00")
    assert parse_decimal(150) == Decimal("150.00")
    assert parse_decimal(None) == Decimal("0.00")
    assert parse_decimal("invalid") == Decimal("0.00")


def test_parse_date():
    d = parse_date("15/04/2025")
    assert d is not None
    assert d.year == 2025
    assert d.month == 4
    assert d.day == 15

    d2 = parse_date("2025-05-20")
    assert d2 is not None
    assert d2.year == 2025
    assert d2.month == 5
    assert d2.day == 20


def test_csv_parser_purchase_register():
    csv_content = b"""Supplier GSTIN,Invoice No,Date,Taxable Amount,CGST,SGST,IGST
29AAAAA0000A1Z5,INV-101,10/05/2025,10000.00,900.00,900.00,0.00
27BBBBB1111B2Z6,INV/202,12/05/2025,50000.00,0.00,0.00,9000.00
"""
    txs = parse_csv_transactions(csv_content)
    assert len(txs) == 2

    first = txs[0]
    assert first["supplier_gstin"] == "29AAAAA0000A1Z5"
    assert first["invoice_number_raw"] == "INV-101"
    assert first["invoice_number_normalized"] == "INV101"
    assert first["taxable_value"] == Decimal("10000.00")
    assert first["cgst"] == Decimal("900.00")
    assert first["sgst"] == Decimal("900.00")
    assert first["igst"] == Decimal("0.00")

    second = txs[1]
    assert second["supplier_gstin"] == "27BBBBB1111B2Z6"
    assert second["invoice_number_raw"] == "INV/202"
    assert second["invoice_number_normalized"] == "INV202"
    assert second["igst"] == Decimal("9000.00")


def test_gstr2b_json_parser():
    gstr2b_payload = {
        "data": {
            "docdata": {
                "b2b": [
                    {
                        "ctin": "29XYZAB1234F1Z8",
                        "inv": [
                            {
                                "inum": "GST/991",
                                "dt": "22-04-2025",
                                "val": 11800.0,
                                "items": [
                                    {
                                        "txval": 10000.0,
                                        "camt": 900.0,
                                        "samt": 900.0,
                                        "iamt": 0.0,
                                        "csamt": 0.0,
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        }
    }
    json_bytes = json.dumps(gstr2b_payload).encode("utf-8")
    txs = parse_gstr2b_json(json_bytes)

    assert len(txs) == 1
    tx = txs[0]
    assert tx["supplier_gstin"] == "29XYZAB1234F1Z8"
    assert tx["invoice_number_raw"] == "GST/991"
    assert tx["invoice_number_normalized"] == "GST991"
    assert tx["taxable_value"] == Decimal("10000.00")
    assert tx["cgst"] == Decimal("900.00")
    assert tx["sgst"] == Decimal("900.00")
