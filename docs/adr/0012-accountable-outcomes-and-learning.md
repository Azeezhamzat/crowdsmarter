# ADR 0012: Use dedicated commands for post-decision learning

## Status

Accepted in Phase 5.

## Context

Changing a decision from finalised to archived is not a clerical status update. The organisation must record what it committed to, who owns implementation, how success will be judged, what was implemented, what actually happened, and what should be reused later.

## Decision

The final lifecycle steps use dedicated transactional services rather than the generic transition endpoint. A one-to-one `DecisionReview` progressively records commitment, implementation, and outcome assessment. `Lesson` records capture reusable learning. Archival requires at least one active lesson. PostgreSQL full-text search retrieves these records alongside earlier decision reasoning.

## Consequences

- Lifecycle status cannot advance without the customer-value record for that stage.
- Human accountability and stale-state protection are preserved.
- Offboarding cannot strand active implementation ownership.
- The model remains inside the modular monolith and PostgreSQL.
- More specialised analytics may later be derived from these records without changing their meaning.
