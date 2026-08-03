# Current state (Phase 19/20/21/22/23 baseline)

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

60 backend migrations applied cleanly across all apps, including two added in
Phase 22 (`apps.foresight.0005_signpostassumptionlink_signpostrisklink` and
`apps.notifications.0003_remove_notification_notification_kind_valid_and_more`,
which adds the `signpost_watch` notification kind). No migration drift
(`makemigrations --check --dry-run` reports no changes). A pre-verification
`pg_dump` backup was taken before Phase 21's test run
(`backups/phase21-pre-verify-*.sql`, not committed).

Note: the running `backend` container only auto-applies migrations on
container start, not live — after generating a migration mid-session, run
`docker compose exec backend python manage.py migrate <app>` explicitly
before relying on the dev database matching the models (this bit Phase 22's
browser verification: the API 500'd with `relation ... does not exist` until
the two new migrations above were applied by hand).

## Test suites

- Backend: `docker compose exec backend pytest` — **363 passed, 0 failed**
  (was 361 passed at the end of Phase 22; +2 tests for Phase 23's
  evaluation-dispersion feature).
- Frontend: `docker compose exec frontend npx vitest run` — **36 test files /
  48 tests, all passing** (unchanged — both Phase 22's and Phase 23's UI
  changes were verified live in the browser instead of with new component
  tests; see known-issues.md if that gap should be closed later).
- `docker compose exec backend python manage.py check` — clean, 0 warnings.
- `docker compose exec backend python manage.py makemigrations --check --dry-run` — clean
  (Phase 23 added no migration — it only changes a computed API response).
- Frontend `npx tsc -b` and `npm run build` — clean.

## Dependencies

- Frontend now has a committed lockfile (`frontend/package-lock.json`,
  generated this phase). `npm audit` reports **0 vulnerabilities**.
  `react-router-dom` was replaced with `react-router@8.3.0` (the `-dom`
  package no longer exists as of v8; `react`/`react-dom` bumped to `19.2.8`
  to meet its minimum version requirement) — see `docs/known-issues.md` for
  the migration details.
- Backend has no committed lockfile yet; `pyproject.toml` uses range
  constraints only. See `docs/known-issues.md`.
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

Committed on `claude/phase-23-collective-intelligence`, not yet pushed.

## Known risks not yet resolved

See `docs/known-issues.md` for the full list with recommended next steps:
significant-but-optional reclaimable Docker volume space from historical
failed-phase stacks (deliberately left alone), the missing backend
dependency lockfile, and the pre-existing 93-error `eslint` backlog
surfaced (not caused) during the react-router upgrade.
