"""Multi-tenant isolation tests for Notices, Drafts, and AI Explanations.

Verifies:
- Firm B cannot access Firm A's NoticeCase or extracted facts.
- Firm B cannot view or approve Firm A's generated response drafts.
"""

from __future__ import annotations

from .conftest import FIRM_A, FIRM_B, auth_header


def test_cross_tenant_notice_and_draft_isolation(client):
    # Setup Firm A
    client.post("/api/v1/firms", json={"name": "Alpha CA"}, headers=auth_header(firm_id=FIRM_A))
    c_resp = client.post("/api/v1/clients", json={"display_name": "Alpha Traders"}, headers=auth_header(firm_id=FIRM_A))
    client_id_a = c_resp.json()["id"]

    notice_bytes = b"FORM GST DRC-01\nREF: ZA2901\nDemand: 25000\n"
    files = {"file": ("notice.pdf", notice_bytes, "application/pdf")}
    up_resp = client.post("/api/v1/notices", data={"client_id": client_id_a}, files=files, headers=auth_header(firm_id=FIRM_A))
    notice_id_a = up_resp.json()["id"]

    # Generate draft for Firm A
    d_resp = client.post(f"/api/v1/notices/{notice_id_a}/draft", json={}, headers=auth_header(firm_id=FIRM_A))
    draft_id_a = d_resp.json()["id"]

    # Setup Firm B
    firm_b_headers = auth_header(user_id="user-b", firm_id=FIRM_B, role="partner")
    client.post("/api/v1/firms", json={"name": "Bravo CA"}, headers=firm_b_headers)

    # 1. Firm B cannot get Firm A's notice case -> 404
    get_n = client.get(f"/api/v1/notices/{notice_id_a}", headers=firm_b_headers)
    assert get_n.status_code == 404

    # 2. Firm B cannot extract facts from Firm A's notice -> 404
    ext_n = client.post(f"/api/v1/notices/{notice_id_a}/extract", headers=firm_b_headers)
    assert ext_n.status_code == 404

    # 3. Firm B cannot get Firm A's draft -> 404
    get_d = client.get(f"/api/v1/drafts/{draft_id_a}", headers=firm_b_headers)
    assert get_d.status_code == 404

    # 4. Firm B cannot approve Firm A's draft -> 404
    app_d = client.post(f"/api/v1/drafts/{draft_id_a}/approve", json={"comment": "Intruder approval"}, headers=firm_b_headers)
    assert app_d.status_code == 404
