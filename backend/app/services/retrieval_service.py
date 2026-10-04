"""RAG Retrieval and Citation Service.

Provides vector search over the knowledge base to support grounded AI drafting.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.provider import get_ai_provider
from app.models import KnowledgeChunk, KnowledgeSource


def search_knowledge_base(
    db: Session,
    *,
    tenant_id: str,
    query: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve relevant chunks from the knowledge base using vector similarity."""
    
    # 1. Embed the query
    provider = get_ai_provider()
    query_embedding = provider.embed(query)
    
    # 2. Search using pgvector's cosine distance `<=>`
    # We also enforce tenant isolation (though official sources might be global, 
    # the schema binds them to a tenant_id, so we filter by it or a global tenant if implemented).
    # Note: If running in SQLite (during tests), the query will fallback or we must mock it.
    
    dialect_name = db.bind.dialect.name
    
    if dialect_name == "sqlite":
        # Fallback for SQLite tests: return deterministic mock results or fetch all and sort in python
        # We'll just fetch some chunks and return them without vector math
        stmt = (
            select(KnowledgeChunk, KnowledgeSource)
            .join(KnowledgeSource, KnowledgeChunk.source_id == KnowledgeSource.id)
            .where(KnowledgeChunk.tenant_id == tenant_id)
            .limit(limit)
        )
        results = db.execute(stmt).all()
    else:
        # PostgreSQL with pgvector
        stmt = (
            select(KnowledgeChunk, KnowledgeSource)
            .join(KnowledgeSource, KnowledgeChunk.source_id == KnowledgeSource.id)
            .where(KnowledgeChunk.tenant_id == tenant_id)
            .order_by(KnowledgeChunk.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        results = db.execute(stmt).all()
        
    extracted = []
    for chunk, source in results:
        extracted.append({
            "chunk_id": chunk.id,
            "source_id": source.id,
            "title": source.title,
            "section": chunk.section_reference,
            "content": chunk.content,
            "url": source.url,
            "version": source.version,
        })
        
    return extracted
