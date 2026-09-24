"""Tenant isolation tests.

Verifies the fundamental tenant boundary: data belonging to one firm
is invisible to another firm, at both the model/DB and API levels.
"""

from __future__ import annotations

from app.models import Client, Firm

from .conftest import FIRM_A, FIRM_B, auth_header


# ---------------------------------------------------------------------------
# Model-level isolation (direct DB)
# ---------------------------------------------------------------------------


def test_create_firm_and_client_with_same_tenant(db_session) -> None:
    firm = Firm(id="firm-a", name="Alpha CA", status="active", plan="starter")
    db_session.add(firm)
    db_session.commit()

    client = Client(
        id="client-a",
        firm_id="firm-a",
        tenant_id="firm-a",
        display_name="Alpha Traders",
        gstin="29ABCDE1234F1Z5",
        status="active",
    )
    db_session.add(client)
    db_session.commit()

    stored = db_session.query(Client).filter(Client.tenant_id == "firm-a").all()
    assert len(stored) == 1
    assert stored[0].display_name == "Alpha Traders"


def test_tenant_isolation_only_returns_current_tenant_records(db_session) -> None:
    db_session.add_all(
        [
            Firm(id="firm-a", name="Alpha CA", status="active", plan="starter"),
            Firm(id="firm-b", name="Bravo CA", status="active", plan="starter"),
            Client(id="client-a", firm_id="firm-a", tenant_id="firm-a", display_name="Alpha Traders", status="active"),
            Client(id="client-b", firm_id="firm-b", tenant_id="firm-b", display_name="Bravo Traders", status="active"),
        ]
    )
    db_session.commit()

    tenant_a_clients = db_session.query(Client).filter(Client.tenant_id == "firm-a").all()
    tenant_b_clients = db_session.query(Client).filter(Client.tenant_id == "firm-b").all()

    assert [c.id for c in tenant_a_clients] == ["client-a"]
    assert [c.id for c in tenant_b_clients] == ["client-b"]


# ---------------------------------------------------------------------------
# API-level isolation
# ---------------------------------------------------------------------------


def test_api_tenant_isolation_clients(client) -> None:
    """Firm A's clients must be invisible to Firm B via the API."""
    # Firm A creates a client.
    client.post("/api/v1/firms", json={"name": "Alpha CA"}, headers=auth_header(firm_id=FIRM_A))
    client.post(
        "/api/v1/clients",
        json={"display_name": "Alpha Secret Client"},
        headers=auth_header(firm_id=FIRM_A),
    )

    # Firm B creates its own context.
    firm_b_headers = auth_header(user_id="user-b", firm_id=FIRM_B, role="owner")
    client.post("/api/v1/firms", json={"name": "Bravo CA"}, headers=firm_b_headers)

    # Firm B lists clients — must not see Firm A's client.
    resp = client.get("/api/v1/clients", headers=firm_b_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    # Firm A still sees its own client.
    resp = client.get("/api/v1/clients", headers=auth_header(firm_id=FIRM_A))
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["display_name"] == "Alpha Secret Client"


def test_api_tenant_isolation_periods(client) -> None:
    """Firm B cannot access Firm A's periods."""
    # Firm A creates client + period.
    client.post("/api/v1/firms", json={"name": "Alpha CA"}, headers=auth_header(firm_id=FIRM_A))
    resp = client.post(
        "/api/v1/clients",
        json={"display_name": "Alpha Traders"},
        headers=auth_header(firm_id=FIRM_A),
    )
    client_id = resp.json()["id"]
    client.post(
        "/api/v1/periods",
        json={"client_id": client_id, "financial_year": "2025-26", "tax_period": "Apr-2025"},
        headers=auth_header(firm_id=FIRM_A),
    )

    # Firm B sees no periods.
    firm_b_headers = auth_header(user_id="user-b", firm_id=FIRM_B, role="owner")
    client.post("/api/v1/firms", json={"name": "Bravo CA"}, headers=firm_b_headers)

    resp = client.get("/api/v1/periods", headers=firm_b_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
