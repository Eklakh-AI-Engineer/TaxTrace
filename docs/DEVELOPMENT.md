# TaxTrace Development

## Backend

Requirements: Python 3.11+.

Typical setup:

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# Linux/macOS
source .venv/bin/activate

pip install -e ".[test]"
```

Run backend tests:

```bash
pytest backend/tests/ -q
```

## Frontend

The frontend uses Node.js with Next.js 16 / React 19.

```bash
cd frontend
npm install
npm run dev
```

Build:

```bash
npm run build
```

Tests:

```bash
npx vitest run
```

## Docker

The repository contains development and production-oriented Docker Compose definitions.

```bash
docker compose up --build
```

## Database / migrations

Alembic migrations live under `migrations/`.

Do not manually mutate production schemas when a migration is required. Add a reversible migration and verify it against the supported database workflow.

## Verification workflow

Before a change is considered complete:

1. run focused backend tests;
2. run relevant frontend tests;
3. run reconciliation/AI quality gates when affected;
4. check tenant isolation for data-access changes;
5. review security impact;
6. update current documentation;
7. use a pull request for integration.

Never commit real client/tax data or credentials.
