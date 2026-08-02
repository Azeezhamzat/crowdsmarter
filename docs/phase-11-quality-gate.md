# Phase 11 quality gate

Phase 11 is complete only when the following behaviours pass.

## Customer value

- a member can preserve an attributable source and original private file;
- a contributor can interpret a source as a structured signal;
- an organisation can inspect signals by STEEP category and time horizon;
- a signal can be monitored in a watchlist and linked explicitly to a decision;
- decision evidence can reference the same structured source;
- customer exports preserve foresight metadata and available original files.

## Governance and permissions

- every record is tenant scoped;
- viewers cannot create or change foresight records;
- contributors can manage records they create or own;
- managers can administer tenant records;
- private downloads require current membership and are audited;
- feed, signal, and watchlist ownership cannot be stranded during offboarding;
- feed ingestion never creates a signal or changes a decision.

## Security

- file size, extension, MIME, and signature rules are tested;
- duplicate file digests on one source are rejected;
- stored paths do not use customer-supplied names;
- download responses are private and non-cacheable;
- RSS/Atom URLs reject credentials and private network destinations;
- redirects and unsafe XML are rejected;
- feed responses are time and size bounded;
- production retrieval requires a domain allowlist;
- no local configuration, media file, secret, cache, or dependency folder enters the release archive.

## Maintainability

- foresight writes use explicit transactional services;
- REST endpoints remain thin and use strict serializers;
- search, evidence, overview, export, audit, and offboarding integrations have tests;
- migrations match models with no drift;
- the frontend uses existing design tokens and no paid dependency;
- architecture, API, permissions, security, deployment, testing, and onboarding documentation describe the actual release.
