# Product Requirements Document (PRD)

**Product:** AI Compliance Execution Platform for Small Indian CA Firms  
**Version:** 1.0  
**Status:** Approved baseline for pre-build  
**Date:** 24 September 2026

---

# 1. Product Overview

The product helps small CA firms process recurring GST compliance work by combining:

- structured data reconciliation;
- document intelligence;
- evidence retrieval;
- AI-assisted explanation;
- AI-assisted drafting;
- task/follow-up management;
- human approval.

The product is an **assistive system**, not an autonomous tax-filing system.

---

# 2. Product Goals

## G1 — Reduce reconciliation effort

Reduce the time required to identify and investigate GST purchase-register/GSTR-2B exceptions.

## G2 — Make exceptions explainable

A user should be able to answer:

- What is wrong?
- Which records are involved?
- Which rule detected it?
- What evidence supports it?
- What might explain it?
- What action is suggested?
- How confident is the system?

## G3 — Accelerate notice preparation

Turn a notice PDF into:

- structured facts;
- identified issues;
- source-grounded legal references;
- an editable response draft.

## G4 — Preserve human control

No consequential external action without explicit human approval.

## G5 — Create a reusable compliance data layer

Normalize documents and transactions into reusable entities that can later support additional compliance workflows.

---

# 3. Non-Goals

The product will not initially:

- replace a CA;
- make final legal/tax determinations;
- autonomously file returns;
- autonomously submit replies;
- replace Tally, Zoho Books, ClearTax or another accounting/GST platform;
- provide unrestricted legal advice;
- scrape arbitrary websites as legal authority;
- use an LLM as the sole numerical reconciliation mechanism.

---

# 4. Personas

## 4.1 CA Partner

Needs:
- concise exception summaries;
- financial impact;
- deadlines;
- evidence;
- approval controls.

Pain:
- too much operational supervision;
- fragmented client status;
- concern about errors.

Success:
- can review high-value/high-risk items quickly.

## 4.2 Senior Accountant

Needs:
- accurate reconciliation;
- investigation workspace;
- bulk filtering;
- exports;
- client/vendor follow-up.

Success:
- substantially fewer manual comparisons.

## 4.3 Junior/Article

Needs:
- clear next actions;
- document requests;
- guided exception handling.

Success:
- can complete routine first-pass work without guessing.

## 4.4 End Client

Needs:
- simple document submission;
- clear requests;
- status visibility where exposed.

Success:
- fewer repeated document requests.

---

# 5. User Stories

## Reconciliation

- As a CA staff member, I can upload a Purchase Register so the system can normalize it.
- As a CA staff member, I can upload/import GSTR-2B for the same client and period.
- As a CA, I can start reconciliation for a selected client and period.
- As a CA, I can see matched, partial and exception records.
- As a CA, I can filter by mismatch type, value, supplier and severity.
- As a CA, I can inspect the source evidence for an exception.
- As a CA, I can accept, reject or annotate a suggested explanation.
- As a CA, I can export the reviewed reconciliation.

## Notice

- As a CA, I can upload a notice PDF.
- As a CA, I can see extracted notice facts.
- As a CA, I can inspect retrieved source material.
- As a CA, I can generate a draft response.
- As a CA, I can edit the draft.
- As a CA, I can see citations/provenance.
- As a CA, I can approve a draft for external use.

## Follow-up

- As staff, I can create a task from an exception.
- As staff, I can assign an owner and due date.
- As staff, I can create a client/vendor message draft.
- As a partner, I can see overdue items.

---

# 6. Functional Requirements

## FR-001 Tenant Management

The system SHALL support isolated firms/tenants.

Acceptance:
- user belongs to one or more authorized firms;
- every business object has tenant context;
- unauthorized cross-tenant access is denied.

## FR-002 Client Management

The system SHALL allow a firm to create/manage clients with:
- client ID;
- display name;
- GSTIN;
- optional PAN/reference fields where legally and operationally required;
- contacts;
- active/inactive state.

## FR-003 Document Intake

Supported initial formats:
- CSV;
- XLSX;
- PDF;
- JSON where useful.

The system SHALL:
- validate file type;
- limit file size;
- calculate a content hash;
- store source metadata;
- associate the document with firm/client/period.

## FR-004 Transaction Normalization

The system SHALL map imported records into a canonical schema.

Minimum fields:
- supplier GSTIN;
- invoice number;
- invoice date;
- taxable value;
- CGST;
- SGST;
- IGST;
- cess;
- source document;
- source row/reference.

## FR-005 Reconciliation

The system SHALL execute:
1. exact matching;
2. normalized matching;
3. controlled fuzzy candidate generation;
4. deterministic exception classification.

## FR-006 Exception States

Initial states:
- MATCHED;
- PARTIAL_MATCH;
- MISSING_IN_2B;
- MISSING_IN_BOOKS;
- DUPLICATE;
- GSTIN_MISMATCH;
- DATE_MISMATCH;
- VALUE_MISMATCH;
- REVIEW_REQUIRED.

## FR-007 Evidence

Each exception SHALL reference:
- book-side source;
- GSTR-2B-side source;
- matching rule;
- relevant fields;
- calculation/comparison result.

