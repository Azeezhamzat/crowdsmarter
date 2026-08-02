# ADR 0018 — Versioned customer-owned export archives

## Status

Accepted.

## Context

Customer ownership requires more than database backups. Organisations need a documented, readable, portable copy of their decision records without depending on CrowdSmarter software or one infrastructure provider.

## Decision

Provide ZIP archives with a versioned manifest. Complete organisation exports contain JSON datasets for every governed tenant domain and CSV copies of major registers. Decision dossiers contain a readable summary plus JSON and CSV datasets for one decision.

Password hashes and invitation token digests are excluded by design. Organisation-wide exports require an active owner or administrator. Decision dossiers use the existing tenant-safe decision selector. Every download is audited and returned with private, no-store response headers.

## Consequences

The schema can evolve through manifest versions. Synchronous in-memory generation is acceptable at pre-revenue scale and remains isolated behind a service boundary so larger installations can move generation to background or streaming infrastructure later.
