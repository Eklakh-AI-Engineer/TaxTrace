# Data Specification

**Version:** 1.0  
**Database:** PostgreSQL  
**Status:** Baseline

---

# 1. Data Principles

1. Every business record is tenant-scoped.
2. Source documents are immutable after upload.
3. Derived data can be regenerated.
4. Provenance is mandatory for compliance results.
5. Schema changes require migrations.
6. Sensitive fields are minimized.
7. Deletion/retention behavior is explicit.

---

# 2. Core Entities

## Firm

```text
firm_id UUID PK
name VARCHAR
status ENUM(active, suspended, archived)
plan VARCHAR
created_at TIMESTAMP
updated_at TIMESTAMP
```

## User

```text
user_id UUID PK
email VARCHAR UNIQUE
name VARCHAR
status ENUM(active, invited, disabled)
created_at TIMESTAMP
updated_at TIMESTAMP
```

## FirmMembership

```text
firm_id UUID FK
user_id UUID FK
role ENUM(owner, partner, senior, staff, viewer)
created_at TIMESTAMP
PRIMARY KEY (firm_id, user_id)
```

## Client

```text
client_id UUID PK
firm_id UUID FK
display_name VARCHAR
gstin VARCHAR
pan_reference VARCHAR NULL
status ENUM(active, inactive)
created_at TIMESTAMP
updated_at TIMESTAMP
```

Do not collect a sensitive field merely because it exists. Every field must have a product purpose.

---

# 3. Compliance Period

```text
period_id UUID PK
client_id UUID FK
financial_year VARCHAR
tax_period VARCHAR
period_type VARCHAR
status VARCHAR
created_at TIMESTAMP
```

Unique constraint should prevent accidental duplicate active periods for the same client/type.

---

# 4. Document

```text
document_id UUID PK
firm_id UUID FK
client_id UUID FK
period_id UUID NULL
document_type VARCHAR
original_filename VARCHAR
storage_uri VARCHAR
content_hash VARCHAR
mime_type VARCHAR
size_bytes BIGINT
processing_status ENUM(
  uploaded,
  queued,
  processing,
  processed,
  failed
)
uploaded_by UUID FK
created_at TIMESTAMP
processed_at TIMESTAMP NULL
```

The content hash helps detect duplicate uploads.

---

# 5. Transaction

Canonical transaction:

```text
transaction_id UUID PK
firm_id UUID FK
client_id UUID FK
period_id UUID FK
source_document_id UUID FK
source_row_reference VARCHAR
supplier_gstin VARCHAR
invoice_number_raw VARCHAR
invoice_number_normalized VARCHAR
invoice_date DATE
taxable_value NUMERIC
cgst NUMERIC
sgst NUMERIC
igst NUMERIC
cess NUMERIC
currency VARCHAR DEFAULT 'INR'
created_at TIMESTAMP
```

All monetary fields must use decimal/numeric types. Never use floating point for accounting amounts.

---

# 6. Match

```text
match_id UUID PK
firm_id UUID FK
period_id UUID FK
book_transaction_id UUID FK
portal_transaction_id UUID FK
status ENUM(
  matched,
  partial_match,
  candidate,
  rejected
)
match_score NUMERIC NULL
rule_version VARCHAR
created_at TIMESTAMP
```

A score is not a truth value. The status and rule evidence must explain the result.

---

# 7. Exception

```text
exception_id UUID PK
firm_id UUID FK
period_id UUID FK
match_id UUID NULL
type VARCHAR
severity ENUM(critical, high, medium, low)
status ENUM(
  open,
  in_review,
  accepted,
  rejected,
  resolved
)
reason_code VARCHAR
explanation TEXT NULL
created_by_system BOOLEAN
assigned_to UUID NULL
created_at TIMESTAMP
updated_at TIMESTAMP
```

---

# 8. Evidence

```text
evidence_id UUID PK
firm_id UUID FK
exception_id UUID NULL
notice_case_id UUID NULL
evidence_type VARCHAR
source_document_id UUID NULL
source_row_reference VARCHAR NULL
source_field VARCHAR NULL
source_text TEXT NULL
source_url TEXT NULL
source_version VARCHAR NULL
metadata JSONB
created_at TIMESTAMP
```

---

# 9. Notice Case

```text
notice_case_id UUID PK
firm_id UUID FK
client_id UUID FK
period_id UUID NULL
source_document_id UUID FK
notice_type VARCHAR
reference_number VARCHAR NULL
issue_date DATE NULL
response_deadline DATE NULL
status ENUM(
  received,
  extracting,
  review_required,
  drafting,
  draft_ready,
  approved,
  closed
)
created_at TIMESTAMP
updated_at TIMESTAMP
```

---

# 10. Knowledge Source

```text
source_id UUID PK
source_type VARCHAR
title VARCHAR
url TEXT
publisher VARCHAR
version VARCHAR NULL
effective_from DATE NULL
effective_to DATE NULL
content_hash VARCHAR
status ENUM(active, superseded, disabled)
retrieved_at TIMESTAMP
created_at TIMESTAMP
```

---

# 11. Knowledge Chunk

```text
chunk_id UUID PK
source_id UUID FK
chunk_index INT
content TEXT
embedding VECTOR
metadata JSONB
content_hash VARCHAR
created_at TIMESTAMP
```

---

# 12. Draft

```text
draft_id UUID PK
firm_id UUID FK
notice_case_id UUID FK
version INT
content TEXT
status ENUM(draft, review, approved, rejected)
prompt_version VARCHAR
model_name VARCHAR
created_at TIMESTAMP
created_by UUID NULL
```

---

# 13. Citation

```text
citation_id UUID PK
draft_id UUID FK
source_id UUID FK
chunk_id UUID NULL
claim_text TEXT
citation_text TEXT
verification_status ENUM(
  pending,
  verified,
  failed,
  manual_review
)
created_at TIMESTAMP
```

---

# 14. Task

```text
task_id UUID PK
firm_id UUID FK
client_id UUID NULL
exception_id UUID NULL
notice_case_id UUID NULL
title VARCHAR
description TEXT
assigned_to UUID NULL
due_at TIMESTAMP NULL
status ENUM(
  open,
  in_progress,
  blocked,
  completed,
  cancelled
)
created_at TIMESTAMP
updated_at TIMESTAMP
```

---

# 15. Audit Event

```text
audit_event_id UUID PK
firm_id UUID FK
actor_type ENUM(user, system, integration)
actor_id UUID NULL
action VARCHAR
entity_type VARCHAR
entity_id UUID
request_id VARCHAR
metadata JSONB
created_at TIMESTAMP
```

Audit events should be append-only from the application perspective.

---

# 16. Indexing

Initial indexes:

- `firm_id` on all tenant-owned tables;
- `(client_id, period_id)` for transaction/exceptions;
- `supplier_gstin`;
- `invoice_number_normalized`;
- `invoice_date`;
- `notice_case.status`;
- `task.due_at`;
- `audit_event.created_at`.

Avoid excessive indexes until actual query patterns are measured.

---

# 17. Data Lifecycle

```text
Upload
 ↓
Process
 ↓
Derived records
 ↓
Review
 ↓
Export
 ↓
Retention period
 ↓
Deletion/anonymization
```

Retention periods must be configurable and validated against the firm's contractual and legal requirements.

---

# 18. Data Quality Rules

- GSTIN must be normalized before matching.
- Invoice numbers must preserve both raw and normalized values.
- Dates must have explicit timezone/period semantics where applicable.
- Monetary values must be decimal.
- Missing values must be represented explicitly, not as zero unless zero is semantically correct.
- Source row references must be preserved.
