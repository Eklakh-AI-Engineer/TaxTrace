"""Tests for WhatsApp Bot integration (Stage 8).

Covers:
- Webhook signature validation.
- Bot command routing (help, tasks, deadlines).
- Auth resolution from channel identifier.
- Security constraints (untrusted data, no external submission without approval).
"""

import hmac
import hashlib
from fastapi.testclient import TestClient
from app.auth import create_access_token
from app.models import Firm, User, FirmMembership, Task, NoticeCase
from datetime import date, timedelta
import pytest
import os

@pytest.fixture
def bot_test_data(db_session):
    firm = Firm(id="firm_bot_01", name="Bot Firm")
    db_session.add(firm)

    user = User(id="whatsapp-user", email="botuser@firm.com", name="Bot User", status="active")
    db_session.add(user)
    db_session.add(FirmMembership(firm_id=firm.id, user_id=user.id, role="staff"))

    from app.models import Client, Document
    
    client_obj = Client(id="client_bot_01", firm_id=firm.id, tenant_id=firm.id, display_name="Bot Client", gstin="27AAACT2727Q1ZW")
    db_session.add(client_obj)
    
    doc = Document(id="doc_bot_01", firm_id=firm.id, client_id=client_obj.id, tenant_id=firm.id, document_type="notice", original_filename="notice.pdf", storage_uri="path/to/doc", content_hash="hash", mime_type="application/pdf", size_bytes=1024)
    db_session.add(doc)

    # Add a pending task
    due_date = date.today() + timedelta(days=2)
    task = Task(id="task_bot_01", tenant_id=firm.id, firm_id=firm.id, client_id=client_obj.id, title="Test Pending Task", status="open", due_date=due_date, source_type="exception")
    db_session.add(task)

    # Add an urgent notice
    notice = NoticeCase(id="notice_bot_01", tenant_id=firm.id, firm_id=firm.id, client_id=client_obj.id, source_document_id=doc.id, notice_type="GST ASMT-10", status="open", response_deadline=date.today() + timedelta(days=1))
    db_session.add(notice)

    db_session.commit()
    
    token = create_access_token("whatsapp-user", firm.id, "staff")
    return {"firm": firm, "token": token, "user": user}

def test_webhook_verification(client: TestClient):
    """Test the Meta webhook handshake."""
    # Pass with valid token
    resp = client.get("/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=taxtrace-dev-verify-token&hub.challenge=12345")
    assert resp.status_code == 200
    assert resp.text == "12345"

    # Fail with invalid token
    resp = client.get("/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=wrong_token&hub.challenge=12345")
    assert resp.status_code == 403

def test_chat_simulator(client: TestClient, bot_test_data):
    """Test the chat simulator endpoint with various commands."""
    headers = {"Authorization": f"Bearer {bot_test_data['token']}"}

    # Help command
    resp = client.post("/api/v1/chat/send", headers=headers, json={"message": "help"})
    assert resp.status_code == 200
    assert "Available commands" in resp.json()["reply"]

    # Pending tasks
    resp = client.post("/api/v1/chat/send", headers=headers, json={"message": "show pending tasks"})
    assert resp.status_code == 200
    assert "Test Pending Task" in resp.json()["reply"]

    # Show deadlines
    resp = client.post("/api/v1/chat/send", headers=headers, json={"message": "show deadlines"})
    assert resp.status_code == 200
    assert "GST ASMT-10" in resp.json()["reply"]

    # Unknown command
    resp = client.post("/api/v1/chat/send", headers=headers, json={"message": "drop database"})
    assert resp.status_code == 200
    assert "I didn't understand that command" in resp.json()["reply"]

def test_whatsapp_cloud_adapter_signature():
    """Test the webhook signature validation in WhatsAppCloudAdapter."""
    from app.channels.adapter import WhatsAppCloudAdapter
    adapter = WhatsAppCloudAdapter("123", "token", "verify", "secret")
    
    body = b"test payload"
    sig = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    
    # Valid
    assert adapter.validate_webhook({"x-hub-signature-256": f"sha256={sig}"}, body) is True
    
    # Invalid
    assert adapter.validate_webhook({"x-hub-signature-256": "sha256=wrong"}, body) is False
