# AI Compliance Execution Platform for Small Indian CA Firms

**Status:** Pre-build baseline  
**Version:** 1.0  
**Date:** 24 September 2026  
**Audience:** Founder/developer, AI engineers, backend/frontend engineers, QA, security reviewers, future contributors

---

## 1. Executive Summary

This project is an **evidence-first AI compliance execution platform for small Indian Chartered Accountant (CA) firms**.

The initial product is not intended to replace a CA, accounting package, GST filing platform, or professional judgment. It is designed to sit between a CA firm's incoming documents and its final human-approved compliance action.

The core operating principle is:

> **AI prepares → Evidence explains → CA approves.**

The first workflow to validate is GST reconciliation, especially comparison of a purchase register against GSTR-2B. The second workflow is compliance-notice understanding and source-grounded response drafting. WhatsApp is an intended low-friction intake/command channel, while a web review workspace is used for detailed investigation.

The original project proposal identified manual GST reconciliation, notice drafting, deadline tracking, a WhatsApp-first interface, FastAPI + Claude API + Supabase, and a ₹999–₹1,999/month pricing hypothesis. This project brief retains the problem and technical direction but revises the differentiation: basic GST reconciliation and WhatsApp automation are already competitive categories, so the product must differentiate through **evidence, explainability, deterministic reconciliation, provenance, human approval, and measurable time savings**.

---

## 2. Problem Statement

Small CA firms frequently coordinate compliance work using a mixture of:

- spreadsheets and CSV/XLSX files;
- accounting-system exports;
- PDFs and scanned documents;
- GST portal data;
- email;
- WhatsApp;
- manual checklists;
- internal working papers.

A recurring problem is not merely "finding a mismatch." It is the effort required to:

1. ingest inconsistent data;
2. normalize it;
3. reconcile records;
4. identify exceptions;
5. investigate the reason;
6. collect evidence;
7. communicate with the client/vendor;
8. prepare a response or working paper;
9. track what remains pending;
10. preserve an audit trail.

The project aims to reduce this operational burden while preserving professional control.

---

## 3. Product Thesis

### Original thesis

> Build an AI Micro-SaaS for CA/Tax firms using a WhatsApp bot for GST reconciliation, compliance notice drafting and deadline tracking.

### Revised thesis

> Build the AI execution/workpaper layer between incoming CA-firm data and the final human-approved compliance action.

### Differentiation hypothesis

The product should not claim uniqueness because it uses:

- AI;
- Claude/GPT;
- RAG;
- WhatsApp;
- GST reconciliation.

Those capabilities are already appearing in competing products.

The differentiation to validate is:

> **Evidence-first compliance execution:** every important result should be traceable to source records, matching rules, retrieved authorities or explicit human input.

---

## 4. Product Principles

1. **Human authority remains with the CA.**
2. **Numerical reconciliation is deterministic first.**
3. **LLMs explain and generate; they do not silently decide financial truth.**
4. **Every consequential AI output should have provenance.**
5. **Uncertainty must be visible.**
6. **No unsupported legal citation.**
7. **Default to conservative automation.**
8. **Tenant isolation is mandatory.**
9. **Client data must never leak across firms.**
10. **Measure time saved, not AI activity.**
11. **Build around existing CA workflows before forcing workflow replacement.**
12. **Prefer small, testable increments over broad autonomous behavior.**

---

## 5. Initial Target Customer

### Initial ICP

A small Indian CA firm or lean tax/compliance team that:

- has recurring GST compliance workload;
- manages multiple MSME clients;
- uses Excel/CSV, PDFs, Tally/accounting exports, email and WhatsApp;
- does not want a large enterprise implementation;
- is willing to use AI as an assistant with CA review;
- can provide authorized/anonymized sample data for a pilot.

### Primary users

| User | Main need |
|---|---|
| CA Partner | Oversight, exception review, approval |
| Senior Accountant | Reconciliation, investigation, working papers |
| Junior/Article | Document collection, first-pass checks, follow-up |
| End Client | Submit documents and respond to requests |

---

## 6. Initial Product Pillars

### RECONCILE

Purchase Register + GSTR-2B ingestion, normalization, deterministic matching and exception management.

### RESPOND

Notice extraction, source-grounded retrieval, evidence-backed drafting and CA review.

### FOLLOW UP

Tasks, due dates, client/vendor requests, reminders and status tracking.

---

## 7. MVP Boundary

### In scope

- firm/user authentication;
- client management;
- purchase-register upload;
- GSTR-2B upload/import;
- canonical transaction schema;
- deterministic matching;
- controlled fuzzy matching;
- exception classification;
- evidence view;
- AI explanation;
- reconciliation export;
- notice PDF ingestion;
- structured notice extraction;
- RAG over approved sources;
- draft response generation;
- citation/provenance tracking;
- audit events;
- basic WhatsApp intake/commands;
- minimal review web UI.

### Out of scope for MVP

- autonomous tax filing;
- autonomous submission of legal responses;
- full accounting-system replacement;
- full CA practice-management suite;
- every GST return/form;
- every Indian tax domain;
- unrestricted autonomous agents;
- unverified legal research;
- production use with real client data before security and privacy controls are validated.

---

## 8. Core Success Criteria

The MVP is successful only if a pilot demonstrates measurable improvement in at least these dimensions:

- acceptable reconciliation precision;
- acceptable exception recall;
- valid evidence references;
- high citation validity for notice drafts;
- reduced investigation time;
- manageable AI/infrastructure cost;
- low rate of unsafe/unsupported outputs;
- repeated use across compliance periods.

---

## 9. Major Risks

- incorrect financial matching;
- hallucinated legal references;
- privacy/data leakage;
- unauthorized action;
- model/provider outage;
- escalating LLM cost;
- poor user adoption;
- over-broad scope;
- commoditization by existing products.

---

## 10. Non-Negotiable Safety Boundary

The system is a professional-assistance tool.

It must not present AI-generated content as independently verified professional advice.

All legal/compliance drafts must be:

- clearly identified as drafts;
- editable;
- source-grounded;
- reviewable;
- attributable to the evidence used;
- subject to CA approval before external use.

---

## 11. First Development Objective

Do not start with the full SaaS.

The first engineering milestone is:

> **A reliable reconciliation engine that takes authorized Purchase Register + GSTR-2B datasets and produces a reviewable exception report with evidence and deterministic reasons.**

Everything else should be layered around this foundation.

---

## 12. Source Basis

Primary project source:

- Uploaded proposal: `Doc1.docx` — "AI Micro-SaaS for CA/Tax Firms."

The proposal describes the original problem, target customer, WhatsApp-first MVP, FastAPI + Claude + Supabase stack, initial pricing hypothesis and proposed acquisition approach.

External research used for this project definition is summarized in the project's research report and includes GST Portal/GSTN guidance and public product documentation from current GST/accounting/CA automation vendors.

See `DECISIONS.md`, `PRD.md` and `README.md` for how source-derived assumptions were converted into engineering requirements.


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
