# ADR 0027: Integrated analysis remains read-only and human-governed

## Status

Accepted.

## Context

By Phase 14, CrowdSmarter held evidence, assumptions, risks, stakeholder positions, foresight links, scenario assessments, collective evaluations, and minority reports. These records were trustworthy but distributed across specialised workspaces. An executive or decision team still needed to reconstruct the complete option picture manually.

A tempting implementation would materialise a single score or recommendation and allow it to drive the decision lifecycle. That would obscure uncertainty, collapse incompatible forms of judgement, and violate the product rule that humans decide.

## Decision

Phase 15 introduces an option-centred read model that composes existing tenant-scoped records without becoming a second source of truth. It may calculate transparent descriptive counts, sums, minima, means, and already-governed evaluation results, but it may not select an option, write reasoning records, or transition a decision.

Three governed records are added only where the existing domains cannot represent the customer workflow:

1. `DecisionIssue` records a human-accepted contradiction, gap, objection, vulnerability, or uncertainty with ownership and resolution history.
2. `DecisionQualityReview` records a versioned human judgement against an explicit checklist. It does not produce a universal quality score.
3. `ExecutiveDecisionSummary` records structured, versioned, human-approved synthesis.

Draft synthesis is visible only to accountable authorities. Published or approved versions are immutable and superseded by later versions rather than overwritten.

## Consequences

- Executives receive one coherent view while every conclusion remains traceable.
- Different evidence and judgement types are not collapsed into false precision.
- The decision lifecycle remains governed by existing services.
- Read-model changes can improve usability without migrating authoritative source records.
- Additional queries are accepted initially; measured performance may later justify PostgreSQL views or denormalised read tables behind the same contract.
- Any future AI drafting must create a separately attributable suggestion or explicit draft and require human acceptance.
