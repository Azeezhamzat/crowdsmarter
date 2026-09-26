# Known issues

## 2026-08-30 readiness update

The historical phase notes below remain as an audit trail, but two statements
are now superseded. `Organisation.retention_days` is consumed by the delayed
deletion request and the new daily preview/report task; permanent destructive
deletion and automated legal holds remain intentionally unimplemented pending
policy approval. The repository also now has a locally exercised centralised
logging/metrics/dashboard/alert foundation, but external alert delivery,
multiprocess metrics, error tracking, and independent review remain open.

Tracked as of Phase 19 (2026-08-03). Move an item to a release note once it
is resolved; do not delete history from this file, mark it resolved instead.

## Closed without action

### Phase 20.4 (role-differentiated "My work" home) — already implemented

The plan assumed a gap here based on the master prompt's roadmap wording; a
close reading of the actual code shows this is already handled, and
building the assumed feature (a role-based "mode switch" on the home
dashboard) would be wrong for how the domain actually works. Every
decision computes a per-user, per-role, per-lifecycle-stage next action
server-side (`apps/portfolio/services.py:_next_action_for` — e.g. a
decision owner in `READY_FOR_DECISION` sees "Review positions and
finalise", a decision-maker without a submitted position sees "Submit your
stakeholder position", a contributor in `OPEN_FOR_CONTRIBUTION` sees
"Contribute options, evidence, assumptions, or risks"), and `MyWorkPanel`
already surfaces this per-card alongside a role badge. A single "mode"
per dashboard visit wouldn't make sense here anyway, since one person can
hold different roles on different decisions simultaneously (owner on one,
contributor on another) — the existing per-card approach is the correct
architecture for that, not a gap to fix. No code change made.

### Old failed-phase Docker volumes remain on disk (by design)

The failed-phase containers, their custom-built images, and the build cache
were removed (see "Fixed in Phase 19" below), reclaiming roughly 50 GB. Their
named Docker volumes (`crowdsmarter-phaseN-failed-*_postgres_data`,
`_media_data`, `_frontend_node_modules`, plus `crowdsmarter-v1_crowdsmarter_postgres`
and the `phase301-backup-*` volumes) remain and are not going to be removed
by an automated pass: the master prompt's non-negotiable rule is "never
delete PostgreSQL or Redis volumes," stated with no exception clause, and it
applies regardless of whether the stack that created them is still active.
They total only ~1 GB, so there's no disk-pressure reason to override that
rule. If the owner wants them gone, remove them by hand after checking each
one individually — this is a manual, owner-executed action, not something to
delegate:

```bash
docker volume ls | grep -E "phase.*-failed|phase301-backup|crowdsmarter-v1"
docker volume rm <id>          # one at a time, after checking its contents
```

### Test account left in the local database

Phase 20.1's accessibility audit needed a real authenticated session with
real data to scan ~33 routes properly (mocked component tests don't render
full pages). Provisioned a local test account
(`a11y-audit@example.test`, via `manage.py provision_local_login`) and its
auto-created organisation ("Azeez CrowdSmarter Workspace"). The test
decision and foresight canvas created during the audit were deleted
afterwards, but the account and organisation themselves could not be
cleanly removed — `AuditEvent`/`MembershipEvent` records reference them
with `on_delete=PROTECT`, which is the append-only audit trail working
exactly as designed, not a bug. Deleting them would mean bypassing that
protection, which this phase deliberately did not do. If you want it gone,
use the organisation's own deactivation/deletion flow (`/organisations/<id>/administration`)
rather than a direct database delete.

Phase 23's browser verification needed a second evaluator to produce a real
disagreement between two independent scorers, so it also created
`second-evaluator@example.test` as a `CONTRIBUTOR` member of the same
organisation. The throwaway decision/exercise/options were deleted
afterwards, but this account hit the identical `AuditEvent.actor`
`PROTECT` constraint and was left in place for the same reason as
`a11y-audit@example.test` above.

## Fixed in Phase 29

- No plan/subscription/billing/entitlement concept existed anywhere in the
  codebase, and no quota or usage-limit enforcement existed anywhere.
  Added a new `apps.billing` app (`Plan`, `OrganisationSubscription`) with
  every new organisation auto-enrolled in a trialing default plan, and
  server-side enforcement of the active plan's `max_active_decisions` /
  `max_active_members` limits (both are no-ops when the limit field is
  `None` or no subscription exists). A backfill data migration seeds three
  plans (`team`/`professional`/`enterprise`) and assigns every pre-existing
  organisation to `team`, with limits generous enough (25 decisions / 15
  members) that a script parsing every existing test function body
  confirmed no pre-existing test could be retroactively broken by the
  backfill.
