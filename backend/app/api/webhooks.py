"""WhatsApp webhook and chat simulator API.

Provides:
  - GET  /api/v1/webhooks/whatsapp     — Meta webhook verification (hub.challenge)
  - POST /api/v1/webhooks/whatsapp     — Incoming message processing
  - POST /api/v1/chat/send             — Web simulator endpoint (dev only)

Security:
  - Webhook signature validation via HMAC-SHA256 (production)
  - All incoming message content treated as UNTRUSTED data (AGENTS.md §5)
  - Bot never triggers external submission without human approval
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.channels.adapter import (
    IncomingMessage,
    OutgoingMessage,
    get_channel_adapter,
)
from app.channels.bot_router import route_message
from app.database import get_db
from app.services import audit_service

router = APIRouter(tags=["channels"])


# ---------------------------------------------------------------------------
# WhatsApp Webhook — Verification (GET)
# ---------------------------------------------------------------------------


@router.get("/api/v1/webhooks/whatsapp")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
) -> Any:
    """Meta webhook verification handshake.

    Meta sends a GET request with hub.mode, hub.verify_token, and hub.challenge.
    We respond with hub.challenge if the token matches.
    """
    expected_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "taxtrace-dev-verify-token")
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return int(hub_challenge) if hub_challenge else ""
    raise HTTPException(status_code=403, detail="Webhook verification failed")


# ---------------------------------------------------------------------------
# WhatsApp Webhook — Incoming Messages (POST)
# ---------------------------------------------------------------------------


class WebhookPayload(BaseModel):
    """Simplified Meta WhatsApp Cloud API webhook payload."""

    object: str | None = None
    entry: list[dict[str, Any]] | None = None


@router.post("/api/v1/webhooks/whatsapp", status_code=200)
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Process incoming WhatsApp messages.

    In production, this validates the X-Hub-Signature-256 header.
    For dev/mock mode, signature validation is skipped.
    """
    body = await request.body()
    adapter = get_channel_adapter("whatsapp")

    # Validate webhook signature (production security)
    headers = dict(request.headers)
    if not adapter.validate_webhook(headers, body):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    # Parse the Meta webhook payload
    try:
        payload = WebhookPayload.model_validate_json(body)
    except Exception:
        return {"status": "ignored"}

    if not payload.entry:
        return {"status": "no_entries"}

    # Process each message in the webhook
    for entry in payload.entry:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])

            for msg in messages:
                if msg.get("type") != "text":
                    continue

                sender_phone = msg.get("from", "")
                text = msg.get("text", {}).get("body", "")

                if not text:
                    continue

                # Build normalized incoming message
                incoming = IncomingMessage(
                    channel="whatsapp",
                    sender_id=sender_phone,
                    text=text,
                    metadata={
                        "message_id": msg.get("id"),
                        "timestamp": msg.get("timestamp"),
                        "contacts": contacts,
                    },
                )

                # For the webhook, we need to resolve the sender to a tenant.
                # In production, this would look up the phone number in firm_memberships.
                # For now, we use a simplified dev auth context.
                auth = _resolve_webhook_auth(db, sender_phone)
                if not auth:
                    # Unknown sender — send a polite rejection
                    adapter.send_message(
                        OutgoingMessage(
                            channel="whatsapp",
                            recipient_id=sender_phone,
                            text="Sorry, your phone number is not registered with TaxTrace. Please contact your CA firm.",
                        )
                    )
                    continue

                # Route the message through the bot
                response = route_message(db, auth, incoming)

                # Audit log the interaction
                audit_service.log_event(
                    db,
                    auth=auth,
                    entity_type="channel",
                    entity_id=f"whatsapp:{sender_phone}",
                    event_type="channel.message_received",
                    payload={
                        "channel": "whatsapp",
                        "command_text": text[:200],  # Truncate for safety
                        "response_preview": response.text[:200],
                    },
                )
                db.commit()

                # Send the response
                adapter.send_message(
                    OutgoingMessage(
                        channel="whatsapp",
                        recipient_id=sender_phone,
                        text=response.text,
                    )
                )

    return {"status": "processed"}


def _resolve_webhook_auth(db: Session, phone: str) -> AuthContext | None:
    """Resolve a phone number to an AuthContext.

    In production, this would look up the user by phone number in the database.
    For development, we return a default dev context.
    """
    # TODO: Production implementation — look up phone in users/firm_memberships table
    # For now, return a dev context if WHATSAPP_DEV_MODE is set
    if os.getenv("WHATSAPP_DEV_MODE", "true").lower() == "true":
        return AuthContext(
            user_id="whatsapp-user",
            firm_id=os.getenv("WHATSAPP_DEV_FIRM_ID", "dev-firm"),
            role="staff",
            request_id=f"wa-{phone}",
        )
    return None


# ---------------------------------------------------------------------------
# Chat Simulator (dev-only endpoint)
# ---------------------------------------------------------------------------


class ChatSimulatorRequest(BaseModel):
    """Request body for the web-based chat simulator."""

    message: str


class ChatSimulatorResponse(BaseModel):
    """Response body for the web-based chat simulator."""

    reply: str
    needs_confirmation: bool = False


@router.post(
    "/api/v1/chat/send",
    response_model=ChatSimulatorResponse,
)
def chat_simulator(
    payload: ChatSimulatorRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> ChatSimulatorResponse:
    """Web-based chat simulator endpoint.

    Uses the same bot router as WhatsApp but with standard auth.
    This allows testing the bot flow through the web UI without Meta's sandbox.
    """
    incoming = IncomingMessage(
        channel="web_simulator",
        sender_id=auth.user_id,
        text=payload.message,
    )

    response = route_message(db, auth, incoming)

    # Audit log
    audit_service.log_event(
        db,
        auth=auth,
        entity_type="channel",
        entity_id=f"simulator:{auth.user_id}",
        event_type="channel.simulator_message",
        payload={
            "command_text": payload.message[:200],
            "response_preview": response.text[:200],
        },
    )
    db.commit()

    return ChatSimulatorResponse(
        reply=response.text,
        needs_confirmation=response.needs_confirmation,
    )
