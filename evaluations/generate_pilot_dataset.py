"""Generates privacy-safe, labeled pilot data for evaluation and onboarding.

This script creates synthetic but realistic GST data (GSTR-2B and Purchase Register)
with known injected edge cases (missing invoices, value mismatches, fuzzy matches).
This ensures that the pilot onboarding dataset serves as a benchmark fixture.
"""

import csv
import json
import os
import random
from datetime import date, timedelta
from typing import Any

# Directory setup
EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.join(EVAL_DIR, "datasets")
os.makedirs(DATASETS_DIR, exist_ok=True)

# Synthetic seed data
VENDORS = [
    {"name": "Tech Corp India", "gstin": "27AAACT2727Q1ZW"},
    {"name": "Global Supplies Pvt Ltd", "gstin": "29AAACG1234H1Z5"},
    {"name": "Apex Logistics", "gstin": "07AAAAA0000A1Z5"},
]

def generate_invoice_number(prefix: str, idx: int) -> str:
    return f"{prefix}-{2026}-{idx:04d}"

def create_dataset(num_transactions: int = 100):
    """Generates matched and mismatched transaction pairs."""
    book_txns = []
    gstr_txns = []
    ground_truth = []
    
    start_date = date(2026, 4, 1)

    for i in range(num_transactions):
        vendor = random.choice(VENDORS)
        inv_date = start_date + timedelta(days=random.randint(0, 30))
        inv_num = generate_invoice_number("INV", i)
        base_amount = round(random.uniform(100.0, 50000.0), 2)
        tax = round(base_amount * 0.18, 2)
        total = round(base_amount + tax, 2)
        
        # Scenario probabilities
        scenario_val = random.random()
        
        if scenario_val < 0.7:
            # 70% Exact Match
            book_txns.append(_make_row(vendor, inv_num, inv_date, base_amount, tax))
            gstr_txns.append(_make_row(vendor, inv_num, inv_date, base_amount, tax))
            ground_truth.append({"invoice": inv_num, "expected_status": "matched"})
            
        elif scenario_val < 0.8:
            # 10% Missing in GSTR-2B
            book_txns.append(_make_row(vendor, inv_num, inv_date, base_amount, tax))
            ground_truth.append({"invoice": inv_num, "expected_status": "missing_in_2b"})
            
        elif scenario_val < 0.9:
            # 10% Value Mismatch (wrong tax in books)
            book_txns.append(_make_row(vendor, inv_num, inv_date, base_amount, round(tax * 0.9, 2)))
            gstr_txns.append(_make_row(vendor, inv_num, inv_date, base_amount, tax))
            ground_truth.append({"invoice": inv_num, "expected_status": "value_mismatch"})
            
        else:
            # 10% Fuzzy match (invoice number typo in books)
            fuzzy_inv = inv_num.replace("-", "") # Removing hyphen
            book_txns.append(_make_row(vendor, fuzzy_inv, inv_date, base_amount, tax))
            gstr_txns.append(_make_row(vendor, inv_num, inv_date, base_amount, tax))
            ground_truth.append({"invoice": inv_num, "expected_status": "fuzzy_match"})

    # Write to files
    _write_csv(os.path.join(DATASETS_DIR, "pilot_books.csv"), book_txns)
    _write_csv(os.path.join(DATASETS_DIR, "pilot_gstr2b.csv"), gstr_txns)
    
    with open(os.path.join(DATASETS_DIR, "ground_truth.json"), "w") as f:
        json.dump(ground_truth, f, indent=2)
        
    print(f"Generated {len(book_txns)} book rows and {len(gstr_txns)} GSTR rows.")
    print(f"Saved to {DATASETS_DIR}")

def _make_row(vendor: dict, inv_num: str, inv_date: date, base: float, tax: float) -> dict:
    return {
        "Supplier Name": vendor["name"],
        "Supplier GSTIN": vendor["gstin"],
        "Invoice Number": inv_num,
        "Invoice Date": inv_date.strftime("%Y-%m-%d"),
        "Taxable Value": base,
        "IGST": round(tax, 2),
        "CGST": 0,
        "SGST": 0
    }

def _write_csv(path: str, rows: list[dict]):
    if not rows:
        return
    with open(path, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    create_dataset(200)
