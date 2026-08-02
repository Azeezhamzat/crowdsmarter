# ADR 0006: Keep pre-revenue infrastructure zero-cost and provider-neutral

- Status: Accepted
- Date: 2026-07-25

## Context

The company is pre-revenue. Recurring infrastructure spend can become accidental product architecture when hosted identity, search, storage, or AI APIs are introduced too early.

## Decision

Use open-source components that run locally or on a single self-hosted/free compute environment. Configure PostgreSQL, SMTP, Redis, storage, and future AI adapters through environment-driven interfaces. Do not make a paid service mandatory for a core workflow.

## Consequences

The initial system can operate without software licence fees and can move to managed infrastructure by changing deployment configuration. Free offerings are not treated as durable guarantees. Operational labour, domains, backups, and security still have real costs and must be planned honestly.
