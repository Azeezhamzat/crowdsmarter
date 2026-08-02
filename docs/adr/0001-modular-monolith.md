# ADR 0001: Use a modular monolith

- Status: Accepted
- Date: 2026-07-25

## Context

The product has many business domains but no measured scaling boundary. A pre-revenue team must minimise operational cost and cognitive load while preserving domain clarity.

## Decision

Deploy one Django application and one PostgreSQL database. Express domain boundaries as Django apps with explicit services and tenant-safe selectors. Do not create microservices.

## Consequences

Transactions, testing, deployment, and local development remain simple. Domain coupling must still be reviewed. A domain may be extracted only after measured independent scaling, ownership, reliability, or release requirements justify the cost.
