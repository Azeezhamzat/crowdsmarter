# AI assistance architecture contract

AI is a supporting capability. Human judgement comes first, and no provider can select an option, submit a stakeholder position, finalise a decision, change lifecycle state, or silently modify an organisational record.

## Provider boundary

Application services depend on the `AIProvider` protocol in `apps.ai_assistance.providers.base`, not a vendor SDK. `apps.ai_assistance.providers.registry.get_provider()` selects the active provider from `PlatformConfiguration.ai_provider_key` (settable at runtime from Platform Administration, no redeploy required), falling back to the deploy-time `AI_PROVIDER_BACKEND` setting for any value it doesn't recognise. An adapter is responsible for invocation, credentials, timeouts, provider usage metadata, normalised structured output, and safe error translation.

Phase 6 uses `RuleBasedAIProvider` by default. It is deterministic, local, transparent, and zero-cost. It reviews only the decision snapshot supplied by the service and makes no network request.

A later addition provides `AnthropicAIProvider` (`apps.ai_assistance.providers.anthropic`) as an operator-selectable real-model alternative. It sends the same decision snapshot to the Anthropic Messages API via a forced tool-use call, so the response is structurally validated JSON rather than free text, then strips any `related_id`/`similar_decisions` reference that doesn't match something actually present in the snapshot before constructing `AIReviewOutput` — the model cannot fabricate a reference to organisational data that doesn't exist. Its system prompt explicitly restates the same "advisory only, cannot alter records" boundary this document defines. The API key is supplied by a platform administrator through Platform Administration → Platform settings, encrypted at rest with a key derived from `SECRET_KEY` (`apps.platform_admin.crypto`), and decrypted only at the moment of the API call. It is never returned by any API response, never written to the audit log (which instead records only whether a key was already set and its last 4 characters), and never logged. Selecting Anthropic without a key configured is rejected at the model-validation layer.

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
