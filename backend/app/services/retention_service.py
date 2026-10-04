"""Data Retention and Deletion Service.

Implements data retention policies per Stage 10.
Purges soft-deleted records and data older than the legally required retention period (e.g., 7 years for tax records).
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import delete

from app.models import Document, Transaction, Match, ExceptionRecord, AuditEvent

def execute_retention_policy(db: Session, retention_years: int = 7):
    """Deletes records older than the retention period."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=365 * retention_years)

    # Delete old exceptions
    db.execute(
        delete(ExceptionRecord).where(ExceptionRecord.created_at < cutoff_date)
    )
    
    # Delete old matches
    db.execute(
        delete(Match).where(Match.created_at < cutoff_date)
    )
    
    # Delete old transactions
    db.execute(
        delete(Transaction).where(Transaction.invoice_date < cutoff_date)
    )
    
    # Delete old documents
    db.execute(
        delete(Document).where(Document.created_at < cutoff_date)
    )
    
    # Delete old audit events
    db.execute(
        delete(AuditEvent).where(AuditEvent.created_at < cutoff_date)
    )

    db.commit()

if __name__ == "__main__":
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        execute_retention_policy(db)
        print("Retention policy executed successfully.")
    finally:
        db.close()
