# AI assistance architecture contract

AI assistance is deferred until the underlying decision records and review workflow are valuable without it. When introduced, it will follow these constraints.

## Provider boundary

Application services depend on an internal interface, not a vendor SDK. A provider adapter is responsible for:

- model invocation;
- authentication and endpoint configuration;
- timeout/retry translation;
- provider usage metadata;
- normalising structured output;
- redacting provider-specific errors.

Provider names, model identifiers, and credentials are configuration. Domain records never contain provider SDK objects.

## Assistance record

Each generated result is persisted as a reviewable assistance record containing:

- organisation and decision scope;
- assistance type;
- provider and model identifier;
- prompt/template version;
- source record identities and versions;
- generated output;
- creation time and initiating human/system actor;
- status: pending review, accepted as reference, dismissed, or superseded;
- reviewer and review rationale;
- usage/cost metadata where available;
- failure details safe for customer display.

AI output does not overwrite evidence, assumptions, risks, positions, or decision rationale. A human may use an assistance result to propose an explicit record change, which follows the ordinary audited workflow.

## Permitted responsibilities

- summarise existing contributions;
- identify potentially missing evidence;
- identify unsupported assumptions;
- identify contradictions for human review;
- suggest potentially missing stakeholder categories;
- retrieve similar historical decisions;
- highlight risks already implied by the record.

## Prohibited behaviour

- selecting or finalising an option;
- changing lifecycle state;
- silently creating or modifying organisational records;
- representing generated claims as verified evidence;
- concealing provider/model provenance;
- making dismissal difficult;
- using customer data for a provider purpose not covered by contract and configuration.

## Zero-cost mode

The application must function with AI disabled. Development may use a deterministic fake adapter and optionally a locally operated model adapter. No paid model request may be required to create, review, finalise, implement, or learn from a decision.
