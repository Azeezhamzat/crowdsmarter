# Current state (Phase 19/20 baseline)

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

57 backend migrations applied cleanly, plus one new migration added in this
phase (`decision_analysis.0002_alter_decisionqualityreview_answers`). No
migration drift (`makemigrations --check --dry-run` reports no changes).

## Test suites

- Backend: `docker compose exec backend pytest` — **340 passed, 0 failed**
  (was 40 failed / 300 passed at the start of Phase 19).
- Frontend: `docker compose run --rm frontend npm test -- --run` — **34 test
  files / 43 tests, all passing** (was 8 files / 4 tests failing, plus 4 files
  colliding with Playwright specs, at the start of Phase 19).
- `docker compose exec backend python manage.py check` — clean, 0 warnings
  (the DRF `min_value` warning is fixed).
- `docker compose exec backend python manage.py makemigrations --check --dry-run` — clean.
- Frontend `npm run typecheck` and `npm run build` — clean.

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

All committed on `claude/phase-20-product-experience`, not yet pushed.

## Known risks not yet resolved

See `docs/known-issues.md` for the full list with recommended next steps:
significant-but-optional reclaimable Docker volume space from historical
failed-phase stacks (deliberately left alone), the missing backend
dependency lockfile, and the pre-existing 93-error `eslint` backlog
surfaced (not caused) during the react-router upgrade.
