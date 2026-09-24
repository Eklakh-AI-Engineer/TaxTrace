"""Shared test fixtures.

Provides an in-memory SQLite database with StaticPool, a FastAPI TestClient
with dependency overrides, and authentication helper utilities.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import Session, sessionmaker

import app.models  # Ensure all SQLAlchemy models are registered in metadata
from app.auth import AuthContext, create_access_token, get_auth_context
from app.database import Base, get_db
from app.main import app


# ---------------------------------------------------------------------------
# Auth helpers (importable constants)
# ---------------------------------------------------------------------------

FIRM_A = "firm-alpha"
FIRM_B = "firm-bravo"
USER_OWNER = "user-owner"
USER_STAFF = "user-staff"
USER_VIEWER = "user-viewer"


def dev_token(user_id: str = USER_OWNER, firm_id: str = FIRM_A, role: str = "owner") -> str:
    """Create a development-mode bearer token."""
    return f"dev.{user_id}.{firm_id}.{role}"


def auth_header(user_id: str = USER_OWNER, firm_id: str = FIRM_A, role: str = "owner") -> dict[str, str]:
    """Return an Authorization header dict for test requests."""
    return {"Authorization": f"Bearer {dev_token(user_id, firm_id, role)}"}


def make_auth_context(
    user_id: str = USER_OWNER,
    firm_id: str = FIRM_A,
    role: str = "owner",
) -> AuthContext:
    """Create an AuthContext for direct service-layer testing."""
    return AuthContext(
        user_id=user_id,
        firm_id=firm_id,
        role=role,
        request_id="test-request-id",
    )


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_engine():
    """Create a fresh in-memory SQLite engine per test using StaticPool.

    StaticPool ensures all sessions and connections share the same
    in-memory database instance in SQLite across threads and requests.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=pool.StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    """Yield a session bound to the test engine."""
    TestSessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=False, expire_on_commit=False)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# TestClient fixture with dependency overrides
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(db_engine):
    """Return a FastAPI TestClient wired to the test database.

    Overrides the ``get_db`` dependency so all requests use the
    in-memory test database.
    """
    TestSessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=False, expire_on_commit=False)

    def _override_get_db():
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as tc:
        yield tc
    app.dependency_overrides.clear()