- Per the master prompt's explicit instruction, wrote ADR 0031
  (`docs/adr/0031-billing-and-subscription-strategy.md`) before writing any
  billing-adjacent code, scoping what's built now (entitlements, no payment
  processing) against what's deliberately deferred (a real payment
  provider, real subscriptions/invoices/tax, webhooks) with a stated plan
  for each.
- Confirmed for the record: real payment processing (Stripe or otherwise),
  SSO/SCIM, and a production observability/deployment stack all require
  real external infrastructure or credentials unavailable in this sandbox.
  Not attempted; not regressed. Same reasoning as skipping real OAuth
  integrations in Phase 26, a real LLM provider in Phase 27, and real
  SSO/SCIM in Phase 28. Documented comprehensively in the new
  `docs/launch-readiness.md` capstone.

## Fixed in Phase 28

- No MFA/two-factor authentication capability existed anywhere in the
  codebase. Added TOTP (RFC 6238) using the Python standard library only —
  verified against the official RFC 4226 Appendix D test vectors before
  being wired into the login flow. New `TOTPDevice`/`MFABackupCode` models,
  enrollment/verification services, a session-pending two-step login gate
  (with its own expiry), and enrollment/disable UI. The no-MFA login path
  is unchanged — confirmed by all pre-existing `apps/accounts` tests
  passing without modification.
- Audited the rest of the security/enterprise-readiness checklist (CSRF,
  session security, password-reset security, rate limiting, file-upload
  validation, mass-assignment protection, audit-log immutability, tenant
  isolation) and confirmed it was already substantially in place from prior
  phases — nothing further to fix there.
- Confirmed for the record: SSO/SAML/OIDC, SCIM, customer-managed keys,
  regional hosting/data residency, IP restrictions, legal hold, and SOC
  2/ISO 27001 attestation all require real external infrastructure or
  third-party audits unavailable in this sandbox. Not attempted; not
  regressed. Same reasoning as skipping real OAuth integrations in Phase 26
  and a real LLM provider in Phase 27.
- `Organisation.retention_days` is stored but nothing currently enforces it
  (no purge job consumes it). Left as a known, narrow, well-scoped gap for
  a future phase rather than folded into this one.

## Fixed in Phase 27

- `apps/ai_assistance` had no evaluation harness at all, and two named
  "appropriate AI functions" (duplicate detection, review triggers) were
  absent from the deterministic rule provider. Added both to
  `RuleBasedAIProvider`, plus a genuine offline-testable evaluation harness
  (`tests/test_evaluation.py`: reproducibility, adversarial-input
  passthrough safety) and a "user correction rate" quality metric surfaced
  on `OrganisationAdministrationPage.tsx`. No migration — `AIReview.output`
  is an unstructured `JSONField`.
- A test caught a real bug before it shipped: adding a `generated_at` field
  to the AI review snapshot (needed for review-trigger date comparisons)
  would have made `input_fingerprint` change on every single review request
  even when the underlying decision hadn't changed, defeating its purpose
  as a reproducibility signal. Fixed by excluding `generated_at` from the
  fingerprint hash — same pattern as excluding `audit_events` from the
  export content hash in Phase 26.
- Confirmed for the record: `apps/ai_assistance` has no real LLM provider
  integration today (`RuleBasedAIProvider` is pure deterministic Python, no
  external HTTP calls, no API key anywhere in settings). Building one is
  out of scope for this sandbox — it would be untestable end-to-end without
  live credentials, and the master prompt explicitly says not to market AI
  functionality before it meets measurable quality criteria. Not attempted;
  not regressed.

## Fixed in Phase 26

- `apps/exports` had no spreadsheet-native output (JSON/CSV only) and no way
  to verify two exports came from identical underlying records — a direct
  gap against the decision-record roadmap's "export hash / immutable
  snapshot" concept. Added a multi-sheet `xlsx/export.xlsx` workbook to both
  the organisation and decision archives, and a `content_sha256` field to
  `manifest.json` (SHA-256 over every dataset's canonical JSON, excluding
  `audit_events` since downloading an export is itself an audited action
  and would otherwise make the hash unstable across back-to-back exports —
  caught by a test before it shipped). New `openpyxl` dependency; the
  backend image was rebuilt so it's baked in, not just runtime-installed.
