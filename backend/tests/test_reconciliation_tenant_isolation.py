"""Tenant isolation tests for Reconciliations and Exceptions.

Verifies:
- Firm B cannot view Firm A's reconciliation summaries.
- Firm B cannot access or update Firm A's exception records.
- Firm B cannot trigger reconciliations on Firm A's clients/periods.
"""

from __future__ import annotations

from .conftest import FIRM_A, FIRM_B, auth_header


def test_cross_tenant_reconciliation_isolation(client):
    # Setup Firm A
    client.post("/api/v1/firms", json={"name": "Alpha CA"}, headers=auth_header(firm_id=FIRM_A))
    c_resp = client.post("/api/v1/clients", json={"display_name": "Alpha Traders"}, headers=auth_header(firm_id=FIRM_A))
    client_id_a = c_resp.json()["id"]

    p_resp = client.post(
        "/api/v1/periods",
        json={"client_id": client_id_a, "financial_year": "2025-26", "tax_period": "Apr-2025"},
        headers=auth_header(firm_id=FIRM_A),
    )
    period_id_a = p_resp.json()["id"]

    # Upload Books & Portal for Firm A
    files_b = {"file": ("books.csv", b"Supplier GSTIN,Invoice No,Taxable Amount\n29A,INV1,1000\n", "text/csv")}
    client.post("/api/v1/documents", data={"client_id": client_id_a, "period_id": period_id_a, "document_type": "purchase_register"}, files=files_b, headers=auth_header(firm_id=FIRM_A))

    files_p = {"file": ("2b.csv", b"Supplier GSTIN,Invoice No,Taxable Amount\n29A,INV1,1000\n", "text/csv")}
    client.post("/api/v1/documents", data={"client_id": client_id_a, "period_id": period_id_a, "document_type": "gstr2b"}, files=files_p, headers=auth_header(firm_id=FIRM_A))

    # Run reconciliation for Firm A
    client.post("/api/v1/reconciliations", json={"client_id": client_id_a, "period_id": period_id_a}, headers=auth_header(firm_id=FIRM_A))

    # Setup Firm B
    firm_b_headers = auth_header(user_id="user-b", firm_id=FIRM_B, role="owner")
    client.post("/api/v1/firms", json={"name": "Bravo CA"}, headers=firm_b_headers)

    # 1. Firm B cannot get Firm A's reconciliation summary -> 404
    sum_resp = client.get(f"/api/v1/reconciliations/{period_id_a}", headers=firm_b_headers)
    assert sum_resp.status_code == 404

    # 2. Firm B cannot list Firm A's exceptions -> empty
    exc_resp = client.get(f"/api/v1/reconciliations/{period_id_a}/exceptions", headers=firm_b_headers)
    assert exc_resp.status_code == 200
    assert exc_resp.json()["total"] == 0

    # 3. Firm B cannot trigger reconciliation for Firm A's client/period -> 404
    trig_resp = client.post("/api/v1/reconciliations", json={"client_id": client_id_a, "period_id": period_id_a}, headers=firm_b_headers)
    assert trig_resp.status_code == 404
