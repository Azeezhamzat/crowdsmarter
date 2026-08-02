# ADR 0008: Explicit structured-reasoning readiness gate

## Status

Accepted for Phase 3.

## Context

A lifecycle label alone does not establish that a decision is ready. Advancing a decision without alternatives, supporting material, exposed assumptions, or recorded risks would create false confidence and weaken customer trust.

## Decision

The transition from `Under Review` to `Ready for Decision` is permitted only when the decision has:

- at least two active options;
- at least one active evidence record;
- at least one active assumption;
- no active assumption marked invalidated; and
- at least one risk that has not been closed.

The application exposes the counts and blockers to users. The transition remains a human command with an explicit rationale. The system does not score or choose an option.

## Rationale

This is the smallest enforceable gate that makes the Phase 3 records operationally meaningful. It improves reasoning completeness without introducing opaque scoring, automated decisions, or premature weighting frameworks.

## Consequences

- Incomplete decisions cannot be labelled ready.
- Users can see exactly which requirement is missing.
- Later phases can add stakeholder positions and finalisation rules without changing the underlying lifecycle architecture.
- The gate may evolve through a new ADR when customer evidence demonstrates different requirements.
