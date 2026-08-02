# ADR 0015: Decision overview as a read model

## Status

Accepted for Phase 8.

## Context

The previous decision workspace exposed framing, lifecycle, reasoning, participants, and navigation with similar visual weight. Users had to understand the methodology before they could identify the next useful action.

## Decision

Add a tenant-scoped overview read model that derives:

- lifecycle progress;
- the next required action;
- framing completeness;
- participant-role coverage;
- unresolved questions and concerns;
- active options and associated evidence/risk counts;
- current material risks;
- target-date status;
- the existing transparent reasoning gate.

The read model cannot mutate a decision. Business rules and permissions remain in the existing services and workflow commands.

## Rationale

- Reduces cognitive load without moving business logic into React.
- Gives executives a coherent summary while preserving detailed records.
- Keeps the API thin and the source of truth in PostgreSQL.
- Avoids caching or a separate analytics store before demonstrated need.

## Consequences

- The endpoint performs several bounded aggregate queries for one decision.
- Query optimisation should be driven by measured use, not speculative scale.
- The next-action text is explainable product guidance, not an AI recommendation.