- Real third-party integrations (Slack, Teams, Jira, Microsoft 365, Google
  Workspace, SSO/SCIM) and a general REST API/webhook platform are
  explicitly out of scope for this environment — no OAuth credentials
  exist here to build or test against them. Not attempted; not regressed.

## Fixed in Phase 25

- Risk, assumption, signpost, and outcome-review data all existed
  per-decision, but nothing rolled any of it up across an organisation — an
  executive had no single place to see "what needs attention right now"
  across all decisions. Added a `watchlist` block to
  `organisation_portfolio()` (stalled decisions, open high risks, at-risk
  assumptions, triggered signposts, benefits-realization rollup), rendered
  in `OrganisationPortfolioPage.tsx` with drill-down to source decisions.
  Pure aggregation of existing fields — no new models, no migration.
- Unlike Phase 22–24's frontend changes, Phase 25's watchlist UI got real
  test coverage (extended `OrganisationPortfolioPage.test.tsx` rather than
  relying on browser verification alone), since the existing test file
  already exercised this exact page.

## Fixed in Phase 24

- `evaluation_results()` already computed a per-criterion rank-sensitivity
  table (`criterion_sensitivity`, ±25% weight perturbation) but nothing on
  the frontend ever read it — a completed calculation was silently unused.
  Added a companion `_tornado()` computation (per-criterion impact on the
  leader's own score) and a rule-based `uncertainty_narrative`, and rendered
  all three (narrative, tornado bars, rank-stability table) in
  `DecisionEvaluationPage.tsx`. Pure read-side change, no migration.
- The dedicated-frontend-test gap noted in "Fixed in Phase 23" now also
  applies to Phase 24's tornado/narrative UI — same reasoning (verified live
  in the browser, typecheck + full suite + manual verification all passed).

## Fixed in Phase 23

- Collective evaluation results showed only a single aggregate
  (`weighted_score`/`confidence` or `approval_rate`/`objection_rate`), with
  no indication of how much evaluators actually disagreed — a direct miss
  against the master prompt's explicit mandate to never show one aggregate
  score without dispersion/dissent. `evaluation_results()` now also computes
  `score_stdev`/`score_min`/`score_max`/`disagreement` (scorecard/Delphi) and
  `dissent_rate` (approval/consent), surfaced as a disagreement badge and
  inline dissent percentage in `DecisionEvaluationPage.tsx`. Pure read-side
  change — no migration.
- Noted for the record: neither Phase 22's foresight-watchlist UI nor Phase
  23's dispersion-badge UI has a dedicated frontend component test yet —
  both were verified live in the browser instead. Not urgent (typecheck +
  the existing 48-test suite + manual verification all passed), but a
  reasonable thing to close out in a future pass if this area sees more
  churn.

## Fixed in Phase 22

- Foresight signposts had no connection to the decision-reasoning artifacts
  they were meant to inform: an assumption or risk could become invalidated
  by a scenario signal and nobody would be notified. Added
  `SignpostAssumptionLink`/`SignpostRiskLink` models, watchlist notification
  delivery (`deliver_signpost_watchlist_notifications`, wired to a daily
  Celery beat job and a management command), and an "Add to watchlist" panel
  in `ForesightScenarioSetPage.tsx`. See `docs/current-state.md` for detail.
- Confirmed a recurring environment gotcha while verifying this phase: the
  `backend` container only runs `manage.py migrate` on container start, not
  on a live filesystem change. Generating a migration mid-session (as this
  phase did twice) leaves the running dev database out of sync until
  `docker compose exec backend python manage.py migrate <app>` is run by
  hand — the symptom is a 500 with `relation "..." does not exist` even
  though `manage.py check` and the test suite (which runs against a freshly
  migrated test database) are both clean. Not a bug in the code; a step to
  remember when browser-verifying a change that added a migration.

## Fixed in Phase 21

