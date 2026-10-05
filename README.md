# TaxTrace — AI Compliance Execution Platform

> **AI prepares. Evidence explains. CA approves.**

TaxTrace is an evidence-first compliance execution platform for small Indian CA firms. Its current pilot baseline combines deterministic GST reconciliation, evidence-grounded AI assistance, notice drafting, task workflows, and a Next.js review interface.

## Current status

**Current milestone: Phase 1 — Pilot-Ready Baseline.**

This is a **controlled-pilot application**, not a production tax/legal decision-maker.

| Capability | Status |
|---|---|
| FastAPI backend | Implemented |
| Next.js 16 / React 19 frontend | Implemented |
| Tenant-aware domain model | Implemented |
| JWT authentication / role permissions | Implemented |
| Purchase Register + GSTR-2B ingestion | Implemented for CSV/JSON |
| Deterministic reconciliation | Implemented |
| Exception review workflow | Implemented |
| Evidence-grounded AI explanations | Implemented with mock provider in verification |
| Notice extraction / draft workflow | Implemented within pilot/mock boundaries |
| Tasks / dashboard / follow-up | Implemented |
| Knowledge/RAG API surface | Implemented; production ingestion/provider scope remains limited |
| WhatsApp channel abstraction / simulator | Implemented |
| PostgreSQL / Alembic path | Implemented in repository; deployment hardening remains |
| Controlled pilot readiness | **Documented as complete** |
| Production deployment | **Not claimed** |
| External security review | Pending |
| Production AI provider + cost controls | Pending |
| Staging / observability / backup validation | Pending |

## Product principle

TaxTrace deliberately separates:

```text
Input
  ↓
Validate
  ↓
Extract / Normalize
  ↓
Deterministic processing
  ↓
Retrieve evidence
  ↓
AI assistance
  ↓
Verify
  ↓
CA approval
  ↓
Audit trail
```

The reconciliation engine does not delegate financial truth to an LLM.

---

## Core workflows

### Reconcile

```text
Purchase Register + GSTR-2B
          ↓
Normalization
          ↓
Deterministic Matching
          ↓
Exception Classification
          ↓
Evidence
          ↓
Review / Decision
          ↓
Export
```

### Respond

```text
Notice
  ↓
Structured extraction
  ↓
Evidence / knowledge retrieval
  ↓
Draft
  ↓
Citation / evidence checks
  ↓
CA approval
```

### Follow up

Tasks connect exceptions and notice cases to owners, due dates, lifecycle states, dashboard monitoring, and communication drafts.

---

## Current technical stack

### Backend

- Python 3.11+
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic / pydantic-settings
- JWT authentication
- pytest

### Frontend

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS 4
- TanStack React Query
- Vitest / Testing Library

### Data / infrastructure

- SQLite-backed development/test path
- PostgreSQL-oriented schema/migrations
- pgvector-oriented knowledge/RAG design
- Docker Compose

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

---

## Verification baseline

The current pilot milestone records:

- **134 backend tests passing**
- **15 frontend tests passing**
- **7 reconciliation benchmark gate tests passing**
- **32 AI quality gate tests passing**
- security audit checks recorded as passing
- frontend production build passing

These are **recorded milestone results**, not a claim that this documentation PR freshly executed the full suite.

Run the current backend tests:

```bash
pytest backend/tests/ -q
```

Run the frontend tests:

```bash
cd frontend
npm install
npx vitest run
```

Run the reconciliation benchmark:

```bash
python evaluations/benchmark_reconciliation.py
```

---

## Repository structure

```text
TaxTrace/
├── backend/
│   ├── app/
│   ├── scripts/
│   └── tests/
├── frontend/
├── migrations/
├── evaluations/
├── docs/
│   ├── README.md
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   ├── EVALUATION.md
│   ├── SECURITY.md
│   ├── API.md
│   ├── milestones/
│   └── history/
├── .env.example
├── docker-compose.yml
├── pyproject.toml
└── AGENTS.md
```

The detailed product/specification corpus is preserved in the repository history area rather than being confused with current runtime status.

---

## Documentation

| Document | Purpose |
|---|---|
| [Documentation index](docs/README.md) | Current documentation map |
| [Architecture](docs/ARCHITECTURE.md) | Implemented system boundaries |
| [Development](docs/DEVELOPMENT.md) | Local setup and verification |
| [Evaluation](docs/EVALUATION.md) | Benchmarks and AI quality gates |
| [Security](docs/SECURITY.md) | Security boundary and pilot limitations |
| [API](docs/API.md) | API surface and contract sources |
| [Pilot milestone](docs/milestones/PHASE_1_PILOT_READY.md) | Recorded pilot-ready evidence |
| [History](docs/history/README.md) | Archived audits and superseded planning documents |

---

## Pilot limitations

The documented pilot baseline still has explicit limitations, including:

- CSV/JSON ingestion rather than a complete document-OCR pipeline;
- mocked/local AI provider in verification;
- production AI provider and cost tracking pending;
- external security review pending;
- production observability pending;
- backup/restore validation pending;
- staging/production CI/CD pending;
- direct Tally/Busy integrations deferred;
- production deployment not claimed.

These limitations are part of the product's current status, not footnotes to be hidden.

---

## Security and privacy

TaxTrace may eventually process sensitive financial and tax information.

Development rules:

- use synthetic/anonymized data for development;
- never commit client documents or secrets;
- keep tenant isolation at every data access layer;
- avoid sensitive document contents in logs;
- review AI provider data handling before production;
- require CA/human approval for consequential professional output.

See [docs/SECURITY.md](docs/SECURITY.md).

---

## Disclaimer

TaxTrace is assistive software. It is not a substitute for a qualified CA, tax professional, or legal counsel. AI-generated explanations and drafts must be reviewed before professional or external use.

---

## License

See the repository license and contribution documents for project terms.
