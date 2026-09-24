"""Audit event service — append-only business event history.

Per SECURITY.md Section 13 and DATA_SPEC.md Section 15, audit events
must be append-only at the application layer and cover:
    authentication, document events, AI generation, source retrieval,
    decisions, approvals, exports, configuration changes.

Every state-changing operation should call ``log_event`` to create an
immutable record of what happened, who did it, and which entity was
affected.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.auth import AuthContext
from app.models import AuditEvent



def _make_json_safe(obj: Any) -> Any:
    """Recursively convert dates, datetimes, Decimals to JSON-serializable primitives."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_make_json_safe(x) for x in obj]
    return obj


def log_event(
    db: Session,
    *,
    auth: AuthContext,
    entity_type: str,
    entity_id: str,
    event_type: str,
    payload: dict | None = None,
) -> AuditEvent:
    """Append an audit event and flush (but do not commit).

    The caller is responsible for committing the transaction so that
    the audit record is written atomically with the business change.
    """
    safe_payload = _make_json_safe(payload) if payload is not None else None
    event = AuditEvent(
        firm_id=auth.firm_id,
        tenant_id=auth.tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        payload_json=safe_payload,
    )
    db.add(event)
    db.flush()
    return event


def list_events_for_entity(
    db: Session,
    *,
    tenant_id: str,
    entity_type: str,
    entity_id: str,
) -> list[AuditEvent]:
    """Return audit events for a specific entity, newest first."""
    return (
        db.query(AuditEvent)
        .filter(
            AuditEvent.tenant_id == tenant_id,
            AuditEvent.entity_type == entity_type,
            AuditEvent.entity_id == entity_id,
        )
        .order_by(AuditEvent.created_at.desc())
        .all()
    )
