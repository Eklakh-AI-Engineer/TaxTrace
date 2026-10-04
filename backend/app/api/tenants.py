from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_tenant_id, require_firm_tenant, tenant_scope_query
from app.models import Client, Firm
from app.schemas import ClientCreate, ClientRead, FirmCreate, FirmRead

router = APIRouter(prefix="/api/v1")


@router.post("/firms", response_model=FirmRead)
def create_firm(payload: FirmCreate, db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id)) -> Firm:
    firm = Firm(id=tenant_id, name=payload.name, status=payload.status, plan=payload.plan)
    db.add(firm)
    db.commit()
    db.refresh(firm)
    return firm


@router.get("/firms/{firm_id}", response_model=FirmRead)
def get_firm(firm_id: str, db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id)) -> Firm:
    require_firm_tenant(firm_id, tenant_id)
    firm = db.get(Firm, firm_id)
    if firm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Firm not found.")
    return firm


@router.get("/firms/{firm_id}/clients", response_model=list[ClientRead])
def list_clients(firm_id: str, db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id)) -> list[Client]:
    require_firm_tenant(firm_id, tenant_id)
    return tenant_scope_query(db, Client, tenant_id).filter(Client.firm_id == firm_id).all()


@router.post("/firms/{firm_id}/clients", response_model=ClientRead)
def create_client(
    firm_id: str,
    payload: ClientCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
) -> Client:
    require_firm_tenant(firm_id, tenant_id)
    client = Client(
        firm_id=firm_id,
        tenant_id=tenant_id,
        display_name=payload.display_name,
        gstin=payload.gstin,
        pan_reference=payload.pan_reference,
        status=payload.status,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client
