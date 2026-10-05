# TaxTrace API

## API boundary

The FastAPI application under `backend/app/api/` is the authoritative runtime API surface.

Current route families include:

- health;
- authentication / users;
- firms / clients / periods;
- document ingestion and download;
- reconciliation;
- exceptions and decisions;
- notices and drafts;
- knowledge search / sources;
- tasks;
- dashboard;
- settings;
- audit-related operations.

See the runtime routers under `backend/app/api/` for current behavior.

## Consequential actions

The API must preserve human approval boundaries for consequential compliance outputs.

Draft generation is not equivalent to approval.

## Development verification

Use the backend test suite and focused API tests when modifying routes:

```bash
pytest backend/tests/ -q
```

The original API specification is retained in the archived specification set.
