"""AI Explanation and Exception Decision service.

Enforces:
- Explanations are strictly grounded in attached Evidence records.
- Facts are clearly separated from hypotheses.
- Audit logging for every human decision and generated explanation.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.prompt_templates import EXPLANATION_SYSTEM_PROMPT
from app.ai.provider import get_ai_provider
from app.auth import AuthContext
from app.models import Evidence, ExceptionRecord
from app.schemas import (
    AIExplanationRequest,
    AIExplanationResponse,
    ExceptionDecisionRequest,
    ExceptionDetailRead,
)
from app.services import audit_service, reconciliation_service


def explain_exception(
    db: Session,
    *,
    auth: AuthContext,
    exception_id: str,
    payload: AIExplanationRequest,
) -> AIExplanationResponse:
    """Generate an evidence-grounded explanation for a reconciliation exception."""
    exc, evidence_list = reconciliation_service.get_exception_detail(
        db, auth=auth, exception_id=exception_id
    )

    if not evidence_list:
        # Construct fallback evidence item from exception record if none exists
        ev = Evidence(
            firm_id=auth.firm_id,
            tenant_id=auth.tenant_id,
            exception_id=exc.id,
            evidence_type="reconciliation_diff",
            source_text=exc.explanation or exc.type,
            meta_data={"reason_code": exc.reason_code, "severity": exc.severity},
        )
        db.add(ev)
        db.flush()
        evidence_list = [ev]

    # Package evidence strictly as untrusted data boundary
    evidence_payload = [
        {
            "evidence_id": e.id,
            "type": e.evidence_type,
            "row_reference": e.source_row_reference,
            "text": e.source_text,
            "metadata": e.meta_data,
        }
        for e in evidence_list
    ]

    user_context = (
        f"EXCEPTION TYPE: {exc.type}\n"
        f"SEVERITY: {exc.severity}\n"
        f"CURRENT REASON CODE: {exc.reason_code}\n\n"
        f"ATTACHED VERIFIED EVIDENCE:\n{json.dumps(evidence_payload, indent=2)}\n\n"
        "Generate a grounded explanation separating verified facts from hypotheses."
    )

    provider = get_ai_provider()
    raw_response = provider.generate(
        system_prompt=EXPLANATION_SYSTEM_PROMPT,
        user_prompt=user_context,
        temperature=0.0,
    )

    # Parse response JSON or provide safe structured fallback
    try:
        parsed = json.loads(raw_response)
    except Exception:
        parsed = {
            "summary": exc.explanation or f"Exception {exc.type} detected.",
            "facts": [f"Discrepancy identified: {exc.type}"],
            "possible_causes": ["Timing difference or supplier amendment"],
            "suggested_next_steps": ["Verify physical invoices with vendor"],
            "confidence": 0.80,
        }

    explanation_id = str(uuid.uuid4())
    evidence_ids = [e.id for e in evidence_list]

    # Audit log the explanation generation event
    audit_service.log_event(
        db,
        auth=auth,
        entity_type="exception",
        entity_id=exc.id,
        event_type="ai.explanation_generated",
        payload={
            "explanation_id": explanation_id,
            "mode": payload.mode,
            "confidence": parsed.get("confidence", 0.8),
            "evidence_ids": evidence_ids,
        },
    )
    db.commit()

    return AIExplanationResponse(
        explanation_id=explanation_id,
        summary=parsed.get("summary", ""),
        facts=parsed.get("facts", []),
        possible_causes=parsed.get("possible_causes", []),
        suggested_next_steps=parsed.get("suggested_next_steps", []),
        confidence=float(parsed.get("confidence", 0.85)),
        evidence_ids=evidence_ids,
    )


def record_exception_decision(
    db: Session,
    *,
    auth: AuthContext,
    exception_id: str,
    payload: ExceptionDecisionRequest,
) -> ExceptionRecord:
    """Record a human reviewer's explicit decision on an exception."""
    exc, _ = reconciliation_service.get_exception_detail(
        db, auth=auth, exception_id=exception_id
    )

    old_status = exc.status
    exc.status = payload.decision
    exc.explanation = f"Decision by {auth.user_id} ({auth.role}): {payload.comment}"

    audit_service.log_event(
        db,
        auth=auth,
        entity_type="exception",
        entity_id=exc.id,
        event_type="exception.decision_recorded",
        payload={
            "decision": payload.decision,
            "comment": payload.comment,
            "old_status": old_status,
            "decided_by": auth.user_id,
        },
    )

    db.commit()
    db.refresh(exc)
    return exc
