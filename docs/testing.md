# Testing strategy

Tests target business behaviour, security boundaries, and customer-visible contracts rather than line coverage alone.

## Backend layers

- **Model tests:** identity and tenant invariants, immutable transitions, immutable position versions, immutable finalisation, invitation state metadata, token-at-rest rules, and append-only audit behaviour.
- **Service tests:** tenant authority, owner continuity, invitations, workspace creation, decision ownership and framing, participant restoration and offboarding, structured reasoning, position versioning, authority coverage, dissent handling, stale-state rejection, finalisation atomicity, and audit creation.
- **Permission tests:** organisation, workspace, decision, participant, position, finalisation, and audit role/object matrices independently of UI visibility.
- **API tests:** every implemented endpoint, strict unknown-field rejection, tenant isolation, permitted and denied roles, lifecycle history, position current/history reads, finalisation, and audit reads.
- **Operational tests:** liveness and database readiness.

Test settings use SQLite for rapid feedback when `DATABASE_URL` is absent. CI supplies PostgreSQL and is authoritative for constraints, transactions, row locking, and database-specific behaviour.

```bash
cd backend
python -m pip install -e '.[dev]'
pytest --cov=apps --cov-report=term-missing
python manage.py makemigrations --check --dry-run
ruff check .
ruff format --check .
mypy crowdsmarter apps
```

## Frontend layers

- API-client tests verify credentials, CSRF, and domain-error handling.
- Component tests verify accessible validation, invitation acceptance, structured review, position coverage, finalisation blocking, and lifecycle presentation.
- Playwright includes the public sign-in smoke test, owner-to-invitee onboarding, and opt-in authenticated decision workflow tests using `E2E_EMAIL` and `E2E_PASSWORD`.

```bash
cd frontend
npm install
npm test -- --run
npm run typecheck
npm run lint
npm run build
E2E_EMAIL='...' E2E_PASSWORD='...' npm run test:e2e
```

## Phase 4 behaviour matrix

Phase 4 tests cover:

1. support requiring an active option;
2. abstention/rejection excluding an option;
3. conditional support requiring conditions;
4. append-only position versioning;
5. observer and outsider denial;
6. current-position and complete-history API behaviour;
7. tenant isolation and strict command inputs;
8. every active decision owner and decision maker requiring a current position;
9. authorised decision owner, organisation manager, and designated decision-maker finalisation;
10. ordinary contributor denial;
11. stale expected-status rejection;
12. active same-decision option validation;
13. dissent-summary enforcement;
14. immutable finalisation and generic-transition bypass prevention;
15. atomic finalisation, transition history, and audit creation;
16. manager-only tenant audit reads.

Frontend coverage verifies that missing authorities are named, finalisation remains disabled until authority coverage is complete, and users are routed to the dedicated governance workflow instead of an ordinary status form.

## Regression rule

Every defect fix begins with a failing test at the lowest layer that reproduces customer-visible behaviour. Permission defects require permitted and denied cases. Lifecycle defects require state-before, command, and state/history-after assertions. Security-sensitive defects require a regression case proving the unsafe path is closed.

## Release verification

The Phase 5 one-terminal upgrade script runs focused outcome, lesson, search, landing-page, type, and build checks inside the built Docker images before reporting success. The full CI suite remains the release authority and should include PostgreSQL, frontend lint, and browser tests before public deployment.

## Phase 5 focused coverage

Phase 5 adds service, model, API, permission, and tenant-isolation tests for commitment, implementation, outcome review, implementation-owner transfer, lessons, archival, offboarding protection, and PostgreSQL full-text search. Frontend tests cover the integrated public landing page, the post-decision command surface, and tenant search results. Playwright includes a public-site smoke test in the same deployment used by the application.
