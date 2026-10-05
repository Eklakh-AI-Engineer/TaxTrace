# TaxTrace Security

## Security model

TaxTrace may process sensitive financial and tax information. Security is therefore a system property rather than a UI feature.

## Current controls

The pilot baseline documents:

- JWT authentication;
- role-based permissions;
- tenant isolation;
- append-only audit events;
- path traversal protection for local storage;
- SHA-256 document hashing;
- HMAC-SHA256 webhook validation;
- evidence-grounded AI behavior;
- human approval for consequential notice drafts;
- environment-based secret configuration.

## Tenant isolation

Business queries should be scoped to the authenticated firm's tenant. Any new service or endpoint that accesses tenant-owned data must include isolation tests.

## AI safety

AI components must not be treated as authoritative tax/legal decision-makers.

Required controls include structured evidence inputs, fact/hypothesis separation, missing-information handling, auditable AI generations, human approval for consequential outputs, and provider data-handling review before production.

## Production gaps

The controlled-pilot milestone does not mean production security is complete.

Pending work includes:

- external penetration/security review;
- production secret rotation;
- retention/deletion validation;
- backup/restore validation;
- production observability;
- production AI-provider cost/data controls;
- staging and deployment hardening.

Never commit credentials, real client documents, or production secrets.
