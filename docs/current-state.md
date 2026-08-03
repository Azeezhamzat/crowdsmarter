# Current state (Phase 19 baseline)

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
- React 19.2.0, TypeScript 5.9.3, Vite 8.1.5, Vitest 4.1.10
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

## Known risks not yet resolved

See `docs/known-issues.md` for the full list with recommended next steps,
including: a personal email address already committed to `origin/main`
history, a `react-router` CVE requiring a deliberate major-version upgrade,
significant reclaimable Docker disk usage from historical failed-phase
containers/volumes, and the missing backend dependency lockfile.
