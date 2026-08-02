# ADR 0016: Explainable portfolio read models over PostgreSQL

## Status

Accepted.

## Context

Users need to know what requires their attention and managers need to see the organisation's decision flow. The existing workspace lists do not provide cross-workspace accountability, due dates, or operational filters.

## Decision

Build read-only portfolio services inside the modular monolith. The personal work view combines explicit decision ownership, active participation, and implementation ownership. The organisation portfolio applies tenant-safe filters over PostgreSQL records and derives visible measures from documented fields.

No portfolio state is stored separately. No workflow command depends on the read model.

## Consequences

- Users receive a useful daily entry point without a new database or warehouse.
- Measures remain explainable and can be recalculated from customer-owned records.
- Future pagination and indexing can be added without changing domain commands.
- Read-model failures cannot mutate or block the decision workflow.
