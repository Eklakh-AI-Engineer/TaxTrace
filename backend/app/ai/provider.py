"""AI client provider abstraction for TaxTrace.

Supports:
- LocalMockAIProvider for fast, deterministic unit/integration testing and offline dev.
- Extensible base class for production LLM integrations (Gemini, Anthropic, OpenAI).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Abstract interface for LLM completions."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        """Generate response text given system instructions and user context."""
        pass


class LocalMockAIProvider(AIProvider):
    """Deterministic mock provider generating grounded answers based on evidence."""

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        prompt_lower = user_prompt.lower()

        # If generating an exception explanation
        if "explanation" in system_prompt.lower() or "exception" in prompt_lower:
            return json.dumps({
                "summary": "Discrepancy detected between Books and GSTR-2B filing.",
                "facts": [
                    "Supplier GSTIN and normalized invoice number match.",
                    "Tax calculation difference exceeds ₹1.00 tolerance.",
                ],
                "possible_causes": [
                    "Supplier may have amended invoice after book entry was posted.",
                    "Possible tax rate confusion between 18% and 12% in the original invoice.",
                ],
                "suggested_next_steps": [
                    "Contact supplier to obtain copy of filed GSTR-1.",
                    "Verify physical tax invoice copy against book entry.",
                ],
                "confidence": 0.88,
            })

        # If generating a communication draft to vendor or client
        if "communication" in system_prompt.lower() or "vendor" in prompt_lower or "whatsapp" in prompt_lower:
            if "whatsapp" in prompt_lower:
                return (
                    "Dear Partner,\n\n"
                    "Regarding invoice reconciliation for our mutual client:\n"
                    "- Invoice: INV-9901\n"
                    "- Status: Not appearing in GSTR-2B\n"
                    "- Action required: Kindly confirm if this invoice has been uploaded in your GSTR-1 return for the relevant period.\n\n"
                    "Thank you,\nTaxTrace Compliance Team"
                )
            return (
                "SUBJECT: Request for Clarification regarding GST Invoice Details\n\n"
                "Dear Vendor Accounts Team,\n\n"
                "During our regular compliance reconciliation for the current tax period, we noted a discrepancy regarding the following transaction:\n"
                "- Invoice Number: INV-9901\n"
                "- Taxable Value: ₹10,000.00\n"
                "- Discrepancy: Record exists in Purchase Register but is missing from GSTR-2B.\n\n"
                "Kindly verify whether this invoice has been declared in your GSTR-1 return. If already filed, please share the filing acknowledgment or copy of the invoice.\n\n"
                "Warm regards,\nCompliance & Accounts Department"
            )

        # If generating a notice draft
        if "draft" in system_prompt.lower() or "notice" in prompt_lower:
            return (
                "SUBJECT: Preliminary Reply to Notice\n\n"
                "1. FACTS OF THE CASE:\n"
                "The assessee has diligently maintained books of account and complied with all statutory filing deadlines.\n\n"
                "2. POINT-BY-POINT REBUTTAL:\n"
                "With reference to the alleged discrepancy in inward supplies, verified reconciliation evidence indicates "
                "that tax credits claimed correspond to bona fide business purchases supported by valid tax invoices.\n\n"
                "3. STATUTORY CITATIONS:\n"
                "Section 16(2) of the CGST Act, 2017 read with Circular No. 183/15/2022-GST.\n\n"
                "4. MISSING INFORMATION & REQUESTED ACTIONS:\n"
                "It is respectfully submitted that proceedings may kindly be dropped in view of the submitted reconciliation."
            )

        return "Default response grounded in verified evidence."


_default_ai_provider: AIProvider | None = None


def get_ai_provider() -> AIProvider:
    """Return the configured AI provider singleton."""
    global _default_ai_provider
    if _default_ai_provider is None:
        _default_ai_provider = LocalMockAIProvider()
    return _default_ai_provider


def set_ai_provider(provider: AIProvider) -> None:
    """Override AI provider (used for testing)."""
    global _default_ai_provider
    _default_ai_provider = provider
