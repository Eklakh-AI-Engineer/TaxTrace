"""Tests for Task Tenant Isolation and Cross-Tenant Security.

Verifies SECURITY.md Section 3:
- Firm A cannot view or list Firm B tasks.
- Firm A cannot modify or delete Firm B tasks.
- Firm A cannot create a task linked to Firm B clients or exceptions.
- Firm A cannot assign a task to a user belonging to Firm B.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth import create_access_token
from app.models import Client, ExceptionRecord, Firm, FirmMembership, Task, User


@pytest.fixture
def two_tenants(db_session):
    # Firm A
    firm_a = Firm(id="firm_ta_01", name="Firm Alpha")
    user_a = User(id="user_ta_01", email="alpha@firm.com", name="Alpha Staff", status="active")
    client_a = Client(id="client_ta_01", firm_id=firm_a.id, tenant_id=firm_a.id, display_name="Alpha Client")
    db_session.add_all([firm_a, user_a, client_a])
    db_session.add(FirmMembership(firm_id=firm_a.id, user_id=user_a.id, role="staff"))

    # Firm B
    firm_b = Firm(id="firm_tb_01", name="Firm Beta")
    user_b = User(id="user_tb_01", email="beta@firm.com", name="Beta Staff", status="active")
    client_b = Client(id="client_tb_01", firm_id=firm_b.id, tenant_id=firm_b.id, display_name="Beta Client")
    task_b = Task(
        id="task_tb_01",
        firm_id=firm_b.id,
        tenant_id=firm_b.id,
        client_id=client_b.id,
        title="Beta Confidential Task",
        status="open",
        owner_id=user_b.id,
    )
    db_session.add_all([firm_b, user_b, client_b, task_b])
    db_session.add(FirmMembership(firm_id=firm_b.id, user_id=user_b.id, role="staff"))

    db_session.commit()

    token_a = create_access_token("user_ta_01", firm_a.id, "staff")
    token_b = create_access_token("user_tb_01", firm_b.id, "staff")

    return {
        "token_a": token_a,
        "token_b": token_b,
        "task_b": task_b,
        "client_b": client_b,
        "user_b": user_b,
    }


def test_cross_tenant_task_access_blocked(client: TestClient, two_tenants):
    headers_a = {"Authorization": f"Bearer {two_tenants['token_a']}"}
    task_b_id = two_tenants["task_b"].id

    # 1. Firm A trying to GET Firm B's task directly -> 404
    resp = client.get(f"/api/v1/tasks/{task_b_id}", headers=headers_a)
    assert resp.status_code == 404

    # 2. Firm A trying to PATCH Firm B's task -> 404
    patch_resp = client.patch(
        f"/api/v1/tasks/{task_b_id}",
        headers=headers_a,
        json={"title": "Hacked Title"},
    )
    assert patch_resp.status_code == 404

    # 3. Firm A trying to list tasks -> should never include Firm B's task
    list_resp = client.get("/api/v1/tasks", headers=headers_a)
    assert list_resp.status_code == 200
    task_ids = [t["id"] for t in list_resp.json()["items"]]
    assert task_b_id not in task_ids


def test_cross_tenant_linkage_prevented(client: TestClient, two_tenants):
    headers_a = {"Authorization": f"Bearer {two_tenants['token_a']}"}

    # Firm A trying to link Firm B's client -> 404
    resp = client.post(
        "/api/v1/tasks",
        headers=headers_a,
        json={
            "title": "Cross-tenant task attempt",
            "client_id": two_tenants["client_b"].id,
        },
    )
    assert resp.status_code == 404
    assert "Linked client not found" in resp.json()["error"]["message"]

    # Firm A trying to assign task to Firm B's user -> 400
    resp_assign = client.post(
        "/api/v1/tasks",
        headers=headers_a,
        json={
            "title": "Cross-tenant assignment attempt",
            "assigned_to": two_tenants["user_b"].id,
        },
    )
    assert resp_assign.status_code == 400
    assert "not a member of this firm" in resp_assign.json()["error"]["message"]
