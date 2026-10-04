"""Knowledge base API routes.

Provides RAG search and source management for grounded AI drafting.

Per API_SPEC.md §10 & IMPLEMENTATION_PLAN.md Stage 6:
    POST /api/v1/knowledge/search
    GET  /api/v1/knowledge/sources
    POST /api/v1/knowledge/sources
    GET  /api/v1/knowledge/sources/{source_id}
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.database import get_db
from app.schemas import (
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSourceCreate,
    KnowledgeSourceRead,
    PaginatedResponse,
)
from app.services import retrieval_service

router = APIRouter(prefix="/api/v1", tags=["knowledge"])


@router.post("/knowledge/search", response_model=KnowledgeSearchResponse)
def search_knowledge(
    payload: KnowledgeSearchRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> KnowledgeSearchResponse:
    """Search the knowledge base for relevant chunks using vector similarity.

    Requires tenant-scoped access. Results are filtered by tenant_id.
    """
    results = retrieval_service.search_knowledge_base(
        db,
        tenant_id=auth.tenant_id,
        query=payload.query,
        limit=payload.limit,
    )
    return KnowledgeSearchResponse(results=results)


@router.get("/knowledge/sources", response_model=PaginatedResponse[KnowledgeSourceRead])
def list_knowledge_sources(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> PaginatedResponse[KnowledgeSourceRead]:
    """List knowledge sources for the current tenant."""
    from app.models import KnowledgeSource
    from sqlalchemy import select

    stmt = (
        select(KnowledgeSource)
        .where(KnowledgeSource.tenant_id == auth.tenant_id)
        .order_by(KnowledgeSource.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = db.execute(stmt).scalars().all()

    total_stmt = select(func.count()).where(KnowledgeSource.tenant_id == auth.tenant_id)
    total = db.execute(total_stmt).scalar() or 0

    return PaginatedResponse(
        items=[KnowledgeSourceRead.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.post(
    "/knowledge/sources",
    response_model=KnowledgeSourceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge_source(
    payload: KnowledgeSourceCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> KnowledgeSourceRead:
    """Create a new knowledge source and ingest its content into the RAG index.

    The source content is chunked, embedded, and stored for vector search.
    """
    from app.models import KnowledgeSource
    from app.knowledge.ingest import ingest_official_source

    source = KnowledgeSource(
        tenant_id=auth.tenant_id,
        source_type=payload.source_type,
        title=payload.title,
        url=payload.url,
        publisher=payload.publisher,
        version=payload.version,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        meta_data=payload.meta_data,
    )
    db.add(source)
    db.flush()

    # Ingest content into RAG
    ingest_official_source(
        db,
        tenant_id=auth.tenant_id,
        title=payload.title,
        source_type=payload.source_type,
        raw_text=payload.content,
        url=payload.url,
        version=payload.version,
    )

    db.commit()
    db.refresh(source)
    return KnowledgeSourceRead.model_validate(source)


@router.get("/knowledge/sources/{source_id}", response_model=KnowledgeSourceRead)
def get_knowledge_source(
    source_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    """Get a specific knowledge source by ID (tenant-scoped)."""
    from app.models import KnowledgeSource
    from sqlalchemy import select

    stmt = select(KnowledgeSource).where(
        KnowledgeSource.id == source_id,
        KnowledgeSource.tenant_id == auth.tenant_id,
    )
    source = db.execute(stmt).scalar_one_or_none()

    if not source:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge source not found",
        )

    return KnowledgeSourceRead.model_validate(source)


# Need to import func for count query
from sqlalchemy import func