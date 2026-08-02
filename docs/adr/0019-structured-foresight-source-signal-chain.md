# ADR 0019 — Structured foresight source-to-signal chain

## Status

Accepted for Phase 11.

## Context

The existing product began when a decision was already visible. A foresight-driven platform must also preserve how organisations notice change and interpret uncertainty. Treating a URL, a signal, and a trend as interchangeable would hide the distinction between observation and judgement.

## Decision

Introduce a bounded `foresight` domain with separate records for:

- attributable sources;
- human-interpreted signals;
- accountable watchlists;
- explicit signal-to-decision relevance links.

A source may exist without a signal. A signal may reference one primary source and may later be supported by additional evidence. Feed synchronisation creates source records only. Signal impact, uncertainty, maturity, horizon, polarity, and relevance remain explicit human assessments.

The first release uses one primary STEEP category and one strategic horizon per signal. Multi-category tagging, trends, drivers, cross-impact relationships, scenarios, and signposts remain later domain slices.

## Rationale

The separation makes provenance inspectable and prevents automated ingestion from silently becoming strategic interpretation. It allows the same source to support evidence and foresight while keeping the human judgement visible.

## Consequences

- Users perform an explicit interpretation step after source capture.
- Signals can be linked to decisions without mutating decision state.
- Search and exports can preserve the complete source-to-signal-to-decision chain.
- Future trends, drivers, scenarios, and adaptive signposts can reference stable signal identifiers.
