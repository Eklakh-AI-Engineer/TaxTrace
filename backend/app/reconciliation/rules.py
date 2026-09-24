"""Reconciliation rule definitions and constants.

Follows PRD.md §6 and DATA_SPEC.md §6-7.
"""

from __future__ import annotations

from enum import Enum


class MatchStatus(str, Enum):
    MATCHED = "matched"
    PARTIAL_MATCH = "partial_match"
    CANDIDATE = "candidate"
    REJECTED = "rejected"


class ExceptionType(str, Enum):
    MATCHED = "MATCHED"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    MISSING_IN_2B = "MISSING_IN_2B"
    MISSING_IN_BOOKS = "MISSING_IN_BOOKS"
    DUPLICATE = "DUPLICATE"
    GSTIN_MISMATCH = "GSTIN_MISMATCH"
    DATE_MISMATCH = "DATE_MISMATCH"
    VALUE_MISMATCH = "VALUE_MISMATCH"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class ExceptionSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExceptionStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    RESOLVED = "resolved"


CURRENT_RULE_VERSION = "recon-rule-v1"
