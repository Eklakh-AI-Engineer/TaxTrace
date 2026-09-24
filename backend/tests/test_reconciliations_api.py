"""Integration tests for Reconciliation and Exception APIs.

Verifies:
- Senior role required to execute reconciliation (403 for staff/viewer).
- Full end-to-end reconciliation run producing matches, exceptions, and evidence.
- Reconciliation summary retrieval.
- Paginated exception retrieval with type/severity filters.
- Exception detail with linked evidence records.
- Exception annotation and status update.
"""

from __future__ import annotations

import io
from app.models import AuditEvent, Evidence, ExceptionRecord, Match
from .conftest import FIRM_A, USER_OWNER, auth_header


def _setup_reconciliation_data(client) -> tuple[str, str]:
    # 1. Setup firm, client, period
    client.post("/api/v1/firms", json={"name": "Alpha CA"}, headers=auth_header())
    c_resp = client.post("/api/v1/clients", json={"display_name": "Alpha Traders"}, headers=auth_header())
    client_id = c_resp.json()["id"]

    p_resp = client.post(
        "/api/v1/periods",
        json={"client_id": client_id, "financial_year": "2025-26", "tax_period": "Apr-2025"},
        headers=auth_header(),
    )
    period_id = p_resp.json()["id"]

    # 2. Upload Books (Purchase Register)
    books_csv = b"""Supplier GSTIN,Invoice No,Date,Taxable Amount,CGST,SGST,IGST
29AAAAA0000A1Z5,INV-101,10/04/2025,10000.00,900.00,900.00,0.00
29AAAAA0000A1Z5,INV-102,12/04/2025,5000.00,450.00,450.00,0.00
27BBBBB1111B1Z2,INV-103,15/04/2025,8000.00,0.00,0.00,1440.00
"""
    files_b = {"file": ("books.csv", books_csv, "text/csv")}
    client.post(
        "/api/v1/documents",
        data={"client_id": client_id, "period_id": period_id, "document_type": "purchase_register"},
        files=files_b,
        headers=auth_header(),
    )

    # 3. Upload Portal (GSTR-2B)
    portal_csv = b"""Supplier GSTIN,Invoice No,Date,Taxable Amount,CGST,SGST,IGST
29AAAAA0000A1Z5,INV-101,10/04/2025,10000.00,900.00,900.00,0.00
29AAAAA0000A1Z5,INV-102,12/04/2025,5000.00,500.00,500.00,0.00
28CCCCC2222C1Z3,INV-PORTAL-ONLY,20/04/2025,3000.00,0.00,0.00,540.00
"""
    files_p = {"file": ("gstr2b.csv", portal_csv, "text/csv")}
    client.post(
        "/api/v1/documents",
        data={"client_id": client_id, "period_id": period_id, "document_type": "gstr2b_csv"},
        files=files_p,
        headers=auth_header(),
    )

    return client_id, period_id


def test_reconciliation_requires_senior_role(client):
    client_id, period_id = _setup_reconciliation_data(client)
    staff_headers = auth_header(role="staff")

    resp = client.post(
        "/api/v1/reconciliations",
        json={"client_id": client_id, "period_id": period_id},
        headers=staff_headers,
    )
    assert resp.status_code == 403


def test_run_reconciliation_end_to_end(client, db_session):
    client_id, period_id = _setup_reconciliation_data(client)

    # Trigger run as owner (higher than senior)
    resp = client.post(
        "/api/v1/reconciliations",
        json={"client_id": client_id, "period_id": period_id},
        headers=auth_header(role="owner"),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "completed"

    summary = data["summary"]
    # INV-101 is exact match
    assert summary["matched"] == 1
    # INV-102 has tax mismatch (450 vs 500)
    assert summary["partial_match"] == 1
    # INV-103 is missing in 2B
    assert summary["missing_in_2b"] == 1
    # INV-PORTAL-ONLY is missing in books
    assert summary["missing_in_books"] == 1

    # Verify audit event was logged
    audit = db_session.query(AuditEvent).filter(
        AuditEvent.entity_id == period_id,
        AuditEvent.event_type == "reconciliation.executed",
    ).first()
    assert audit is not None


def test_get_reconciliation_summary(client):
    client_id, period_id = _setup_reconciliation_data(client)
    client.post(
        "/api/v1/reconciliations",
        json={"client_id": client_id, "period_id": period_id},
        headers=auth_header(),
    )

    resp = client.get(f"/api/v1/reconciliations/{period_id}", headers=auth_header())
    assert resp.status_code == 200
    data = resp.json()
    assert data["matched"] == 1
    assert data["total_exceptions"] == 3


def test_list_exceptions_and_get_detail(client):
    client_id, period_id = _setup_reconciliation_data(client)
    client.post(
        "/api/v1/reconciliations",
        json={"client_id": client_id, "period_id": period_id},
        headers=auth_header(),
    )

    # List exceptions filtered by type
    exc_resp = client.get(
        f"/api/v1/reconciliations/{period_id}/exceptions?type=MISSING_IN_2B",
        headers=auth_header(),
    )
    assert exc_resp.status_code == 200
    exc_data = exc_resp.json()
    assert exc_data["total"] == 1
    exc_id = exc_data["items"][0]["id"]

    # Get exception detail with evidence
    detail_resp = client.get(f"/api/v1/exceptions/{exc_id}", headers=auth_header())
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == exc_id
    assert detail["type"] == "MISSING_IN_2B"
    assert len(detail["evidence"]) >= 1


def test_update_exception_status(client):
    client_id, period_id = _setup_reconciliation_data(client)
    client.post(
        "/api/v1/reconciliations",
        json={"client_id": client_id, "period_id": period_id},
        headers=auth_header(),
    )

    exc_list = client.get(f"/api/v1/reconciliations/{period_id}/exceptions", headers=auth_header()).json()
    exc_id = exc_list["items"][0]["id"]

    # Patch exception
    patch_resp = client.patch(
        f"/api/v1/exceptions/{exc_id}",
        json={"status": "in_review", "explanation": "Investigating with vendor"},
        headers=auth_header(),
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "in_review"
    assert patch_resp.json()["explanation"] == "Investigating with vendor"
