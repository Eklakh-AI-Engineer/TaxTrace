# Repository Structure

**Version:** 1.0

---

# 1. Recommended Repository

```text
ai-ca-compliance/
├── README.md
├── AGENTS.md
├── CHANGELOG.md
├── pyproject.toml
├── package.json
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .dockerignore
│
├── docs/
│   ├── PROJECT_BRIEF.md
│   ├── PRD.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── TECH_STACK.md
│   ├── REPO_STRUCTURE.md
│   ├── DATA_SPEC.md
│   ├── API_SPEC.md
│   ├── UI_SPEC.md
│   ├── EVALUATION_PLAN.md
│   ├── TESTING_STRATEGY.md
│   ├── SECURITY.md
│   ├── DECISIONS.md
│   ├── ROADMAP.md
│   └── CODING_RULES.md
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── api/
│   │   ├── auth/
│   │   ├── firms/
│   │   ├── clients/
│   │   ├── documents/
│   │   ├── transactions/
│   │   ├── reconciliation/
│   │   ├── notices/
│   │   ├── knowledge/
│   │   ├── ai/
│   │   ├── tasks/
│   │   ├── audit/
│   │   └── common/
│   └── tests/
│       ├── unit/
│       ├── integration/
│       ├── contract/
│       └── fixtures/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── lib/
│   ├── hooks/
│   ├── types/
│   └── tests/
│
├── workers/
│   ├── document_worker.py
│   ├── reconciliation_worker.py
│   ├── notice_worker.py
│   └── tasks/
│
├── knowledge/
│   ├── sources/
│   ├── manifests/
│   ├── processed/
│   └── evaluation/
│
├── scripts/
│   ├── seed_dev.py
│   ├── ingest_knowledge.py
│   └── benchmark_reconciliation.py
│
├── migrations/
│
└── infra/
    ├── docker/
    ├── ci/
    └── deployment/
```

---

# 2. Backend Module Rules

Each domain module should preferably contain:

```text
router.py
schemas.py
models.py
service.py
repository.py
rules.py
exceptions.py
```

Only create files that are justified.

---

# 3. Dependency Direction

Preferred:

```text
API
 ↓
Application Service
 ↓
Domain Logic
 ↓
Repository / Infrastructure
```

Do not:

```text
Router → raw SQL
Router → LLM SDK
UI → database
Domain → FastAPI request objects
```

---

# 4. Domain Ownership

| Domain | Owns |
|---|---|
| firms | firm settings and membership |
| clients | client identity |
| documents | file metadata and processing |
| transactions | canonical financial records |
| reconciliation | matching and exception rules |
| notices | notice cases and drafts |
| knowledge | source ingestion/retrieval |
| ai | model/provider abstraction |
| tasks | workflow tasks |
| audit | immutable business events |

---

# 5. Tests

Mirror source structure where practical.

Example:

```text
backend/app/reconciliation/service.py
backend/tests/unit/reconciliation/test_service.py
```

Fixtures should be synthetic or authorized/anonymized.

---

# 6. Documentation

Architecture decisions belong in `DECISIONS.md`.

Feature behavior belongs in `PRD.md`.

API contract belongs in `API_SPEC.md`.

Data schema belongs in `DATA_SPEC.md`.

Do not duplicate authoritative definitions across many documents.
