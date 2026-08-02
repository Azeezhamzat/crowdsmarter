# ADR 0007: Stage lifecycle transitions by domain readiness

## Status

Accepted.

## Context

The product requires an eleven-state decision lifecycle. Phase 2 implements framing, participants, and lifecycle infrastructure, while options, finalisation, commitments, reviews, and lessons arrive in later slices.

## Decision

Represent the complete lifecycle immediately, but enable only transitions whose required domain records and validation exist. Return the next blocked transition and rationale through the API and show it in the interface.

## Rationale

Hiding later states would weaken the product contract. Allowing them without supporting records would create false governance and unreliable organisational history. Explicit blocking preserves both simplicity and integrity.

## Consequences

- Later slices extend transition validators rather than replacing the lifecycle design.
- Customers can see the intended workflow without entering invalid states.
- Transition services remain the only status mutation path.
- Reversals require a separate, evidence-based design decision.
