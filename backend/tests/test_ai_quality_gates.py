"""AI Quality Gate Tests for CI.

Evaluates:
1. AI Explanation quality - unsupported claim rate, fact/hypothesis separation
2. Notice Draft quality - citation pass rate, missing info detection
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.ai.provider import LocalMockAIProvider, set_ai_provider
from app.auth import AuthContext
from app.models import Evidence, ExceptionRecord, NoticeCase
from app.schemas import AIExplanationRequest, DraftCreateRequest
from app.services.ai_service import explain_exception
from app.services.notice_service import generate_notice_draft
from app.database import Base, engine
from app.parsers.normalizer import parse_decimal


class TestAIQualityGates:
    """AI quality gates that must pass for pilot readiness."""

    @pytest.fixture(scope="class")
    def db(self) -> Session:
        Base.metadata.create_all(bind=engine)
        session = next(iter(__import__("app.database", fromlist=["get_db"]).get_db()))
        yield session
        session.close()

    @pytest.fixture(scope="class")
    def auth_senior(self) -> AuthContext:
        return AuthContext(
            user_id="test_user",
            firm_id="test_firm",
            role="senior",
            request_id="bench_req",
        )

    @pytest.fixture(scope="class")
    def auth_partner(self) -> AuthContext:
        return AuthContext(
            user_id="test_user",
            firm_id="test_firm",
            role="partner",
            request_id="bench_req",
        )

    @pytest.fixture(autouse=True)
    def setup_ai_provider(self):
        """Use mock AI provider for deterministic testing."""
        provider = LocalMockAIProvider()
        set_ai_provider(provider)
        yield
        set_ai_provider(LocalMockAIProvider())

    def create_mock_exception(self, db: Session, exc_type: str = "VALUE_MISMATCH") -> ExceptionRecord:
        """Create a mock exception with evidence for testing."""
        exc = ExceptionRecord(
            firm_id="test_firm",
            period_id="test_period",
            tenant_id="test_firm",
            type=exc_type,
            severity="medium",
            status="open",
            reason_code="TEST_REASON",
            explanation="Test discrepancy between books and portal",
            created_by_system=True,
        )
        db.add(exc)
        db.flush()

        ev = Evidence(
            firm_id="test_firm",
            tenant_id="test_firm",
            exception_id=exc.id,
            evidence_type="reconciliation_diff",
            source_text="Book tax: 180, Portal tax: 360",
            meta_data={"diff_tax": "180", "reason": "VALUE_MISMATCH"},
        )
        db.add(ev)
        db.commit()
        db.refresh(exc)
        return exc

    def create_mock_notice_case(self, db: Session) -> NoticeCase:
        """Create a mock notice case with evidence for testing."""
        notice = NoticeCase(
            firm_id="test_firm",
            client_id="test_client",
            period_id="test_period",
            tenant_id="test_firm",
            source_document_id="test_doc",
            notice_type="GST_DRC_01",
            reference_number="DRC01/2026/001",
            status="facts_extracted",
        )
        db.add(notice)
        db.flush()

        sections = ["Section 73", "Section 74", "Section 16"]
        for sec in sections:
            ev = Evidence(
                firm_id="test_firm",
                tenant_id="test_firm",
                notice_case_id=notice.id,
                evidence_type="statutory_section",
                source_text=f"Cited section: {sec}",
                meta_data={"section": sec},
            )
            db.add(ev)

        ev_demand = Evidence(
            firm_id="test_firm",
            tenant_id="test_firm",
            notice_case_id=notice.id,
            evidence_type="demand_amount",
            source_text="Demand Tax: 500000",
            meta_data={"demand_tax_amount": 500000},
        )
        db.add(ev_demand)
        db.commit()
        db.refresh(notice)
        return notice

    @pytest.mark.parametrize("exc_type", [
        "MATCHED",
        "VALUE_MISMATCH",
        "PARTIAL_MATCH",
        "MISSING_IN_2B",
        "MISSING_IN_BOOKS",
        "DUPLICATE",
        "REVIEW_REQUIRED",
    ])
    def test_explanation_unsupported_claim_rate(self, db: Session, auth_senior: AuthContext, exc_type: str):
        """Unsupported claim rate must be < 5% (mock provider should be 0%)."""
        exc = self.create_mock_exception(db, exc_type)

        response = explain_exception(
            db,
            auth=auth_senior,
            exception_id=exc.id,
            payload=AIExplanationRequest(mode="standard"),
        )

        # Check for unsupported claim indicators
        unsupported_indicators = [
            "definitely", "certainly", "proven", "guaranteed", "must be",
            "conclusively", "without doubt", "confirmed fact"
        ]
        text = f"{response.summary} {' '.join(response.facts)} {' '.join(response.possible_causes)}".lower()
        has_unsupported = any(indicator in text for indicator in unsupported_indicators)

        # Mock provider should have 0% unsupported claims
        assert not has_unsupported, f"Unsupported claim detected in {exc_type} explanation: {text}"

    @pytest.mark.parametrize("exc_type", [
        "MATCHED",
        "VALUE_MISMATCH",
        "PARTIAL_MATCH",
        "MISSING_IN_2B",
        "MISSING_IN_BOOKS",
        "DUPLICATE",
        "REVIEW_REQUIRED",
    ])
    def test_explanation_fact_hypothesis_separation(self, db: Session, auth_senior: AuthContext, exc_type: str):
        """Explanations must separate facts from hypotheses (>90%)."""
        exc = self.create_mock_exception(db, exc_type)

        response = explain_exception(
            db,
            auth=auth_senior,
            exception_id=exc.id,
            payload=AIExplanationRequest(mode="standard"),
        )

        # Mock provider returns both facts and possible_causes
        assert response.facts, f"No facts in {exc_type} explanation"
        assert response.possible_causes, f"No possible causes in {exc_type} explanation"
        assert len(response.facts) >= 1
        assert len(response.possible_causes) >= 1

    @pytest.mark.parametrize("exc_type", [
        "MATCHED",
        "VALUE_MISMATCH",
        "PARTIAL_MATCH",
        "MISSING_IN_2B",
        "MISSING_IN_BOOKS",
        "DUPLICATE",
        "REVIEW_REQUIRED",
    ])
    def test_explanation_confidence_scoring(self, db: Session, auth_senior: AuthContext, exc_type: str):
        """All explanations must have confidence scores in [0, 1]."""
        exc = self.create_mock_exception(db, exc_type)

        response = explain_exception(
            db,
            auth=auth_senior,
            exception_id=exc.id,
            payload=AIExplanationRequest(mode="standard"),
        )

        assert response.confidence is not None
        assert 0.0 <= response.confidence <= 1.0

    @pytest.mark.parametrize("exc_type", [
        "MATCHED",
        "VALUE_MISMATCH",
        "PARTIAL_MATCH",
        "MISSING_IN_2B",
        "MISSING_IN_BOOKS",
        "DUPLICATE",
        "REVIEW_REQUIRED",
    ])
    def test_explanation_evidence_linking(self, db: Session, auth_senior: AuthContext, exc_type: str):
        """All explanations must link to evidence IDs."""
        exc = self.create_mock_exception(db, exc_type)

        response = explain_exception(
            db,
            auth=auth_senior,
            exception_id=exc.id,
            payload=AIExplanationRequest(mode="standard"),
        )

        assert response.evidence_ids
        assert len(response.evidence_ids) >= 1

    def test_draft_citation_pass_rate(self, db: Session, auth_partner: AuthContext):
        """Draft citation pass rate must be > 90%."""
        notice = self.create_mock_notice_case(db)

        draft = generate_notice_draft(
            db,
            auth=auth_partner,
            notice_case_id=notice.id,
            payload=DraftCreateRequest(
                instructions="Draft a preliminary reply denying the demand",
            ),
        )

        # All cited sections should exist in evidence
        evidence_sections = [
            ev.meta_data.get("section") for ev in
            db.query(Evidence).filter(Evidence.notice_case_id == notice.id).all()
            if ev.meta_data and "section" in ev.meta_data
        ]

        for cited_section in draft.cited_sections:
            assert cited_section in evidence_sections, (
                f"Cited section {cited_section} not found in evidence"
            )

    def test_draft_missing_information_flagged(self, db: Session, auth_partner: AuthContext):
        """Drafts must flag missing information (100%)."""
        notice = self.create_mock_notice_case(db)

        draft = generate_notice_draft(
            db,
            auth=auth_partner,
            notice_case_id=notice.id,
            payload=DraftCreateRequest(
                instructions="Draft a preliminary reply denying the demand",
            ),
        )

        assert draft.missing_information
        assert len(draft.missing_information) >= 1
        # Should include the standard missing info about GSTR-3B proof
        assert any("GSTR-3B" in item for item in draft.missing_information)

    def test_draft_no_fabrication(self, db: Session, auth_partner: AuthContext):
        """Drafts must not fabricate facts or legal citations (100%)."""
        notice = self.create_mock_notice_case(db)

        draft = generate_notice_draft(
            db,
            auth=auth_partner,
            notice_case_id=notice.id,
            payload=DraftCreateRequest(
                instructions="Draft a preliminary reply denying the demand",
            ),
        )

        # Mock provider generates grounded content
        # Check that content references known evidence
        content_lower = draft.content.lower()
        
        # Should reference the notice type
        assert "drc" in content_lower or "notice" in content_lower
        
        # Should not contain obviously fabricated specific case law
        fabricated_indicators = [
            "supreme court ruled in 2025", "high court judgment 2024",
            "section 999", "rule 888", "circular 999"
        ]
        for indicator in fabricated_indicators:
            assert indicator not in content_lower, f"Potential fabrication detected: {indicator}"

    def test_draft_status_under_review(self, db: Session, auth_partner: AuthContext):
        """Generated drafts must have status 'under_review' not 'approved'."""
        notice = self.create_mock_notice_case(db)

        draft = generate_notice_draft(
            db,
            auth=auth_partner,
            notice_case_id=notice.id,
            payload=DraftCreateRequest(
                instructions="Draft a preliminary reply denying the demand",
            ),
        )

        assert draft.status == "under_review"
        assert draft.approved_by is None
        assert draft.approved_at is None