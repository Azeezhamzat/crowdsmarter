# Phase 12 quality gate

Phase 12 is complete only when the following behaviour passes in Docker with PostgreSQL.

## Domain behaviour

- canvas ownership is limited to active organisation members;
- viewers cannot create mapping records;
- all driver, signal, relationship, loop, implication, and decision references are tenant-safe;
- causal self-links and cross-canvas links are rejected;
- feedback loops require at least two distinct same-canvas drivers and preserve their human-defined sequence;
- futures-wheel depth cannot exceed three orders;
- archived canvases are read-only;
- strategic implications linked to decisions appear in the decision overview;
- active ownership blocks unsafe member offboarding;
- material commands create audit events.

## API behaviour

- every Phase 12 route requires authentication;
- tenant outsiders receive 404 rather than object disclosure;
- unknown command fields fail explicitly;
- serializers remain API-only and services own workflows;
- canvas workspace responses contain prefetched, bounded records.

## Frontend behaviour

- users can create and govern a canvas without a second tool;
- drivers can be grounded in Phase 11 signals;
- causal links and explicit feedback loops remain understandable without drag-and-drop drawing;
- stakeholder influence and exposure are plotted in a genuine matrix rather than merely listed;
- Futures Wheel and Three Horizons remain usable on desktop and narrow screens;
- implications can be linked to decisions and opened from the decision overview;
- keyboard focus, labels, error states, empty states, and reduced-motion behaviour remain present.

## Operational behaviour

- migrations apply without drift;
- existing Phase 11 records remain intact;
- organisation exports include Phase 12 records;
- PostgreSQL search returns new foresight records;
- the upgrade script backs up the database, preserves Phase 11 source, verifies both services, and restores both the Phase 11 source and pre-upgrade database automatically after a failed validation step.
