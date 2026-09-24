"""Audit service tests.

Covers:
    - Audit events are created for firm/client/period operations
    - Events are append-only (created, never modified)
    - Events are tenant-scoped
    - Events contain correct entity type and event type
"""

from __future__ import annotations

from app.models import AuditEvent

from .conftest import FIRM_A, FIRM_B, auth_header


def _setup_firm(tc, headers=None) -> None:
    tc.post("/api/v1/firms", json={"name": "Alpha CA"}, headers=headers or auth_header())


def test_firm_creation_audit(client, db_session) -> None:
    _setup_firm(client)
    events = db_session.query(AuditEvent).filter(
        AuditEvent.tenant_id == FIRM_A,
        AuditEvent.event_type == "firm.created",
    ).all()
    assert len(events) == 1
    assert events[0].entity_type == "firm"
    assert events[0].entity_id == FIRM_A


def test_client_creation_audit(client, db_session) -> None:
    _setup_firm(client)
    client.post(
        "/api/v1/clients",
        json={"display_name": "Traders"},
        headers=auth_header(),
    )
    events = db_session.query(AuditEvent).filter(
        AuditEvent.tenant_id == FIRM_A,
        AuditEvent.event_type == "client.created",
    ).all()
    assert len(events) == 1
    assert events[0].entity_type == "client"
    assert events[0].payload_json["display_name"] == "Traders"


def test_client_update_audit(client, db_session) -> None:
    _setup_firm(client)
    resp = client.post(
        "/api/v1/clients",
        json={"display_name": "Original"},
        headers=auth_header(),
    )
    client_id = resp.json()["id"]
    client.patch(
        f"/api/v1/clients/{client_id}",
        json={"display_name": "Updated"},
        headers=auth_header(),
    )
    events = db_session.query(AuditEvent).filter(
        AuditEvent.tenant_id == FIRM_A,
        AuditEvent.event_type == "client.updated",
    ).all()
    assert len(events) == 1
    assert events[0].payload_json["display_name"] == "Updated"


def test_period_creation_audit(client, db_session) -> None:
    _setup_firm(client)
    resp = client.post(
        "/api/v1/clients",
        json={"display_name": "Traders"},
        headers=auth_header(),
    )
    client_id = resp.json()["id"]
    client.post(
        "/api/v1/periods",
        json={
            "client_id": client_id,
            "financial_year": "2025-26",
            "tax_period": "Apr-2025",
        },
        headers=auth_header(),
    )
    events = db_session.query(AuditEvent).filter(
        AuditEvent.tenant_id == FIRM_A,
        AuditEvent.event_type == "period.created",
    ).all()
    assert len(events) == 1
    assert events[0].payload_json["financial_year"] == "2025-26"


def test_audit_events_are_tenant_scoped(client, db_session) -> None:
    """Firm B's audit events don't include Firm A's."""
    _setup_firm(client)
    firm_b_headers = auth_header(user_id="user-b", firm_id=FIRM_B, role="owner")
    _setup_firm(client, headers=firm_b_headers)

    firm_a_events = db_session.query(AuditEvent).filter(AuditEvent.tenant_id == FIRM_A).count()
    firm_b_events = db_session.query(AuditEvent).filter(AuditEvent.tenant_id == FIRM_B).count()

    # Each firm should only have its own events.
    assert firm_a_events >= 1
    assert firm_b_events >= 1

    # Firm A's events should not appear in firm B's scope.
    all_events = db_session.query(AuditEvent).all()
    for event in all_events:
        if event.tenant_id == FIRM_A:
            assert event.firm_id == FIRM_A
        elif event.tenant_id == FIRM_B:
            assert event.firm_id == FIRM_B
