# Current state (Phase 19/20/21/22/23/24/25/26/27/28 baseline)

Verified against the running system on 2026-08-03. Update this document
whenever the baseline materially changes; do not let it drift into aspiration.

## Repository

`~/Downloads/crowdsmarter` is the canonical Git working tree, tracking
`origin/main` at `https://github.com/Azeezhamzat/crowdsmarter.git`. It was
previously untracked (no `.git`) while a separate publishing clone
(`~/Downloads/crowdsmarter-github-publish`) held the only Git history; the two
trees were reconciled with near-zero drift and this tree is now the single
source of truth. See `docs/development-workflow.md`.

## Stack versions (verified)

- Python 3.12.13, Django 5.2.16, Django REST Framework 3.16.1
- PostgreSQL 17 (Docker image `postgres:17-alpine`), Redis 7 (`redis:7-alpine`)
- React 19.2.8, TypeScript 5.9.3, Vite 8.1.5, Vitest 4.1.10, React Router 8.3.0
- `frontend/package.json` and `backend/pyproject.toml` both report `0.18.2`

## Migrations

61 backend migrations applied cleanly across all apps, including
`apps.accounts.0003_totpdevice_mfabackupcode` (Phase 28) and two from Phase 22
(`apps.foresight.0005_signpostassumptionlink_signpostrisklink` and
`apps.notifications.0003_remove_notification_notification_kind_valid_and_more`,
which adds the `signpost_watch` notification kind). No migration drift
(`makemigrations --check --dry-run` reports no changes). A pre-verification
`pg_dump` backup was taken before Phase 21's test run
(`backups/phase21-pre-verify-*.sql`, not committed). Phase 28's migration was
applied to the dev DB immediately after generation, avoiding the Phase 22
"migrate on container start only" gotcha documented below.

Note: the running `backend` container only auto-applies migrations on
container start, not live — after generating a migration mid-session, run
`docker compose exec backend python manage.py migrate <app>` explicitly
before relying on the dev database matching the models (this bit Phase 22's
browser verification: the API 500'd with `relation ... does not exist` until
the two new migrations above were applied by hand).

## Test suites

- Backend: `docker compose exec backend pytest` — **384 passed, 0 failed**
  (was 376 passed at the end of Phase 27; +8 new tests for Phase 28's MFA
  feature: `apps/accounts/tests/test_mfa.py`).
- Frontend: `docker compose exec frontend npx vitest run` — **36 test files /
  50 tests, all passing** (+2 new tests: an MFA-enrollment walkthrough in
  `AccountSettingsPage.test.tsx` and a login-gate test in
  `LoginPage.test.tsx`).
- `docker compose exec backend python manage.py check` — clean, 0 warnings.
- `docker compose exec backend python manage.py makemigrations --check --dry-run` — clean.
- Frontend `npx tsc -b` and `npm run build` — clean.
- Backend Docker image rebuilt (`docker compose build backend`) to bake in
  the new `openpyxl` dependency, then the full suite re-run against the
  rebuilt container to confirm — see "Dependencies" below.

## Dependencies

- Frontend now has a committed lockfile (`frontend/package-lock.json`,
  generated this phase). `npm audit` reports **0 vulnerabilities**.
  `react-router-dom` was replaced with `react-router@8.3.0` (the `-dom`
  package no longer exists as of v8; `react`/`react-dom` bumped to `19.2.8`
  to meet its minimum version requirement) — see `docs/known-issues.md` for
  the migration details.
- Backend has no committed lockfile yet; `pyproject.toml` uses range
  constraints only. See `docs/known-issues.md`.
- Phase 26 added `openpyxl>=3.1,<4` to `backend/pyproject.toml` (XLSX export
  generation). Installed at runtime first (`pip install openpyxl`) to
  iterate, then the backend image was properly rebuilt
  (`docker compose build backend && docker compose up -d backend`) so the
  dependency is baked in rather than only present in the live container's
  ephemeral filesystem.
- `npm run lint` fails with 93 pre-existing errors unrelated to anything
  fixed in this phase (confirmed by re-running it against the unmodified
  code, which fails with 386). Not fixed here; see `docs/known-issues.md`.

## CI