- Decision criteria had no home: `decisions`/`decision_options` recorded
  alternatives, but there was no standalone place to record and weigh the
  criteria used to judge them. Added a new `apps/criteria` app (title,
  description, measurement note, maximize/minimize direction, 0–100 weight
  with rationale, optional must-have + threshold, owner, order, active/
  retired status) with the same service/permission/audit-log pattern as
  `apps/risks`, plus a `CriteriaSection.tsx` UI tab and an additive
  `active_criteria` readiness-gate count.
- `DecisionOption` was too shallow to support real comparison: it had no
  cost, resourcing, timeline, reversibility, experiment framing, or
  cross-option relationships. Added `estimated_cost`, `cost_notes`,
  `resource_notes`, `implementation_time_estimate`, `reversibility`,
  `is_experiment`/`experiment_notes`, and two self-referential
  relationships — `depends_on` (asymmetric) and `mutually_exclusive_with`
  (symmetric) — validated against self-reference and cross-decision leakage
  in `services.py`. `OptionsSection.tsx`'s form and cards were extended to
  match, including resolving related-option IDs to titles for display.

## Fixed in Phase 20

- WCAG 2.2 AA audit across ~33 route templates (`axe-core`, real
  authenticated data) found and fixed 9 violations: 5 colour-contrast
  instances (one a genuine dark-on-dark bug from an incomplete theme
  override), a non-keyboard-focusable scrollable region, a critical
  ARIA-tablist structure violation, a prohibited `aria-label` on a
  role-less `<span>`, and an unlabelled `<select>`. Full details in
  `docs/accessibility.md`.

## Fixed in Phase 19

