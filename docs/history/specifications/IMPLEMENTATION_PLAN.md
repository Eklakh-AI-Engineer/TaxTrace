# TaxTrace Implementation Plan

## 1. Current repository status

This repository is currently a specification-first foundation, not an implemented product.

What already exists:
- Product and market framing: `PROJECT_BRIEF.md`, `PRD.md`, `README.md`
- Architecture and technical direction: `SYSTEM_ARCHITECTURE.md`, `TECH_STACK.md`, `REPO_STRUCTURE.md`
- Data and API contracts: `DATA_SPEC.md`, `API_SPEC.md`
- UX and workflow definition: `UI_SPEC.md`
- Evaluation and quality requirements: `EVALUATION_PLAN.md`, `TESTING_STRATEGY.md`
- Security and compliance baseline: `SECURITY.md`
- Decision record and engineering conventions: `DECISIONS.md`, `CODING_RULES.md`, `AGENTS.md`
- Delivery sequencing: `ROADMAP.md`, `CHANGELOG.md`, `MANIFEST.md`

What is not implemented yet:
- No backend application code
- No database schema or migrations
- No frontend application
- No worker services
- No object storage integration
- No AI gateway or provider integration
- No RAG/knowledge ingest pipeline
- No WhatsApp adapter
- No production auth or tenant controls in code
- No evaluation dataset or benchmark harness in code
- No deployment infrastructure

In other words, the repository is a well-defined architecture and product specification package, but it is still a pre-build baseline. The product must be implemented from this specification and should do so in a staged, dependency-aware order.

---

## 2. Actual product scope to build

TaxTrace should be built as an evidence-first compliance execution platform for small Indian CA firms with a modular monolith design and background workers.

The end-state product includes:
- firm and tenant-aware authentication and authorization
- client, period, and document management
- upload and normalization of purchase-register and GSTR-2B data
- deterministic reconciliation engine
- exception management with audit and evidence linking
- AI-based explanation and notice drafting only behind evidence boundaries
- notice intake, extraction, citation-backed drafting, and approval
- task/follow-up workflow
- WhatsApp intake/channel support
- review-centric web UI
- observability, security, and pilot operations

The design direction is intentionally conservative: AI assists, but CA approval remains required.

---

## 3. Implementation principles

The implementation should follow the project’s explicit principles:

1. Deterministic finance logic first; AI second.
2. Provenance for every important result.
3. Tenant isolation is mandatory.
4. No unsupported legal or tax conclusions.
5. Human approval before external action.
6. Fail safe when evidence is weak or missing.
7. Build the smallest useful workflow first, then expand.
8. Measure quality with benchmark and evaluation gates.

---

## 4. Recommended implementation order

The correct order is not “build everything in parallel.” The project should be built in dependency-driven stages, starting with the core reconciliation workflow and then layering in AI and communication features.

### Stage 0 — Project scaffolding and baseline engineering setup

Purpose:
- establish repo structure and codebase conventions
- define runtime, tooling, and environment model
- create the skeleton for backend, frontend, workers, migrations, and infra

Deliverables:
- Python project config (`pyproject.toml`, lint/test config)
- frontend app scaffold
- Docker Compose/dev environment
- `.env.example` and secret handling conventions
- CI workflow skeleton
- repo structure matching documented architecture
- baseline documentation for setup, developer workflow, and contribution rules

Dependencies:
- none; this is the enabling setup for all later work

Key gate:
- local developer environment can start backend and frontend services with seeded config

Why first:
- without this, every downstream implementation is disconnected and hard to validate

---

### Stage 1 — Core domain model and tenant-safe foundation

Purpose:
- create the business schema and shared domain layer for firms, users, clients, documents, periods, transactions, matches, exceptions, tasks, and audit events
- implement auth boundaries and tenant gating logic

Deliverables:
- PostgreSQL schema and Alembic migrations
- SQLAlchemy models and repositories
- auth/session model and permissions
- firm membership roles
- tenant-aware common service layer
- audit event model and append-only event logging
- document metadata and file hash tracking

Dependencies:
- Stage 0 scaffolding

Key design constraints:
- all business tables must be tenant-scoped
- all queries for business data must resolve tenant from authenticated identity
- files must be stored with random keys and immutable metadata
- money fields must be `DECIMAL`/numeric, never float

Key gate:
- a user can create a firm, create a client, upload a document, and see that tenant isolation is enforced in API and repository logic

Why early:
- the rest of the workflow depends on normalized objects, permissions, and auditability

---

### Stage 2 — Document ingestion and normalization pipeline

Purpose:
- accept uploaded files, validate them, store originals, and normalize transaction rows into canonical records

Deliverables:
- file validation and upload API
- content hash and metadata storage
- object storage integration
- CSV/XLSX parsing layer
- canonical transaction mapper
- document processing queue and worker
- parsing status and failure handling
- duplicate detection basics

