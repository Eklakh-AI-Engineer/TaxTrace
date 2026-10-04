#!/usr/bin/env python3
"""Seed development database with test data.

Idempotent seed script for local development environment.
Creates test_firm, test_user, FirmMembership, and ensures
test client data belongs to test_firm.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

# Ensure backend is on path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db, Base, engine
from app.models import Client, Firm, FirmMembership, User


DEV_FIRM_ID = "test_firm"
DEV_USER_ID = "test_user"
DEV_USER_EMAIL = "test@test.com"
DEV_USER_NAME = "Test User"


def seed_dev_data(db: Session) -> dict:
    """Seed development database with test data.
    
    Idempotent: safe to run multiple times.
    
    Returns:
        dict with counts of created/updated records.
    """
    results = {
        "firm_created": False,
        "user_created": False,
        "membership_created": False,
        "clients_updated": 0,
    }

    # 1. Ensure test_firm exists
    firm = db.execute(
        select(Firm).where(Firm.id == DEV_FIRM_ID)
    ).scalar_one_or_none()
    
    if not firm:
        firm = Firm(
            id=DEV_FIRM_ID,
            name="Test Firm",
            status="active",
            plan="professional",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(firm)
        db.flush()
        results["firm_created"] = True
    else:
        # Ensure firm has correct data
        if firm.name != "Test Firm":
            firm.name = "Test Firm"
        if firm.status != "active":
            firm.status = "active"
        firm.updated_at = datetime.now(timezone.utc)
        results["firm_updated"] = True

    # 2. Ensure test_user exists
    user = db.execute(
        select(User).where(User.id == DEV_USER_ID)
    ).scalar_one_or_none()
    
    if not user:
        user = User(
            id=DEV_USER_ID,
            email=DEV_USER_EMAIL,
            name=DEV_USER_NAME,
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.flush()
        results["user_created"] = True
    else:
        # Ensure user has correct data
        if user.email != DEV_USER_EMAIL:
            user.email = DEV_USER_EMAIL
        if user.name != DEV_USER_NAME:
            user.name = DEV_USER_NAME
        if user.status != "active":
            user.status = "active"
        user.updated_at = datetime.now(timezone.utc)
        results["user_updated"] = True

    # 3. Ensure FirmMembership exists
    membership = db.execute(
        select(FirmMembership).where(
            FirmMembership.firm_id == DEV_FIRM_ID,
            FirmMembership.user_id == DEV_USER_ID
        )
    ).scalar_one_or_none()
    
    if not membership:
        membership = FirmMembership(
            firm_id=DEV_FIRM_ID,
            user_id=DEV_USER_ID,
            role="partner",
            created_at=datetime.now(timezone.utc),
        )
        db.add(membership)
        db.flush()
        results["membership_created"] = True
    else:
        # Ensure role is correct
        if membership.role != "partner":
            membership.role = "partner"
            results["membership_updated"] = True

    # 4. Ensure test clients belong to test_firm
    clients = db.execute(
        select(Client).where(Client.tenant_id != DEV_FIRM_ID)
    ).scalars().all()
    
    for client in clients:
        client.tenant_id = DEV_FIRM_ID
        client.firm_id = DEV_FIRM_ID
        client.updated_at = datetime.now(timezone.utc)
        results["clients_updated"] += 1

    db.commit()
    return results


def main():
    """Main entry point."""
    print("=" * 60)
    print("TaxTrace Development Database Seed")
    print("=" * 60)
    
    db = next(get_db())
    try:
        results = seed_dev_data(db)
        
        print("\nResults:")
        for key, value in results.items():
            if value:
                print(f"  {key}: {value}")
        
        # Verify
        db = next(get_db())
        firm = db.execute(select(Firm).where(Firm.id == DEV_FIRM_ID)).scalar_one_or_none()
        user = db.execute(select(User).where(User.id == DEV_USER_ID)).scalar_one_or_none()
        membership = db.execute(
            select(FirmMembership).where(
                FirmMembership.firm_id == DEV_FIRM_ID,
                FirmMembership.user_id == DEV_USER_ID
            )
        ).scalar_one_or_none()
        clients = db.execute(select(Client).where(Client.tenant_id == DEV_FIRM_ID)).scalars().all()
        
        print("\nVerification:")
        print(f"  Firm: {firm.id if firm else 'MISSING'} ({firm.name if firm else 'N/A'})")
        print(f"  User: {user.id if user else 'MISSING'} ({user.email if user else 'N/A'})")
        print(f"  Membership: {'EXISTS' if membership else 'MISSING'}")
        print(f"  Clients in test_firm: {len(clients)}")
        
        if firm and user and membership and len(clients) >= 3:
            print("\n✅ All verification checks passed!")
            return 0
        else:
            print("\n❌ Verification failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())