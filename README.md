# AI Compliance Execution Platform for Small Indian CA Firms

> **Evidence-first AI compliance execution — AI prepares, evidence explains, CA approves.**

---

## 1. What is this?

This repository is the foundation for an AI-powered compliance execution platform designed for small Indian CA firms.

The first target workflow is GST reconciliation, particularly:

```text
Purchase Register
       +
GSTR-2B
       ↓
Normalization
       ↓
Deterministic Matching
       ↓
Exception Classification
       ↓
Evidence
       ↓
AI Explanation
       ↓
CA Review
```

A second workflow covers GST/compliance notices:

```text
Notice PDF
   ↓
Extraction
   ↓
Approved-source retrieval
   ↓
Grounded analysis
   ↓
Draft response
   ↓
Citation verification
   ↓
CA approval
```

---

# 2. Core Product Principle

## AI prepares.
## Evidence explains.
## CA approves.

The product is an assistant, not an autonomous tax or legal decision-maker.

---

# 3. Why this project?

The original project proposal identified a recurring operational problem in small CA firms: manual GST reconciliation, notice drafting and deadline tracking.

Current market research confirms that these workflows are real, but it also shows that GST reconciliation, AI notice drafting and WhatsApp-based CA automation are increasingly competitive.

Therefore, the project is intentionally positioned around:

- evidence;
- provenance;
- deterministic reconciliation;
- explainability;
- human approval;
- workflow execution;
- measurable time savings.

---

# 4. Main Modules

### RECONCILE

- Purchase Register ingestion;
- GSTR-2B ingestion;
- normalization;
- deterministic matching;
- exception classification;
- evidence;
- review;
- export.

### RESPOND

- notice ingestion;
- structured extraction;
- approved knowledge retrieval;
- citation mapping;
- AI drafting;
- verification;
- approval.

### FOLLOW UP

- tasks;
- owners;
- due dates;
- client/vendor communication drafts;
- status.

---

# 5. Current Status

This repository begins at the **pre-build specification stage**.

### Completed

- product brief;
- PRD;
- architecture;
- technology specification;
- repository design;
- data specification;
- API specification;
- UI specification;
- evaluation plan;
- testing strategy;
- security baseline;
- architecture decisions;
- roadmap;
- coding rules;
- agent instructions;
- changelog;
- README.

### Not yet completed

- implementation;
- production database;
- real WhatsApp integration;
- real CA pilot;
- production RAG corpus;
- production AI provider integration;
- deployment;
- security certification/review;
- commercial validation.

---

# 6. Documentation Map

| File | Purpose |
|---|---|
| `PROJECT_BRIEF.md` | High-level project definition |
| `PRD.md` | Product requirements |
| `SYSTEM_ARCHITECTURE.md` | Technical architecture |
| `TECH_STACK.md` | Technology choices |
| `REPO_STRUCTURE.md` | Codebase organization |
| `DATA_SPEC.md` | Database/domain data specification |
| `API_SPEC.md` | API contract |
| `UI_SPEC.md` | UX/UI behavior |
| `EVALUATION_PLAN.md` | AI/data evaluation |
| `TESTING_STRATEGY.md` | Software testing |
| `SECURITY.md` | Security/privacy controls |
| `DECISIONS.md` | Architecture decisions |
| `ROADMAP.md` | Development roadmap |
| `CODING_RULES.md` | Engineering standards |
| `AGENTS.md` | AI coding-agent instructions |
| `CHANGELOG.md` | Project history |

---

# 7. Recommended Development Order

Do not start by implementing everything.

Use:

```text
01. Discovery
02. Data model
03. Reconciliation engine
04. Evaluation benchmark
05. Evidence workspace
06. AI explanation
07. Notice RAG
08. Draft verification
09. WhatsApp
10. Pilot
11. Security hardening
12. Integrations
```

---

# 8. First Coding Milestone

The first real feature should be:

> **Upload Purchase Register + GSTR-2B → normalize → reconcile → produce deterministic exceptions → show evidence.**

The system should work without an LLM.

This gives the project a reliable core.

---

# 9. Local Development — Planned

The eventual local environment should support:

```text
Docker
PostgreSQL
Redis
Backend
Frontend
Worker
```

Create `.env` from `.env.example`.

Never commit secrets.

---

# 10. Engineering Standards

All contributions must follow:

- typed Python;
- explicit schemas;
- deterministic money calculations;
- migrations;
- tenant isolation;
- structured logging;
- tests;
- AI evaluation;
- prompt versioning;
- security review.

See `CODING_RULES.md`.

---

# 11. AI Development Rule

The project must not become:

> "Upload document → ask GPT → trust response."

Instead:

```text
Input
 ↓
Validate
 ↓
Extract
 ↓
Deterministic processing
 ↓
Retrieve evidence
 ↓
AI assistance
 ↓
Verify
 ↓
Human review
```

---

# 12. Data & Privacy

The project may eventually handle sensitive financial/tax data.

Therefore:

- use synthetic/anonymized data during development;
- do not upload real client documents to development tools without authorization;
- do not commit client data;
- do not log sensitive document contents;
- isolate tenants;
- review AI provider data handling before production.

---

# 13. Research Basis

The project originated from the uploaded proposal:

> **AI Micro-SaaS for CA/Tax Firms**

The proposal described:
- small CA firms;
- manual GST compliance;
- GSTR-2B reconciliation;
- notice drafting;
- WhatsApp-first interaction;
- FastAPI + Claude API + Supabase;
- subscription pricing hypothesis.

The research phase refined this into the current evidence-first architecture.

---

# 14. Important Product Disclaimer

This software is an assistive technology project.

It is not a substitute for a qualified CA/tax professional or legal counsel.

AI-generated content must be reviewed before professional or external use.

---

# 15. Contribution Workflow

```text
Issue
 ↓
Read requirements
 ↓
Design
 ↓
Implement
 ↓
Test
 ↓
Evaluate
 ↓
Security review
 ↓
Document
 ↓
Pull Request
```

---

# 16. Suggested First Git Commit

```text
chore: initialize AI CA compliance platform foundation
```

---

# 17. North Star

The long-term objective is not to build another chatbot.

It is to build a system that can take messy compliance inputs and turn them into:

```text
Structured work
+
Evidence
+
Explanation
+
Suggested next action
+
Human approval
+
Audit trail
```

That is the product.


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
