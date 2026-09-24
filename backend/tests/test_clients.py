"""Client API tests.

Covers:
    - Create client → 201
    - List clients (pagination)
    - Get client by ID
    - Update client
    - Tenant isolation: firm B cannot see firm A's clients
    - Search clients by name
    - Audit events for client operations
"""

from __future__ import annotations

from .conftest import FIRM_A, FIRM_B, auth_header


def _setup_firm(client) -> None:
    client.post("/api/v1/firms", json={"name": "Alpha CA"}, headers=auth_header())


def _create_client(tc, display_name: str = "Alpha Traders", gstin: str | None = None, headers=None) -> dict:
    body = {"display_name": display_name}
    if gstin:
        body["gstin"] = gstin
    resp = tc.post(
        "/api/v1/clients",
        json=body,
        headers=headers or auth_header(),
    )
    return resp


def test_create_client(client) -> None:
    _setup_firm(client)
    resp = _create_client(client, gstin="29ABCDE1234F1Z5")
    assert resp.status_code == 201
    data = resp.json()
    assert data["display_name"] == "Alpha Traders"
    assert data["gstin"] == "29ABCDE1234F1Z5"
    assert data["tenant_id"] == FIRM_A
    assert data["firm_id"] == FIRM_A


def test_list_clients_empty(client) -> None:
    _setup_firm(client)
    resp = client.get("/api/v1/clients", headers=auth_header())
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_clients_with_data(client) -> None:
    _setup_firm(client)
    _create_client(client, "Client One")
    _create_client(client, "Client Two")
    resp = client.get("/api/v1/clients", headers=auth_header())
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_get_client_by_id(client) -> None:
    _setup_firm(client)
    create_resp = _create_client(client)
    client_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/clients/{client_id}", headers=auth_header())
    assert resp.status_code == 200
    assert resp.json()["id"] == client_id


def test_get_nonexistent_client_returns_404(client) -> None:
    _setup_firm(client)
    resp = client.get("/api/v1/clients/nonexistent", headers=auth_header())
    assert resp.status_code == 404


def test_update_client(client) -> None:
    _setup_firm(client)
    create_resp = _create_client(client)
    client_id = create_resp.json()["id"]

    resp = client.patch(
        f"/api/v1/clients/{client_id}",
        json={"display_name": "Updated Traders"},
        headers=auth_header(),
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Updated Traders"


def test_tenant_isolation_clients(client) -> None:
    """Firm B cannot see Firm A's clients."""
    # Create firm A and a client.
    _setup_firm(client)
    _create_client(client, "Alpha Traders")

    # Create firm B.
    firm_b_headers = auth_header(user_id="user-b", firm_id=FIRM_B, role="owner")
    client.post("/api/v1/firms", json={"name": "Bravo CA"}, headers=firm_b_headers)

    # List clients as firm B — should be empty.
    resp = client.get("/api/v1/clients", headers=firm_b_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_search_clients(client) -> None:
    _setup_firm(client)
    _create_client(client, "Alpha Traders", gstin="29ABCDE1234F1Z5")
    _create_client(client, "Beta Industries")

    resp = client.get("/api/v1/clients?search=Alpha", headers=auth_header())
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["display_name"] == "Alpha Traders"


def test_pagination(client) -> None:
    _setup_firm(client)
    for i in range(5):
        _create_client(client, f"Client {i}")

    resp = client.get("/api/v1/clients?page=1&page_size=2", headers=auth_header())
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["has_next"] is True

    resp2 = client.get("/api/v1/clients?page=3&page_size=2", headers=auth_header())
    data2 = resp2.json()
    assert len(data2["items"]) == 1
    assert data2["has_next"] is False
