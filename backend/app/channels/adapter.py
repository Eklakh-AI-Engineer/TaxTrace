"""Channel adapter abstraction.

Defines a generic interface for messaging channels (WhatsApp, SMS, etc.)
so the domain logic is decoupled from any specific channel provider.

Design constraint (IMPLEMENTATION_PLAN.md Stage 8):
  - WhatsApp is a channel, not the domain model.
  - All incoming channel content is treated as untrusted data.
  - The bot should never trigger external compliance submission without human approval.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IncomingMessage:
    """Normalized inbound message from any channel."""

    channel: str  # "whatsapp", "sms", "web_simulator"
    sender_id: str  # channel-specific user identifier
    text: str  # raw message text (treated as UNTRUSTED)
    metadata: dict[str, Any] = field(default_factory=dict)
    # metadata may include: message_id, timestamp, media_url, etc.


@dataclass
class OutgoingMessage:
    """Normalized outbound message to any channel."""

    channel: str
    recipient_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ChannelAdapter(ABC):
    """Abstract interface for a messaging channel."""

    @abstractmethod
    def send_message(self, message: OutgoingMessage) -> dict[str, Any]:
        """Send a message through the channel. Returns provider response."""
        pass

    @abstractmethod
    def validate_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        """Validate that an incoming webhook request is authentic."""
        pass


class MockChannelAdapter(ChannelAdapter):
    """In-memory mock adapter for development and testing.

    Stores all sent messages in a list for inspection.
    """

    def __init__(self) -> None:
        self.sent_messages: list[OutgoingMessage] = []

    def send_message(self, message: OutgoingMessage) -> dict[str, Any]:
        self.sent_messages.append(message)
        return {"status": "sent", "message_id": f"mock_{len(self.sent_messages)}"}

    def validate_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        # Mock always validates
        return True


class WhatsAppCloudAdapter(ChannelAdapter):
    """Production adapter for Meta WhatsApp Cloud API.

    Requires WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN,
    and WHATSAPP_VERIFY_TOKEN environment variables.
    """

    def __init__(
        self,
        phone_number_id: str,
        access_token: str,
        verify_token: str,
        app_secret: str | None = None,
    ) -> None:
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.verify_token = verify_token
        self.app_secret = app_secret

    def send_message(self, message: OutgoingMessage) -> dict[str, Any]:
        """Send a text message via the WhatsApp Cloud API.

        In production, this would POST to:
        https://graph.facebook.com/v18.0/{phone_number_id}/messages
        """
        import httpx

        url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": message.recipient_id,
            "type": "text",
            "text": {"body": message.text},
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        resp = httpx.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def validate_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        """Validate Meta's X-Hub-Signature-256 header using HMAC-SHA256."""
        if not self.app_secret:
            return False

        import hashlib
        import hmac

        expected_sig = headers.get("x-hub-signature-256", "")
        if not expected_sig.startswith("sha256="):
            return False

        computed = hmac.new(
            self.app_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(f"sha256={computed}", expected_sig)


# ---------------------------------------------------------------------------
# Singleton registry
# ---------------------------------------------------------------------------

_adapters: dict[str, ChannelAdapter] = {}


def get_channel_adapter(channel: str = "whatsapp") -> ChannelAdapter:
    """Return the configured adapter for the given channel."""
    if channel not in _adapters:
        _adapters[channel] = MockChannelAdapter()
    return _adapters[channel]


def set_channel_adapter(channel: str, adapter: ChannelAdapter) -> None:
    """Override the adapter for a channel (used for testing and configuration)."""
    _adapters[channel] = adapter
