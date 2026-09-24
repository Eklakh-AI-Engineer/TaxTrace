"""Deterministic and AI-assisted structured notice extractor."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from app.parsers.normalizer import parse_date, parse_decimal


def extract_notice_facts_deterministic(text: str) -> dict[str, Any]:
    """Extract standard patterns (GSTIN, DIN/Reference, Sections, Dates, Notice Types) from notice text."""
    facts: dict[str, Any] = {
        "notice_type": "OTHER",
        "reference_number": None,
        "taxpayer_gstin": None,
        "taxpayer_name": None,
        "tax_period": None,
        "issue_date": None,
        "response_deadline": None,
        "demand_tax_amount": None,
        "cited_sections": [],
        "summary_allegations": None,
    }

    if not text:
        return facts

    # Detect Notice Type
    text_upper = text.upper()
    if "DRC-01" in text_upper or "DRC 01" in text_upper:
        facts["notice_type"] = "GST_DRC_01"
    elif "ASMT-10" in text_upper or "ASMT 10" in text_upper:
        facts["notice_type"] = "GST_ASMT_10"
    elif "SECTION 148" in text_upper or "SEC 148" in text_upper or "SEC. 148" in text_upper:
        facts["notice_type"] = "IT_SEC_148"
    elif "SECTION 142(1)" in text_upper or "142(1)" in text_upper:
        facts["notice_type"] = "IT_SEC_142_1"

    # Detect Indian GSTIN (standard 15-character alphanumeric regex)
    gstin_match = re.search(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b", text)
    if gstin_match:
        facts["taxpayer_gstin"] = gstin_match.group(1)

    # Detect Reference Number / DIN
    din_match = re.search(r"(?:DIN|REF(?:ERENCE)?(?:\s+NO)?|NOTICE\s+NO)[\s\:\-]+([A-Za-z0-9\/\-]+)", text, re.IGNORECASE)
    if din_match:
        facts["reference_number"] = din_match.group(1).strip()

    # Detect Cited Sections
    sections = re.findall(r"(?:Section|Sec\.?)\s+([0-9]{1,3}(?:\([0-9a-zA-Z]+\))?)", text, re.IGNORECASE)
    if sections:
        facts["cited_sections"] = sorted(list(set(sections)))

    # Detect Date patterns
    date_matches = re.findall(r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b", text)
    if date_matches:
        parsed_dates = [parse_date(d) for d in date_matches if parse_date(d)]
        if parsed_dates:
            facts["issue_date"] = parsed_dates[0]
            if len(parsed_dates) > 1:
                facts["response_deadline"] = parsed_dates[-1]

    # Detect monetary demands
    demand_match = re.search(r"(?:Demand|Tax\s+payable|Total\s+Tax|Amount\s+determined)[\s\:\-₹Rs\.]+([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
    if demand_match:
        facts["demand_tax_amount"] = float(parse_decimal(demand_match.group(1)))

    return facts
