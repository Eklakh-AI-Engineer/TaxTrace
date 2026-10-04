# TaxTrace Phase 1 — Pilot-Ready Baseline

**Tag:** `v0.1.0-pilot`  
**Date:** 2026-10-04  
**Commit:** `<to be filled after commit>`  
**Branch:** `main`

---

## 🎯 Phase 1 Objective

Deliver a **pilot-ready** AI Compliance Execution Platform for small Indian CA firms with the complete MVP workflow:

> **Upload → Reconcile → Review → Export** (Purchase Register + GSTR-2B)  
> **Notice → Extract → Draft → Approve** (Compliance notices)  
> **Tasks → Kanban → Message** (Follow-up workflow)  
> **WhatsApp Simulator** (Channel preview)

All quality gates pass. No production deployment — controlled pilot only.

---

## ✅ Definition of Done (DoD) — All Verified

| DoD Item | Status | Evidence |
|----------|--------|----------|
| Implementation exists | ✅ | 134 backend tests, 15 frontend tests passing |
| Tests exist | ✅ | Backend: 134 tests (pytest), Frontend: 15 tests (Vitest) |
| Relevant tests pass | ✅ | `pytest backend/tests/ -q` → 134 passed; `vitest run` → 15 passed |
| Security considered | ✅ | Tenant isolation at every query layer (6 isolation tests); path traversal protection; HMAC webhook validation; JWT auth with dev-mode bypass |
| Docs updated | ✅ | `PILOT_ONBOARDING.md`, `docs/milestones/PHASE_1_PILOT_READY.md` |
| No known blocking issue hidden | ✅ | All gate checks pass; benchmark 100% precision/recall |

---

## 📊 Validation Results

### Backend Tests (134 passed)
```
pytest backend/tests/ -q
→ 134 passed, 5 warnings in ~4.1s
```
Includes:
- 95 core tests (auth, tenants, documents, reconciliation, notices, tasks, audit, permissions, storage, knowledge RAG)
- 7 benchmark gate tests (`test_benchmark_gates.py`)
- 32 AI quality gate tests (`test_ai_quality_gates.py`)

### Frontend Tests (15 passed)
```
npx vitest run
→ 3 test files, 15 tests passed in ~5.6s
```
- 8 `TaskCard` component tests
- 3 `ExceptionsPage` integration tests
- 4 `utils` unit tests

### Reconciliation Benchmark (100% gates)
```
python evaluations/benchmark_reconciliation.py
→ ALL GATES PASSED

Exception Type       Precision    Recall      F1
matched              1.000        1.000       1.000
missing_in_2b        1.000        1.000       1.000
value_mismatch       1.000        1.000       1.000

Gates: precision ≥ 0.90, recall ≥ 0.85 → ALL PASS
```
Dataset: 200 book transactions, 181 portal transactions, 200 ground truth labels.

### AI Quality Gates (100% pass)
- Unsupported claim rate: **0%** (gate: < 5%)
- Fact/hypothesis separation: **100%** (gate: > 90%)
- Confidence scoring: **100%** (gate: 100%)
- Evidence linking: **100%** (gate: 100%)
- Citation pass rate: **100%** (gate: > 90%)
- Missing info flagged: **100%** (gate: 100%)
- No fabrication: **100%** (gate: 100%)

---

## 🏗️ Implemented Scope (Phase 1)

### Stage 0 — Scaffolding ✅
- Python/FastAPI backend, Next.js 16 frontend, Docker Compose, pyproject.toml

### Stage 1 — Core Domain & Tenant Safety ✅
- 12 PostgreSQL tables (firms, users, clients, periods, documents, transactions, matches, exceptions, evidence, notice_cases, knowledge_sources, tasks, audit_events, knowledge_chunks)
- All tables tenant-scoped (`tenant_id = firm_id`)
- Alembic migrations (3)
- JWT auth + role-based access (owner/partner/staff/viewer)

### Stage 2 — Document Ingestion & Normalization ✅
- CSV/JSON upload with validation, SHA-256 hashing, duplicate detection
- LocalStorage backend with tenant isolation + path traversal protection
- Flexible CSV parser (Indian CA column mappings)
- GSTR-2B JSON parser (GSTN schema)
- Canonical transaction schema

### Stage 3 — Deterministic Reconciliation Engine ✅
- 4-pass matching: Exact → Normalized Value → Controlled Fuzzy → Unmatched
- Exception types: MATCHED, PARTIAL_MATCH, VALUE_MISMATCH, MISSING_IN_2B, MISSING_IN_BOOKS, DUPLICATE, REVIEW_REQUIRED
- Rule versioning recorded per run
- **No LLM decides financial truth**

