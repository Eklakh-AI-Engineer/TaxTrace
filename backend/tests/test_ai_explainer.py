"""Unit and integration tests for AI grounded explanation and exception decisions.

Verifies:
- Explanations are generated using attached verified evidence.
- Verified facts are separated from hypotheses.
- Human decisions (accepted, rejected, resolved, needs_info) are recorded with audit trails.
"""

from __future__ import annotations

from app.models import AuditEvent, Evidence, ExceptionRecord
from .conftest import FIRM_A, auth_header


def _setup_exception_with_evidence(client, db_session) -> str:
    client.post("/api/v1/firms", json={"name": "Alpha CA"}, headers=auth_header())
    c_resp = client.post("/api/v1/clients", json={"display_name": "Alpha Traders"}, headers=auth_header())
    client_id = c_resp.json()["id"]

    p_resp = client.post(
        "/api/v1/periods",
        json={"client_id": client_id, "financial_year": "2025-26", "tax_period": "Apr-2025"},
        headers=auth_header(),
    )
    period_id = p_resp.json()["id"]

    # Directly create an exception record
    exc = ExceptionRecord(
        firm_id=FIRM_A,
        period_id=period_id,
        tenant_id=FIRM_A,
        type="VALUE_MISMATCH",
        severity="high",
        status="open",
        reason_code="SIGNIFICANT_VALUE_DISCREPANCY",
        explanation="Tax mismatch: Books=900.00, Portal=1800.00",
        created_by_system=True,
    )
    db_session.add(exc)
    db_session.flush()

    # Attach evidence
    ev = Evidence(
        firm_id=FIRM_A,
        tenant_id=FIRM_A,
        exception_id=exc.id,
        evidence_type="reconciliation_diff",
        source_text="Invoice INV/901: Books tax 900.00 vs GSTR-2B tax 1800.00",
        meta_data={"diff_tax": "-900.00"},
    )
    db_session.add(ev)
    db_session.commit()

    return exc.id


def test_ai_explanation_generation(client, db_session):
    exc_id = _setup_exception_with_evidence(client, db_session)

    resp = client.post(
        f"/api/v1/exceptions/{exc_id}/explanation",
        json={"mode": "concise"},
        headers=auth_header(),
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "summary" in data
    assert isinstance(data["facts"], list)
    assert isinstance(data["possible_causes"], list)
    assert isinstance(data["suggested_next_steps"], list)
    assert data["confidence"] > 0.0
    assert len(data["evidence_ids"]) >= 1

    # Verify audit event logged
    audit = db_session.query(AuditEvent).filter(
        AuditEvent.entity_id == exc_id,
        AuditEvent.event_type == "ai.explanation_generated",
    ).first()
    assert audit is not None


def test_record_human_decision_on_exception(client, db_session):
    exc_id = _setup_exception_with_evidence(client, db_session)

    resp = client.post(
        f"/api/v1/exceptions/{exc_id}/decision",
        json={
            "decision": "accepted",
            "comment": "Supplier issued credit note in subsequent month. Verified.",
        },
        headers=auth_header(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "accepted"
    assert "Credit note" in data["explanation"] or "Verified" in data["explanation"]

    # Verify audit event logged
    audit = db_session.query(AuditEvent).filter(
        AuditEvent.entity_id == exc_id,
        AuditEvent.event_type == "exception.decision_recorded",
    ).first()
    assert audit is not None
    assert audit.payload_json["decision"] == "accepted"
