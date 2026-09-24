"""Tests for Partner Monitoring Dashboard API (Stage 5).

Covers:
- Access control: Role.SENIOR or higher can access /dashboard/overview. Role.STAFF is forbidden.
- Metrics calculation: Open/in-progress/blocked/completed task counts, overdue task items.
- Unresolved exception metrics.
- Active notice cases and urgent deadline countdowns.
"""

from __future__ import annotations

from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

from app.auth import create_access_token
from app.models import Client, ExceptionRecord, Firm, FirmMembership, NoticeCase, Task, User


@pytest.fixture
def dashboard_fixture(db_session):
    firm = Firm(id="firm_dash_01", name="Partner CA Firm")
    db_session.add(firm)

    senior = User(id="user_dash_senior", email="partner@dash.com", name="Partner User", status="active")
    staff = User(id="user_dash_staff", email="staff@dash.com", name="Staff User", status="active")
    db_session.add_all([senior, staff])

    db_session.add(FirmMembership(firm_id=firm.id, user_id=senior.id, role="senior"))
    db_session.add(FirmMembership(firm_id=firm.id, user_id=staff.id, role="staff"))

    # 1. Tasks: 1 overdue open, 1 normal open, 1 completed
    yesterday = date.today() - timedelta(days=2)
    tomorrow = date.today() + timedelta(days=2)

    t1 = Task(firm_id=firm.id, tenant_id=firm.id, title="Overdue Item", status="open", due_date=yesterday)
    t2 = Task(firm_id=firm.id, tenant_id=firm.id, title="Normal Item", status="open", due_date=tomorrow)
    t3 = Task(firm_id=firm.id, tenant_id=firm.id, title="Done Item", status="completed")
    db_session.add_all([t1, t2, t3])

    # 2. Exceptions: 1 open, 1 resolved
    e1 = ExceptionRecord(
        firm_id=firm.id,
        tenant_id=firm.id,
        period_id="period_dash_01",
        type="VALUE_MISMATCH",
        severity="medium",
        status="open",
    )
    e2 = ExceptionRecord(
        firm_id=firm.id,
        tenant_id=firm.id,
        period_id="period_dash_01",
        type="VALUE_MISMATCH",
        severity="medium",
        status="resolved",
    )
    db_session.add_all([e1, e2])

    # 3. Notice: 1 active notice due in 4 days
    n1 = NoticeCase(
        id="notice_dash_01",
        firm_id=firm.id,
        tenant_id=firm.id,
        client_id="client_dash_01",
        source_document_id="doc_dash_01",
        notice_type="GST_DRC_01",
        status="received",
        response_deadline=date.today() + timedelta(days=4),
    )
    db_session.add(n1)

    db_session.commit()

    return {
        "token_senior": create_access_token("user_dash_senior", firm.id, "senior"),
        "token_staff": create_access_token("user_dash_staff", firm.id, "staff"),
        "firm": firm,
    }


def test_dashboard_access_control(client: TestClient, dashboard_fixture):
    headers_staff = {"Authorization": f"Bearer {dashboard_fixture['token_staff']}"}
    headers_senior = {"Authorization": f"Bearer {dashboard_fixture['token_senior']}"}

    # Staff forbidden -> 403
    resp_staff = client.get("/api/v1/dashboard/overview", headers=headers_staff)
    assert resp_staff.status_code == 403

    # Senior allowed -> 200
    resp_senior = client.get("/api/v1/dashboard/overview", headers=headers_senior)
    assert resp_senior.status_code == 200


def test_dashboard_metrics(client: TestClient, dashboard_fixture):
    headers_senior = {"Authorization": f"Bearer {dashboard_fixture['token_senior']}"}

    resp = client.get("/api/v1/dashboard/overview", headers=headers_senior)
    assert resp.status_code == 200
    data = resp.json()

    # Tasks
    tasks = data["tasks"]
    assert tasks["total_open"] == 2
    assert tasks["completed"] == 1
    assert tasks["overdue"] == 1

    # Overdue items list
    assert len(data["overdue_task_items"]) == 1
    assert data["overdue_task_items"][0]["title"] == "Overdue Item"

    # Exceptions
    assert data["exceptions"]["total_unresolved"] == 1
    assert data["exceptions"]["open"] == 1

    # Notices
    assert data["notices"]["total_active"] == 1
    assert data["notices"]["urgent_deadlines_within_7_days"] == 1