### Stage 4 — Exception Review Workspace ✅
- Filtered, paginated exception listing
- Detail view with evidence panel (book vs portal side-by-side)
- Decision actions: Accept, Reject, Needs Info
- Dashboard metrics

### Stage 5 — AI Explanation Layer ✅
- Evidence-grounded explanations with fact/hypothesis separation
- Confidence scoring, uncertainty handling
- Audit logging for every AI generation

### Stage 6 — Notice Intelligence & Drafting ✅
- PDF/text notice upload → deterministic fact extraction (GSTIN, DIN, sections, dates, amounts)
- RAG retrieval from knowledge base (pgvector + cosine similarity)
- Citation-backed draft generation with missing info flags
- Partner-only approval workflow + audit trail

### Stage 7 — Tasks & Follow-up ✅
- Task CRUD with status lifecycle (open → in_progress → blocked → completed)
- Kanban board UI with drag-to-move columns
- Due dates, overdue highlighting, owner assignment
- AI vendor/client message drafting (email/WhatsApp)

### Stage 8 — WhatsApp Channel Layer ✅
- Channel adapter abstraction (WhatsApp Cloud API + Mock)
- Bot command router: help, pending tasks, review tasks, show deadlines, explain mismatch
- Webhook signature validation (HMAC-SHA256)
- Web-based WhatsApp simulator

### Evaluation Infrastructure ✅
- Synthetic pilot dataset generator (200 transactions, 70/10/10/10 split)
- 200-row ground truth benchmark
- Benchmark script + CI gate tests

---

## 📁 Key Files Added in Phase 1

```
evaluations/
  benchmark_reconciliation.py          # Benchmark runner
  datasets/pilot_books.csv             # 200 synthetic PR rows
  datasets/pilot_gstr2b.csv            # 181 synthetic GSTR-2B rows
  datasets/ground_truth.json           # 200 expected labels
  generate_pilot_dataset.py            # Dataset generator

backend/
  scripts/seed_knowledge_base.py       # 8 official sources → 17 chunks
  tests/test_benchmark_gates.py        # 7 benchmark gate tests
  tests/test_ai_quality_gates.py       # 32 AI quality gate tests

frontend/
  vitest.config.ts / vitest.setup.ts   # Test config
  src/lib/period-context.tsx           # Period selector context
  src/components/TaskCard.tsx          # Extracted TaskCard component
  src/components/__tests__/TaskCard.test.tsx
  src/app/exceptions/__tests__/ExceptionsPage.test.tsx
  src/app/notices/[id]/page.tsx        # Notice detail + draft UI
  src/app/notices/page.tsx             # Notice list
  src/lib/api.ts                       # Extended with notice/draft/export APIs

PILOT_ONBOARDING.md                    # End-to-end pilot guide
docs/milestones/PHASE_1_PILOT_READY.md # This document
```

---

## 🔐 Security Baseline

- **Tenant isolation**: Every business query filters by `tenant_id = auth.firm_id` (verified by 6 isolation tests)
- **Auth**: JWT (production) + dev-mode token (`dev.<user>.<firm>.<role>`)
- **File storage**: Random UUID keys, tenant-isolated paths, SHA-256 at rest
- **Webhooks**: HMAC-SHA256 signature validation
- **Audit trail**: Append-only events for all consequential actions
- **AI safety**: Explanations grounded in evidence; drafts editable; human approval required

---

## ⚠️ Known Limitations (Pilot)

| Limitation | Mitigation |
|------------|------------|
| CSV/JSON only (no PDF OCR) | Provided CSV datasets |
| Single-period view | Period selector in UI |
| Mock AI provider only | Template-based explanations |
| No Tally/Busy direct import | Export to CSV first |
| Single-tenant demo | Data isolated per firm |
| XLSX parser not implemented | Use CSV export |

---

## 🚀 Next: Phase 2 (Production Hardening)

Phase 2 will address:
1. Security review & penetration testing
2. Production AI provider (Anthropic/OpenAI) with cost tracking
3. Observability (structured logs, Prometheus metrics, Grafana dashboards)
4. Data retention/deletion flows
5. Backup/restore validation
6. CI/CD pipeline to staging/production
7. Load testing & performance baselines

**Do not start Phase 2 until pilot feedback is collected and reviewed.**

---

## 📌 Commit & Tag

```bash
# After this document is committed:
git tag -a v0.1.0-pilot -m "TaxTrace Phase 1 — Pilot-Ready baseline"
git push origin main --tags
```

**Verification:**
- Tag points to this commit
- Working tree clean
- All 149 tests pass
- Benchmark gates pass