`.github/workflows/ci.yml` already exists (backend lint/mypy/migration-check/
pytest with an 85% coverage gate; frontend lint/typecheck/test/build; a
docker-compose-based e2e job with Playwright). It was previously unreliable
because the frontend `npm test` step collided with Playwright specs and
`npm install` had no lockfile to pin against; both are fixed in this phase.

## Docker Compose

Four services running under the `crowdsmarter` project (`db`, `redis`,
`backend`, `frontend`), all healthy. `docker compose config` validates
cleanly. `docker buildx` is not installed locally; Compose falls back from
Bake without disrupting the working setup.

## Phase 20 (product experience) progress

- **20.1 — WCAG 2.2 AA audit**: real `axe-core` scan across ~33 authenticated
  and public route templates using live session data. Found and fixed 9
  violations (5 colour-contrast, one a genuine dark-on-dark bug; a
  non-keyboard-focusable scrollable region; a critical ARIA-tablist
  structure violation; a prohibited `aria-label`; an unlabelled `<select>`).
- **20.2 — First-run onboarding**: organisations with zero decisions now see
  a direct "frame your first decision" CTA on the organisation page instead
  of a neutral section nav.
- **20.3 — Contextual help**: added a small reusable `PageHelp` disclosure
  component, used on the foresight, prioritisation, and decision-analysis
  screens to explain their domain-specific concepts.
- **20.4 — Role-differentiated home**: investigated, found already
  substantially implemented server-side (`_next_action_for` in
  `apps/portfolio/services.py` computes a role- and lifecycle-stage-aware
  next action per decision); no code change needed — see
  `docs/known-issues.md`.

All committed on `claude/phase-20-product-experience`, pushed to origin.

## Phase 21 (decision workspace depth) progress

Audited the reasoning artifacts (options, evidence, assumptions, risks) and
the decision lifecycle's readiness gate against the master prompt's
"deepen the decision workspace" intent. Found two real, specific gaps and
addressed both:

- **Standalone decision criteria**: new `apps/criteria` Django app
  (`Criterion` model — title, description, measurement note, direction
  maximize/minimize, 0–100 weight with rationale, optional must-have +
  threshold, owner, order, active/retired status), following the exact
  service-layer/permission/audit pattern already used by `apps/risks`. Wired
  into the decision reasoning UI as a new `CriteriaSection.tsx`, a new
  "Criteria" tab, and an additive `active_criteria` count on the readiness
  gate (not added to `blockers`, so decisions already in flight are not
  newly gated).
- **Deeper option modelling**: `DecisionOption` gained `estimated_cost`,
  `cost_notes`, `resource_notes`, `implementation_time_estimate`,
  `reversibility` (easily/partially/difficult/irreversible),
  `is_experiment` + `experiment_notes` (MVP-style bounded experiments), and
  two self-referential option relationships — `depends_on` (asymmetric) and
  `mutually_exclusive_with` (symmetric) — both tenant- and
  self-reference-validated in `services.py`. `OptionsSection.tsx`'s form and
  option cards were extended to capture and display all of the above,
  including resolving dependency/exclusivity IDs to option titles.

Verified live in the browser (not just unit tests): logged in as the
existing `a11y-audit@example.test` test account, created a throwaway
decision and two options with a real dependency link, confirmed the form
saved correctly and the card rendered cost, reversibility, experiment, and
"Depends on: <title>" as expected, then deleted the throwaway decision.

Committed on `claude/phase-21-decision-workspace`, pushed, and fast-forward
merged into `main` (solo-maintainer repo — no PR needed; see
`docs/development-workflow.md`).

## Phase 22 (foresight adaptive-strategy watchlist) progress

Audited the full `apps/foresight` app (sources, signals, feeds, systems
mapping, scenario planning, wind-tunnelling, signposts) against the master
prompt's foresight roadmap. Found the workspace, horizon-scanning, systems
mapping, and scenario-planning sub-areas already substantially built; the
one genuine, realistically-scoped gap was **adaptive strategy** — signposts
had no connection to assumptions, risks, or notifications, so an
organisation had no way to know a specific assumption or risk should be
revisited when a signpost moved. Addressed that gap only:

- New `SignpostAssumptionLink` and `SignpostRiskLink` models (mirroring the
  existing `SignalDecisionLink` pattern), linking a `Signpost` to a specific
  `Assumption` or `Risk` in the same organisation, with a required rationale.
