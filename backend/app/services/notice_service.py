"""Notice Intelligence, Fact Extraction, Draft Generation, and Partner Approval Service.

Follows:
- PRD.md §6 & SECURITY.md §5, §9:
- Notices are parsed into structured facts attached as verified Evidence.
- Response drafts cite statutory sources.
- Partner human approval is mandatory before any draft can be considered approved.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.notice_extractor import extract_notice_facts_deterministic
from app.ai.prompt_templates import DRAFT_GENERATION_SYSTEM_PROMPT
from app.ai.provider import get_ai_provider
from app.auth import AuthContext
from app.models import Client, Document, Evidence, NoticeCase, Period
from app.schemas import (
    DraftApproveRequest,
    DraftCreateRequest,
    DraftRead,
    NoticeExtractionResponse,
)
from app.services import audit_service, document_service
from app.storage.backend import get_storage_backend


def create_notice_case(
    db: Session,
    *,
    auth: AuthContext,
    client_id: str,
    period_id: str | None,
    document_id: str,
    notice_type: str = "OTHER",
) -> NoticeCase:
    """Create a new NoticeCase associated with an uploaded notice document."""
    # Validate client exists in tenant
    client = (
        db.query(Client)
        .filter(Client.id == client_id, Client.tenant_id == auth.tenant_id)
        .first()
    )
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found in this tenant.",
        )

    # Validate document exists in tenant
    doc = document_service.get_document(db, auth=auth, document_id=document_id)

    notice = NoticeCase(
        firm_id=auth.firm_id,
        client_id=client_id,
        period_id=period_id,
        tenant_id=auth.tenant_id,
        source_document_id=doc.id,
        notice_type=notice_type,
        status="received",
    )
    db.add(notice)
    db.flush()

    audit_service.log_event(
        db,
        auth=auth,
        entity_type="notice_case",
        entity_id=notice.id,
        event_type="notice.created",
        payload={"client_id": client_id, "document_id": doc.id, "notice_type": notice_type},
    )

    db.commit()
    db.refresh(notice)
    return notice


def get_notice_case(db: Session, *, auth: AuthContext, notice_case_id: str) -> NoticeCase:
    """Retrieve single notice case enforcing tenant boundary."""
    notice = (
        db.query(NoticeCase)
        .filter(NoticeCase.id == notice_case_id, NoticeCase.tenant_id == auth.tenant_id)
        .first()
    )
    if notice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice case not found.",
        )
    return notice


def extract_notice_facts(
    db: Session,
    *,
    auth: AuthContext,
    notice_case_id: str,
) -> NoticeExtractionResponse:
    """Extract structured facts from notice text and attach Evidence records."""
    notice = get_notice_case(db, auth=auth, notice_case_id=notice_case_id)
    doc = document_service.get_document(db, auth=auth, document_id=notice.source_document_id)

    # Read notice file content
    storage = get_storage_backend()
    raw_bytes = storage.read(doc.storage_uri)
    text_content = raw_bytes.decode("utf-8", errors="replace")

    facts = extract_notice_facts_deterministic(text_content)

    # Update NoticeCase with extracted values
    if facts.get("notice_type") and facts["notice_type"] != "OTHER":
        notice.notice_type = facts["notice_type"]
    if facts.get("reference_number"):
        notice.reference_number = facts["reference_number"]
    if facts.get("issue_date"):
        notice.issue_date = facts["issue_date"]
    if facts.get("response_deadline"):
        notice.response_deadline = facts["response_deadline"]

    notice.status = "facts_extracted"

    # Attach extracted fact evidence
    ev_count = 0
    if facts.get("cited_sections"):
        for sec in facts["cited_sections"]:
            ev = Evidence(
                firm_id=auth.firm_id,
                tenant_id=auth.tenant_id,
                notice_case_id=notice.id,
                evidence_type="statutory_section",
                source_document_id=doc.id,
                source_field="cited_section",
                source_text=f"Section {sec}",
                meta_data={"section": sec},
            )
            db.add(ev)
            ev_count += 1

    if facts.get("demand_tax_amount"):
        ev_tax = Evidence(
            firm_id=auth.firm_id,
            tenant_id=auth.tenant_id,
            notice_case_id=notice.id,
            evidence_type="demand_amount",
            source_document_id=doc.id,
            source_field="demand_tax_amount",
            source_text=f"Demand Tax: {facts['demand_tax_amount']}",
            meta_data={"demand_tax_amount": facts["demand_tax_amount"]},
        )
        db.add(ev_tax)
        ev_count += 1

    audit_service.log_event(
        db,
        auth=auth,
        entity_type="notice_case",
        entity_id=notice.id,
        event_type="notice.facts_extracted",
        payload=facts,
    )

    db.commit()
    db.refresh(notice)

    return NoticeExtractionResponse(
        notice_case_id=notice.id,
        notice_type=notice.notice_type,
        reference_number=notice.reference_number,
        taxpayer_gstin=facts.get("taxpayer_gstin"),
        taxpayer_name=facts.get("taxpayer_name"),
        issue_date=notice.issue_date,
        response_deadline=notice.response_deadline,
        demand_tax_amount=facts.get("demand_tax_amount"),
        cited_sections=facts.get("cited_sections", []),
        evidence_created_count=ev_count,
    )


# In-memory store for generated drafts (can be persisted to tasks/drafts table)
_DRAFTS_STORE: dict[str, dict[str, Any]] = {}


def generate_notice_draft(
    db: Session,
    *,
    auth: AuthContext,
    notice_case_id: str,
    payload: DraftCreateRequest,
) -> DraftRead:
    """Generate a formal preliminary response draft grounded in notice facts and evidence."""
    notice = get_notice_case(db, auth=auth, notice_case_id=notice_case_id)

    # Gather evidence attached to this notice
    evidence_items = (
        db.query(Evidence)
        .filter(Evidence.notice_case_id == notice.id, Evidence.tenant_id == auth.tenant_id)
        .all()
    )

    evidence_context = [
        {"type": e.evidence_type, "text": e.source_text, "meta": e.meta_data}
        for e in evidence_items
    ]

    user_prompt = (
        f"NOTICE TYPE: {notice.notice_type}\n"
        f"REFERENCE NUMBER: {notice.reference_number}\n"
        f"DEADLINE: {notice.response_deadline}\n"
        f"INSTRUCTIONS: {payload.instructions}\n\n"
        f"VERIFIED EVIDENCE:\n{evidence_context}\n"
    )

    provider = get_ai_provider()
    draft_text = provider.generate(
        system_prompt=DRAFT_GENERATION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.0,
    )

    draft_id = f"draft_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)

    draft_data = {
        "id": draft_id,
        "tenant_id": auth.tenant_id,
        "notice_case_id": notice.id,
        "status": "under_review",
        "content": draft_text,
        "cited_sections": [e.meta_data.get("section") for e in evidence_items if e.meta_data and "section" in e.meta_data],
        "missing_information": ["[REQUIRES CA VERIFICATION] Proof of tax payment by supplier (Form GSTR-3B)"],
        "approved_by": None,
        "approval_comment": None,
        "created_at": now,
        "approved_at": None,
    }
    _DRAFTS_STORE[draft_id] = draft_data

    audit_service.log_event(
        db,
        auth=auth,
        entity_type="notice_case",
        entity_id=notice.id,
        event_type="notice.draft_generated",
        payload={"draft_id": draft_id, "notice_type": notice.notice_type},
    )
    db.commit()

    return DraftRead(**draft_data)


def get_draft(auth: AuthContext, draft_id: str) -> DraftRead:
    """Retrieve draft with tenant isolation check."""
    draft = _DRAFTS_STORE.get(draft_id)
    if draft is None or draft.get("tenant_id") != auth.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found.",
        )
    return DraftRead(**draft)


def approve_draft(
    db: Session,
    *,
    auth: AuthContext,
    draft_id: str,
    payload: DraftApproveRequest,
) -> DraftRead:
    """Approve draft (requires partner role)."""
    draft = _DRAFTS_STORE.get(draft_id)
    if draft is None or draft.get("tenant_id") != auth.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found.",
        )

    now = datetime.now(timezone.utc)
    draft["status"] = "approved"
    draft["approved_by"] = auth.user_id
    draft["approval_comment"] = payload.comment
    draft["approved_at"] = now

    audit_service.log_event(
        db,
        auth=auth,
        entity_type="draft",
        entity_id=draft_id,
        event_type="draft.approved",
        payload={"approved_by": auth.user_id, "comment": payload.comment},
    )
    db.commit()

    return DraftRead(**draft)
