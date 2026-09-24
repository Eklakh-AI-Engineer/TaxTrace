"""AI package for TaxTrace."""

from app.ai.notice_extractor import extract_notice_facts_deterministic
from app.ai.prompt_templates import (
    DRAFT_GENERATION_SYSTEM_PROMPT,
    EXPLANATION_SYSTEM_PROMPT,
    NOTICE_EXTRACTION_SYSTEM_PROMPT,
)
from app.ai.provider import (
    AIProvider,
    LocalMockAIProvider,
    get_ai_provider,
    set_ai_provider,
)

__all__ = [
    "AIProvider",
    "LocalMockAIProvider",
    "get_ai_provider",
    "set_ai_provider",
    "EXPLANATION_SYSTEM_PROMPT",
    "NOTICE_EXTRACTION_SYSTEM_PROMPT",
    "DRAFT_GENERATION_SYSTEM_PROMPT",
    "extract_notice_facts_deterministic",
]
