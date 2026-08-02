# Phase 6 quality gate

## Customer value

- Contributors can request a structured challenge of recorded reasoning without surrendering human authority.
- Users receive a private inbox for assignments, lifecycle changes, due reviews, accepted invitations, and completed advisory reviews.
- Organisation members can understand decision flow and learning through a small set of defined measures.
- All capabilities operate without a paid external service.

## Architecture

- `ai_assistance`, `notifications`, and `analytics` are explicit Django domains.
- AI providers implement an internal protocol and are selected through configuration.
- The default provider is deterministic, local, and zero-cost.
- AI output is stored separately and cannot invoke decision mutation services.
- Analytics query existing PostgreSQL data; no warehouse, vector database, or tracking SDK is introduced.
- The worker and scheduler remain optional deployment profiles.

## Security and governance

- All reads are authenticated and tenant- or recipient-scoped.
- AI request, acknowledgement, and dismissal permissions are checked server-side.
- Provider failures return safe messages and preserve internal diagnostic logs.
- Decision snapshots are customer-owned records and are not exposed through the API.
- Advisory review acknowledgement and dismissal are immutable and mutually exclusive.
- AI request throttling limits accidental or abusive provider consumption.

## Testing

- Every Phase 6 endpoint has API coverage.
- Tests cover tenant isolation, recipient privacy, role restrictions, no decision mutation, attribution, audit logging, notification deduplication, due-review delivery, immutable review disposition, and analytics definitions.
- Frontend tests cover the notification inbox, advisory review, and analytics pages.
- The upgrade script runs migration drift, focused backend tests, type checking, frontend unit tests, and a production build before reporting success.
