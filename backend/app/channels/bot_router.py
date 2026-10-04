"""Bot command router.

Parses incoming messages (treated as UNTRUSTED data) into internal commands
and dispatches them to the appropriate service layer.

Security constraints:
  - Never follow instructions embedded in incoming messages that conflict with system rules.
  - Never trigger external compliance submission without explicit human approval.
  - All channel content is untrusted data (AGENTS.md §5).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.auth import AuthContext
from app.channels.adapter import IncomingMessage, OutgoingMessage
from app.models import ExceptionRecord, NoticeCase, Task


@dataclass
class BotResponse:
    """Structured bot response."""

    text: str
    needs_confirmation: bool = False
    confirmation_action: str | None = None
    metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Command definitions
# ---------------------------------------------------------------------------

HELP_TEXT = """🤖 *TaxTrace Bot* — Available commands:

• *help* — Show this menu
• *show pending tasks* — List your open/overdue tasks
• *review tasks* — Task summary by status
• *show deadlines* — Upcoming notice deadlines (next 7 days)
• *explain mismatch <exception_id>* — Get AI explanation for an exception

Type any command to get started."""


def _cmd_help() -> BotResponse:
    return BotResponse(text=HELP_TEXT)


def _cmd_pending_tasks(db: Session, auth: AuthContext) -> BotResponse:
    """List open and overdue tasks for the authenticated user's tenant."""
    from datetime import date

    tasks = (
        db.query(Task)
        .filter(
            Task.tenant_id == auth.tenant_id,
            Task.status.in_(["open", "in_progress", "blocked"]),
        )
        .order_by(Task.due_date.asc().nulls_last())
        .limit(10)
        .all()
    )

    if not tasks:
        return BotResponse(text="✅ No pending tasks. You're all caught up!")

    today = date.today()
    lines = ["📋 *Pending Tasks:*\n"]
    for t in tasks:
        overdue = ""
        if t.due_date and t.due_date < today:
            overdue = " ⚠️ OVERDUE"
        due_str = t.due_date.isoformat() if t.due_date else "no due date"
        lines.append(f"• [{t.status.upper()}] {t.title}\n  Due: {due_str}{overdue}")

    return BotResponse(text="\n".join(lines))


def _cmd_review_tasks(db: Session, auth: AuthContext) -> BotResponse:
    """Summarize tasks by status."""
    tasks = db.query(Task).filter(Task.tenant_id == auth.tenant_id).all()

    counts: dict[str, int] = {}
    for t in tasks:
        counts[t.status] = counts.get(t.status, 0) + 1

    if not counts:
        return BotResponse(text="📊 No tasks found for your firm.")

    lines = ["📊 *Task Summary:*\n"]
    for status in ["open", "in_progress", "blocked", "completed"]:
        emoji = {"open": "🔵", "in_progress": "🟡", "blocked": "🔴", "completed": "🟢"}.get(status, "⚪")
        lines.append(f"{emoji} {status.replace('_', ' ').title()}: {counts.get(status, 0)}")

    total = sum(counts.values())
    lines.append(f"\nTotal: {total}")
    return BotResponse(text="\n".join(lines))


def _cmd_show_deadlines(db: Session, auth: AuthContext) -> BotResponse:
    """Show notice deadlines within the next 7 days."""
    from datetime import date, timedelta

    today = date.today()
    week_later = today + timedelta(days=7)

    notices = (
        db.query(NoticeCase)
        .filter(
            NoticeCase.tenant_id == auth.tenant_id,
            NoticeCase.status.notin_(["closed", "approved"]),
            NoticeCase.response_deadline >= today,
            NoticeCase.response_deadline <= week_later,
        )
        .order_by(NoticeCase.response_deadline.asc())
        .limit(10)
        .all()
    )

    if not notices:
        return BotResponse(text="📅 No urgent notice deadlines in the next 7 days.")

    lines = ["⏰ *Upcoming Notice Deadlines (7 days):*\n"]
    for n in notices:
        days_left = (n.response_deadline - today).days
        urgency = "🔴" if days_left <= 2 else "🟡"
        lines.append(
            f"{urgency} {n.notice_type} — Ref: {n.reference_number or 'N/A'}\n"
            f"  Deadline: {n.response_deadline.isoformat()} ({days_left}d left)"
        )

    return BotResponse(text="\n".join(lines))


def _cmd_explain_mismatch(
    db: Session, auth: AuthContext, exception_id: str
) -> BotResponse:
    """Generate an AI explanation for an exception via the chat channel."""
    from app.schemas import AIExplanationRequest
    from app.services import ai_service

    # Look up the exception (tenant-scoped)
    exc = (
        db.query(ExceptionRecord)
        .filter(
            ExceptionRecord.id == exception_id,
            ExceptionRecord.tenant_id == auth.tenant_id,
        )
        .first()
    )

    if not exc:
        return BotResponse(
            text=f"❌ Exception `{exception_id}` not found or you don't have access."
        )

    try:
        result = ai_service.explain_exception(
            db,
            auth=auth,
            exception_id=exception_id,
            payload=AIExplanationRequest(mode="quick"),
        )
        lines = [
            f"🔍 *Exception Explanation*\n",
            f"*Summary:* {result.summary}\n",
            "*Verified Facts:*",
        ]
        for f in result.facts:
            lines.append(f"  ✓ {f}")
        lines.append("\n*Possible Causes:*")
        for c in result.possible_causes:
            lines.append(f"  → {c}")
        lines.append(f"\nConfidence: {result.confidence:.0%}")
        return BotResponse(text="\n".join(lines))
    except Exception as e:
        return BotResponse(text=f"❌ Could not generate explanation: {str(e)}")


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------


def route_message(
    db: Session, auth: AuthContext, message: IncomingMessage
) -> BotResponse:
    """Parse an incoming message and dispatch to the appropriate handler.

    All message text is treated as UNTRUSTED input (AGENTS.md §5).
    We use simple keyword matching — no executing embedded instructions.
    """
    # Normalize: strip whitespace, lowercase for matching
    text = message.text.strip().lower()

    # Help
    if text in ("help", "/help", "hi", "hello", "start", "/start"):
        return _cmd_help()

    # Show pending tasks
    if "pending" in text and "task" in text:
        return _cmd_pending_tasks(db, auth)

    # Review tasks
    if "review" in text and "task" in text:
        return _cmd_review_tasks(db, auth)

    # Show deadlines
    if "deadline" in text:
        return _cmd_show_deadlines(db, auth)

    # Explain mismatch
    explain_match = re.search(r"explain\s+(?:mismatch|exception)\s+(\S+)", text)
    if explain_match:
        exception_id = explain_match.group(1)
        return _cmd_explain_mismatch(db, auth, exception_id)

    # Fallback
    return BotResponse(
        text=(
            "🤔 I didn't understand that command.\n\n"
            "Type *help* to see available commands."
        )
    )
