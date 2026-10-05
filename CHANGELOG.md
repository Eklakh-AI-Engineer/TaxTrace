# Changelog

All notable project changes are documented here.

## [Unreleased]

### Documentation
- Reframed the repository around the current pilot-ready implementation.
- Added maintained architecture, development, evaluation, security, and API documentation.
- Archived superseded pre-build specifications and historical audits under `docs/history/`.

### Current implementation baseline
- FastAPI backend with tenant-aware domain services.
- Next.js 16 / React 19 frontend.
- Deterministic GST reconciliation.
- Evidence-grounded AI assistance and notice drafting.
- Tasks, dashboard, follow-up, and WhatsApp channel abstraction.
- Alembic migration path and current Stage 6 schema additions.

### Verification
The current pilot milestone records:
- 134 backend tests passing;
- 15 frontend tests passing;
- 7 reconciliation benchmark gate tests passing;
- 32 AI quality gate tests passing;
- passing security checks and frontend production build.

These are recorded milestone results; they are not represented as freshly executed by this documentation change.

### Production work still pending
- external security review;
- staging/production CI/CD;
- observability and operational monitoring;
- backup/restore validation;
- production AI provider and cost controls;
- direct external integrations and production deployment.

## Historical baseline

The original pre-build product, architecture, and implementation specifications are preserved under:

```text
docs/history/specifications/
```

Historical audits are preserved under:

```text
docs/history/audits/
```

See [docs/history/README.md](docs/history/README.md) for interpretation rules.
