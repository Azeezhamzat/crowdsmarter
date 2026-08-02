# Phase 1 quality gate

A Phase 1 feature is complete only when all applicable items are true.

## Customer value

- An authorised user can establish a tenant and accountable owner.
- Membership authority is understandable and enforceable.
- Cross-tenant data is not disclosed.
- Material changes are attributable.

## Engineering

- Business logic lives in transactional services.
- API views and serializers remain thin.
- Every endpoint has automated tests.
- Every role boundary has allowed and denied tests.
- Owner-continuity and tenant-isolation rules have regression tests.
- Migrations are committed and migration drift is checked in CI.
- Backend lint/type checks and frontend lint/type/build checks pass.

## Security

- Session authentication and CSRF are enforced.
- Login is rate-limited and errors do not distinguish account existence.
- Production secrets and allowed hosts fail fast.
- Secure cookies and HTTPS security settings are enabled in production.
- Audit events are append-only through normal application interfaces.

## Operations

- Database readiness is distinct from process liveness.
- Required workflows do not depend on a worker.
- Logs go to standard output.
- Deployment and restore expectations are documented.

## Deferred before customer production

Before storing live customer data, complete an external security review, tested backup restoration, privacy policy and data-processing documentation, monitoring/alerting selection, and an incident-response runbook.
