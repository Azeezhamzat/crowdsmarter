# ADR 0021 — Structured systems foresight canvases

## Status

Accepted for Phase 12.

## Context

A free-form whiteboard can draw almost anything but does not reliably preserve provenance, permissions, rationale, or reusable organisational knowledge. CrowdSmarter needs systems thinking without turning causal claims into unexplained graphics.

## Decision

Systems foresight is represented through explicit domain records: canvases, drivers, signal links, stakeholders, causal relationships, feedback loops, futures-wheel consequences, Three Horizons items, and strategic implications.

Every record is tenant-scoped and attributable. Causal relationships require source and target drivers, polarity, strength, delay, and rationale. Feedback loops require an explicitly ordered sequence of at least two same-canvas drivers and a human explanation of the loop behaviour. Visualisations are projections of these governed records rather than the source of truth.

## Consequences

- relationships remain auditable and exportable;
- the interface can offer useful maps without storing opaque diagram coordinates;
- later scenario and wind-tunnelling workflows can reuse drivers and implications;
- users cannot freely position arbitrary shapes or claim that the system discovered causality;
- richer visual layout may be added later without changing the domain model.