Dependencies:
- Stage 1 domain model

Key subcomponents:
- document upload API
- document worker
- transaction normalization service
- source-row tracking and provenance map

Key gate:
- a purchase register or GSTR-2B file can be ingested, normalized, and persisted in canonical transaction form with traceable source rows

Why this is critical:
- all later reconciliation logic depends on the canonical transaction model

---

### Stage 3 — Deterministic reconciliation engine

Purpose:
- implement the product’s actual numeric core with deterministic matching and exception classification

Deliverables:
- exact match logic
- normalized match logic
- composite key generation
- controlled fuzzy matching
- duplicate detection
- mismatch classification
- rule versioning and deterministic output
- reconciliation job orchestration
- exception record creation with evidence references

Dependencies:
- Stage 1 and Stage 2

Core workflow:
- book document + GSTR-2B document
- normalize both
- apply matching rules in sequence
- classify exceptions
- persist evidence and match status

Key design constraints:
- no LLM should be used to decide the financial truth of a transaction
- rule version must be recorded for every reconciliation run
- confidence scores must never be treated as a substitute for evidence

Key gate:
- the reconciliation engine produces an explainable exception list without an AI component

This is the highest-priority product milestone and should be treated as the first true working product feature.

---

### Stage 4 — Evidence workspace and exception review UI

Purpose:
- allow CA staff to inspect mismatches, understand why they happened, and make decisions

Deliverables:
- exception dashboard
- filters by issuer, supplier, amount, severity, and status
- detail view with book and portal records side by side
- evidence panel with source rows and rule metadata
- decision actions: accepted, rejected, needs_info, resolved
- task generation from exceptions
- audit trail for review actions
- export of reviewed reconciliation result

Dependencies:
- Stage 3 reconciliation engine

Key gate:
- a CA user can review a real exception and answer: what changed, why, what evidence supports it, and what next action is appropriate

Why this stage matters:
- the product is valuable only when the output is reviewable and auditable, not just generated

---

### Stage 5 — AI explanation layer behind evidence boundaries

Purpose:
- add explanation support without creating unsafe or ungrounded financial conclusions

Deliverables:
- provider-agnostic LLM gateway
- structured explanation schema
- evidence-only prompts
- prompt versioning and model tracking
- confidence and uncertainty handling
- AI explanation API and UI
- fallback behavior when evidence is insufficient
- regression benchmark for supported vs. unsupported claims

Dependencies:
- Stage 3 and Stage 4

Key design constraints:
- the LLM can explain only what is supported by supplied evidence
- unsupported hypotheses must be marked as hypotheses, not facts
- all generated explanations must map to evidence IDs
- prompt and model metadata must be stored with output

Key gate:
- generated explanations are factual, source-grounded, and visibly distinguish facts from hypotheses

This should be implemented after the deterministic engine is working, not before.

---

### Stage 6 — Notice intake and grounded notice-response workflow

Purpose:
- support second core workflow: notice PDF ingestion, extraction, source retrieval, draft response, citation verification, and CA approval

Deliverables:
- notice upload and case creation
- extraction from PDF or structured notice documents
- notice issue parsing and structured facts
- approved source registry
- knowledge-base ingestion pipeline for official sources
- retrieval and citation service
- drafting service with source-grounded generation
- verification against retrieved sources
- approved draft state and approval history

Dependencies:
- Stage 1 domain model
- Stage 5 AI layer for drafting, if used
- approved-source knowledge ingest process

Key design constraints:
- notice drafting must never proceed without approved source retrieval
- no invented legal authority or fabricated fact should pass review
- citations must map to stored source documents/chunks
- all drafts remain editable and reviewable before external submission

Key gate:
- a CA can upload a supported notice, inspect extracted facts, retrieve relevant authorities, and generate a reviewable draft with visible citations

---

### Stage 7 — Tasks, follow-up, and operational workflow

Purpose:
- convert exceptions and notices into concrete operational work

Deliverables:
- task model and lifecycle states
- assignment and due-date tracking
- exception-to-task creation
- due date, backlog, overdue handling
- follow-up message drafting for clients/vendors
- operational dashboard metrics

Dependencies:
- Stage 4 exception workspace
- Stage 6 notice workflow

Key gate:
- staff can turn an exception or notice into a task and track completion through review and closure

Why this matters:
- without task lifecycle, the system becomes analysis-only instead of execution-oriented

---

### Stage 8 — WhatsApp integration and channel layer

Purpose:
- add a lightweight intake and status channel for common workflows

Deliverables:
- official WhatsApp Business integration
- event translation layer from WhatsApp messages to internal commands
- secure webhook validation
- document intake via approved message flows
- status and exception summaries via chat
- commands such as review tasks, explain mismatch, upload notice, show pending list
- confirmation flow before destructive or external actions

