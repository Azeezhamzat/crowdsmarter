# ADR 0020 — Private source files and bounded feed ingestion

## Status

Accepted for Phase 11.

## Context

Evidence-heavy organisations need original reports, datasets, images, and internal records. Foresight teams also need a low-cost way to bring public RSS and Atom items into a source library. Public media URLs, unrestricted server-side fetching, or a paid content provider would conflict with security, zero-cost operation, and replaceability.

## Decision

Use Django's storage abstraction for private source attachments and a manually triggered, standard-library RSS/Atom retriever for public feeds.

Attachments are size limited, extension and MIME allowlisted, signature checked, SHA-256 recorded, stored under generated identifiers, tenant-authorised at download, and included in exports. Production can replace local storage with a private S3-compatible backend through configuration.

Feed retrieval rejects credentials, redirects, local/private addresses, responses over 2 MB, and unsafe XML. Production requires an explicit deployment allowlist. Feed items become unassessed sources and are never transformed automatically into signals.

## Rationale

This meets the immediate customer need without a separate object-storage service in development, a crawler, a commercial intelligence feed, or a worker dependency. It establishes clear replacement points for malware scanning, S3 storage, and future ingestion adapters.

## Consequences

- Local operation retains zero recurring cost.
- Production operators must configure trusted feed domains or leave feed retrieval disabled.
- Malware scanning remains a documented production-assurance integration point.
- Core decision and foresight workflows remain available if storage scanning, feeds, or the network are unavailable.
