"""Firm API tests.

Covers:
    - Create firm → 201
    - Duplicate firm → 409
    - Get /firms/me → 200
    - Update /firms/me → 200 (owner only)
    - List members includes creator
    - Audit event is created on firm creation
"""

from __future__ import annotations

from app.models import AuditEvent

from .conftest import FIRM_A, USER_OWNER, auth_header


def _create_firm(client, name: str = "Alpha CA", **kwargs) -> dict:
    headers = kwargs.pop("headers", auth_header())
    resp = client.post(
        "/api/v1/firms",
        json={"name": name},
        headers=headers,
    )
    return resp


def test_create_firm(client) -> None:
    resp = _create_firm(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == FIRM_A
    assert data["name"] == "Alpha CA"
    assert data["status"] == "active"


def test_duplicate_firm_returns_409(client) -> None:
    _create_firm(client)
    resp = _create_firm(client)
    assert resp.status_code == 409


def test_get_current_firm(client) -> None:
    _create_firm(client)
    resp = client.get("/api/v1/firms/me", headers=auth_header())
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alpha CA"


def test_get_firm_without_creating_returns_404(client) -> None:
    resp = client.get("/api/v1/firms/me", headers=auth_header())
    assert resp.status_code == 404


def test_update_firm_by_owner(client) -> None:
    _create_firm(client)
    resp = client.patch(
        "/api/v1/firms/me",
        json={"name": "Alpha CA Renamed"},
        headers=auth_header(),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alpha CA Renamed"


def test_update_firm_by_staff_returns_403(client) -> None:
    _create_firm(client)
    staff_headers = auth_header(user_id="staff-user", firm_id=FIRM_A, role="staff")
    resp = client.patch(
        "/api/v1/firms/me",
        json={"name": "Should Fail"},
        headers=staff_headers,
    )
    assert resp.status_code == 403


def test_list_members_includes_owner(client) -> None:
    _create_firm(client)
    resp = client.get("/api/v1/firms/me/members", headers=auth_header())
    assert resp.status_code == 200
    members = resp.json()
    assert len(members) >= 1
    assert any(m["user_id"] == USER_OWNER and m["role"] == "owner" for m in members)


def test_firm_creation_creates_audit_event(client, db_session) -> None:
    _create_firm(client)
    events = db_session.query(AuditEvent).filter(AuditEvent.tenant_id == FIRM_A).all()
    assert len(events) >= 1
    assert any(e.event_type == "firm.created" for e in events)
