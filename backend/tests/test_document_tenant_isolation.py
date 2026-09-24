"""Multi-tenant isolation tests for documents and evidence vault.

Verifies:
- Firm B cannot access, list, or download Firm A's uploaded documents.
- Firm B cannot upload documents linked to Firm A's clients.
"""

from __future__ import annotations

from .conftest import FIRM_A, FIRM_B, auth_header


def test_cross_tenant_document_access_blocked(client):
    # Firm A setup
    client.post("/api/v1/firms", json={"name": "Alpha CA"}, headers=auth_header(firm_id=FIRM_A))
    c_resp = client.post("/api/v1/clients", json={"display_name": "Alpha Traders"}, headers=auth_header(firm_id=FIRM_A))
    client_id_a = c_resp.json()["id"]

    files = {"file": ("alpha_secret.csv", b"InvoiceNo\nINV01\n", "text/csv")}
    data = {"client_id": client_id_a, "document_type": "purchase_register"}
    up_resp = client.post("/api/v1/documents", data=data, files=files, headers=auth_header(firm_id=FIRM_A))
    doc_id = up_resp.json()["document_id"]

    # Firm B setup
    firm_b_headers = auth_header(user_id="user-b", firm_id=FIRM_B, role="owner")
    client.post("/api/v1/firms", json={"name": "Bravo CA"}, headers=firm_b_headers)

    # 1. Firm B lists documents -> empty
    list_resp = client.get("/api/v1/documents", headers=firm_b_headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 0

    # 2. Firm B tries to get Firm A's document metadata -> 404
    meta_resp = client.get(f"/api/v1/documents/{doc_id}", headers=firm_b_headers)
    assert meta_resp.status_code == 404

    # 3. Firm B tries to download Firm A's document -> 404
    down_resp = client.get(f"/api/v1/documents/{doc_id}/download", headers=firm_b_headers)
    assert down_resp.status_code == 404

    # 4. Firm B tries to upload targeting Firm A's client_id -> 404
    files_b = {"file": ("intruder.csv", b"InvoiceNo\nINV99\n", "text/csv")}
    intrude_data = {"client_id": client_id_a, "document_type": "purchase_register"}
    intrude_resp = client.post("/api/v1/documents", data=intrude_data, files=files_b, headers=firm_b_headers)
    assert intrude_resp.status_code == 404
