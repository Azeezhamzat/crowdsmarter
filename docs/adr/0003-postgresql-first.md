# ADR 0003: Use PostgreSQL as the initial data and search platform

- Status: Accepted
- Date: 2026-07-25

## Context

The platform needs relational integrity, transactional workflows, auditing, and later full-text search. Separate search and vector infrastructure would add cost and operational failure modes before demand exists.

## Decision

Use PostgreSQL for production and Docker development. Permit in-memory SQLite only for fast tests that do not exercise PostgreSQL-specific behaviour. Begin search with PostgreSQL filtering and full-text search.

## Consequences

The system gains strong transactions and a portable managed/self-hosted path. CI remains PostgreSQL-authoritative. A dedicated search system requires measured limitations and a new ADR.