- A real personal email address (the repository owner's) was committed as
  test input in `backend/apps/accounts/tests/test_commands.py` at `3cc6459`
  and published to `origin/main` on GitHub. Rewrote history with
  `git filter-repo` (verified zero matches remain anywhere in history on any
  branch, and that the rewrite changed only that one line, nothing else),
  backed up both trees first, and force-pushed the cleaned history to
  `origin/main` and `origin/claude/phase-19-stabilisation`. The 13 open
  Dependabot PRs are now based on superseded commits and will be recreated
  automatically by Dependabot's next run.
- Removed 34 stopped/idle containers and their images from ten abandoned
  upgrade attempts (`crowdsmarter-phase6-failed-*` through
  `crowdsmarter-phase17-failed-*`, `crowdsmarter-phase301-backup-*`,
  `crowdsmarter-v1-*`), then cleared the build cache. Reclaimed ~24 GB of
  build cache and ~35 GB of images; the live stack was unaffected throughout.
  No volumes were touched — see "Closed without action" above.
- `react-router` high-severity advisory (GHSA-qwww-vcr4-c8h2, CSRF bypass in
  RSC/framework server-action mode — this app doesn't use that mode, but the
  installed version was still in the flagged range `>=7.12.0 <8.3.0`).
  `react-router-dom@7.18.1` had no 8.x release available at all: as of v8,
  React Router dropped the separate `react-router-dom` package entirely and
  consolidated into `react-router` (DOM APIs like `RouterProvider` now come
  from the `react-router/dom` subpath). Uninstalled `react-router-dom`,
  installed `react-router@8.3.0` directly, and updated every import across
  ~74 files (`from "react-router-dom"` → `from "react-router"`, except
  `RouterProvider` in `src/main.tsx` → `from "react-router/dom"`). Also
  bumped `react`/`react-dom` to `19.2.8` (v8's stated minimum is `19.2.7+`)
  and `engines.node` to `>=22.22` (v8's stated minimum; the container already
  runs 22.23.2). `npm audit` now reports 0 vulnerabilities. Verified with
  typecheck, the full test suite (34/34 files), a production build, and a
  manual browser smoke test of the landing page, `/login`, the `/app`
  protected-route redirect, and the `/*` not-found route — no console
  errors, no regressions.
- DRF `min_value should be an integer or Decimal instance` warning — two
  `DecimalField(min_value=0.01)` float literals in
  `backend/apps/evaluations/serializers.py` changed to `Decimal("0.01")`.
- `apps/contributions/views.py` calling `create_request()` with a missing
  required `reviewer_id` keyword-only argument whenever a client omitted an
  optional reviewer — the service now defaults it to `None`.
- `apps/contributions/services.py` `update_request`/`submit_request` using
  `select_for_update()` combined with `select_related("reviewer")` (a
  nullable FK), which PostgreSQL rejects (`FOR UPDATE cannot be applied to
  the nullable side of an outer join`) — fixed with
  `select_for_update(of=("self",))`.
- `DecisionQualityReview.answers` (`JSONField(default=dict)`, no
  `blank=True`) rejected its own default value on `full_clean()` — added
  `blank=True` plus migration `decision_analysis.0002_...`.
- `DecisionMethodVersionDetailView` had no `GET` handler at all (405 instead
  of a tenant-safe 404 for invisible drafts) — added, reusing the existing
  `version_for_user` selector.
- `OrganisationInvitation.clean()` normalised the email *after* Django's
  `full_clean()` had already validated the raw, unstripped value — moved
  normalisation into an overridden `full_clean()` so it runs first.
- ~15 backend permission tests (`organisations`, `participants`,
  `invitations`, `workspaces`, `decisions`) passed a raw `WSGIRequest` into
  `has_object_permission()` instead of wrapping it in DRF's `Request`, so
  `force_authenticate`'s `.user` never resolved — not a production defect,
  DRF's own `dispatch()` always wraps requests correctly; test-only fix.
- `test_demo_request_is_rate_limited` replaced the whole `REST_FRAMEWORK`
  settings dict via `override_settings`, but DRF binds
  `SimpleRateThrottle.THROTTLE_RATES` as a class attribute at import time —
  `override_settings` never reaches it. Fixed by monkeypatching the throttle
  class's `.rate` directly, matching the existing pattern already used for
  `LoginRateThrottle` in `apps/accounts/tests/test_api.py`.
- Several isolated test bugs: a stale `create_request` email mismatch, a
  duplicate `organisation=` kwarg passed to the `decision_factory` fixture, a
  `pytest.raises(match=...)` regex not matching the actual error text (two
  instances), a `logger.exception` mock asserted outside its `patch(...)`
  context, and two stale in-memory `candidate.portfolio` FK caches read
  before a portfolio status transition landed in the database.
- Frontend: `vite.config.ts` had no `test.exclude` for `e2e/`, so `npm test`
  (Vitest) tried to execute Playwright specs and failed on all four with
  "Playwright Test did not expect test() to be called here."
- Frontend: Testing Library's default 1000ms `findBy`/`waitFor` timeout and
  Vitest's default 5000ms per-test timeout were both too tight for full-suite
  parallel execution in this environment, causing correctly-rendering
  components to fail non-deterministically. Raised both globally
  (`asyncUtilTimeout: 5000`, `testTimeout: 15000`).
- Four component tests used synchronous `getByRole`/`getByText` immediately
  after an unrelated `findByRole` resolved, racing a second, separately
  async-resolving query; one used an exact-string `getByText` against text
  split across a compound JSX expression; one `getByText` was ambiguous
  because the same name legitimately appears twice in the rendered page (a
  canvas summary and an owner-select dropdown option).
- Frontend `npm audit`: `brace-expansion` DoS fixed by removing an unsafe
  cross-major override and regenerating the lockfile with patched compatible
  transitive releases. This preserves ESLint's older `minimatch` contract.

## Resolved in the 2026-08-27 release audit

### Frontend lint, dependency locking, and initial bundle size

The accumulated ESLint backlog is cleared: the configured gate now exits
without errors or warnings. React Hook Form subscriptions use `useWatch()`,
which is compatible with the optional React Compiler. Backend production and
development requirements are hash-locked, the npm lockfile is consistent
with `npm ci`, and the dependency audit reports no known npm vulnerabilities.
Route-level lazy loading reduced the shared initial JavaScript chunk from
about 1.06 MB to about 360 kB; pages now load their own small feature chunks
on demand.

## Deferred, not started

- ADR duplicate numbering (0014, 0015, 0016 each shared by two unrelated
  ADRs) — content is fine, only numbering collides; needs a renumbering pass
  with a documented mapping.
- `docs/product-capability-matrix.md` and `docs/roadmap.md` — not yet
  written; need a full feature-by-app audit pass, deferred from this phase.
- 13 open Dependabot PRs on `origin` (pip: Django, DRF, dj-database-url,
  gunicorn, pytest-cov; npm: eslint-plugin-react-hooks, eslint/js,
  hookform/resolvers, prettier, react-router-dom; GitHub Actions bumps) —
  not reviewed or merged in this phase. The `react-router-dom` one is now
  moot since that package was removed entirely.
