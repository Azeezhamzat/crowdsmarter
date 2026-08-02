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

## Phase 6 coverage

Focused backend tests cover notification privacy and deduplication, due-review delivery, advisory-provider output, attribution, no decision mutation, role restrictions, tenant isolation, immutable acknowledgement and dismissal, safe input rejection, and analytics definitions. Frontend tests cover the notification inbox, advisory-review page, and organisation analytics page.

Provider adapters should be contract-tested with deterministic fixtures. Tests must confirm that provider failures do not modify decisions and that customer-facing errors do not expose credentials, raw exceptions, or provider-specific secrets.

## Phase 7 focused tests

```bash
pytest apps/collaboration apps/portfolio apps/notifications
```

```bash
npm test -- --run \
  src/features/collaboration/DecisionCollaborationPage.test.tsx \
  src/features/portfolio/MyWorkPanel.test.tsx \
  src/features/portfolio/OrganisationPortfolioPage.test.tsx
```

The complete suite remains required before public deployment.

## Phase 8 focused tests

```bash
pytest apps/decisions/tests/test_templates_and_overview.py \
  apps/decisions/tests/test_api.py \
  apps/decisions/tests/test_services.py
```

```bash
npm test -- --run \
  src/features/decisions/GuidedDecisionCreatePage.test.tsx \
  src/features/decisions/DecisionLifecycle.test.tsx
```

The Phase 8 upgrade also runs Django system checks, migration-drift checks, frontend type checking, and a production frontend build. Template tests confirm that prompts remain advisory and that guided creation still produces a Draft. Overview tests confirm tenant isolation and accurate read-side composition.

## Phase 10 focused tests

```bash
pytest apps/accounts/tests/test_api.py apps/exports/tests/test_api.py
```

Coverage includes generic recovery responses, single-use reset tokens, current-password enforcement, session preservation, profile attribution, manager-only organisation exports, tenant-isolated decision dossiers, manifest contents, and exclusion of password and invitation-token secrets.

```bash
npm test -- --run \
  src/features/auth/LoginPage.test.tsx \
  src/features/auth/ForgotPasswordPage.test.tsx \
  src/features/auth/ResetPasswordPage.test.tsx \
  src/components/AppShell.test.tsx
```

The upgrade also runs complete frontend type checking and a production build.

## Phase 11 test behaviour

Foresight tests cover:

- tenant-isolated source, signal, feed, attachment, watchlist, and decision-link reads;
- viewer write denial and contributor record ownership;
- active-member ownership and offboarding protection;
- source-to-signal-to-watchlist-to-decision traceability;
- evidence links to structured same-tenant sources;
- file size, extension, MIME, signature, duplicate-digest, and private-download rules;
- attachment download audit events;
- RSS and Atom parsing, malformed XML, private-host rejection, domain allowlists, conditional requests, idempotent imports, and safe failures;
- organisation and decision export inclusion of foresight metadata and available private files;
- search indexing and decision-overview signal links;
- frontend source, signal, radar, watchlist, feed, evidence-source, and decision-link contracts.

Network tests mock feed retrieval. The automated suite must not depend on a public RSS endpoint.

## Phase 12 test behaviour

Phase 12 tests cover tenant isolation, viewer restrictions, strict command fields, active-member ownership, source-to-signal-to-driver traceability, cross-canvas relationship rejection, explicit feedback-loop validation, three-order consequence limits, archived read-only behaviour, strategic implication decision links, decision-overview integration, search, exports, audit, and safe offboarding.

## Phase 14 test behaviour

Phase 14 tests cover scorecard weighting, scale direction, confidence aggregation, criterion-weight sensitivity, quorum, threshold calculations, blind open rounds, peer-anonymous representation, method-specific ballots, Delphi round sequencing, minority reports, observer denial, strict unknown fields, and cross-tenant object isolation.

Portfolio tests cover positive weights, score and confidence bounds, unique same-tenant candidates, sealed aggregate results, peer anonymity, mandatory candidates, budget and capacity constraints, deterministic recommendation order, explicit exclusion reasons, authority selections, search, exports, audit records, and ownership-safe offboarding.

Frontend tests cover discoverability of all four evaluation methods, peer-anonymous setup, decision-envelope creation, resource constraints, sealed-result messaging, and the explicit non-automation principle. The Phase 13 to 14 upgrader also runs complete TypeScript checking, focused Vitest suites, the production Vite build, Django checks, migration-drift checks, and focused backend tests.

## Phase 15 test behaviour

Phase 15 backend tests cover cross-decision link rejection, active ownership, issue resolution attribution, owner-versus-manager update authority, ownership-transfer restrictions, synthesis draft confidentiality, version supersession, approved-summary immutability, strict unknown-field rejection, cross-tenant `404` behaviour, and the explicit no-automation principle.

The upgrade gate also exercises export, search, organisation offboarding, evaluation, scenario, and decision regressions. Frontend tests verify the option-centred view, evidence balance, scenario and collective-evaluation context, governed issue navigation, and the statement that the workspace cannot select an option.

```bash
pytest apps/decision_analysis/tests \
  apps/exports/tests/test_api.py \
  apps/search/tests/test_api.py \
  apps/organisations/tests/test_api.py \
  apps/evaluations/tests/test_api.py \
  apps/foresight/tests/test_scenario_services.py \
  apps/decisions/tests/test_api.py
```

```bash
npm test -- --run \
  src/features/decision-analysis/DecisionAnalysisPage.test.tsx \
  src/features/evaluations/DecisionEvaluationPage.test.tsx \
  src/components/AppShell.test.tsx \
  src/features/decisions/DecisionLifecycle.test.tsx
```

## Phase 15.1 test behaviour

Phase 15.1 backend tests cover CSRF enforcement, strict public-form validation, consent, honeypot rejection, storage, optional email notification, case-insensitive authentication, first-run owner creation, and standard-input password repair. Frontend tests cover the homepage conversion path, actionable credential recovery, demo form submission, email normalisation, and success references.

## Phase 16 testing focus

Phase 16 tests cover request state transitions, assignee and reviewer permissions, tenant isolation, strict serializers, draft and submitted-revision immutability, personal-work filtering, facilitation state rules, reminder/digest failure behaviour, export/search integration, offboarding blockers, frontend assignment/review flows, responsive navigation, and the exact local-login provisioning command. The release upgrader also runs representative regression suites from authentication, organisations, decisions, notifications, exports, analysis, and the public experience.

## Phase 17 testing focus

Phase 17 tests cover strict method commands, draft visibility, owner-only approval, immutable approved versions, same-tenant method application, usage provenance, administrative field permissions, ownership transfer, append-only membership history, deactivation safeguards, owner-only deletion history, invitation-policy behaviour, export/search integration, and secure debug-only local login provisioning. The upgrader also runs representative authentication, organisation, decision, invitation, contribution, export, search, and public-site regressions.

## Phase 18A accessibility testing focus

Phase 18A component tests cover route titles and live announcements, post-navigation focus, quick-navigation dialog semantics and focus restoration, workflow-tab keyboard behaviour, field-error announcements, and not-found recovery links. Public Playwright checks cover one `main` landmark per route, working skip navigation, public form labels, the ARIA tabs pattern, and the named not-found route.

The automated suite is a regression gate, not a certification. Manual assistive-technology testing remains required as described in [accessibility](accessibility.md).
