# Deployment and zero-cost operation

## Local development

Copy `.env.example` to `.env`, then run `docker compose up --build`. PostgreSQL is required. Redis and Celery are optional and live behind the `workers` profile.

## Pre-revenue production shape

The smallest credible deployment is one Linux host running:

- the production Django container;
- PostgreSQL with a persistent encrypted volume;
- the built frontend served by Nginx;
- a reverse proxy terminating HTTPS;
- optional Redis/worker containers only when a shipped feature needs them.

This can run on owned hardware or a suitable free compute allowance. Free-tier terms change, so the application does not encode a hosting provider.

## Required production configuration

At minimum set:

- `DJANGO_SETTINGS_MODULE=crowdsmarter.settings.production`;
- a long random `DJANGO_SECRET_KEY`;
- `DJANGO_ALLOWED_HOSTS`;
- `DJANGO_CSRF_TRUSTED_ORIGINS`;
- `DATABASE_URL`;
- `FRONTEND_BASE_URL` for invitation links;
- SMTP settings before external invitations;
- HTTPS proxy headers and certificates.

Production startup fails when the secret, allowed hosts, or database URL are absent. Run `python manage.py migrate` as an explicit release step before replacing application containers.

## Same-origin routing

Expose the static frontend and `/api`, `/admin`, `/health`, and `/static` under one HTTPS origin. This avoids cross-origin credential complexity and keeps Django's session and CSRF protections straightforward. The production frontend image proxies those paths to the environment-configured `BACKEND_UPSTREAM` value, which defaults to `backend:8000`. A CDN or static platform may provide equivalent rewrite rules without changing the application build.

## Database

Any PostgreSQL service is supported through `DATABASE_URL`. Before onboarding customer data:

1. schedule encrypted `pg_dump` backups;
2. test restoration, not only backup creation;
3. restrict network access and database roles;
4. monitor disk use and connection exhaustion;
5. document retention and deletion procedures.

Moving to managed PostgreSQL requires no application change.

## Media storage

Local filesystem storage is the default. Before multiple application replicas or untrusted uploads, install the backend's `s3` extra and set `STORAGE_BACKEND=s3` plus S3-compatible credentials. Upload validation and tenant-scoped file models belong to the vertical slice that introduces files.

## Email and invitations

The console backend is safe for development and the local UI exposes the current invitation link only when `DEBUG=true`. SMTP settings are environment-driven. Production invitation responses never return the raw link, so configure a working SMTP provider and `FRONTEND_BASE_URL` before inviting external users. Keep `DJANGO_SECRET_KEY` stable because invitation digests are keyed with it. No workflow assumes one commercial email provider.

## Workers

Do not run Redis or Celery solely because they are in the technology stack. Start workers when notifications, exports, or AI jobs are shipped. Synchronous records remain authoritative; queued work must be recoverable.

## Scaling sequence

1. Measure database, CPU, memory, and request latency.
2. Tune queries and indexes.
3. Increase single-host resources if cost-effective.
4. Separate managed PostgreSQL/storage.
5. Add stateless backend replicas behind a load balancer.
6. Add worker replicas by queue depth.
7. Consider orchestration only when deployment complexity justifies it.

## Phase 6 operational configuration

The default AI provider requires no key:

```env
AI_PROVIDER_BACKEND=apps.ai_assistance.providers.rules.RuleBasedAIProvider
API_AI_REVIEW_THROTTLE_RATE=20/hour
```

Core workflows, AI requests, analytics, and ordinary notifications run in the web process. Due-review delivery can be invoked manually:

```bash
docker compose exec backend python manage.py send_due_review_notifications
```

For scheduled daily delivery, start the optional profiles:

```bash
docker compose --profile workers up -d worker scheduler
```

A future external provider is enabled by installing its adapter in the backend image and changing `AI_PROVIDER_BACKEND`. This change must not require modifications to decision-domain code.

## Phase 11 storage and feed configuration

Local Docker development uses the existing private media volume mounted at `/app/media`. No new service is required.

Relevant environment variables:

```text
SOURCE_ATTACHMENT_MAX_BYTES=15728640
SOURCE_ATTACHMENT_ALLOWED_CONTENT_TYPES=application/pdf,text/plain,text/csv,application/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,image/png,image/jpeg,image/webp
SOURCE_ATTACHMENT_ALLOWED_EXTENSIONS=.pdf,.txt,.csv,.docx,.xlsx,.png,.jpg,.jpeg,.webp
FORESIGHT_FEED_ALLOWED_DOMAINS=
API_FORESIGHT_FEED_SYNC_THROTTLE_RATE=20/hour
```

Production should configure a private S3-compatible Django storage backend and an explicit comma-separated feed-domain allowlist. Leaving `FORESIGHT_FEED_ALLOWED_DOMAINS` empty disables production feed creation and retrieval safely. Storage migration changes Django `STORAGES` configuration rather than foresight domain code.
