# Phase 3.1 quality gate

## Customer value

- [x] A manager can invite a person who has no account.
- [x] The invited person chooses their own password and explicitly accepts.
- [x] Existing accounts authenticate rather than resetting a password through an invitation.
- [x] Managers can inspect, resend, and revoke invitations.
- [x] Local operation remains free and does not require Celery or a paid identity provider.

## Security and privacy

- [x] Raw invitation tokens are never stored.
- [x] Tokens use strong randomness and a secret-keyed digest.
- [x] Browser links use fragments rather than backend URL/query tokens.
- [x] Acceptance is CSRF-protected and rate-limited.
- [x] Owner invitation authority is owner-only.
- [x] Issuer authority is checked again at acceptance.
- [x] Responses containing invitation details use `Cache-Control: no-store`.
- [x] Tenant outsiders cannot enumerate invitation records.
- [x] Direct membership creation through the API is closed.

## Maintainability

- [x] Models, serializers, selectors, permissions, services, views, URLs, admin, migration, and tests are separated.
- [x] Email and frontend origins are environment-configured.
- [x] SMTP failure does not roll back the invitation record.
- [x] Audit events cover creation, reissue, resend, delivery, failure, revocation, acceptance, and membership creation.
- [x] Architecture, API, permissions, security, testing, deployment, and upgrade documentation are updated.

## Verification

- [x] Python source compiles and parses.
- [x] TypeScript and TSX parse successfully.
- [x] Migration source matches the model design under static review.
- [ ] Django/DRF runtime tests must pass in Docker.
- [ ] Frontend typecheck, component tests, build, and Playwright must pass in Docker.
- [ ] PostgreSQL migration drift check must report no changes.
