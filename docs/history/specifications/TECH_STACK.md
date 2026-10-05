# Technology Stack

**Version:** 1.0

---

# 1. Recommended Stack

| Layer | Recommendation | Reason |
|---|---|---|
| Backend | Python + FastAPI | Strong fit for AI/data workflows and async APIs |
| Database | PostgreSQL | Relational integrity + mature ecosystem |
| Managed DB option | Supabase PostgreSQL | Fast MVP development |
| ORM | SQLAlchemy 2.x | Explicit data model and migration-friendly |
| Migrations | Alembic | Version-controlled schema |
| Validation | Pydantic v2 | Typed API/domain schemas |
| Queue | Celery + Redis or equivalent | Background processing |
| Object storage | S3-compatible / Supabase Storage | Source documents and artifacts |
| Frontend | Next.js/React + TypeScript | Review-heavy web UI |
| Styling | Tailwind CSS or project-approved UI system | Fast consistent UI |
| LLM | Provider-agnostic gateway; Claude/GPT initially | Avoid vendor lock-in |
| RAG | PostgreSQL + pgvector initially | Reduce infrastructure |
| OCR | Pluggable OCR provider + PDF text extraction | Mixed document quality |
| PDF | Python PDF parser stack | Document processing |
| Testing | pytest + API integration tests + Playwright | Layered testing |
| Formatting | Ruff/Black or Ruff formatter | Consistent Python |
| Type checking | mypy/pyright | Safer backend |
| Frontend lint | ESLint | Code quality |
| Containers | Docker | Reproducible environment |
| CI | GitHub Actions | Automated quality gates |
| Monitoring | Structured logs + OpenTelemetry-compatible tooling | Debugging and observability |

---

# 2. Python Version

Use a currently supported Python 3.x release selected at implementation start.

Pin the version in:
- `.python-version`;
- `pyproject.toml`;
- Docker image;
- CI.

Do not allow local and CI Python versions to drift.

---

# 3. Backend Rules

FastAPI should handle:

- authentication boundary;
- API routing;
- schema validation;
- service orchestration;
- response serialization.

Business logic should live in service/domain modules, not route functions.

---

# 4. Database

Use PostgreSQL for:

- firms;
- users;
- clients;
- periods;
- documents;
- transactions;
- matches;
- exceptions;
- notices;
- drafts;
- tasks;
- audit events;
- knowledge-source metadata.

Use migrations for every schema change.

Never manually modify production schema without a corresponding migration.

---

# 5. Object Storage

Store:

- uploaded originals;
- normalized export artifacts;
- generated drafts;
- generated reports.

Store metadata in PostgreSQL.

Never make the object filename the source of truth.

---

# 6. LLM Provider Strategy

Use an abstraction:

```python
class LLMProvider:
    async def generate_structured(...): ...
    async def generate_text(...): ...
```

Domain code should call:

```text
llm_gateway.generate_structured(...)
```

not a vendor SDK directly.

---

# 7. Model Routing

Use deterministic logic before LLM calls.

Suggested routing:

| Task | Default |
|---|---|
| Numeric comparison | Code |
| GSTIN equality | Code |
| Invoice normalization | Code + deterministic rules |
| Fuzzy candidate generation | Algorithm |
| Document classification | Small/fast LLM or classifier |
| Explanation | Strong LLM |
| Legal draft | Strong LLM + RAG |
| Citation verification | Code + retrieval |

---

# 8. RAG

Initial recommendation:

- PostgreSQL;
- pgvector;
- source metadata;
- chunk hashes;
- embeddings;
- lexical fallback;
- retrieval logging.

A separate vector database should only be introduced when scale or retrieval quality requires it.

---

# 9. WhatsApp

Use an official/authorized WhatsApp Business integration.

The adapter should convert incoming messages into internal commands/events.

Never let WhatsApp-specific payloads leak throughout the domain layer.

---

# 10. Configuration

Environment variables should cover:

```text
APP_ENV
DATABASE_URL
REDIS_URL
OBJECT_STORAGE_URL
OBJECT_STORAGE_BUCKET
OBJECT_STORAGE_ACCESS_KEY
OBJECT_STORAGE_SECRET_KEY
LLM_PROVIDER
LLM_API_KEY
WHATSAPP_PROVIDER
WHATSAPP_VERIFY_TOKEN
WHATSAPP_ACCESS_TOKEN
JWT_SECRET
```

Never commit secrets.

Provide `.env.example`, never `.env`.

---

# 11. Development Environments

Required:

- local;
- test;
- staging;
- production.

Production data must never be copied to local development without explicit authorization and approved anonymization.

---

# 12. Dependency Policy

Every dependency should have a reason.

Prefer stable, actively maintained libraries.

Pin production dependencies sufficiently to make builds reproducible.

Run dependency vulnerability scans in CI.
