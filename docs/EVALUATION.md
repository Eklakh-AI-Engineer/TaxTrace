# TaxTrace Evaluation

## 1. Current verification layers

The pilot-ready milestone records separate verification layers:

- backend pytest suite;
- frontend Vitest suite;
- reconciliation benchmark gates;
- AI quality gates;
- security checks;
- frontend production build.

The current recorded milestone reports 134 backend tests, 15 frontend tests, 7 benchmark gate tests, and 32 AI quality-gate tests passing.

These are recorded results. This documentation change does not claim to have executed them.

## 2. Reconciliation benchmark

The reconciliation benchmark evaluates deterministic exception classification.

Recorded pilot gates include:

| Exception class | Precision target | Recall target |
|---|---:|---:|
| matched | ≥ 0.90 | ≥ 0.85 |
| missing in 2B | ≥ 0.90 | ≥ 0.85 |
| value mismatch | ≥ 0.90 | ≥ 0.85 |

The pilot milestone records 1.000 precision and 1.000 recall for the reported benchmark cases.

Run:

```bash
python evaluations/benchmark_reconciliation.py
```

Do not present the historical result as a fresh measurement without rerunning the benchmark.

## 3. AI quality gates

The pilot milestone records checks for:

- unsupported claim rate;
- fact/hypothesis separation;
- confidence scoring;
- evidence linking;
- citation behavior;
- missing-information handling;
- non-fabrication.

## 4. Evaluation boundaries

The benchmark suite is not a substitute for production validation.

Before production use, evaluation should include representative anonymized data, broader document formats, provider-specific behavior, adversarial inputs, latency/cost measurements, regression datasets, human CA review, and security/privacy testing.

## 5. Evidence policy

Do not construct evaluation labels from model output. Benchmark inputs and expected results must remain independent from the system being measured.
