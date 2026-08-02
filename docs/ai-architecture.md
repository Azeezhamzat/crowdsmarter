# AI assistance architecture contract

AI is a supporting capability. Human judgement comes first, and no provider can select an option, submit a stakeholder position, finalise a decision, change lifecycle state, or silently modify an organisational record.

## Provider boundary

Application services depend on the `AIProvider` protocol in `apps.ai_assistance.providers.base`, not a vendor SDK. `AI_PROVIDER_BACKEND` selects a provider by import path. An adapter is responsible for invocation, credentials, timeouts, provider usage metadata, normalised structured output, and safe error translation.

Phase 6 uses `RuleBasedAIProvider` by default. It is deterministic, local, transparent, and zero-cost. It reviews only the decision snapshot supplied by the service and makes no network request.

## Assistance record

Every request creates an `AIReview` containing:

- organisation and decision scope;
- requesting human;
- provider, model or rules identifier, and prompt/schema version;
- private source snapshot and SHA-256 fingerprint;
- status, output, safe failure message, and timestamps;
- immutable human acknowledgement notes or dismissal reason.

The API does not expose the private source snapshot. Output remains separate from evidence, assumptions, risks, positions, finalisation, outcomes, and lessons. A human may act on a finding only through the ordinary permissioned and audited workflow.

## Phase 6 review responsibilities

- identify absent or option-unspecific evidence;
- highlight unverified or invalidated assumptions;
- expose directly opposing evidence stances;
- identify missing stakeholder roles;
- highlight material recorded risks;
- retrieve similar historical decisions using transparent term overlap;
- explain limitations and provenance.

## Prohibited behaviour

- selecting or finalising an option;
- changing lifecycle state;
- silently creating or modifying organisational records;
- representing generated claims as verified evidence;
- concealing provider or model provenance;
- overwriting human acknowledgement or dismissal;
- making the core workflow depend on provider availability;
- sending customer data to a provider not covered by deployment configuration and contract.

## Adding a provider

A new adapter must implement the internal protocol, return `AIReviewOutput`, avoid database mutation, redact provider-specific errors, and be tested with deterministic fixtures. Before production use, document data sent, purpose, retention, training use, region, credentials, timeouts, retries, rate limits, cost controls, and the configuration-only rollback path.
