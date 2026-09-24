"""Communication drafting service for vendor and client follow-ups.

Implements PRD §5 Follow-up:
"As staff, I can create a client/vendor message draft."
Grounds messages strictly in verified evidence (SECURITY.md §7 & §9).
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.prompt_templates import COMMUNICATION_DRAFT_SYSTEM_PROMPT
from app.ai.provider import get_ai_provider
from app.auth import AuthContext
from app.models import Evidence, ExceptionRecord, Task, Transaction
from app.schemas import MessageDraftRequest, MessageDraftResponse
from app.services.task_service import get_task


def draft_follow_up_message(
    db: Session,
    *,
    auth: AuthContext,
    task_id: str,
    payload: MessageDraftRequest,
) -> MessageDraftResponse:
    """Draft a communication message to a vendor or client based on task evidence."""
    task = get_task(db, auth=auth, task_id=task_id)

    evidence_references: list[str] = []
    context_lines: list[str] = [
        f"Task Title: {task.title}",
        f"Task Description: {task.description or 'N/A'}",
        f"Target Channel: {payload.channel.upper()}",
        f"Recipient Type: {payload.recipient_type.title()}",
    ]

    # If linked to an Exception, retrieve discrepancy details and evidence
    if task.exception_id:
        exc = (
            db.query(ExceptionRecord)
            .filter(
                ExceptionRecord.id == task.exception_id,
                ExceptionRecord.tenant_id == auth.tenant_id,
            )
            .first()
        )
        if exc:
            context_lines.append(f"Discrepancy Type: {exc.type}")
            context_lines.append(f"Discrepancy Severity: {exc.severity}")

            # Fetch linked evidence
            evidences = (
                db.query(Evidence)
                .filter(
                    Evidence.exception_id == exc.id,
                    Evidence.tenant_id == auth.tenant_id,
                )
                .all()
            )
            for ev in evidences:
                evidence_references.append(ev.id)
                context_lines.append(
                    f"Evidence [{ev.id}]: field={ev.source_field} | text={ev.source_text} | row={ev.source_row_reference}"
                )

    if payload.custom_instructions:
        context_lines.append(f"Additional Instructions from CA: {payload.custom_instructions}")

    user_prompt = (
        "Draft a follow-up communication based strictly on the following verified compliance context:\n\n"
        + "\n".join(context_lines)
    )

    ai_provider = get_ai_provider()
    draft_raw = ai_provider.generate(
        system_prompt=COMMUNICATION_DRAFT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    subject: str | None = None
    body: str = draft_raw.strip()

    if payload.channel.lower() == "email" and "SUBJECT:" in draft_raw:
        parts = draft_raw.split("\n\n", 1)
        if len(parts) == 2 and parts[0].startswith("SUBJECT:"):
            subject = parts[0].replace("SUBJECT:", "").strip()
            body = parts[1].strip()

    return MessageDraftResponse(
        task_id=task.id,
        channel=payload.channel.lower(),
        recipient_type=payload.recipient_type.lower(),
        subject=subject,
        message_body=body,
        evidence_references=evidence_references,
    )
