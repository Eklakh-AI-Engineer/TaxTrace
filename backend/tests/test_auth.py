"""Authentication tests.

Covers:
    - Missing credentials → 401
    - Invalid dev token format → 401
    - Valid dev token → 200
    - JWT token creation and verification
    - Expired JWT → 401
    - users/me endpoint returns correct identity
"""

from __future__ import annotations

from datetime import timedelta

from app.auth import create_access_token

from .conftest import FIRM_A, USER_OWNER, auth_header


def test_missing_auth_returns_401(client) -> None:
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_invalid_dev_token_returns_401(client) -> None:
    resp = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer dev.only-two-parts"},
    )
    assert resp.status_code == 401


def test_valid_dev_token_returns_user(client) -> None:
    resp = client.get("/api/v1/users/me", headers=auth_header())
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == USER_OWNER
    assert data["firm_id"] == FIRM_A
    assert data["role"] == "owner"
    assert data["tenant_id"] == FIRM_A


def test_jwt_token_works(client) -> None:
    token = create_access_token(
        user_id="jwt-user",
        firm_id="jwt-firm",
        role="partner",
    )
    resp = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "jwt-user"
    assert data["firm_id"] == "jwt-firm"
    assert data["role"] == "partner"


def test_expired_jwt_returns_401(client) -> None:
    token = create_access_token(
        user_id="expired-user",
        firm_id="expired-firm",
        role="staff",
        expires_delta=timedelta(seconds=-10),
    )
    resp = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401


def test_request_id_header_is_returned(client) -> None:
    resp = client.get("/api/v1/users/me", headers=auth_header())
    assert "X-Request-ID" in resp.headers


def test_custom_request_id_is_preserved(client) -> None:
    headers = {**auth_header(), "X-Request-ID": "custom-req-123"}
    resp = client.get("/api/v1/users/me", headers=headers)
    assert resp.headers["X-Request-ID"] == "custom-req-123"