- New `deliver_signpost_watchlist_notifications()` in
  `apps.notifications.services`, following the exact `DecisionReview` due-
  notification pattern: notifies the signpost owner, the linked decision's
  owner, and the owners of any linked assumptions/risks when a
  `SignpostObservation` records `strong` or `contradictory` movement, and
  separately nudges the signpost owner when an active signpost has gone past
  its review cadence with no new observation. Wired to a Celery task, a
  management command (`send_signpost_watchlist_notifications`), and a daily
  `CELERY_BEAT_SCHEDULE` entry, all mirroring the existing due-review job.
- New API endpoints (`/foresight/signposts/<id>/assumption-links/` and
  `/risk-links/`) and UI: `ForesightScenarioSetPage.tsx`'s signposts tab
  gained an "Add to watchlist" panel (shown when the scenario set is linked
  to a decision, since that's what makes the assumption/risk pickers
  meaningful) and each signpost card now shows its linked assumptions/risks.

Verified live in the browser end to end: created a decision with a linked
assumption and risk, a foresight canvas/scenario set linked to that decision,
and a signpost; linked the signpost to the assumption through the new UI;
recorded a `strong` observation; ran the new management command and
confirmed exactly one `signpost_watch` notification was created and
displayed correctly on `/notifications`. Then deleted all the throwaway
foresight/decision test data.

Committed on `claude/phase-22-foresight-adaptive-strategy`, pushed, and
fast-forward merged into `main`.

## Phase 23 (collective-intelligence aggregation transparency) progress

Audited `apps/contributions` and `apps/evaluations` against the master
prompt's collective-intelligence roadmap (contribution orchestration, bias
reduction, aggregation, forecasting). Most of it was already built —
`apps/evaluations.EvaluationRound` is already a genuine pooled, time-boxed,
blind-until-close round with quorum, confidence, rationale, and minority
reports; `apps/contributions` already handles assignment/reminder workflows.
The one unmet, explicitly-worded mandate in that section — "never present
one aggregate score without showing uncertainty, dispersion, and dissent" —
was not met: `evaluation_results()` only ever returned a single
`weighted_score`/`confidence` pair. Fixed that specific gap only:

- For scorecard/Delphi exercises, `evaluation_results()` now also computes
  each evaluator's own weighted score for an option (not just the aggregate),
  then reports the spread across evaluators as `score_stdev`/`score_min`/
  `score_max` and a `disagreement` label (`low`/`moderate`/`high`, thresholds
  on the normalised 0–100 scale).
- For approval/consent exercises, it now also reports `dissent_rate` — the
  share of non-abstaining votes that didn't match the majority vote.
- `DecisionEvaluationPage.tsx`'s `RoundPanel` shows a
  low/moderate/high-disagreement badge (with a range tooltip) next to every
  scorecard result, and the dissent percentage inline next to vote results.

This is a pure read-side change — no new model, no migration; `EvaluationRound`,
`EvaluationSubmission`, and `EvaluationResponse` are unchanged.

Verified live in the browser: two evaluators scored one option identically
(3 and 3) and one option divergently (5 and 1); the identical option
correctly showed "Low disagreement" and the divergent one "High
disagreement". Then deleted the throwaway decision — the second test
account it required (`second-evaluator@example.test`) could not be removed
due to `AuditEvent.actor` `PROTECT`, same pattern as the existing
`a11y-audit@example.test` account; see `docs/known-issues.md`.

Committed on `claude/phase-23-collective-intelligence`, pushed, and
fast-forward merged into `main`.

## Phase 24 (advanced decision analysis — sensitivity transparency) progress

Audited "analysis methods" and "uncertainty and sensitivity" from the
decision-intelligence roadmap. Most methods already exist and are mature:
weighted-sum MCDA and constrained portfolio optimization in
`apps/evaluations`, scenario wind-tunnelling in `apps/foresight`. Genuinely
absent methods (outranking, AHP-style pairwise comparison, cost-
effectiveness, expected value, utility, regret) are each a much bigger,
riskier build than fits one phase, so none were started. Instead, the audit
found something more valuable and much better bounded: `_sensitivity()` in
`apps/evaluations/services.py` already computed a rank-sensitivity table
under ±25% weight perturbation, but the frontend never rendered it — the
computation existed and was silently thrown away. Fixed that, and extended
it:

- Refactored `_sensitivity()` to share a `_simulate_scores()`/
  `_perturbed_weights()` helper with a new `_tornado()` function, which
  reports, for the current top-ranked option, how much a ±25% weight change
  on each criterion moves *that option's own score* — classic tornado-chart
  data, sorted by impact descending.
- Added a rule-based `uncertainty_narrative` string to `evaluation_results()`
  (for both scorecard/Delphi and approval/consent methods), stating plainly
  whether the current leader's rank is stable under weight perturbation and
  flagging moderate/high evaluator disagreement — directly answering the
  roadmap's "do not imply mathematical certainty where inputs are
  subjective" instruction.
- `DecisionEvaluationPage.tsx`'s `RoundPanel` now renders the narrative
  sentence, a tornado bar chart, and a "Rank stability under ±25% weight
  changes" details table (the previously invisible sensitivity data).

Pure read-side change — no new model, no migration.

Verified live in the browser: an exercise with a heavily-weighted and a
lightly-weighted criterion produced tornado bars matching hand-calculated
values exactly (±9.7 and ±9.4), sorted correctly, alongside the expected
"ranks first and stays first..." narrative sentence.

Committed on `claude/phase-24-decision-analysis`, pushed, and fast-forward
merged into `main`.

## Phase 25 (portfolio and executive intelligence) progress

Audited "cross-decision portfolio," "strategic alignment," "dependencies,"
"review/watchlists," "assumption and signpost monitoring," and "actionable
executive reporting" against `apps/portfolio` (no models — a pure read-model
over `Decision`/`DecisionReview` via `organisation_portfolio()`) and the
narrower `apps/evaluations.PrioritisationPortfolio` (a curated,
budget-constrained candidate-selection tool, not an always-on portfolio
view). Confirmed the org-wide decision list/status/urgency dashboard
already exists with drill-down; a real strategic-objective/value taxonomy,
decision-to-decision dependency modelling, and concentration-risk/decision-
debt detection are all genuinely absent but each would need new concepts
and models — too large for one phase. The better-bounded find: risk,
assumption, signpost, and outcome-review data already existed per-decision
but nothing rolled any of it up across the organisation — an executive
had no single place to see it.

Added a `watchlist` block to `organisation_portfolio()`
(`apps/portfolio/services.py`), pure aggregation of existing fields, no new
models or migration:

- **Stalled decisions** — active-status decisions with no update in 21+
  days.
- **Open high risks** — `Risk.status` open/monitoring with
  likelihood or impact ≥ 4/5.
- **Assumptions at risk** — active assumptions that are either invalidated
  or overdue for re-verification (`review_date` in the past).
- **Signposts triggered** — `SignpostObservation`s with `strong`/
  `contradictory` assessments in the last 30 days.
- **Benefits realization** — org-wide rollup of `DecisionReview
  .outcome_assessment` counts.

`OrganisationPortfolioPage.tsx` renders all five as a new "Watchlist"
section between the summary metrics and the filterable decision list, each
entry linking to its source decision (or, for signposts, the scenario-set
workspace) — satisfying the roadmap's drill-down requirement.

Verified live in the browser: created one decision per watchlist category
(stalled, high-risk, at-risk-assumption, reviewed-with-outcome) plus a
foresight signpost with a strong observation; all five categories rendered
correctly with accurate counts and working drill-down links, then deleted
the throwaway data.

Committed on `claude/phase-25-portfolio-executive`, pushed, and fast-forward
merged into `main`.

## Phase 26 (integrations and customer outputs — exports) progress

Audited "high-quality exports," "imports," "API/webhooks," "selected
work-management integrations," and "data portability" against
`apps/exports` and the whole codebase. Confirmed: no real third-party OAuth
integration (Slack, Teams, Jira, Microsoft 365, Google Workspace, SSO/SCIM)
is buildable or testable in this sandboxed environment regardless of scope
choice — none were attempted. `apps/exports` already produces a solid
portable ZIP (JSON + curated CSV, RBAC-gated, audit-logged, secrets
stripped) for both a full organisation and a single decision, but had zero
spreadsheet-native output and no way to verify two exports came from
identical underlying records — a direct gap against the decision-record
roadmap's named "export hash / immutable snapshot" concept. No REST API
versioning, API-key model, or webhook delivery mechanism exists anywhere in
the codebase; establishing those is a much larger, more novel effort than
fits one phase and was deferred.

