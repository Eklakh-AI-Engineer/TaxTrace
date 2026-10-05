# TaxTrace Architecture

## 1. Product boundary

TaxTrace is an evidence-first compliance workflow system.

The architectural invariant is:

```text
AI prepares
   ↓
Evidence explains
   ↓
CA approves
   ↓
Audit trail records
```

## 2. Current workflow

### Reconciliation

```text
Purchase Register / GSTR-2B
        ↓
Document validation
        ↓
Normalization
        ↓
Deterministic reconciliation
        ↓
Exception records + evidence
        ↓
Exception review workspace
        ↓
Human decision
        ↓
Export / follow-up
```

### Notice workflow

```text
Notice input
    ↓
Fact extraction
    ↓
Evidence / knowledge retrieval
    ↓
Grounded draft
    ↓
Missing-information / citation handling
    ↓
Partner / CA approval
    ↓
Audit trail
```

### Follow-up

```text
Exception / Notice
      ↓
Task
      ↓
Owner + due date
      ↓
Lifecycle
      ↓
Dashboard / message draft
```

## 3. Backend layers

The current backend is organized around:

- API routers;
- authentication / permissions;
- SQLAlchemy domain models;
- service modules;
- parsers and normalization;
- reconciliation engine;
- AI provider abstraction;
- notice intelligence;
- knowledge/retrieval interfaces;
- audit logging;
- storage;
- migrations.

Tenant isolation is a cross-cutting invariant: business queries should be scoped to the authenticated firm's tenant.

## 4. Frontend

The frontend is a Next.js 16 / React 19 application with TypeScript, Tailwind CSS, React Query, and Vitest tooling.

The pilot UI includes workflows for reconciliation, exceptions, clients, notices, knowledge, tasks, and settings.

## 5. Database and migrations

The repository contains Alembic migrations and a PostgreSQL-oriented schema. The Stage 6 schema additions include task descriptions, exception/notice foreign keys, and a drafts table.

Migration presence does not by itself prove a production database deployment; deployment hardening remains a separate milestone.

## 6. AI boundary

AI components are provider-agnostic and consume structured evidence. The deterministic reconciliation engine remains the source of financial truth.

AI output must be:

- evidence-grounded;
- structured;
- auditable;
- reviewable;
- subject to human approval where consequential.

## 7. Production boundary

The pilot-ready milestone does **not** equal production readiness.

Production still requires external security review, staging deployment, observability, backup/restore validation, production AI-provider controls, and operational hardening.
