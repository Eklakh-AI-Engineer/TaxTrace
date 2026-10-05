# Testing Strategy

**Version:** 1.0

---

# 1. Testing Philosophy

Test the system at multiple levels.

```text
Unit
 ↓
Domain
 ↓
Integration
 ↓
Contract
 ↓
AI evaluation
 ↓
End-to-end
 ↓
Security
```

No AI feature should be accepted solely because a manual demo looked good.

---

# 2. Unit Tests

Cover:

- GSTIN normalization;
- invoice-number normalization;
- date parsing;
- amount arithmetic;
- tax calculations;
- matching rules;
- exception classification;
- severity calculation;
- permission checks;
- source citation parsing.

Financial arithmetic tests should include decimal precision and boundary cases.

---

# 3. Reconciliation Golden Tests

Maintain fixed fixtures:

```text
exact_match.xlsx
partial_match.xlsx
missing_2b.xlsx
missing_books.xlsx
duplicate_candidates.xlsx
gstin_mismatch.xlsx
date_mismatch.xlsx
value_mismatch.xlsx
```

Each fixture has an expected result file.

The reconciliation engine must be deterministic for the same:
- inputs;
- rule version;
- configuration.

---

# 4. Integration Tests

Test:

- database;
- object storage;
- queue;
- document processor;
- LLM gateway mock;
- RAG retrieval;
- audit logging.

External providers should be mocked in normal CI.

---

# 5. Contract Tests

Validate:

- API request schema;
- response schema;
- error schema;
- webhook payload handling.

Frontend should not silently depend on undocumented backend fields.

---

# 6. AI Tests

Use a fixed evaluation set.

Test:

- structured output schema;
- refusal/uncertainty behavior;
- evidence-only explanation;
- citation support;
- prompt injection resistance;
- missing context;
- conflicting evidence.

---

# 7. Prompt Regression Tests

Each prompt has:

```text
prompt_id
version
purpose
input_schema
output_schema
test_cases
```

Changing a prompt requires evaluation.

---

# 8. RAG Tests

Test:

- correct source retrieval;
- irrelevant-source rejection;
- source version;
- citation mapping;
- no-source behavior.

Expected no-source behavior:

> "I could not verify this from the approved knowledge sources."

Not a guessed answer.

---

# 9. End-to-End Tests

Scenario:

```text
Create firm
 ↓
Create client
 ↓
Upload files
 ↓
Run reconciliation
 ↓
Review exception
 ↓
Generate explanation
 ↓
Create task
 ↓
Upload notice
 ↓
Generate draft
 ↓
Verify citation
 ↓
Approve
 ↓
Audit trail
```

---

# 10. Security Tests

At minimum:

- broken access control;
- IDOR;
- tenant escape;
- malicious upload;
- path traversal;
- SQL injection;
- XSS;
- CSRF where relevant;
- webhook spoofing;
- token leakage;
- prompt injection;
- sensitive logging.

---

# 11. Performance Tests

Measure:

- upload latency;
- reconciliation throughput;
- concurrent reconciliation jobs;
- queue delay;
- API p95 latency;
- LLM response latency.

Do not optimize prematurely; establish baseline first.

---

# 12. CI Gates

Pull requests should fail if:

- formatting fails;
- lint fails;
- type checks fail beyond configured baseline;
- unit tests fail;
- integration tests fail;
- security scan finds blocking issue;
- schema migration is invalid.

---

# 13. Release Checklist

- all tests pass;
- evaluation benchmark recorded;
- migrations reviewed;
- security review completed for relevant changes;
- changelog updated;
- rollback path known;
- monitoring verified;
- feature flags configured if needed.
