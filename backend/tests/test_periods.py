"""Period API tests.

Covers:
    - Create period → 201
    - Duplicate active period → 409
    - Period requires valid client in same tenant
    - List periods with client filter
    - Get period by ID
    - Update period status
    - Tenant isolation
"""

from __future__ import annotations

from .conftest import FIRM_A, FIRM_B, auth_header


def _setup_firm_and_client(tc) -> str:
    """Create firm + client and return client_id."""
    tc.post("/api/v1/firms", json={"name": "Alpha CA"}, headers=auth_header())
    resp = tc.post(
        "/api/v1/clients",
        json={"display_name": "Alpha Traders"},
        headers=auth_header(),
    )
    return resp.json()["id"]


def _create_period(tc, client_id: str, fy: str = "2025-26", tp: str = "Apr-2025", headers=None):
    return tc.post(
        "/api/v1/periods",
        json={
            "client_id": client_id,
            "financial_year": fy,
            "tax_period": tp,
        },
        headers=headers or auth_header(),
    )


def test_create_period(client) -> None:
    client_id = _setup_firm_and_client(client)
    resp = _create_period(client, client_id)
    assert resp.status_code == 201
    data = resp.json()
    assert data["client_id"] == client_id
    assert data["financial_year"] == "2025-26"
    assert data["tax_period"] == "Apr-2025"
    assert data["status"] == "open"


def test_duplicate_active_period_returns_409(client) -> None:
    client_id = _setup_firm_and_client(client)
    _create_period(client, client_id)
    resp = _create_period(client, client_id)
    assert resp.status_code == 409


def test_period_with_invalid_client_returns_404(client) -> None:
    client.post("/api/v1/firms", json={"name": "Alpha CA"}, headers=auth_header())
    resp = _create_period(client, "nonexistent-client")
    assert resp.status_code == 404


def test_period_with_other_tenant_client_returns_404(client) -> None:
    """Cannot create a period for another tenant's client."""
    # Firm A creates a client.
    client_id = _setup_firm_and_client(client)

    # Firm B tries to create a period for firm A's client.
    firm_b_headers = auth_header(user_id="user-b", firm_id=FIRM_B, role="owner")
    client.post("/api/v1/firms", json={"name": "Bravo CA"}, headers=firm_b_headers)

    resp = _create_period(client, client_id, headers=firm_b_headers)
    assert resp.status_code == 404


def test_list_periods(client) -> None:
    client_id = _setup_firm_and_client(client)
    _create_period(client, client_id, fy="2025-26", tp="Apr-2025")
    _create_period(client, client_id, fy="2025-26", tp="May-2025")

    resp = client.get("/api/v1/periods", headers=auth_header())
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_list_periods_with_client_filter(client) -> None:
    client_id_a = _setup_firm_and_client(client)

    # Create second client.
    resp = client.post(
        "/api/v1/clients",
        json={"display_name": "Beta Corp"},
        headers=auth_header(),
    )
    client_id_b = resp.json()["id"]

    _create_period(client, client_id_a, fy="2025-26", tp="Apr-2025")
    _create_period(client, client_id_b, fy="2025-26", tp="Apr-2025")

    resp = client.get(
        f"/api/v1/periods?client_id={client_id_a}",
        headers=auth_header(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["client_id"] == client_id_a


def test_get_period_by_id(client) -> None:
    client_id = _setup_firm_and_client(client)
    create_resp = _create_period(client, client_id)
    period_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/periods/{period_id}", headers=auth_header())
    assert resp.status_code == 200
    assert resp.json()["id"] == period_id


def test_update_period_status(client) -> None:
    client_id = _setup_firm_and_client(client)
    create_resp = _create_period(client, client_id)
    period_id = create_resp.json()["id"]

    resp = client.patch(
        f"/api/v1/periods/{period_id}",
        json={"status": "closed"},
        headers=auth_header(),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"
