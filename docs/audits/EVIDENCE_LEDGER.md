# TaxTrace Evidence Ledger

## Purpose

This directory records verified engineering evidence and the project's current development interpretation.

## Evidence sources

| Evidence | Date | Scope | Status |
|---|---|---|---|
| Independent audit | 2026-10-05 | Repository at commit `81d3613` | Recorded |
| Phase 1 milestone | 2026-10-04 | Current implementation baseline | Recorded |
| Reconciliation benchmark | 2026-10-05 audit record | Synthetic reconciliation dataset | Recorded: 1.000 precision/recall on reported classes |
| Backend tests | 2026-10-05 audit record | `backend/tests/` | Recorded: 134 passed |
| Frontend tests | 2026-10-05 audit record | Vitest | Recorded: 15 passed |
| TypeScript | 2026-10-05 audit record | `tsc --noEmit` | Recorded: exit 0 |
| Security audit | 2026-10-05 audit record | Backend security audit | Recorded: 5/5 pass |

## Current development objective

**TaxTrace is currently a local-run development project.**

The evidence supports a strong deterministic reconciliation core and a working full-stack development implementation. It does **not** establish production readiness.

### Local-development priorities

1. Reproducible local installation and dependency declarations.
2. Deterministic reconciliation correctness.
3. Real local AI-provider integration behind the existing abstraction.
4. PDF/XLSX intake where required by the local MVP.
5. RAG/citation verification.
6. End-to-end frontend/backend workflow verification.
7. Accurate status documentation.

### Explicitly deferred

Production-only or pilot-hardening work such as external penetration testing, production deployment, backup/restore drills, staging infrastructure, real WhatsApp Business API, and Tally/accounting integrations are not immediate local-development requirements.

## Evidence rules

- **Verified** means the audit recorded direct execution or repository inspection.
- **Recorded** means the result is preserved from a prior verification run and must be rerun before being presented as a fresh result.
- **Mocked/partial** must remain labeled as such.
- Do not claim production readiness from local-development evidence.
- When implementation changes, rerun relevant tests and update this ledger.