Dependencies:
- Stage 1 auth and tenant model
- Stage 4 exception review
- Stage 7 tasks

Key design constraints:
- WhatsApp is a channel, not the domain model
- all incoming channel content is treated as untrusted data
- the bot should never trigger external compliance submission without human approval

Key gate:
- common user actions work through chat without needing the full web review workspace

---

### Stage 9 — Pilot, evaluation, and quality hardening

Purpose:
- validate product value on actual CA-firm workflows before broader roll-out

Deliverables:
- evaluation benchmarks
- labeled reconciliation fixtures
- notice evaluation cases
- privacy-safe pilot dataset
- operational dashboards for time saved, exception volume, and cost
- pilot onboarding process
- override and correction logging
- benchmark gating before each release

Dependencies:
- Stage 3 through Stage 8

Success criteria:
- reconciliation precision and recall meet internal gates
- AI explanation unsupported-claim rate remains near zero
- citation pass rate is reliable and auditable
- pilot users can complete routine workflows faster than manual methods

---

### Stage 10 — Security hardening, production policies, and deployment

Purpose:
- move from working prototype to controlled production-ready deployment

Deliverables:
- production security review
- rate limiting and abuse controls
- secret management and rotation procedures
- data retention and deletion flows
- backup and restore validation
- RBAC and approval auditing
- observability and alerting
- deployment on staging/production environments
- provider data-retention and compliance checks

Dependencies:
- all earlier stages, particularly auth, tenant isolation, and AI/rag layers

Key gate:
- no production deployment should occur without explicit security review and policy validation

---

### Stage 11 — Expansion and integrations

Purpose:
- add optional integrations only after core value has proven itself

Candidate integrations:
- Tally / accounting exports
- other GST sources
- email ingestion
- client portal sync
- document OCR enhancements
- additional compliance workflows beyond GST

Dependencies:
- pilot evidence, not speculative assumptions

Key rule:
- add integrations only when they reduce real friction and are validated by user behavior

---

## 5. Critical dependency map

The most important order of dependency is:

1. Foundation + tenant model
2. Document ingestion + canonical transactions
3. Reconciliation engine
4. Exception review workspace
5. AI explanations
6. Notice processing + RAG
7. Tasks and operational workflow
8. WhatsApp channel
9. Pilot and evaluation
10. Security hardening and deployment
11. Expansion integrations

The critical path is:

Domain model → document normalization → deterministic matching → exception review → explanation → notice workflow → pilot → hardening.

If the team tries to add AI or WhatsApp before the deterministic core is stable, the project will drift into a fragile prototype that cannot be trusted.

---

## 6. Recommended implementation milestone sequence

The recommended milestone sequence for the first build is:

### Milestone A — Reconciliation foundation
- create firm/client/period model
- upload CSV/XLSX
- normalize transactions
- build deterministic matching
- produce reviewable exceptions with evidence

This is the first shipping milestone.

### Milestone B — Review workspace
- exception dashboard
- drill-down detail
- rule explanation
- decision workflow
- task generation

### Milestone C — AI explanation
- structured explanation endpoint
- evidence-only prompts
- prompt versioning
- benchmark gating

### Milestone D — Notice copilot
- notice intake
- extraction
- retrieval
- citation verification
- draft response

### Milestone E — Pilot-ready platform
- WhatsApp tier
- audit and approvals
- security review
- operational metrics

---

## 7. Practical team recommendations

### Team split
- backend/data engineers: domain model, transaction normalization, reconciliation engine, API
- security/architecture lead: tenant isolation, auth, audit, retention, release gate
- AI engineer: gateway, prompt logic, retrieval, evaluation
- frontend engineer: exception review workspace and operational UI
- QA/automation engineer: golden tests, API and UI regression coverage
- product/CA SME: benchmark design, workflow validation, pilot feedback

### Execution recommendation
- do not build the full SaaS in one pass
- implement one workflow end-to-end before moving to the next major feature
- treat each stage as a release candidate with explicit quality and security gates

---

## 8. Most important risk to avoid

The biggest risk is building a product that looks impressive in demos but is not trustworthy in actual compliance work.

That risk appears if the team:
- lets LLMs decide financial reconciliation without deterministic logic
- fails to attach evidence and source provenance
- bypasses tenant isolation
- drafts legal content without approved-source verification
- treats WhatsApp as the product rather than a channel
- expands to broad functionality before the core workflow is stable

The correct response is to keep the product anchored to evidence, deterministic rules, and CA review.

---

## 9. Final recommendation

The best implementation path for TaxTrace is:

1. build the deterministic reconciliation core first;
2. prove it on evidence-backed review workflows;
3. add AI explanations only after the baseline is stable;
4. then add notice drafting, tasking, and WhatsApp support;
5. harden security and validate through pilot usage before broad scaling.

This sequence aligns with the project’s core product principle:

AI prepares. Evidence explains. CA approves.
