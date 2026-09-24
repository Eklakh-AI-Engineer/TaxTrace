# API Specification

**Version:** 1.0  
**Style:** REST/JSON  
**Base path:** `/api/v1`

---

# 1. API Conventions

## Authentication

Use bearer authentication:

```http
Authorization: Bearer <token>
```

Every request resolves:

```text
user → membership → firm → authorization
```

## Common Headers

```http
X-Request-ID: <uuid>
Idempotency-Key: <uuid>   # required for side-effecting retryable operations
```

## Common Error

```json
{
  "error": {
    "code": "DOCUMENT_INVALID",
    "message": "The uploaded file could not be processed.",
    "request_id": "req_123",
    "details": {}
  }
}
```

---

# 2. Health

## GET `/health`

Response:

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

Do not expose secrets or database credentials.

---

# 3. Firms

## GET `/firms/me`

Returns current firm context.

## PATCH `/firms/me`

Updates permitted firm settings.

---

# 4. Clients

## GET `/clients`

Query:

```text
status
search
page
page_size
```

## POST `/clients`

Request:

```json
{
  "display_name": "Example Traders",
  "gstin": "GSTIN",
  "status": "active"
}
```

## GET `/clients/{client_id}`

## PATCH `/clients/{client_id}`

---

# 5. Documents

## POST `/documents`

Multipart upload.

Required metadata:

```text
client_id
period_id
document_type
file
```

Response:

```json
{
  "document_id": "doc_123",
  "status": "queued",
  "content_hash": "sha256:..."
}
```

## GET `/documents/{document_id}`

Returns processing state.

## GET `/documents/{document_id}/download`

Requires authorization.

---

# 6. Reconciliation

## POST `/reconciliations`

```json
{
  "client_id": "client_123",
  "period_id": "period_123",
  "book_document_id": "doc_books",
  "gstr2b_document_id": "doc_2b",
  "rule_version": "recon-v1"
}
```

Response:

```json
{
  "reconciliation_id": "rec_123",
  "status": "queued"
}
```

## GET `/reconciliations/{reconciliation_id}`

Returns:

```json
{
  "id": "rec_123",
  "status": "completed",
  "summary": {
    "matched": 1200,
    "partial_match": 24,
    "missing_in_2b": 41,
    "missing_in_books": 13,
    "duplicates": 3
  }
}
```

## GET `/reconciliations/{id}/exceptions`

Filters:

```text
type
severity
status
supplier_gstin
min_value
max_value
page
page_size
```

---

# 7. Exception

## GET `/exceptions/{exception_id}`

Returns:

- exception;
- classification;
- evidence;
- matching rule;
- source records;
- audit history.

## POST `/exceptions/{exception_id}/decision`

```json
{
  "decision": "accepted",
  "comment": "Verified against supplier communication."
}
```

Allowed decisions:
- accepted;
- rejected;
- resolved;
- needs_info.

Every decision creates an audit event.

---

# 8. AI Explanation

## POST `/exceptions/{exception_id}/explanation`

```json
{
  "mode": "concise"
}
```

Response:

```json
{
  "explanation_id": "exp_123",
  "summary": "...",
  "facts": [],
  "possible_causes": [],
  "suggested_next_steps": [],
  "confidence": 0.84,
  "evidence_ids": ["ev_1", "ev_2"]
}
```

The response must distinguish evidence-backed facts from hypotheses.

---

# 9. Notices

## POST `/notices`

Upload a notice PDF.

## GET `/notices/{notice_case_id}`

Returns structured notice metadata.

## POST `/notices/{notice_case_id}/extract`

Starts/retries extraction.

## POST `/notices/{notice_case_id}/draft`

Request:

```json
{
  "instructions": "Prepare a concise factual draft based only on verified evidence."
}
```

Response:

```json
{
  "draft_id": "draft_123",
  "status": "draft"
}
```

---

# 10. Drafts

## GET `/drafts/{draft_id}`

## POST `/drafts/{draft_id}/verify`

Runs citation/fact checks.

## POST `/drafts/{draft_id}/approve`

Requires appropriate role.

Request:

```json
{
  "comment": "Reviewed and approved."
}
```

Approval is never implicit.

---

# 11. Tasks

## GET `/tasks`

## POST `/tasks`

```json
{
  "title": "Request missing invoice",
  "client_id": "client_123",
  "due_at": "2026-09-28T10:00:00+05:30",
  "assigned_to": "user_123"
}
```

## PATCH `/tasks/{task_id}`

---

# 12. WhatsApp Webhook

## POST `/integrations/whatsapp/webhook`

Responsibilities:
- authenticate webhook;
- deduplicate message;
- map external user to firm/user;
- enqueue command;
- return quickly.

Never execute long-running AI work synchronously in the webhook.

---

# 13. API Security Requirements

- validate all input;
- enforce tenant authorization on every resource;
- use pagination;
- limit file sizes;
- rate-limit expensive endpoints;
- redact secrets from logs;
- prevent insecure direct object references;
- validate webhook signatures;
- use idempotency for retryable side effects.

---

# 14. Versioning

Breaking API changes require a new major API version.

Backward-compatible additions may remain in `/api/v1`.

---

# 15. OpenAPI

The actual application SHALL expose a generated OpenAPI document from the FastAPI application.

The generated contract becomes the source of truth for implementation-level endpoint schemas after the domain models are finalized.