Addressed the two best-bounded, purely-additive gaps in `apps/exports/services.py`:

- **XLSX export** — a single multi-sheet workbook (`xlsx/export.xlsx`, one
  sheet per dataset, Excel's 31-character/uniqueness sheet-name limits
  handled) added to both the organisation and decision archives, using the
  new `openpyxl` dependency. Mirrors the same "curated key registers" set
  already used for CSV on the organisation export; the decision export gets
  every dataset (it's already small enough).
- **Export integrity hash** — `manifest.json` now includes
  `content_sha256`, a SHA-256 over the canonical JSON of every dataset, so
  two exports of the same underlying state hash identically and any change
  is detectable. Bumped `EXPORT_SCHEMA_VERSION` to `1.8`.

A test written for the hash caught a real bug before it shipped: the first
implementation hashed the `audit_events` dataset too, but downloading an
export is itself an audited action, so the hash was never stable across two
back-to-back exports of otherwise-identical data. Fixed by excluding
`audit_events` from the hash computation (documented inline — the export
still includes the full audit trail in JSON/CSV/XLSX, it just isn't part of
the content fingerprint).

`OrganisationExportPage.tsx`'s copy was updated to mention the workbook and
the content fingerprint.

The backend Docker image was rebuilt (`docker compose build backend`) so
`openpyxl` is baked in rather than only present via a runtime `pip install`
in the live container's ephemeral filesystem; the full test suite was
re-run against the rebuilt container to confirm.

Verified directly (via `manage.py shell`, calling `build_organisation_export`
and `build_decision_export` against real data): both produce
openpyxl-readable workbooks (57 and 48 sheets respectively) with a valid
64-character `content_sha256` in the manifest.

Committed on `claude/phase-26-exports-data-portability`, pushed, and
fast-forward merged into `main`.

## Phase 27 (governed AI copilot) progress

Audited `apps/ai_assistance` against the AI roadmap's "appropriate
functions," "required controls," and "AI evaluation" sections. The single
most important finding: **this codebase has no real LLM integration at
all** — `RuleBasedAIProvider` (the hard default, and the only provider that
exists) is pure deterministic Python (token-overlap similarity, threshold
checks), with zero external HTTP calls and no API key referenced anywhere
in settings or `.env.example`. Most of the roadmap's "required controls"
were already implemented (explicit initiation, visible provider/model,
tenant boundaries, source references, uncertainty disclosure, no automatic
writes, graceful fallback, audit logging of every request/completion/
dismissal). No AI evaluation harness existed at all. Building a real
provider integration was correctly out of scope — untestable here without
live credentials, and the roadmap explicitly says not to market AI
functionality before it meets measurable quality criteria.

Extended the existing deterministic provider and built a genuine,
offline-testable evaluation harness instead:

- **Two new "appropriate AI functions"**, both additive to
  `RuleBasedAIProvider`: duplicate-evidence detection (pairwise text
  similarity across active evidence, ≥60% term overlap) and review-trigger
  suggestions (assumptions/risks whose `review_date` has passed). Required
  adding `generated_at` to `build_decision_snapshot()` so the provider knows
  "today" without a hidden `datetime.now()` call inside deterministic logic.
- **A real bug caught by testing**: adding `generated_at` to the snapshot
  would have defeated `input_fingerprint`'s reproducibility purpose, since
  the fingerprint hashes the *entire* snapshot and a timestamp that always
  differs would make it change on every request even when nothing else
  did. Fixed by excluding `generated_at` from `_fingerprint()` — the same
  pattern as excluding `audit_events` from Phase 26's export content hash.
- **An evaluation harness** (`apps/ai_assistance/tests/test_evaluation.py`):
  reproducibility (same snapshot → byte-identical output, since
  `AIReviewOutput` is a frozen dataclass), adversarial-input passthrough
  (script-tag-style content in assumption text round-trips as literal text,
  not executed or stripped), and the two new finding types.
- **A quality/"user correction rate" metric** —
  `ai_review_quality_metrics()` aggregates existing `reviewed_at`/
  `dismissed_at` dispositions into a correction rate, exposed via an
  owner/admin-gated endpoint and a new "AI review quality" card on
  `OrganisationAdministrationPage.tsx`.

Verified live in the browser: created a decision with two near-duplicate
evidence items and an overdue assumption/risk, ran a real advisory review,
and confirmed both new finding sections appeared with accurate detail text;
then marked the review as human-reviewed and confirmed the quality card on
the administration page showed 1 completed / 1 confirmed / 0% correction
rate.

Committed on `claude/phase-27-ai-copilot`, pushed, and fast-forward merged
into `main`.

## Phase 28 (enterprise security and compliance) progress

Audited the full security checklist, GDPR-adjacent capability, and
enterprise-controls roadmap (section 15) against the codebase, which has
already been through 19+ phases of hardening. Confirmed most of the review
checklist already holds: CSRF (`CsrfViewMiddleware` + `@csrf_protect` on
every mutating auth view), session security (`SESSION_COOKIE_HTTPONLY`,
`SECURE_*` settings in production), password-reset security (single-use
timed tokens, constant public response, dedicated throttles), real
per-endpoint rate limiting across 6+ apps, keyed-digest invitation tokens,
magic-byte file-upload validation, `StrictSerializer` mass-assignment
protection, and a genuinely append-only, `PROTECT`-enforced audit log.
Export (Phase 26) and a real deletion-request/offboarding workflow already
exist. SSO/SAML/OIDC, SCIM, customer-managed keys, and multi-region hosting
are all correctly out of scope here — no real identity provider, directory
service, KMS, or region infrastructure exists in this sandbox to build or
test against, the same constraint that ruled out Phase 26/27's equivalent
externals.

The one confirmed, genuinely unbuilt, fully self-contained gap: **MFA**.
Implemented TOTP (RFC 6238) two-factor authentication using only the Python
standard library — no new runtime dependency, verified against the official
RFC 4226 Appendix D test vectors before being wired into the app (all 10
matched exactly):

- New `TOTPDevice` (secret, `confirmed_at`) and `MFABackupCode` (keyed
  digest, matching the invitation-token pattern — plaintext codes are shown
  exactly once) models on `apps.accounts`.
- `begin_mfa_enrollment`/`confirm_mfa_enrollment`/`disable_mfa`/
  `verify_mfa_code` service functions, each audit-logged.
- `SessionLoginView` now gates on confirmed MFA via a session-stored
  pending marker (`mfa_pending_user_id` + a timestamp, expiring after
  `MFA_PENDING_SESSION_SECONDS`, default 300s) instead of logging in
  directly — the normal no-MFA path is byte-for-byte unchanged, confirmed
  by all 15 pre-existing `apps/accounts` tests passing untouched.
- A new `MFAVerifyView` (rate-limited, `mfa_verify` throttle scope)
  completes the pending login on a valid TOTP or backup code.
- Frontend: a "Two-factor authentication" section on
  `AccountSettingsPage.tsx` (enroll → confirm → one-time backup-code
  reveal → disable-with-password), and a second-factor step in
  `LoginPage.tsx` that appears only when the login response is
  `{mfa_required: true}`.

Verified live in the browser end to end — the real, hardest-to-fake path:
enrolled MFA on the shared `a11y-audit@example.test` test account, computed
matching 6-digit TOTP codes from the actual issued secret using the same
`apps.accounts.totp` module via `manage.py shell` (not a mock), completed a
real gated login with a fresh code, then **disabled MFA again on that
account** before finishing, since it's reused for every phase's browser
verification and leaving it MFA-enabled would have silently broken every
future phase's login step.

Committed on `claude/phase-28-mfa-enterprise-security`, not yet pushed.

## Known risks not yet resolved

See `docs/known-issues.md` for the full list with recommended next steps:
significant-but-optional reclaimable Docker volume space from historical
failed-phase stacks (deliberately left alone), the missing backend
dependency lockfile, and the pre-existing 93-error `eslint` backlog
surfaced (not caused) during the react-router upgrade.
