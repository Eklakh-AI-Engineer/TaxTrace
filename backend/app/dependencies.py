"""Shared FastAPI dependencies.

This module re-exports the primary auth dependency and provides
utility functions for tenant-scoped database access.

Legacy tenant-header dependencies are retained for backward
compatibility with existing tests but new code should use
``get_auth_context`` from ``app.auth``.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context  # noqa: F401 — re-export


def tenant_scope_query(db: Session, model, tenant_id: str):
    """Return a query filtered by tenant_id.

    Provides a reusable base query that enforces tenant isolation
    at the repository level.
    """
    return db.query(model).filter(model.tenant_id == tenant_id)
