"""RAG Knowledge Ingestion Pipeline.

Parses official documents (PDFs, Markdown, etc.) and chunks them into pgvector embeddings
for use in grounded notice drafting.
"""

from __future__ import annotations

import re
from typing import Iterator

from sqlalchemy.orm import Session

from app.ai.provider import get_ai_provider
from app.models import KnowledgeChunk, KnowledgeSource


def chunk_text(text: str, max_words: int = 150) -> Iterator[str]:
    """Basic chunker: split text into overlapping chunks.
    In production, use semantic chunking or LangChain's RecursiveCharacterTextSplitter.
    """
    words = text.split()
    overlap = 30
    for i in range(0, len(words), max_words - overlap):
        yield " ".join(words[i : i + max_words])


def ingest_official_source(
    db: Session,
    *,
    tenant_id: str,
    title: str,
    source_type: str,
    raw_text: str,
    url: str | None = None,
    version: str | None = None,
) -> KnowledgeSource:
    """Ingest a raw text document, chunk it, embed it, and store in the RAG knowledge base."""
    
    # 1. Create Source Document
    source = KnowledgeSource(
        tenant_id=tenant_id,
        title=title,
        source_type=source_type,
        url=url,
        version=version,
    )
    db.add(source)
    db.flush()
    
    # 2. Extract Sections (very basic heuristic for tax laws)
    # E.g. "Section 16: ..."
    sections = re.split(r"(?i)\n(?=section \d+)", raw_text)
    
    # 3. Chunk and Embed
    provider = get_ai_provider()
    chunk_index = 0
    
    for section_text in sections:
        section_text = section_text.strip()
        if not section_text:
            continue
            
        # Try to identify section number
        sec_match = re.match(r"(?i)section\s+([\d\w]+)", section_text)
        section_ref = sec_match.group(1) if sec_match else None
        
        for chunk in chunk_text(section_text):
            if not chunk.strip():
                continue
                
            embedding = provider.embed(chunk)
            
            kc = KnowledgeChunk(
                source_id=source.id,
                tenant_id=tenant_id,
                chunk_index=chunk_index,
                content=chunk,
                section_reference=section_ref,
                embedding=embedding,
            )
            db.add(kc)
            chunk_index += 1
            
    db.commit()
    db.refresh(source)
    return source
