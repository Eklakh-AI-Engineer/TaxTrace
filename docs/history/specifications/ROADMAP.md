# Product & Engineering Roadmap

**Version:** 1.0

---

# 1. Roadmap Philosophy

Build evidence before automation.

The project should progress from:

```text
Problem validation
→ deterministic core
→ evidence workspace
→ AI assistance
→ WhatsApp
→ pilot
→ integrations
→ expansion
```

---

# 2. Phase 0 — Discovery

### Objectives

- interview CA professionals;
- validate workflow;
- collect sample schemas;
- identify first notice types;
- define approved knowledge sources;
- create labelled benchmark.

### Exit criteria

- 5–15 meaningful interviews;
- representative sample data;
- documented current-state workflow;
- MVP scope confirmed.

---

# 3. Phase 1 — Reconciliation Core

Build:

- client/period model;
- document upload;
- parsing;
- canonical transactions;
- exact matching;
- normalization;
- exception taxonomy;
- benchmark suite.

### Exit

A repeatable reconciliation result can be produced without an LLM.

---

# 4. Phase 2 — Evidence Workspace

Build:

- exception list;
- filters;
- side-by-side records;
- rule explanation;
- evidence references;
- decisions;
- export;
- audit log.

### Exit

A CA can investigate an exception end-to-end.

---

# 5. Phase 3 — AI Explanation

Build:

- structured explanation schema;
- LLM gateway;
- evidence-only prompt;
- confidence/uncertainty;
- prompt versioning;
- AI regression tests.

### Exit

AI explanations meet evaluation thresholds and never silently invent evidence.

---

# 6. Phase 4 — Notice Copilot

Build:

- notice extraction;
- source registry;
- RAG ingestion;
- retrieval;
- citations;
- draft generation;
- verification;
- approval.

### Exit

A CA can turn a supported notice into a reviewable source-grounded draft.

---

# 7. Phase 5 — WhatsApp

Build:

- official WhatsApp integration;
- identity mapping;
- document intake;
- status;
- summaries;
- exception lookup;
- task commands.

### Exit

Pilot users can perform common commands without opening the web UI.

---

# 8. Phase 6 — Controlled Pilot

Target:

- 2–5 small CA firms initially.

Measure:

- time saved;
- match quality;
- override rate;
- notice draft correction rate;
- repeat use;
- cost/client.

---

# 9. Phase 7 — Hardening

Build:

- security hardening;
- backups;
- monitoring;
- rate limiting;
- provider failure handling;
- deletion/retention workflows;
- admin tools.

---

# 10. Phase 8 — Integrations

Candidate integrations:

- Tally exports;
- accounting software;
- additional GST data imports;
- email;
- client portal;
- additional document formats.

Only add an integration when pilot evidence shows it reduces friction.

---

# 11. Phase 9 — Expansion

Potential future capabilities:

- more GST workflows;
- vendor follow-up automation;
- client document collection;
- compliance calendar;
- working-paper generation;
- practice analytics.

Do not expand until the core workflow has demonstrated repeated value.

---

# 12. Release Gates

Every major phase requires:

```text
Functional acceptance
+
Evaluation benchmark
+
Security review
+
Observability
+
Documentation
```
