"""Data Retention and Deletion API routes.

Provides:
- Retention policy management
- Soft delete for clients, periods, documents
- Hard delete (purge) of soft-deleted records
- Right to erasure (GDPR/DPDP compliance)
- Retention policy execution (admin)
"""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.database import get_db
from app.permissions import Role, require_role
from app.schemas import (
    RetentionPolicyExecuteRequest,
    RetentionPolicyExecuteResponse,
    RetentionPolicyRead,
    SoftDeleteRequest,
    SoftDeleteResponse,
)
from app.services import retention_service

router = APIRouter(prefix="/api/v1", tags=["retention"])


@router.get("/retention/policy", response_model=RetentionPolicyRead)
def get_retention_policy(
    auth: AuthContext = Depends(get_auth_context),
) -> RetentionPolicyRead:
    """Get current retention policy configuration."""
    from app.services.retention_service import DEFAULT_RETENTION_POLICIES
    return RetentionPolicyRead(policies=DEFAULT_RETENTION_POLICIES)


@router.post(
    "/retention/execute",
    response_model=RetentionPolicyExecuteResponse,
    dependencies=[Depends(require_role(Role.OWNER))],
)
def execute_retention_policy(
    payload: RetentionPolicyExecuteRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> RetentionPolicyExecuteResponse:
    """Execute retention policy (admin only).
    
    Performs dry-run by default. Set dry_run=false to actually delete.
    Requires owner role.
    """
    results = retention_service.execute_retention_policy(
        db,
        policies=payload.policies,
        dry_run=payload.dry_run,
    )
    return RetentionPolicyExecuteResponse(
        dry_run=payload.dry_run,
        results=results,
        executed_at=datetime.now(timezone.utc),
    )


@router.post(
    "/clients/{client_id}/soft-delete",
    response_model=SoftDeleteResponse,
    dependencies=[Depends(require_role(Role.PARTNER))],
)
def soft_delete_client(
    client_id: str,
    payload: SoftDeleteRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> SoftDeleteResponse:
    """Soft delete a client (partner or above).
    
    Marks client as deleted but retains data for retention period.
    Requires partner role or above.
    """
    success = retention_service.soft_delete_client(
        db,
        client_id=client_id,
        tenant_id=auth.tenant_id,
        deleted_by=auth.user_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or already deleted",
        )
    return SoftDeleteResponse(
        entity_type="client",
        entity_id=client_id,
        status="soft_deleted",
        deleted_at=datetime.now(timezone.utc),
    )


@router.post(
    "/periods/{period_id}/soft-delete",
    response_model=SoftDeleteResponse,
    dependencies=[Depends(require_role(Role.PARTNER))],
)
def soft_delete_period(
    period_id: str,
    payload: SoftDeleteRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> SoftDeleteResponse:
    """Soft delete a period (partner or above)."""
    success = retention_service.soft_delete_period(
        db,
        period_id=period_id,
        tenant_id=auth.tenant_id,
        deleted_by=auth.user_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Period not found or already deleted",
        )
    return SoftDeleteResponse(
        entity_type="period",
        entity_id=period_id,
        status="soft_deleted",
        deleted_at=datetime.now(timezone.utc),
    )


@router.post(
    "/documents/{document_id}/soft-delete",
    response_model=SoftDeleteResponse,
    dependencies=[Depends(require_role(Role.SENIOR))],
)
def soft_delete_document(
    document_id: str,
    payload: SoftDeleteRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> SoftDeleteResponse:
    """Soft delete a document (senior or above)."""
    success = retention_service.soft_delete_document(
        db,
        document_id=document_id,
        tenant_id=auth.tenant_id,
        deleted_by=auth.user_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or already deleted",
        )
    return SoftDeleteResponse(
        entity_type="document",
        entity_id=document_id,
        status="soft_deleted",
        deleted_at=datetime.now(timezone.utc),
    )


@router.post(
    "/retention/purge",
    response_model=RetentionPolicyExecuteResponse,
    dependencies=[Depends(require_role(Role.OWNER))],
)
def purge_soft_deleted(
    retention_years: int = Query(1, ge=1, le=10),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> RetentionPolicyExecuteResponse:
    """Purge soft-deleted records older than retention period (owner only)."""
    from app.services.retention_service import (
        purge_soft_deleted_clients,
        purge_soft_deleted_periods,
        purge_soft_deleted_documents,
    )
    
    results = {
        "soft_deleted_clients": retention_service.purge_soft_deleted_clients(db, retention_years),
        "soft_deleted_periods": retention_service.purge_soft_deleted_periods(db, retention_years),
        "soft_deleted_documents": retention_service.purge_soft_deleted_documents(db, retention_years),
    }
    return RetentionPolicyExecuteResponse(
        dry_run=False,
        results=results,
        executed_at=datetime.now(timezone.utc),
    )


@router.post(
    "/erasure",
    response_model=RetentionPolicyExecuteResponse,
    dependencies=[Depends(require_role(Role.OWNER))],
)
def execute_right_to_erasure(
    user_id: str = Query(..., description="User ID to erase"),
    reason: str = Query("User requested erasure under GDPR/DPDP"),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> RetentionPolicyExecuteResponse:
    """Execute right to erasure (GDPR Article 17 / DPDP Section 12).
    
    Erases all personal data for a user within the tenant.
    Does NOT delete audit events or legal/tax records that must be retained.
    Requires owner role.
    """
    results = retention_service.execute_right_to_erasure(
        db,
        tenant_id=auth.tenant_id,
        user_id=user_id,
        reason=reason,
    )
    return RetentionPolicyExecuteResponse(
        dry_run=False,
        results=results,
        executed_at=datetime.now(timezone.utc),
    )