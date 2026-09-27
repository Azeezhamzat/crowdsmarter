# Internal security and privacy review — 2026-08-30

## Scope and limitation

This is an engineering self-review of the repository and local Docker deployment. It is not independent, not a penetration test, and not a compliance certification. An external reviewer must validate the deployed service, infrastructure, policies, and organisational practices before real customer data is accepted.

## Data flow summary

The browser sends same-origin session-authenticated requests through Nginx to Django. Django enforces tenant membership and role policy and stores authoritative records in PostgreSQL. Private attachments use Django storage and are scanned before acceptance. Redis/Celery are optional delivery mechanisms, not authoritative stores. The optional local observability stack collects bounded metrics and structured container logs. SMTP and any external AI/storage provider are separately configured trust boundaries.

## Controls verified in code

- session authentication, CSRF enforcement, secure production cookies, HSTS and restrictive browser headers;
- tenant-safe selectors and repeated service-layer authorisation;
- immutable audit, position, transition, and finalisation records;
- generic authentication responses, throttling, password reset, verified email change, TOTP MFA, and backup codes;
- private no-store file downloads, extension/MIME/signature/size checks, SHA-256 metadata, fail-closed malware scanning, and clean-only production download/export;
- JSON request logs with request IDs and bounded route/status metrics;
- database and cache readiness probes plus local Prometheus/Loki/Grafana/Alertmanager configuration;
- delayed deletion requests and a non-destructive due-review report;
- SMTP and production-security deployment checks;
- an isolated PostgreSQL backup-restore drill.

## Findings

| Priority | Finding | Current mitigation | Required closure |
| --- | --- | --- | --- |
| High | No independent security/privacy assessment has occurred | This review documents scope and evidence honestly | Commission an independent code, deployment, privacy, and penetration review |
| High | Production SMTP credentials, DNS authentication, bounce handling, and inbox delivery are unverified | Startup validation and a provider acceptance runbook exist | Configure a provider and record end-to-end delivery evidence |
| High | Destructive tenant deletion and automated legal holds are not implemented | No automatic deletion; due items require manual review | Approve policy, implement two-person deletion/legal-hold workflow, test on synthetic data |
| High | Local alerts have no external receiver | Alerts remain visible in Alertmanager | Configure, trigger, receive, acknowledge, and resolve a monitored production alert |
| Medium | Built-in HTTP metrics are process-local | Single-process local tests are deterministic; logs and health remain centralised | Use a multiprocess-aware exporter or per-instance scraping before multi-worker SLO reporting |
| Medium | Local media storage is a single-host dependency | Private volume and tested metadata/export controls | Use encrypted private object storage, lifecycle rules, access logging, and recovery testing |
| Medium | Deployment secrets are flat environment files | Templates contain no credentials and production checks fail fast | Move production secrets to a managed secret store with rotation and least privilege |
| Medium | Image patching and vulnerability scanning are operational, not enforced in CI | Major service versions are pinned and application CI is present | Add container/dependency scanning, patch SLAs, SBOM/provenance, and immutable image digests |
| Medium | ClamAV resource demand changes the original small-host sizing assumption | Scanner is profile-gated locally and mandatory in production Compose | Load-test on the chosen host and size memory/CPU before launch |
| Medium | The pinned official ClamAV image is AMD64-only | Compose declares AMD64 so Apple Silicon can emulate it | Use an AMD64 production host or performance/security-review a maintained native ARM image |

## Privacy review notes

Metrics use route templates rather than object IDs. Application logs deliberately exclude bodies, query strings, tokens, uploaded file names, scanner signatures, and email content. User UUIDs remain personal data and require access control and expiry. Customer exports include private attachments only when verified clean. External AI, object storage, monitoring, or mail providers require a data-processing, residency, retention, subprocessor, and deletion assessment before activation.

## Release decision

The locally testable engineering foundations are suitable for further staging evaluation. The service is **not approved for production customer data** until every High finding is closed or formally risk-accepted by the accountable owner, a real restoration is evidenced, production alert delivery and email delivery are evidenced, and an independent reviewer signs off.
