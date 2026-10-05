# Architecture & Product Decisions

**Version:** 1.0

This file records decisions that should not be silently reversed.

---

# ADR-001 — Evidence-first product positioning

**Status:** Accepted

### Context
Basic GST reconciliation and AI/WhatsApp features are already present in current products.

### Decision
Position the product around evidence-first compliance execution.

### Consequences
The data model must include provenance and evidence. AI outputs must be reviewable.

---

# ADR-002 — Deterministic reconciliation core

**Status:** Accepted

### Context
Financial matching requires reproducibility and predictable behavior.

### Decision
Use deterministic rules/algorithms for the core reconciliation result. Use AI for explanation and unstructured interpretation.

### Consequences
Rule versions must be stored. Matching must be benchmarked independently of the LLM.

---

# ADR-003 — Human approval for consequential actions

**Status:** Accepted

### Decision
AI-generated legal/compliance drafts cannot directly become external submissions.

### Consequences
Approval is a state transition and audit event.

---

# ADR-004 — Modular monolith first

**Status:** Accepted

### Context
The initial team and workload do not justify distributed microservices.

### Decision
Build a modular monolith with background workers.

### Consequences
Clear module boundaries are mandatory. Services may be extracted later.

---

# ADR-005 — PostgreSQL as primary database

**Status:** Accepted

### Decision
Use PostgreSQL for application state and initial vector retrieval through pgvector where suitable.

### Consequences
One operational database can support MVP data and retrieval.

---

# ADR-006 — Provider-agnostic LLM gateway

**Status:** Accepted

### Decision
Do not bind domain services directly to a single LLM vendor.

### Consequences
Model/provider selection becomes configuration/routing.

---

# ADR-007 — WhatsApp is a channel, not the domain model

**Status:** Accepted

### Decision
WhatsApp payloads are translated into internal commands/events.

### Consequences
The product remains usable through web UI and future channels.

---

# ADR-008 — No autonomous filing in MVP

**Status:** Accepted

### Decision
The MVP cannot autonomously file returns or submit compliance responses.

### Consequences
The system focuses on preparation, evidence and approval.

---

# ADR-009 — Source-controlled legal knowledge

**Status:** Accepted

### Decision
Legal/compliance retrieval uses an approved source registry rather than arbitrary web search at generation time.

### Consequences
Knowledge ingestion, versioning and source verification are first-class workflows.

---

# ADR-010 — Prompt versions are data

**Status:** Accepted

### Decision
Every production AI generation records a prompt/template version and model identifier.

### Consequences
AI outputs become reproducible/auditable to the extent possible.

---

# ADR-011 — Pricing remains a hypothesis

**Status:** Accepted

### Context
The original proposal suggested ₹999–₹1,999/month.

### Decision
Do not encode this as a final commercial price until validated.

### Consequences
Pricing experiments belong in customer discovery.

---

# ADR-012 — Web review workspace is required after core validation

**Status:** Accepted

### Context
WhatsApp is convenient for intake/commands but poor for reviewing large exception sets.

### Decision
Use WhatsApp for low-friction actions and a web UI for investigation/approval.

---

# ADR-013 — Source records remain immutable

**Status:** Accepted

### Decision
Uploaded originals cannot be edited in place.

### Consequences
Corrections create new versions/derived records and preserve provenance.
