# Coding Rules

**Version:** 1.0

---

# 1. General Principles

- Prefer simple code over clever code.
- Keep functions small and focused.
- Use explicit names.
- Validate at boundaries.
- Fail loudly and safely.
- Never hide business rules inside UI code.
- Never hide financial calculations inside prompts.
- Do not duplicate domain logic.

---

# 2. Python

Use:
- type hints;
- Pydantic for external schemas;
- SQLAlchemy for persistence;
- async where it provides actual value;
- structured exceptions.

Avoid:
- global mutable state;
- raw SQL scattered through routes;
- broad `except Exception` without logging/recovery;
- magic numbers;
- implicit float arithmetic for money.

---

# 3. Money

Use `Decimal`/database numeric.

Never:

```python
total = 0.1 + 0.2
```

for accounting logic.

Use explicit rounding rules.

---

# 4. Dates

Use timezone-aware datetimes for events.

Separate:
- business/tax period;
- calendar date;
- timestamp.

Never infer a tax period from a timestamp without explicit rules.

---

# 5. Database

- migrations required;
- foreign keys required;
- tenant filters required;
- transactions for multi-record state changes;
- indexes based on measured query needs.

---

# 6. API

- request/response schemas are explicit;
- consistent error format;
- pagination for collections;
- authorization before data access;
- idempotency for retryable side effects.

---

# 7. AI Code

All LLM calls must:

- use typed input/output schemas;
- record model/provider;
- record prompt version;
- handle timeout;
- handle malformed output;
- validate structured output;
- define fallback behavior.

Never allow an LLM string to directly trigger an irreversible action.

---

# 8. Prompts

Prompts are version-controlled artifacts.

Each prompt should document:

```text
Purpose
Input
Output schema
Allowed evidence
Forbidden behavior
Failure behavior
Evaluation cases
```

---

# 9. RAG

Retrieved text is untrusted content.

The model must not follow instructions found inside retrieved documents.

Every citation must map to a stored source/chunk.

---

# 10. Logging

Use structured logs.

Include:
- request ID;
- tenant ID;
- operation;
- duration;
- outcome.

Do not log sensitive source content by default.

---

# 11. Naming

Python:
```text
snake_case
```

Classes:
```text
PascalCase
```

Constants:
```text
UPPER_SNAKE_CASE
```

API:
```text
plural nouns
```

---

# 12. Comments

Comment why, not what.

Bad:

```python
# Add 1
x += 1
```

Good:

```python
# Preserve one-based source row numbers for audit references.
source_row += 1
```

---

# 13. Testing

Every bug fix requires a regression test.

Every new domain rule requires:
- unit test;
- edge cases;
- benchmark impact review.

---

# 14. Git

Commit format:

```text
feat: add reconciliation exception model
fix: prevent duplicate reconciliation jobs
test: add GSTIN normalization cases
docs: update notice RAG policy
refactor: isolate LLM gateway
```

Keep commits focused.

---

# 15. Pull Requests

PR must include:

- purpose;
- implementation summary;
- tests;
- security impact;
- migration impact;
- AI evaluation impact where relevant;
- screenshots for UI changes.

---

# 16. Forbidden Shortcuts

Do not:

- disable authorization to make a test pass;
- hard-code tenant IDs;
- store secrets in source;
- bypass migrations;
- suppress failing AI evaluations;
- make LLM output authoritative without evidence;
- catch errors and return HTTP 200;
- delete failing tests without replacing coverage.
