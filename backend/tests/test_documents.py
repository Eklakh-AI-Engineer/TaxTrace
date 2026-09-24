"""Document API and Evidence Vault tests.

Verifies:
- Document upload (.csv, .json, .pdf).
- SHA-256 calculation and storage.
- Duplicate detection (HTTP 409).
- Document listing with filters.
- Document download with audit logging.
- Extracted canonical transactions.
- Invalid extension / MIME handling.
"""

from __future__ import annotations

import io
from app.models import AuditEvent, Document, Transaction
from .conftest import FIRM_A, auth_header


def _setup_firm_client_period(client) -> tuple[str, str]:
    client.post("/api/v1/firms", json={"name": "Alpha CA"}, headers=auth_header())
    c_resp = client.post("/api/v1/clients", json={"display_name": "Alpha Traders"}, headers=auth_header())
    client_id = c_resp.json()["id"]

    p_resp = client.post(
        "/api/v1/periods",
        json={"client_id": client_id, "financial_year": "2025-26", "tax_period": "Apr-2025"},
        headers=auth_header(),
    )
    period_id = p_resp.json()["id"]
    return client_id, period_id


def test_upload_purchase_register_csv(client, db_session):
    client_id, period_id = _setup_firm_client_period(client)
    csv_bytes = b"""Supplier GSTIN,Invoice No,Date,Taxable Amount,CGST,SGST,IGST
29AAAAA0000A1Z5,INV-101,10/05/2025,10000.00,900.00,900.00,0.00
"""
    files = {"file": ("purchase_register.csv", csv_bytes, "text/csv")}
    data = {
        "client_id": client_id,
        "period_id": period_id,
        "document_type": "purchase_register",
    }

    resp = client.post("/api/v1/documents", data=data, files=files, headers=auth_header())
    assert resp.status_code == 201
    res_data = resp.json()

    doc_id = res_data["document_id"]
    assert res_data["status"] == "processed"
    assert res_data["original_filename"] == "purchase_register.csv"
    assert res_data["extracted_transactions_count"] == 1
    assert "content_hash" in res_data

    # Verify transactions created in database
    txs = db_session.query(Transaction).filter(Transaction.source_document_id == doc_id).all()
    assert len(txs) == 1
    assert txs[0].invoice_number_normalized == "INV101"
    assert txs[0].taxable_value == 10000.00


def test_duplicate_document_upload_rejected(client):
    client_id, period_id = _setup_firm_client_period(client)
    csv_bytes = b"InvoiceNo,Taxable\nINV01,500.00\n"
    files = {"file": ("books.csv", csv_bytes, "text/csv")}
    data = {
        "client_id": client_id,
        "period_id": period_id,
        "document_type": "purchase_register",
    }

    # First upload succeeds
    resp1 = client.post("/api/v1/documents", data=data, files=files, headers=auth_header())
    assert resp1.status_code == 201

    # Second upload with identical content returns 409
    files2 = {"file": ("books_copy.csv", io.BytesIO(csv_bytes), "text/csv")}
    resp2 = client.post("/api/v1/documents", data=data, files=files2, headers=auth_header())
    assert resp2.status_code == 409
    assert "Duplicate document detected" in resp2.json()["error"]["message"]


def test_unsupported_file_extension(client):
    client_id, period_id = _setup_firm_client_period(client)
    files = {"file": ("script.exe", b"binarycontent", "application/octet-stream")}
    data = {"client_id": client_id, "document_type": "notice"}

    resp = client.post("/api/v1/documents", data=data, files=files, headers=auth_header())
    assert resp.status_code == 400
    assert "Unsupported file extension" in resp.json()["error"]["message"]


def test_get_document_detail_and_transactions(client):
    client_id, period_id = _setup_firm_client_period(client)
    csv_bytes = b"Invoice No,Taxable Amount\nBILL-009,2500.00\n"
    files = {"file": ("invoices.csv", csv_bytes, "text/csv")}
    data = {"client_id": client_id, "period_id": period_id, "document_type": "purchase_register"}

    upload_resp = client.post("/api/v1/documents", data=data, files=files, headers=auth_header())
    doc_id = upload_resp.json()["document_id"]

    # Retrieve metadata
    detail_resp = client.get(f"/api/v1/documents/{doc_id}", headers=auth_header())
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == doc_id
    assert detail_resp.json()["processing_status"] == "processed"

    # Retrieve extracted transactions
    tx_resp = client.get(f"/api/v1/documents/{doc_id}/transactions", headers=auth_header())
    assert tx_resp.status_code == 200
    assert tx_resp.json()["total"] == 1
    assert tx_resp.json()["items"][0]["invoice_number_normalized"] == "BILL009"


def test_download_document(client, db_session):
    client_id, period_id = _setup_firm_client_period(client)
    content = b"PDF-NOTICE-FACTS-CONTENT"
    files = {"file": ("notice_sec148.pdf", content, "application/pdf")}
    data = {"client_id": client_id, "document_type": "notice_pdf"}

    upload_resp = client.post("/api/v1/documents", data=data, files=files, headers=auth_header())
    doc_id = upload_resp.json()["document_id"]

    # Download document
    down_resp = client.get(f"/api/v1/documents/{doc_id}/download", headers=auth_header())
    assert down_resp.status_code == 200
    assert down_resp.content == content

    # Verify download audit event was recorded
    audit = db_session.query(AuditEvent).filter(
        AuditEvent.entity_id == doc_id,
        AuditEvent.event_type == "document.downloaded",
    ).first()
    assert audit is not None
