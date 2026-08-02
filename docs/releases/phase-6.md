# Phase 6 release notes

## Delivered

- Provider-neutral AI assistance interface configured through `AI_PROVIDER_BACKEND`.
- A transparent, deterministic, zero-cost rules provider enabled by default.
- Attributable decision snapshots and SHA-256 fingerprints for every advisory review.
- Review output for missing evidence, unsupported assumptions, contradictory evidence, missing stakeholder roles, material risks, and similar historical decisions.
- Immutable human acknowledgement or dismissal of completed advisory output.
- Safe provider-failure records that do not expose provider secrets or change decision data.
- Private in-app notifications for assignments, lifecycle changes, accepted invitations, due outcome reviews, and completed advisory reviews.
- An optional Celery Beat scheduler for due-review notifications, plus a synchronous management command.
- Explainable organisation analytics calculated directly from PostgreSQL decision, participant, outcome, and lesson records.
- Frontend pages for notifications, advisory review, and organisation analytics.
- Docker startup waits for PostgreSQL connectivity and backend health before exposing the frontend.
- Phase 6 migrations, permission and tenant-isolation tests, documentation, and a one-terminal Linux upgrade.

## Human-authority guarantees

- AI cannot select an option, submit a stakeholder position, finalise a decision, change lifecycle state, or alter any organisational record.
- Every AI review identifies the provider, model or rules identifier, requesting human, creation time, decision snapshot fingerprint, output, and human disposition.
- Dismissal and acknowledgement are explicit, attributable, mutually exclusive, and cannot be overwritten.
- The application remains fully usable when AI assistance is unavailable or disabled.

## Zero-cost operation

The default provider executes local deterministic rules and sends no customer data to an external service. Analytics use PostgreSQL, and notifications use the existing application database. Redis, Celery workers, and the scheduler remain optional; no paid model, warehouse, push-notification service, vector database, or external analytics platform is required.

## Deliberately excluded

- Automatic record changes based on AI output.
- AI option selection or decision finalisation.
- A hard-coded commercial AI provider.
- Vector embeddings or a vector database.
- A separate analytics warehouse or executive leaderboard.
- Email, SMS, mobile-push, or browser-push notification infrastructure.
- Automated claims that a decision is objectively “good” or “bad”.
