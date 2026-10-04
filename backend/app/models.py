from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    func,
)
from typing import Any
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.database import Base


class Firm(Base):
    __tablename__ = "firms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    plan: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    memberships: Mapped[list["FirmMembership"]] = relationship(back_populates="firm", cascade="all, delete-orphan")
    clients: Mapped[list["Client"]] = relationship(back_populates="firm", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    memberships: Mapped[list["FirmMembership"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class FirmMembership(Base):
    __tablename__ = "firm_memberships"
    __table_args__ = (PrimaryKeyConstraint("firm_id", "user_id"),)

    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="staff", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    firm: Mapped["Firm"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="memberships")


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gstin: Mapped[str | None] = mapped_column(String(30), nullable=True)
    pan_reference: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    firm: Mapped["Firm"] = relationship(back_populates="clients")


class Period(Base):
    __tablename__ = "periods"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    financial_year: Mapped[str] = mapped_column(String(50), nullable=False)
    tax_period: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), nullable=False)
    period_id: Mapped[str | None] = mapped_column(ForeignKey("periods.id"), nullable=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(255), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Numeric(precision=20), nullable=False)
    processing_status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False)
    uploaded_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), nullable=False)
    period_id: Mapped[str] = mapped_column(ForeignKey("periods.id"), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source_document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)
    source_row_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supplier_gstin: Mapped[str | None] = mapped_column(String(30), nullable=True)
    invoice_number_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_number_normalized: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    taxable_value: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=2), nullable=True)
    cgst: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=2), nullable=True)
    sgst: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=2), nullable=True)
    igst: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=2), nullable=True)
    cess: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False)
    period_id: Mapped[str] = mapped_column(ForeignKey("periods.id"), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    book_transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.id"), nullable=False)
    portal_transaction_id: Mapped[str | None] = mapped_column(ForeignKey("transactions.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="candidate", nullable=False)
    match_score: Mapped[float | None] = mapped_column(Numeric(precision=10, scale=4), nullable=True)
    rule_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ExceptionRecord(Base):
    __tablename__ = "exceptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False)
    period_id: Mapped[str] = mapped_column(ForeignKey("periods.id"), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    match_id: Mapped[str | None] = mapped_column(ForeignKey("matches.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_system: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    exception_id: Mapped[str | None] = mapped_column(ForeignKey("exceptions.id"), nullable=True)
    notice_case_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    evidence_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_document_id: Mapped[str | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    source_row_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_field: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NoticeCase(Base):
    __tablename__ = "notice_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), nullable=False)
    period_id: Mapped[str | None] = mapped_column(ForeignKey("periods.id"), nullable=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source_document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)
    notice_type: Mapped[str] = mapped_column(String(100), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    issue_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    response_deadline: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="received", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    effective_from: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False)
    client_id: Mapped[str | None] = mapped_column(ForeignKey("clients.id"), nullable=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    exception_id: Mapped[str | None] = mapped_column(ForeignKey("exceptions.id"), nullable=True)
    notice_case_id: Mapped[str | None] = mapped_column(ForeignKey("notice_cases.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)
    owner_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id: Mapped[str] = mapped_column(ForeignKey("knowledge_sources.id"), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    section_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding: Mapped[Any | None] = mapped_column(Vector(384), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    source: Mapped["KnowledgeSource"] = relationship()
