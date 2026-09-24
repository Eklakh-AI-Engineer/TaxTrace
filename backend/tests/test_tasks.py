"""Tests for Task Management and Communication Drafting (Stage 5).

Covers:
- Task creation with assigned_to, due_date, client link.
- Task status lifecycle: open -> in_progress -> completed.
- Task filtering by status, overdue, and assignee.
- Reassigning tasks with firm member validation.
- Deleting tasks (requires Senior role).
- Communication drafting for missing invoice follow-up (Email & WhatsApp).
"""

from __future__ import annotations

from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

from app.auth import create_access_token
from app.models import Client, ExceptionRecord, Firm, FirmMembership, Task, User


@pytest.fixture
def firm_and_members(db_session):
    firm = Firm(id="firm_stage5_01", name="Stage5 Accounting")
    db_session.add(firm)

    # Owner
    owner = User(id="user_owner_01", email="owner@stage5.com", name="Partner CA", status="active")
    db_session.add(owner)
    db_session.add(FirmMembership(firm_id=firm.id, user_id=owner.id, role="owner"))

    # Senior
    senior = User(id="user_senior_01", email="senior@stage5.com", name="Senior Associate", status="active")
    db_session.add(senior)
    db_session.add(FirmMembership(firm_id=firm.id, user_id=senior.id, role="senior"))

    # Staff
    staff = User(id="user_staff_01", email="staff@stage5.com", name="Article Clerk", status="active")
    db_session.add(staff)
    db_session.add(FirmMembership(firm_id=firm.id, user_id=staff.id, role="staff"))

    # Client
    client = Client(id="client_s5_01", firm_id=firm.id, tenant_id=firm.id, display_name="Tata Steel Ltd", gstin="27AAACT2727Q1ZW")
    db_session.add(client)

    # Exception
    exc = ExceptionRecord(
        id="exc_s5_01",
        firm_id=firm.id,
        tenant_id=firm.id,
        period_id="period_s5_01",
        type="MISSING_IN_2B",
        severity="medium",
        status="open",
        reason_code="RULE_MISSING_IN_2B",
        explanation="Invoice INV-9901 present in Books but missing from GSTR-2B filing.",
    )
    db_session.add(exc)

    db_session.commit()

    tokens = {
        "owner": create_access_token("user_owner_01", firm.id, "owner"),
        "senior": create_access_token("user_senior_01", firm.id, "senior"),
        "staff": create_access_token("user_staff_01", firm.id, "staff"),
    }

    return {"firm": firm, "tokens": tokens, "client": client, "exception": exc}


def test_task_create_and_lifecycle(client: TestClient, firm_and_members):
    headers_staff = {"Authorization": f"Bearer {firm_and_members['tokens']['staff']}"}

    # 1. Create Task
    due_date = (date.today() + timedelta(days=3)).isoformat()
    resp = client.post(
        "/api/v1/tasks",
        headers=headers_staff,
        json={
            "title": "Follow up with vendor for missing INV-9901",
            "description": "Invoice of ₹10,000 missing in GSTR-2B",
            "client_id": firm_and_members["client"].id,
            "exception_id": firm_and_members["exception"].id,
            "assigned_to": "user_staff_01",
            "due_date": due_date,
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    task_id = data["id"]
    assert data["status"] == "open"
    assert data["owner_id"] == "user_staff_01"
    assert data["client_id"] == firm_and_members["client"].id
    assert data["exception_id"] == firm_and_members["exception"].id

    # 2. Get Task details
    get_resp = client.get(f"/api/v1/tasks/{task_id}", headers=headers_staff)
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Follow up with vendor for missing INV-9901"

    # 3. Update status to in_progress
    patch_resp = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers_staff,
        json={"status": "in_progress"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "in_progress"

    # 4. Reassign to senior
    reassign_resp = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers_staff,
        json={"assigned_to": "user_senior_01", "status": "completed"},
    )
    assert reassign_resp.status_code == 200
    assert reassign_resp.json()["owner_id"] == "user_senior_01"
    assert reassign_resp.json()["status"] == "completed"


def test_task_filters_and_overdue(client: TestClient, firm_and_members):
    headers = {"Authorization": f"Bearer {firm_and_members['tokens']['staff']}"}

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    future = (date.today() + timedelta(days=5)).isoformat()

    # Create an overdue open task
    client.post(
        "/api/v1/tasks",
        headers=headers,
        json={
            "title": "Overdue reconciliation query",
            "due_date": yesterday,
            "assigned_to": "user_staff_01",
        },
    )

    # Create a future task
    client.post(
        "/api/v1/tasks",
        headers=headers,
        json={
            "title": "Future audit review",
            "due_date": future,
            "assigned_to": "user_senior_01",
        },
    )

    # Filter overdue only
    resp = client.get("/api/v1/tasks?overdue_only=true", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["status"] in ["open", "in_progress", "blocked"]
        assert item["due_date"] < date.today().isoformat()

    # Filter by assignee
    resp_senior = client.get("/api/v1/tasks?assigned_to=user_senior_01", headers=headers)
    assert resp_senior.status_code == 200
    for item in resp_senior.json()["items"]:
        assert item["owner_id"] == "user_senior_01"


def test_task_delete_role_permissions(client: TestClient, firm_and_members):
    headers_staff = {"Authorization": f"Bearer {firm_and_members['tokens']['staff']}"}
    headers_senior = {"Authorization": f"Bearer {firm_and_members['tokens']['senior']}"}

    # Create a task
    resp = client.post(
        "/api/v1/tasks",
        headers=headers_staff,
        json={"title": "Task to delete"},
    )
    task_id = resp.json()["id"]

    # Staff trying to delete -> 403 Forbidden
    del_staff = client.delete(f"/api/v1/tasks/{task_id}", headers=headers_staff)
    assert del_staff.status_code == 403

    # Senior trying to delete -> 204 No Content
    del_senior = client.delete(f"/api/v1/tasks/{task_id}", headers=headers_senior)
    assert del_senior.status_code == 204

    # Verify 404
    get_del = client.get(f"/api/v1/tasks/{task_id}", headers=headers_senior)
    assert get_del.status_code == 404


def test_vendor_message_drafting(client: TestClient, firm_and_members):
    headers = {"Authorization": f"Bearer {firm_and_members['tokens']['staff']}"}

    # Create task linked to exception
    resp = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={
            "title": "Vendor ITC clarification for INV-9901",
            "exception_id": firm_and_members["exception"].id,
        },
    )
    task_id = resp.json()["id"]

    # Generate Email draft
    email_resp = client.post(
        f"/api/v1/tasks/{task_id}/draft-message",
        headers=headers,
        json={"channel": "email", "recipient_type": "vendor"},
    )
    assert email_resp.status_code == 200
    data = email_resp.json()
    assert data["task_id"] == task_id
    assert data["channel"] == "email"
    assert data["subject"] is not None
    assert "INV-9901" in data["message_body"]

    # Generate WhatsApp draft
    wa_resp = client.post(
        f"/api/v1/tasks/{task_id}/draft-message",
        headers=headers,
        json={"channel": "whatsapp", "recipient_type": "vendor"},
    )
    assert wa_resp.status_code == 200
    wa_data = wa_resp.json()
    assert wa_data["channel"] == "whatsapp"
    assert "INV-9901" in wa_data["message_body"]
