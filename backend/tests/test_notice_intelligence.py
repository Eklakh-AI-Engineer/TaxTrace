"""Unit and integration tests for Notice Intelligence, Fact Extraction, Draft Generation, and Partner Approval.

Verifies:
- Notice document upload.
- Deterministic extraction of notice type, GSTIN, reference number, demand amounts, and sections.
- Generation of preliminary reply drafts.
- Partner role enforcement for draft approval (staff/senior roles are forbidden).
"""

from __future__ import annotations

from app.models import AuditEvent, Evidence, NoticeCase
from .conftest import FIRM_A, auth_header


def _setup_notice_case(client) -> tuple[str, str]:
    client.post("/api/v1/firms", json={"name": "Alpha CA"}, headers=auth_header())
    c_resp = client.post("/api/v1/clients", json={"display_name": "Alpha Traders"}, headers=auth_header())
    client_id = c_resp.json()["id"]

    notice_text = (
        "FORM GST DRC-01\n"
        "REFERENCE NO: ZA290425000129F\n"
        "GSTIN: 29AAAAA0000A1Z5\n"
        "DATE: 15/04/2025\n"
        "REPLY DEADLINE: 30/05/2025\n\n"
        "DEMAND NOTICE UNDER SECTION 73(1) OF CGST ACT, 2017\n"
        "Whereas discrepancy observed in ITC claimed in GSTR-3B vs GSTR-2B.\n"
        "Total Tax Payable: ₹ 45,000.00\n"
    ).encode("utf-8")

    files = {"file": ("notice_drc01.pdf", notice_text, "application/pdf")}
    up_resp = client.post(
        "/api/v1/notices",
        data={"client_id": client_id},
        files=files,
        headers=auth_header(),
    )
    assert up_resp.status_code == 201
    notice_id = up_resp.json()["id"]
    return client_id, notice_id


def test_notice_upload_and_extraction(client, db_session):
    client_id, notice_id = _setup_notice_case(client)

    # Trigger fact extraction
    ext_resp = client.post(f"/api/v1/notices/{notice_id}/extract", headers=auth_header())
    assert ext_resp.status_code == 200
    ext_data = ext_resp.json()

    assert ext_data["notice_type"] == "GST_DRC_01"
    assert ext_data["reference_number"] == "ZA290425000129F"
    assert ext_data["taxpayer_gstin"] == "29AAAAA0000A1Z5"
    assert ext_data["demand_tax_amount"] == 45000.0
    assert "73" in ext_data["cited_sections"] or "73(1)" in ext_data["cited_sections"]
    assert ext_data["evidence_created_count"] >= 1

    # Verify Evidence was persisted
    evidences = db_session.query(Evidence).filter(Evidence.notice_case_id == notice_id).all()
    assert len(evidences) >= 1


def test_notice_draft_generation(client):
    client_id, notice_id = _setup_notice_case(client)
    client.post(f"/api/v1/notices/{notice_id}/extract", headers=auth_header())

    # Generate draft
    draft_resp = client.post(
        f"/api/v1/notices/{notice_id}/draft",
        json={"instructions": "Focus on bona fide purchase documentation."},
        headers=auth_header(),
    )
    assert draft_resp.status_code == 200
    draft_data = draft_resp.json()

    assert draft_data["status"] == "under_review"
    assert "FACTS OF THE CASE" in draft_data["content"]
    assert len(draft_data["missing_information"]) >= 1

    draft_id = draft_data["id"]

    # Verify draft API
    v_resp = client.post(f"/api/v1/drafts/{draft_id}/verify", headers=auth_header())
    assert v_resp.status_code == 200
    assert v_resp.json()["verified"] is True


def test_draft_approval_requires_partner_role(client):
    client_id, notice_id = _setup_notice_case(client)
    draft_resp = client.post(
        f"/api/v1/notices/{notice_id}/draft",
        json={},
        headers=auth_header(),
    )
    draft_id = draft_resp.json()["id"]

    # Staff role cannot approve -> 403
    staff_headers = auth_header(role="staff")
    rej_resp = client.post(
        f"/api/v1/drafts/{draft_id}/approve",
        json={"comment": "Approved by staff"},
        headers=staff_headers,
    )
    assert rej_resp.status_code == 403

    # Partner role approves -> 200
    partner_headers = auth_header(role="partner")
    app_resp = client.post(
        f"/api/v1/drafts/{draft_id}/approve",
        json={"comment": "Reviewed statutory compliance and verified tax invoices."},
        headers=partner_headers,
    )
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "approved"
    assert app_resp.json()["approved_by"] == "user-owner"