## FR-008 AI Explanation

The system MAY generate an explanation using an LLM.

The explanation SHALL:
- use only supplied evidence;
- distinguish facts from hypotheses;
- state uncertainty;
- avoid claiming a final tax/legal conclusion.

## FR-009 Notice Extraction

The system SHALL attempt to extract:
- notice type;
- reference number;
- GSTIN;
- taxpayer name;
- tax period;
- issue date;
- response deadline if explicitly present;
- amounts;
- cited sections/rules;
- allegations/issues;
- requested documents/actions.

## FR-010 Legal Retrieval

The system SHALL retrieve from approved knowledge sources.

Each retrieved item SHALL store:
- source ID;
- title;
- source URL/location;
- effective/version metadata where available;
- retrieval timestamp;
- content hash/version.

## FR-011 Draft Generation

The system SHALL generate editable drafts.

Drafts SHALL:
- separate facts from legal analysis;
- cite retrieved sources;
- identify missing information;
- never invent supporting documents;
- never claim approval.

## FR-012 Human Approval

Any external compliance/legal response SHALL require explicit approval.

## FR-013 Audit Logging

The system SHALL record:
- login;
- document upload;
- reconciliation run;
- exception decision;
- AI generation;
- source retrieval;
- draft version;
- approval/rejection;
- export;
- administrative changes.

## FR-014 WhatsApp

The first WhatsApp scope SHALL include:
- document intake;
- processing status;
- summary;
- exception lookup;
- notice upload;
- task/status commands.

## FR-015 Export

Initial exports:
- CSV/XLSX reconciliation report;
- PDF summary where required;
- draft response document.

---

# 7. Non-Functional Requirements

## NFR-001 Accuracy

The reconciliation engine must be evaluated against a labelled benchmark before pilot use.

## NFR-002 Reliability

Long-running document/reconciliation jobs must be retryable and idempotent.

## NFR-003 Security

Tenant isolation and access control are mandatory.

## NFR-004 Observability

Every production workflow must produce structured logs and measurable latency/cost metrics.

## NFR-005 Explainability

Exceptions must expose deterministic reasons and evidence references.

## NFR-006 Cost

The system should avoid unnecessary LLM calls.

## NFR-007 Maintainability

Business rules, schemas and prompts must be versioned.

## NFR-008 Auditability

Important user and system actions must be reconstructable.

---

# 8. Severity Model

| Severity | Meaning |
|---|---|
| CRITICAL | Potentially material issue or unsafe output requiring immediate human review |
| HIGH | Significant financial/compliance impact |
| MEDIUM | Requires investigation but is not immediately material |
| LOW | Data quality or informational issue |

Severity is a workflow priority, not a legal conclusion.

---

# 9. Product Workflow

```text
Upload
  ↓
Validate
  ↓
Normalize
  ↓
Reconcile
  ↓
Classify
  ↓
Evidence
  ↓
AI explanation (optional)
  ↓
CA review
  ↓
Decision
  ↓
Task/follow-up
  ↓
Export/audit
```

Notice workflow:

```text
Notice PDF
  ↓
Extraction
  ↓
Validation
  ↓
Source retrieval
  ↓
Grounded analysis
  ↓
Draft
  ↓
Citation verification
  ↓
CA edit
  ↓
CA approval
```

---

# 10. Acceptance Criteria for MVP

The MVP is ready for controlled pilot when:

- files can be uploaded and associated with a client/period;
- canonical transactions are created;
- matching results are reproducible;
- exception types are deterministic;
- evidence can be opened from every exception;
- AI explanations cannot access unrelated tenant data;
- notice drafts include source references;
- approval events are recorded;
- unsafe/unverified legal claims are detectable by tests;
- baseline metrics are available.

---

# 11. Open Product Questions

1. Which exact Purchase Register export formats are most common among pilot firms?
2. What GSTR-2B data representation will be provided in practice?
3. What invoice-number normalization rules are acceptable to CAs?
4. Which notice types should be supported first?
5. Which legal sources may be used as approved authorities?
6. What retention period do pilot firms require?
7. What is the preferred WhatsApp command language?
8. What pricing is acceptable after measurable time savings are demonstrated?

These must be answered through discovery rather than guessed.


---

# Research Basis & Source Notes

The project definition was informed by the uploaded proposal and current public documentation reviewed during research.

Key source categories:
- GST Portal/GSTN guidance on GSTR-2B and reconciliation;
- official/authoritative tax and compliance material;
- public product documentation from GST/accounting/CA automation vendors.

Representative sources:
- GST Portal GSTR-2B FAQ: https://tutorial.gst.gov.in/userguide/returns/FAQ_gstr2b.htm
- Zoho Books GSTR-2B reconciliation: https://www.zoho.com/in/books/help/gst/gstr2b-reconcile.html
- ClearTax GST: https://cleartax.in/gst
- AIMunim: https://www.aimunim.in/
- Turia: https://turia.in/
- Xpert CA: https://xpertca.in/
- TaxEye: https://taxeye.in/
- TaxZeo: https://zeohq.com/products/taxzeo

Vendor pages document advertised capabilities and should not be treated as independent evidence of product quality, accuracy or market share.
