"""Tests for RAG knowledge ingest and retrieval pipeline."""

from app.knowledge.ingest import ingest_official_source
from app.services.retrieval_service import search_knowledge_base


def test_ingest_and_retrieve_rag(db_session):
    # 1. Ingest a mock official source
    raw_text = """
    Section 16: Eligibility and conditions for taking input tax credit.
    Every registered person shall, subject to such conditions and restrictions as may be prescribed 
    and in the manner specified in section 49, be entitled to take credit of input tax charged on 
    any supply of goods or services or both to him which are used or intended to be used in the course 
    or furtherance of his business and the said amount shall be credited to the electronic credit ledger of such person.
    
    Section 17: Apportionment of credit and blocked credits.
    Where the goods or services or both are used by the registered person partly for the purpose of 
    any business and partly for other purposes, the amount of credit shall be restricted to so much 
    of the input tax as is attributable to the purposes of his business.
    """
    
    tenant_id = "test-tenant-123"
    
    source = ingest_official_source(
        db=db_session,
        tenant_id=tenant_id,
        title="CGST Act 2017",
        source_type="ACT",
        raw_text=raw_text,
    )
    
    assert source.id is not None
    
    # 2. Retrieve using the RAG search
    # (Since we are using SQLite, this falls back to sequential fetch, but tests the pipeline nonetheless)
    results = search_knowledge_base(
        db=db_session,
        tenant_id=tenant_id,
        query="input tax credit eligibility",
        limit=2
    )
    
    assert len(results) > 0
    assert results[0]["title"] == "CGST Act 2017"
    assert results[0]["content"] is not None
    assert "16" in results[0]["section"] or results[0]["section"] is None
