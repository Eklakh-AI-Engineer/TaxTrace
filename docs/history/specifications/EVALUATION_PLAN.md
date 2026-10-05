# Evaluation Plan

**Version:** 1.0

---

# 1. Objective

Measure whether the product is accurate, useful, safe and economically viable before real production reliance.

Evaluation is divided into:

1. deterministic reconciliation;
2. document extraction;
3. AI explanations;
4. RAG retrieval;
5. legal drafting;
6. end-to-end workflow;
7. operational metrics.

---

# 2. Evaluation Dataset

Build a controlled dataset containing:

- synthetic records;
- explicitly authorized/anonymized real-world patterns;
- edge cases;
- known difficult invoice numbers;
- missing invoices;
- duplicate candidates;
- amount differences;
- GSTIN differences;
- date differences;
- multi-line/multi-document patterns.

Never use unapproved client data in evaluation.

---

# 3. Reconciliation Metrics

## Precision

```text
correct_matches / all_system_confirmed_matches
```

## Recall

```text
correctly_detected_exceptions / all_labelled_exceptions
```

## Candidate quality

For fuzzy matching:

```text
true candidate pairs / all generated candidates
```

## False positive rate

Particularly important for:
- matched;
- duplicate;
- high-severity exception.

---

# 4. Target Thresholds

Initial internal targets should be set after a baseline run.

Suggested starting gates:

| Metric | Initial gate |
|---|---:|
| Exact-match precision | ≥ 99% |
| High-confidence match precision | ≥ 99% |
| Exception recall | ≥ 95% |
| Critical false-positive rate | ≤ 1% |
| Evidence linkage success | ≥ 99% |
| Citation verification pass rate | ≥ 99% for approved-source citations |

These are engineering gates, not claims of regulatory accuracy. They must be validated on a representative labelled dataset.

---

# 5. AI Explanation Evaluation

Human reviewers score:

- factual correctness;
- evidence coverage;
- clarity;
- uncertainty handling;
- action usefulness;
- unsupported claim rate.

Use a 0–2 rubric:

```text
0 = unacceptable
1 = usable with correction
2 = correct/useful
```

Track unsupported claims separately.

---

# 6. RAG Evaluation

Measure:

### Retrieval Recall

Was the correct source/chunk retrieved?

### Citation Precision

Does each cited source actually support the claim?

### Groundedness

Does the response stay within retrieved evidence?

### Version correctness

Does the response use the appropriate source version/effective period where relevant?

---

# 7. Notice Draft Evaluation

Reviewers assess:

1. factual extraction;
2. notice issue identification;
3. source validity;
4. citation support;
5. completeness;
6. unsupported claims;
7. invented facts;
8. tone/format;
9. edit distance required from CA.

A draft fails if it invents:
- facts;
- documents;
- payments;
- legal citations;
- procedural events.

---

# 8. Safety Evaluation

Adversarial tests:

- prompt injection inside uploaded documents;
- malicious instructions in PDFs;
- cross-tenant retrieval attempts;
- attempts to expose system prompts;
- attempts to trigger external actions;
- hallucinated citation requests;
- missing evidence;
- ambiguous notice language.

Expected behavior:

```text
detect → constrain → explain limitation → require human review
```

---

# 9. User Evaluation

Pilot metrics:

- task completion time;
- minutes saved;
- correction time;
- repeat usage;
- number of AI suggestions accepted;
- number of overrides;
- perceived trust;
- onboarding time.

---

# 10. Cost Evaluation

Track per operation:

```text
document processing cost
LLM cost
embedding cost
storage cost
queue/compute cost
```

Primary unit metric:

> Cost per client-period reconciliation.

Secondary:

> Cost per notice draft.

---

# 11. Evaluation Reports

Each release should record:

- dataset version;
- code commit;
- model/version;
- prompt version;
- rule version;
- metrics;
- failures;
- known limitations.

Do not compare metrics from different datasets without explicitly noting the change.


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
