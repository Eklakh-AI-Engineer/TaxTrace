"""Role-based permission tests.

Covers:
    - Owner can perform owner-only actions
    - Partner can perform partner+ actions
    - Staff cannot perform partner-only actions
    - Viewer cannot perform staff-only actions
    - has_minimum_role utility
"""

from __future__ import annotations

from app.permissions import Role, has_minimum_role

from .conftest import FIRM_A, auth_header


def _setup_firm(tc) -> None:
    tc.post("/api/v1/firms", json={"name": "Alpha CA"}, headers=auth_header())


def test_has_minimum_role_owner():
    assert has_minimum_role("owner", Role.OWNER) is True
    assert has_minimum_role("owner", Role.PARTNER) is True
    assert has_minimum_role("owner", Role.VIEWER) is True


def test_has_minimum_role_staff():
    assert has_minimum_role("staff", Role.STAFF) is True
    assert has_minimum_role("staff", Role.VIEWER) is True
    assert has_minimum_role("staff", Role.SENIOR) is False
    assert has_minimum_role("staff", Role.OWNER) is False


def test_has_minimum_role_viewer():
    assert has_minimum_role("viewer", Role.VIEWER) is True
    assert has_minimum_role("viewer", Role.STAFF) is False


def test_has_minimum_role_unknown():
    """Unknown roles should be denied everything."""
    assert has_minimum_role("unknown_role", Role.VIEWER) is False


def test_owner_can_update_firm(client) -> None:
    _setup_firm(client)
    resp = client.patch(
        "/api/v1/firms/me",
        json={"name": "Updated"},
        headers=auth_header(role="owner"),
    )
    assert resp.status_code == 200


def test_partner_cannot_update_firm(client) -> None:
    _setup_firm(client)
    resp = client.patch(
        "/api/v1/firms/me",
        json={"name": "Should Fail"},
        headers=auth_header(role="partner"),
    )
    assert resp.status_code == 403


def test_staff_cannot_update_firm(client) -> None:
    _setup_firm(client)
    resp = client.patch(
        "/api/v1/firms/me",
        json={"name": "Should Fail"},
        headers=auth_header(role="staff"),
    )
    assert resp.status_code == 403


def test_viewer_cannot_update_firm(client) -> None:
    _setup_firm(client)
    resp = client.patch(
        "/api/v1/firms/me",
        json={"name": "Should Fail"},
        headers=auth_header(role="viewer"),
    )
    assert resp.status_code == 403


def test_viewer_can_read_firm(client) -> None:
    _setup_firm(client)
    resp = client.get(
        "/api/v1/firms/me",
        headers=auth_header(role="viewer"),
    )
    assert resp.status_code == 200


def test_staff_can_create_client(client) -> None:
    _setup_firm(client)
    resp = client.post(
        "/api/v1/clients",
        json={"display_name": "Test Client"},
        headers=auth_header(role="staff"),
    )
    assert resp.status_code == 201
