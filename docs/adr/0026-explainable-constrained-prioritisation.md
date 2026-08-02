# ADR 0026: explainable constrained portfolio prioritisation

## Status

Accepted for Phase 14.

## Context

Organisation-level portfolio views show decisions but do not compare them through collectively assessed criteria or finite resource envelopes. A black-box optimiser would conflict with CrowdSmarter's explainability, human-authority, and evidence-traceability principles.

## Decision

Introduce organisation-scoped prioritisation portfolios with accountable ownership, weighted criteria, candidate decisions, independent assessments, optional peer anonymity, sealed aggregate results, budget and capacity constraints, and explicit authority selections.

The service computes a deterministic, explainable greedy recommendation. Mandatory candidates are considered first, followed by candidates ranked by confidence-aware weighted score. Every included or excluded candidate exposes the relevant resource effect or constraint reason. The recommendation never changes candidate decisions, allocates resources, or records final organisational approval.

Authorised managers record actual selections and rationale separately from the recommendation. This separation preserves the distinction between collective intelligence, analytical support, and accountable authority.

## Consequences

- teams can compare a portfolio without hiding trade-offs behind a composite score;
- resource limits are explicit and inspectable;
- sealed assessment protects independent contribution;
- recommendations remain reproducible but are deliberately not mathematically optimal claims;
- later Phase 15 adaptive action portfolios can extend this foundation with contingent and reversible actions.
