# ADR 0013: Provider-neutral advisory AI with a zero-cost default

## Status

Accepted for Phase 6.

## Context

The CrowdSmarter must assist organisational reasoning without transferring decision authority to a model, creating a paid-service dependency before revenue, or coupling the product to one provider. AI output may contain mistakes and must never silently rewrite customer records.

## Decision

The application depends on an internal provider protocol. `AI_PROVIDER_BACKEND` names a replaceable Python adapter. Phase 6 ships a deterministic rules provider that runs locally and requires no external account, network request, or recurring cost.

Each request persists an `AIReview` containing:

- tenant, decision, and requesting human;
- provider and model or rules identifier;
- prompt/schema version;
- a deterministic snapshot and SHA-256 fingerprint;
- structured output or a safe failure state;
- human acknowledgement or dismissal and rationale;
- creation, start, completion, and review timestamps.

The snapshot is not returned by the customer API. Output is a separate advisory record and has no service pathway to alter decision framing, options, evidence, assumptions, risks, positions, finalisation, outcomes, or lessons.

## Consequences

- The complete workflow operates with AI disabled or failing.
- A local model or commercial API can be introduced through a new adapter and configuration, not a domain rewrite.
- Provider adapters must return the stable internal output contract and must not mutate database records.
- Provider errors are logged internally and represented to customers with a safe generic message.
- Each new provider requires privacy, security, data-residency, cost, timeout, and output-quality review.
